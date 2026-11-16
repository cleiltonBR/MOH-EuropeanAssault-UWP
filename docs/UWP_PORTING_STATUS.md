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

**Foundation/audit only.** The branch and automated source audit are being established first. No UWP package or Xbox runtime success is claimed yet.
