#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# EZ Omega (ie. DeadSkullzJr's cheats) cheat conversion script
# Reads and processes codes and generates some usable output
# It tries to perform some sanity checking too.

import sys, os, json, argparse, re

parser = argparse.ArgumentParser(prog='cht_conv')
parser.add_argument('--input', dest='infiles', nargs='+', help='List of files to process')
parser.add_argument('--g2i', dest='mapfile', required=True, help='File map (gameid to cheat)')
parser.add_argument('--outfile', dest='outfile', required=True, help='Output path in JSON format')
args = parser.parse_args()

def decode(s):
  # Parse the codes and check them.
  l = s.strip().split(";")

  # The format is ADDR,VAL1,VAL2... tho it seems we only have one or two.
  ret = []
  for e in l:
    addr, *vals = e.split(",")

    addrv = int(addr, 16)
    valsv = [int(x,16) for x in vals]
    if addrv >= 0x02000000 and addrv < 0x02100000:
      # Wrongly encoded EWRAM address?
      print("Warn: potential bad EWRAM addr '0x%x'" % addrv, file=sys.stderr)
      addrv = (addrv - 0x02000000) % 0x40000
    elif addrv >= 0x03000000 and addrv < 0x03100000:
      # Wrongly encoded IWRAM address?
      print("Warn: potential bad IWRAM addr '0x%x'" % addrv, file=sys.stderr)
      addrv = ((addrv - 0x03000000) % 0x8000) + 0x40000
    elif addrv >= 0x48000:  # 256KiB + 32KiB
      print("Warn: potential bad addr '0x%x'" % addrv, file=sys.stderr)
      addrv = ((addrv - 0x40000) % 0x8000) + 0x40000       # Mirror IWRAM
    if any(x > 0xFF for x in valsv):  # Must be bytes
      return None

    ret.append({"addr": addrv, "values": valsv})

  return ret

def optimize(chts):
  # Sort cheats and try to merge them
  chts = sorted(chts, key=lambda x: x["addr"])
  ret = []
  for c in chts:
    if ret and ret[-1]["addr"] + len(ret[-1]["values"]) == c["addr"]:
      ret[-1]["values"] += c["values"]
    else:
      ret.append(c)
  return ret

def convaddr(addr):
  # Addresses are expressed as EWRAM+IWRAM offsets:
  if addr >= 0x40000:
    return 0x03000000 | (addr & 0x7FFF)
  return 0x02000000 | (addr & 0x3FFFF)

def cencode(cheats):
  ret = []
  for c in cheats:
    addr = convaddr(c["addr"])
    vs = c["values"]

    # Expand 1-5 byte writes using simple sequences for readability
    if len(vs) == 1:
      ret.append({"addr": 0x30000000 | addr, "value": vs[0]})
    elif len(vs) == 2:
      ret.append({"addr": 0x80000000 | addr, "value": vs[0] | (vs[1] << 8)})
    elif len(vs) == 3:
      ret.append({"addr": 0x80000000 | addr,     "value": vs[0] | (vs[1] << 8)})
      ret.append({"addr": 0x30000000 | addr + 2, "value": vs[2]})
    elif len(vs) == 4:
      ret.append({"addr": 0x80000000 | addr,     "value": vs[0] | (vs[1] << 8)})
      ret.append({"addr": 0x80000000 | addr + 2, "value": vs[2] | (vs[3] << 8)})
    elif len(vs) == 5:
      ret.append({"addr": 0x80000000 | addr,     "value": vs[0] | (vs[1] << 8)})
      ret.append({"addr": 0x80000000 | addr + 2, "value": vs[2] | (vs[3] << 8)})
      ret.append({"addr": 0x30000000 | addr + 4, "value": vs[4]})

    elif len(vs) % 2 == 0 and all(vs[i] == vs[i % 2] for i in range(len(vs))):
      # A 16 bit fill, use a sliding code with increments = 0
      ret.append({"addr": 0x40000000 | addr, "value": vs[0] | (vs[1] << 8)})
      ret.append({"addr": len(vs) // 2, "value": 0})

    # TODO: Implement incremental sequences using sliding codes (like 1, 2, 3...)

    else:
      # If it's an odd size buffer, we take the last byte and write it at the end.
      lastb = None
      if len(vs) % 2:
        lastb = (addr + len(vs) - 1, vs[-1])
        vs = vs[:-1]

      # Use a supercode to write a sequence of 16 bit values
      ret.append({"addr": 0x50000000 | addr, "value": len(vs) // 2})
      vs16 = [vs[i+1] | (vs[i] << 8) for i in range(0, len(vs), 2)]
      for i in range(0, len(vs16), 3):
        v1 = vs16[i]
        v2 = vs16[i+1] if i + 1 < len(vs16) else 0
        v3 = vs16[i+2] if i + 2 < len(vs16) else 0
        ret.append({"addr": (v1 << 16) | v2, "value": v3})

      if lastb:
        ret.append({"addr": 0x30000000 | lastb[0], "value": lastb[1]})

  return ret

def encode(codes):
  return " ".join("%08X+%04X" % (c["addr"], c["value"]) for c in codes)

# Process map file
gmap = {}
rawm = open(args.mapfile).read().strip()
for i in range(0, len(rawm), 8):
  gameid, chtn = rawm[i:i+4], rawm[i+4:i+8]
  gmap[chtn] = gameid

chtl = []
for f in args.infiles:
  cht = {
    "filename": os.path.basename(f),
    "game-codes": [],
    "codes": [],
  }

  m = re.search("([0-9]+)\\.cht", f)
  if m:
    gid = gmap.get(m.group(1), None)
    if gid:
      cht["game-codes"].append(gid + "-00")

  desc = None
  for line in open(f, "r").read().split("\n"):
    m = re.match('\\[(.*)\\]', line.strip())
    if m:
      desc = m.group(1)
      if desc.lower() == "gameinfo":
        desc = None

    m = re.match('Switch=([A-Fa-f0-9,;]+)', line.strip())
    if m:
      code = m.group(1)
      assert desc is not None

      dcode = decode(code)
      if dcode is None:
        print("Bad cheat format", f, code, file=sys.stderr)
      else:
        # Optimize cheats
        dcode = optimize(dcode)
        # Encode using codebreaker format
        c = cencode(dcode)
        cht["codes"].append({"title": desc, "code": encode(c)})

      desc = None
  chtl.append(cht)

with open(args.outfile, "w") as ofd:
  ofd.write(json.dumps(chtl, indent=2))

