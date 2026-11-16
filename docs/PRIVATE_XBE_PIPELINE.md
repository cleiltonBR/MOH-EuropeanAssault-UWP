# Private XBE recompilation

The XBE and all generated game-specific C must remain on the owner's machine. Do not upload them to this public repository, Actions artifacts, or releases.

## Requirements

- Windows with PowerShell
- Python 3.10+ available through the `py -3` launcher
- Capstone: `py -3 -m pip install capstone`

## Run

From a PowerShell window, in the repository checkout:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\tools\run-private-xbe-pipeline.ps1 -XbePath "D:\Games\MOH European Assault\default.xbe"
```

The script runs the documented stages in order: XBE parse, disassembly, function identification, ABI recovery, and full C recompilation. It writes generated sources to `source/mygame/src/recomp/gen/` and intermediate analysis to the toolkit's local `tools/*/output/` folders. These paths are ignored by the repository's `.gitignore`.

The script uses `--exclude-manual` with `source/mygame/src/recomp_manual.c` so functions implemented by hand are not emitted again.

## Important limitation

The existing `source/gen_hand_edits.txt` is a record of line-specific edits from the existing generated tree. It is not a patch program. The runner deliberately does **not** apply those edits automatically: line-number-only replay could silently modify the wrong C statements if the generated output differs. Review and safely reapply each listed edit before attempting a full build.

This pipeline does not build a UWP package and does not prove that the game starts on Xbox. It only creates the private recompiled C input needed for the next integration stage.
