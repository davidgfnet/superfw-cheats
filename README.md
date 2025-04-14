
Game Boy Advance - Cheats repo for SuperFW
==========================================

This repo contains CodeBreaker-compatible cheat codes to be used with SuperFW.

The cheats are under `cheats/` and are expressed in JSON format. They are
identified using GameID and version (in the `ABCD-EF` format) so that loaders
such as SuperFW can easily find them.

The packing script `scripts/pack-cheats.py` can be used to pack them in a ZIP
file. Each cheat is expanded (aka replicated) to all its GameID/versions. The
idea is that most games and versions will use the same (or compatible) cheats
so it makes no sense to replicate them per ID (the script takes care of that).

The script `scripts/conv-retro.py` can be used to convert libretro-formatted
cheats. This only works if the cheat codes are compatible (ie. Code Breaker).
There's an assumption that no master codes are required (cheats run on VBlank
and they do not feature a hooking function).

