# ================================================
# 名前をRPG3寄りのローマ字へ短縮した版
# ・自作関数/変数: nittei_saikeisan, toroku_yomu など
# ・外部API/JSON/Streamlitが決めた項目名: 互換性のため維持
# ・通常変数はPython慣例に合わせて小文字を使用
# ================================================


from __future__ import annotations

import copy
import html
import io
import json
import math
import os
import random
import re
import socket
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus
from urllib import parse as urlparse
from urllib import request as urlrequest

import folium
import requests
import streamlit as st
import qrcode
from folium.plugins import AntPath, MarkerCluster
from streamlit_folium import st_folium

st.set_page_config(page_title="旅ゲームメーカー 全国版", page_icon="🗾", layout="wide")

# Streamlitの状態データ。長い st.session_state を短くする。
ss = st.session_state


def css_yomu() -> None:
    """同じフォルダにある style.css を読み込む。"""
    css_file = Path(__file__).with_name("style.css")

    if not css_file.exists():
        st.error(f"CSSファイルが見つかりません: {css_file}")
        return

    css = css_file.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


css_yomu()





API_KENSAKU = "https://nominatim.openstreetmap.org/search"
API_SHUHEN = "https://overpass-api.de/api/interpreter"
API_KEIRO = {
    "車": [
        "https://router.project-osrm.org",
        "https://routing.openstreetmap.de/routed-car",
    ],
    "徒歩": [
        "https://routing.openstreetmap.de/routed-foot",
    ],
    "自転車": [
        "https://routing.openstreetmap.de/routed-bike",
    ],
}
API_VALHALLA = "https://valhalla1.openstreetmap.de/route"
UA = "tabigame-japan-realmap-integrated/2.0"
FILE_BACKUP = Path(__file__).with_name("trip_backup_latest.json")
FILE_KYOYU = Path(__file__).with_name("shared_trip_state.json")
FILE_TOROKU = Path(__file__).with_name("registered_places.json")

KUBUN_JOKEN = {
    "カフェ": ['["amenity"="cafe"]'],
    "ランチ・レストラン": ['["amenity"="restaurant"]'],
    "観光スポット": ['["tourism"="attraction"]', '["tourism"="museum"]', '["historic"]'],
    "ビーチ": ['["natural"="beach"]'],
    "ホテル": ['["tourism"="hotel"]'],
    "コンビニ": ['["shop"="convenience"]'],
    "スーパー": ['["shop"="supermarket"]'],
    "温泉・スパ": ['["amenity"="public_bath"]', '["leisure"="spa"]'],
}
KUBUN_ICON = {
    "カフェ": "☕", "ランチ・レストラン": "🍽️", "観光スポット": "📍",
    "ビーチ": "🏖️", "ホテル": "🏨", "コンビニ": "🏪",
    "スーパー": "🛒", "温泉・スパ": "♨️", "固定予定": "🧷", "レンタカー": "🚗",
}
IDO_PROFILE = {"車": "driving", "徒歩": "foot", "自転車": "bike"}
IDO_ICON = {"車": "🚗", "徒歩": "🚶", "自転車": "🚲"}


KUBUN_SHOKI = {
    "カフェ": {"cost": 1500, "open": "08:00", "close": "20:00", "indoor": True, "priority": 3},
    "ランチ・レストラン": {"cost": 3000, "open": "11:00", "close": "21:00", "indoor": True, "priority": 3},
    "観光スポット": {"cost": 2000, "open": "09:00", "close": "18:00", "indoor": False, "priority": 3},
    "ビーチ": {"cost": 1000, "open": "08:00", "close": "19:00", "indoor": False, "priority": 3},
    "ホテル": {"cost": 0, "open": "00:00", "close": "23:59", "indoor": True, "priority": 5},
    "コンビニ": {"cost": 1000, "open": "00:00", "close": "23:59", "indoor": True, "priority": 1},
    "スーパー": {"cost": 3000, "open": "09:00", "close": "22:00", "indoor": True, "priority": 2},
    "温泉・スパ": {"cost": 2500, "open": "10:00", "close": "22:00", "indoor": True, "priority": 3},
    "固定予定": {"cost": 0, "open": "00:00", "close": "23:59", "indoor": True, "priority": 5},
    "レンタカー": {"cost": 0, "open": "00:00", "close": "23:59", "indoor": True, "priority": 5},
}

CHIIKI_CHUSHIN = {
    "日本全体": (36.2, 138.2, 5),
    "北海道": (43.3, 142.8, 6),
    "東北": (39.0, 140.7, 6),
    "関東": (35.7, 139.6, 8),
    "中部": (36.0, 137.5, 7),
    "関西": (34.8, 135.4, 8),
    "中国": (34.5, 132.5, 7),
    "四国": (33.7, 133.5, 8),
    "九州": (32.7, 130.7, 7),
    "沖縄": (26.4, 127.8, 8),
}

CHIIKI_HANI = {
    "北海道": ((41.2, 139.0), (45.8, 146.2)),
    "東北": ((36.8, 138.0), (41.6, 142.2)),
    "関東": ((34.7, 138.0), (37.1, 141.2)),
    "中部": ((34.2, 136.0), (37.8, 139.2)),
    "関西": ((33.4, 134.0), (35.9, 136.9)),
    "中国": ((33.5, 130.7), (35.7, 134.8)),
    "四国": ((32.7, 132.0), (34.6, 134.8)),
    "九州": ((30.8, 129.0), (34.1, 132.3)),
    "沖縄": ((24.0, 122.5), (28.8, 131.5)),
}

def chiiki_hantei(lat: float, lon: float) -> str:
    for name, ((lat0, lon0), (lat1, lon1)) in CHIIKI_HANI.items():
        if lat0 <= lat <= lat1 and lon0 <= lon <= lon1:
            return name
    if lat < 30:
        return "沖縄"
    if lat > 40:
        return "北海道"
    if lon < 133:
        return "九州"
    return "関東"

def syoki_data() -> None:
    shoki = {
        "page": "旅程",
        "trip_start": date(2026, 7, 17),
        "trip_days": 4,
        "spots": [],
        "search_results": [],
        "nearby_results": [],
        "day_modes": {},
        "map_region": "沖縄",
        "video_style": "思い出風",
        "day_start_times": {},
        "url_import_results": [],
        "registered_places": [],
    }
    for key, value in shoki.items():
        if key not in ss:
            ss[key] = value

    if not ss.spots:
        ss.spots = [
            {
                "_uid": uuid.uuid4().hex,
                "name": "ABCレンタカー那覇空港営業所",
                "address": "沖縄県那覇市周辺",
                "lat": 26.1905,
                "lon": 127.6555,
                "day": "2026-07-17",
                "start": "10:00",
                "stay": 0,
                "fixed": True,
                "memo": "レンタカー受取",
                "category": "レンタカー",
            },
            {
                "_uid": uuid.uuid4().hex,
                "name": "沖縄美ら海水族館",
                "address": "沖縄県国頭郡本部町石川424",
                "lat": 26.6944,
                "lon": 127.8779,
                "day": "2026-07-18",
                "start": "10:00",
                "stay": 180,
                "fixed": False,
                "memo": "必ず行きたい",
                "category": "観光スポット",
            },
            {
                "_uid": uuid.uuid4().hex,
                "name": "ABCレンタカー那覇空港営業所（返却）",
                "address": "沖縄県那覇市周辺",
                "lat": 26.1905,
                "lon": 127.6555,
                "day": "2026-07-20",
                "start": "16:00",
                "stay": 0,
                "fixed": True,
                "memo": "16:00までに返却",
                "category": "レンタカー",
            },
        ]

syoki_data()


def basho_hosoku(basho: dict) -> dict:
    kubun = basho.get("category", "観光スポット")
    shoki = KUBUN_SHOKI.get(kubun, KUBUN_SHOKI["観光スポット"])
    basho.setdefault("_uid", uuid.uuid4().hex)
    basho.setdefault("address", "")
    basho.setdefault("fixed", False)
    basho.setdefault("memo", "")
    basho.setdefault("category", kubun)
    basho.setdefault("cost", int(shoki["cost"]))
    basho.setdefault("open", str(shoki["open"]))
    basho.setdefault("close", str(shoki["close"]))
    basho.setdefault("indoor", bool(shoki["indoor"]))
    basho.setdefault("priority", int(shoki["priority"]))
    basho.setdefault("must_visit", False)
    basho.setdefault("map_url", "")
    basho.setdefault("manual_order", 9999)

    if kubun == "レンタカー" or "レンタカー" in str(basho.get("name", "")) or "返却" in str(basho.get("name", "")):
        basho["stay"] = 0

    return basho

for _spot in ss.spots:
    basho_hosoku(_spot)

def lan_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        if ip and not ip.startswith("127."):
            return ip
    except OSError:
        pass
    finally:
        sock.close()
    return ""

def qr_png(value: str) -> bytes:
    image = qrcode.make(value)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()

def map_url_gyo(moto_bun: str) -> list[dict]:
    results = []
    seen = set()
    for moto_gyo in str(moto_bun or "").splitlines():
        line = moto_gyo.strip()
        if not line:
            continue
        match = re.search(r"https?://[^\\s<>\\\"]+", line)
        if not match:
            results.append({"ok": False, "reason": "URLが見つかりません", "original": moto_gyo})
            continue
        url = match.group(0).rstrip("),。、]")
        if url in seen:
            results.append({"ok": False, "reason": "同じURLが重複しています", "url": url})
            continue
        seen.add(url)
        before = re.sub(r"[\\s|｜:：\\t]+$", "", line[:match.start()].strip())
        results.append({"ok": True, "url": url, "name_override": before[:100]})
    return results


def google_mei(value: str) -> str:
    value = html.unescape(urlparse.unquote_plus(str(value or ""))).strip()
    value = re.sub(r"\s*[-–—]\s*Google\s*Maps.*$", "", value, flags=re.I)
    value = re.sub(r"\s*·\s*Google.*$", "", value, flags=re.I)
    value = re.sub(r"\s+", " ", value).strip(" /|-")
    return value

