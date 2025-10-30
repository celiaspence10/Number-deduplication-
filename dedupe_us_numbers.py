#!/usr/bin/env python3

import argparse
import os
import re
import sys
from typing import Iterable, List, Set, Tuple


US_COUNTRY_CODE = "1"


def normalize_us_number(raw: str) -> Tuple[bool, str]:
    """
    Normalize a raw phone string to E.164 for US numbers: +1XXXXXXXXXX.

    Rules:
    - Keep digits only; ignore spaces, dashes, parentheses, dots, etc.
    - Accept 10-digit NANP numbers → +1XXXXXXXXXX（严格 NANP：NXX NXX XXXX，N=2-9）
    - Accept 11 digits starting with 1 → treat as country code +1 → +1XXXXXXXXXX
    - Accept numbers starting with +1 followed by 10 digits
    - Reject all others

    Returns (is_valid_us, e164_or_empty)
    """
    if not raw:
        return False, ""

    s = raw.strip()
    # Remove common extension markers like x123, ext123 (ignore extensions)
    s = re.split(r"(?i)\bext\b|\bx\b|#", s)[0]

    # Keep leading + for detection, strip other non-digits
    if s.startswith("+"):
        digits = "+" + re.sub(r"\D", "", s[1:])
    else:
        digits = re.sub(r"\D", "", s)

    # Handle +1XXXXXXXXXX
    if digits.startswith("+" + US_COUNTRY_CODE):
        rest = digits[2:]
        if _is_valid_nanp_10(rest):
            return True, "+" + US_COUNTRY_CODE + rest
        return False, ""

    # Handle 11 digits starting with 1
    if len(digits) == 11 and digits.startswith(US_COUNTRY_CODE):
        ten = digits[1:]
        if _is_valid_nanp_10(ten):
            return True, "+" + US_COUNTRY_CODE + ten
        return False, ""

    # Handle plain 10 digits
    if _is_valid_nanp_10(digits):
        return True, "+" + US_COUNTRY_CODE + digits

    return False, ""


def _is_valid_nanp_10(d: str) -> bool:
    """Return True if string is a valid 10-digit NANP number (NXX NXX XXXX).
    Rules:
    - Must be 10 digits
    - Area code (d[0:3]) and central office code (d[3:6]) must start with 2-9
    - Disallow N11 as central office (d[4:6] == '11')
    """
    if len(d) != 10 or not d.isdigit():
        return False
    if d[0] in "01" or d[3] in "01":
        return False
    # central office code cannot be N11
    if d[4:6] == "11":
        return False
    return True


def dedupe_numbers(lines: Iterable[str], keep_order: bool = True) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for line in lines:
        ok, e164 = normalize_us_number(line)
        if not ok:
            continue
        if e164 in seen:
            continue
        seen.add(e164)
        out.append(e164)
    if keep_order:
        return out
    return sorted(out)


def read_lines_from_file(path: str, encoding: str = "utf-8") -> Iterable[str]:
    with open(path, "r", encoding=encoding, errors="ignore") as f:
        for line in f:
            yield line.rstrip("\n")


def write_lines_to_file(path: str, lines: Iterable[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for item in lines:
            f.write(item + "\n")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deduplicate US phone numbers from a TXT file by normalizing to E.164 (+1XXXXXXXXXX).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input",
        help="Path to input TXT file (one number per line; formats may vary).",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path. If omitted, writes alongside input as <name>.deduped.txt",
        default=None,
    )
    parser.add_argument(
        "--no-keep-order",
        action="store_true",
        help="If set, output will be sorted instead of keeping first-seen order.",
    )
    parser.add_argument(
        "--show-stats",
        action="store_true",
        help="Print stats about counts before writing output.",
    )
    return parser.parse_args(argv)


def derive_output_path(input_path: str) -> str:
    base, ext = os.path.splitext(input_path)
    return f"{base}.deduped.txt"


def main(argv: List[str]) -> int:
    args = parse_args(argv)

    input_path = args.input
    if not os.path.isfile(input_path):
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 2

    lines = list(read_lines_from_file(input_path))

    # For stats: count valid and unique
    normalized_all: List[str] = []
    for line in lines:
        ok, e164 = normalize_us_number(line)
        if ok:
            normalized_all.append(e164)

    unique_numbers = dedupe_numbers(lines, keep_order=not args.no_keep_order)

    if args.show_stats:
        total = len(lines)
        valid = len(normalized_all)
        unique = len(unique_numbers)
        print(f"Total lines: {total}")
        print(f"Valid US numbers: {valid}")
        print(f"Unique after dedupe: {unique}")

    output_path = args.output or derive_output_path(input_path)
    write_lines_to_file(output_path, unique_numbers)
    print(f"Wrote {len(unique_numbers)} unique numbers to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))


