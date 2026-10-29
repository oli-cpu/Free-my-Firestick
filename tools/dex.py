"""A small, self-contained DEX (Dalvik Executable, version 035) assembler.

Classes are described with smali-like instruction tuples; this module resolves
all constant pools, encodes the bytecode and writes a spec-conformant .dex file
(sorted id sections, map_list, adler32 checksum and SHA-1 signature).
Reference: https://source.android.com/docs/core/runtime/dex-format
"""
import hashlib
import re
import struct
import zlib

ACC_PUBLIC, ACC_PRIVATE, ACC_PROTECTED, ACC_STATIC, ACC_FINAL = 0x1, 0x2, 0x4, 0x8, 0x10
ACC_CONSTRUCTOR = 0x10000
NO_INDEX = 0xFFFFFFFF


def uleb(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def sleb(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if (n == 0 and not (b & 0x40)) or (n == -1 and (b & 0x40)):
            out.append(b)
            return bytes(out)
        out.append(b | 0x80)


def mutf8(s):
    out = bytearray()
    for ch in s:
        c = ord(ch)
        if c == 0:
            out += b'\xc0\x80'
        elif c < 0x80:
            out.append(c)
        elif c < 0x800:
            out += bytes([0xC0 | (c >> 6), 0x80 | (c & 0x3F)])
        elif c < 0x10000:
            out += bytes([0xE0 | (c >> 12), 0x80 | ((c >> 6) & 0x3F), 0x80 | (c & 0x3F)])
        else:
            raise ValueError('supplementary characters not supported')
    return bytes(out)


def utf16_key(s):
    return [ord(c) for c in s]


MREF = re.compile(r'^(L[^;]+;)->([^(]+)\((.*)\)(.+)$')
FREF = re.compile(r'^(L[^;]+;)->([^:]+):(.+)$')


def split_params(sig):
    out, i = [], 0
    while i < len(sig):
        j = i
        while sig[j] == '[':
            j += 1
        if sig[j] == 'L':
            j = sig.index(';', j)
        out.append(sig[i:j + 1])
        i = j + 1
    return out


def shorty_char(t):
    return 'L' if t[0] in 'L[' else t


def type_words(t):
    return 2 if t in ('J', 'D') else 1


# opcode table: name -> (opcode, format)
OPS = {
    'nop': (0x00, '10x'),
    'move-result': (0x0a, '11x'), 'move-result-object': (0x0c, '11x'),
    'move-exception': (0x0d, '11x'),
    'return-void': (0x0e, '10x'), 'return': (0x0f, '11x'), 'return-object': (0x11, '11x'),
    'const/4': (0x12, '11n'), 'const/16': (0x13, '21s'), 'const': (0x14, '31i'),
    'const/high16': (0x15, '21h'), 'const-wide/16': (0x16, '21s'),
    'const-string': (0x1a, '21c'), 'const-class': (0x1c, '21c'),
    'check-cast': (0x1f, '21c'), 'new-instance': (0x22, '21c'),
    'goto/16': (0x29, '20t'),
    'if-eq': (0x32, '22t'), 'if-ne': (0x33, '22t'), 'if-lt': (0x34, '22t'),
    'if-ge': (0x35, '22t'), 'if-gt': (0x36, '22t'), 'if-le': (0x37, '22t'),
    'if-eqz': (0x38, '21t'), 'if-nez': (0x39, '21t'), 'if-ltz': (0x3a, '21t'),
    'if-gez': (0x3b, '21t'), 'if-gtz': (0x3c, '21t'), 'if-lez': (0x3d, '21t'),
    'iget-object': (0x54, '22c'), 'iput-object': (0x5b, '22c'),
    'sget-boolean': (0x63, '21c'), 'sget-object': (0x62, '21c'),
    'sput-boolean': (0x6a, '21c'),
    'invoke-virtual': (0x6e, '35c'), 'invoke-super': (0x6f, '35c'),
    'invoke-direct': (0x70, '35c'), 'invoke-static': (0x71, '35c'),
    'invoke-interface': (0x72, '35c'),
    'add-int/lit8': (0xd8, '22b'),
}
FMT_UNITS = {'10x': 1, '11x': 1, '11n': 1, '21s': 2, '21h': 2, '31i': 3, '21c': 2,
             '20t': 2, '22t': 2, '21t': 2, '22c': 2, '35c': 3, '22b': 2}


class Method:
    def __init__(self, cls, name, params, ret, access, locals_=0, code=None, annotations=()):
        self.cls, self.name, self.params, self.ret = cls, name, list(params), ret
        self.access, self.locals, self.code = access, locals_, code
        self.annotations = list(annotations)

    @property
    def ref(self):
        return '%s->%s(%s)%s' % (self.cls, self.name, ''.join(self.params), self.ret)

    @property
    def is_direct(self):
        return bool(self.access & (ACC_STATIC | ACC_PRIVATE | ACC_CONSTRUCTOR))


class ClassDef:
    def __init__(self, name, super_, interfaces=(), access=ACC_PUBLIC):
        self.name, self.super, self.interfaces, self.access = name, super_, list(interfaces), access
        self.fields = []   # (name, type, access)
        self.methods = []

    def field(self, name, type_, access=0):
        self.fields.append((name, type_, access))

    def method(self, name, sig, access, locals_=0, code=None, annotations=()):
        m = re.match(r'^\((.*)\)(.+)$', sig)
        m = Method(self.name, name, split_params(m.group(1)), m.group(2), access, locals_, code, annotations)
        self.methods.append(m)
        return m


class Dex:
    def __init__(self):
        self.classes = []

    def add(self, cls):
        self.classes.append(cls)
        return cls

    # ---------------------------------------------------------------- pools
    def _collect(self):
        strings, types, protos, fields, methods = set(), set(), set(), set(), set()

        def T(t):
            types.add(t)
            strings.add(t)

        def P(params, ret):
            T(ret)
            for p in params:
                T(p)
            shorty = shorty_char(ret) + ''.join(shorty_char(p) for p in params)
            strings.add(shorty)
            protos.add((ret, tuple(params)))

        def M(ref):
            m = MREF.match(ref)
            assert m, ref
            c, n, ps, r = m.group(1), m.group(2), split_params(m.group(3)), m.group(4)
            T(c)
            strings.add(n)
            P(ps, r)
            methods.add((c, n, r, tuple(ps)))

        def F(ref):
            m = FREF.match(ref)
            assert m, ref
            c, n, t = m.groups()
            T(c), T(t)
            strings.add(n)
            fields.add((c, n, t))

        for cls in self.classes:
            T(cls.name)
            T(cls.super)
            for i in cls.interfaces:
                T(i)
            for (n, t, a) in cls.fields:
                F('%s->%s:%s' % (cls.name, n, t))
            for m in cls.methods:
                M(m.ref)
                for a in m.annotations:
                    T(a)
                for ins in (m.code or []):
                    op = ins[0]
                    if op in ('label', 'try', 'endtry', 'catchall'):
                        continue
                    fmt = OPS[op][1]
                    if op == 'const-string':
                        strings.add(ins[2])
                    elif op in ('const-class', 'check-cast', 'new-instance'):
                        T(ins[2])
                    elif fmt == '35c':
                        M(ins[2])
                    elif fmt == '22c':
                        F(ins[3])
                    elif op in ('sget-boolean', 'sget-object', 'sput-boolean'):
                        F(ins[2])
        self.strings = sorted(strings, key=utf16_key)
        self.sidx = {s: i for i, s in enumerate(self.strings)}
        self.types = sorted(types, key=lambda t: self.sidx[t])
        self.tidx = {t: i for i, t in enumerate(self.types)}

        def proto_key(p):
            return (self.tidx[p[0]], [self.tidx[x] for x in p[1]])
        self.protos = sorted(protos, key=proto_key)
        self.pidx = {p: i for i, p in enumerate(self.protos)}
        self.fields_ = sorted(fields, key=lambda f: (self.tidx[f[0]], self.sidx[f[1]], self.tidx[f[2]]))
        self.fidx = {'%s->%s:%s' % f: i for i, f in enumerate(self.fields_)}
        self.methods_ = sorted(methods, key=lambda m: (self.tidx[m[0]], self.sidx[m[1]], self.pidx[(m[2], m[3])]))
        self.midx = {'%s->%s(%s)%s' % (m[0], m[1], ''.join(m[3]), m[2]): i for i, m in enumerate(self.methods_)}

    # ---------------------------------------------------------------- code
    def _assemble(self, m):
        ins_size = sum(type_words(p) for p in m.params) + (0 if m.access & ACC_STATIC else 1)
        regs = m.locals + ins_size

        def R(r):
            if r[0] == 'p':
                n = m.locals + int(r[1:])
            else:
                assert r[0] == 'v'
                n = int(r[1:])
            assert 0 <= n < regs, (m.ref, r, regs)
            return n

        # pass 1: addresses
        addr, labels, items = 0, {}, []
        tries, cur_try = [], None
        for ins in m.code:
            op = ins[0]
            if op == 'label':
                assert ins[1] not in labels, ins
                labels[ins[1]] = addr
                continue
            if op == 'try':
                cur_try = [addr, None, ins[1]]   # start, end, handler label
                continue
            if op == 'endtry':
                cur_try[1] = addr
                tries.append(cur_try)
                cur_try = None
                continue
            items.append((addr, ins))
            addr += FMT_UNITS[OPS[op][1]]
        assert cur_try is None
        insns_size = addr

        outs = 0
        units = []
        for (pc, ins) in items:
            op = ins[0]
            code, fmt = OPS[op]

            def off(label):
                d = labels[label] - pc
                return d

            if fmt == '10x':
                units += [code]
            elif fmt == '11x':
                units += [code | (R(ins[1]) << 8)]
            elif fmt == '11n':
                a, b = R(ins[1]), ins[2]
                assert a < 16 and -8 <= b <= 7, ins
                units += [code | (a << 8) | ((b & 0xF) << 12)]
            elif fmt == '21s':
                a, b = R(ins[1]), ins[2]
                assert -32768 <= b <= 32767
                units += [code | (a << 8), b & 0xFFFF]
            elif fmt == '21h':
                a, b = R(ins[1]), ins[2]   # b = high 16 bits
                assert 0 <= b <= 0xFFFF
                units += [code | (a << 8), b]
            elif fmt == '31i':
                a, b = R(ins[1]), ins[2] & 0xFFFFFFFF
                units += [code | (a << 8), b & 0xFFFF, b >> 16]
            elif fmt == '21c':
                a = R(ins[1])
                if op == 'const-string':
                    idx = self.sidx[ins[2]]
                elif op in ('const-class', 'check-cast', 'new-instance'):
                    idx = self.tidx[ins[2]]
                else:
                    idx = self.fidx[ins[2]]
                assert idx <= 0xFFFF
                units += [code | (a << 8), idx]
            elif fmt == '20t':
                d = off(ins[1])
                assert d != 0
                units += [code, d & 0xFFFF]
            elif fmt == '22t':
                a, b = R(ins[1]), R(ins[2])
                assert a < 16 and b < 16
                units += [code | (a << 8) | (b << 12), off(ins[3]) & 0xFFFF]
            elif fmt == '21t':
                a = R(ins[1])
                units += [code | (a << 8), off(ins[2]) & 0xFFFF]
            elif fmt == '22c':
                a, b = R(ins[1]), R(ins[2])
                assert a < 16 and b < 16
                units += [code | (a << 8) | (b << 12), self.fidx[ins[3]]]
            elif fmt == '22b':
                a, b, c = R(ins[1]), R(ins[2]), ins[3]
                assert -128 <= c <= 127
                units += [code | (a << 8), b | ((c & 0xFF) << 8)]
            elif fmt == '35c':
                rs = [R(r) for r in ins[1]]
                assert len(rs) <= 5 and all(r < 16 for r in rs), ins
                mref = ins[2]
                mm = MREF.match(mref)
                words = sum(type_words(p) for p in split_params(mm.group(3))) + (0 if op == 'invoke-static' else 1)
                assert words == len(rs), ('arg count mismatch', m.ref, ins)
                outs = max(outs, words)
                rr = rs + [0] * (5 - len(rs))
                units += [code | (rr[4] << 8) | (len(rs) << 12), self.midx[mref],
                          rr[0] | (rr[1] << 4) | (rr[2] << 8) | (rr[3] << 12)]
            else:
                raise ValueError(fmt)
        assert len(units) == insns_size

        body = struct.pack('<HHHHII', regs, ins_size, outs, len(tries), 0, insns_size)
        body += struct.pack('<%dH' % len(units), *units)
        if tries:
            if insns_size % 2:
                body += b'\x00\x00'
            # one catch-all handler per distinct label
            handler_labels = []
            for t in tries:
                if t[2] not in handler_labels:
                    handler_labels.append(t[2])
            hlist = uleb(len(handler_labels))
            hoff = {}
            for hl in handler_labels:
                hoff[hl] = len(hlist)
                hlist += sleb(0) + uleb(labels[hl])
            for (start, end, hl) in tries:
                assert end > start
                body += struct.pack('<IHH', start, end - start, hoff[hl])
            body += hlist
        return body

    # ---------------------------------------------------------------- write
    def build(self):
        self._collect()
        HEADER = 0x70
        n_str, n_typ, n_pro, n_fld, n_met, n_cls = (len(self.strings), len(self.types), len(self.protos),
                                                    len(self.fields_), len(self.methods_), len(self.classes))
        off_str = HEADER
        off_typ = off_str + 4 * n_str
        off_pro = off_typ + 4 * n_typ
        off_fld = off_pro + 12 * n_pro
        off_met = off_fld + 8 * n_fld
        off_cls = off_met + 8 * n_met
        data_off = off_cls + 32 * n_cls

        data = bytearray()
        sections = []  # (type, count, offset)

        def align(n):
            while (data_off + len(data)) % n:
                data.append(0)

        def here():
            return data_off + len(data)

        # code items
        align(4)
        code_off = {}
        start = here()
        count = 0
        for cls in self.classes:
            for m in cls.methods:
                if m.code is None:
                    continue
                align(4)
                code_off[m.ref] = here()
                data.extend(self._assemble(m))
                count += 1
        if count:
            sections.append((0x2001, count, start))

        # type lists (proto params + interfaces), deduplicated
        align(4)
        tl_off = {}
        start = here()
        count = 0
        all_lists = [p[1] for p in self.protos if p[1]] + [tuple(c.interfaces) for c in self.classes if c.interfaces]
        for tl in all_lists:
            if tl in tl_off:
                continue
            align(4)
            tl_off[tl] = here()
            data.extend(struct.pack('<I', len(tl)))
            data.extend(struct.pack('<%dH' % len(tl), *[self.tidx[t] for t in tl]))
            count += 1
        if count:
            sections.append((0x1001, count, start))

        # string data
        str_off = []
        start = here()
        for s in self.strings:
            str_off.append(here())
            data.extend(uleb(len(s)) + mutf8(s) + b'\x00')
        sections.append((0x2002, n_str, start))

        # annotation items (one per annotation type, no elements, RUNTIME visibility)
        ann_types = sorted({a for c in self.classes for m in c.methods for a in m.annotations}, key=lambda t: self.tidx[t])
        ann_item_off = {}
        if ann_types:
            start = here()
            for a in ann_types:
                ann_item_off[a] = here()
                data.extend(b'\x01' + uleb(self.tidx[a]) + uleb(0))
            sections.append((0x2004, len(ann_types), start))

        # class data
        class_data_off = {}
        start = here()
        for cls in self.classes:
            class_data_off[cls.name] = here()
            sf = sorted([f for f in cls.fields if f[2] & ACC_STATIC], key=lambda f: self.fidx['%s->%s:%s' % (cls.name, f[0], f[1])])
            inf = sorted([f for f in cls.fields if not f[2] & ACC_STATIC], key=lambda f: self.fidx['%s->%s:%s' % (cls.name, f[0], f[1])])
            dm = sorted([m for m in cls.methods if m.is_direct], key=lambda m: self.midx[m.ref])
            vm = sorted([m for m in cls.methods if not m.is_direct], key=lambda m: self.midx[m.ref])
            out = uleb(len(sf)) + uleb(len(inf)) + uleb(len(dm)) + uleb(len(vm))
            for group in (sf, inf):
                prev = 0
                for (n, t, a) in group:
                    i = self.fidx['%s->%s:%s' % (cls.name, n, t)]
                    out += uleb(i - prev) + uleb(a)
                    prev = i
            for group in (dm, vm):
                prev = 0
                for mm in group:
                    i = self.midx[mm.ref]
                    out += uleb(i - prev) + uleb(mm.access) + uleb(code_off.get(mm.ref, 0))
                    prev = i
            data.extend(out)
        sections.append((0x2000, n_cls, start))

        # annotation sets + directories (4-byte aligned)
        ann_dir_off = {}
        set_off = {}
        if ann_types:
            align(4)
            start = here()
            count = 0
            for cls in self.classes:
                for mm in cls.methods:
                    if mm.annotations:
                        key = tuple(sorted(mm.annotations, key=lambda t: self.tidx[t]))
                        if key in set_off:
                            continue
                        align(4)
                        set_off[key] = here()
                        data.extend(struct.pack('<I', len(key)))
                        for a in key:
                            data.extend(struct.pack('<I', ann_item_off[a]))
                        count += 1
            sections.append((0x1003, count, start))
            align(4)
            start = here()
            count = 0
            for cls in self.classes:
                annotated = sorted([mm for mm in cls.methods if mm.annotations], key=lambda mm: self.midx[mm.ref])
                if not annotated:
                    continue
                align(4)
                ann_dir_off[cls.name] = here()
                data.extend(struct.pack('<IIII', 0, 0, len(annotated), 0))
                for mm in annotated:
                    key = tuple(sorted(mm.annotations, key=lambda t: self.tidx[t]))
                    data.extend(struct.pack('<II', self.midx[mm.ref], set_off[key]))
                count += 1
            sections.append((0x2006, count, start))

        # map list
        align(4)
        map_off = here()
        allsec = [(0x0000, 1, 0), (0x0001, n_str, off_str), (0x0002, n_typ, off_typ)]
        if n_pro:
            allsec.append((0x0003, n_pro, off_pro))
        if n_fld:
            allsec.append((0x0004, n_fld, off_fld))
        if n_met:
            allsec.append((0x0005, n_met, off_met))
        allsec.append((0x0006, n_cls, off_cls))
        allsec += sections
        allsec.append((0x1000, 1, map_off))
        allsec.sort(key=lambda s: s[2])
        data.extend(struct.pack('<I', len(allsec)))
        for (t, c, o) in allsec:
            data.extend(struct.pack('<HHII', t, 0, c, o))
        align(4)

        # id sections
        ids = bytearray()
        for o in str_off:
            ids += struct.pack('<I', o)
        for t in self.types:
            ids += struct.pack('<I', self.sidx[t])
        for (ret, params) in self.protos:
            shorty = shorty_char(ret) + ''.join(shorty_char(p) for p in params)
            ids += struct.pack('<III', self.sidx[shorty], self.tidx[ret], tl_off[params] if params else 0)
        for (c, n, t) in self.fields_:
            ids += struct.pack('<HHI', self.tidx[c], self.tidx[t], self.sidx[n])
        for (c, n, r, ps) in self.methods_:
            ids += struct.pack('<HHI', self.tidx[c], self.pidx[(r, ps)], self.sidx[n])
        for cls in self.classes:
            ids += struct.pack('<IIIIIIII', self.tidx[cls.name], cls.access, self.tidx[cls.super],
                               tl_off[tuple(cls.interfaces)] if cls.interfaces else 0, NO_INDEX,
                               ann_dir_off.get(cls.name, 0), class_data_off[cls.name], 0)
        assert HEADER + len(ids) == data_off

        file_size = data_off + len(data)
        header = bytearray(b'dex\n035\x00') + bytes(4) + bytes(20)
        header += struct.pack('<IIIIII', file_size, HEADER, 0x12345678, 0, 0, map_off)
        header += struct.pack('<II', n_str, off_str if n_str else 0)
        header += struct.pack('<II', n_typ, off_typ if n_typ else 0)
        header += struct.pack('<II', n_pro, off_pro if n_pro else 0)
        header += struct.pack('<II', n_fld, off_fld if n_fld else 0)
        header += struct.pack('<II', n_met, off_met if n_met else 0)
        header += struct.pack('<II', n_cls, off_cls if n_cls else 0)
        header += struct.pack('<II', len(data), data_off)
        assert len(header) == HEADER
        blob = bytearray(header + ids + data)
        blob[12:32] = hashlib.sha1(blob[32:]).digest()
        blob[8:12] = struct.pack('<I', zlib.adler32(bytes(blob[12:])) & 0xFFFFFFFF)
        return bytes(blob)