def meta_toru(html_bun: str, key: str) -> str:
    patterns = [
        rf'<meta[^>]+property=["\']{re.escape(key)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{re.escape(key)}["\']',
        rf'<meta[^>]+name=["\']{re.escape(key)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']{re.escape(key)}["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, html_bun, flags=re.I)
        if match:
            return html.unescape(match.group(1)).strip()
    return ""

def seishiki_url_toru(html_bun: str) -> str:
    patterns = [
        r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
        r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']',
        r'<meta[^>]+property=["\']og:url["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:url["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, html_bun, flags=re.I)
        if match:
            return html.unescape(match.group(1)).strip()
    return ""

def google_zahyo(value: str):
    decoded = urlparse.unquote(str(value or ""))

    patterns = [
        r"!3d(-?\d{1,3}\.\d+)!4d(-?\d{1,3}\.\d+)",
        r"/@(-?\d{1,3}\.\d+),(-?\d{1,3}\.\d+),",
        r"(?:[?&](?:query|q|ll)=)(-?\d{1,3}\.\d+)\s*(?:,|%2C)\s*(-?\d{1,3}\.\d+)",
        r"(?:center=)(-?\d{1,3}\.\d+)%2C(-?\d{1,3}\.\d+)",
    ]
    for pattern in patterns:
        matches = list(re.finditer(pattern, decoded, flags=re.I))
        if matches:
            match = matches[-1]
            lat, lon = float(match.group(1)), float(match.group(2))
            if 20.0 <= lat <= 46.5 and 122.0 <= lon <= 154.5:
                return lat, lon
    return None

def kubun_hantei(name: str, address: str = "") -> str:
    target = f"{name} {address}".lower()

    hotel_go = [
        "hotel", "ホテル", "inn", "イン", "旅館", "民宿", "resort", "リゾート",
        "villa", "ヴィラ", "ロッジ", "hostel", "ホステル", "ゲストハウス",
        "terrace", "テラス", "tower", "タワー", "hilton", "ハイアット",
        "marriott", "マリオット", "nikko", "日航", "ana", "プリンス",
    ]
    rental_go = ["レンタカー", "rent a car", "car rental", "貸渡", "返却"]
    cafe_go = ["cafe", "coffee", "カフェ", "珈琲", "コーヒー"]
    res_go = ["restaurant", "レストラン", "食堂", "そば", "寿司", "焼肉", "居酒屋"]

    if any(word in target for word in rental_go):
        return "レンタカー"
    if any(word in target for word in hotel_go):
        return "ホテル"
    if any(word in target for word in cafe_go):
        return "カフェ"
    if any(word in target for word in res_go):
        return "ランチ・レストラン"
    return "観光スポット"

def map_url_kakunin(moto_url: str, mei_shitei: str = "") -> dict:
    url = str(moto_url or "").strip()
    if not re.match(r"^https?://", url):
        raise ValueError("https:// から始まるGoogleマップURLを貼ってください。")

    saigo_url = url
    html_bun = ""
    try:
        request = urlrequest.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 Chrome/124 Safari/537.36"
                ),
                "Accept-Language": "ja,en;q=0.8",
            },
        )
        with urlrequest.urlopen(request, timeout=18) as response:
            saigo_url = response.geturl()
            naiyo_shurui = response.headers.get("Content-Type", "")
            if "text/html" in naiyo_shurui:
                html_bun = response.read(1_500_000).decode("utf-8", errors="ignore")
    except Exception:
        saigo_url = url

    hon_url = seishiki_url_toru(html_bun)

    coords = None
    for koho_url in [saigo_url, hon_url, url]:
        if koho_url:
            coords = google_zahyo(koho_url)
            if coords:
                break

    name = mei_shitei.strip()
    address = ""

    for koho_url in [saigo_url, hon_url, url]:
        if not koho_url or name:
            continue
        parsed = urlparse.urlparse(koho_url)
        path_hit = re.search(r"/maps/(?:place|search)/([^/]+)", parsed.path)
        if path_hit:
            candidate = google_mei(path_hit.group(1))
            if candidate.lower() not in {"maps", "search"}:
                name = candidate

        if not name:
            query = urlparse.parse_qs(parsed.query)
            for key in ("query", "q"):
                candidate = query.get(key, [""])[0]
                if candidate and not re.fullmatch(
                    r"-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?",
                    candidate,
                ):
                    name = google_mei(candidate)
                    break

    og_mei = google_mei(meta_toru(html_bun, "og:title"))
    if og_mei and (not name or name in {"Google Maps", "Googleマップ"}):
        name = og_mei

    if not name and html_bun:
        title_hit = re.search(r"<title[^>]*>(.*?)</title>", html_bun, flags=re.I | re.S)
        if title_hit:
            name = google_mei(title_hit.group(1))

    description = (
        meta_toru(html_bun, "og:description")
        or meta_toru(html_bun, "description")
    )
    if description:
        address = re.sub(r"\s+", " ", html.unescape(description)).strip()[:240]

    # If URL has no coordinate, fall back to geocoding by resolved name.
    if coords is None and name:
        kensaku_bun = name if not address else f"{name} {address}"
        candidates = basho_kensaku(kensaku_bun)
        if not candidates:
            candidates = basho_kensaku(name)
        if candidates:
            coords = (candidates[0]["lat"], candidates[0]["lon"])
            if not address:
                address = candidates[0].get("address", "")

    if coords is None:
        raise ValueError(
            "場所の座標を取得できませんでした。"
            "Googleマップで店やホテルの詳細画面を開き、共有リンクを貼り直してください。"
        )

    if not name:
        gyaku_koho = basho_kensaku(f"{coords[0]},{coords[1]}")
        if gyaku_koho:
            name = gyaku_koho[0]["name"]
            if not address:
                address = gyaku_koho[0].get("address", "")
        else:
            name = "Googleマップの場所"

    kubun = kubun_hantei(name, address)

    return {
        "name": name[:100],
        "address": address,
        "lat": float(coords[0]),
        "lon": float(coords[1]),
        "map_url": saigo_url or hon_url or url,
        "category": kubun,
    }

