import math

def P_survive(d: float, alpha: float = 0.2) -> float:
    loss_dB = alpha * d
    return 10 ** (-loss_dB / 10)

def P_det(d: float, eta: float, P_dark: float) -> float:
    p_s = P_survive(d)
    return p_s * eta + P_dark * (1 - p_s * eta)

def Q_dark(d: float, eta: float, P_dark: float) -> float:
    p_s = P_survive(d)
    p_d = P_det(d, eta, P_dark)
    if p_d == 0:
        return 0.5
    return P_dark * (1 - p_s * eta) / (2 * p_d)
