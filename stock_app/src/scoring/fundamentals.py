def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def score_from_threshold(value, good, bad, higher_is_better=True):
    """
    value가 good에 가까울수록 100, bad에 가까울수록 0.
    """
    if value is None:
        return None
    if higher_is_better:
        if value >= good: return 100.0
        if value <= bad: return 0.0
        return 100.0 * (value - bad) / (good - bad)
    else:
        if value <= good: return 100.0
        if value >= bad: return 0.0
        return 100.0 * (bad - value) / (bad - good)

def fundamentals_score_kr(metrics):
    # 아주 단순한 MVP 스코어(추후 조정 가능)
    # 가중치 합 1.0
    w_rev = 0.20
    w_opm = 0.25
    w_debt = 0.30
    w_net = 0.25

    revenue = metrics.get("revenue")
    op_profit = metrics.get("op_profit")
    net_income = metrics.get("net_income")
    debt_ratio = metrics.get("debt_ratio_pct")

    op_margin = None
    if revenue and op_profit is not None and revenue != 0:
        op_margin = (op_profit / revenue) * 100.0

    s_rev = score_from_threshold(revenue, good=1e13, bad=0, higher_is_better=True)        # 규모 proxy
    s_opm = score_from_threshold(op_margin, good=15, bad=0, higher_is_better=True)        # 영업이익률
    s_debt = score_from_threshold(debt_ratio, good=50, bad=200, higher_is_better=False)   # 부채비율
    s_net = score_from_threshold(net_income, good=1e12, bad=0, higher_is_better=True)

    parts = {"revenue": s_rev, "op_margin_pct": s_opm, "debt_ratio_pct": s_debt, "net_income": s_net}
    # None은 제외하고 다시 정규화
    valid = [(k,v) for k,v in parts.items() if v is not None]
    if not valid:
        return 0.0, parts, {"op_margin_pct": op_margin}

    # 가중치도 None인 항목 제외 정규화
    weights = {"revenue": w_rev, "op_margin_pct": w_opm, "debt_ratio_pct": w_debt, "net_income": w_net}
    wsum = sum(weights[k] for k,_ in valid)
    total = sum((weights[k]/wsum) * v for k,v in valid)

    return clamp(total, 0, 100), parts, {"op_margin_pct": op_margin}