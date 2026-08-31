import sys, os, numpy as np
sys.path.append(os.path.abspath("."))
from core.alice import Alice
from core.channel import QuantumChannel
from core.bob import Bob
from core.wcp import apply_wcp_to_states
from core.pns import PNSAttack
from core.decoy import assign_decoy_intensities, compute_gains
from core.constants import DETECTOR_EFFICIENCY, DARK_COUNT_PROB, ATTENUATION_COEFF_DB_PER_KM
from core.detector import P_survive

n_bits = 200000  # bigger sample for stable Y_1

MU_SIGNAL = 0.5
MU_DECOY  = 0.1
ALPHA     = ATTENUATION_COEFF_DB_PER_KM
ETA       = DETECTOR_EFFICIENCY
P_DARK    = DARK_COUNT_PROB

def estimate_y1_lmc(Q_s, Q_d, Q_vac, mu_s, mu_d):
    """
    Lo, Ma & Chen (2005) Y_1 lower bound.
    Q_s, Q_d, Q_vac: raw gains (fraction of pulses detected) at signal/decoy/vacuum intensity.
    mu_s, mu_d: mean photon numbers for signal/decoy states.
    """
    Y_0 = Q_vac  # vacuum yield = dark count rate per slot

    numerator = (
        Q_d * np.exp(mu_d)
        - Q_s * np.exp(mu_s) * (mu_d**2 / mu_s**2)
        - (mu_s**2 - mu_d**2) / mu_s**2 * Y_0
    )
    denominator = mu_d - (mu_d**2 / mu_s)

    Y_1_L = (mu_s / mu_s) * numerator / denominator  # simplifies: outer mu_s cancels
    # The correct LMC formula:  Y_1_L = mu_s/(mu_s*mu_d - mu_d^2) * [...]
    denom_full = mu_s * mu_d - mu_d**2
    Y_1_L = mu_s / denom_full * (
        Q_d * np.exp(mu_d)
        - Q_s * np.exp(mu_s) * (mu_d**2 / mu_s**2)
        - (mu_s**2 - mu_d**2) / mu_s**2 * Y_0
    )
    return Y_1_L, Y_0

def expected_y1(dist):
    """Single-photon expected yield for an honest channel."""
    p_s = P_survive(dist)
    return p_s * ETA + P_DARK

def run_scenario(name, dist, attack_prob, mu=0.2):
    rng = np.random.default_rng(42)
    a = Alice()
    bits  = a.generate_bits(n_bits)
    bases = a.choose_bases(n_bits)
    states = a.encode_states(bits, bases)

    intensities = assign_decoy_intensities(n_bits, rng)
    pc = rng.poisson(intensities)
    states = apply_wcp_to_states(states, pc)

    ch = QuantumChannel(dist, 0.02, detector_efficiency=ETA, dark_count_prob=P_DARK)
    cs = ch.transmit(states)

    if attack_prob > 0:
        pns = PNSAttack(p_block=attack_prob * 0.5, p_split=attack_prob)
        es, _ = pns.attack(cs, rng)
    else:
        es = cs

    bob = Bob()
    ms = bob.measure(es)

    gains = compute_gains(ms, intensities)
    Q_s   = gains['signal_gain']
    Q_d   = gains['decoy_gain']
    Q_vac = gains['vacuum_gain']

    Y_1_L, Y_0 = estimate_y1_lmc(Q_s, Q_d, Q_vac, MU_SIGNAL, MU_DECOY)
    Y_1_exp    = expected_y1(dist)

    thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
    results = {t: (Y_1_L < t * Y_1_exp) for t in thresholds}

    print(f"--- {name} ---")
    print(f"  Q_signal: {Q_s:.6f} | Q_decoy: {Q_d:.6f} | Q_vacuum: {Q_vac:.8f}")
    print(f"  Y_0 (vacuum yield):    {Y_0:.8f}")
    print(f"  Y_1_L  (LMC lower):    {Y_1_L:.6f}")
    print(f"  Y_1_expected (honest): {Y_1_exp:.6f}")
    print(f"  Y_1_L / Y_1_exp:       {Y_1_L / Y_1_exp:.4f}")
    print(f"  Threshold sensitivity: ", end="")
    for t, det in results.items():
        print(f"  t={t}: {'DETECTED' if det else 'clean'}", end=" |")
    print()
    print()

run_scenario("Clean baseline d=0km",  dist=0,  attack_prob=0.0)
run_scenario("PNS attack d=0km",      dist=0,  attack_prob=1.0)
run_scenario("Clean baseline d=50km", dist=50, attack_prob=0.0)
run_scenario("PNS attack d=50km",     dist=50, attack_prob=1.0)
