#!/usr/bin/env python3
"""Disassemble private XBE bytes around unresolved generated call targets."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xbe", type=Path, required=True)
    parser.add_argument("--analysis-dir", type=Path, required=True)
    parser.add_argument("--gen-dir", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    args = parser.parse_args()

    meta = load_json(args.analysis_dir / "moh_analysis.json")
    functions = load_json(args.analysis_dir / "disasm" / "functions.json")
    xrefs = load_json(args.analysis_dir / "disasm" / "xrefs.json")
    image = args.xbe.read_bytes()
    source = (args.gen_dir / "recomp_stubs_unresolved.c").read_text(
        encoding="utf-8", errors="replace"
    )

    stub_pattern = re.compile(
        r"void\s+sub_([0-9A-Fa-f]{8})\s*\(\s*void\s*\)\s*\{(.*?)\}",
        re.DOTALL,
    )
    sections = []
    for section in meta.get("sections", []):
        sections.append({
            "name": section["name"],
            "va": int(section["virtual_addr"], 16),
            "raw": int(section["raw_addr"], 16),
            "raw_size": int(section["raw_size"]),
            "virtual_size": int(section["virtual_size"]),
        })
    function_ranges = sorted(
        (int(f["start"], 16), int(f["end"], 16), f.get("name", ""))
        for f in functions
    )
    xrefs_by_target = {}
    for xref in xrefs:
        xrefs_by_target.setdefault(int(xref["to"], 16), []).append(xref)

    disassembler = Cs(CS_ARCH_X86, CS_MODE_32)
    records = []
    for match in stub_pattern.finditer(source):
        address = int(match.group(1), 16)
        section = next(
            (s for s in sections if s["va"] <= address < s["va"] + s["virtual_size"]),
            None,
        )
        file_offset = None
        byte_window = ""
        instructions = []
        if section and address < section["va"] + section["raw_size"]:
            file_offset = section["raw"] + address - section["va"]
            chunk = image[file_offset:min(file_offset + 48, section["raw"] + section["raw_size"])]
            byte_window = chunk.hex()
            instructions = [
                {
                    "address": f"0x{insn.address:08X}",
                    "size": insn.size,
                    "mnemonic": insn.mnemonic,
                    "operands": insn.op_str,
                    "bytes": insn.bytes.hex(),
                }
                for insn in disassembler.disasm(chunk, address)
            ]

        parent = next(
            (
                {"start": f"0x{start:08X}", "end": f"0x{end:08X}", "name": name}
                for start, end, name in function_ranges
                if start <= address < end
            ),
            None,
        )
        records.append({
            "address": f"0x{address:08X}",
            "section": section["name"] if section else None,
            "file_offset": f"0x{file_offset:X}" if file_offset is not None else None,
            "containing_function": parent,
            "xrefs_to_target": xrefs_by_target.get(address, []),
            "bytes": byte_window,
            "instructions_from_target": instructions,
            "generated_stub_body": match.group(2).strip(),
        })

    section_counts = Counter(r["section"] or "OUTSIDE_SECTIONS" for r in records)
    report = {
        "total": len(records),
        "sections": dict(sorted(section_counts.items())),
        "records": records,
    }
    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / "unresolved_stub_context.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Unresolved stub machine-code context",
        "",
        f"- Targets inspected: {len(records)}",
        "",
        "## By section",
        "",
    ]
    lines.extend(f"- {name}: {count}" for name, count in sorted(section_counts.items()))
    for record in records:
        lines.extend(["", f"## {record['address']} — {record['section'] or 'outside image'}", ""])
        if record["containing_function"]:
            parent = record["containing_function"]
            lines.append(
                f"- Existing function range: {parent['name']} "
                f"({parent['start']}–{parent['end']})"
            )
        if record["xrefs_to_target"]:
            lines.append(
                "- Xrefs: " + ", ".join(
                    f"{xref['type']} from {xref['from']}" for xref in record["xrefs_to_target"]
                )
            )
        else:
            lines.append("- Xrefs: none in static xref database")
        if record["instructions_from_target"]:
            decoded = "; ".join(
                f"{insn['address']} {insn['mnemonic']} {insn['operands']}".strip()
                for insn in record["instructions_from_target"]
            )
            lines.append(f"- Instructions: {decoded}")
        else:
            lines.append("- Instructions: no file-backed bytes at target")

    (args.report_dir / "unresolved_stub_context.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(f"Inspected {len(records)} unresolved targets; sections={dict(section_counts)}")
    if len(records) != 255:
        raise SystemExit(f"Expected 255 unresolved targets, found {len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
