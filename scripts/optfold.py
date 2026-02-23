#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Folds a cheat output file grouping identical cheats into a single one.

import sys, os, json, argparse, re, hashlib

parser = argparse.ArgumentParser(prog='cht_fold')
parser.add_argument('--input', dest='infiles', nargs='+', help='List of files to process')
parser.add_argument('--gamecodes', dest='gcodes', default=None, help='JSON map of game ids and files')
parser.add_argument('--outfile', dest='outfile', required=True, help='Output path in JSON format')
args = parser.parse_args()

import os

def choose_base_name(names):
  if len(names) == 1:
    return names[0]

  prefix = os.path.commonprefix(names)

  if prefix and prefix[-1] == '(':
    base = prefix[:-1].strip()
  else:
    # Titles differ → prefer USA version
    preferred = next((n for n in names if "USA" in n), names[0])
    cut = max(preferred.rfind("("), preferred.rfind("["))
    base = preferred[:cut].rstrip() if cut != -1 else preferred

  # Remove existing extension if present
  if base.lower().endswith(".gba"):
    base = base[:-4]

  return base + ".gba"

gmap = {}
if args.gcodes:
  gmap = json.load(open(args.gcodes))

chtl = []
for f in args.infiles:
  chtl += json.load(open(f))

chtm = {}
for c in chtl:
  codes = sorted(c["codes"], key=lambda x: (x["title"], x["code"]))
  fp = hashlib.sha256((";".join(x["title"] + "|" + x["code"] for x in codes)).encode("utf-8")).hexdigest()
  if fp not in chtm:
    chtm[fp] = []
  if c["game-codes"][0] in gmap:
    c["filename"] = gmap[c["game-codes"][0]]
  chtm[fp].append(c)

print("Loaded %d cheats and merged into %d cheats" % (len(chtl), len(chtm)))

chtl = []
for chts in chtm.values():
  gamecodes = set()
  for e in chts:
    gamecodes |= set(e['game-codes'])
  gamecodes = sorted(gamecodes)

  chtl.append(chts[0])
  chtl[-1]['game-codes'] = gamecodes
  chtl[-1]['filename'] = choose_base_name([x['filename'] for x in chts])

chtl = sorted(chtl, key=lambda x: (x["filename"], x["game-codes"][0]))

with open(args.outfile, "w") as ofd:
  ofd.write(json.dumps(chtl, indent=2))

