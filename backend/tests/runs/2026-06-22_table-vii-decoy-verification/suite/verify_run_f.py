import sys, os, numpy as np
sys.path.append(os.path.abspath("."))
from core.alice import Alice
from core.channel import QuantumChannel
from core.bob import Bob
from core.protocol import BB84Protocol
from core.wcp import apply_wcp_to_states
from core.pns import PNSAttack
from core.decoy import assign_decoy_intensities, compute_gains, detect_pns_attack
from core.metrics import compute_skr
from core.constants import DETECTOR_EFFICIENCY, DARK_COUNT_PROB

n_bits = 100000
dist   = 50
noise  = 0.02
reps   = 5
ETA    = DETECTOR_EFFICIENCY
P_DARK = DARK_COUNT_PROB

skr_list, qber_list, sifted_list, alert_list, status_list = [], [], [], [], []

for rep in range(reps):
    rng = np.random.default_rng(rep * 37)
    a = Alice()
    bits  = a.generate_bits(n_bits)
    bases = a.choose_bases(n_bits)
    states = a.encode_states(bits, bases)
    intensities = assign_decoy_intensities(n_bits, rng)
    pc = rng.poisson(intensities)
    states = apply_wcp_to_states(states, pc)
    ch = QuantumChannel(dist, noise, detector_efficiency=ETA, dark_count_prob=P_DARK)
    cs = ch.transmit(states)
    pns = PNSAttack(p_block=0.5, p_split=1.0)
    es, _ = pns.attack(cs, rng)
    bob = Bob()
    ms = bob.measure(es)
    gains = compute_gains(ms, intensities)
    pns_res = detect_pns_attack(gains, distance_km=dist, eta=ETA, dark_count_prob=P_DARK)
    decoy_alert = pns_res['pns_detected']
    p = BB84Protocol()
    sr = p.sift(ms)
    qr = p.estimate_qber(sr)
    ex = p.extract_key(qr)
    status = "Aborted" if ex['session_aborted'] or decoy_alert else "Continued"
    skr = compute_skr(sr['sifted_count'], n_bits, qr['qber'])
    skr_list.append(skr); qber_list.append(qr['qber'])
    sifted_list.append(sr['sifted_count'])
    alert_list.append(decoy_alert); status_list.append(status)
    print(f"  rep {rep}: Y_1_L={pns_res['y1_lower_bound']:.5f}  Y_1_exp={pns_res['y1_expected']:.5f}  ratio={pns_res['y1_suppression']:.4f}  alert={decoy_alert}  status={status}")

print()
print(f"Run F (WCP, mu=0.2, PNS, Decoy, d=50km) — mean over {reps} reps:")
print(f"  QBER      = {np.mean(qber_list)*100:.2f}%")
print(f"  SKR       = {np.mean(skr_list):.2e}")
print(f"  Sifted    = {np.mean(sifted_list):.1f}")
print(f"  Decoy Alert triggered ALL reps: {all(alert_list)}")
print(f"  Status    = {status_list}")
