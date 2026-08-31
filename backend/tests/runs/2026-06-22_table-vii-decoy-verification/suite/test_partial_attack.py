import sys, os, numpy as np
sys.path.append(os.path.abspath("."))
from core.alice import Alice
from core.channel import QuantumChannel
from core.bob import Bob
from core.wcp import apply_wcp_to_states
from core.pns import PNSAttack
from core.decoy import assign_decoy_intensities, compute_gains, detect_pns_attack
from core.constants import DETECTOR_EFFICIENCY, DARK_COUNT_PROB

ETA = DETECTOR_EFFICIENCY; P_DARK = DARK_COUNT_PROB

def measure_ratio(n_bits, attack_prob, seed):
    p_block = attack_prob * 0.5; p_split = attack_prob
    rng = np.random.default_rng(seed)
    a = Alice()
    states = a.encode_states(a.generate_bits(n_bits), a.choose_bases(n_bits))
    intensities = assign_decoy_intensities(n_bits, rng)
    states = apply_wcp_to_states(states, rng.poisson(intensities))
    cs = QuantumChannel(0, 0.0, detector_efficiency=ETA, dark_count_prob=P_DARK).transmit(states)
    es, _ = PNSAttack(p_block, p_split).attack(cs, rng)
    ms = Bob().measure(es)
    gains = compute_gains(ms, intensities)
    res = detect_pns_attack(gains, distance_km=0, eta=ETA, dark_count_prob=P_DARK)
    return res['y1_suppression'], res['pns_detected']

print("attack_prob=0.5 (p_block=0.25), d=0km:")
for n_bits in [5000, 20000, 50000]:
    rs = [measure_ratio(n_bits, 0.5, s*100) for s in range(5)]
    ratios = [r[0] for r in rs]
    detected = [r[1] for r in rs]
    print(f"  n_bits={n_bits:6d}: ratios={[f'{r:.3f}' for r in ratios]}  mean={np.mean(ratios):.3f}  detected={sum(detected)}/5")
