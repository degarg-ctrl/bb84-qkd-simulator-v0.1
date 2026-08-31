import sys, os, numpy as np, time
sys.path.append(os.path.abspath("."))
from core.alice import Alice
from core.channel import QuantumChannel
from core.bob import Bob
from core.protocol import BB84Protocol
from core.wcp import poisson_photon_counts, apply_wcp_to_states
from core.pns import PNSAttack
from core.constants import DETECTOR_EFFICIENCY, DARK_COUNT_PROB
from core.metrics import compute_skr

total_bits = 5000000
chunk_size = 500000
noise = 0.02
reps = 10
distances = [0, 10, 20, 25, 30, 40, 50, 60, 70, 75, 90, 100, 110, 120, 125, 140]

def run_chunk(dist, source_model, mu, attack_prob, n_bits):
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
    return sr['sifted_count'], qr['errors_found'], qr['sample_size']

def run_config(dist, source_model, mu, attack_prob):
    sifted = 0; errors = 0; samples = 0
    for _ in range(total_bits // chunk_size):
        s, e, sm = run_chunk(dist, source_model, mu, attack_prob, chunk_size)
        sifted += s; errors += e; samples += sm
    
    qber = errors / samples if samples > 0 else 0.0
    skr = compute_skr(sifted, total_bits, qber)
    return skr, qber, sifted

print("| Distance (km) | SKR_A | SKR_B | SKR_C | Delta_A-B (%) | Delta_A-C (%) | QBER_C (%) | Ret C/B (%) | Sifted C | Flags |")
print("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

start_time = time.time()

for d in distances:
    skr_A_list, skr_B_list, skr_C_list = [], [], []
    qber_C_list, sifted_C_list = [], []
    
    for _ in range(reps):
        skrA, _, _ = run_config(d, 'ideal', 0, 0.0)
        skrB, _, _ = run_config(d, 'realistic', 0.2, 0.0)
        skrC, qberC, siftedC = run_config(d, 'realistic', 0.2, 1.0)
        skr_A_list.append(skrA); skr_B_list.append(skrB); skr_C_list.append(skrC)
        qber_C_list.append(qberC); sifted_C_list.append(siftedC)
        
    mA = np.mean(skr_A_list)
    mB = np.mean(skr_B_list)
    mC = np.mean(skr_C_list)
    mQ = np.mean(qber_C_list) * 100
    mSifted = np.mean(sifted_C_list)
    
    deltaAB = ((mB - mA) / max(mA, 1e-12)) * 100
    deltaAC = ((mC - mA) / max(mA, 1e-12)) * 100
    retCB = (mC / max(mB, 1e-12)) * 100
    
    flags = "Insufficient sample size" if mSifted < 200 else ""
    
    print(f"| {d} | {mA:.2e} | {mB:.2e} | {mC:.2e} | {deltaAB:+.1f}% | {deltaAC:+.1f}% | {mQ:.2f}% | {retCB:.1f}% | {mSifted:.1f} | {flags} |")

end_time = time.time()
print(f"\nTotal runtime: {(end_time - start_time) / 60:.1f} minutes")
