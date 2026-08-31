# Findings

**Root Cause**: `apply_wcp_to_states` correctly set `detected=False` for vacuum pulses, but `lost` wasn't being explicitly set to `True`. As a result, `QuantumChannel.transmit()` treated these vacuum pulses as actual surviving photons.
**Resolution**: Modified `channel.py` to properly enforce `lost=True` for vacuum pulses, ensuring they do not contribute to sifted keys or skew QBER under attack.
