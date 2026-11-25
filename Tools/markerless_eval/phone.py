"""Install the standalone benchmark and collect private S22 ONNX measurements over ADB."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import cv2
import numpy as np

from .docaligner_models import MODELS
from .heldout import outside_checkout

PACKAGE = "org.mechavision.benchmark"


def collect(args):
    outside_checkout(args.image)
    outside_checkout(args.output)
    if args.output.exists():
        raise ValueError("Use a fresh report path.")
    model = MODELS["fastvit_sa24"]
    with args.weights.open("rb") as stream:
        if (args.weights.stat().st_size != model.size
                or hashlib.file_digest(stream, "sha256").hexdigest() != model.sha256):
            raise ValueError("Unexpected SA24 checkpoint.")
    frame = cv2.imdecode(np.frombuffer(args.image.read_bytes(), dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("The source frame cannot be decoded.")
    ok, image = cv2.imencode(".png", frame)
    if not ok:
        raise ValueError("Could not encode the EXIF-oriented source frame.")
    adb = ["adb"] + (["-s", args.serial] if args.serial else [])
    subprocess.run([*adb, "install", "-r", str(args.apk)], check=True)
    for filename, data in (("sa24.onnx", args.weights.read_bytes()), ("frame.png", image.tobytes())):
        remote = f"run-as {PACKAGE} sh -c 'mkdir -p files && cat > files/{filename}'"
        subprocess.run([*adb, "exec-in", remote], input=data, check=True)
    command = [*adb, "shell", "am", "instrument", "-w",
               "-e", "iterations", str(args.iterations), "-e", "threads", str(args.threads),
               "-e", "warmup", str(args.warmup), f"{PACKAGE}/.Benchmark"]
    response = subprocess.run(command, check=True, capture_output=True, text=True)
    for line in response.stdout.splitlines():
        if line.startswith("MECHAVISION_RESULT "):
            report = json.loads(line.split(" ", 1)[1])
            report["benchmark_apk_bytes"] = args.apk.stat().st_size
            with args.output.open("x", encoding="utf-8") as output:
                json.dump(report, output, indent=2, allow_nan=False)
                output.write("\n")
            print(f"Phone measurements saved to {args.output}")
            return
    raise ValueError(f"Benchmark did not return measurements:\n{response.stdout}\n{response.stderr}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("apk", "weights", "image", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--serial", help="ADB device serial if multiple devices are connected")
    parser.add_argument("--iterations", type=int, default=30)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--threads", type=int, default=1)
    args = parser.parse_args()
    if not (5 <= args.iterations <= 200 and 1 <= args.warmup <= 30 and 1 <= args.threads <= 8):
        parser.error("iterations, warmup or thread count is outside the supported range")
    try:
        collect(args)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    main()
