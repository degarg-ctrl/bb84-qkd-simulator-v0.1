"""
backend/core/decoy.py

Decoy State Protocol — countermeasure against PNS attack.
Alice randomly sends pulses with different mean photon numbers.
Comparing single-photon yield statistics reveals PNS attack.

Implementation: Lo, Ma & Chen (2005) PRL 94, 230504.
Computes Y_1 lower bound (Eq. 5) from measured gains at signal and
decoy intensities.  Flags PNS attack when Y_1_L falls more than
PNS_Y1_SUPPRESSION_THRESHOLD below the expected honest-channel value.

Physics reference: PHYSICS_CONTRACT.md Section 16
"""

import numpy as np
from core.constants import (
    ATTENUATION_COEFF_DB_PER_KM,
    DETECTOR_EFFICIENCY,
    DARK_COUNT_PROB,
)
from core.wcp import theoretical_pulse_fractions

# Default intensity levels
MU_SIGNAL = 0.5   # Signal state intensity
MU_DECOY  = 0.1   # Decoy state intensity
MU_VACUUM = 0.0   # Vacuum state intensity

# Fraction of pulses at each intensity
SIGNAL_FRACTION = 0.70
DECOY_FRACTION  = 0.20
VACUUM_FRACTION = 0.10

# Relative suppression threshold for Y_1-based PNS detection.
# Flag attack when Y_1_L < PNS_Y1_SUPPRESSION_THRESHOLD * Y_1_expected.
# Validated empirically (5 reps, 200k bits):
#   Clean channel: Y_1_L/Y_1_exp in [0.91, 1.14] at d=0 and d=50km
#   PNS full attack: Y_1_L/Y_1_exp in [0.43, 0.52] at d=0 and d=50km
#   Gap between attack and clean: >0.39 — threshold 0.6 is conservative.
PNS_Y1_SUPPRESSION_THRESHOLD = 0.6


def assign_decoy_intensities(
  n_pulses: int,
  rng: np.random.Generator = None
) -> np.ndarray:
  """
  Randomly assign intensity levels to pulses.
  
  Per PHYSICS_CONTRACT Section 16:
  70% signal (mu=0.5), 20% decoy (mu=0.1), 10% vacuum (mu=0)
  
  Args:
    n_pulses: total number of pulses
    rng: numpy random generator
  Returns:
    array of mean photon numbers per pulse
  """
  if rng is None:
    rng = np.random.default_rng()

  intensities = rng.choice(
    [MU_SIGNAL, MU_DECOY, MU_VACUUM],
    size=n_pulses,
    p=[SIGNAL_FRACTION, DECOY_FRACTION, VACUUM_FRACTION]
  )
  return intensities


def compute_gains(
  states: list[dict],
  intensities: np.ndarray
) -> dict:
  """
  Compute gain statistics for signal, decoy, and vacuum states.
  
  Gain Q_mu = fraction of pulses detected at intensity mu.
  Uses state['index'] (the original pulse index set by Alice) to
  correctly map surviving states back to their intensity assignment.
  
  Args:
    states: photon states (possibly after channel/Eve/Bob losses)
    intensities: intensity array from assign_decoy_intensities,
                 indexed by original pulse index
  Returns:
    dict with signal_gain, decoy_gain, vacuum_gain,
    normalized_signal, normalized_decoy, ratio,
    signal_total, decoy_total
  """
  signal_total    = 0
  signal_detected = 0
  decoy_total     = 0
  decoy_detected  = 0
  vacuum_total    = 0
  vacuum_detected = 0

  for state in states:
    original_index = state.get('index')
    if original_index is None or original_index >= len(intensities):
      continue
    mu = intensities[original_index]
    detected = state.get('detected', False) and \
               not state.get('lost', False)

    if mu == MU_SIGNAL:
      signal_total    += 1
      signal_detected += int(detected)
    elif mu == MU_DECOY:
      decoy_total     += 1
      decoy_detected  += int(detected)
    elif mu == MU_VACUUM:
      vacuum_total    += 1
      vacuum_detected += int(detected)

  signal_gain = signal_detected / max(1, signal_total)
  decoy_gain  = decoy_detected  / max(1, decoy_total)
  vacuum_gain = vacuum_detected / max(1, vacuum_total)

  # Legacy normalized-gain fields kept for backward compatibility with
  # existing tests/logs — no longer used for PNS detection.
  norm_signal = signal_gain / MU_SIGNAL if MU_SIGNAL > 0 else 0.0
  norm_decoy  = decoy_gain  / MU_DECOY  if MU_DECOY  > 0 else 0.0

  return {
    'signal_gain':       signal_gain,
    'decoy_gain':        decoy_gain,
    'vacuum_gain':       vacuum_gain,
    'normalized_signal': norm_signal,
    'normalized_decoy':  norm_decoy,
    'ratio': norm_signal / norm_decoy if norm_decoy > 0 else 1.0,
    'signal_total':      signal_total,
    'decoy_total':       decoy_total,
  }