def toroku_yomu() -> list[dict]:
    if not FILE_TOROKU.exists():
        return []
    try:
        data = json.loads(FILE_TOROKU.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []

def toroku_hozon() -> None:
    FILE_TOROKU.write_text(
        json.dumps(ss.registered_places, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

if not ss.registered_places:
    ss.registered_places = toroku_yomu()


def kyoyu_data() -> dict:
    return {
        "version": 8,
        "updated_at": datetime.now().isoformat(timespec="microseconds"),
        "trip_start": str(ss.trip_start),
        "trip_days": int(ss.trip_days),
        "spots": ss.spots,
        "day_modes": ss.day_modes,
        "map_region": ss.map_region,
        "day_start_times": ss.day_start_times,
        "registered_places": ss.registered_places,
    }


def kyoyu_hanei(payload: dict) -> bool:
    if not isinstance(payload, dict) or "spots" not in payload:
        return False

    ss.spots = payload.get("spots", [])
    ss.trip_start = date.fromisoformat(
        payload.get("trip_start", str(ss.trip_start))
    )
    ss.trip_days = int(
        payload.get("trip_days", ss.trip_days)
    )
    ss.day_modes = payload.get("day_modes", {})
    ss.map_region = payload.get(
        "map_region",
        ss.map_region,
    )
    ss.day_start_times = payload.get("day_start_times", {})
    ss.registered_places = payload.get(
        "registered_places",
        ss.registered_places,
    )

    id_seiri()
    for basho in ss.spots:
        basho_hosoku(basho)

    ss["_shared_updated_at"] = str(
        payload.get("updated_at", "")
    )
    return True


def kyoyu_hozon() -> None:
    """Macとスマホが共通で読むJSONへ、壊れないよう原子的に保存する。"""
    payload = kyoyu_data()
    kari_file = FILE_KYOYU.with_suffix(".tmp")

    kari_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(kari_file, FILE_KYOYU)

    ss["_shared_updated_at"] = payload["updated_at"]
    try:
        ss["_shared_mtime_ns"] = FILE_KYOYU.stat().st_mtime_ns
    except OSError:
        pass


def kyoyu_yomu(force: bool = False) -> bool:
    """
    別ブラウザで更新された共有データだけを読み込む。
    同じセッション自身の保存直後は読み戻さない。
    """
    if not FILE_KYOYU.exists():
        return False

    try:
        ima_mtime = FILE_KYOYU.stat().st_mtime_ns
    except OSError:
        return False

    mae_mtime = int(ss.get("_shared_mtime_ns", 0) or 0)
    if not force and ima_mtime <= mae_mtime:
        return False

    try:
        payload = json.loads(FILE_KYOYU.read_text(encoding="utf-8"))
    except Exception:
        return False

    kyoyu_koshin = str(payload.get("updated_at", ""))
    jibun_koshin = str(ss.get("_shared_updated_at", ""))

    if not force and kyoyu_koshin and kyoyu_koshin == jibun_koshin:
        ss["_shared_mtime_ns"] = ima_mtime
        return False

    if not kyoyu_hanei(payload):
        return False

    ss["_shared_mtime_ns"] = ima_mtime
    ss["_schedule_initialized"] = True
    return True


def auto_hozon() -> None:
    payload = kyoyu_data()

    try:
        FILE_BACKUP.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass

    try:
        kyoyu_hozon()
    except Exception:
        pass


def rental_ka(basho: dict) -> bool:
    name = str(basho.get("name", ""))
    return str(basho.get("category", "")) == "レンタカー" or "レンタカー" in name or "返却" in name

def hotel_ka(basho: dict) -> bool:
    return str(basho.get("category", "")) == "ホテル"

def hi_bunrui(hi: str):
    items = [s for s in ss.spots if s.get("day") == hi]
    rental_uke = [s for s in items if rental_ka(s) and "返却" not in str(s.get("name", ""))]
    rental_hen = [s for s in items if rental_ka(s) and "返却" in str(s.get("name", ""))]
    hotels = [s for s in items if hotel_ka(s)]
    kanko_list = [s for s in items if s not in rental_uke and s not in rental_hen and s not in hotels]
    kanko_list.sort(key=lambda s: int(s.get("manual_order", 9999)))
    return rental_uke, kanko_list, hotels, rental_hen


def henshu_bunrui(hi: str):
    hyoji_list = hi_hyoji(hi)
    rental_uke = [
        item for item in hyoji_list
        if rental_ka(item)
        and "返却" not in str(item.get("name", ""))
        and not item.get("is_day_start_anchor")
    ]
    kanko_list = [
        item for item in hyoji_list
        if not rental_ka(item)
        and not hotel_ka(item)
        and not item.get("is_day_start_anchor")
    ]
    hotels = [
        item for item in hyoji_list
        if hotel_ka(item)
        and not item.get("is_day_start_anchor")
    ]
    rental_hen = [
        item for item in hyoji_list
        if rental_ka(item)
        and "返却" in str(item.get("name", ""))
        and not item.get("is_day_start_anchor")
    ]
    shuppatsu = next(
        (item for item in hyoji_list if item.get("is_day_start_anchor")),
        None,
    )
    return shuppatsu, rental_uke, kanko_list, hotels, rental_hen

def junban_seiri(hi: str) -> None:
    for i, basho in enumerate(hi_bunrui(hi)[1]):
        basho["manual_order"] = i

def kanko_jun_ido(hi: str, uid: str, direction: int) -> None:
    spots = hi_bunrui(hi)[1]
    ids = [s["_uid"] for s in spots]
    if uid not in ids: return
    i = ids.index(uid); j = i + direction
    if j < 0 or j >= len(spots): return
    spots[i]["manual_order"], spots[j]["manual_order"] = spots[j].get("manual_order",j), spots[i].get("manual_order",i)
    junban_seiri(hi)

def hi_yotei(hi: str):
    a,b,c,d = hi_bunrui(hi)
    return a+b+c+d

def zenjitsu_hotel(hi: str) -> dict | None:
    """指定日の前日に設定されたホテルを1軒取得する。"""
    try:
        mae_hi = str(date.fromisoformat(hi) - timedelta(days=1))
    except (TypeError, ValueError):
        return None

    hotels = [
        basho for basho in ss.spots
        if hotel_ka(basho)
        and str(basho.get("day", "")) == mae_hi
    ]
    if not hotels:
        return None

    return sorted(
        hotels,
        key=lambda item: (
            0 if item.get("scheduled_hotel") else 1,
            0 if item.get("auto_hotel") else 1,
            str(item.get("start", "23:59")),
        ),
    )[0]


def hi_hyoji(hi: str) -> list[dict]:
    """
    旅のしおり・予定編集・地図・距離集計で共通利用する1日の並び。
    レンタカー受取がない2日目以降は、前泊ホテルを出発地点として追加する。
    """
    moto_list = hi_yotei(hi)
    rental_uke, _, _, _ = hi_bunrui(hi)

    if rental_uke:
        return moto_list

    hotel = zenjitsu_hotel(hi)
    if hotel is None:
        return moto_list

    hotel_start = copy.deepcopy(hotel)
    hotel_start["_uid"] = f"previous_hotel_{hi}_{hotel.get('_uid', '')}"
    hotel_start["day"] = hi
    hotel_start["start"] = kaishi_jikoku(hi)
    hotel_start["arrival"] = kaishi_jikoku(hi)
    hotel_start["departure"] = kaishi_jikoku(hi)
    hotel_start["stay"] = 0
    hotel_start["memo"] = "前泊ホテルから出発"
    hotel_start["is_day_start_anchor"] = True
    hotel_start["fixed"] = True
    hotel_start["editable"] = False
    hotel_start["travel_minutes_from_previous"] = 0
    hotel_start["distance_km_from_previous"] = 0.0
    return [hotel_start] + moto_list


def hi_keiro(hi: str) -> list[dict]:
    return hi_hyoji(hi)



def yotei_hi_ido(uid: str, ido_hi: str) -> tuple[bool, str]:
    """観光・固定予定・ホテル・レンタカーを別の日へ移動する。"""
    item = next(
        (basho for basho in ss.spots if basho.get("_uid") == uid),
        None,
    )
    if item is None:
        return False, "予定が見つかりませんでした。"

    moto_hi = str(item.get("day", ""))
    ido_hi = str(ido_hi)

    if moto_hi == ido_hi:
        return False, "日付は変更されていません。"

    # ホテルは移動先にすでにホテルがある場合、重複させず日付を入れ替える。
    if hotel_ka(item):
        aite_hotel = next(
            (
                basho for basho in ss.spots
                if basho.get("_uid") != uid
                and hotel_ka(basho)
                and str(basho.get("day", "")) == ido_hi
            ),
            None,
        )
        if aite_hotel is not None:
            aite_hotel["day"] = moto_hi

    item["day"] = ido_hi

    if not hotel_ka(item) and not rental_ka(item):
        item["manual_order"] = len(hi_bunrui(ido_hi)[1])

    for taisho_hi in {moto_hi, ido_hi}:
        if taisho_hi:
            junban_seiri(taisho_hi)
            nittei_saikeisan(
                taisho_hi,
                ss.day_modes.get(taisho_hi, "車"),
                narabikae=False,
            )

            if hotel_ka(item):
                try:
                    yoku_hi = str(date.fromisoformat(taisho_hi) + timedelta(days=1))
                except ValueError:
                    yoku_hi = ""
                if yoku_hi in [str(hi) for hi in ryoko_bi()]:
                    nittei_saikeisan(
                        yoku_hi,
                        ss.day_modes.get(yoku_hi, "車"),
                        narabikae=False,
                    )

    widget_seiri(uid)
    auto_hozon()
    return True, f"{date.fromisoformat(ido_hi).strftime('%m月%d日')}へ移動しました。"


def kaishi_jikoku(hi: str) -> str:
    return ss.day_start_times.get(hi, "09:00")

def kaishi_jikoku_set(hi: str, value: str) -> None:
    ss.day_start_times[hi] = value


def widget_seiri(uid: str) -> None:
    """削除・日程変更後に残るStreamlitウィジェット状態を消す。"""
    uid = str(uid)
    prefixes = (
        f"stay_{uid}",
        f"memo_{uid}",
        f"up_{uid}",
        f"down_{uid}",
        f"del_{uid}",
        f"remove_hotel_{uid}",
    )

    for key in list(ss.keys()):
        key_moji = str(key)
        if key_moji in prefixes or key_moji.endswith(f"_{uid}"):
            del ss[key]


def yotei_sakujo(uid: str) -> tuple[bool, set[str]]:
    """指定UIDの予定を完全に削除し、影響日を返す。"""
    taisho_list = [
        basho
        for basho in ss.spots
        if str(basho.get("_uid", "")) == str(uid)
    ]
    eikyo_hi = {
        str(basho.get("day", ""))
        for basho in taisho_list
    }
    hotel_keshi = any(hotel_ka(basho) for basho in taisho_list)

    before = len(ss.spots)
    ss.spots = [
        basho
        for basho in ss.spots
        if str(basho.get("_uid", "")) != str(uid)
    ]
    deleted = len(ss.spots) < before

    widget_seiri(uid)

    for hi in sorted(hi for hi in eikyo_hi if hi):
        junban_seiri(hi)
        nittei_saikeisan(
            hi,
            ss.day_modes.get(hi, "車"),
            narabikae=False,
        )

        if hotel_keshi:
            try:
                yoku_hi = str(date.fromisoformat(hi) + timedelta(days=1))
            except ValueError:
                yoku_hi = ""
            if yoku_hi in [str(item) for item in ryoko_bi()]:
                nittei_saikeisan(
                    yoku_hi,
                    ss.day_modes.get(yoku_hi, "車"),
                    narabikae=False,
                )

    if deleted:
        auto_hozon()

    return deleted, eikyo_hi


def basho_sagasu(uid: str) -> dict | None:
    return next(
        (basho for basho in ss.spots if basho.get("_uid") == uid),
        None,
    )



def jikoku_saikeisan(hi: str) -> None:
    """
    保存済みの移動時間を使って、到着・出発時刻だけを高速再計算する。
    外部の経路サーバーへは接続しない。
    """
    items = hi_yotei(hi)
    if not items:
        return

    cursor = hhmm_fun(kaishi_jikoku(hi))
    rental_uke, _, _, _ = hi_bunrui(hi)
    mae_hotel = None if rental_uke else zenjitsu_hotel(hi)

    for index, item in enumerate(items):
        if index == 0:
            if mae_hotel is not None:
                cursor += int(item.get("travel_minutes_from_previous", 0) or 0)
        else:
            cursor += int(item.get("travel_minutes_from_previous", 0) or 0)

        item["arrival"] = fun_hhmm(cursor)
        item["start"] = item["arrival"]
        cursor += int(item.get("stay", 0 if rental_ka(item) else 60))
        item["departure"] = fun_hhmm(cursor)


def jikoku_saikeisan_yoku(hi: str) -> None:
    jikoku_saikeisan(hi)

    try:
        yoku_hi = str(date.fromisoformat(hi) + timedelta(days=1))
    except (TypeError, ValueError):
        yoku_hi = ""

    if yoku_hi in [str(item) for item in ryoko_bi()]:
        jikoku_saikeisan(yoku_hi)


def nittei_saikeisan_yoku(hi: str) -> None:
    if not hi:
        return

    nittei_saikeisan(
        hi,
        ss.day_modes.get(hi, "車"),
        narabikae=False,
    )

    try:
        yoku_hi = str(date.fromisoformat(hi) + timedelta(days=1))
    except (TypeError, ValueError):
        yoku_hi = ""

    if yoku_hi in [str(item) for item in ryoko_bi()]:
        nittei_saikeisan(
            yoku_hi,
            ss.day_modes.get(yoku_hi, "車"),
            narabikae=False,
        )


def basho_henko(
    uid: str,
    komoku: str,
    wkey: str,
    hi: str,
    sai_keisan: bool = True,
) -> None:
    """入力変更をデータへ即時反映し、必要なら時刻も即時再計算する。"""
    basho = basho_sagasu(uid)
    if basho is None or wkey not in ss:
        return

    value = ss[wkey]
    if komoku in {"stay", "cost", "priority", "manual_order"}:
        value = int(value)

    basho[komoku] = value

    if sai_keisan:
        jikoku_saikeisan(hi)

    auto_hozon()


def kaishi_henko(hi: str, wkey: str) -> None:
    value = ss.get(wkey)
    if value is None:
        return

    if hasattr(value, "strftime"):
        value = value.strftime("%H:%M")
    else:
        value = str(value)

    kaishi_jikoku_set(hi, value)
    jikoku_saikeisan(hi)
    auto_hozon()


def ido_henko(hi: str, wkey: str) -> None:
    ido = ss.get(wkey, "車")
    ss.day_modes[hi] = ido
    nittei_saikeisan(hi, ido, narabikae=False)
    auto_hozon()


def ryoko_henko() -> None:
    """旅行開始日・日数の変更を同じ再実行内で反映する。"""
    if "_trip_start_input" in ss:
        ss.trip_start = ss["_trip_start_input"]
    if "_trip_days_input" in ss:
        ss.trip_days = int(ss["_trip_days_input"])

    for ryoko_hi in ryoko_bi():
        ss.day_modes.setdefault(str(ryoko_hi), "車")

    zenbi_saikeisan(narabikae=False)
    auto_hozon()


def hhmm_fun(value: str) -> int:
    try:
        hour, minute = str(value).split(":")
        return int(hour) * 60 + int(minute)
    except Exception:
        return 9 * 60

def fun_hhmm(value: int) -> str:
    value = max(0, int(value))
    return f"{(value // 60) % 24:02d}:{value % 60:02d}"

def nittei_saikeisan(hi: str, ido: str, narabikae: bool = False) -> None:
    rental_uke, kanko_list, hotels, rental_hen = hi_bunrui(hi)

    if narabikae and len(kanko_list) > 1:
        remaining = kanko_list[:]
        ordered = []

        if rental_uke:
            current = rental_uke[-1]
        else:
            current = zenjitsu_hotel(hi)

        if current is None:
            current = remaining.pop(0)
            ordered.append(current)

        while remaining:
            tsugi_basho = min(remaining, key=lambda item: chokusen_km(current, item))
            ordered.append(tsugi_basho)
            remaining.remove(tsugi_basho)
            current = tsugi_basho

        for index, item in enumerate(ordered):
            item["manual_order"] = index
        kanko_list = ordered

    items = rental_uke + kanko_list + hotels + rental_hen
    if not items:
        return

    cursor = hhmm_fun(kaishi_jikoku(hi))

    # レンタカー受取がない日は、前泊ホテルがその日の出発地点。
    previous = None if rental_uke else zenjitsu_hotel(hi)

    for item in items:
        if previous is None:
            item["travel_minutes_from_previous"] = 0
            item["distance_km_from_previous"] = 0.0
            item["route_estimated"] = False
        else:
            route = keiro_shutoku(
                previous["lat"],
                previous["lon"],
                item["lat"],
                item["lon"],
                ido,
            )
            if route.get("ok"):
                item["travel_minutes_from_previous"] = int(route["minutes"])
                item["distance_km_from_previous"] = float(route["km"])
                item["route_estimated"] = False
                item["route_error"] = ""
                cursor += int(route["minutes"])
            else:
                item["travel_minutes_from_previous"] = 0
                item["distance_km_from_previous"] = 0.0
                item["route_estimated"] = False
                item["route_error"] = route.get("error", "道路経路を取得できませんでした")

        item["arrival"] = fun_hhmm(cursor)
        item["start"] = item["arrival"]
        cursor += int(item.get("stay", 60))
        item["departure"] = fun_hhmm(cursor)
        previous = item

def zenbi_saikeisan(narabikae: bool = False) -> None:
    for hi in ryoko_bi():
        hi_moji = str(hi)
        ido = ss.day_modes.get(hi_moji, "車")
        nittei_saikeisan(hi_moji, ido, narabikae=narabikae)

def hi_gokei(hi: str) -> tuple[int, float]:
    items = hi_hyoji(hi)
    gokei_fun = sum(int(item.get("travel_minutes_from_previous", 0)) for item in items)
    gokei_km = sum(float(item.get("distance_km_from_previous", 0.0)) for item in items)
    return gokei_fun, round(gokei_km, 1)

def chikaku_jun(hi: str, ido: str) -> None:
    nittei_saikeisan(hi, ido, narabikae=True)


def hotel_koho() -> list[dict]:
    return [
        place for place in ss.registered_places
        if place.get("category") == "ホテル"
    ]

def nittei_hotel() -> list[dict]:
    return [
        basho for basho in ss.spots
        if basho.get("category") == "ホテル"
    ]

def toroku_kesu(uid: str) -> None:
    ss.registered_places = [
        place for place in ss.registered_places
        if place.get("_uid") != uid
    ]
    toroku_hozon()


def hotel_hazusu(uid: str) -> None:
    """自動追加・手動追加・旧データを問わず、指定ホテルを日程から外す。"""
    hazushi_hi = {
        basho.get("day")
        for basho in ss.spots
        if basho.get("_uid") == uid and basho.get("category") == "ホテル"
    }
    ss.spots = [
        basho for basho in ss.spots
        if not (basho.get("_uid") == uid and basho.get("category") == "ホテル")
    ]
    for hi in hazushi_hi:
        if hi:
            nittei_saikeisan(hi, ss.day_modes.get(hi, "車"), narabikae=False)
    auto_hozon()


def hi_hotel_hazusu(hi: str) -> int:
    """指定日のホテルをすべて日程から外す。候補一覧は消さない。"""
    before = len(ss.spots)
    ss.spots = [
        basho for basho in ss.spots
        if not (basho.get("category") == "ホテル" and basho.get("day") == hi)
    ]
    removed = before - len(ss.spots)
    nittei_saikeisan(hi, ss.day_modes.get(hi, "車"), narabikae=False)
    auto_hozon()
    return removed


def hotel_jufuku() -> dict[str, int]:
    """各日にホテルを1軒だけ残し、残りを日程から外す。"""
    grouped: dict[str, list[dict]] = {}
    for basho in ss.spots:
        if basho.get("category") == "ホテル" and basho.get("day"):
            grouped.setdefault(str(basho["day"]), []).append(basho)

    nokosu_id: set[str] = set()
    hi_betsu_kesu: dict[str, int] = {}
    for hi, hotels in grouped.items():
        hotel_jun = sorted(
            hotels,
            key=lambda item: (
                0 if item.get("scheduled_hotel") else 1,
                0 if item.get("auto_hotel") else 1,
                int(item.get("manual_order", 9999)),
                str(item.get("start", "23:59")),
            ),
        )
        nokosu_id.add(hotel_jun[0]["_uid"])
        if len(hotel_jun) > 1:
            hi_betsu_kesu[hi] = len(hotel_jun) - 1

    if hi_betsu_kesu:
        ss.spots = [
            basho for basho in ss.spots
            if basho.get("category") != "ホテル" or basho.get("_uid") in nokosu_id
        ]
        for hi in hi_betsu_kesu:
            nittei_saikeisan(hi, ss.day_modes.get(hi, "車"), narabikae=False)
        auto_hozon()
    return hi_betsu_kesu


def hotel_set(candidate: dict, haku: int) -> None:
    dates = ryoko_bi()
    if haku < 0 or haku >= max(0, len(dates) - 1):
        raise ValueError("宿泊日が範囲外です。")

    hi = str(dates[haku])

    # 同じ日にはホテルを1軒だけ残す。旧データ由来も含めて置き換える。
    ss.spots = [
        basho for basho in ss.spots
        if not (basho.get("category") == "ホテル" and basho.get("day") == hi)
    ]

    event = copy.deepcopy(candidate)
    event["_uid"] = uuid.uuid4().hex
    event["day"] = hi
    event["start"] = "19:00"
    event["stay"] = 30
    event["fixed"] = True
    event["scheduled_hotel"] = True
    event["source_candidate_uid"] = candidate.get("_uid")
    event["auto_hotel"] = True
    event["memo"] = f"{haku + 1}泊目"
    event["manual_order"] = 9999
    ss.spots.append(event)

    nittei_saikeisan(
        hi,
        ss.day_modes.get(hi, "車"),
        narabikae=False,
    )
    auto_hozon()

def hotel_wariate(hotel_id_list: list[str | None]) -> None:
    """泊ごとに選ばれたホテルだけを設定する。未設定は何も入れない。"""
    dates = ryoko_bi()
    nights = max(0, len(dates) - 1)
    koho_map = {
        place["_uid"]: place
        for place in hotel_koho()
    }
    ryoko_hi_set = {str(hi) for hi in dates[:-1]}

    # 旅行期間内の日程ホテルを一度すべて外す。候補一覧は残す。
    ss.spots = [
        basho for basho in ss.spots
        if not (
            basho.get("category") == "ホテル"
            and str(basho.get("day", "")) in ryoko_hi_set
        )
    ]

    for haku in range(nights):
        hotel_id = hotel_id_list[haku] if haku < len(hotel_id_list) else None
        if not hotel_id:
            continue
        candidate = koho_map.get(hotel_id)
        if candidate is not None:
            hotel_set(candidate, haku)

    zenbi_saikeisan(narabikae=False)
    auto_hozon()

def api_json(url, params=None, method="get", data=None, timeout=30):
    headers = {"User-Agent": UA, "Accept-Language": "ja"}
    if method == "post":
        response = requests.post(url, data=data, headers=headers, timeout=timeout)
    else:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()

@st.cache_data(ttl=86400, show_spinner=False)
def basho_kensaku(query):
    data = api_json(
        API_KENSAKU,
        params={
            "q": query,
            "format": "jsonv2",
            "limit": 8,
            "countrycodes": "jp",
            "addressdetails": 1,
        },
    )
    return [
        {
            "name": item.get("name") or item["display_name"].split(",")[0],
            "address": item["display_name"],
            "lat": float(item["lat"]),
            "lon": float(item["lon"]),
        }
        for item in data
    ]

@st.cache_data(ttl=3600, show_spinner=False)
def shuhen_kensaku(lat, lon, kubun, radius):
    clauses = []
    for rule in KUBUN_JOKEN[kubun]:
        clauses.extend([
            f"node{rule}(around:{radius},{lat},{lon});",
            f"way{rule}(around:{radius},{lat},{lon});",
            f"relation{rule}(around:{radius},{lat},{lon});",
        ])
    query = f"[out:json][timeout:25];({''.join(clauses)});out center tags 40;"
    data = api_json(API_SHUHEN, method="post", data={"data": query})
    result = []
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name:ja") or tags.get("name")
        if not name:
            continue
        center = element.get("center", {})
        rlat = element.get("lat", center.get("lat"))
        rlon = element.get("lon", center.get("lon"))
        if rlat is None or rlon is None:
            continue
        result.append({
            "name": name,
            "address": " ".join(filter(None, [
                tags.get("addr:province"),
                tags.get("addr:city"),
                tags.get("addr:suburb"),
            ])),
            "lat": float(rlat),
            "lon": float(rlon),
            "category": kubun,
        })
    unique = {}
    for item in result:
        unique[(item["name"], round(item["lat"], 5), round(item["lon"], 5))] = item
    return list(unique.values())

def chokusen_km(a, b):
    radius = 6371
    p1 = math.radians(a["lat"])
    p2 = math.radians(b["lat"])
    dp = math.radians(b["lat"] - a["lat"])
    dl = math.radians(b["lon"] - a["lon"])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))

def keiro_ok(
    coords: list[list[float]],
    choku_km: float,
    michi_km: float,
) -> bool:
    """
    道路形状が返っていることだけを確認する。
    正常な離島・湾岸道路を誤って弾かないよう、距離比による厳しい拒否はしない。
    """
    if len(coords) < 3:
        return False

    if michi_km <= 0:
        return False

    # 完全な直線代用に近い2点だけの形状は上で拒否済み。
    # 正常な道路形状は細かい中間点を持つため、その場合のみ採用する。
    return True


def polyline_fukugo(encoded: str, precision: int = 6) -> list[list[float]]:
    """Valhallaのencoded polylineを[lat, lon]へ変換する。"""
    if not encoded:
        return []

    coordinates = []
    index = 0
    latitude = 0
    longitude = 0
    factor = 10 ** precision

    while index < len(encoded):
        values = []

        for _ in range(2):
            result = 0
            shift = 0

            while True:
                if index >= len(encoded):
                    return coordinates

                byte = ord(encoded[index]) - 63
                index += 1
                result |= (byte & 0x1F) << shift
                shift += 5

                if byte < 0x20:
                    break

            values.append(~(result >> 1) if result & 1 else result >> 1)

        latitude += values[0]
        longitude += values[1]
        coordinates.append([latitude / factor, longitude / factor])

    return coordinates


def val_keiro(a_lat, a_lon, b_lat, b_lon, ido):
    costing = {
        "車": "auto",
        "徒歩": "pedestrian",
        "自転車": "bicycle",
    }.get(ido, "auto")

    payload = {
        "locations": [
            {"lat": float(a_lat), "lon": float(a_lon)},
            {"lat": float(b_lat), "lon": float(b_lon)},
        ],
        "costing": costing,
        "units": "kilometers",
        "directions_options": {"units": "kilometers"},
    }

    response = requests.post(
        API_VALHALLA,
        json=payload,
        headers={
            "User-Agent": UA,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        timeout=35,
    )
    response.raise_for_status()
    data = response.json()

    trip = data.get("trip") or {}
    summary = trip.get("summary") or {}
    legs = trip.get("legs") or []

    if not legs:
        return None

    shape = str(legs[0].get("shape") or "")
    coords = polyline_fukugo(shape, precision=6)
    km = float(summary.get("length") or 0.0)
    minutes = max(1, round(float(summary.get("time") or 0.0) / 60))

    if not keiro_ok(coords, 0.0, km):
        return None

    return {
        "ok": True,
        "minutes": minutes,
        "km": round(km, 1),
        "coords": coords,
        "estimated": False,
        "source": "Valhalla道路経路",
        "error": "",
    }


def keiro_gaisan(a_lat, a_lon, b_lat, b_lon, ido):
    """
    道路経路サーバーが使えない時だけ、距離と時間を数値で概算する。
    地図描画用の座標は返さないため、海上の直線は表示されない。
    """
    choku_km = chokusen_km(
        {"lat": float(a_lat), "lon": float(a_lon)},
        {"lat": float(b_lat), "lon": float(b_lon)},
    )

    michi_bairitsu = {
        "車": 1.30,
        "徒歩": 1.18,
        "自転車": 1.22,
    }.get(ido, 1.30)

    heikin_soku = {
        "車": 38.0,
        "徒歩": 4.5,
        "自転車": 15.0,
    }.get(ido, 38.0)

    gaisan_km = max(0.1, choku_km * michi_bairitsu)
    gaisan_fun = max(
        1,
        round((gaisan_km / heikin_soku) * 60),
    )

    return {
        "ok": True,
        "minutes": gaisan_fun,
        "km": round(gaisan_km, 1),
        "coords": [],
        "estimated": True,
        "source": "概算",
        "error": "",
    }


@st.cache_data(ttl=900, show_spinner=False)
def keiro_shutoku(a_lat, a_lon, b_lat, b_lon, ido):
    """
    まずOSRM、失敗時はValhallaから道路経路を取得する。
    直線距離による代用は行わない。
    """
    endpoints = API_KEIRO.get(ido, API_KEIRO["車"])
    choku_km = chokusen_km(
        {"lat": float(a_lat), "lon": float(a_lon)},
        {"lat": float(b_lat), "lon": float(b_lon)},
    )
    errors = []

    for endpoint in endpoints:
        try:
            data = api_json(
                f"{endpoint}/route/v1/driving/{a_lon},{a_lat};{b_lon},{b_lat}",
                params={
                    "overview": "full",
                    "geometries": "geojson",
                    "steps": "false",
                    "alternatives": "false",
                },
                timeout=30,
            )

            if data.get("code") != "Ok" or not data.get("routes"):
                errors.append(str(data.get("message") or data.get("code") or "OSRM経路なし"))
                continue

            route = data["routes"][0]
            coordinates = route.get("geometry", {}).get("coordinates", [])
            coords = [[lat, lon] for lon, lat in coordinates]
            michi_km = round(float(route.get("distance", 0)) / 1000, 1)
            minutes = max(1, round(float(route.get("duration", 0)) / 60))

            if keiro_ok(coords, choku_km, michi_km):
                return {
                    "ok": True,
                    "minutes": minutes,
                    "km": michi_km,
                    "coords": coords,
                    "estimated": False,
                    "source": "OSRM道路経路",
                    "error": "",
                }

            errors.append("OSRMの道路形状が不完全でした")

        except Exception as exc:
            errors.append(f"OSRM: {exc}")

    try:
        val_kekka = val_keiro(
            a_lat,
            a_lon,
            b_lat,
            b_lon,
            ido,
        )
        if val_kekka:
            return val_kekka
        errors.append("Valhalla経路なし")
    except Exception as exc:
        errors.append(f"Valhalla: {exc}")

    fallback = keiro_gaisan(
        a_lat,
        a_lon,
        b_lat,
        b_lon,
        ido,
    )
    fallback["error_detail"] = " / ".join(errors[-3:])
    return fallback


def jikan_hyoji(minutes):
    hours, mins = divmod(int(minutes), 60)
    if hours and mins:
        return f"{hours}時間{mins}分"
    if hours:
        return f"{hours}時間"
    return f"{mins}分"


def keiro_bun(item: dict) -> str:
    """旅のしおりに表示する経路情報を安全に組み立てる。"""
    minutes = int(item.get("travel_minutes_from_previous", 0) or 0)
    km = float(item.get("distance_km_from_previous", 0.0) or 0.0)

    if minutes > 0:
        prefix = "概算 " if item.get("route_estimated") else ""
        return f"{prefix}{jikan_hyoji(minutes)} / {km:.1f}km"

    if item.get("is_day_start_anchor"):
        return "ホテル出発"

    return "開始地点"


def gmap_url(basho):
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(str(basho['lat']) + ',' + str(basho['lon']))}"

def gmap_keiro_url(origin: dict, destination: dict, ido: str = "車") -> str:
    travelmode = {"車": "driving", "徒歩": "walking", "自転車": "bicycling"}.get(ido, "driving")
    return (
        "https://www.google.com/maps/dir/?api=1"
        f"&origin={origin['lat']},{origin['lon']}"
        f"&destination={destination['lat']},{destination['lon']}"
        f"&travelmode={travelmode}"
    )

def ryoko_bi():
    return [
        ss.trip_start + timedelta(days=i)
        for i in range(int(ss.trip_days))
    ]

def id_seiri():
    seen = set()
    for basho in ss.spots:
        uid = str(basho.get("_uid", "")).strip()
        if not uid or uid in seen:
            uid = uuid.uuid4().hex
            basho["_uid"] = uid
        seen.add(uid)

def basho_tsuika(basho, hi, start, stay, kubun):
    shoki = KUBUN_SHOKI.get(kubun, KUBUN_SHOKI["観光スポット"])
    ss.spots.append({
        "_uid": uuid.uuid4().hex,
        "name": basho["name"],
        "address": basho.get("address", ""),
        "lat": float(basho["lat"]),
        "lon": float(basho["lon"]),
        "day": hi,
        "start": start,
        "stay": int(stay),
        "fixed": False,
        "memo": "",
        "category": kubun,
        "cost": int(shoki["cost"]),
        "open": str(shoki["open"]),
        "close": str(shoki["close"]),
        "indoor": bool(shoki["indoor"]),
        "priority": int(shoki["priority"]),
        "must_visit": False,
        "map_url": basho.get("map_url", ""),
        "manual_order": len(hi_bunrui(hi)[1]) if kubun not in ("ホテル", "レンタカー") else 9999,
    })
    ss.map_region = chiiki_hantei(float(basho["lat"]), float(basho["lon"]))
    ido = ss.day_modes.get(hi, "車")
    nittei_saikeisan(hi, ido, narabikae=False)
    auto_hozon()

def chizu_tsukuru(sentaku_hi=None):
    region = ss.map_region
    chushin_lat, chushin_lon, zoom = CHIIKI_CHUSHIN.get(region, CHIIKI_CHUSHIN["日本全体"])
    fmap = folium.Map(
        location=[chushin_lat, chushin_lon],
        zoom_start=zoom,
        control_scale=True,
        tiles="OpenStreetMap",
    )

    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
        attr="OpenStreetMap HOT",
        name="見やすい地図",
    ).add_to(fmap)

    hyoji_basho = ss.spots
    if region != "日本全体":
        hyoji_basho = [
            basho for basho in ss.spots
            if chiiki_hantei(basho["lat"], basho["lon"]) == region
        ]

    cluster = MarkerCluster(name="登録地点").add_to(fmap)
    for index, basho in enumerate(hyoji_basho, start=1):
        iro = "red" if basho.get("fixed") else "blue"
        popup = f"""
        <b>{index}. {basho['name']}</b><br>
        {basho.get('address', '')}<br>
        {basho['day']} {basho['start']}<br>
        滞在 {basho['stay']}分 / 予算 {basho.get('cost',0):,}円<br>
        営業 {basho.get('open','?')}〜{basho.get('close','?')} / 優先度 {basho.get('priority',3)}
        """
        folium.Marker(
            [basho["lat"], basho["lon"]],
            tooltip=f"{index}. {basho['name']}",
            popup=folium.Popup(popup, max_width=320),
            icon=folium.Icon(color=iro, icon="info-sign"),
        ).add_to(cluster)

    if sentaku_hi:
        hi_basho = hi_hyoji(sentaku_hi)
        ido = ss.day_modes.get(sentaku_hi, "車")
        for i in range(1, len(hi_basho)):
            origin = hi_basho[i - 1]
            destination = hi_basho[i]
            coords = destination.get("route_coords", [])

            if not coords:
                continue

            tooltip = (
                f"{origin['name']} → {destination['name']}｜"
                f"{jikan_hyoji(destination.get('travel_minutes_from_previous', 0))}｜"
                f"{destination.get('distance_km_from_previous', 0):.1f}km"
            )
            AntPath(
                locations=coords,
                tooltip=tooltip,
                color="#ff5f70",
                pulse_color="#ffffff",
                weight=7,
                opacity=0.9,
                delay=900,
            ).add_to(fmap)

    if hyoji_basho:
        fmap.fit_bounds([
            [min(s["lat"] for s in hyoji_basho), min(s["lon"] for s in hyoji_basho)],
            [max(s["lat"] for s in hyoji_basho), max(s["lon"] for s in hyoji_basho)],
        ], padding=(35, 35))

    folium.LayerControl(collapsed=True).add_to(fmap)
    return fmap

