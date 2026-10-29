"""Independent DEX reader used to validate dex.py output.

Re-parses the file from bytes (header, map, id sections, class data, code,
try/catch, annotations), checks checksum/signature/alignment/sort order, prints
a smali-like disassembly and runs a simplified register type-flow check
(uninitialized refs, int vs reference use, undefined registers).
"""
import hashlib
import struct
import sys
import zlib

OPN = {0x00: ('nop', '10x'), 0x0a: ('move-result', '11x'), 0x0c: ('move-result-object', '11x'),
       0x0d: ('move-exception', '11x'), 0x0e: ('return-void', '10x'), 0x0f: ('return', '11x'),
       0x11: ('return-object', '11x'), 0x12: ('const/4', '11n'), 0x13: ('const/16', '21s'),
       0x14: ('const', '31i'), 0x15: ('const/high16', '21h'), 0x16: ('const-wide/16', '21s'), 0x1a: ('const-string', '21c'),
       0x1c: ('const-class', '21c'), 0x1f: ('check-cast', '21c'), 0x22: ('new-instance', '21c'),
       0x29: ('goto/16', '20t'), 0x32: ('if-eq', '22t'), 0x33: ('if-ne', '22t'), 0x34: ('if-lt', '22t'),
       0x35: ('if-ge', '22t'), 0x36: ('if-gt', '22t'), 0x37: ('if-le', '22t'), 0x38: ('if-eqz', '21t'),
       0x39: ('if-nez', '21t'), 0x3a: ('if-ltz', '21t'), 0x3b: ('if-gez', '21t'), 0x3c: ('if-gtz', '21t'),
       0x3d: ('if-lez', '21t'), 0x54: ('iget-object', '22c'), 0x5b: ('iput-object', '22c'),
       0x62: ('sget-object', '21c'), 0x63: ('sget-boolean', '21c'), 0x6a: ('sput-boolean', '21c'),
       0x6e: ('invoke-virtual', '35c'), 0x6f: ('invoke-super', '35c'), 0x70: ('invoke-direct', '35c'),
       0x71: ('invoke-static', '35c'), 0x72: ('invoke-interface', '35c'), 0xd8: ('add-int/lit8', '22b')}
UNITS = {'10x': 1, '11x': 1, '11n': 1, '21s': 2, '21h': 2, '31i': 3, '21c': 2, '20t': 2, '22t': 2,
         '21t': 2, '22c': 2, '35c': 3, '22b': 2}

errors = []


def err(msg):
    errors.append(msg)


def uleb(b, p):
    r = s = 0
    while True:
        x = b[p]; p += 1
        r |= (x & 0x7f) << s
        s += 7
        if not x & 0x80:
            return r, p


def sleb(b, p):
    r = s = 0
    while True:
        x = b[p]; p += 1
        r |= (x & 0x7f) << s
        s += 7
        if not x & 0x80:
            if x & 0x40:
                r -= 1 << s
            return r, p


