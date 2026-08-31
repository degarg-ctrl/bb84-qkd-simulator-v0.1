import sys, os, numpy as np, time
sys.path.append(os.path.abspath("."))
from core.alice import Alice
from core.channel import QuantumChannel
from core.bob import Bob
from core.protocol import BB84Protocol
from core.wcp import poisson_photon_counts, apply_wcp_to_states
from core.pns import PNSAttack
from core.constants import DETECTOR_EFFICIENCY, DARK_COUNT_PROB

total_bits = 5000000
chunk_size = 500000
noise = 0.02
reps = 10
d = 175

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
    p = BB84Protocol(); sr = p.sift(ms)
    return sr['sifted_count']

def run_config(dist, source_model, mu, attack_prob):
    sifted = 0
    for _ in range(total_bits // chunk_size):
        sifted += run_chunk(dist, source_model, mu, attack_prob, chunk_size)
    return sifted

start = time.time()
counts_C = []
for i in range(reps):
    run_config(d, 'ideal', 0, 0.0)
    run_config(d, 'realistic', 0.2, 0.0)
    counts_C.append(run_config(d, 'realistic', 0.2, 1.0))
    print(f"Rep {i+1} done", flush=True)

end = time.time()
print(f"Time for {reps} reps of A, B, C at {d}km: {end-start:.2f} seconds")
print(f"Mean sifted_count (C) at {d}km: {np.mean(counts_C):.1f}")
