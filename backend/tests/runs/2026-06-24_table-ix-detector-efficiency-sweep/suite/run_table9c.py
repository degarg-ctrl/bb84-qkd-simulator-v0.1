import sys, os, time, numpy as np
sys.path.append(os.path.abspath("."))
from core.alice import Alice
from core.channel import QuantumChannel
from core.bob import Bob
from core.protocol import BB84Protocol
from core.wcp import poisson_photon_counts, apply_wcp_to_states
from core.metrics import compute_skr
from core.detector import Q_dark

n_bits = 600000
reps = 5
noise = 0.02
mu = 0.2
dist = 50

def run_config(eta, p_dark):
    skrs, q_effs, sifteds, aborteds = [], [], [], []
    for rep in range(reps):
        rng = np.random.default_rng(rep * 137 + hash(f"{dist}_{eta}_{p_dark}") % 10000)
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

print("## REVISED SUB-STUDY IX-C (technology comparison at d=50km, n=600,000)")
print("| $\eta$ | {dark}$ | SKR | {dark}$ (%) | {eff}$ (%) | Sifted Count | Session Status |")
print("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

for eta, p_dark in [(0.20, 1e-5), (0.40, 3e-6), (0.90, 5e-8), (0.98, 1e-8)]:
    res = run_config(eta, p_dark)
    q_dark_val = Q_dark(dist, eta, p_dark)
    status = "Aborted" if res['aborted'] else "Continued"
    flag = " (Low Confidence: <1000 counts)" if res['sifted'] < 1000 else ""
    print(f"| {eta:.2f} | {p_dark:.0e} | {res['skr']:.2e} | {q_dark_val*100:.2f}% | {res['q_eff']*100:.2f}% | {res['sifted']:.1f} | {status}{flag} |")