def main(path, quiet=False):
    b = open(path, 'rb').read()
    if b[:8] != b'dex\n035\x00':
        err('bad magic')
    if struct.unpack_from('<I', b, 8)[0] != zlib.adler32(b[12:]) & 0xffffffff:
        err('bad checksum')
    if b[12:32] != hashlib.sha1(b[32:]).digest():
        err('bad signature')
    (fsize, hsize, endian, lsize, loff, map_off, ns, os_, nt, ot, np_, op, nf, of, nm, om, nc, oc, dsize, doff) = \
        struct.unpack_from('<20I', b, 32)
    if fsize != len(b): err('file_size')
    if hsize != 0x70 or endian != 0x12345678: err('header')
    if doff + dsize != len(b): err('data section must end at EOF (got %d+%d vs %d)' % (doff, dsize, len(b)))
    if dsize % 4: err('data_size not multiple of 4')

    def string(i):
        o = struct.unpack_from('<I', b, os_ + 4 * i)[0]
        n, p = uleb(b, o)
        e = b.index(b'\x00', p)
        return b[p:e].decode('utf-8')
    S = [string(i) for i in range(ns)]
    if S != sorted(S, key=lambda s: [ord(c) for c in s]): err('strings not sorted')
    if len(set(S)) != len(S): err('duplicate strings')
    T = [S[struct.unpack_from('<I', b, ot + 4 * i)[0]] for i in range(nt)]
    tsi = [struct.unpack_from('<I', b, ot + 4 * i)[0] for i in range(nt)]
    if tsi != sorted(tsi) or len(set(tsi)) != len(tsi): err('types not sorted/unique')

    def tlist(o):
        if not o:
            return []
        if o % 4: err('type_list misaligned')
        n = struct.unpack_from('<I', b, o)[0]
        return [struct.unpack_from('<H', b, o + 4 + 2 * i)[0] for i in range(n)]
    P = []
    pkeys = []
    for i in range(np_):
        sh, rt, po = struct.unpack_from('<III', b, op + 12 * i)
        params = tlist(po)
        P.append((T[rt], [T[x] for x in params], S[sh]))
        pkeys.append((rt, params))
        exp = ''.join('L' if t[0] in 'L[' else t for t in [T[rt]] + [T[x] for x in params])
        if exp != S[sh]: err('shorty mismatch %s %s' % (exp, S[sh]))
    if pkeys != sorted(pkeys): err('protos not sorted')
    F = []
    fk = []
    for i in range(nf):
        c, t, n = struct.unpack_from('<HHI', b, of + 8 * i)
        F.append('%s->%s:%s' % (T[c], S[n], T[t]))
        fk.append((c, n, t))
    if fk != sorted(fk): err('fields not sorted')
    M = []
    mk = []
    MP = []
    for i in range(nm):
        c, p, n = struct.unpack_from('<HHI', b, om + 8 * i)
        M.append('%s->%s(%s)%s' % (T[c], S[n], ''.join(P[p][1]), P[p][0]))
        MP.append(P[p])
        mk.append((c, n, p))
    if mk != sorted(mk): err('methods not sorted')

    # map list
    n = struct.unpack_from('<I', b, map_off)[0]
    prev = -1
    for i in range(n):
        t, _, cnt, o = struct.unpack_from('<HHII', b, map_off + 4 + 12 * i)
        if o <= prev: err('map not sorted')
        prev = o
        if t in (0x2001, 0x1001, 0x1003, 0x2006, 0x1000) and o % 4: err('section %x misaligned' % t)

    out = []
    for ci in range(nc):
        (cidx, acc, sup, ioff, src, aoff, cdo, svo) = struct.unpack_from('<8I', b, oc + 32 * ci)
        out.append('.class %s %s extends %s implements %s' % (hex(acc), T[cidx], T[sup], [T[x] for x in tlist(ioff)]))
        annotated = {}
        if aoff:
            if aoff % 4: err('annotations dir misaligned')
            ca, fs, ms, ps = struct.unpack_from('<4I', b, aoff)
            for k in range(ms):
                midx, setoff = struct.unpack_from('<II', b, aoff + 16 + 8 * k)
                if setoff % 4: err('ann set misaligned')
                sn = struct.unpack_from('<I', b, setoff)[0]
                names = []
                for j in range(sn):
                    io = struct.unpack_from('<I', b, setoff + 4 + 4 * j)[0]
                    vis = b[io]
                    ti, p2 = uleb(b, io + 1)
                    sz, p2 = uleb(b, p2)
                    names.append('%s(vis=%d,elems=%d)' % (T[ti], vis, sz))
                annotated[midx] = names
        p = cdo
        sfs, p = uleb(b, p); ifs, p = uleb(b, p); dms, p = uleb(b, p); vms, p = uleb(b, p)
        for cnt, kind in ((sfs, 'static'), (ifs, 'instance')):
            idx = 0
            for _ in range(cnt):
                d, p = uleb(b, p); a, p = uleb(b, p)
                idx += d
                out.append('  .field %s %s %s' % (kind, hex(a), F[idx]))
        for cnt, kind in ((dms, 'direct'), (vms, 'virtual')):
            idx = 0
            for _ in range(cnt):
                d, p = uleb(b, p); a, p = uleb(b, p); co, p = uleb(b, p)
                idx += d
                if not M[idx].startswith(T[cidx] + '->'): err('method not owned by class: ' + M[idx])
                out.append('  .method %s %s %s %s' % (kind, hex(a), M[idx], annotated.get(idx, '')))
                if co:
                    out += disasm(b, co, S, T, F, M, MP, M[idx], a, T[cidx])
    if not quiet:
        print('\n'.join(out))
    return errors


