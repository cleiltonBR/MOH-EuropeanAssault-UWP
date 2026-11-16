#!/usr/bin/env python3
"""Report desktop-Windows assumptions that need review for a UWP/Xbox host.

This is a triage aid, not a UWP compatibility verdict. It deliberately reports
matches instead of rewriting or suppressing code.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = [ROOT / "source" / "mygame", ROOT / "source" / "xboxrecomp-0.16.0"]
PATTERNS = {
    "desktop_process_or_module_introspection": r"\b(GetModuleHandle|GetModuleHandleEx|GetModuleFileName|CreateToolhelp32Snapshot|Thread32First|OpenProcess|OpenThread|GetThreadContext|SetThreadContext)\w*\b",
    "desktop_exception_and_debugging": r"\b(AddVectoredExceptionHandler|SetUnhandledExceptionFilter|SymInitialize|SymFromAddr|MiniDumpWriteDump|__try|__except)\b",
    "desktop_cpu_affinity_or_priority": r"\b(GetSystemCpuSetInformation|SetProcessDefaultCpuSets|SetThreadSelectedCpuSets|SetThreadPriority|SetProcessAffinityMask)\w*\b",
    "desktop_window_or_dialog": r"\b(WinMain|MessageBox[AW]?|CreateWindowEx[AW]?|RegisterClassEx[AW]?)\b",
    "desktop_filesystem_or_environment": r"\b(FindFirstFile[AW]?|FindNextFile[AW]?|GetEnvironmentVariable[AW]?|SetEnvironmentVariable[AW]?|_putenv|getenv)\b",
}
compiled = {name: re.compile(pattern) for name, pattern in PATTERNS.items()}
counts = {name: 0 for name in PATTERNS}
examples = {name: [] for name in PATTERNS}

for root in SCAN_ROOTS:
    if not root.exists():
        continue
    for path in root.rglob("*"):
        if path.suffix.lower() not in {".c", ".h", ".cpp", ".hpp", ".cmake"} and path.name != "CMakeLists.txt":
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line_no, line in enumerate(lines, 1):
            for category, regex in compiled.items():
                if regex.search(line):
                    counts[category] += 1
                    if len(examples[category]) < 8:
                        examples[category].append(f"{path.relative_to(ROOT)}:{line_no}: {line.strip()[:180]}")

total = sum(counts.values())
print("UWP/Xbox desktop-API triage report")
print("NOTE: matches require manual review; this is not a compatibility verdict.")
for category, count in counts.items():
    print(f"\n{category}: {count} match(es)")
    for example in examples[category]:
        print(f"  {example}")
print(f"\nTotal matched source lines: {total}")
print("Audit completed; findings are informational.")
sys.exit(0)
