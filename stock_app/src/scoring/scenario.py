import numpy as np
import pandas as pd

def compute_momentum(close, lookback=63):
    if len(close) < lookback + 2:
        return 0.0
    return float(close[-1] / close[-lookback] - 1.0)

def compute_vol(close, lookback=63):
    if len(close) < lookback + 2:
        return 0.25
    r = np.diff(np.log(close[-lookback:]))
    return float(np.std(r) * np.sqrt(252))

def scenario_forecast(close_series, fundamental_score_0_100, pos_score_0_1, neg_score_0_1, days=252, seed=7):
    """
    매우 단순한 '시나리오 밴드' MVP:
    - 드리프트(mu): 모멘텀 + 재무점수 + 뉴스감성
    - 변동성(sig): 최근 변동성 기반 (하한/상한)
    - 5개 시나리오에 서로 다른 mu 배치
    """
    rng = np.random.default_rng(seed)
    close = np.asarray(close_series, dtype=float)
    s0 = float(close[-1])

    mom = compute_momentum(close)
    vol = compute_vol(close)
    vol = float(np.clip(vol, 0.10, 0.80))

    # 뉴스 심리: pos - neg
    sent = float(np.clip(pos_score_0_1 - neg_score_0_1, -1.0, 1.0))
    fund = (float(fundamental_score_0_100) - 50.0) / 50.0  # -1..+1

    base_mu = 0.06 + 0.40*mom + 0.10*fund + 0.08*sent  # 연 기대수익(거칠게)
    base_mu = float(np.clip(base_mu, -0.40, 0.60))

    scenarios = [
        ("Bull",       base_mu + 0.18, 0.22),
        ("Mild Bull",  base_mu + 0.08, 0.24),
        ("Base",       base_mu + 0.00, 0.28),
        ("Mild Bear",  base_mu - 0.10, 0.16),
        ("Bear",       base_mu - 0.22, 0.10),
    ]

    # 확률(가중): fund/sent가 좋으면 상방 시나리오 확률 증가
    tilt = 0.6*fund + 0.8*sent
    raw_p = np.array([0.18+0.10*tilt, 0.22+0.06*tilt, 0.26, 0.20-0.06*tilt, 0.14-0.10*tilt])
    raw_p = np.clip(raw_p, 0.03, None)
    p = raw_p / raw_p.sum()

    # 각 시나리오의 중앙경로 + 밴드(간단히 lognormal 근사)
    out = []
    t = np.arange(days+1)
    for (name, mu, prob), sig_mult in zip(zip([s[0] for s in scenarios],
                                              [s[1] for s in scenarios],
                                              p),
                                          [0.9, 1.0, 1.1, 1.0, 0.95]):
        mu = float(mu)
        sig = float(np.clip(vol * sig_mult, 0.10, 0.90))
        # 기대 경로: S(t)=S0*exp((mu-0.5*sig^2)*t/252)
        med = s0 * np.exp((mu - 0.5*sig*sig) * (t/252.0))
        # 밴드: +/- 1.0 sigma
        up = s0 * np.exp((mu - 0.5*sig*sig) * (t/252.0) + sig*np.sqrt(t/252.0))
        dn = s0 * np.exp((mu - 0.5*sig*sig) * (t/252.0) - sig*np.sqrt(t/252.0))

        out.append({
            "scenario": name,
            "prob": float(prob),
            "mu": mu,
            "sigma": sig,
            "t": t,
            "median": med,
            "upper": up,
            "lower": dn,
        })

    # 추세: 가장 높은 확률 시나리오의 마지막 중앙값이 s0보다 크면 상승
    top = max(out, key=lambda x: x["prob"])
    trend = "상승" if top["median"][-1] >= s0 else "하락"

    return trend, out