def disasm(b, co, S, T, F, M, MP, mname, acc, cls):
    out = []
    if co % 4: err('code item misaligned ' + mname)
    regs, ins, outs, tries, dbg, isz = struct.unpack_from('<HHHHII', b, co)
    u = struct.unpack_from('<%dH' % isz, b, co + 16)
    out.append('    .registers %d ins %d outs %d tries %d' % (regs, ins, outs, tries))
    pc = 0
    instrs = {}
    max_outs = 0
    while pc < isz:
        w = u[pc]
        opc = w & 0xff
        if opc not in OPN:
            err('unknown opcode %x in %s' % (opc, mname)); break
        name, fmt = OPN[opc]
        A = (w >> 8) & 0xff
        d = {'op': name, 'fmt': fmt}
        if fmt == '11x':
            d['regs'] = [A]
        elif fmt == '11n':
            d['regs'] = [A & 0xf]; v = A >> 4; d['lit'] = v - 16 if v > 7 else v
        elif fmt == '21s':
            d['regs'] = [A]; v = u[pc + 1]; d['lit'] = v - 65536 if v > 32767 else v
        elif fmt == '21h':
            d['regs'] = [A]; d['lit'] = u[pc + 1] << 16
        elif fmt == '31i':
            d['regs'] = [A]; d['lit'] = u[pc + 1] | (u[pc + 2] << 16)
        elif fmt == '21c':
            d['regs'] = [A]; i = u[pc + 1]
            d['ref'] = S[i] if name == 'const-string' else (T[i] if name in ('const-class', 'check-cast', 'new-instance') else F[i])
        elif fmt == '20t':
            v = u[pc + 1]; d['target'] = pc + (v - 65536 if v > 32767 else v)
        elif fmt == '22t':
            d['regs'] = [A & 0xf, A >> 4]; v = u[pc + 1]; d['target'] = pc + (v - 65536 if v > 32767 else v)
        elif fmt == '21t':
            d['regs'] = [A]; v = u[pc + 1]; d['target'] = pc + (v - 65536 if v > 32767 else v)
        elif fmt == '22c':
            d['regs'] = [A & 0xf, A >> 4]; d['ref'] = F[u[pc + 1]]
        elif fmt == '22b':
            d['regs'] = [A, u[pc + 1] & 0xff]; v = u[pc + 1] >> 8; d['lit'] = v - 256 if v > 127 else v
        elif fmt == '35c':
            cnt = A >> 4; g = A & 0xf; x = u[pc + 2]
            rr = [x & 0xf, (x >> 4) & 0xf, (x >> 8) & 0xf, (x >> 12) & 0xf, g][:cnt]
            d['regs'] = rr; d['ref'] = M[u[pc + 1]]; d['proto'] = MP[u[pc + 1]]
            max_outs = max(max_outs, cnt)
        for r in d.get('regs', []):
            if r >= regs: err('%s: register v%d out of range at %d' % (mname, r, pc))
        instrs[pc] = d
        text = '      %04x: %s %s %s %s %s' % (pc, name, ','.join('v%d' % r for r in d.get('regs', [])),
                                             d.get('ref', ''), d.get('lit', ''), ('-> %04x' % d['target']) if 'target' in d else '')
        out.append(text.rstrip())
        pc += UNITS[fmt]
    if pc != isz: err('insns size mismatch ' + mname)
    if max_outs > outs: err('outs too small ' + mname)
    for d in instrs.values():
        if 'target' in d and d['target'] not in instrs: err('bad branch target in ' + mname)
    # tries
    handlers = []
    if tries:
        p = co + 16 + 2 * isz
        if isz % 2:
            p += 2
        tl = []
        for i in range(tries):
            s, n, h = struct.unpack_from('<IHH', b, p + 8 * i)
            tl.append((s, n, h))
        hbase = p + 8 * tries
        for (s, n, h) in tl:
            q = hbase + h
            size, q = sleb(b, q)
            typed = []
            for _ in range(abs(size)):
                ti, q = uleb(b, q); ad, q = uleb(b, q); typed.append((T[ti], ad))
            ca = None
            if size <= 0:
                ca, q = uleb(b, q)
            out.append('    .try %04x..%04x catch %s catchall %s' % (s, s + n, typed, ('%04x' % ca) if ca is not None else None))
            if ca not in instrs: err('bad handler addr ' + mname)
            if s not in instrs or (s + n not in instrs and s + n != isz): err('bad try range ' + mname)
            handlers.append((s, s + n, ca))
    typeflow(instrs, regs, ins, mname, acc, cls, handlers, isz)
    return out


