#!/usr/bin/env python3
"""
Benchmark Script for LightGBM on Credit Card Fraud Detection
Lab 16: Cloud AI Environment Setup

This script loads the Credit Card Fraud dataset, trains a LightGBM binary classifier,
evaluates model performance (AUC-ROC, Accuracy, F1, Precision, Recall),
measures single-row inference latency and 1,000-row batch throughput,
and outputs formatted results to console and benchmark_result.json.
"""

import os
import sys
import time
import json
import warnings
import argparse
import platform
from pathlib import Path

# Safe encoding for cross-platform terminals (Windows/Linux)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score,
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    classification_report,
)
import lightgbm as lgb


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run LightGBM Fraud Detection Benchmark on CPU/GPU"
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=None,
        help="Path to creditcard.csv (if not provided, searches default locations)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="benchmark_result.json",
        help="Path to output JSON file (default: benchmark_result.json)",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Fraction of data for test set (default: 0.2)",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--generate-mock",
        action="store_true",
        help="Generate synthetic mock dataset if real dataset is not found",
    )
    parser.add_argument(
        "--mock-rows",
        type=int,
        default=284807,
        help="Number of rows for mock dataset (default: 284807 matching real dataset)",
    )
    return parser.parse_args()


def find_dataset(user_path=None):
    """Search for creditcard.csv in common locations."""
    if user_path and os.path.exists(user_path):
        return Path(user_path)

    search_candidates = [
        Path("creditcard.csv"),
        Path("ml-benchmark/creditcard.csv"),
        Path.home() / "ml-benchmark" / "creditcard.csv",
        Path("data/creditcard.csv"),
        Path("../creditcard.csv"),
    ]

    for p in search_candidates:
        if p.exists():
            return p
    return None


def generate_mock_creditcard_data(n_rows=284807, random_state=42):
    """
    Generate synthetic data mimicking the Kaggle Credit Card Fraud dataset:
    - Features: Time, V1-V28 (PCA components), Amount, Class (0 or 1).
    - Extremely imbalanced: ~0.17% positive (fraud) cases.
    """
    print(f"\n[INFO] Generating synthetic dataset ({n_rows:,} rows, 30 features)...")
    rng = np.random.default_rng(random_state)

    time_col = np.sort(rng.uniform(0, 172800, n_rows))  # 2 days in seconds
    v_cols = {f"V{i}": rng.normal(loc=0.0, scale=1.5, size=n_rows) for i in range(1, 29)}
    amount_col = np.round(rng.exponential(scale=88.0, size=n_rows), 2)

    # Inject slight signal into fraud cases (~0.17% fraud rate)
    fraud_prob = 0.00172
    is_fraud = rng.random(n_rows) < fraud_prob
    if is_fraud.sum() == 0:
        is_fraud[0:10] = True

    # Shift features slightly for fraud cases to mimic real signal
    v_cols["V14"][is_fraud] -= 3.5
    v_cols["V17"][is_fraud] -= 3.0
    v_cols["V4"][is_fraud] += 2.5
    v_cols["V11"][is_fraud] += 2.0

    data = {"Time": time_col}
    data.update(v_cols)
    data["Amount"] = amount_col
    data["Class"] = is_fraud.astype(int)

    df = pd.DataFrame(data)
    fraud_count = int(df["Class"].sum())
    fraud_rate = float(df["Class"].mean() * 100)
    print(f"[INFO] Synthetic dataset generated: {len(df):,} records, {fraud_count:,} frauds ({fraud_rate:.3f}%).")
    return df


