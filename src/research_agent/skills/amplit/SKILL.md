---
name: amp-prediction
description: Use when predicting antimicrobial-peptide probabilities from peptide CSV or FASTA files with an official local AMPLiT environment.
---

# AMPLiT Prediction

Wraps the official AMPLiT model without installing or changing the user's
environment.

Configure `AMPLIT_HOME` as the official repository directory and
`AMPLIT_PYTHON` as its compatible Python executable. Required resources include
`utils1.py`, `word2vec11.bin`, and `Model/G1.h5` through `Model/G3.h5`.

Missing dependencies stop execution and return installation instructions.
