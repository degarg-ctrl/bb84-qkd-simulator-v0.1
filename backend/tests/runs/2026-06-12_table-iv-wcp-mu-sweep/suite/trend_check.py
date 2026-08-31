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
        pns_stats = {}

    bob = Bob(); ms = bob.measure(es)
    p = BB84Protocol(); sr = p.sift(ms); qr = p.estimate_qber(sr)
    skr = compute_skr(sr['sifted_count'], n, qr['qber'])
    
    # Count detected pulse types in the post-attack state
    detected_single = sum(1 for s in es if s.get('detected') and s.get('wcp_single'))
    detected_multi  = sum(1 for s in es if s.get('detected') and s.get('wcp_multi'))
    detected_total  = sum(1 for s in es if s.get('detected'))
    
    return skr, qr['qber'], sr['sifted_count'], detected_single, detected_multi, detected_total, pns_stats

n_large = 100000
REPS = 5

print("=== TREND VERIFICATION (n=100,000, 5 reps) ===")
print(f"{'mu':>5} | {'SKR_noEve':>10} | {'SKR_PNS':>10} | {'Ret%':>6} | {'det_single(noEve)':>17} | {'det_single(PNS)':>15} | {'det_multi(PNS)':>14}")
print("-"*105)

for mu in [0.02, 0.10, 0.20, 0.30, 0.40, 0.55]:
    s_no, s_pns, ret_list = [], [], []
    ds_no_list, ds_pns_list, dm_pns_list = [], [], []
    
    for _ in range(REPS):
        skr_no, _, _, ds_no, _, _, _ = run_sim(n_large, mu, 0.0)
        skr_p, _, _, ds_p, dm_p, _, stats = run_sim(n_large, mu, 1.0)
        s_no.append(skr_no); s_pns.append(skr_p)
        ret_list.append(skr_p / max(skr_no, 1e-12))
        ds_no_list.append(ds_no); ds_pns_list.append(ds_p); dm_pns_list.append(dm_p)
    
    mn = np.mean(s_no); mp = np.mean(s_pns); ret = np.mean(ret_list) * 100
    print(f"{mu:>5.2f} | {mn:>10.4e} | {mp:>10.4e} | {ret:>6.1f}% | {np.mean(ds_no_list):>17.0f} | {np.mean(ds_pns_list):>15.0f} | {np.mean(dm_pns_list):>14.0f}")
