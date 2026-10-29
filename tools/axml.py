"""Android binary XML (AXML) writer + reader, for AndroidManifest.xml and res/xml files."""
import struct

ANDROID_NS = 'http://schemas.android.com/apk/res/android'

# Framework attribute IDs, read from the Android framework resources.arsc (see README).
ATTR_IDS = {
    'theme': 0x01010000, 'label': 0x01010001, 'icon': 0x01010002, 'name': 0x01010003,
    'permission': 0x01010006, 'exported': 0x01010010, 'process': 0x01010011,
    'launchMode': 0x0101001d,
    'screenOrientation': 0x0101001e, 'configChanges': 0x0101001f, 'description': 0x01010020,
    'value': 0x01010024, 'resource': 0x01010025, 'minSdkVersion': 0x0101020c,
    'versionCode': 0x0101021b, 'versionName': 0x0101021c, 'windowSoftInputMode': 0x0101022b,
    'targetSdkVersion': 0x01010270, 'allowBackup': 0x01010280, 'required': 0x0101028e,
    'hardwareAccelerated': 0x010102d3, 'accessibilityEventTypes': 0x01010380,
    'accessibilityFeedbackType': 0x01010382, 'notificationTimeout': 0x01010383,
    'accessibilityFlags': 0x01010384, 'canRetrieveWindowContent': 0x01010385,
    'canRequestFilterKeyEvents': 0x010103d9, 'banner': 0x010103f2,
    'usesCleartextTraffic': 0x010104ec,
}

T_REF, T_STRING, T_INT_DEC, T_INT_HEX, T_BOOL = 0x01, 0x03, 0x10, 0x11, 0x12


class E:
    """XML element. attrs: list of (name, value, android_ns: bool)."""
    def __init__(self, tag, attrs=None, children=None):
        self.tag = tag
        self.attrs = attrs or []
        self.children = children or []


def A(name, value):
    return (name, value, True)


def P(name, value):
    return (name, value, False)


def ref(x):
    return ('ref', x)


def hexint(x):
    return ('hex', x)


def _pool(strings):
    """UTF-16 string pool chunk."""
    offs, data = [], bytearray()
    for s in strings:
        offs.append(len(data))
        u = s.encode('utf-16le')
        n = len(s)
        assert n < 0x8000
        data += struct.pack('<H', n) + u + b'\x00\x00'
    while len(data) % 4:
        data += b'\x00'
    hsize = 28
    sstart = hsize + 4 * len(strings)
    size = sstart + len(data)
    return struct.pack('<HHIIIIII', 0x0001, hsize, size, len(strings), 0, 0, sstart, 0) + \
        struct.pack('<%dI' % len(strings), *offs) + bytes(data)


def write(root):
    # gather strings: attribute names with resource IDs first (ordered like the resource map)
    res_names, others = [], []

    def walk(e):
        for (n, v, ns) in e.attrs:
            if ns:
                assert n in ATTR_IDS, n
                if n not in res_names:
                    res_names.append(n)
            elif n not in others:
                others.append(n)
            if isinstance(v, str) and v not in others:
                others.append(v)
        if e.tag not in others:
            others.append(e.tag)
        for c in e.children:
            walk(c)
    walk(root)
    res_names.sort(key=lambda n: ATTR_IDS[n])
    extra = ['android', ANDROID_NS]
    strings = list(res_names) + [s for s in others + extra if s not in res_names]
    # dedupe keeping order
    seen, pool = set(), []
    for s in strings:
        if s not in seen:
            seen.add(s)
            pool.append(s)
    si = {s: i for i, s in enumerate(pool)}

    chunks = bytearray()
    chunks += _pool(pool)
    rmap = struct.pack('<%dI' % len(res_names), *[ATTR_IDS[n] for n in res_names])
    chunks += struct.pack('<HHI', 0x0180, 8, 8 + len(rmap)) + rmap

    NONE = 0xFFFFFFFF
    line = [1]

    def node_hdr(typ, size):
        line[0] += 1
        return struct.pack('<HHIII', typ, 16, size, line[0], NONE)

    chunks += node_hdr(0x0100, 24) + struct.pack('<II', si['android'], si[ANDROID_NS])

    def emit(e):
        attrs = []
        for (n, v, ns) in e.attrs:
            key = (0, ATTR_IDS[n]) if ns else (1, n)
            if isinstance(v, str):
                raw, typ, data = si[v], T_STRING, si[v]
            elif isinstance(v, bool):
                raw, typ, data = NONE, T_BOOL, (0xFFFFFFFF if v else 0)
            elif isinstance(v, int):
                raw, typ, data = NONE, T_INT_DEC, v & 0xFFFFFFFF
            elif v[0] == 'ref':
                raw, typ, data = NONE, T_REF, v[1]
            elif v[0] == 'hex':
                raw, typ, data = NONE, T_INT_HEX, v[1]
            else:
                raise ValueError(v)
            attrs.append((key, struct.pack('<IIIHBBI', si[ANDROID_NS] if ns else NONE, si[n], raw, 8, 0, typ, data)))
        attrs.sort(key=lambda a: a[0])
        body = struct.pack('<IIHHHHHH', NONE, si[e.tag], 20, 20, len(attrs), 0, 0, 0) + b''.join(a[1] for a in attrs)
        out = node_hdr(0x0102, 16 + len(body)) + body
        for c in e.children:
            out += emit(c)
        out += node_hdr(0x0103, 24) + struct.pack('<II', NONE, si[e.tag])
        return out

    chunks += emit(root)
    chunks += node_hdr(0x0101, 24) + struct.pack('<II', si['android'], si[ANDROID_NS])
    return struct.pack('<HHI', 0x0003, 8, 8 + len(chunks)) + bytes(chunks)


def dump(buf):
    """Decode AXML back to readable XML (validation)."""
    from arsc_read import read_string_pool
    typ, hs, size = struct.unpack_from('<HHI', buf, 0)
    assert typ == 0x0003 and size == len(buf), (typ, size, len(buf))
    p = hs
    strings, rmap = None, []
    out, depth = [], 0
    while p < size:
        t, h, s = struct.unpack_from('<HHI', buf, p)
        if t == 0x0001:
            strings, _ = read_string_pool(buf, p)
        elif t == 0x0180:
            rmap = list(struct.unpack_from('<%dI' % ((s - 8) // 4), buf, p + 8))
        elif t == 0x0102:
            ns, name, ast, asz, cnt = struct.unpack_from('<IIHHH', buf, p + 16)
            parts = []
            prev = -1
            for i in range(cnt):
                ans, an, raw, vs, _, vt, vd = struct.unpack_from('<IIIHBBI', buf, p + 16 + ast + i * asz)
                rid = rmap[an] if an < len(rmap) else None
                if rid is not None:
                    assert rid > prev, 'attributes not sorted by resource id'
                    prev = rid
                pre = 'android:' if ans != 0xFFFFFFFF else ''
                if vt == T_STRING:
                    v = '"%s"' % strings[vd]
                elif vt == T_BOOL:
                    v = 'true' if vd else 'false'
                elif vt == T_REF:
                    v = '@0x%08x' % vd
                elif vt == T_INT_HEX:
                    v = '0x%x' % vd
                else:
                    v = str(vd)
                parts.append('%s%s=%s%s' % (pre, strings[an], v, (' [res 0x%08x]' % rid) if rid else ''))
            out.append('  ' * depth + '<%s %s>' % (strings[name], ' '.join(parts)))
            depth += 1
        elif t == 0x0103:
            depth -= 1
        p += s
    return '\n'.join(out)
