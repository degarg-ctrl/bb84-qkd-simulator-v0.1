import sys
import os
import numpy as np

sys.path.append(os.path.abspath("."))

from core.alice import Alice
from core.channel import QuantumChannel
from core.eve import Eve
from core.bob import Bob
from core.protocol import BB84Protocol
from core.metrics import compute_skr, binary_entropy

def investigate(distance_km, noise_level, n_bits=1000000):
    alice = Alice()
    bits = alice.generate_bits(n_bits)
    bases = alice.choose_bases(n_bits)
    states = alice.encode_states(bits, bases)
    
    # We will use the proper baseline parameters for these tests (eta=0.85, P_dark=1e-5)
    # to show what happens when the correct efficiency is applied.
    channel = QuantumChannel(distance_km=distance_km, noise_level=noise_level, 
                             detector_efficiency=0.85, dark_count_prob=1e-5)
    
    channel_states = channel.transmit(states)
    
    eve = Eve(attack_strategy='none', attack_prob=0.0)
    eve_states = eve.intercept(channel_states)
    
    bob = Bob()
    measured_states = bob.measure(eve_states)
    
    protocol = BB84Protocol()
    sift_result = protocol.sift(measured_states)
    qber_result = protocol.estimate_qber(sift_result)
    
    skr = compute_skr(sift_result['sifted_count'], n_bits, qber_result['qber'])
    
    S = sift_result['sifted_count'] / n_bits
    Q = qber_result['qber']
    H_Q = binary_entropy(Q) if Q > 0 else 0.0
    calc_skr = S * (1 - 2 * H_Q)
    
    actual_detected = sum(1 for s in channel_states if s['detected'])
    p_det_used = actual_detected / n_bits
    
    print(f"=== TEST at {distance_km}km ===")
    print(f"Exact sifted key length: {sift_result['sifted_count']} (S = {S:.6f})")
    print(f"Exact QBER (Q): {Q:.6f}")
    print(f"Binary entropy H(Q): {H_Q:.6f}")
    print(f"Final SKR (S * (1 - 2*H(Q))): {calc_skr:.6e}")
    if distance_km == 50:
        print(f"P_det({distance_km}km) actually used: {p_det_used:.6f}")
        print(f"Validated P_survive({distance_km}km): {channel.p_survive:.6f}")
    print()

investigate(0, 0.02, 1000000)
investigate(50, 0.02, 1000000)
