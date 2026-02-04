# Stratified Blind Test Dataset

This folder contains the stratified blind test set used for evaluation in the RRE MVP.

## Purpose
The dataset is used exclusively for evaluation and benchmarking.
It is NOT used for model training.

## Source
- Original corpus: SHOE_ACOSI (2023)
- Source files: train.txt + test.txt
- Total source pool: 1,031 reviews

## Construction
- Stratified by sentiment and aspect
- Target distribution:
  - Negative (1–2★): 60%, Neutral (3★): 25%,  Positive (4–5★): 15%
  - Mix aspects: Fit/Sizing: 20%, Shipping/Packaging: 19%, Material/Quality: 18%, Instructions/UX: 15% , Color/Aesthetics: 15%, Comfort:8% , Value/ Price : 3%, Durability : 2%
  - With implicit aspects:With implicit aspect: 65%, With direct aspect: 35% 
- Random seed: 42
- Total reviews: 100

## Notes
- This dataset is intentionally fixed
- Any regeneration must follow the documented sampling protocol
