#!/usr/bin/env python3
"""Offline mapped-PE research; explicit samples, RVA addresses, coverage and provenance.

Requires Python 3.10+. Capstone is needed only for code analysis. No process access.
Run --help; the research workflow is references/runtime-memory-analysis.md.
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import importlib.metadata
import json
import struct
import sys
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path

SCHEMA = "wh3-module-dump/v1"
ANALYSIS_SCHEMA = "wh3-offline-analysis/v1"
MEM_COMMIT, PAGE_GUARD = 0x1000, 0x100
READABLE = {0x02, 0x04, 0x08, 0x20, 0x40, 0x80}
EXECUTABLE = {0x10, 0x20, 0x40, 0x80}


def number(value):
    return int(value, 0) if isinstance(value, str) else int(value)


def readable(state, protect):
    return state == MEM_COMMIT and not protect & PAGE_GUARD and protect & 0xFF in READABLE


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def merged_ranges(ranges, size):
    result = []
    for start, end in sorted(ranges):
        if not 0 <= start < end <= size:
            raise ValueError("invalid coverage range")
        if result and start < result[-1][1]:
            raise ValueError("overlapping coverage ranges")
        if result and start == result[-1][1]:
            result[-1] = (result[-1][0], end)
        else:
            result.append((start, end))
    return result


@dataclass(frozen=True)
class Function:
    start: int
    end: int
    source: str = "exception-directory"


class Image:
    def __init__(self, dump, layout=None, raw=False):
        self.path = Path(dump)
        self.data = self.path.read_bytes()
        self.dump_hash = hashlib.sha256(self.data).hexdigest()
        self.raw, self.base = raw, 0
        self.size = len(self.data)
        self.layout_hash = None
        self.meta = {}
        self.sections, self.functions, self.diagnostics = [], [], []
        if raw:
            self.valid = [(0, self.size)] if self.size else []
        else:
            if layout is None:
                raise ValueError("mapped-pe requires an explicit --layout")
            payload = Path(layout).read_bytes()
            self.layout_hash = hashlib.sha256(payload).hexdigest()
            self.meta = json.loads(payload)
            if self.meta.get("schema") != SCHEMA or self.meta.get("format") != "mapped-pe":
                raise ValueError("unsupported layout schema/format; convert legacy metadata explicitly")
            if self.meta.get("dump_sha256") != self.dump_hash:
                raise ValueError("dump SHA-256 does not match layout")
            self.base = number(self.meta["image_base"])
            if not 0 < self.base < 2**64 or number(self.meta["image_size"]) != self.size:
                raise ValueError("invalid image base or dump length")
            self.valid = merged_ranges(
                [(number(r["rva"]), number(r["rva"]) + number(r["size"]))
                 for r in self.meta["valid_ranges"]], self.size)
            if "regions" in self.meta:
                allowed = merged_ranges(
                    [(number(r["rva"]), number(r["rva"]) + number(r["size"]))
                     for r in self.meta["regions"]
                     if readable(number(r["state"]), number(r["protect"]))], self.size)
                for start, end in self.valid:
                    if not any(a <= start and end <= b for a, b in allowed):
                        raise ValueError("valid bytes intersect non-readable/guard region metadata")
        self.valid_starts = [a for a, _ in self.valid]
        if not raw:
            self._parse_pe()
        self.function_starts = [f.start for f in self.functions]

    def span_end(self, rva):
        pos = bisect.bisect_right(self.valid_starts, rva) - 1
        if pos >= 0 and rva < self.valid[pos][1]:
            return self.valid[pos][1]
        return rva

    def read(self, rva, size):
        if size < 0 or rva < 0 or rva + size > self.size or self.span_end(rva) < rva + size:
            raise ValueError(f"unavailable bytes at RVA {rva:#x}, size {size:#x}")
        return self.data[rva:rva + size]

    def unpack(self, fmt, rva):
        return struct.unpack(fmt, self.read(rva, struct.calcsize(fmt)))

    def _parse_pe(self):
        if self.read(0, 2) != b"MZ":
            raise ValueError("missing readable MZ header")
        pe, = self.unpack("<I", 0x3C)
        if self.read(pe, 4) != b"PE\0\0":
            raise ValueError("invalid PE signature")
        machine, count, stamp, _, _, opt_size, _ = self.unpack("<HHIIIHH", pe + 4)
        if machine != 0x8664 or not 0 < count <= 96 or opt_size < 112:
            raise ValueError("only valid AMD64 PE32+ module images are supported")
        opt = pe + 24
        self.read(opt, opt_size)
        magic, = self.unpack("<H", opt)
        self.preferred_base, = self.unpack("<Q", opt + 24)
        image_size, = self.unpack("<I", opt + 56)
        if magic != 0x20B or image_size != self.size:
            raise ValueError("PE SizeOfImage mismatch: raw disk PE/minidump is not a mapped-pe image")
        self.pe_timestamp = stamp
        section_table = opt + opt_size
        for index in range(count):
            name, vsize, rva, raw_size, raw_offset, _, _, _, _, flags = self.unpack(
                "<8sIIIIIIHHI", section_table + index * 40)
            end = rva + max(vsize, raw_size)
            if end > self.size:
                raise ValueError("section exceeds SizeOfImage")
            self.sections.append({"name": name.rstrip(b"\0").decode("ascii", "replace"),
                                  "rva": rva, "end": end, "raw_offset": raw_offset,
                                  "flags": flags})
        directories, = self.unpack("<I", opt + 108)
        if directories <= 3 or opt_size < 112 + 4 * 8:
            self.diagnostics.append("exception directory not present")
            return
        rva, size = self.unpack("<II", opt + 112 + 3 * 8)
        if not rva or not size:
            self.diagnostics.append("exception directory empty; supply vetted --range entries")
            return
        if rva + size > self.size or size // 12 > 2_000_000:
            raise ValueError("invalid exception directory size")
        if size % 12:
            self.diagnostics.append("exception directory size has a partial record")
        bad, missing = 0, 0
        ranges = set()
        for offset in range(rva, rva + size - 11, 12):
            try:
                start, end, unwind = self.unpack("<III", offset)
            except ValueError:
                missing += 1
                continue
            if start == end == unwind == 0:
                continue
            if not 0 <= start < end <= self.size or not 0 < unwind < self.size or not self.executable(start):
                bad += 1
                continue
            ranges.add((start, end))
        for start, end in sorted(ranges):
            if self.functions and start < self.functions[-1].end:
                bad += 1
                continue
            self.functions.append(Function(start, end))
        if bad or missing:
            self.diagnostics.append(f"exception records rejected={bad}, unavailable={missing}")

    def executable(self, rva):
        section = any(s["flags"] & 0x20000000 and s["rva"] <= rva < s["end"] for s in self.sections)
        if not section:
            return False
        if "regions" not in self.meta:
            return True
        return any(number(r["rva"]) <= rva < number(r["rva"]) + number(r["size"])
                   and number(r["state"]) == MEM_COMMIT
                   and not number(r["protect"]) & PAGE_GUARD
                   and number(r["protect"]) & 0xFF in EXECUTABLE for r in self.meta["regions"])

    def function_at(self, rva, functions=None):
        functions = self.functions if functions is None else functions
        starts = self.function_starts if functions is self.functions else [f.start for f in functions]
        index = bisect.bisect_right(starts, rva) - 1
        return functions[index] if index >= 0 and rva < functions[index].end else None

    def identity(self):
        try:
            version = importlib.metadata.version("capstone")
        except importlib.metadata.PackageNotFoundError:
            version = None
        return {"dump_sha256": self.dump_hash, "layout_sha256": self.layout_hash,
                "image_base": self.base if not self.raw else None, "size": self.size,
                "tool_sha256": sha256_file(__file__), "capstone_version": version,
                "format": "raw" if self.raw else "mapped-pe"}

    def holes(self):
        cursor, result = 0, []
        for start, end in self.valid:
            if start > cursor:
                result.append({"rva": cursor, "size": start - cursor})
            cursor = end
        if cursor < self.size:
            result.append({"rva": cursor, "size": self.size - cursor})
        return result


def capstone_engine():
    try:
        import capstone as cs
        from capstone import x86_const as x86
    except ImportError as exc:
        raise ValueError("Capstone missing; install it in the selected Python environment") from exc
    engine = cs.Cs(cs.CS_ARCH_X86, cs.CS_MODE_64)
    engine.detail = True
    return engine, cs, x86


def functions_for(image, ranges):
    if not ranges:
        if not image.functions:
            raise ValueError("no trustworthy function ranges; supply vetted --range START:END")
        return image.functions
    result = []
    for text in ranges:
        start, end = (number(s) for s in text.split(":"))
        if not 0 <= start < end <= image.size or not image.executable(start):
            raise ValueError("manual range must start in executable module bytes")
        result.append(Function(start, end, "manual-vetted-entry"))
    merged_ranges([(f.start, f.end) for f in result], image.size)
    return sorted(result, key=lambda f: f.start)


def decode_function(image, function, budget, engine, cs, x86):
    """Follow local CFG; direct calls fall through, branch targets remain local.

    No attempt to resolve jump tables or exception paths. Each gap/limit is reported.
    """
    work = [function.start]
    instructions, visited, occupied, issues = {}, set(), set(), []
    while work:
        rva = work.pop()
        while function.start <= rva < function.end:
            if rva in visited:
                break
            if rva in occupied:
                issues.append({"rva": rva, "reason": "branch into an instruction"})
                break
            if len(instructions) >= budget:
                issues.append({"rva": rva, "reason": "instruction budget reached"})
                return list(sorted(instructions.values(), key=lambda i: i.address)), issues
            visited.add(rva)
            count = min(15, function.end - rva, image.span_end(rva) - rva)
            if count <= 0:
                issues.append({"rva": rva, "reason": "unavailable code bytes"})
                break
            ins = next(engine.disasm(image.read(rva, count), image.base + rva, count=1), None)
            if ins is None:
                issues.append({"rva": rva, "reason": "decode stopped"})
                break
            if any(pos in occupied for pos in range(rva, rva + ins.size)):
                issues.append({"rva": rva, "reason": "overlapping instruction paths"})
                break
            occupied.update(range(rva, rva + ins.size))
            instructions[rva] = ins
            if ins.group(cs.CS_GRP_RET) or ins.group(cs.CS_GRP_IRET) or ins.mnemonic in ("int3", "ud2", "hlt"):
                break
            if ins.group(cs.CS_GRP_JUMP):
                direct = bool(ins.operands and ins.operands[0].type == x86.X86_OP_IMM)
                if direct:
                    target = ins.operands[0].imm - image.base
                    if function.start <= target < function.end:
                        work.append(target)
                else:
                    issues.append({"rva": rva, "reason": "unresolved indirect branch"})
                if ins.mnemonic in ("jmp", "ljmp"):
                    break
            rva += ins.size
    return list(sorted(instructions.values(), key=lambda i: i.address)), issues


def scan_code(image, functions, max_instructions, callback):
    engine, cs, x86 = capstone_engine()
    remaining, issues, scanned = max_instructions, [], 0
    for function in functions:
        if remaining <= 0:
            break
        instructions, gaps = decode_function(image, function, remaining, engine, cs, x86)
        remaining -= len(instructions)
        scanned += 1
        issues.extend({"function": function.start, **gap} for gap in gaps)
        callback(function, instructions, cs, x86)
    return {"functions_requested": len(functions), "functions_scanned": scanned,
            "instructions_decoded": max_instructions - remaining,
            "budget_exhausted": remaining <= 0, "issues": issues,
            "sample_diagnostics": image.diagnostics, "unavailable_ranges": image.holes(),
            "limits": ["exception/leaf ranges may be absent", "jump tables and exception paths unresolved",
                       "segment bases and heap data absent from module image",
                       "decoded static code is not proof of runtime execution"]}


def instruction_row(image, ins):
    return {"rva": ins.address - image.base, "va": ins.address,
            "bytes": ins.bytes.hex(), "mnemonic": ins.mnemonic, "operands": ins.op_str}


def find_pattern(image, pattern, limit, context=0, alignment=1):
    if not pattern or limit < 1 or context < 0 or alignment < 1:
        raise ValueError("pattern, limit, context or alignment is invalid")
    hits, total = [], 0
    for start, end in image.valid:
        cursor = start
        while True:
            pos = image.data.find(pattern, cursor, end)
            if pos < 0:
                break
            cursor = pos + 1
            if pos % alignment:
                continue
            total += 1
            if len(hits) < limit:
                lo, hi = max(start, pos - context), min(end, pos + len(pattern) + context)
                block = image.data[lo:hi]
                row = {"file_offset": pos, "context_offset": lo, "hex": block.hex(),
                       "ascii": "".join(chr(b) if 32 <= b <= 126 else "." for b in block)}
                if not image.raw:
                    row.update(rva=pos, va=image.base + pos)
                hits.append(row)
    return {"total": total, "returned": len(hits), "truncated": total > len(hits), "hits": hits}


def graph_data(image, functions, max_instructions):
    edges = []
    def consume(function, instructions, cs, x86):
        for ins in instructions:
            is_call, is_jump = ins.group(cs.CS_GRP_CALL), ins.group(cs.CS_GRP_JUMP)
            if not is_call and not is_jump:
                continue
            direct = bool(ins.operands and ins.operands[0].type == x86.X86_OP_IMM)
            target_va = ins.operands[0].imm if direct else None
            target = target_va - image.base if target_va is not None else None
            local = target is not None and 0 <= target < image.size
            if is_jump and direct and function.start <= target < function.end:
                continue
            callee = image.function_at(target, functions) if local else None
            edges.append({"caller": function.start, "site": ins.address - image.base,
                          "kind": "call" if is_call else "jump-transfer",
                          "direct": direct, "target_va": target_va,
                          "target_rva": target if local else None,
                          "callee": callee.start if callee else None,
                          "target_is_entry": bool(callee and target == callee.start),
                          "operands": ins.op_str})
    coverage = scan_code(image, functions, max_instructions, consume)
    return {"identity": image.identity(), "ranges": [f.__dict__ for f in functions],
            "edges": edges, "coverage": coverage}


def reverse_callers(graph, target, depth):
    if depth < 1:
        raise ValueError("depth must be positive")
    reverse = defaultdict(list)
    for edge in graph["edges"]:
        if edge["direct"] and edge["callee"] is not None:
            reverse[edge["callee"]].append(edge)
    visited, queue, result = {target}, deque([(target, 0)]), []
    while queue:
        callee, level = queue.popleft()
        if level >= depth:
            continue
        for edge in reverse.get(callee, []):
            result.append({"depth": level + 1, **edge})
            if edge["caller"] not in visited:
                visited.add(edge["caller"])
                queue.append((edge["caller"], level + 1))
    return {"target_function": target, "depth": depth, "edges": result,
            "coverage": graph["coverage"]}


def validate_graph(graph, image, functions):
    if graph.get("identity") != image.identity():
        raise ValueError("graph cache belongs to a different dump/layout/base/tool/Capstone")
    if graph.get("ranges") != [f.__dict__ for f in functions]:
        raise ValueError("graph cache uses different function ranges")


def field_data(image, functions, max_instructions, offsets, stride, limit):
    fields, strides, histogram = [], [], Counter()
    total_fields, total_strides = 0, 0
    def consume(function, instructions, cs, x86):
        nonlocal total_fields, total_strides
        matches = [ins for ins in instructions if ins.mnemonic == "imul"
                   and any(op.type == x86.X86_OP_IMM and op.imm == stride for op in ins.operands)]
        for ins in matches:
            total_strides += 1
            if len(strides) < limit:
                strides.append({"function": function.start, **instruction_row(image, ins)})
        if stride is not None and not matches:
            return
        for ins in instructions:
            for op in ins.operands:
                if op.type != x86.X86_OP_MEM or ins.mnemonic == "lea":
                    continue
                mem = op.mem
                base, index = ins.reg_name(mem.base), ins.reg_name(mem.index)
                segment = ins.reg_name(mem.segment)
                if not base or base in ("rsp", "rbp", "esp", "ebp", "rip", "eip"):
                    continue
                if offsets and mem.disp not in offsets:
                    continue
                total_fields += 1
                read, write = bool(op.access & cs.CS_AC_READ), bool(op.access & cs.CS_AC_WRITE)
                key = (base, index, mem.scale, mem.disp, op.size, read, write, segment)
                histogram[key] += 1
                if len(fields) < limit:
                    fields.append({"function": function.start, **instruction_row(image, ins),
                                   "base": base, "index": index, "segment": segment, "scale": mem.scale,
                                   "disp": mem.disp, "width": op.size,
                                   "read": read, "write": write,
                                   "access_unknown": op.access == 0})
    coverage = scan_code(image, functions, max_instructions, consume)
    return {"field_total": total_fields, "stride_total": total_strides,
            "fields": fields, "strides": strides,
            "truncated": total_fields > len(fields) or total_strides > len(strides),
            "histogram": [{"base": k[0], "index": k[1], "scale": k[2], "disp": k[3],
                           "width": k[4], "read": k[5], "write": k[6], "segment": k[7], "count": count}
                          for k, count in histogram.most_common()],
            "coverage": coverage,
            "interpretation": "candidate accesses; stride and nearby writes do not prove object identity"}


def command_result(image, args):
    if args.command == "info":
        return {"module": image.meta.get("module"), "sections": image.sections,
                "function_ranges": len(image.functions), "holes": image.holes(),
                "diagnostics": image.diagnostics}
    if args.command == "find":
        pattern = bytes.fromhex(args.hex) if args.hex is not None else args.text.encode(args.encoding)
        return find_pattern(image, pattern, args.limit, args.context)
    if image.raw:
        raise ValueError("raw input only supports info/find; it has no RVA/VA or function mapping")
    if args.command == "anchors":
        rows = []
        for value in args.anchor:
            rva, text = value.split("=", 1)
            rva, expected = number(rva), bytes.fromhex(text)
            if not expected:
                raise ValueError("empty anchor")
            try:
                actual = image.read(rva, len(expected))
                rows.append({"rva": rva, "expected": expected.hex(), "actual": actual.hex(),
                             "pass": actual == expected})
            except ValueError as exc:
                rows.append({"rva": rva, "pass": False, "error": str(exc)})
        return {"anchors": rows, "all_passed": all(r["pass"] for r in rows),
                "scope": "only tested ranges; not whole-image validity"}
    if args.command == "pointers":
        result = find_pattern(image, struct.pack("<Q", image.base + args.target),
                              args.limit, alignment=args.alignment)
        result["scope"] = "absolute address candidates; not proof of a vtable"
        return result
    if args.command == "candidates":
        hits, total = [], 0
        for start, end in image.valid:
            cursor = start
            while True:
                pos = image.data.find(b"\xe8", cursor, end)
                if pos < 0:
                    break
                cursor = pos + 1
                if pos + 5 <= end and image.executable(pos):
                    disp, = image.unpack("<i", pos + 1)
                    if pos + 5 + disp == args.target:
                        total += 1
                        if len(hits) < args.limit:
                            hits.append({"site": pos, "target": args.target})
        return {"total": total, "hits": hits, "truncated": total > len(hits),
                "scope": "unverified raw E8 candidates, including possible embedded data"}
    functions = functions_for(image, args.ranges)
    if args.command == "graph":
        return graph_data(image, functions, args.max_instructions)
    if args.command == "callers":
        if args.graph:
            payload = json.loads(Path(args.graph).read_text(encoding="utf-8"))
            graph = payload["result"]
            validate_graph(graph, image, functions)
        else:
            graph = graph_data(image, functions, args.max_instructions)
        target = image.function_at(args.target, functions)
        if target is None:
            raise ValueError("target is outside the selected function ranges")
        return reverse_callers(graph, target.start, args.depth)
    if args.command == "fields":
        return field_data(image, functions, args.max_instructions, args.offset, args.stride, args.limit)
    if args.command == "disasm":
        function = image.function_at(args.rva, functions)
        if function is None:
            raise ValueError("RVA has no function range; supply a vetted --range")
        rows = []
        def consume(fn, instructions, cs, x86):
            rows.extend(instruction_row(image, ins) for ins in instructions)
        coverage = scan_code(image, [function], args.max_instructions, consume)
        return {"function": function.__dict__, "requested_rva": args.rva,
                "requested_is_instruction": any(r["rva"] == args.rva for r in rows),
                "instruction_total": len(rows), "instructions": rows[:args.limit],
                "truncated": len(rows) > args.limit, "coverage": coverage}
    if args.command == "xref":
        rows, total = [], 0
        def consume(fn, instructions, cs, x86):
            nonlocal total
            for ins in instructions:
                for op in ins.operands:
                    if (op.type == x86.X86_OP_MEM and op.mem.base == x86.X86_REG_RIP
                            and (not op.mem.segment or ins.mnemonic == "lea")):
                        target = ins.address + ins.size + op.mem.disp - image.base
                        if target == args.target:
                            total += 1
                            if len(rows) < args.limit:
                                rows.append({"function": fn.start, **instruction_row(image, ins),
                                             "target": target, "address_only": ins.mnemonic == "lea",
                                             "read": bool(op.access & cs.CS_AC_READ) and ins.mnemonic != "lea",
                                             "write": bool(op.access & cs.CS_AC_WRITE)})
        coverage = scan_code(image, functions, args.max_instructions, consume)
        return {"total": total, "refs": rows, "truncated": total > len(rows), "coverage": coverage}
    raise ValueError("unknown command")


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dump", required=True, help="explicit binary sample")
    p.add_argument("--layout", help="explicit v1 mapped-pe layout")
    p.add_argument("--format", choices=("mapped-pe", "raw"), default="mapped-pe")
    p.add_argument("--range", dest="ranges", action="append", default=[], help="vetted entry/end RVA START:END")
    p.add_argument("--max-instructions", type=int, default=2_000_000, help="global decode budget; reported when exhausted")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("info", "find", "anchors", "xref", "disasm", "graph", "callers", "pointers", "fields", "candidates"):
        q = sub.add_parser(name)
        q.add_argument("--out", help="new JSON file; never overwrite")
        q.add_argument("--limit", type=int, default=200, help="returned-hit limit, not scan limit")
        if name == "find":
            group = q.add_mutually_exclusive_group(required=True)
            group.add_argument("--text")
            group.add_argument("--hex", help="literal hex bytes, no wildcards/regex")
            q.add_argument("--encoding", choices=("ascii", "utf-8", "utf-16le"), default="ascii")
            q.add_argument("--context", type=int, default=0)
        if name == "anchors":
            q.add_argument("--anchor", action="append", required=True, help="RVA=HEX_BYTES")
        if name in ("xref", "callers", "pointers", "candidates"):
            q.add_argument("--target", type=number, required=True, help="target RVA in this module")
        if name == "pointers":
            q.add_argument("--alignment", type=int, default=8)
        if name == "disasm":
            q.add_argument("--rva", type=number, required=True)
        if name == "callers":
            q.add_argument("--graph", help="identity-checked graph.json produced by graph command")
            q.add_argument("--depth", type=int, default=3)
        if name == "fields":
            q.add_argument("--offset", type=number, action="append", default=[])
            q.add_argument("--stride", type=number, help="candidate IMUL immediate; not pointer dataflow proof")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.limit < 1 or args.max_instructions < 1:
            raise ValueError("limits must be positive")
        if args.out and Path(args.out).exists():
            raise ValueError("output exists; choose a new artifact name")
        image = Image(args.dump, args.layout, args.format == "raw")
        for key in ("target", "rva"):
            value = getattr(args, key, None)
            if value is not None and not 0 <= value < image.size:
                raise ValueError(f"{key} must be a valid RVA within this sample")
        result = command_result(image, args)
        payload = {"schema": ANALYSIS_SCHEMA, "identity": image.identity(),
                   "command": args.command, "parameters": vars(args),
                   "sample_diagnostics": image.diagnostics,
                   "unavailable_ranges": image.holes(), "result": result}
        encoded = json.dumps(payload, ensure_ascii=False, indent=2)
        if args.out:
            with Path(args.out).open("x", encoding="utf-8") as stream:
                stream.write(encoded + "\n")
            print(json.dumps({"output": str(Path(args.out).resolve()), "identity": image.identity()}))
        else:
            print(encoded)
        return 2 if args.command == "anchors" and not result["all_passed"] else 0
    except (OSError, ValueError, KeyError, TypeError, struct.error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
