#!/usr/bin/env python3
"""User-operated Windows x64 module capture from an existing, explicit PID.

Read-only APIs only; no game launch, debug attach, suspend, inject or memory writes.
Agent work uses the resulting bin/layout offline. --help performs no process access.
"""
from __future__ import annotations

import argparse
import ctypes as ct
import datetime as dt
import json
import os
import sys
import uuid
from pathlib import Path

from wh3_dump import SCHEMA, merged_ranges, number, readable, sha256_file

DWORD, WORD, BOOL = ct.c_uint32, ct.c_uint16, ct.c_int32
HANDLE, SIZE_T = ct.c_void_p, ct.c_size_t
PROCESS_VM_READ, PROCESS_QUERY_INFORMATION = 0x10, 0x400
TH32CS_SNAPMODULE, TH32CS_SNAPMODULE32 = 0x8, 0x10
INVALID_HANDLE_VALUE = ct.c_void_p(-1).value


class MBI(ct.Structure):
    _fields_ = [("BaseAddress", HANDLE), ("AllocationBase", HANDLE),
                ("AllocationProtect", DWORD), ("PartitionId", WORD),
                ("RegionSize", SIZE_T), ("State", DWORD), ("Protect", DWORD),
                ("Type", DWORD)]


class ModuleEntry(ct.Structure):
    _fields_ = [("dwSize", DWORD), ("th32ModuleID", DWORD), ("th32ProcessID", DWORD),
                ("GlblcntUsage", DWORD), ("ProccntUsage", DWORD),
                ("modBaseAddr", HANDLE), ("modBaseSize", DWORD), ("hModule", HANDLE),
                ("szModule", ct.c_wchar * 256), ("szExePath", ct.c_wchar * 260)]


class FileTime(ct.Structure):
    _fields_ = [("low", DWORD), ("high", DWORD)]


class WindowsReader:
    def __init__(self, pid):
        if os.name != "nt" or ct.sizeof(HANDLE) != 8:
            raise ValueError("capture requires Windows and a 64-bit Python")
        self.k32 = ct.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "OpenProcess": ([DWORD, BOOL, DWORD], HANDLE),
            "CloseHandle": ([HANDLE], BOOL),
            "CreateToolhelp32Snapshot": ([DWORD, DWORD], HANDLE),
            "Module32FirstW": ([HANDLE, ct.POINTER(ModuleEntry)], BOOL),
            "Module32NextW": ([HANDLE, ct.POINTER(ModuleEntry)], BOOL),
            "VirtualQueryEx": ([HANDLE, HANDLE, ct.POINTER(MBI), SIZE_T], SIZE_T),
            "ReadProcessMemory": ([HANDLE, HANDLE, HANDLE, SIZE_T, ct.POINTER(SIZE_T)], BOOL),
            "GetProcessTimes": ([HANDLE] + [ct.POINTER(FileTime)] * 4, BOOL),
            "GetExitCodeProcess": ([HANDLE, ct.POINTER(DWORD)], BOOL),
        }
        for name, (arguments, result) in signatures.items():
            fn = getattr(self.k32, name)
            fn.argtypes, fn.restype = arguments, result
        self.handle = self.k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
        if not self.handle:
            raise ct.WinError(ct.get_last_error())
        self.pid = pid

    def close(self):
        if self.handle:
            self.k32.CloseHandle(self.handle)
            self.handle = None

    def creation_time(self):
        times = [FileTime() for _ in range(4)]
        if not self.k32.GetProcessTimes(self.handle, *(ct.byref(t) for t in times)):
            raise ct.WinError(ct.get_last_error())
        return times[0].low | times[0].high << 32

    def alive(self):
        code = DWORD()
        if not self.k32.GetExitCodeProcess(self.handle, ct.byref(code)):
            raise ct.WinError(ct.get_last_error())
        return code.value == 259

    def modules(self):
        snapshot = None
        for _ in range(8):
            snapshot = self.k32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, self.pid)
            if snapshot not in (None, INVALID_HANDLE_VALUE):
                break
            error = ct.get_last_error()
            if error != 24:  # ERROR_BAD_LENGTH: module list may change during enumeration.
                raise ct.WinError(error)
        else:
            raise ct.WinError(ct.get_last_error())
        try:
            entry = ModuleEntry()
            entry.dwSize = ct.sizeof(entry)
            if not self.k32.Module32FirstW(snapshot, ct.byref(entry)):
                raise ct.WinError(ct.get_last_error())
            result = []
            while True:
                result.append({"name": entry.szModule, "path": entry.szExePath,
                               "base": entry.modBaseAddr, "size": entry.modBaseSize})
                if not self.k32.Module32NextW(snapshot, ct.byref(entry)):
                    if ct.get_last_error() != 18:  # ERROR_NO_MORE_FILES.
                        raise ct.WinError(ct.get_last_error())
                    break
            return result
        finally:
            self.k32.CloseHandle(snapshot)

    def query_regions(self, base, size):
        result, cursor, end = [], base, base + size
        while cursor < end:
            mbi = MBI()
            count = self.k32.VirtualQueryEx(self.handle, cursor, ct.byref(mbi), ct.sizeof(mbi))
            if count != ct.sizeof(mbi):
                raise ct.WinError(ct.get_last_error())
            start, stop = max(cursor, mbi.BaseAddress or 0), min(end, (mbi.BaseAddress or 0) + mbi.RegionSize)
            if not start == cursor < stop:
                raise ValueError("VirtualQueryEx returned a non-advancing/invalid region")
            result.append({"rva": start - base, "size": stop - start,
                           "allocation_base": mbi.AllocationBase,
                           "state": mbi.State, "protect": mbi.Protect, "type": mbi.Type})
            cursor = stop
        return result

    def read(self, address, count):
        buffer, received = (ct.c_ubyte * count)(), SIZE_T()
        ct.set_last_error(0)
        ok = self.k32.ReadProcessMemory(self.handle, address, buffer, count, ct.byref(received))
        error = 0 if ok else ct.get_last_error()
        if received.value > count:
            raise ValueError("ReadProcessMemory returned an invalid byte count")
        return bytes(buffer[:received.value]), error