def typeflow(instrs, regs, ins, mname, acc, cls, handlers, isz):
    """Very small abstract interpreter: types are 'int', 'zero', ('ref', T), ('uninit', T, pc), None=undefined."""
    params = []
    sig = mname.split('(', 1)[1]
    ptypes_s, ret = sig.rsplit(')', 1)
    i = 0
    plist = []
    while i < len(ptypes_s):
        j = i
        while ptypes_s[j] == '[': j += 1
        if ptypes_s[j] == 'L': j = ptypes_s.index(';', j)
        plist.append(ptypes_s[i:j + 1]); i = j + 1
    is_static = bool(acc & 0x8)
    is_ctor = '-><init>' in mname
    start = [None] * regs
    r = regs - ins
    if not is_static:
        start[r] = ('uninit-this', cls) if is_ctor else ('ref', cls); r += 1
    for t in plist:
        start[r] = ('ref', t) if t[0] in 'L[' else 'int'; r += 1

    def is_ref(x):
        return x == 'zero' or (isinstance(x, tuple) and x[0] == 'ref')

    def merge(a, b2):
        if a == b2: return a
        if a is None or b2 is None: return 'conflict'
        if is_ref(a) and is_ref(b2):
            if a == 'zero': return b2
            if b2 == 'zero': return a
            return ('ref', 'Ljava/lang/Object;')
        if a in ('int', 'zero') and b2 in ('int', 'zero'): return 'int'
        return 'conflict'

    states = {0: start}
    work = [0]
    pcs = sorted(instrs)
    nxt = {pcs[k]: (pcs[k + 1] if k + 1 < len(pcs) else None) for k in range(len(pcs))}
    visits = 0
    while work:
        visits += 1
        if visits > 10000: err('typeflow did not converge ' + mname); return
        pc = work.pop()
        st = list(states[pc])
        d = instrs[pc]
        op = d['op']
        rr = d.get('regs', [])
        succ = []
        pending_result = None

        def need(reg, kind):
            v = st[reg]
            ok = (kind == 'int' and v in ('int', 'zero')) or (kind == 'ref' and is_ref(v)) or \
                 (kind == 'any' and v not in (None, 'conflict'))
            if not ok:
                err('%s @%04x %s: v%d expected %s got %s' % (mname, pc, op, reg, kind, v))

        if op in ('const/4', 'const/16', 'const', 'const/high16'):
            st[rr[0]] = 'zero' if d['lit'] == 0 else 'int'
        elif op == 'const-wide/16':
            st[rr[0]] = 'wide'; st[rr[0] + 1] = 'wide-hi'
        elif op == 'const-string':
            st[rr[0]] = ('ref', 'Ljava/lang/String;')
        elif op == 'const-class':
            st[rr[0]] = ('ref', 'Ljava/lang/Class;')
        elif op == 'new-instance':
            st[rr[0]] = ('uninit', d['ref'], pc)
        elif op == 'check-cast':
            need(rr[0], 'ref'); st[rr[0]] = ('ref', d['ref'])
        elif op in ('iget-object',):
            need(rr[1], 'ref'); st[rr[0]] = ('ref', d['ref'].split(':', 1)[1])
        elif op == 'iput-object':
            need(rr[0], 'ref'); need(rr[1], 'ref')
            if is_ctor and st[rr[1]] == ('uninit-this', cls):
                pass
        elif op == 'sget-object':
            st[rr[0]] = ('ref', d['ref'].split(':', 1)[1])
        elif op == 'sget-boolean':
            st[rr[0]] = 'int'
        elif op == 'sput-boolean':
            need(rr[0], 'int')
        elif op.startswith('invoke-'):
            ret_t, ptypes, _ = d['proto']
            k = 0
            if op != 'invoke-static':
                v = st[rr[0]]
                if op == 'invoke-direct' and '-><init>' in d['ref']:
                    if not (isinstance(v, tuple) and v[0] in ('uninit', 'uninit-this')):
                        err('%s @%04x: <init> on initialized/undefined v%d (%s)' % (mname, pc, rr[0], v))
                    else:
                        newt = ('ref', v[1])
                        st = [newt if x == v else x for x in st]
                else:
                    need(rr[0], 'ref')
                k = 1
            for t in ptypes:
                if t in ('J', 'D'):
                    if st[rr[k]] != 'wide' or st[rr[k + 1]] != 'wide-hi':
                        err('%s @%04x %s: v%d expected wide pair' % (mname, pc, op, rr[k]))
                    k += 2
                    continue
                need(rr[k], 'ref' if t[0] in 'L[' else 'int'); k += 1
            if ret_t != 'V':
                pending_result = ('ref', ret_t) if ret_t[0] in 'L[' else 'int'
        elif op in ('move-result', 'move-result-object'):
            pass
        elif op == 'add-int/lit8':
            need(rr[1], 'int'); st[rr[0]] = 'int'
        elif op in ('if-eqz', 'if-nez'):
            need(rr[0], 'any')
        elif op in ('if-ltz', 'if-gez', 'if-gtz', 'if-lez'):
            need(rr[0], 'int')
        elif op in ('if-eq', 'if-ne', 'if-lt', 'if-ge', 'if-gt', 'if-le'):
            need(rr[0], 'any'); need(rr[1], 'any')
        elif op == 'return':
            need(rr[0], 'int')
            if ret not in ('Z', 'I'): err('%s: return type mismatch' % mname)
        elif op == 'return-object':
            need(rr[0], 'ref')
            if ret[0] not in 'L[': err('%s: return-object in non-object method' % mname)
        elif op == 'return-void':
            if ret != 'V': err('%s: return-void in non-void method' % mname)
            if is_ctor and any(x == ('uninit-this', cls) for x in st):
                err('%s: constructor returns without calling super <init>' % mname)
        # move-result must directly follow an invoke with a result
        n = nxt[pc]
        if n is not None and instrs[n]['op'] in ('move-result', 'move-result-object'):
            if pending_result is None:
                err('%s @%04x: move-result without result-producing invoke' % (mname, n))
            else:
                want = 'move-result-object' if pending_result != 'int' else 'move-result'
                if instrs[n]['op'] != want:
                    err('%s @%04x: wrong move-result kind' % (mname, n))
                st2 = list(st)
                st2[instrs[n]['regs'][0]] = pending_result
                succ_state_after = st2
                # skip over the move-result instruction
                after = nxt[n]
                tgt_list = [(after, succ_state_after)] if after is not None else []
                for (s, e, h) in handlers:
                    if s <= pc < e:
                        tgt_list.append((h, st))
                for (t, s_) in tgt_list:
                    push(states, work, t, s_, merge)
                continue
        if op in ('return', 'return-object', 'return-void'):
            pass
        elif op == 'goto/16':
            succ.append(d['target'])
        elif op.startswith('if-'):
            succ += [d['target'], n]
        else:
            if n is None:
                err('%s: falls off end of code' % mname)
            else:
                succ.append(n)
        for (s, e, h) in handlers:
            if s <= pc < e and op not in ('const/4', 'const/16', 'const', 'const/high16', 'const-wide/16', 'goto/16', 'return', 'return-void', 'move-result', 'move-result-object'):
                push(states, work, h, states[pc], merge)
        for t in succ:
            if t is None:
                err('%s: falls off end' % mname); continue
            push(states, work, t, st, merge)


def push(states, work, t, st, merge):
    if t not in states:
        states[t] = list(st)
        work.append(t)
    else:
        old = states[t]
        new = [merge(a, b) for a, b in zip(old, st)]
        if new != old:
            states[t] = new
            work.append(t)


if __name__ == '__main__':
    e = main(sys.argv[1], quiet='-q' in sys.argv)
    print('\nERRORS:' if e else '\nOK: no structural/type errors found')
    for x in e:
        print('  ', x)
