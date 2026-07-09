"""Controlled inference wrapper executed inside the user's AMPLiT environment."""

from __future__ import annotations

import argparse
import csv
import importlib
import sys
from pathlib import Path


def _word2vec_features(raw_sequences, model_path: Path):
    import numpy as np
    from gensim.models import KeyedVectors

    word_vectors = KeyedVectors.load_word2vec_format(str(model_path), binary=True)
    features = np.zeros((len(raw_sequences), 50, 100))
    for row_index, sequence in enumerate(raw_sequences):
        for position, amino_acid in enumerate(sequence):
            features[row_index, position, :] = word_vectors[amino_acid]
    return features


def _build_model(utils1, input_shapes):
    model, _ = utils1.Phos1(
        2, 9, input_shapes[0], input_shapes[1], input_shapes[2],
        input_shapes[2], input_shapes[2], input_shapes[2],
        "RandomUniform", 9, 16, 15, 75, 15, 0, 0, 0,
        16, 1, 16, 0.2, 0.2, 0.000001,
    )
    return model


def predict(
    amplit_home: Path,
    input_path: Path,
    feature_input_path: Path,
    output_path: Path,
    batch_size: int,
):
    import numpy as np

    sys.path.insert(0, str(amplit_home))
    utils1 = importlib.import_module("utils1")
    one_hot, _, raw_sequences, _ = utils1.getMatrixLabelh(
        str(feature_input_path), 50
    )
    physicochemical = utils1.getMatrixLabelFingerprint(
        str(feature_input_path), 50
    )
    word2vec = _word2vec_features(raw_sequences, amplit_home / "word2vec11.bin")
    model = _build_model(
        utils1,
        (one_hot.shape[1:], word2vec.shape[1:], physicochemical.shape[1:]),
    )
    scores = []
    for filename in ("G1.h5", "G2.h5", "G3.h5"):
        model.load_weights(str(amplit_home / "Model" / filename))
        prediction = model.predict(
            [one_hot, word2vec, physicochemical],
            batch_size=batch_size,
            verbose=0,
        )
        scores.append(prediction[:, 1])
    mean_scores = np.mean(np.stack(scores), axis=0)
    with input_path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    with output_path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(
            target, fieldnames=["row_id", "sequence", "amp_score"]
        )
        writer.writeheader()
        if len(rows) != len(mean_scores):
            raise ValueError("Prediction count does not match input row count")
        for row, score in zip(rows, mean_scores):
            writer.writerow(
                {
                    "row_id": row["row_id"],
                    "sequence": row["sequence"],
                    "amp_score": float(score),
                }
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--amplit-home", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--feature-input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--batch-size", type=int, default=512)
    args = parser.parse_args()
    predict(
        Path(args.amplit_home),
        Path(args.input),
        Path(args.feature_input),
        Path(args.output),
        args.batch_size,
    )


if __name__ == "__main__":
    main()
