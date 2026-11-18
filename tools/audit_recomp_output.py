#!/usr/bin/env python3
"""Audit generated recompilation output without modifying generated code."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-dir", type=Path, required=True)
    parser.add_argument("--gen-dir", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    args = parser.parse_args()

    analysis = args.analysis_dir
    generated = args.gen_dir
    report_dir = args.report_dir
    report_dir.mkdir(parents=True, exist_ok=True)

    recomp_summary = load_json(report_dir / "summary.json")
    xbe = load_json(analysis / "moh_analysis.json")
    functions = load_json(analysis / "disasm" / "functions.json")
    xrefs = load_json(analysis / "disasm" / "xrefs.json")

    sections = []
    for section in xbe.get("sections", []):
        start = int(section["virtual_addr"], 16)
        sections.append((start, start + int(section["virtual_size"]), section["name"]))

    function_ranges = []
    for function in functions:
        start = int(function["start"], 16)
        end = int(function["end"], 16)
        function_ranges.append((start, end, function.get("name", "")))
    function_ranges.sort()

    callers = defaultdict(list)
    for xref in xrefs:
        if xref.get("type") in {"call", "kernel_call"}:
            callers[int(xref["to"], 16)].append(xref["from"])

    stub_file = generated / "recomp_stubs_unresolved.c"
    text = stub_file.read_text(encoding="utf-8", errors="replace") if stub_file.exists() else ""
    # Match each function body broadly, then validate the instrumentation call.
    # Generated cleanup/comment formatting varies between unresolved targets.
    pattern = re.compile(
        r"void\s+(sub_([0-9A-Fa-f]{8}))\s*\(\s*void\s*\)\s*\{(.*?)\}",
        re.DOTALL,
    )

    records = []
    for match in pattern.finditer(text):
        name, address_hex, body = match.groups()
        hit = re.search(r"RECOMP_STUB_HIT\(0x[0-9A-Fa-f]{8}u\)", body)
        if not hit:
            continue
        reason_match = re.search(r"/\*\s*(.*?)\s*\*/", body, re.DOTALL)
        reason = reason_match.group(1).strip() if reason_match else "no generator note"
        address = int(address_hex, 16)
        section_name = next((name for start, end, name in sections if start <= address < end), "OUTSIDE_SECTIONS")
        containing = next(
            ((start, end, fname) for start, end, fname in function_ranges if start <= address < end),
            None,
        )
        exact = next((f for f in functions if int(f["start"], 16) == address), None)
        records.append({
            "address": f"0x{address:08X}",
            "symbol": name,
            "section": section_name,
            "classification": (
                "exact_detected_function" if exact else
                "inside_detected_function" if containing else
                "not_covered_by_detected_function"
            ),
            "containing_function": containing[2] if containing and not exact else None,
            "stub_note": reason,
            "direct_callers": callers.get(address, []),
        })

    section_counts = Counter(item["section"] for item in records)
    if len(records) != int(recomp_summary.get("unresolved_stubs", len(records))):
        raise SystemExit(
            f"Audit parsed {len(records)} stub bodies, but summary reports "
            f"{recomp_summary.get('unresolved_stubs')} unresolved stubs; refusing incomplete report"
        )
    classification_counts = Counter(item["classification"] for item in records)
    reason_counts = Counter(item["stub_note"] for item in records)

    report = {
        "recompilation": {
            "total_functions": recomp_summary.get("total"),
            "translated": recomp_summary.get("translated"),
            "failed": recomp_summary.get("failed"),
            "unresolved_stubs": recomp_summary.get("unresolved_stubs"),
            "manual_functions": recomp_summary.get("manual_functions"),
            "generated_c_chunks": recomp_summary.get("num_chunks"),
        },
        "audit": {
            "stub_records_parsed": len(records),
            "stubs_by_section": dict(sorted(section_counts.items())),
            "stubs_by_classification": dict(sorted(classification_counts.items())),
            "stub_notes": dict(sorted(reason_counts.items())),
            "records": records,
        },
    }

    json_path = report_dir / "unresolved_stub_audit.json"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Recompilation output audit",
        "",
        f"- Translated functions: {report['recompilation']['translated']}",
        f"- Failed translations: {report['recompilation']['failed']}",
        f"- Unresolved stubs reported: {report['recompilation']['unresolved_stubs']}",
        f"- Stub records parsed: {len(records)}",
        "",
        "## Unresolved stubs by XBE section",
        "",
        "| Section | Count |",
        "|---|---:|",
    ]
    lines.extend(f"| {section} | {count} |" for section, count in sorted(section_counts.items()))
    lines += ["", "## Stub classification", "", "| Classification | Count |", "|---|---:|"]
    lines.extend(f"| {kind} | {count} |" for kind, count in sorted(classification_counts.items()))
    lines += [
        "",
        "This is a static inventory only. It does not prove runtime compatibility or that a stub is safe to leave unresolved.",
        "Review library-section targets as potential Xbox SDK/library compatibility work before implementing replacements.",
        "",
    ]
    (report_dir / "unresolved_stub_audit.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Parsed {len(records)} unresolved stubs")
    print("By section: " + json.dumps(dict(section_counts), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