def select_module(modules, value):
    full_path = "/" in value or "\\" in value
    norm = os.path.normcase(os.path.abspath(value)) if full_path else value.casefold()
    matches = [m for m in modules if
               (os.path.normcase(os.path.abspath(m["path"])) == norm if full_path
                else m["name"].casefold() == norm)]
    if len(matches) != 1:
        raise ValueError(f"module match count={len(matches)}; use the exact module path in this PID")
    return matches[0]


def capture_span(reader, base, size, regions, stream, chunk_size=1024 * 1024, page_size=4096):
    """Sparse image; preserve confirmed partial reads and bounded page retries."""
    if chunk_size < 1 or page_size < 1:
        raise ValueError("chunk/page sizes must be positive")
    cursor = 0
    for region in regions:
        if region["rva"] != cursor or region["size"] <= 0:
            raise ValueError("region list must cover the image exactly")
        cursor += region["size"]
    if cursor != size:
        raise ValueError("region coverage does not equal module size")
    stream.truncate(size)
    valid, attempts, skipped = [], [], []

    def read_piece(rva, count):
        block, error = reader.read(base + rva, count)
        if len(block) > count:
            raise ValueError("reader returned too many bytes")
        if block:
            stream.seek(rva)
            stream.write(block)
            valid.append((rva, rva + len(block)))
        if error or len(block) < count:
            attempts.append({"rva": rva, "requested": count, "received": len(block), "error": error})
        return len(block)

    for region in regions:
        start, stop = region["rva"], region["rva"] + region["size"]
        if not readable(region["state"], region["protect"]):
            skipped.append({"rva": start, "size": stop - start, "reason": "not-readable-or-guard"})
            continue
        cursor = start
        while cursor < stop:
            count = min(chunk_size, stop - cursor)
            received = read_piece(cursor, count)
            rest, chunk_end = cursor + received, cursor + count
            while rest < chunk_end:
                count_page = min(page_size - (base + rest) % page_size, chunk_end - rest)
                read_piece(rest, count_page)
                rest += count_page
            cursor = chunk_end
    return {"valid_ranges": [{"rva": a, "size": b - a} for a, b in merged_ranges(valid, size)],
            "read_attempts": attempts, "skipped_ranges": skipped}


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pid", type=int, required=True)
    p.add_argument("--module", required=True, help="exact filename or full module path")
    p.add_argument("--list-only", action="store_true")
    p.add_argument("--out-dir", help="dedicated capture directory")
    p.add_argument("--max-size", type=number, default=1024**3, help="explicit module size budget")
    args = p.parse_args(argv)
    reader = None
    try:
        if args.pid < 1 or args.max_size < 1 or not args.list_only and not args.out_dir:
            raise ValueError("positive PID/size and --out-dir for capture are required")
        reader = WindowsReader(args.pid)
        creation = reader.creation_time()
        module = select_module(reader.modules(), args.module)
        base, size = module["base"], module["size"]
        if not base or not 0 < size <= args.max_size:
            raise ValueError("module base/size invalid or size budget exceeded")
        regions = reader.query_regions(base, size)
        if args.list_only:
            print(json.dumps({"pid": args.pid, "process_creation_filetime": creation,
                              "module": module, "regions": regions}, indent=2))
            return 0
        disk_before = sha256_file(module["path"])
        output = Path(args.out_dir)
        output.mkdir(parents=True, exist_ok=True)
        stem = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:12]
        dump, layout = output / (stem + ".bin"), output / (stem + ".layout.json")
        started = utc_now()
        print(json.dumps({"status": "reading", "module": module, "output": str(dump.resolve())}), flush=True)
        with dump.open("x+b") as stream:
            coverage = capture_span(reader, base, size, regions, stream)
        if not reader.alive() or reader.creation_time() != creation:
            raise ValueError("process exited/identity changed during capture; binary remains incomplete without layout")
        current = select_module(reader.modules(), module["path"])
        if current != module or sha256_file(module["path"]) != disk_before:
            raise ValueError("module changed during capture; do not analyze this incomplete binary")
        payload = {"schema": SCHEMA, "format": "mapped-pe", "pid": args.pid,
                   "process_creation_filetime": creation, "capture_started_utc": started,
                   "capture_finished_utc": utc_now(), "image_base": base, "image_size": size,
                   "module": {**module, "disk_sha256": disk_before},
                   "dump_sha256": sha256_file(dump), "regions": regions,
                   "capture_tool_sha256": sha256_file(__file__), **coverage,
                   "consistency": "sequential reads, not an atomic process snapshot"}
        with layout.open("x", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2)
            stream.write("\n")
        print(json.dumps({"dump": str(dump.resolve()), "layout": str(layout.resolve()),
                          "valid_bytes": sum(r["size"] for r in coverage["valid_ranges"]),
                          "image_size": size, "read_attempt_failures": len(coverage["read_attempts"])}))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"capture error: {exc}", file=sys.stderr)
        return 2
    finally:
        if reader:
            reader.close()


if __name__ == "__main__":
    raise SystemExit(main())
