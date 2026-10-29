"""Minimal reader for Android resources.arsc / binary XML string pools.
Used to (a) look up framework attribute IDs and (b) validate our own output."""
import struct


def read_string_pool(buf, off):
    typ, hsize, size = struct.unpack_from('<HHI', buf, off)
    assert typ == 0x0001, hex(typ)
    count, styles, flags, sstart, ystart = struct.unpack_from('<IIIII', buf, off + 8)
    utf8 = bool(flags & 0x100)
    offs = struct.unpack_from('<%dI' % count, buf, off + hsize)
    base = off + sstart
    out = []
    for o in offs:
        p = base + o
        if utf8:
            n = buf[p]; p += 1
            if n & 0x80:
                p += 1
            n = buf[p]; p += 1
            if n & 0x80:
                n = ((n & 0x7f) << 8) | buf[p]; p += 1
            out.append(buf[p:p + n].decode('utf-8', 'replace'))
        else:
            n = struct.unpack_from('<H', buf, p)[0]; p += 2
            if n & 0x8000:
                n = ((n & 0x7fff) << 16) | struct.unpack_from('<H', buf, p)[0]; p += 2
            out.append(buf[p:p + 2 * n].decode('utf-16le', 'replace'))
    return out, size


def read_arsc(buf):
    """Returns {(type_name, entry_name): res_id} plus a list of (res_id, type, name, value) entries."""
    typ, hsize, size, pkgcount = struct.unpack_from('<HHII', buf, 0)
    assert typ == 0x0002
    off = hsize
    gstrings = None
    ids = {}
    values = []
    while off < size:
        ctype, chsize, csize = struct.unpack_from('<HHI', buf, off)
        if ctype == 0x0001:
            gstrings, _ = read_string_pool(buf, off)
        elif ctype == 0x0200:
            pid = struct.unpack_from('<I', buf, off + 8)[0]
            type_off, = struct.unpack_from('<I', buf, off + 8 + 4 + 256)
            key_off, = struct.unpack_from('<I', buf, off + 8 + 4 + 256 + 8)
            tstrings, _ = read_string_pool(buf, off + type_off)
            kstrings, _ = read_string_pool(buf, off + key_off)
            p = off + chsize
            end = off + csize
            while p < end:
                t2, h2, s2 = struct.unpack_from('<HHI', buf, p)
                if t2 == 0x0201:
                    tid, tflags = buf[p + 8], buf[p + 9]
                    count, estart = struct.unpack_from('<II', buf, p + 12)
                    cfgsize = struct.unpack_from('<I', buf, p + 20)[0]
                    tname = tstrings[tid - 1]
                    if tflags & 0x01:  # sparse
                        pairs = struct.unpack_from('<%dI' % count, buf, p + h2)
                        entries = [((x & 0xffff), (x >> 16) * 4) for x in pairs]
                    elif tflags & 0x02:  # 16-bit offsets
                        o16 = struct.unpack_from('<%dH' % count, buf, p + h2)
                        entries = [(i, (x * 4 if x != 0xffff else None)) for i, x in enumerate(o16)]
                    else:
                        o32 = struct.unpack_from('<%dI' % count, buf, p + h2)
                        entries = [(i, (x if x != 0xffffffff else None)) for i, x in enumerate(o32)]
                    for idx, eo in entries:
                        if eo is None:
                            continue
                        ep = p + estart + eo
                        esize, eflags, ekey = struct.unpack_from('<HHI', buf, ep)
                        if eflags & 0x0008:  # FLAG_COMPACT: key in first u16, value in ekey
                            name = kstrings[esize]
                            rid = (pid << 24) | (tid << 16) | idx
                            ids[(tname, name)] = rid
                            continue
                        name = kstrings[ekey]
                        rid = (pid << 24) | (tid << 16) | idx
                        ids[(tname, name)] = rid
                        if not (eflags & 0x0001):
                            vsize, _, vtype, vdata = struct.unpack_from('<HBBI', buf, ep + esize)
                            sval = gstrings[vdata] if (vtype == 0x03 and gstrings) else None
                            values.append((rid, tname, name, vtype, vdata, sval, cfgsize))
                p += s2
        off += csize
    return ids, values


if __name__ == '__main__':
    import sys
    data = open(sys.argv[1], 'rb').read()
    ids, _ = read_arsc(data)
    for q in sys.argv[2:]:
        t, n = q.split('/')
        print(q, hex(ids.get((t, n), 0)))
