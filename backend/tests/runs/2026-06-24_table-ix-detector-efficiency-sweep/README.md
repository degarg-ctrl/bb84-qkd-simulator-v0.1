# Test Run: 2026-06-24 — Table IX Detector Efficiency and Dark Count Sweeps

## Purpose
Empirical study of the physical impact of detector quantum efficiency ($\eta$) and dark count probability ($P_{\text{dark}}$) on BB84 QKD metrics (SKR, $Q_{\text{dark}}$, $Q_{\text{eff}}$, sifted counts, and session abort thresholds) across varying fiber transmission distances (50 km, 100 km, 150 km).

## Sub-Studies
- **Sub-Study IX-A:** Detector efficiency ($\eta$) sweep ($0.50$ to $0.99$) at $d=50\text{ km}$, $P_{\text{dark}}=10^{-5}$.
- **Sub-Study IX-B:** Dark count rate sweep ($P_{\text{dark}} = 10^{-7}$ to $10^{-3}$) across distances $50\text{ km}, 100\text{ km}, 150\text{ km}$.
- **Sub-Study IX-C:** Practical detector technology comparison (InGaAs SPADs vs SNSPDs).

## How to Re-Run
```powershell
# From qkd-simulator/backend/
& ".\.venv\Scripts\python.exe" tests/runs/2026-06-24_table-ix-detector-efficiency-sweep/suite/run_table9.py
& ".\.venv\Scripts\python.exe" tests/runs/2026-06-24_table-ix-detector-efficiency-sweep/suite/run_table9c.py
```
