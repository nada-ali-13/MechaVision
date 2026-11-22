"""Download and verify official DocAligner weights outside the checkout."""

import argparse
import hashlib
import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .docaligner_models import DOWNLOAD, MODELS, Model


class ReleaseRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urlsplit(newurl)
        if target.scheme != "https" or target.hostname not in {"github.com", "release-assets.githubusercontent.com"}:
            raise ValueError("The release requested a redirect outside the approved GitHub HTTPS hosts")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def verify_existing(path: Path, model: Model) -> None:
    if path.stat().st_size == model.size:
        with path.open("rb") as existing:
            if hashlib.file_digest(existing, "sha256").hexdigest() == model.sha256:
                return
    raise ValueError(f"The existing file {path} fails its release size or SHA-256 check. Choose another output directory.")


def fetch(output_dir: Path, model: Model) -> Path:
    destination = output_dir / model.filename
    if destination.exists():
        verify_existing(destination, model)
        return destination

    opener = build_opener(ReleaseRedirectHandler())
    request = Request(DOWNLOAD + model.filename, headers={"Accept": "application/octet-stream"})
    digest = hashlib.sha256()
    size = 0
    partial = None
    try:
        with opener.open(request, timeout=60) as response, NamedTemporaryFile(
            dir=output_dir, prefix=".docaligner-", suffix=".part", delete=False
        ) as output:
            partial = Path(output.name)
            for chunk in iter(lambda: response.read(1 << 20), b""):
                size += len(chunk)
                if size > model.size:
                    raise ValueError(f"Release response for {model.filename} exceeds its pinned size")
                digest.update(chunk)
                output.write(chunk)
        if size != model.size or digest.hexdigest() != model.sha256:
            raise ValueError(f"Release response for {model.filename} fails its pinned size or SHA-256 check")
        try:
            os.link(partial, destination)
        except FileExistsError:
            verify_existing(destination, model)
    finally:
        if partial is not None:
            partial.unlink(missing_ok=True)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True, help="Local cache directory outside the checkout")
    parser.add_argument("--model", choices=tuple(MODELS), action="append", help="Repeat to select models. Defaults to all.")
    args = parser.parse_args()
    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name in args.model or MODELS:
            model = MODELS[name]
            path = fetch(args.output_dir, model)
            print(f"{model.sha256}  {path}")
    except (URLError, OSError, ValueError) as error:
        print(f"DocAligner download failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
