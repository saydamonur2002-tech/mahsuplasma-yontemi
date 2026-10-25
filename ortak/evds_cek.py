"""EVDS3 grup çekici (anahtarsız herkese açık uç nokta). Çeyreklik frequency=5.
Kullanım: python evds_cek.py <çıktı.csv> <grup1> <grup2> ...
Not: sayılar nokta ondalıkla yazılır; toplulaştırma her serinin DEFAULT_AGG_METHOD'u ile yapılır
(stok: last, akım: sum)."""
import csv
import json
import sys
import urllib.request

BASE = "https://evds3.tcmb.gov.tr/igmevdsms-dis"


def get_json(url, body=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST" if body is not None else "GET",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8-sig"))


def fetch_group(code, start="01-01-2000", end="07-10-2026", freq="5"):
    series = get_json(f"{BASE}/serieList/fe/type=json&code={code}")
    aggs = [s["DEFAULT_AGG_METHOD"] for s in series]
    body = {
        "type": "json",
        "series": "-".join(s["SERIE_CODE"] for s in series),
        "aggregationTypes": "-".join(aggs),
        "formulas": "-".join("0" for _ in series),
        "startDate": start,
        "endDate": end,
        "frequency": freq,
        "decimalSeperator": ".",
        "decimal": "4",
        "dateFormat": "0",
        "lang": "TR",
        "yon": "0",
        "sira": "0",
        "ozelFormuller": [],
        "groupSeperator": True,
        "isRaporSayfasi": False,
    }
    data = get_json(f"{BASE}/fe", body)
    rows = []
    for it in data["items"]:
        for s in series:
            v = it.get(s["SERIE_CODE"].replace(".", "_"))
            if v not in (None, ""):
                rows.append((code, str(it["Tarih"]), s["SERIE_CODE"], s["SERIE_NAME"], s["DEFAULT_AGG_METHOD"], float(str(v).replace(",", ""))))
    return rows, len(series)


if __name__ == "__main__":
    out, groups = sys.argv[1], sys.argv[2:]
    allrows = []
    for g in groups:
        try:
            rows, n = fetch_group(g)
            print(g, n, "seri,", len(rows), "gözlem")
            allrows += rows
        except Exception as exc:  # noqa: BLE001
            print(g, "HATA", exc)
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Grup", "Donem", "Seri", "Ad", "Agg", "Deger"])
        w.writerows(allrows)
