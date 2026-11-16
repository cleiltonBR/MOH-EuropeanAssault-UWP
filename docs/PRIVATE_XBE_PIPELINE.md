# Private XBE analysis and recompilation

The XBE and all generated game-specific C must stay out of this public repository. The supported cloud workflow is stored in the separate private repository:

- Private input repository: `cleiltonBR/MOH-EuropeanAssault-Private`
- Workflow: `.github/workflows/private-xbe-recompile.yml`
- Source checkout: this repository's `uwp/port-foundation` branch
- Private output: a GitHub Actions artifact in the private repository, retained for one day

## Run from a phone

1. Open the [private repository](https://github.com/cleiltonBR/MOH-EuropeanAssault-Private).
2. Open **Actions**.
3. Select **Private XBE analysis and recompilation**.
4. Tap **Run workflow**, keep the `main` branch selected, and confirm.
5. Wait for the run to finish. The workflow checks the XBE signature, parses the XBE, disassembles executable code, identifies functions, recovers ABI information, and runs the C recompiler.
6. If successful, download the artifact named `moh-european-assault-private-recomp` from that run in the private repository.

The workflow checks out this public source branch but does not copy the XBE or generated game code into it. The artifact is created only in the private repository and expires after one day.

## Important limitations

- A successful recompilation is not a UWP build and does not prove the game starts on Xbox.
- The existing `source/gen_hand_edits.txt` records edits made to a prior generated tree. It is not an automated patch. The workflow does not replay line-number edits, because that could silently alter the wrong code. We must compare and safely reapply the relevant edits before using generated code in a build.
- The workflow is a first cloud pipeline run. Its actual execution is still pending; do not treat the workflow file being committed as proof that the pipeline succeeded.
