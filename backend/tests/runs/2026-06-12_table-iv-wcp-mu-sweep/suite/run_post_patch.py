import sys, os, numpy as np
sys.path.append(os.path.abspath("."))
from core.alice import Alice
from core.channel import QuantumChannel
from core.eve import Eve
from core.bob import Bob
from core.protocol import BB84Protocol
from core.metrics import compute_skr
from core.wcp import poisson_photon_counts, apply_wcp_to_states, classify_pulses
from core.pns import PNSAttack
from core.constants import DETECTOR_EFFICIENCY, DARK_COUNT_PROB
from core.decoy import assign_decoy_intensities, compute_gains, detect_pns_attack
from core.detector import P_det, Q_dark

# ---- TABLE I RE-RUN (post-patch) ----
def t1():
    n=10000; a=Alice(); b=Alice(); bits=a.generate_bits(n); bases=a.choose_bases(n)
    states=a.encode_states(bits,bases)
    ch=QuantumChannel(0,0.0,detector_efficiency=1.0,dark_count_prob=0.0)
    cs=ch.transmit(states)
    e=Eve(attack_strategy='none',attack_prob=0.0); es=e.intercept(cs)
    bob=Bob(); ms=bob.measure(es)
    p=BB84Protocol(); sr=p.sift(ms); qr=p.estimate_qber(sr)
    return qr['qber']*100

def t2():
    n=10000; a=Alice(); bits=a.generate_bits(n); bases=a.choose_bases(n)
    states=a.encode_states(bits,bases)
    ch=QuantumChannel(0,0.0,detector_efficiency=1.0,dark_count_prob=0.0)
    cs=ch.transmit(states)
    e=Eve(attack_strategy='intercept_resend',attack_prob=1.0); es=e.intercept(cs)
    bob=Bob(); ms=bob.measure(es)
    p=BB84Protocol(); sr=p.sift(ms); qr=p.estimate_qber(sr)
    return qr['qber']*100

def t3():
    n=10000; rng=np.random.default_rng()
    pc=poisson_photon_counts(n,0.2,rng); s=classify_pulses(pc)
    return s['multi_fraction']*100

def t4():
    ch=QuantumChannel(distance_km=50,noise_level=0.0)
    return ch.p_survive*100

def t5():
    n=10000; a=Alice(); bits=a.generate_bits(n); bases=a.choose_bases(n)
    states=a.encode_states(bits,bases)
    ch=QuantumChannel(0,0.02,detector_efficiency=1.0,dark_count_prob=0.0)
    cs=ch.transmit(states)
    e=Eve(attack_strategy='none',attack_prob=0.0); es=e.intercept(cs)
    bob=Bob(); ms=bob.measure(es)
    p=BB84Protocol(); sr=p.sift(ms); qr=p.estimate_qber(sr)
    return compute_skr(sr['sifted_count'],n,qr['qber'])

def t6():
    n=10000; a=Alice(); bits=a.generate_bits(n); bases=a.choose_bases(n)
    states=a.encode_states(bits,bases)
    ch=QuantumChannel(50,0.02,detector_efficiency=1.0,dark_count_prob=0.0)
    cs=ch.transmit(states)
    e=Eve(attack_strategy='none',attack_prob=0.0); es=e.intercept(cs)
    bob=Bob(); ms=bob.measure(es)
    p=BB84Protocol(); sr=p.sift(ms); qr=p.estimate_qber(sr)
    return compute_skr(sr['sifted_count'],n,qr['qber'])

def t7():
    n=10000; rng=np.random.default_rng(); a=Alice()
    bits=a.generate_bits(n); bases=a.choose_bases(n); states=a.encode_states(bits,bases)
    di=assign_decoy_intensities(n,rng); pc=np.array([rng.poisson(mu) for mu in di])
    states=apply_wcp_to_states(states,pc)
    ch=QuantumChannel(50,0.0); cs=ch.transmit(states)
    from core.pns import PNSAttack; pns=PNSAttack(p_block=0.5,p_split=1.0)
    es,_=pns.attack(cs,rng)
    bob=Bob(); ms=bob.measure(es)
    gains=compute_gains(ms,di); dr=detect_pns_attack(gains)
    return dr['pns_detected']

