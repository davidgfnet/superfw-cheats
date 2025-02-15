#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# libretro cheat conversion scripts
# Will read cheats, disregard certain codes (ie. master hook) and output
# a SuperFW-friendly cheat file.
# It performs some sanity checking too.

import sys, os, json, argparse, re

parser = argparse.ArgumentParser(prog='cht_conv')
parser.add_argument('--input', dest='infiles', nargs='+', help='List of files to process')
parser.add_argument('--outfile', dest='outfile', required=True, help='Output path in JSON format')
args = parser.parse_args()

BAD_CHARSET = 1
BAD_FORMAT  = 2
BAD_OPCODE  = 3
BAD_ADDR    = 4
BAD_LEN     = 5

def inrange(addr, minaddr, maxaddr):
  return addr >= minaddr and addr <= maxaddr

def decode(s):
  if any(x not in "0123456789ABCDEFabcdef +:" for x in s):
    return BAD_CHARSET

  # Parse the codes and check them.
  s = s.replace("+", " ").replace(":", " ")
  l = s.strip().split(" ")

  # The format can be ABCD01234+EF89 or ABCD01234EF89
  # We validate and accept both

  codelens = sorted(set([len(x) for x in l]))
  if codelens != [4, 8] and codelens != [12]:
    return BAD_FORMAT

  # Ensure they come in pairs
  if codelens == [4, 8]:
    if len(l) % 2 != 0:
      return BAD_FORMAT
    if any(len(x) != [8, 4][i % 2] for i, x in enumerate(l)):
      return BAD_FORMAT

    return [{"addr": int(l[i], 16), "value": int(l[i+1], 16)} for i in range(0, len(l), 2)]
  else:
    return [{"addr": int(x[0:8], 16), "value": int(x[8:12], 16)} for x in l]

def encode(codes):
  return " ".join("%08X+%04X" % (c["addr"], c["value"]) for c in codes)

def filter_master(codes):
  ret = []
  i = 0
  while i < len(codes):
    c = codes[i]

    op = c["addr"] >> 28

    if op == 0 or op == 1:
      i += 1    # Skip
    elif op == 4:
      ret.append(codes[i])
      ret.append(codes[i+1])
      i += 2
    elif op == 5:
      ret.append(codes[i])
      i += 1
      numc = (c["value"] + 5) // 6

      for j in range(numc):
        ret.append(codes[i])
        i += 1
    else:
      ret.append(codes[i])
      i += 1

  return ret

def validate_code(codes):
  i = 0
  while i < len(codes):
    c = codes[i]
    i += 1

    op = c["addr"] >> 28
    if op == 9:
      return BAD_OPCODE

    # Skip payload/data
    if op == 4:
      i += 1
    elif op == 5:
      numd = (c["value"] + 5) // 6
      if i + numd >= len(codes):
        return BAD_LEN
      i += numd

    # Validate that addresses are in RAM
    if op not in [13, 0, 1]:
      if (not inrange(c["addr"] & 0xFFFFFFF, 0x03000000, 0x03007fff) and
          not inrange(c["addr"] & 0xFFFFFFF, 0x02000000, 0x0203ffff) and
          not inrange(c["addr"] & 0xFFFFFFF, 0x04000000, 0x040003ff) and
          not inrange(c["addr"] & 0xFFFFFFF, 0x05000000, 0x050003ff) and
          not inrange(c["addr"] & 0xFFFFFFF, 0x06000000, 0x06017fff) and
          not inrange(c["addr"] & 0xFFFFFFF, 0x07000000, 0x070003ff)):
        return BAD_ADDR

  return 0

chtl = []
for f in args.infiles:
  cht = {
    "filename": os.path.basename(f),
    "game-codes": [],
    "codes": [],
  }
  desc = None
  for line in open(f, "r").read().split("\n"):
    m = re.match('cheat[0-9]+_desc[ ]*=[ ]*"(.*)"', line.strip())
    if m:
      desc = m.group(1)
    m = re.match('cheat[0-9]+_code[ ]*=[ ]*"([^"]+)"', line.strip())
    if m:
      code = m.group(1)
      assert desc is not None

      dcode = decode(code)
      if dcode == BAD_CHARSET:
        print("Bad character in cheat code", f, code)
      elif dcode == BAD_FORMAT:
        print("Bad cheat format", f, code)
      else:
        # Validate that the code is fine
        err = validate_code(dcode)
        if err == BAD_OPCODE:
          print("Invalid opcode!", f, code)
        elif err == BAD_ADDR:
          print("Invalid addr!", f, code)
        elif err == BAD_LEN:
          print("Invalid opcode length!", f, code)
        else:
          # Filter out the enable codes
          dcode = filter_master(dcode)

          if dcode:
            reencoded = encode(dcode)
            cht["codes"].append({"title": desc, "code": reencoded})

      desc = None
  chtl.append(cht)

  with open(args.outfile, "w") as ofd:
    ofd.write(json.dumps(chtl, indent=2))

