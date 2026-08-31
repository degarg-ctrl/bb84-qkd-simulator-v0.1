# Requirements: Table IX Detector Empirical Study

## Objective
Validate the physical behavior of quantum detectors in the simulation engine under parameterized sweeps of detection efficiency $\eta \in [0.50, 0.99]$ and dark count probability $P_{\text{dark}} \in [10^{-7}, 10^{-3}]$ across $0-150\text{ km}$.

## Functional Invariants
1. Sifted counts must scale linearly with $\eta$.
2. Dark count contribution $Q_{\text{dark}}$ must increase as channel attenuation increases at fixed $P_{\text{dark}}$.
3. Sessions must abort when effective QBER exceeds $11\%$.
