import sys, os, numpy as np
sys.path.append(os.path.abspath("."))
from core.alice import Alice
from core.channel import QuantumChannel
from core.bob import Bob
from core.wcp import apply_wcp_to_states
from core.pns import PNSAttack
from core.decoy import assign_decoy_intensities, compute_gains, detect_pns_attack
from core.constants import DETECTOR_EFFICIENCY, DARK_COUNT_PROB

n_bits = 200000
ETA    = DETECTOR_EFFICIENCY
P_DARK = DARK_COUNT_PROB

def run_scenario(name, dist, attack_prob):
    rng = np.random.default_rng(42)
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
    res   = detect_pns_attack(gains, distance_km=dist, eta=ETA, dark_count_prob=P_DARK)
    correct = (attack_prob > 0) == res['pns_detected']
    print(f"{'PASS' if correct else 'FAIL'} | {name}")
    print(f"     Q_signal={gains['signal_gain']:.6f}  Q_decoy={gains['decoy_gain']:.6f}  Q_vac={gains['vacuum_gain']:.8f}")
    print(f"     Y_1_L={res['y1_lower_bound']:.6f}  Y_1_exp={res['y1_expected']:.6f}  ratio={res['y1_suppression']:.4f}  threshold={res['threshold_used']}")
    print(f"     pns_detected={res['pns_detected']}  confidence={res['confidence']:.4f}")
    print()

run_scenario("Clean baseline d=0km  (expect NOT detected)", 0,  0.0)
run_scenario("PNS attack   d=0km  (expect DETECTED)",       0,  1.0)
run_scenario("Clean baseline d=50km (expect NOT detected)", 50, 0.0)
run_scenario("PNS attack   d=50km (expect DETECTED)",       50, 1.0)
