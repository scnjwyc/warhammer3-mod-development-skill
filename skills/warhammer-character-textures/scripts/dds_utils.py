"""Small, dependency-free DDS inspection helpers for the texture skill."""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from pathlib import Path


DXGI_NAMES = {
    70: "BC1_TYPELESS",
    71: "BC1_UNORM",
    72: "BC1_UNORM_SRGB",
    76: "BC3_TYPELESS",
    77: "BC3_UNORM",
    78: "BC3_UNORM_SRGB",
    94: "BC6H_TYPELESS",
    95: "BC6H_UF16",
    96: "BC6H_SF16",
    97: "BC7_TYPELESS",
    98: "BC7_UNORM",
    99: "BC7_SRGB",
}
BC6_FORMATS = {94, 95, 96}
BC7_FORMATS = {98, 99}


@dataclass(frozen=True)
class DDSInfo:
    path: Path
    width: int
    height: int
    mip_count: int
    format_id: int | None
    format_name: str
    fourcc: str

    @property
    def is_bc6(self) -> bool:
        return self.format_id in BC6_FORMATS

    @property
    def is_bc7(self) -> bool:
        return self.format_id in BC7_FORMATS


def read_dds_info(path: Path) -> DDSInfo:
    with path.open("rb") as handle:
        data = handle.read(148)
    if len(data) < 128 or data[:4] != b"DDS ":
        raise ValueError("不是有效的 DDS 文件")
    if struct.unpack_from("<I", data, 4)[0] != 124 or struct.unpack_from("<I", data, 76)[0] != 32:
        raise ValueError("DDS header/pixel-format size 非法")

    height = struct.unpack_from("<I", data, 12)[0]
    width = struct.unpack_from("<I", data, 16)[0]
    mip_count = struct.unpack_from("<I", data, 28)[0]
    if not width or not height:
        raise ValueError("DDS 宽高必须为正数")
    fourcc_bytes = data[84:88]
    fourcc = fourcc_bytes.rstrip(b"\0").decode("ascii", errors="replace")
    format_id = None
    format_name = fourcc or "UNKNOWN"
    if fourcc == "DX10":
        if len(data) < 148:
            raise ValueError("DDS 缺少 DX10 格式扩展头")
        format_id = struct.unpack_from("<I", data, 128)[0]
        format_name = DXGI_NAMES.get(format_id, f"DXGI_{format_id}")

    return DDSInfo(
        path=path,
        width=width,
        height=height,
        mip_count=max(1, mip_count),
        format_id=format_id,
        format_name=format_name,
        fourcc=fourcc,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def safe_relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def main() -> int:
    """Inspect headers only. Pixel decoding and alpha validation are external."""
    import argparse
    from dataclasses import asdict
    import json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    result = []
    failed = False
    for path in args.files:
        try:
            info = read_dds_info(path)
            row = asdict(info)
            row.update(path=str(path), sha256=sha256(path), is_bc6=info.is_bc6,
                       validation="header only; payload and alpha not decoded")
        except (OSError, ValueError) as exc:
            row = {"path": str(path), "error": str(exc)}
            failed = True
        result.append(row)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
