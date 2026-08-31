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

n_bits = 1000000 
distance = 30
noise = 0.0
eta = 0.85
p_dark = 1e-5

def trace_sim(mu):
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
        detector_efficiency=eta, 
        dark_count_prob=p_dark
    )
    channel_states = channel.transmit(states)
    
    bob_no = Bob()
    measured_no = bob_no.measure(channel_states)
    protocol_no = BB84Protocol()
    sift_no = protocol_no.sift(measured_no)
    qber_no = protocol_no.estimate_qber(sift_no)
    skr_no = compute_skr(sift_no['sifted_count'], n_bits, qber_no['qber'])
    
    pns = PNSAttack(p_block=0.5, p_split=1.0)
    eve_states, pns_stats = pns.attack(channel_states, rng)
    
    bob_yes = Bob()
    measured_yes = bob_yes.measure(eve_states)
    protocol_yes = BB84Protocol()
    sift_yes = protocol_yes.sift(measured_yes)
    qber_yes = protocol_yes.estimate_qber(sift_yes)
    skr_yes = compute_skr(sift_yes['sifted_count'], n_bits, qber_yes['qber'])
    
    def breakdown(states_to_measure):
        detected = [s for s in states_to_measure if s.get('detected', False)]
        n_vac = sum(1 for s in detected if s.get('wcp_vacuum', False))
        n_sing = sum(1 for s in detected if s.get('wcp_single', False))
        n_mult = sum(1 for s in detected if s.get('wcp_multi', False))
        return n_vac, n_sing, n_mult, len(detected)
        
    v_no, s_no, m_no, tot_no = breakdown(channel_states)
    v_yes, s_yes, m_yes, tot_yes = breakdown(eve_states)
    
    return {
        'mu': mu,
        'tot_pulses': n_bits,
        'vac_gen': sum(1 for s in states if s.get('wcp_vacuum')),
        'sing_gen': sum(1 for s in states if s.get('wcp_single')),
        'mult_gen': sum(1 for s in states if s.get('wcp_multi')),
        'detected_no_eve': tot_no,
        'det_sing_no': s_no,
        'det_mult_no': m_no,
        'detected_eve': tot_yes,
        'det_sing_eve': s_yes,
        'det_mult_eve': m_yes,
        'sifted_no': sift_no['sifted_count'],
        'sifted_yes': sift_yes['sifted_count'],
        'skr_no': skr_no,
        'skr_yes': skr_yes,
        'skr_retention': skr_yes / max(skr_no, 1e-9)
    }

res_02 = trace_sim(0.02)
res_55 = trace_sim(0.55)

for r in [res_02, res_55]:
    print(f"\n--- mu = {r['mu']} ---")
    print(f"Generated: Vacuum={r['vac_gen']}, Single={r['sing_gen']}, Multi={r['mult_gen']}")
    print(f"Detected (No Eve): Total={r['detected_no_eve']} (Single={r['det_sing_no']}, Multi={r['det_mult_no']})")
    print(f"Detected (PNS): Total={r['detected_eve']} (Single={r['det_sing_eve']}, Multi={r['det_mult_eve']})")
    print(f"Sifted No={r['sifted_no']}, PNS={r['sifted_yes']}")
    print(f"SKR No={r['skr_no']:.4e}, PNS={r['skr_yes']:.4e} -> Retention={r['skr_retention']:.4f}")
