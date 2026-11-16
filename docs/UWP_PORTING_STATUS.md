# Medal of Honor: European Assault — UWP port status

## Scope

This repository is the independent UWP/Xbox Series X Developer Mode effort. It is not the Android port.

The first target is a genuine UWP package that can be deployed to an Xbox Series X in Developer Mode. A successful desktop build is not evidence that the game runs on Xbox.

## Verified baseline

- The host is currently created with CMake as a conventional Win32 executable: `add_executable(... WIN32 ...)`.
- The game host entry point is `WinMain` in `source/mygame/src/main.c`.
- The host initializes the XBE memory layout, Xbox kernel replacement, kernel bridge, path redirection and then calls `xbe_entry_point()`.
- The current host uses desktop-oriented APIs for process/thread inspection, exception handling, CPU-set affinity, filesystem traversal, module/symbol inspection and message boxes.
- The runtime's platform CMake currently distinguishes ordinary Windows from POSIX; it has no dedicated UWP/Xbox platform target.
- The generated game C sources are intentionally absent from this repository. `source/README.md` documents an approximately 86 MB generated tree derived from the user's own `DEFAULT.XBE`, and notes that post-processing is not automated yet.

## Required implementation work

1. **UWP application host**
   - Replace the desktop `WinMain`/window assumptions with a UWP app lifecycle and a supported Xbox presentation path.
   - Keep game initialization behind a narrow host interface so diagnostics and desktop-only facilities can be excluded cleanly.
2. **Storage and XBE input**
   - Read the user's legally obtained game data from an app-accessible location (for example, the app's selected/imported game folder or packaged app data).
   - Store saves and writable state only in UWP app data.
   - Do not commit, package into this repository, or publish the user's `default.xbe` or game assets.
3. **Runtime platform layer**
   - Introduce an explicit UWP platform target in the runtime build.
   - Audit every Win32 dependency in kernel, D3D, audio, video, USB and input code; replace or conditionally compile unsupported APIs rather than assuming desktop Win32 availability.
4. **Graphics and input**
   - Verify D3D11 device creation and swap-chain/presentation APIs supported by Xbox UWP.
   - Route Xbox controller input through APIs available to UWP.
5. **Packaging and validation**
   - Produce an Xbox-targeted MSIX/AppX package with correct architecture, capabilities and manifest.
   - Deploy on an actual Xbox Series X Developer Mode device and validate XBE loading, kernel startup, first rendered frame, audio and controller input.

## Guardrails

- Keep all work on `uwp/port-foundation` until a verified milestone is ready; do not destabilize `main`.
- Do not treat a CMake configure or compile as proof of game initialization.
- Do not silently replace unsupported APIs with no-op stubs where they affect game behavior.
- The user's XBE is an input to the private generation/build process and must remain outside the public Git repository.
- The generated recompilation tree must be produced from the user's own XBE and post-processed according to `source/gen_hand_edits.txt` before a full game build can be considered complete.

## Current milestone

**Initial XBE analysis and recompilation completed; UWP runtime integration remains pending.**

The private GitHub Actions pipeline successfully parsed the user's XBE, disassembled its executable sections, identified functions, recovered ABI/signature data, and generated C output. The successful run reported:

- 21,149 total functions; 21,142 translated; 0 translation failures.
- 255 unresolved call-target stubs and 7 manual functions.
- 85 generated C chunks plus dispatch, declarations, types and unresolved-stub files.
- The first output artifact was retained privately; generated game code and the XBE remain outside this public repository.

These numbers describe the recompiler's output, not a working game. In particular, unresolved stubs still need classification and implementation, and generated output must be checked against the project's manual post-processing requirements before integration.

A private workflow audit step is now being added to classify unresolved stubs by XBE section and by whether they overlap detected functions. The largest known concentration is in the embedded Xbox library sections (D3D, DSOUND, XPP and XGRPH), so these must be treated as Xbox SDK/runtime compatibility work rather than blindly replaced with empty functions.

No UWP package, successful game initialization, rendered frame, or Xbox runtime success is claimed yet.

## XBE received and structurally checked

The user supplied `default.xbe`. Its header identifies **MOH European Assault** (Title ID `0x4541005E`), with 12 sections and decoded entry point `0x001EF095`. This matches the entry-point constant already present in `source/mygame/src/main.c`. The detailed section map and file SHA-256 are recorded in [DEFAULT_XBE_ANALYSIS.md](DEFAULT_XBE_ANALYSIS.md).

The binary was inspected in the private analysis environment and was not committed. Full disassembly/recompilation remains pending: the repository's documented pipeline requires Python 3.10+ and Capstone, and the current execution environment does not have Capstone installed. The generated `src/recomp/gen/` tree remains empty in the public repository. The XBE alone also does not include the game's separate data assets.

