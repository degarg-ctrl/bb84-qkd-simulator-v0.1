# Findings

Two major bugs were found in `decoy.py`:
1. **Index Misalignment**: `compute_gains` read sequentially from `intensities` rather than using the original pulse index, scrambling the gains. (Fixed proactively by using `state['index']`).
2. **Absolute Threshold Bug**: `PNS_DETECTION_EPSILON` is hardcoded to an absolute `0.05`. At 50km, channel loss drops overall detection rates to ~1%, meaning normalized gains max out around ~0.04. It is mathematically impossible for their absolute difference to exceed 0.05 at this distance.
