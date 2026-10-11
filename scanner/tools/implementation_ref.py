"""
Compute the SCANNER implementation_ref for a set of executed files.

Definition (D-019):
  1. For each file, sha256 of its UTF-8 bytes with CRLF normalized to LF.
  2. One manifest line per file: "<repo-relative POSIX path>  <sha256>\\n",
     lines sorted by path.
  3. implementation_ref = "sha256:" + sha256 of the concatenated manifest.

Every live report must list the files and carry this value. A report whose
implementation_ref does not match the accepted manifest is rejected.

Usage (from the repository root):
    python scanner/tools/implementation_ref.py FILE [FILE ...]
"""
import hashlib
import sys
from pathlib import Path


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def manifest(paths):
    root = Path.cwd().resolve()
    lines = []
    for p in paths:
        rel = Path(p).resolve().relative_to(root).as_posix()
        lines.append(f"{rel}  {file_sha256(Path(p))}\n")
    return sorted(lines)


def main(argv) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    lines = manifest(argv[1:])
    for line in lines:
        print(line, end="")
    ref = hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()
    print(f"implementation_ref: sha256:{ref}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
