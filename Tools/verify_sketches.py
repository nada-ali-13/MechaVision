#!/usr/bin/env python3
"""Check all catalog sketches with the AVR toolchain or with host syntax declarations."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--avr", action="store_true", help="run arduino-cli compile for Uno")
    mode.add_argument("--host", action="store_true", help="parse as C++ with host declarations")
    args = parser.parse_args()

    tool_name = "arduino-cli" if args.avr else os.environ.get("CXX", "g++")
    tool = shutil.which(tool_name)
    if tool is None:
        parser.error(f"required executable not found: {tool_name}")

    sketches = sorted((ROOT / "ArduinoProjects").glob("*/*.ino"))
    if not sketches:
        parser.error("no sketches found in ArduinoProjects")

    host_headers = ROOT / "Tools" / "host_arduino"
    failures = []
    for sketch in sketches:
        if args.avr:
            command = [tool, "compile", "--fqbn", "arduino:avr:uno", str(sketch.parent)]
        else:
            command = [
                tool, "-std=gnu++11", "-fsyntax-only", "-x", "c++",
                "-I", str(host_headers), "-include", "Arduino.h", str(sketch),
            ]
        result = subprocess.run(command, text=True, capture_output=True, check=False)
        relative = sketch.relative_to(ROOT)
        print(f"{'PASS' if result.returncode == 0 else 'FAIL'} {relative}", flush=True)
        if result.returncode:
            failures.append(relative)
            sys.stderr.write(result.stdout + result.stderr)

    check = "AVR compile" if args.avr else "host C++ syntax"
    print(f"{check}: {len(sketches) - len(failures)}/{len(sketches)} passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
