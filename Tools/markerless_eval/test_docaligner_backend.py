import tempfile
import unittest
from pathlib import Path

from Tools.markerless_eval.docaligner_backend import create_backend
from Tools.markerless_eval.docaligner_models import MODELS
from Tools.markerless_eval.fetch_weights import verify_existing


class CheckpointTests(unittest.TestCase):
    def test_backend_rejects_an_unknown_digest_before_loading_model(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, MODELS["lcnet100"].filename)
            path.write_bytes(b"corrupted checkpoint")
            with self.assertRaisesRegex(ValueError, "checkpoint SHA-256"):
                create_backend({"weights": str(path)})

    def test_downloader_refuses_an_existing_wrong_size_or_digest(self):
        model = MODELS["lcnet100"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, model.filename)
            for size in (4, model.size):
                with path.open("wb") as wrong_file:
                    wrong_file.truncate(size)
                with self.subTest(size=size), self.assertRaisesRegex(ValueError, "size or SHA-256"):
                    verify_existing(path, model)
                self.assertEqual(path.stat().st_size, size)


if __name__ == "__main__":
    unittest.main()
