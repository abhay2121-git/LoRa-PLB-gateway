import time
import pandas as pd
from app.ml.predictor import (
    load_model,
    load_preprocessor,
    _extract_features,
    REQUIRED_FEATURES,
    predict_priority,
)

# 1. Realistic test event payload (Critical emergency scenario)
sample_packet = {
    "packet_type": "SOS",
    "heart_rate": 142,
    "spo2": 88,
    "battery": 45,
    "retry_count": 1,
    "hop_count": 2,
}

# 2. Warm-up runs to ensure model/preprocessor caches and JIT paths are primed
print("Warming up...")
for _ in range(50):
    predict_priority(sample_packet)

# Pre-transform sample for isolated model.predict() timing
features = _extract_features(sample_packet)
transformed = load_preprocessor().transform(pd.DataFrame([features], columns=REQUIRED_FEATURES))
model = load_model()

# 3. Benchmark parameters
NUM_RUNS = 1000

# Benchmark A: Raw model.predict() inference call
t0 = time.perf_counter()
for _ in range(NUM_RUNS):
    model.predict(transformed)
t1 = time.perf_counter()
raw_avg_ms = ((t1 - t0) * 1000) / NUM_RUNS

# Benchmark B: End-to-end gateway classification pipeline (extraction + transform + predict)
t2 = time.perf_counter()
for _ in range(NUM_RUNS):
    predict_priority(sample_packet)
t3 = time.perf_counter()
e2e_avg_ms = ((t3 - t2) * 1000) / NUM_RUNS

# 4. Display Results
print("-" * 55)
print(f"Number of Evaluation Runs          : {NUM_RUNS}")
print(f"Isolated model.predict() Average    : {raw_avg_ms:.3f} ms")
print(f"End-to-end Classification Average  : {e2e_avg_ms:.3f} ms")
print("-" * 55)
print(f"Value for [FILL]: {raw_avg_ms:.2f} ms (or {e2e_avg_ms:.2f} ms for full pipeline)")
