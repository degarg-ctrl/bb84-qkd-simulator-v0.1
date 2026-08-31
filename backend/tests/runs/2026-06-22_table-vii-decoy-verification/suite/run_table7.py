import sys, os, numpy as np
sys.path.append(os.path.abspath("."))
from core.alice import Alice
from core.channel import QuantumChannel
from core.bob import Bob
from core.protocol import BB84Protocol
from core.wcp import poisson_photon_counts, apply_wcp_to_states
from core.pns import PNSAttack
from core.eve import Eve
from core.decoy import assign_decoy_intensities, compute_gains, detect_pns_attack
from core.constants import DETECTOR_EFFICIENCY, DARK_COUNT_PROB
from core.metrics import compute_skr

n_bits = 100000
dist = 50
noise = 0.02
reps = 5

def run_config(source_model, strategy, eve_attack, mu=None, decoy=False):
    rng = np.random.default_rng()
    a = Alice()
    bits = a.generate_bits(n_bits); bases = a.choose_bases(n_bits)
    states = a.encode_states(bits, bases)
    
    if source_model == 'realistic':
        if decoy:
            intensities = assign_decoy_intensities(n_bits, rng)
            pc = rng.poisson(intensities)
        else:
            pc = poisson_photon_counts(n_bits, mu, rng)
            intensities = None
            
        states = apply_wcp_to_states(states, pc)
        det_eff = DETECTOR_EFFICIENCY
        dark_prob = DARK_COUNT_PROB
    else:
        det_eff = 1.0
        dark_prob = 0.0
        intensities = None

    if strategy == 'intercept-resend' and eve_attack > 0:
        eve = Eve(attack_strategy='intercept_resend', attack_prob=eve_attack)
        cs = eve.intercept(states)
    else:
        cs = states

    ch = QuantumChannel(dist, noise, detector_efficiency=det_eff, dark_count_prob=dark_prob)
    cs = ch.transmit(cs)
    
    if strategy == 'pns' and eve_attack > 0:
        pns = PNSAttack(p_block=eve_attack * 0.5, p_split=eve_attack)
        es, pns_stats = pns.attack(cs, rng)
    else:
        es = cs

    bob = Bob(); ms = bob.measure(es)
    
    decoy_alert = False
    if decoy:
        gains = compute_gains(ms, intensities)
        pns_res = detect_pns_attack(gains)
        decoy_alert = pns_res['pns_detected']
        
    p = BB84Protocol(); sr = p.sift(ms); qr = p.estimate_qber(sr)
    extract = p.extract_key(qr)
    status = "Aborted" if extract['session_aborted'] else "Continued"
    
    if decoy_alert:
        status = "Aborted"
        
    skr = compute_skr(sr['sifted_count'], n_bits, qr['qber'])
    return skr, qr['qber'], sr['sifted_count'], status, decoy_alert

configs = [
    ("A", 'ideal', None, 0.0, None, False),
    ("B", 'ideal', 'intercept-resend', 1.0, None, False),
    ("C", 'ideal', 'intercept-resend', 0.36, None, False),
    ("D", 'realistic', 'pns', 1.0, 0.20, False),
    ("E", 'realistic', 'pns', 1.0, 0.40, False),
    ("F", 'realistic', 'pns', 1.0, 0.20, True)
]

base_configs = {
    "Base_D": ('realistic', None, 0.0, 0.20, False),
    "Base_E": ('realistic', None, 0.0, 0.40, False)
}

print("| Run | Configuration | QBER (%) | SKR (bits/pulse) | Sifted | Status | Decoy Alert | Ret. Ratio (%) |")
print("|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|")

# Precompute baselines
base_D_skr_list = []
base_E_skr_list = []
for _ in range(reps):
    skrD, _, _, _, _ = run_config(*base_configs["Base_D"])
    skrE, _, _, _, _ = run_config(*base_configs["Base_E"])
    base_D_skr_list.append(skrD)
    base_E_skr_list.append(skrE)
mean_base_D = np.mean(base_D_skr_list)
mean_base_E = np.mean(base_E_skr_list)

for run_name, src, strat, attk, mu, dec in configs:
    skr_list, qber_list, sifted_list = [], [], []
    aborted_count = 0
    decoy_alert_count = 0
    for _ in range(reps):
        skr, qb, sift, stat, d_alrt = run_config(src, strat, attk, mu, dec)
        skr_list.append(skr); qber_list.append(qb); sifted_list.append(sift)
        if stat == "Aborted": aborted_count += 1
        if d_alrt: decoy_alert_count += 1
        
    m_skr = np.mean(skr_list)
    m_qb = np.mean(qber_list) * 100
    m_sift = np.mean(sifted_list)
    stat_str = "Aborted" if aborted_count > reps/2 else "Continued"
    d_alrt_str = "Yes" if decoy_alert_count > reps/2 else "No"
    
    ret_ratio = "N/A"
    if run_name == "D":
        ret_ratio = f"{(m_skr / max(mean_base_D, 1e-12)) * 100:.1f}%"
    elif run_name == "E":
        ret_ratio = f"{(m_skr / max(mean_base_E, 1e-12)) * 100:.1f}%"
        
    desc = f"{src}, {strat if strat else 'No attack'}, mu={mu if mu else 'N/A'}, eve={attk}"
    if dec: desc += " (Decoy)"
    print(f"| {run_name} | {desc} | {m_qb:.2f}% | {m_skr:.2e} | {m_sift:.1f} | {stat_str} | {d_alrt_str} | {ret_ratio} |")
