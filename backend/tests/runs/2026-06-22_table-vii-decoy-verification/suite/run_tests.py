import sys
import os
import numpy as np
import json

sys.path.append(os.path.abspath("."))

from core.alice import Alice
from core.channel import QuantumChannel
from core.eve import Eve
from core.bob import Bob
from core.protocol import BB84Protocol
from core.metrics import compute_skr, compute_efficiency
from core.wcp import poisson_photon_counts, classify_pulses, apply_wcp_to_states
from core.pns import PNSAttack
from core.decoy import assign_decoy_intensities, compute_gains, detect_pns_attack
from core.detector import P_det, Q_dark

def run_test_1():
    n_bits = 10000
    alice = Alice()
    bits = alice.generate_bits(n_bits)
    bases = alice.choose_bases(n_bits)
    states = alice.encode_states(bits, bases)
    
    channel = QuantumChannel(distance_km=0, noise_level=0.0, detector_efficiency=1.0, dark_count_prob=0.0)
    channel_states = channel.transmit(states)
    
    eve = Eve(attack_strategy='none', attack_prob=0.0)
    eve_states = eve.intercept(channel_states)
    
    bob = Bob()
    measured_states = bob.measure(eve_states)
    
    protocol = BB84Protocol()
    sift_result = protocol.sift(measured_states)
    qber_result = protocol.estimate_qber(sift_result)
    
    return qber_result['qber'] * 100

def run_test_2():
    n_bits = 10000
    alice = Alice()
    bits = alice.generate_bits(n_bits)
    bases = alice.choose_bases(n_bits)
    states = alice.encode_states(bits, bases)
    
    channel = QuantumChannel(distance_km=0, noise_level=0.0, detector_efficiency=1.0, dark_count_prob=0.0)
    channel_states = channel.transmit(states)
    
    eve = Eve(attack_strategy='intercept_resend', attack_prob=1.0)
    eve_states = eve.intercept(channel_states)
    
    bob = Bob()
    measured_states = bob.measure(eve_states)
    
    protocol = BB84Protocol()
    sift_result = protocol.sift(measured_states)
    qber_result = protocol.estimate_qber(sift_result)
    
    return qber_result['qber'] * 100

def run_test_3():
    n_bits = 10000
    rng = np.random.default_rng()
    photon_counts = poisson_photon_counts(n_bits, 0.2, rng)
    stats = classify_pulses(photon_counts)
    return stats['multi_fraction'] * 100

def run_test_4():
    channel = QuantumChannel(distance_km=50, noise_level=0.0)
    return channel.p_survive * 100

def run_test_5():
    n_bits = 10000
    alice = Alice()
    bits = alice.generate_bits(n_bits)
    bases = alice.choose_bases(n_bits)
    states = alice.encode_states(bits, bases)
    
    channel = QuantumChannel(distance_km=0, noise_level=0.02, detector_efficiency=1.0, dark_count_prob=0.0)
    channel_states = channel.transmit(states)
    
    eve = Eve(attack_strategy='none', attack_prob=0.0)
    eve_states = eve.intercept(channel_states)
    
    bob = Bob()
    measured_states = bob.measure(eve_states)
    
    protocol = BB84Protocol()
    sift_result = protocol.sift(measured_states)
    qber_result = protocol.estimate_qber(sift_result)
    skr = compute_skr(sift_result['sifted_count'], n_bits, qber_result['qber'])
    return skr

def run_test_6():
    n_bits = 10000
    alice = Alice()
    bits = alice.generate_bits(n_bits)
    bases = alice.choose_bases(n_bits)
    states = alice.encode_states(bits, bases)
    
    channel = QuantumChannel(distance_km=50, noise_level=0.02, detector_efficiency=1.0, dark_count_prob=0.0)
    channel_states = channel.transmit(states)
    
    eve = Eve(attack_strategy='none', attack_prob=0.0)
    eve_states = eve.intercept(channel_states)
    
    bob = Bob()
    measured_states = bob.measure(eve_states)
    
    protocol = BB84Protocol()
    sift_result = protocol.sift(measured_states)
    qber_result = protocol.estimate_qber(sift_result)
    skr = compute_skr(sift_result['sifted_count'], n_bits, qber_result['qber'])
    return skr

def run_test_7():
    n_bits = 10000
    rng = np.random.default_rng()
    
    alice = Alice()
    bits = alice.generate_bits(n_bits)
    bases = alice.choose_bases(n_bits)
    states = alice.encode_states(bits, bases)
    
    decoy_intensities = assign_decoy_intensities(n_bits, rng)
    photon_counts = np.array([rng.poisson(mu) for mu in decoy_intensities])
    states = apply_wcp_to_states(states, photon_counts)
    
    channel = QuantumChannel(distance_km=50, noise_level=0.0)
    channel_states = channel.transmit(states)
    
    pns = PNSAttack(p_block=0.5, p_split=1.0)
    eve_states, _ = pns.attack(channel_states, rng)
    
    bob = Bob()
    measured_states = bob.measure(eve_states)
    
    gains = compute_gains(measured_states, decoy_intensities)
    decoy_results = detect_pns_attack(gains)
    
    return decoy_results['pns_detected']

def run_test_8():
    n_bits = 10000
    rng = np.random.default_rng()
    
    alice = Alice()
    bits = alice.generate_bits(n_bits)
    bases = alice.choose_bases(n_bits)
    states = alice.encode_states(bits, bases)
    
    photon_counts = poisson_photon_counts(n_bits, 0.2, rng)
    states = apply_wcp_to_states(states, photon_counts)
    
    channel = QuantumChannel(distance_km=50, noise_level=0.0)
    channel_states = channel.transmit(states)
    
    pns = PNSAttack(p_block=0.5, p_split=1.0)
    eve_states, _ = pns.attack(channel_states, rng)
    
    bob = Bob()
    measured_states = bob.measure(eve_states)
    
    protocol = BB84Protocol()
    sift_result = protocol.sift(measured_states)
    qber_result = protocol.estimate_qber(sift_result)
    
    return qber_result['qber'] * 100

def run_test_9():
    val = P_det(d=0, eta=0.85, P_dark=1e-5)
    return val

def run_test_10():
    val = Q_dark(d=100, eta=0.85, P_dark=1e-5)
    return val * 100

tests = [run_test_1, run_test_2, run_test_3, run_test_4, run_test_5, run_test_6, run_test_7, run_test_8, run_test_9, run_test_10]
results = []

for i, test_func in enumerate(tests):
    runs = []
    for _ in range(3):
        runs.append(test_func())
    
    if isinstance(runs[0], bool) or isinstance(runs[0], np.bool_):
        mean_val = bool(all(runs))
    else:
        mean_val = float(sum(runs) / 3.0)
    results.append(mean_val)

print(json.dumps(results))
