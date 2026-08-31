import sys, os, numpy as np
sys.path.append(os.path.abspath("."))
from core.alice import Alice
from core.channel import QuantumChannel
from core.bob import Bob
from core.wcp import apply_wcp_to_states
from core.pns import PNSAttack
from core.decoy import assign_decoy_intensities, compute_gains
from core.constants import DETECTOR_EFFICIENCY, DARK_COUNT_PROB
from core.detector import P_survive

n_bits = 200000
MU_SIGNAL = 0.5
MU_DECOY  = 0.1
ETA       = DETECTOR_EFFICIENCY
P_DARK    = DARK_COUNT_PROB

def estimate_y1_lmc(Q_s, Q_d, Q_vac, mu_s, mu_d):
    Y_0 = Q_vac
    denom_full = mu_s * mu_d - mu_d**2
    Y_1_L = (mu_s / denom_full) * (
        Q_d * np.exp(mu_d)
        - Q_s * np.exp(mu_s) * (mu_d**2 / mu_s**2)
        - (mu_s**2 - mu_d**2) / mu_s**2 * Y_0
    )
    return Y_1_L, Y_0

def expected_y1(dist):
    p_s = P_survive(dist)
    return p_s * ETA + P_DARK

def measure_y1(dist, attack_prob, seed):
    rng = np.random.default_rng(seed)
    a = Alice()
    bits  = a.generate_bits(n_bits)
    bases = a.choose_bases(n_bits)
    states = a.encode_states(bits, bases)
    intensities = assign_decoy_intensities(n_bits, rng)
    pc = rng.poisson(intensities)
    states = apply_wcp_to_states(states, pc)
    ch = QuantumChannel(dist, 0.02, detector_efficiency=ETA, dark_count_prob=P_DARK)
    cs = ch.transmit(states)
    if attack_prob > 0:
        pns = PNSAttack(p_block=attack_prob * 0.5, p_split=attack_prob)
        es, _ = pns.attack(cs, rng)
    else:
        es = cs
    bob = Bob()
    ms = bob.measure(es)
    gains = compute_gains(ms, intensities)
    Y_1_L, Y_0 = estimate_y1_lmc(gains['signal_gain'], gains['decoy_gain'], gains['vacuum_gain'], MU_SIGNAL, MU_DECOY)
    return Y_1_L

print("Running 5-rep stability check for each scenario...")
THRESHOLD = 0.6

scenarios = [
    ("Clean d=0km",  0,  0.0, False),
    ("PNS   d=0km",  0,  1.0, True),
    ("Clean d=50km", 50, 0.0, False),
    ("PNS   d=50km", 50, 1.0, True),
]

for name, dist, atk, expect_detected in scenarios:
    ratios = []
    for seed in range(5):
        Y_1_L = measure_y1(dist, atk, seed * 17)
        Y_1_exp = expected_y1(dist)
        ratios.append(Y_1_L / Y_1_exp)
    mean_r = np.mean(ratios)
    detected = mean_r < THRESHOLD
    correct = detected == expect_detected
    print(f"{name}: mean Y_1_L/Y_1_exp={mean_r:.4f}  threshold={THRESHOLD} -> {'DETECTED' if detected else 'clean'} {'OK' if correct else 'WRONG'}")
    for i, r in enumerate(ratios):
        print(f"   rep {i}: {r:.4f}")
    print()
