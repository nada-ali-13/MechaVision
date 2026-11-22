"""Pinned DocAligner 1.1.1 heatmap release asset sizes and SHA-256 digests."""

from dataclasses import dataclass


RELEASE = "https://github.com/DocsaidLab/DocAligner/releases/tag/1.1.1"
DOWNLOAD = "https://github.com/DocsaidLab/DocAligner/releases/download/1.1.1/"
LICENSE = "https://github.com/DocsaidLab/DocAligner/blob/1.1.1/LICENSE"


@dataclass(frozen=True)
class Model:
    filename: str
    size: int
    sha256: str


# Digests published by GitHub for the upstream release listed above.
MODELS = {
    "fastvit_sa24": Model(
        "fastvit_sa24_h_e_bifpn_256_fp32.onnx", 83_084_930,
        "7f9f5a8935b2eb22b3ee0245d34996063f54562df390d34714af2d76928695bc",
    ),
    "fastvit_t8": Model(
        "fastvit_t8_h_e_bifpn_256_fp32.onnx", 13_167_814,
        "950070fd4a46e25d46db7c35d0ed77612d9063f70d4543c7c504f0da6a943a89",
    ),
    "lcnet100": Model(
        "lcnet100_h_e_bifpn_256_fp32.onnx", 4_767_987,
        "f4117b786e3a18470f3865c93f3c2bd69d9b998edd60f385574a5c665e79594e",
    ),
}
