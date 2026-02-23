#!/usr/bin/env python3

# Just lists filenames and game codes as map

import os
import sys
import json

directory = sys.argv[1]

result = {}

for name in os.listdir(directory):
    if not name.lower().endswith(".gba"):
        continue

    path = os.path.join(directory, name)
    if not os.path.isfile(path):
        continue

    with open(path, "rb") as f:
        f.seek(0x0AC)
        game_code = f.read(4).decode("ascii")

        f.seek(0x0BC)
        version = f.read(1)[0]

    key = f"{game_code}-{version:02X}"
    result[key] = name

print(json.dumps(result, indent=2))
