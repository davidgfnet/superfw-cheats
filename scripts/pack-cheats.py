#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Processes JSON cheats and produces a Super-FW compatible CodeBreaker cheats
# It wraps them nicely in a zipfile

import sys, os, json, argparse, zipfile

parser = argparse.ArgumentParser(prog='cht_write')
parser.add_argument('--input', dest='infiles', nargs='+', help='List of files to process')
parser.add_argument('--outfile', dest='outfile', required=True, help='Output path in ZIP format')
args = parser.parse_args()

with zipfile.ZipFile(args.outfile, "w") as ofd:
  for f in args.infiles:
    # Parse the JSON and produce a simple text file
    content = json.loads(open(f, "r").read())

    text = ""
    for entry in content["codes"]:
      text += entry["title"] + "\n" + entry["code"] + "\n"

    for code in content["game-codes"]:
      assert len(code) == 7
      ofd.writestr(code + ".cht", text.encode("utf-8"))