def t8():
    n=10000; rng=np.random.default_rng(); a=Alice()
    bits=a.generate_bits(n); bases=a.choose_bases(n); states=a.encode_states(bits,bases)
    pc=poisson_photon_counts(n,0.2,rng); states=apply_wcp_to_states(states,pc)
    ch=QuantumChannel(50,0.0); cs=ch.transmit(states)
    pns=PNSAttack(p_block=0.5,p_split=1.0); es,_=pns.attack(cs,rng)
    bob=Bob(); ms=bob.measure(es)
    p=BB84Protocol(); sr=p.sift(ms); qr=p.estimate_qber(sr)
    return qr['qber']*100

def t9(): return P_det(d=0,eta=0.85,P_dark=1e-5)
def t10(): return Q_dark(d=100,eta=0.85,P_dark=1e-5)*100

tests=[t1,t2,t3,t4,t5,t6,t7,t8,t9,t10]
print("=== TABLE I POST-PATCH ===")
for i,fn in enumerate(tests):
    runs=[fn() for _ in range(3)]
    if isinstance(runs[0],(bool,np.bool_)):
        v=bool(all(runs))
    else:
        v=float(sum(runs)/3)
    print(f"T{i+1}: {v}")

# ---- TABLE IV RE-RUN (post-patch) ----
mu_values=[0.02,0.05,0.08,0.10,0.13,0.15,0.18,0.20,0.23,0.25,0.28,0.30,0.35,0.40,0.45,0.50,0.53,0.55]
n=10000; dist=30

def run_sim(mu,attack_prob):
    rng=np.random.default_rng(); a=Alice()
    bits=a.generate_bits(n); bases=a.choose_bases(n); states=a.encode_states(bits,bases)
    pc=poisson_photon_counts(n,mu,rng); states=apply_wcp_to_states(states,pc)
    ch=QuantumChannel(dist,0.0,detector_efficiency=DETECTOR_EFFICIENCY,dark_count_prob=DARK_COUNT_PROB)
    cs=ch.transmit(states)
    if attack_prob>0:
        pns=PNSAttack(p_block=attack_prob*0.5,p_split=attack_prob)
        es,_=pns.attack(cs,rng)
    else:
        es=cs
    bob=Bob(); ms=bob.measure(es)
    p=BB84Protocol(); sr=p.sift(ms); qr=p.estimate_qber(sr)
    skr=compute_skr(sr['sifted_count'],n,qr['qber'])
    return skr,qr['qber'],sr['sifted_count']

print("\n=== TABLE IV POST-PATCH ===")
print("| mu | SKR_no_Eve | SKR_PNS | QBER_PNS | Sifted | Retention | Flags |")
print("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
for mu in mu_values:
    s_no,s_pns,q_pns,sifted=[],[],[],[]
    for _ in range(3):
        sk_no,_,si=run_sim(mu,0.0); s_no.append(sk_no); sifted.append(si)
        sk_p,qp,_=run_sim(mu,1.0); s_pns.append(sk_p); q_pns.append(qp)
    mn=np.mean(s_no); mp=np.mean(s_pns); mq=np.mean(q_pns)*100; ms=np.mean(sifted)
    ret=mp/max(mn,1e-9)
    flag="None"
    if mq>1.0: flag="High QBER"
    elif mn>1e-9 and abs(mp-mn)/mn>0.05: flag="SKR Drop (>5%)"
    print(f"| {mu:.2f} | {mn:.4e} | {mp:.4e} | {mq:.3f}% | {ms:.0f} | {ret:.4f} | {flag} |")