def run_benchmark(args):
    dataset_path = find_dataset(args.data_path)
    is_mock = False

    t0_load = time.perf_counter()
    if dataset_path:
        print(f"\n[1/5] Loading real dataset from: {dataset_path.resolve()}")
        df = pd.read_csv(dataset_path)
        data_source = str(dataset_path.resolve())
    else:
        if args.generate_mock or not sys.stdin.isatty():
            print("\n[!] Dataset creditcard.csv not found in standard paths.")
            print("    Using synthetic dataset for benchmark testing (--generate-mock enabled).")
            df = generate_mock_creditcard_data(n_rows=args.mock_rows, random_state=args.random_state)
            data_source = f"synthetic_mock_{args.mock_rows}_rows"
            is_mock = True
        else:
            print("\n" + "=" * 70)
            print("[-] ERROR: creditcard.csv not found!")
            print("    Please download the dataset from Kaggle:")
            print("    kaggle datasets download -d mlg-ulb/creditcardfraud --unzip -p ~/ml-benchmark/")
            print("    or run with `--generate-mock` to test with synthetic data.")
            print("=" * 70 + "\n")
            sys.exit(1)

    t1_load = time.perf_counter()
    data_load_time_sec = t1_load - t0_load
    class_dist = {int(k): int(v) for k, v in df["Class"].value_counts().items()}
    print(f"      Rows: {len(df):,}, Columns: {df.shape[1]}")
    print(f"      Class distribution: {class_dist}")
    print(f"      Load time: {data_load_time_sec:.4f} s")

    # Split features and target
    X = df.drop(columns=["Class"])
    y = df["Class"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=args.random_state, stratify=y
    )
    print(f"\n[2/5] Train set: {len(X_train):,} samples | Test set: {len(X_test):,} samples")

    # Configure LightGBM Classifier
    clf = lgb.LGBMClassifier(
        objective="binary",
        metric="auc",
        boosting_type="gbdt",
        n_estimators=150,
        learning_rate=0.05,
        num_leaves=31,
        random_state=args.random_state,
        n_jobs=-1,
        verbose=-1,
    )

    print("\n[3/5] Training LightGBM Classifier...")
    t0_train = time.perf_counter()
    callbacks = [
        lgb.early_stopping(stopping_rounds=20, verbose=False),
        lgb.log_evaluation(period=0),
    ]
    clf.fit(
        X_train,
        y_train,
        eval_set=[(X_test, y_test)],
        eval_metric="auc",
        callbacks=callbacks,
    )
    t1_train = time.perf_counter()
    training_time_sec = t1_train - t0_train
    best_iteration = (
        clf.best_iteration_
        if hasattr(clf, "best_iteration_") and clf.best_iteration_ is not None
        else 150
    )
    print(f"      Training completed in {training_time_sec:.4f} s (Best iteration: {best_iteration})")

    # Evaluation on Test set
    print("\n[4/5] Evaluating model on test set...")
    y_pred_proba = clf.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)

    auc_roc = float(roc_auc_score(y_test, y_pred_proba))
    accuracy = float(accuracy_score(y_test, y_pred))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    precision = float(precision_score(y_test, y_pred, zero_division=0))
    recall = float(recall_score(y_test, y_pred, zero_division=0))

    # Inference Latency & Throughput Benchmark
    print("\n[5/5] Measuring inference latency and throughput...")

    # 1. Single row inference latency
    single_row = X_test.iloc[[0]]
    # Warmup
    for _ in range(10):
        _ = clf.predict_proba(single_row)

    n_lat_runs = 200
    lat_times = []
    for _ in range(n_lat_runs):
        st = time.perf_counter()
        _ = clf.predict_proba(single_row)
        et = time.perf_counter()
        lat_times.append((et - st) * 1000.0)  # ms

    single_row_latency_ms = float(np.mean(lat_times))

    # 2. Batch 1000 rows inference throughput
    if len(X_test) >= 1000:
        batch_1000 = X_test.iloc[:1000]
    else:
        batch_1000 = pd.concat([X_test] * (1000 // len(X_test) + 1)).iloc[:1000]

    # Warmup
    for _ in range(3):
        _ = clf.predict_proba(batch_1000)

    n_batch_runs = 20
    batch_times = []
    for _ in range(n_batch_runs):
        st = time.perf_counter()
        _ = clf.predict_proba(batch_1000)
        et = time.perf_counter()
        batch_times.append(et - st)

    avg_batch_time_sec = float(np.mean(batch_times))
    throughput_rows_per_sec = float(1000.0 / avg_batch_time_sec)
    batch_1000_latency_ms = float(avg_batch_time_sec * 1000.0)

    # Collect Results
    results = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "system": {
                "os": platform.system(),
                "release": platform.release(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "lightgbm_version": lgb.__version__,
            },
            "data_source": data_source,
            "is_synthetic": is_mock,
            "total_rows": int(len(df)),
            "train_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
        },
        "metrics": {
            "data_load_time_sec": round(data_load_time_sec, 4),
            "training_time_sec": round(training_time_sec, 4),
            "best_iteration": int(best_iteration),
            "auc_roc": round(auc_roc, 5),
            "accuracy": round(accuracy, 5),
            "f1_score": round(f1, 5),
            "precision": round(precision, 5),
            "recall": round(recall, 5),
            "inference_latency_single_row_ms": round(single_row_latency_ms, 4),
            "inference_throughput_1000_rows_sec": round(throughput_rows_per_sec, 2),
            "inference_batch_1000_time_ms": round(batch_1000_latency_ms, 2),
        },
    }

    # Save to JSON
    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
    print(f"\n[OK] Results saved to: {output_path.resolve()}")

    # Print Summary Table
    separator = "-" * 70
    double_separator = "=" * 70
    print("\n" + double_separator)
    print("           LIGHTGBM BENCHMARK RESULTS (LAB 16)")
    print(double_separator)
    print(f"{'Metric':<36} | {'Ket qua / Value':<30}")
    print(separator)
    print(f"{'Thoi gian load data':<36} | {results['metrics']['data_load_time_sec']} s")
    print(f"{'Thoi gian training':<36} | {results['metrics']['training_time_sec']} s")
    print(f"{'Best iteration':<36} | {results['metrics']['best_iteration']}")
    print(f"{'AUC-ROC':<36} | {results['metrics']['auc_roc']:.5f}")
    print(f"{'Accuracy':<36} | {results['metrics']['accuracy']:.5f} ({results['metrics']['accuracy']*100:.2f}%)")
    print(f"{'F1-Score':<36} | {results['metrics']['f1_score']:.5f}")
    print(f"{'Precision':<36} | {results['metrics']['precision']:.5f}")
    print(f"{'Recall':<36} | {results['metrics']['recall']:.5f}")
    print(f"{'Inference latency (1 row)':<36} | {results['metrics']['inference_latency_single_row_ms']:.3f} ms")
    print(f"{'Inference throughput (1000 rows)':<36} | {results['metrics']['inference_throughput_1000_rows_sec']:,.0f} rows/s ({results['metrics']['inference_batch_1000_time_ms']:.2f} ms)")
    print(double_separator)

    # Markdown table for report
    print("\n[+] Markdown Table for Lab Report:")
    print("| Metric | Ket qua |")
    print("|---|---|")
    print(f"| Thoi gian load data | {results['metrics']['data_load_time_sec']} s |")
    print(f"| Thoi gian training | {results['metrics']['training_time_sec']} s |")
    print(f"| Best iteration | {results['metrics']['best_iteration']} |")
    print(f"| AUC-ROC | {results['metrics']['auc_roc']:.5f} |")
    print(f"| Accuracy | {results['metrics']['accuracy']:.5f} |")
    print(f"| F1-Score | {results['metrics']['f1_score']:.5f} |")
    print(f"| Precision | {results['metrics']['precision']:.5f} |")
    print(f"| Recall | {results['metrics']['recall']:.5f} |")
    print(f"| Inference latency (1 row) | {results['metrics']['inference_latency_single_row_ms']:.3f} ms |")
    print(f"| Inference throughput (1000 rows) | {results['metrics']['inference_throughput_1000_rows_sec']:,.0f} rows/s ({results['metrics']['inference_batch_1000_time_ms']:.2f} ms) |")

    return results


if __name__ == "__main__":
    run_benchmark(parse_args())
