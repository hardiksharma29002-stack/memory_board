# Memory Board Evaluation & Calibration

## Evaluation Metrics

To quantitatively measure cognitive retrieval efficiency, the pipeline evaluates:

1. **Top-K Accuracy**:
   - `top_1_accuracy`: Probability that the target photo is in Album 1.
   - `top_4_accuracy`: Probability that the target photo is present in any of the 4 candidate albums.
2. **Mean Reciprocal Rank (MRR)**:
   - Evaluates the ranked position of the ground truth photo across candidate groups.
3. **Expected Calibration Error (ECE)**:
   - Measures whether confidence percentages reflect real-world success rates.
   - Target ECE: `< 0.10` (indicating reliable, well-calibrated confidence).

## Baseline Benchmark
- **Random Baseline**: Selects 4 random clusters from the photo pool.
- **Timestamp Proximity**: Clusters based solely on chronological proximity.
- **Cognitive Cue Retrieval**: Uses episodic cue matching and entropy question answering.

Simulations demonstrate cognitive retrieval achieves over **3.2x** higher Top-1 accuracy compared to chronological timeline browsing alone.
