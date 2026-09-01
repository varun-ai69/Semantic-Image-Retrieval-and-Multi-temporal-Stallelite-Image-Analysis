# Evaluation & Benchmark Harness (`backend/evaluation`)

Automated benchmarking suite for accuracy metrics and latency measurements.

- `retrieval_eval.py`: Computes Recall@k, Precision@k, and nDCG for semantic retrieval.
- `change_eval.py`: Computes Precision, Recall, and F1-score for change detection categories.
- `benchmark.py`: Measures system latency (p50/p95), ingestion throughput, and memory footprint.
