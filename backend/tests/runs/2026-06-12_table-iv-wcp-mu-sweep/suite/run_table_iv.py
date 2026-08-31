import sys
import os
import numpy as np

sys.path.append(os.path.abspath("."))

from core.alice import Alice
from core.channel import QuantumChannel
from core.bob import Bob
from core.protocol import BB84Protocol
from core.metrics import compute_skr
from core.wcp import poisson_photon_counts, apply_wcp_to_states
from core.pns import PNSAttack
from core.constants import DETECTOR_EFFICIENCY, DARK_COUNT_PROB

mu_values = [0.02, 0.05, 0.08, 0.10, 0.13, 0.15, 0.18, 0.20, 0.23, 0.25, 0.28, 0.30, 0.35, 0.40, 0.45, 0.50, 0.53, 0.55]

n_bits = 10000
distance = 30
noise = 0.0

def run_sim(mu, attack_prob):
    rng = np.random.default_rng()
    alice = Alice()
    bits = alice.generate_bits(n_bits)
    bases = alice.choose_bases(n_bits)
    states = alice.encode_states(bits, bases)
    
    photon_counts = poisson_photon_counts(n_bits, mu, rng)
    states = apply_wcp_to_states(states, photon_counts)
    
    channel = QuantumChannel(
        distance_km=distance, 
        noise_level=noise, 
        detector_efficiency=DETECTOR_EFFICIENCY, 
        dark_count_prob=DARK_COUNT_PROB
    )
    channel_states = channel.transmit(states)
    
    if attack_prob > 0:
        pns = PNSAttack(p_block=attack_prob * 0.5, p_split=attack_prob)
        eve_states, _ = pns.attack(channel_states, rng)
    else:
        eve_states = channel_states
        
    bob = Bob()
    measured_states = bob.measure(eve_states)
    
    protocol = BB84Protocol()
    sift_result = protocol.sift(measured_states)
    qber_result = protocol.estimate_qber(sift_result)
    skr = compute_skr(sift_result['sifted_count'], n_bits, qber_result['qber'])
    
    return skr, qber_result['qber'], sift_result['sifted_count']

print("| $\mu$ | SKR_no_Eve | SKR_PNS | QBER_PNS | Sifted_bits | Flags |")
print("| :--- | :--- | :--- | :--- | :--- | :--- |")

for mu in mu_values:
    skr_no_eve_list = []
    skr_pns_list = []
    qber_pns_list = []
    sifted_list = []
    
    for _ in range(3):
        skr_no, _, sifted_no = run_sim(mu, 0.0)
        skr_pns, qber_pns, _ = run_sim(mu, 1.0)
        
        skr_no_eve_list.append(skr_no)
        skr_pns_list.append(skr_pns)
        qber_pns_list.append(qber_pns)
        sifted_list.append(sifted_no)
        
    m_skr_no = np.mean(skr_no_eve_list)
    m_skr_pns = np.mean(skr_pns_list)
    m_qber_pns = np.mean(qber_pns_list) * 100
    m_sifted = np.mean(sifted_list)
    
    flag = ""
    if m_qber_pns > 1.0:
        flag += "High QBER "
    
    if m_skr_no > 1e-9 and abs(m_skr_pns - m_skr_no) / m_skr_no > 0.05:
        flag += "SKR Drop (>5%) "
        
    if flag == "":
        flag = "None"
        
    print(f"| {mu:.2f} | {m_skr_no:.4e} | {m_skr_pns:.4e} | {m_qber_pns:.3f}% | {m_sifted:.0f} | {flag} |")
