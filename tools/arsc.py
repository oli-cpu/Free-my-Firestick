"""Minimal resources.arsc writer: one package (0x7f), a few types, one config per type."""
import struct
from axml import _pool


def _config(density=0):
    cfg = bytearray(64)
    struct.pack_into('<I', cfg, 0, 64)
    struct.pack_into('<H', cfg, 14, density)   # ResTable_config.density
    return bytes(cfg)


def write(package_name, types):
    """types: ordered list of (type_name, density, [(entry_name, string_value)]).
    Every value is a string (file path or text). Returns (bytes, {"type/name": res_id})."""
    gstrings, ids = [], {}
    for (tname, dens, entries) in types:
        for (ename, val) in entries:
            if val not in gstrings:
                gstrings.append(val)
    keys = []
    for (tname, dens, entries) in types:
        for (ename, val) in entries:
            if ename not in keys:
                keys.append(ename)
    tnames = [t[0] for t in types]

    body = bytearray()
    for ti, (tname, dens, entries) in enumerate(types, start=1):
        n = len(entries)
        spec = struct.pack('<HHIBBHI', 0x0202, 16, 16 + 4 * n, ti, 0, 0, n) + bytes(4 * n)
        body += spec
        hsize = 20 + 64
        offsets, edata = [], bytearray()
        for ei, (ename, val) in enumerate(entries):
            offsets.append(len(edata))
            edata += struct.pack('<HHI', 8, 0, keys.index(ename))
            edata += struct.pack('<HBBI', 8, 0, 0x03, gstrings.index(val))
            ids['%s/%s' % (tname, ename)] = 0x7f000000 | (ti << 16) | ei
        estart = hsize + 4 * n
        tchunk = struct.pack('<HHIBBHII', 0x0201, hsize, estart + len(edata), ti, 0, 0, n, estart) + \
            _config(dens) + struct.pack('<%dI' % n, *offsets) + bytes(edata)
        body += tchunk

    tpool = _pool(tnames)
    kpool = _pool(keys)
    PKG_HDR = 288
    name16 = package_name.encode('utf-16le')[:254]
    name16 += bytes(256 - len(name16))
    type_off = PKG_HDR
    key_off = PKG_HDR + len(tpool)
    pkg = struct.pack('<HHII', 0x0200, PKG_HDR, PKG_HDR + len(tpool) + len(kpool) + len(body), 0x7f) + name16 + \
        struct.pack('<IIIII', type_off, len(tnames), key_off, len(keys), 0)
    assert len(pkg) == PKG_HDR
    pkg += tpool + kpool + body
    gpool = _pool(gstrings)
    table = struct.pack('<HHII', 0x0002, 12, 12 + len(gpool) + len(pkg), 1) + gpool + pkg
    return table, ids
