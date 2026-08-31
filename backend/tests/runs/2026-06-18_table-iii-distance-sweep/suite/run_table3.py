import sys, os, numpy as np
sys.path.append(os.path.abspath("."))
from core.alice import Alice
from core.channel import QuantumChannel
from core.bob import Bob
from core.protocol import BB84Protocol
from core.metrics import compute_skr
from core.wcp import poisson_photon_counts, apply_wcp_to_states
from core.pns import PNSAttack
from core.constants import DETECTOR_EFFICIENCY, DARK_COUNT_PROB

n_bits = 100000
noise = 0.02
reps = 5
distances = [0, 10, 20, 25, 30, 40, 50, 60, 70, 75, 90, 100, 110, 120, 125, 140, 150, 175]

def run_config(dist, source_model, mu, attack_prob):
    rng = np.random.default_rng()
    a = Alice()
    bits = a.generate_bits(n_bits); bases = a.choose_bases(n_bits)
    states = a.encode_states(bits, bases)
    
    if source_model == 'realistic':
        pc = poisson_photon_counts(n_bits, mu, rng)
        states = apply_wcp_to_states(states, pc)
        det_eff = DETECTOR_EFFICIENCY
        dark_prob = DARK_COUNT_PROB
    else:
        det_eff = 1.0
        dark_prob = 0.0

    ch = QuantumChannel(dist, noise, detector_efficiency=det_eff, dark_count_prob=dark_prob)
    cs = ch.transmit(states)
    
    if attack_prob > 0:
        pns = PNSAttack(p_block=attack_prob * 0.5, p_split=attack_prob)
        es, pns_stats = pns.attack(cs, rng)
    else:
        es = cs

    bob = Bob(); ms = bob.measure(es)
    p = BB84Protocol(); sr = p.sift(ms); qr = p.estimate_qber(sr)
    skr = compute_skr(sr['sifted_count'], n_bits, qr['qber'])
    return skr, qr['qber']

print("| Distance (km) | SKR_A (mean±std) | SKR_B (mean±std) | SKR_C (mean±std) | Delta_A-B (%) | Delta_A-C (%) | QBER_C (%) | Retention C/B (%) |")
print("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

for d in distances:
    skr_A_list, skr_B_list, skr_C_list = [], [] , []
    qber_C_list = []
    
    for _ in range(reps):
        skrA, _ = run_config(d, 'ideal', 0, 0.0)
        skrB, _ = run_config(d, 'realistic', 0.2, 0.0)
        skrC, qberC = run_config(d, 'realistic', 0.2, 1.0)
        skr_A_list.append(skrA); skr_B_list.append(skrB); skr_C_list.append(skrC); qber_C_list.append(qberC)
        
    mA, stdA = np.mean(skr_A_list), np.std(skr_A_list)
    mB, stdB = np.mean(skr_B_list), np.std(skr_B_list)
    mC, stdC = np.mean(skr_C_list), np.std(skr_C_list)
    mQ = np.mean(qber_C_list) * 100
    
    deltaAB = ((mB - mA) / max(mA, 1e-12)) * 100
    deltaAC = ((mC - mA) / max(mA, 1e-12)) * 100
    retCB = (mC / max(mB, 1e-12)) * 100
    
    print(f"| {d} | {mA:.2e}±{stdA:.2e} | {mB:.2e}±{stdB:.2e} | {mC:.2e}±{stdC:.2e} | {deltaAB:+.1f}% | {deltaAC:+.1f}% | {mQ:.2f}% | {retCB:.1f}% |")
