"""Use binary CSV labels with the corner benchmark without inventing corner annotations."""

import argparse
from collections import Counter
import csv
import json
from pathlib import Path, PurePosixPath

from .metrics import distribution


def labeled_records(csv_path):
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if set(reader.fieldnames or ()) != {"filename", "label"}:
            raise ValueError("expected filename and label CSV columns")
        records = {}
        for row in reader:
            path = PurePosixPath(row["filename"])
            label = row["label"]
            if (path.is_absolute() or ".." in path.parts or "\\" in row["filename"]
                    or not path.parts or path.as_posix() in records
                    or label not in {"board", "no_board"}):
                raise ValueError(f"invalid or duplicate label record: {row}")
            records[path.as_posix()] = label
        if not records:
            raise ValueError("labels CSV is empty")
        return records


def make_manifest(labels):
    return {
        "schema_version": 1,
        "images": [{"id": f"photo-{index:02d}", "path": name}
                   for index, name in enumerate(labels, 1)],
    }


def score_presence(labels, manifest, predictions):
    files = {frame["id"]: frame["path"] for frame in manifest["images"]}
    results = {row["id"]: row for row in predictions["images"]}
    if (files.keys() != results.keys() or set(files.values()) != labels.keys()
            or len(files) != len(labels) or len(files) != len(manifest["images"])
            or len(results) != len(predictions["images"])):
        raise ValueError("labels, manifest and predictions must cover each image exactly once")

    counts = Counter()
    rows = []
    for frame_id, name in files.items():
        row = results[frame_id]
        label = labels[name]
        accepted = row["corners_px"] is not None
        if row["outcome"] == "inference_error":
            outcome = "inference_error"
        elif label == "board":
            outcome = "positive_accepted" if accepted else "positive_rejected"
        else:
            outcome = "negative_accepted" if accepted else "negative_rejected"
        counts[outcome] += 1
        rows.append({"id": frame_id, "filename": name, "label": label, "outcome": outcome,
                     "reason": row.get("reason"), "inference_ms": row["inference_ms"]})
    return {
        "label_counts": dict(Counter(labels.values())),
        "counts": dict(counts),
        "latency_ms": distribution(ms for row in rows for ms in row["inference_ms"]),
        "images": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("labels", type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--results", type=Path, help="score existing predictions instead of generating a manifest")
    args = parser.parse_args()
    try:
        labels = labeled_records(args.labels)
        if args.results is None:
            args.manifest.write_text(json.dumps(make_manifest(labels), indent=2) + "\n", encoding="utf-8")
        else:
            with args.manifest.open(encoding="utf-8") as manifest, args.results.open(encoding="utf-8") as results:
                print(json.dumps(score_presence(labels, json.load(manifest), json.load(results)), indent=2))
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    main()
