# Test Findings: Table IX Detector Efficiency and Dark Count Analysis

## 1. Detector Efficiency ($\eta$) Trends (Sub-Study IX-A)
- Increasing detector quantum efficiency from $0.50$ to $0.99$ yields a proportional increase in sifted photon counts ($467 \to 872$ counts at $N=100,000$, $50\text{ km}$).
- Secret Key Rate (SKR) scales monotonically with efficiency ($\sim 3.9 \times 10^{-3} \to 6.6 \times 10^{-3}$), reflecting higher yield without introducing state distortion.

## 2. Dark Count Probability ($P_{\text{dark}}$) & Distance Limits (Sub-Study IX-B)
- At moderate distances ($50\text{ km}$), dark count rates up to $10^{-4}$ contribute minimal error ($Q_{\text{dark}} < 0.05\%$), keeping sessions securely continued.
- When $P_{\text{dark}} \ge 10^{-3}$, dark count noise rapidly drives $Q_{\text{eff}}$ towards $5\%$, reducing SKR.
- At long distances ($100\text{ km}$ and $150\text{ km}$), photon loss along the fiber ($0.2\text{ dB/km}$) drastically diminishes true signal arrival. In this regime, dark count noise dominates, pushing effective QBER above the $11\%$ security threshold and triggering automatic session aborts.

## 3. Technology Comparison (Sub-Study IX-C)
- High-efficiency, ultra-low dark count detectors (SNSPDs: $\eta \ge 0.90$, $P_{\text{dark}} \le 10^{-8}$) sustain valid key exchange at extended distances where standard InGaAs SPADs fail due to thermal dark noise.
