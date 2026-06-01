import os, re, io, zipfile, requests
import xml.etree.ElementTree as ET

DART_BASE = "https://opendart.fss.or.kr/api"

def get_dart_key():
    return os.environ.get("DART_API_KEY")

def api_get(path, params):
    url = f"{DART_BASE}/{path}"
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r

def api_get_json(path, params):
    return api_get(path, params).json()

def download_corpcode_zip(api_key):
    return api_get("corpCode.xml", {"crtfc_key": api_key}).content

def load_corpcode_table(api_key):
    zbytes = download_corpcode_zip(api_key)
    with zipfile.ZipFile(io.BytesIO(zbytes)) as zf:
        xml_name = [n for n in zf.namelist() if n.lower().endswith(".xml")][0]
        xml_data = zf.read(xml_name)
    root = ET.fromstring(xml_data)
    rows = []
    for item in root.findall("list"):
        rows.append({
            "corp_code": (item.findtext("corp_code") or "").strip(),
            "corp_name": (item.findtext("corp_name") or "").strip(),
            "stock_code": (item.findtext("stock_code") or "").strip(),
        })
    return [r for r in rows if r["corp_code"] and r["corp_name"]]

def search_corp(rows, keyword, limit=20):
    k = (keyword or "").strip().lower()
    if not k:
        return []
    hits = [r for r in rows if k in (r["corp_name"] or "").lower()]
    hits.sort(key=lambda r: (0 if r["stock_code"] else 1, len(r["corp_name"])))
    return hits[:limit]

def get_financials_single_company(api_key, corp_code, bsns_year, reprt_code="11011", fs_div="CFS"):
    return api_get_json("fnlttSinglAcntAll.json", {
        "crtfc_key": api_key,
        "corp_code": corp_code,
        "bsns_year": str(bsns_year),
        "reprt_code": reprt_code,
        "fs_div": fs_div,
    })

def _to_number(x):
    if x is None:
        return None
    s = str(x).strip().replace(",", "")
    if s in ("", "-", "null", "None"):
        return None
    try:
        return float(s)
    except:
        return None

def _norm(s):
    s = (s or "").strip()
    s = re.sub(r"\s+", "", s)
    return s.replace("(", "").replace(")", "")

def pick_account(rows, keywords):
    nk = [_norm(k) for k in keywords]
    for r in rows:
        an = _norm(r.get("account_nm"))
        for k in nk:
            if k and k in an:
                return _to_number(r.get("thstrm_amount"))
    return None

def extract_basic_metrics(fin_json):
    if (fin_json or {}).get("status") != "000":
        return None, fin_json.get("message", "DART error")
    rows = fin_json.get("list") or []
    if not rows:
        return None, "DART list empty"

    revenue = pick_account(rows, ["매출액", "영업수익", "수익"])
    op_profit = pick_account(rows, ["영업이익"])
    net_income = pick_account(rows, ["당기순이익", "당기순손익", "당기순이익손실"])
    total_liab = pick_account(rows, ["부채총계", "총부채"])
    total_equity = pick_account(rows, ["자본총계", "총자본"])

    debt_ratio = None
    if total_liab is not None and total_equity is not None and total_equity > 0:
        debt_ratio = (total_liab / total_equity) * 100.0

    return {
        "revenue": revenue,
        "op_profit": op_profit,
        "net_income": net_income,
        "total_liab": total_liab,
        "total_equity": total_equity,
        "debt_ratio_pct": debt_ratio,
    }, None