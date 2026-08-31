# Error Log
Format: [YYYY-MM-DD HH:MM] | Branch | Error | Cause | Resolution | Prevention

[2026-05-04 04:19] | main | ERROR: Simulator fails to run for PNS, Partial, and Burst attacks
Cause: frontend API validator in simulatorAPI.js had hardcoded list of allowed strategies that did not match backend schema or ConfigPanel output.
Resolution: Synced validStrategies array in simulatorAPI.js with backend Literal and fixed ConfigPanel value outputs.
Prevention: When updating Enums or Literals in backend schemas, always grep for the values in the frontend to ensure API validators and UI dropdowns are kept in sync.

[2026-05-04 05:22] | main | ERROR: Z gate causes 50.7% QBER (expected <0.10 vs baseline 0%)
Cause: Test assertion in test_gates.py assumed Z gate is a no-op across all bases. Per PHYSICS_CONTRACT.md Section 10, Z gate flips |+> <-> |-> in diagonal basis ('x'), causing ~50% QBER on a mixed basis stream.
Resolution: Corrected test_z_gate_minimal_qber_change assertion to check expected ~0.50 QBER for mixed basis stream per physics specification.
Prevention: Test assertions must be derived from exact quantum state matrix transformations per PHYSICS_CONTRACT.md.

[2026-05-04 05:22] | main | ERROR: X gate shows no bit-flip effect in test_x_gate_bit_flip
Cause: Test measured avg_bob_bit on a 50/50 uniform bit stream (where E[1-B] = 1-E[B] = 0.5), resulting in 0 delta.
Resolution: Corrected test_x_gate_bit_flip assertion to measure QBER delta on '+' basis photons (100% error flip).
Prevention: Bit-flip gate tests must compare QBER or state match against Alice's bit, not the average of a symmetric 50/50 random stream.


[2026-03-12 19:40] | feature/frontend-scaffold | ERROR: docs/ folder missing on branch
Cause: Feature branches created before docs commit on develop. Branch did not have docs/ when checked out.
Resolution: Merged develop into feature/frontend-scaffold to bring docs/ across.
Prevention: Always merge develop into feature branch before starting work on it.

[2026-03-12 19:45] | all-branches | ERROR: PowerShell command incompatibility
Cause: Init prompt used Unix commands (cp, source) not available in PowerShell.
Resolution: Used PowerShell equivalents — Copy-Item, absolute venv paths.
Prevention: All future shell commands in this project must use PowerShell syntax.
Key mappings:
  cp        → Copy-Item
  mv        → Move-Item  
  rm        → Remove-Item
  source    → . (dot operator) or full path activation
  touch     → New-Item -ItemType File
  mkdir -p  → New-Item -ItemType Directory -Force
  curl      → Invoke-WebRequest or curl.exe

[2026-03-12 22:50] | feature/backend-api | ERROR: QBER inflation to 30.9%
Cause: channel.py dark count block overwrote physical 'bit' field directly, corrupting photon state before Eve and Bob processing.
Resolution: Dark count random bit stored in separate 'dark_count_bit' field. Bob reads 'dark_count_bit' when dark_count=True.
Prevention: Channel must never modify 'bit' or 'alice_bit' fields for dark count events. Channel only adds metadata fields.

Template:
[DATETIME] | [branch] | ERROR: [message]
Cause:      [what caused it]
Resolution: [how it was fixed]
Prevention: [rule to prevent recurrence]
