import sys, os, numpy as np
sys.path.append(os.path.abspath("."))
from core.alice import Alice
from core.channel import QuantumChannel
from core.bob import Bob
from core.protocol import BB84Protocol
from core.wcp import poisson_photon_counts, apply_wcp_to_states
from core.pns import PNSAttack
from core.constants import DETECTOR_EFFICIENCY, DARK_COUNT_PROB

n_bits = 100000
noise = 0.02
reps = 5
distances = [0, 10, 20, 25, 30, 40, 50, 60, 70, 75, 90, 100, 110, 120, 125, 140, 150, 175]

def get_sifted_count(dist):
    rng = np.random.default_rng()
    a = Alice()
    bits = a.generate_bits(n_bits); bases = a.choose_bases(n_bits)
    states = a.encode_states(bits, bases)
    
    pc = poisson_photon_counts(n_bits, 0.2, rng)
    states = apply_wcp_to_states(states, pc)
    
    ch = QuantumChannel(dist, noise, detector_efficiency=DETECTOR_EFFICIENCY, dark_count_prob=DARK_COUNT_PROB)
    cs = ch.transmit(states)
    
    pns = PNSAttack(p_block=0.5, p_split=1.0)
    es, pns_stats = pns.attack(cs, rng)
    
    bob = Bob(); ms = bob.measure(es)
    p = BB84Protocol(); sr = p.sift(ms)
    return sr['sifted_count']

print("| Distance (km) | Mean Sifted Count (C) |")
print("| :--- | :--- |")

for d in distances:
    counts = []
    for _ in range(reps):
        counts.append(get_sifted_count(d))
    mC = np.mean(counts)
    print(f"| {d} | {mC:.1f} |")