def gamen_ido(page):
    ss.page = page
    st.rerun()

id_seiri()

# Macとスマホの別セッションで更新された共有データを読み込む。
_shared_changed = kyoyu_yomu(force=False)
if _shared_changed:
    for _day in ryoko_bi():
        ss.day_modes.setdefault(str(_day), "車")

if not ss.get("_route_cache_cleared_v4", False):
    try:
        keiro_shutoku.clear()
    except Exception:
        pass
    ss["_route_cache_cleared_v4"] = True

for _scheduled_spot in ss.spots:
    if rental_ka(_scheduled_spot):
        _scheduled_spot["stay"] = 0

for hi in ryoko_bi():
    ss.day_modes.setdefault(str(hi), "車")

# 初回表示時だけ全日程を計算する。以降は各入力のコールバックで即時更新する。
if not ss.get("_schedule_initialized", False):
    zenbi_saikeisan(narabikae=False)
    ss["_schedule_initialized"] = True

if not FILE_KYOYU.exists():
    try:
        kyoyu_hozon()
    except Exception:
        pass

h1, h2, h3, h4, h5 = st.columns([2.6, 1, 1, 1.15, 1.1])
with h1:
    st.markdown(
        '<div class="hero"><div class="logo"><span class="a">旅</span><span class="b">ゲーム</span><span class="c">メーカー</span> 全国版</div><div class="subtitle">正確な実地図を使って、全国の旅行プランをゲーム感のある画面で組み立てる</div></div>',
        unsafe_allow_html=True,
    )
