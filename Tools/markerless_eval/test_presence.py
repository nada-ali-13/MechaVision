import unittest

from Tools.markerless_eval.presence import make_manifest, score_presence


class PresenceTests(unittest.TestCase):
    def test_counts_rejection_separately_from_inference_errors(self):
        labels = {"board/photo.jpg": "board", "no_board/photo.jpg": "no_board",
                  "no_board/second.jpg": "no_board"}
        manifest = make_manifest(labels)
        predictions = {"images": [
            {"id": "photo-01", "corners_px": [[0, 0], [8, 0], [8, 8], [0, 8]],
             "outcome": "unannotated", "inference_ms": [10]},
            {"id": "photo-02", "corners_px": None, "outcome": "unannotated", "inference_ms": [20]},
            {"id": "photo-03", "corners_px": None, "outcome": "inference_error", "inference_ms": []},
        ]}
        score = score_presence(labels, manifest, predictions)
        self.assertEqual(score["counts"], {"positive_accepted": 1, "negative_rejected": 1,
                                           "inference_error": 1})
        self.assertEqual(score["latency_ms"]["median"], 15)
        with self.assertRaisesRegex(ValueError, "exactly once"):
            score_presence(labels, manifest, {"images": predictions["images"][:-1]})
