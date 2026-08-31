import sys, os, numpy as np
sys.path.append(os.path.abspath("."))
from core.alice import Alice
from core.channel import QuantumChannel
from core.bob import Bob
from core.wcp import apply_wcp_to_states
from core.pns import PNSAttack
from core.decoy import assign_decoy_intensities, compute_gains, detect_pns_attack

rng = np.random.default_rng(42)
n_bits = 100000
a = Alice()
bits = a.generate_bits(n_bits); bases = a.choose_bases(n_bits)
states = a.encode_states(bits, bases)

intensities = assign_decoy_intensities(n_bits, rng)
pc = rng.poisson(intensities)
states = apply_wcp_to_states(states, pc)

print("Total states generated:", len(states))
ch = QuantumChannel(50, 0.02)
cs = ch.transmit(states)
print("States after channel:", len(cs))

pns = PNSAttack(p_block=0.5, p_split=1.0)
es, _ = pns.attack(cs, rng)
print("States after Eve:", len(es))

bob = Bob()
ms = bob.measure(es)
print("States after Bob:", len(ms))

gains = compute_gains(ms, intensities)
print(gains)

res = detect_pns_attack(gains)
print("PNS Detected:", res['pns_detected'])