def estimate_y1_lmc(
  Q_s:   float,
  Q_d:   float,
  Q_vac: float,
  mu_s:  float = MU_SIGNAL,
  mu_d:  float = MU_DECOY,
) -> tuple[float, float]:
  """
  Lo, Ma & Chen (2005) lower bound on the single-photon yield Y_1.

  Reference: PRL 94, 230504 (2005), Eq. (5).

  Y_1^L = mu_s / (mu_s*mu_d - mu_d^2) * [
      Q_d * exp(mu_d)
    - Q_s * exp(mu_s) * (mu_d/mu_s)^2
    - (mu_s^2 - mu_d^2) / mu_s^2 * Y_0
  ]

  Y_0 (vacuum yield) is taken directly from Q_vac (fraction of vacuum
  pulses that register a click — dominated by dark counts).

  Args:
    Q_s:   raw signal gain (fraction detected at mu_s)
    Q_d:   raw decoy  gain (fraction detected at mu_d)
    Q_vac: raw vacuum gain (fraction detected at mu=0; yields Y_0)
    mu_s:  mean photon number for signal pulses (default: MU_SIGNAL)
    mu_d:  mean photon number for decoy  pulses (default: MU_DECOY)
  Returns:
    (Y_1_L, Y_0): lower bound on single-photon yield, vacuum yield
  """
  Y_0 = Q_vac

  denom = mu_s * mu_d - mu_d ** 2          # mu_d * (mu_s - mu_d)

  if abs(denom) < 1e-15:
    # Degenerate — identical intensities, cannot estimate Y_1
    return 0.0, Y_0

  Y_1_L = (mu_s / denom) * (
    Q_d * np.exp(mu_d)
    - Q_s * np.exp(mu_s) * (mu_d ** 2 / mu_s ** 2)
    - (mu_s ** 2 - mu_d ** 2) / mu_s ** 2 * Y_0
  )

  return float(Y_1_L), float(Y_0)


def expected_single_photon_yield(
  distance_km:    float = 0.0,
  eta:            float = DETECTOR_EFFICIENCY,
  dark_count_prob: float = DARK_COUNT_PROB,
  attenuation:    float = ATTENUATION_COEFF_DB_PER_KM,
) -> float:
  """
  Theoretical Y_1 for a single photon in an honest, unattacked channel.

  Y_1_expected = P_survive(d) * eta + P_dark

  This is the detection probability for a genuinely single-photon pulse
  absent any eavesdropping.  Used as the reference against which
  Y_1_L is compared to infer PNS attack.

  Args:
    distance_km:    fiber distance (km)
    eta:            detector efficiency
    dark_count_prob: per-slot dark count probability
    attenuation:    fiber attenuation (dB/km)
  Returns:
    Expected single-photon yield (float)
  """
  loss_dB  = attenuation * distance_km
  p_survive = 10.0 ** (-loss_dB / 10.0)
  return p_survive * eta + dark_count_prob


