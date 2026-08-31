# Test Log
Format: [YYYY-MM-DD] | Run folder | Tests | Result | Notes

---

[2026-06-24] | 2026-06-24_table-ix-detector-efficiency-sweep | 3 sub-studies | COMPLETED | Table IX detector efficiency (0.50-0.99) & dark count (10^-7 - 10^-3) sweeps across 50-150km. Evaluated SPAD vs SNSPD technology limits.
[2026-06-22] | 2026-06-22_table-vii-decoy-verification | 6 configs | 6 COMPLETED | Table VII: Simulated paired attack scenarios at 50km. Identified absolute epsilon threshold bug in decoy.py.
[2026-06-18] | 2026-06-18_table-iii-distance-sweep | 16 dists  | 16 COMPLETED | Table III distance sweep to 140km using n=5,000,000 to ensure stable QBER at sparse counts.
[2026-06-12] | 2026-06-12_table-iv-wcp-mu-sweep | 18 mu vals | 18 COMPLETED | Table IV sweep. Validated 42% -> 62% SKR retention trend under PNS attack.
[2026-06-08] | 2026-06-08_channel-vacuum-bug | 195 tests | 195 PASS / 0 FAIL | Bug hunt for vacuum pulse anomaly. Fixed channel.py to enforce `lost=True` on wcp_vacuum pulses.
[2026-05-04] | 2026-05-04_comprehensive-validation | 85 tests | 85 PASS / 0 FAIL | 8-section empirical suite. All 85 physics tests pass following test_gates.py assertion correction to match PHYSICS_CONTRACT.md. Section 8 (API sync) skipped — requires live backend server.
[2026-05-02] | 2026-05-02_physics-accuracy | 113 tests | 113 PASS / 0 FAIL | Full BB84 physics accuracy suite — gates, WCP/PNS/decoy, property-based (Hypothesis), parameter sweep, physics benchmarks. All physics contract invariants verified.
[2026-03-29] | 2026-03-29_sprint-11-13     | 14 tests  | 14 PASS / 0 FAIL  | Sprint 11-13 component verification — 7 new components integrity checked, store integration verified, 14 physics pipeline tests passed.

---
<!-- New entries go above this line, most recent first -->
