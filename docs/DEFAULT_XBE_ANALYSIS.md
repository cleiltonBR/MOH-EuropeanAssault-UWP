# DEFAULT.XBE — structural analysis

This report records metadata extracted from the user's privately supplied XBE. The binary itself is not included in this repository.

## File identity

- File name: `default.xbe`
- File size: 3,686,400 bytes (3.52 MiB)
- SHA-256: `5a34d7f3a38293178c34865dc60819b0796f17e1c7091722079cf075d33335e8`
- Header magic: `XBEH`

## Header and certificate

| Field | Value |
|---|---:|
| Title | MOH European Assault |
| Title ID | `0x4541005E` |
| XBE base address | `0x00010000` |
| XBE entry point (decoded) | `0x001EF095` |
| Encoded entry point | `0xA8E2A73E` |
| Header size | 2,528 bytes |
| Image virtual size | 5,444,768 bytes |
| Number of sections | 12 |
| Certificate size | 492 bytes |
| Header timestamp (UTC) | 2005-05-11 20:26:42 |
| Certificate timestamp (UTC) | 2005-05-17 19:55:55 |

The decoded entry point matches the address already configured in `source/mygame/src/main.c` (`YOUR_GAME_ENTRY_POINT 0x001EF095`). This confirms that the existing constant agrees with the supplied XBE header; it does not yet validate the generated C entry point or game startup.

## Section map

| Section | Virtual address | Virtual size | Raw file offset | Raw size |
|---|---:|---:|---:|---:|
| .text | `0x00011000` | 2,912,876 | `0x00001000` | 2,912,876 |
| D3D | `0x002D8280` | 80,568 | `0x002C9000` | 66,032 |
| DSOUND | `0x002EBD40` | 37,884 | `0x002DA000` | 37,260 |
| XGRPH | `0x002F5140` | 5,577 | `0x002E4000` | 5,576 |
| XPP | `0x002F6720` | 32,392 | `0x002E6000` | 32,392 |
| .rdata | `0x002FE5C0` | 356,080 | `0x002EE000` | 356,064 |
| .data | `0x003554C0` | 1,970,364 | `0x00345000` | 197,604 |
| DOLBY | `0x00536580` | 29,056 | `0x00376000` | 29,036 |
| $$XTINFO | `0x0053D700` | 178 | `0x0037E000` | 178 |
| $$XTIMAGE | `0x0053D7C0` | 10,240 | `0x0037F000` | 10,240 |
| $$XSIMAGE | `0x0053FFC0` | 4,096 | `0x00382000` | 4,096 |
| .XTLID | `0x00540FC0` | 1,232 | `0x00383000` | 1,232 |

## What this establishes

- The supplied file is structurally an Xbox executable (XBEH) and identifies itself as MOH European Assault.
- The configured XBE entry-point constant in the host source matches the decoded header entry point.
- The executable contains 12 mapped sections, including the game code and Xbox graphics/audio-related sections.

## What this does not establish

- No disassembly, function discovery, ABI recovery or C recompilation has been run yet.
- No kernel import/thunk inventory has been validated yet.
- No game data directory (textures, levels, movies, audio and other assets) was supplied with this XBE.
- No UWP build, package, deployment or Xbox execution has been performed.

## Recompilation prerequisites and next pipeline

The repository's `source/xboxrecomp-0.16.0/docs/GETTING_STARTED.md` defines the required order:

1. Parse XBE and write the JSON analysis file.
2. Disassemble the XBE text section and produce function/xref inventories.
3. Identify linked library functions.
4. Recover calling conventions and ABI signatures (required; the guide warns that skipping this step silently falls back to incorrect generic signatures).
5. Recompile all functions into `source/mygame/src/recomp/gen/`.
6. Reapply the port-specific edits recorded in `source/gen_hand_edits.txt`.

The pipeline requires Python 3.10+ and Capstone. The current execution environment does not have Capstone installed, so this report deliberately stops at verified structural parsing rather than claiming that the full recompilation has completed.

## Privacy and repository handling

The XBE binary remains outside Git. Only structural metadata and its SHA-256 are recorded here. Do not add the user's XBE or copyrighted game assets to public commits, Actions artifacts, or release packages.
