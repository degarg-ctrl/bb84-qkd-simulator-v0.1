import sys, os, numpy as np
sys.path.append(os.path.abspath("."))
from core.alice import Alice
from core.channel import QuantumChannel
from core.bob import Bob
from core.wcp import apply_wcp_to_states
from core.pns import PNSAttack
from core.decoy import assign_decoy_intensities, compute_gains, detect_pns_attack
from core.constants import DETECTOR_EFFICIENCY, DARK_COUNT_PROB

n_bits = 100000

def run_scenario(name, dist, attack_prob, mu):
    rng = np.random.default_rng(42) # fixed seed for reproducibility
    a = Alice()
    bits = a.generate_bits(n_bits); bases = a.choose_bases(n_bits)
    states = a.encode_states(bits, bases)
    
    intensities = assign_decoy_intensities(n_bits, rng)
    pc = rng.poisson(intensities)
    
    states = apply_wcp_to_states(states, pc)
    
    ch = QuantumChannel(dist, 0.02, detector_efficiency=DETECTOR_EFFICIENCY, dark_count_prob=DARK_COUNT_PROB)
    cs = ch.transmit(states)
    
    if attack_prob > 0:
        pns = PNSAttack(p_block=attack_prob * 0.5, p_split=attack_prob)
        es, _ = pns.attack(cs, rng)
    else:
        es = cs
        
    bob = Bob()
    ms = bob.measure(es)
    
    gains = compute_gains(ms, intensities)
    res = detect_pns_attack(gains)
    
    print(f"--- {name} ---")
    print(f"Distance: {dist}km | mu: {mu} | attack_prob: {attack_prob}")
    print(f"Q_signal: {gains['signal_gain']:.6f}")
    print(f"Q_decoy:  {gains['decoy_gain']:.6f}")
    print(f"Q_vacuum: {gains['vacuum_gain']:.6f}")
    print(f"Norm_signal (Q_s/mu_s): {gains['normalized_signal']:.6f}")
    print(f"Norm_decoy  (Q_d/mu_d): {gains['normalized_decoy']:.6f}")
    print(f"gain_ratio_diff:        {res['gain_difference']:.6f}")
    print(f"Decoy Alert Triggered?: {res['pns_detected']}")
    print("")

run_scenario("Run F at 50km", dist=50, attack_prob=1.0, mu=0.2)
run_scenario("Run F at 0km", dist=0, attack_prob=1.0, mu=0.2)
run_scenario("Clean Baseline at 0km", dist=0, attack_prob=0.0, mu=0.2)
