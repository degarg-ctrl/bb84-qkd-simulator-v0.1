import sys, os, time, numpy as np
sys.path.append(os.path.abspath("."))
from core.alice import Alice
from core.channel import QuantumChannel
from core.bob import Bob
from core.protocol import BB84Protocol
from core.wcp import poisson_photon_counts, apply_wcp_to_states
from core.metrics import compute_skr
from core.detector import Q_dark

n_bits = 100000
reps = 5
noise = 0.02
mu = 0.2

# Confirm channel vacuum bug is active
test_pc = np.array([0, 1])
test_states = [{'bit':0, 'basis':0, 'state':'H'}, {'bit':1, 'basis':0, 'state':'V'}]
test_states = apply_wcp_to_states(test_states, test_pc)
test_ch = QuantumChannel(10, 0, detector_efficiency=1.0, dark_count_prob=0.0)
test_res = test_ch.transmit(test_states)
assert test_res[0].get('lost', False) == True, "Vacuum pulse fix is NOT active!"
print("Confirmed channel.py vacuum-pulse fix is active.\n")

def run_config(dist, eta, p_dark):
    skrs, q_effs, sifteds, aborteds = [], [], [], []
    for rep in range(reps):
        rng = np.random.default_rng(rep * 42 + hash(f"{dist}_{eta}_{p_dark}") % 10000)
        a = Alice()
        bits = a.generate_bits(n_bits)
        bases = a.choose_bases(n_bits)
        states = a.encode_states(bits, bases)
        
        pc = poisson_photon_counts(n_bits, mu, rng)
        states = apply_wcp_to_states(states, pc)
        
        ch = QuantumChannel(dist, noise, detector_efficiency=eta, dark_count_prob=p_dark)
        cs = ch.transmit(states)
        
        bob = Bob()
        ms = bob.measure(cs)
        
        p = BB84Protocol()
        sr = p.sift(ms)
        qr = p.estimate_qber(sr)
        ex = p.extract_key(qr)
        
        skrs.append(compute_skr(sr['sifted_count'], n_bits, qr['qber']))
        q_effs.append(qr['qber'])
        sifteds.append(sr['sifted_count'])
        aborteds.append(ex['session_aborted'])
        
    return {
        'skr': np.mean(skrs),
        'q_eff': np.mean(q_effs),
        'sifted': np.mean(sifteds),
        'aborted': any(aborteds),
    }

print("## SUB-STUDY IX-A (detector efficiency sweep)")
print("| $\eta$ | SKR | {dark}$ (%) | {eff}$ (%) | Sifted Count | Session Status |")
print("| :--- | :--- | :--- | :--- | :--- | :--- |")
for eta in [0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95, 0.98, 0.99]:
    dist = 50
    p_dark = 1e-5
    res = run_config(dist, eta, p_dark)
    q_dark_val = Q_dark(dist, eta, p_dark)
    status = "Aborted" if res['aborted'] else "Continued"
    flag = " (Low Confidence)" if res['sifted'] < 200 else ""
    print(f"| {eta:.2f} | {res['skr']:.2e} | {q_dark_val*100:.2f}% | {res['q_eff']*100:.2f}% | {res['sifted']:.1f} | {status}{flag} |")

print("\n## SUB-STUDY IX-B (dark count rate sweep)")
print("| Distance (km) | {dark}$ | SKR | {dark}$ (%) | {eff}$ (%) | Sifted Count | Session Status |")
print("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
eta = 0.85
for dist in [50, 100, 150]:
    for p_dark_exp in [-7, -6, -5.5, -5, -4.5, -4, -3.5, -3]:
        p_dark = 10**p_dark_exp
        res = run_config(dist, eta, p_dark)
        q_dark_val = Q_dark(dist, eta, p_dark)
        status = "Aborted" if res['aborted'] else "Continued"
        flag = " (Low Confidence: sparse counts)" if res['sifted'] < 200 else ""
        print(f"| {dist} | 10^{p_dark_exp} | {res['skr']:.2e} | {q_dark_val*100:.2f}% | {res['q_eff']*100:.2f}% | {res['sifted']:.1f} | {status}{flag} |")

print("\n## SUB-STUDY IX-C (technology comparison)")
print("| $\eta$ | {dark}$ | SKR | {dark}$ (%) | {eff}$ (%) | Sifted Count | Session Status |")
print("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
dist = 100
for eta, p_dark in [(0.20, 1e-5), (0.40, 3e-6), (0.90, 5e-8), (0.98, 1e-8)]:
    res = run_config(dist, eta, p_dark)
    q_dark_val = Q_dark(dist, eta, p_dark)
    status = "Aborted" if res['aborted'] else "Continued"
    flag = " (Low Confidence)" if res['sifted'] < 200 else ""
    print(f"| {eta:.2f} | {p_dark:.0e} | {res['skr']:.2e} | {q_dark_val*100:.2f}% | {res['q_eff']*100:.2f}% | {res['sifted']:.1f} | {status}{flag} |")
