"""Fetch pinned public smoke-test images to a caller-selected local directory."""

import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.request import urlopen

MANIFEST = Path(__file__).with_name("public_photos.json")
MAX_IMAGE_BYTES = 16 * 1024 * 1024
PINNED_RAW_URL = re.compile(
    r"https://raw\.githubusercontent\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/[0-9a-f]{40}/[^?#]+"
)
SHA256 = re.compile(r"[0-9a-f]{64}")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="local fixture directory outside the checkout")
    destination = parser.parse_args().output.resolve()
    repo_root = Path(__file__).resolve().parents[3]
    if destination.is_relative_to(repo_root):
        parser.error("choose an output directory outside the checkout")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    destination.mkdir(parents=True, exist_ok=True)
    for item in manifest["images"]:
        name = item["path"]
        url = item["source"]["url"]
        expected = item["source"]["sha256"]
        if not re.fullmatch(r"[A-Za-z0-9_]+\.(jpg|jpeg|png)", name):
            parser.error(f"invalid image filename: {name!r}")
        if not PINNED_RAW_URL.fullmatch(url) or not SHA256.fullmatch(expected):
            parser.error(f"invalid pinned source for {name}")
        output = destination / name
        if output.is_symlink():
            parser.error(f"refusing to follow an existing symbolic link: {output}")
        if output.is_file():
            if sha256(output.read_bytes()) != expected:
                parser.error(f"existing file has the wrong SHA-256: {output}")
            print(f"OK {name} (cached)")
            continue
        with urlopen(url, timeout=15) as response:
            data = response.read(MAX_IMAGE_BYTES + 1)
        if len(data) > MAX_IMAGE_BYTES or sha256(data) != expected:
            parser.error(f"download failed integrity checks: {name}")
        with output.open("xb") as target:
            target.write(data)
        print(f"OK {name}")


if __name__ == "__main__":
    main()