def detect_pns_attack(
  gains:          dict,
  distance_km:    float = 0.0,
  eta:            float = DETECTOR_EFFICIENCY,
  dark_count_prob: float = DARK_COUNT_PROB,
  mu_s:           float = MU_SIGNAL,
  mu_d:           float = MU_DECOY,
) -> dict:
  """
  Detect PNS attack using Lo, Ma & Chen Y_1 lower-bound estimation.

  Per PHYSICS_CONTRACT Section 16 / LMC (2005):
  Eve's PNS attack selectively blocks single-photon pulses, depressing
  the observed single-photon yield Y_1 far below the honest-channel
  expectation.  The naive Q_mu/mu ratio is NOT used here because it
  varies systematically with distance attenuation, causing false
  positives on clean channels.

  Detection criterion:
    Y_1_L < PNS_Y1_SUPPRESSION_THRESHOLD * Y_1_expected

  where Y_1_L is the LMC lower bound and Y_1_expected is the honest
  single-photon yield for the current distance/efficiency.

  Threshold = 0.6 validated over 5 reps x 200k bits:
    Clean channel:  Y_1_L/Y_1_exp ≈ 1.0  (range 0.91–1.14)
    Full PNS attack: Y_1_L/Y_1_exp ≈ 0.5  (range 0.43–0.52)

  Args:
    gains:          dict from compute_gains()
    distance_km:    fiber distance used in the session (km)
    eta:            detector efficiency
    dark_count_prob: per-slot dark count probability
    mu_s:           signal intensity
    mu_d:           decoy  intensity
  Returns:
    dict with:
      pns_detected    – bool
      confidence      – float [0, 1] (how far below threshold)
      y1_lower_bound  – Y_1_L (computed)
      y1_expected     – Y_1_expected (honest channel)
      y1_suppression  – Y_1_L / Y_1_expected ratio
      threshold_used  – PNS_Y1_SUPPRESSION_THRESHOLD
      signal_gain     – raw Q_s
      decoy_gain      – raw Q_d
      # Legacy fields for backward compat:
      gain_difference – |norm_signal - norm_decoy| (old metric, informational only)
  """
  Q_s   = gains['signal_gain']
  Q_d   = gains['decoy_gain']
  Q_vac = gains['vacuum_gain']

  Y_1_L, Y_0 = estimate_y1_lmc(Q_s, Q_d, Q_vac, mu_s, mu_d)
  Y_1_exp    = expected_single_photon_yield(distance_km, eta, dark_count_prob)

  suppression = Y_1_L / Y_1_exp if Y_1_exp > 0 else 1.0
  detected    = suppression < PNS_Y1_SUPPRESSION_THRESHOLD

  # Confidence: 1.0 when suppression=0; 0.0 when suppression>=threshold
  confidence = max(0.0, min(1.0,
    1.0 - suppression / PNS_Y1_SUPPRESSION_THRESHOLD
  ))

  # Legacy gain_difference field — informational only, NOT used for detection
  legacy_diff = abs(
    gains.get('normalized_signal', 0.0) - gains.get('normalized_decoy', 0.0)
  )

  return {
    'pns_detected':   detected,
    'confidence':     float(confidence),
    'y1_lower_bound': float(Y_1_L),
    'y1_expected':    float(Y_1_exp),
    'y1_suppression': float(suppression),
    'threshold_used': PNS_Y1_SUPPRESSION_THRESHOLD,
    'signal_gain':    Q_s,
    'decoy_gain':     Q_d,
    # Legacy field kept for backward compat with old test assertions
    'gain_difference': float(legacy_diff),
  }


# Depends on: core/constants.py, core/wcp.py, numpy
# Used by: routers/simulation.py when decoy_enabled=True