with h2:
    st.markdown(
        f'<div class="stat-card"><div class="label">📅 旅行日数</div><div class="value">{len(ryoko_bi())}日</div></div>',
        unsafe_allow_html=True,
    )
with h3:
    st.markdown(
        f'<div class="stat-card"><div class="label">📍 登録地点</div><div class="value">{len(ss.spots)}件</div></div>',
        unsafe_allow_html=True,
    )
with h4:
    st.markdown(
        f'<div class="stat-card"><div class="label">🗺️ 表示地域</div><div class="value">{ss.map_region}</div></div>',
        unsafe_allow_html=True,
    )
with h5:
    st.markdown(
        '<div class="stat-card"><div class="label">🧭 地図</div><div class="value">実地図</div></div>',
        unsafe_allow_html=True,
    )

if ss.page == "旅程":
    left, center, right = st.columns([1, 2.35, 1.35])

    with left:
        st.markdown('<div class="panel"><div class="panel-title">🛠 旅行設定</div>', unsafe_allow_html=True)

        sync_col1, sync_col2 = st.columns([1.4, 1])
        with sync_col1:
            st.success("Mac・スマホ共通データで連動中")
        with sync_col2:
            if st.button(
                "🔄 最新データを取得",
                use_container_width=True,
                key="reload_shared_state",
            ):
                if kyoyu_yomu(force=True):
                    st.success("最新データを読み込みました。")
                else:
                    st.info("共有データは最新です。")
                st.rerun()
        st.date_input(
            "旅行開始日",
            ss.trip_start,
            key="_trip_start_input",
            on_change=ryoko_henko,
        )
        st.number_input(
            "旅行日数",
            1,
            14,
            int(ss.trip_days),
            key="_trip_days_input",
            on_change=ryoko_henko,
        )

        chiiki_list = list(CHIIKI_CHUSHIN)
        ss.map_region = st.selectbox(
            "地図の表示範囲",
            chiiki_list,
            index=chiiki_list.index(ss.map_region),
        )

        if st.button("🔎 場所を検索", type="primary", use_container_width=True, key="button_769_1"):
            gamen_ido("スポット検索")
        if st.button("📍 近くを探す", use_container_width=True, key="button_771_2"):
            gamen_ido("近くを探す")
        if st.button("🧰 便利機能", use_container_width=True, key="button_773_3"):
            gamen_ido("便利機能")

        sentaku_hi = st.selectbox(
            "ルートを表示する日",
            [str(hi) for hi in ryoko_bi()],
            format_func=lambda value: date.fromisoformat(value).strftime("%m月%d日"),
        )
        kaishi_key = f"day_start_{sentaku_hi}"
        st.time_input(
            "その日の開始時間",
            datetime.strptime(kaishi_jikoku(sentaku_hi), "%H:%M").time(),
            key=kaishi_key,
            on_change=kaishi_henko,
            args=(sentaku_hi, kaishi_key),
        )

        modes = ["車", "徒歩", "自転車"]
        ido_key = f"day_mode_{sentaku_hi}"
        st.radio(
            "移動手段",
            modes,
            index=modes.index(ss.day_modes.get(sentaku_hi, "車")),
            horizontal=True,
            key=ido_key,
            on_change=ido_henko,
            args=(sentaku_hi, ido_key),
        )
        sentaku_ido = ss.day_modes.get(sentaku_hi, "車")

        if st.button("🕒 今の順番のまま時刻を再計算", use_container_width=True, key="button_798_4"):
            nittei_saikeisan(sentaku_hi, sentaku_ido, narabikae=False)
            auto_hozon()
            st.success("順番を変えずに、距離・移動時間・到着時刻を再計算しました。")
            st.rerun()

        hi_list = hi_yotei(sentaku_hi)
        if hi_list:
            gokei_fun, gokei_km = hi_gokei(sentaku_hi)
            st.markdown("#### 自動計算結果")
            c1, c2 = st.columns(2)
            c1.metric("合計移動時間", jikan_hyoji(gokei_fun))
            c2.metric("合計距離", f"{gokei_km:.1f}km")
            for item in hi_list:
                if item.get("travel_minutes_from_previous", 0):
                    suffix = "（概算）" if item.get("route_estimated") else ""
                    st.caption(
                        f"{IDO_ICON[sentaku_ido]} {item['name']}："
                        f"前の場所から {jikan_hyoji(item['travel_minutes_from_previous'])} / "
                        f"{item.get('distance_km_from_previous', 0):.1f}km {suffix}"
                    )
        st.markdown("</div>", unsafe_allow_html=True)

    with center:
        st.markdown('<div class="map-wrap">', unsafe_allow_html=True)
        st_folium(
            chizu_tsukuru(sentaku_hi),
            width=None,
            height=400,
            returned_objects=[],
            key=f"main_map_{ss.map_region}_{sentaku_hi}_{sentaku_ido}",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### ✏️ 予定を編集")
        st.caption("距離と時間はOpenStreetMapの道路経路から計算します。直線や海上線では代用しません。")
        st.success("軽量版：滞在時間・開始時間・メモは外部通信なしで即時反映します。")
        st.caption("観光・固定予定・ホテル・レンタカーのすべてで日程を変更できます。")
        eraberu_hi = [str(hi) for hi in ryoko_bi()]

        def render_date_move(item: dict, current_day: str, prefix: str) -> None:
            uid = item["_uid"]
            date_col, button_col = st.columns([2.2, 1.2])
            with date_col:
                ido_saki_hi = st.selectbox(
                    "移動先の日",
                    eraberu_hi,
                    index=eraberu_hi.index(current_day),
                    format_func=lambda value: date.fromisoformat(value).strftime("%m月%d日"),
                    key=f"{prefix}_date_{uid}",
                    label_visibility="collapsed",
                )
            with button_col:
                if st.button(
                    "この日に移動",
                    key=f"{prefix}_move_{uid}",
                    type="primary",
                    use_container_width=True,
                ):
                    changed, message = yotei_hi_ido(uid, ido_saki_hi)
                    if changed:
                        st.success(message)
                        st.rerun()
                    else:
                        st.info(message)

        for hi in ryoko_bi():
            hi_moji = str(hi)
            shuppatsu, rental_uke, kanko_list, hotels, rental_hen = henshu_bunrui(hi_moji)

            with st.expander(hi.strftime("%m月%d日") + "の予定", expanded=False):
                if not (shuppatsu or rental_uke or kanko_list or hotels or rental_hen):
                    st.info("予定なし")
                    continue

                if shuppatsu:
                    saisho_yotei = (rental_uke + kanko_list + hotels + rental_hen)
                    saisho_yotei = saisho_yotei[0] if saisho_yotei else None
                    st.markdown("#### 🏨 前泊ホテルから出発")
                    st.markdown(
                        f"**{shuppatsu['name']}**　"
                        f"{kaishi_jikoku(hi_moji)}出発"
                    )
                    if saisho_yotei:
                        st.info(
                            f"次の目的地「{saisho_yotei['name']}」まで "
                            f"{jikan_hyoji(saisho_yotei.get('travel_minutes_from_previous', 0))}・"
                            f"{saisho_yotei.get('distance_km_from_previous', 0):.1f}km"
                        )

                if rental_uke:
                    st.markdown("#### 🚗 レンタカー受取")
                    for item in rental_uke:
                        st.markdown(
                            f"**{item['name']}**　"
                            f"{item.get('arrival', item.get('start','--:--'))}着 → "
                            f"{item.get('departure','--:--')}発"
                        )
                        render_date_move(item, hi_moji, "rental_start")
                        st.divider()

                if kanko_list:
                    st.markdown("#### 📍 観光・食事・その他の予定")

                for index, item in enumerate(kanko_list):
                    uid = item["_uid"]
                    st.markdown(
                        f"**{index + 1}. {item['name']}**　"
                        f"{item.get('arrival', item.get('start','--:--'))}着 → "
                        f"{item.get('departure','--:--')}発"
                    )

                    if item.get("travel_minutes_from_previous", 0):
                        st.caption(
                            f"前の地点から "
                            f"{jikan_hyoji(item.get('travel_minutes_from_previous', 0))}・"
                            f"{item.get('distance_km_from_previous', 0):.1f}km"
                        )

                    order_up, order_down, map_col, delete_col = st.columns(4)

                    with order_up:
                        if st.button(
                            "↑ 上へ",
                            key=f"up_{uid}",
                            disabled=index == 0,
                            use_container_width=True,
                        ):
                            kanko_jun_ido(hi_moji, uid, -1)
                            nittei_saikeisan(
                                hi_moji,
                                ss.day_modes.get(hi_moji, "車"),
                            )
                            auto_hozon()
                            st.rerun()

                    with order_down:
                        if st.button(
                            "↓ 下へ",
                            key=f"down_{uid}",
                            disabled=index == len(kanko_list) - 1,
                            use_container_width=True,
                        ):
                            kanko_jun_ido(hi_moji, uid, 1)
                            nittei_saikeisan(
                                hi_moji,
                                ss.day_modes.get(hi_moji, "車"),
                            )
                            auto_hozon()
                            st.rerun()

                    with map_col:
                        st.link_button(
                            "地図",
                            item.get("map_url") or gmap_url(item),
                            use_container_width=True,
                        )

                    with delete_col:
                        if st.button(
                            "削除",
                            key=f"del_{uid}",
                            use_container_width=True,
                        ):
                            deleted, _ = yotei_sakujo(uid)
                            if deleted:
                                st.success("予定を削除しました。")
                            st.rerun()

                    render_date_move(item, hi_moji, "other")

                    detail1, detail2 = st.columns(2)
                    stay_key = f"stay_{uid}"
                    memo_key = f"memo_{uid}"

                    with detail1:
                        st.number_input(
                            "滞在時間（分）",
                            10,
                            600,
                            int(item.get("stay", 60)),
                            10,
                            key=stay_key,
                            on_change=basho_henko,
                            args=(uid, "stay", stay_key, hi_moji, True),
                        )

                    with detail2:
                        st.text_input(
                            "メモ",
                            item.get("memo", ""),
                            key=memo_key,
                            on_change=basho_henko,
                            args=(uid, "memo", memo_key, hi_moji, False),
                        )

                    st.divider()

                if hotels:
                    st.markdown("#### 🏨 宿泊ホテル")

                for item in hotels:
                    uid = item["_uid"]
                    st.markdown(
                        f"**{item['name']}**　"
                        f"{item.get('arrival', item.get('start','--:--'))}到着"
                    )
                    if item.get("travel_minutes_from_previous", 0):
                        st.caption(
                            f"前の地点から "
                            f"{jikan_hyoji(item.get('travel_minutes_from_previous', 0))}・"
                            f"{item.get('distance_km_from_previous', 0):.1f}km"
                        )

                    render_date_move(item, hi_moji, "hotel")

                    if st.button(
                        "日程から外す",
                        key=f"remove_hotel_{uid}",
                        use_container_width=True,
                    ):
                        yotei_sakujo(uid)
                        st.success("ホテルを日程から外しました。")
                        st.rerun()

                    st.divider()

                if rental_hen:
                    st.markdown("#### 🚗 レンタカー返却")

                for item in rental_hen:
                    st.markdown(
                        f"**{item['name']}**　"
                        f"{item.get('arrival', item.get('start','--:--'))}着"
                    )
                    if item.get("travel_minutes_from_previous", 0):
                        st.caption(
                            f"前の地点から "
                            f"{jikan_hyoji(item.get('travel_minutes_from_previous', 0))}・"
                            f"{item.get('distance_km_from_previous', 0):.1f}km"
                        )
                    render_date_move(item, hi_moji, "rental_return")
                    st.divider()

    with right:
        st.markdown('<div class="panel"><div class="panel-title">📖 旅のしおり</div>', unsafe_allow_html=True)
        for index, hi in enumerate(ryoko_bi(), start=1):
            items = hi_hyoji(str(hi))
            rows = "".join(
                (
                    f'<div class="timeline-row">'
                    f'<div class="time">{item.get("arrival", item.get("start", "--:--"))}</div>'
                    f'<div>{KUBUN_ICON.get(item.get("category"), "📍")} '
                    f'{"【レンタカー】" if rental_ka(item) else ("【ホテル】" if hotel_ka(item) else "")} '
                    f'{item["name"]}'
                    f'<br><span style="font-size:.75rem;color:#6f7e86;">'
                    f'{keiro_bun(item)}'
                    f'</span></div>'
                    f'<div class="badge">{item.get("departure", "--:--")}発</div>'
                    f'</div>'
                )
                for item in items
            ) or (
                '<div class="timeline-row">'
                '<div>-</div><div>予定なし</div>'
                '<div class="badge">自由</div></div>'
            )

            css_class = "orange" if index % 3 == 2 else ("blue" if index % 3 == 0 else "")
            ido = ss.day_modes.get(str(hi), "車")
            st.markdown(
                f'<div class="day-card"><div class="day-head {css_class}">DAY {index}｜{hi.strftime("%m/%d")} {IDO_ICON[ido]} {ido}</div><div class="timeline">{rows}</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

elif ss.page == "スポット検索":
    left, center, right = st.columns([1, 2.2, 1.35])

    with left:
        st.markdown('<div class="panel"><div class="panel-title">🔎 全国の場所を検索</div>', unsafe_allow_html=True)
        query = st.text_input("施設名・住所・地域", placeholder="沖縄美ら海水族館 / 金閣寺 / 札幌時計台")
        add_day = st.selectbox("追加する日", [str(hi) for hi in ryoko_bi()])
        add_stay = st.number_input("滞在分", 10, 600, 60, 10)
        add_category = st.selectbox("分類", list(KUBUN_JOKEN), index=2)

        if st.button("検索する", type="primary", use_container_width=True, key="button_919_5"):
            if query.strip():
                with st.spinner("全国から検索中…"):
                    ss.search_results = basho_kensaku(query)
                if ss.search_results:
                    first = ss.search_results[0]
                    ss.map_region = chiiki_hantei(first["lat"], first["lon"])
                    st.rerun()

        if st.button("← 旅程へ戻る", use_container_width=True, key="button_928_6"):
            gamen_ido("旅程")
        st.markdown("</div>", unsafe_allow_html=True)

    with center:
        temp_map = folium.Map(
            location=CHIIKI_CHUSHIN[ss.map_region][:2],
            zoom_start=CHIIKI_CHUSHIN[ss.map_region][2],
            control_scale=True,
        )
        for result in ss.search_results:
            folium.Marker(
                [result["lat"], result["lon"]],
                tooltip=result["name"],
                popup=result["address"],
                icon=folium.Icon(color="green", icon="search"),
            ).add_to(temp_map)
        if ss.search_results:
            temp_map.fit_bounds([
                [min(x["lat"] for x in ss.search_results), min(x["lon"] for x in ss.search_results)],
                [max(x["lat"] for x in ss.search_results), max(x["lon"] for x in ss.search_results)],
            ], padding=(35, 35))

        st.markdown('<div class="map-wrap">', unsafe_allow_html=True)
        st_folium(temp_map, width=None, height=720, returned_objects=[], key="search_map")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel"><div class="panel-title">検索結果</div>', unsafe_allow_html=True)
        for index, result in enumerate(ss.search_results):
            region = chiiki_hantei(result["lat"], result["lon"])
            st.markdown(
                f'<div class="spot-card"><div class="spot-title">{result["name"]}</div><div class="spot-meta">{region}｜{result["address"]}</div></div>',
                unsafe_allow_html=True,
            )
            a, b = st.columns(2)
            a.link_button("地図で確認", gmap_url(result), use_container_width=True)
            if b.button("日程に追加", key=f"search_add_{index}", use_container_width=True):
                basho_tsuika(result, add_day, kaishi_jikoku(add_day), add_stay, add_category)
                st.success("追加しました")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif ss.page == "近くを探す":
    left, center, right = st.columns([1, 2.2, 1.35])

    with left:
        st.markdown('<div class="panel"><div class="panel-title">📍 登録地点の近くを検索</div>', unsafe_allow_html=True)
        if ss.spots:
            names = [
                f'{basho["name"]}（{chiiki_hantei(basho["lat"], basho["lon"])}）'
                for basho in ss.spots
            ]
            base_index = st.selectbox("基準地点", range(len(names)), format_func=lambda i: names[i])
            base = ss.spots[base_index]
            ss.map_region = chiiki_hantei(base["lat"], base["lon"])

            kubun = st.selectbox("ジャンル", list(KUBUN_JOKEN))
            radius = st.slider("範囲", 500, 10000, 3000, 500)
            add_day = st.selectbox("追加日", [str(hi) for hi in ryoko_bi()])

            if st.button("近くを検索", type="primary", use_container_width=True, key="button_989_7"):
                with st.spinner("周辺検索中…"):
                    result = shuhen_kensaku(base["lat"], base["lon"], kubun, radius)
                    for item in result:
                        item["distance"] = chokusen_km(base, item)
                    ss.nearby_results = sorted(result, key=lambda x: x["distance"])[:20]

        if st.button("← 旅程へ戻る", use_container_width=True, key="button_996_8"):
            gamen_ido("旅程")
        st.markdown("</div>", unsafe_allow_html=True)

    with center:
        near_map = folium.Map(location=[base["lat"], base["lon"]], zoom_start=13, control_scale=True)
        folium.Marker(
            [base["lat"], base["lon"]],
            tooltip=f"基準地点：{base['name']}",
            icon=folium.Icon(color="red", icon="flag"),
        ).add_to(near_map)
        for item in ss.nearby_results:
            folium.Marker(
                [item["lat"], item["lon"]],
                tooltip=f"{item['name']}｜約{item['distance']:.1f}km",
                icon=folium.Icon(color="green", icon="info-sign"),
            ).add_to(near_map)

        st.markdown('<div class="map-wrap">', unsafe_allow_html=True)
        st_folium(near_map, width=None, height=720, returned_objects=[], key="nearby_map")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel"><div class="panel-title">周辺候補</div>', unsafe_allow_html=True)
        for index, item in enumerate(ss.nearby_results):
            st.markdown(
                f'<div class="spot-card"><div class="spot-title">{KUBUN_ICON.get(item.get("category"),"📍")} {item["name"]}</div><div class="spot-meta">約{item["distance"]:.1f}km｜{item.get("address","")}</div></div>',
                unsafe_allow_html=True,
            )
            a, b = st.columns(2)
            a.link_button("地図で確認", gmap_url(item), use_container_width=True)
            if b.button("日程に追加", key=f"near_add_{index}", use_container_width=True):
                basho_tsuika(item, add_day, kaishi_jikoku(add_day), 60, item.get("category", "観光スポット"))
                st.success("追加しました")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


elif ss.page == "便利機能":
    left, center, right = st.columns([1.05, 2.15, 1.35])

    with left:
        st.markdown('<div class="panel"><div class="panel-title">🧰 便利機能</div>', unsafe_allow_html=True)
        tool = st.radio(
            "使う機能",
            ["GoogleマップURL登録", "ホテル順", "自動旅程", "スマホ接続"],
        )
        if st.button("← 旅程へ戻る", use_container_width=True, key="button_1043_9"):
            gamen_ido("旅程")
        st.markdown("</div>", unsafe_allow_html=True)

    with center:
        if tool == "GoogleマップURL登録":
            st.markdown('<div class="panel"><div class="panel-title">🔗 GoogleマップURL一括登録</div>', unsafe_allow_html=True)
            raw_urls = st.text_area(
                "1行1URL。『場所名 | URL』にも対応",
                height=220,
                placeholder="ロワジールホテル那覇 | https://www.google.com/maps/place/...",
            )
            kubun = st.selectbox("登録時の分類", ["自動判定"] + list(KUBUN_JOKEN), index=0, key="url_category")
            if st.button("URLを読み取って登録", type="primary", use_container_width=True, key="button_1056_10"):
                results = []
                for parsed in map_url_gyo(raw_urls):
                    if not parsed.get("ok"):
                        results.append({"状態": "失敗", "場所名": "", "理由": parsed.get("reason", "")})
                        continue
                    try:
                        resolved = map_url_kakunin(parsed["url"], parsed.get("name_override", ""))
                        hantei_kubun = resolved.get("category") or kubun
                        if kubun != "自動判定":
                            hantei_kubun = kubun
                        shoki = KUBUN_SHOKI.get(
                            hantei_kubun,
                            KUBUN_SHOKI["観光スポット"],
                        )
                        record = {
                            "_uid": uuid.uuid4().hex,
                            **resolved,
                            "category": hantei_kubun,
                            "cost": shoki["cost"],
                            "open": shoki["open"],
                            "close": shoki["close"],
                            "indoor": shoki["indoor"],
                            "priority": shoki["priority"],
                            "must_visit": False,
                        }
                        duplicate = any(
                            abs(float(x["lat"]) - record["lat"]) < 0.00002
                            and abs(float(x["lon"]) - record["lon"]) < 0.00002
                            for x in ss.registered_places
                        )
                        if duplicate:
                            results.append({"状態": "重複", "場所名": record["name"], "理由": "すでに登録済み"})
                        else:
                            ss.registered_places.append(record)
                            results.append({"状態": "登録完了", "場所名": record["name"], "理由": f'{record["category"]}として登録 / 座標取得済み'})
                    except Exception as exc:
                        results.append({"状態": "失敗", "場所名": parsed.get("name_override", ""), "理由": str(exc)})
                ss.url_import_results = results
                toroku_hozon()
                st.rerun()

            if ss.url_import_results:
                st.dataframe(ss.url_import_results, use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="panel"><div class="panel-title">登録済み候補</div>', unsafe_allow_html=True)
            for index, place in enumerate(ss.registered_places):
                st.markdown(
                    f'<div class="spot-card"><div class="spot-title">{place["name"]}</div>'
                    f'<div class="spot-meta">{chiiki_hantei(place["lat"],place["lon"])}｜'
                    f'{place.get("category","観光スポット")}｜{place["lat"]:.5f},{place["lon"]:.5f}</div></div>',
                    unsafe_allow_html=True,
                )
                a, b, c = st.columns(3)
                a.link_button("Googleマップ", place.get("map_url") or gmap_url(place), use_container_width=True)
                if b.button("日程へ追加", key=f"registered_add_{index}", use_container_width=True):
                    ima_hibi = ryoko_bi()
                    basho_tsuika(
                        place,
                        str(ima_hibi[0]),
                        kaishi_jikoku(str(ima_hibi[0])),
                        30 if place.get("category") == "ホテル" else 60,
                        place.get("category", "観光スポット"),
                    )
                    auto_hozon()
                    st.success("初日に追加しました。旅程画面で日付と時刻を変更できます。")
                if c.button("候補を削除", key=f"registered_delete_{index}", use_container_width=True):
                    toroku_kesu(place["_uid"])
                    st.success("候補一覧から削除しました。")
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        elif tool == "ホテル順":
            st.markdown('<div class="panel"><div class="panel-title">🏨 泊ごとのホテル設定</div>', unsafe_allow_html=True)

            candidates = hotel_koho()
            ima_hibi = ryoko_bi()
            nights = max(0, len(ima_hibi) - 1)

            st.caption(
                "ホテル候補を先に登録してから、1泊目・2泊目ごとに1軒ずつ選びます。"
                "『未設定』を選んだ泊にはホテルを入れません。"
            )

            if nights == 0:
                st.info("日帰り旅行のため、宿泊ホテルの設定はありません。")
            elif not candidates:
                st.info("ホテル候補がありません。GoogleマップURL登録でホテルを追加してください。")
            else:
                hi_hotel_now = {
                    str(basho.get("day")): basho
                    for basho in nittei_hotel()
                    if basho.get("day")
                }
                erabu_id = [None] + [hotel["_uid"] for hotel in candidates]
                mei_map = {None: "未設定"}
                mei_map.update({hotel["_uid"]: hotel["name"] for hotel in candidates})

                sentaku_hotel_id = []
                for haku in range(nights):
                    stay_day = str(ima_hibi[haku])
                    current = hi_hotel_now.get(stay_day)
                    ima_id = current.get("source_candidate_uid") if current else None

                    # 旧データでは候補UIDが無いので、名前と座標から候補を照合する。
                    if current and ima_id not in erabu_id:
                        matched = next(
                            (
                                candidate for candidate in candidates
                                if candidate.get("name") == current.get("name")
                                and abs(float(candidate.get("lat", 0)) - float(current.get("lat", 0))) < 0.0001
                                and abs(float(candidate.get("lon", 0)) - float(current.get("lon", 0))) < 0.0001
                            ),
                            None,
                        )
                        ima_id = matched.get("_uid") if matched else None

                    default_index = erabu_id.index(ima_id) if ima_id in erabu_id else 0
                    selected = st.selectbox(
                        f"{haku + 1}泊目｜{ima_hibi[haku].strftime('%m月%d日')}",
                        erabu_id,
                        index=default_index,
                        format_func=lambda value, labels=mei_map: labels.get(value, "未設定"),
                        key=f"night_hotel_select_{haku}",
                    )
                    sentaku_hotel_id.append(selected)

                apply_col, clear_col = st.columns(2)
                with apply_col:
                    if st.button(
                        "このホテル設定を確定",
                        type="primary",
                        key="apply_hotel_plan",
                        use_container_width=True,
                    ):
                        hotel_wariate(sentaku_hotel_id)
                        st.success("泊ごとのホテル設定を更新しました。")
                        st.rerun()

                with clear_col:
                    if st.button(
                        "全泊を未設定に戻す",
                        key="clear_all_hotel_plan",
                        use_container_width=True,
                    ):
                        hotel_wariate([None] * nights)
                        for haku in range(nights):
                            ss.pop(f"night_hotel_select_{haku}", None)
                        st.success("日程からすべてのホテルを外しました。候補一覧は残っています。")
                        st.rerun()

            st.divider()
            st.markdown("### 登録済みホテル候補")
            st.caption("候補を削除しても、すでに日程へ設定済みのホテルは確定操作までは残ります。")

            if not candidates:
                st.caption("ホテル候補はありません。")
            else:
                for hotel in candidates:
                    uid = hotel["_uid"]
                    st.markdown(
                        f'<div class="spot-card"><div class="spot-title">🏨 {hotel["name"]}</div>'
                        f'<div class="spot-meta">{hotel.get("address", "")}</div></div>',
                        unsafe_allow_html=True,
                    )
                    map_col, delete_col = st.columns(2)
                    with map_col:
                        st.link_button(
                            "Googleマップ",
                            hotel.get("map_url") or gmap_url(hotel),
                            use_container_width=True,
                        )
                    with delete_col:
                        if st.button(
                            "候補から削除",
                            key=f"delete_hotel_candidate_{uid}",
                            use_container_width=True,
                        ):
                            toroku_kesu(uid)
                            st.rerun()

            st.divider()
            st.markdown("### 現在の日程ホテル")
            scheduled = sorted(
                nittei_hotel(),
                key=lambda item: str(item.get("day", "")),
            )
            if not scheduled:
                st.info("日程にホテルは入っていません。")
            else:
                for hotel in scheduled:
                    st.write(
                        f'**{hotel.get("memo", "宿泊")}｜{hotel.get("day", "")}**　{hotel["name"]}'
                    )

            st.markdown("</div>", unsafe_allow_html=True)

        elif tool == "自動旅程":
            st.markdown('<div class="panel"><div class="panel-title">✨ 自動旅程調整</div>', unsafe_allow_html=True)
            st.write("現在の並び順を固定したまま、各日の距離・移動時間・到着時刻・出発時刻を再計算します。")
            if st.button("全日程の時刻だけ再計算", type="primary", use_container_width=True, key="button_1139_12"):
                zenbi_saikeisan(narabikae=False)
                auto_hozon()
                st.success("順番を変えずに全日程を再計算しました。")
                st.rerun()
            st.warning("営業時間や予約時刻は完全自動ではないため、調整後に確認してください。")
            st.markdown("</div>", unsafe_allow_html=True)

        else:
            st.markdown('<div class="panel"><div class="panel-title">📱 スマホで開く</div>', unsafe_allow_html=True)
            lan_ip = lan_ip()
            if lan_ip:
                sumaho_url = f"http://{lan_ip}:8501"
                st.write(f"同じWi-Fiのスマホで開くURL：`{sumaho_url}`")
                st.image(qr_png(sumaho_url), width=230)
            else:
                st.warning("MacのWi-Fi内IPを取得できませんでした。")
            st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel"><div class="panel-title">📊 旅行情報</div>', unsafe_allow_html=True)
        gokei_kingaku = sum(int(basho.get("cost", 0)) for basho in ss.spots)
        kanarazu_kensu = sum(bool(basho.get("must_visit")) for basho in ss.spots)
        hotel_kensu = sum(basho.get("category") == "ホテル" for basho in ss.spots)
        st.metric("予算目安合計", f"{gokei_kingaku:,}円")
        st.metric("必須スポット", f"{kanarazu_kensu}件")
        st.metric("ホテル候補", f"{hotel_kensu}件")
        st.metric("URL登録候補", f"{len(ss.registered_places)}件")
        st.markdown("</div>", unsafe_allow_html=True)


st.markdown("### 💾 保存・読み込み")
save_col, load_col = st.columns([1, 1.4])

with save_col:
    payload = {
        "version": 5,
        "trip_start": str(ss.trip_start),
        "trip_days": int(ss.trip_days),
        "spots": ss.spots,
        "day_modes": ss.day_modes,
        "map_region": ss.map_region,
        "day_start_times": ss.day_start_times,
        "registered_places": ss.registered_places,
    }
    st.download_button(
        "旅行データを保存",
        json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name="tabigame_japan_realmap_data.json",
        mime="application/json",
        use_container_width=True,
    )

with load_col:
    uploaded = st.file_uploader(
        "保存データを読み込む",
        type=["json"],
        key="saved_trip_file_uploader",
    )

    if uploaded is not None:
        st.caption("ファイルを選んだだけでは上書きしません。「このデータを読み込む」を押した時だけ反映します。")

    if st.button(
        "このデータを読み込む",
        type="primary",
        use_container_width=True,
        disabled=uploaded is None,
        key="load_saved_trip_button",
    ):
        try:
            uploaded.seek(0)
            loaded = json.load(uploaded)

            if isinstance(loaded, dict) and "spots" in loaded:
                ss.spots = loaded["spots"]
                ss.trip_start = date.fromisoformat(
                    loaded.get("trip_start", "2026-07-17")
                )
                ss.trip_days = int(loaded.get("trip_days", 4))
                ss.day_modes = loaded.get("day_modes", {})
                ss.map_region = loaded.get(
                    "map_region",
                    loaded.get("selected_region", "沖縄"),
                )
                ss.registered_places = loaded.get(
                    "registered_places",
                    ss.registered_places,
                )
                ss.day_start_times = loaded.get(
                    "day_start_times",
                    ss.day_start_times,
                )
                toroku_hozon()

            elif isinstance(loaded, list):
                ss.spots = loaded
            else:
                raise ValueError("未対応の保存形式です")

            id_seiri()

            for _spot in ss.spots:
                basho_hosoku(_spot)
                _spot.pop("route_error", None)
                _spot.pop("route_source", None)
                _spot.pop("route_estimated", None)
                _spot.pop("route_coords", None)

            hotel_jufuku()

            try:
                keiro_shutoku.clear()
            except Exception:
                pass

            zenbi_saikeisan(narabikae=False)
            ss["_schedule_initialized"] = True
            auto_hozon()
            st.success("保存データを読み込み、Mac・スマホ共通データへ反映しました。")
            st.rerun()

        except Exception as exc:
            st.error(f"読み込み失敗: {exc}")

st.markdown('<div class="navbar">', unsafe_allow_html=True)
n1, n2, n3, n4 = st.columns(4)
with n1:
    if st.button("🗓️ 旅程", use_container_width=True, key="button_1225_13"):
        gamen_ido("旅程")
with n2:
    if st.button("🔎 全国検索", use_container_width=True, key="button_1228_14"):
        gamen_ido("スポット検索")
with n3:
    if st.button("📍 近くを探す", use_container_width=True, key="button_1231_15"):
        gamen_ido("近くを探す")
with n4:
    if st.button("🧰 便利機能", use_container_width=True, key="button_1234_16"):
        gamen_ido("便利機能")
st.markdown("</div>", unsafe_allow_html=True)

st.caption("地図: OpenStreetMap / 経路: OSRM / 周辺検索: Overpass。Googleマップのリンクで最終確認できます。")
