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

dist = 30

def run_sim(n, mu, attack_prob):
    rng = np.random.default_rng()
    a = Alice()
    bits = a.generate_bits(n); bases = a.choose_bases(n)
    states = a.encode_states(bits, bases)
    pc = poisson_photon_counts(n, mu, rng)
    states = apply_wcp_to_states(states, pc)
    ch = QuantumChannel(dist, 0.0, detector_efficiency=DETECTOR_EFFICIENCY, dark_count_prob=DARK_COUNT_PROB)
    cs = ch.transmit(states)
    
    if attack_prob > 0:
        pns = PNSAttack(p_block=attack_prob * 0.5, p_split=attack_prob)
        es, pns_stats = pns.attack(cs, rng)
    else:
        es = cs

    bob = Bob(); ms = bob.measure(es)
    p = BB84Protocol(); sr = p.sift(ms); qr = p.estimate_qber(sr)
    skr = compute_skr(sr['sifted_count'], n, qr['qber'])
    return skr, qr['qber'], sr['sifted_count']

mu_values = [0.02, 0.05, 0.08, 0.10, 0.13, 0.15, 0.18, 0.20, 0.23, 0.25, 0.28, 0.30, 0.35, 0.40, 0.45, 0.50, 0.53, 0.55]
n_large = 100000
REPS = 5

print("| mu | SKR_no_Eve | SKR_PNS | QBER_PNS | Sifted_bits | Retention (%) |")
print("| :--- | :--- | :--- | :--- | :--- | :--- |")

for mu in mu_values:
    s_no, s_pns, q_pns, sifted = [], [], [], []
    for _ in range(REPS):
        sk_no, _, si = run_sim(n_large, mu, 0.0)
        sk_p, qp, _ = run_sim(n_large, mu, 1.0)
        s_no.append(sk_no); s_pns.append(sk_p); q_pns.append(qp); sifted.append(si)
    
    mn = np.mean(s_no)
    mp = np.mean(s_pns)
    mq = np.mean(q_pns) * 100
    ms = np.mean(sifted)
    ret = (mp / max(mn, 1e-12)) * 100
    
    print(f"| {mu:.2f} | {mn:.4e} | {mp:.4e} | {mq:.3f}% | {ms:.0f} | {ret:.1f}% |")
