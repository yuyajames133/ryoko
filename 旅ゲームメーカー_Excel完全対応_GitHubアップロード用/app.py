
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
import pandas as pd
from folium.plugins import AntPath, MarkerCluster
from streamlit_folium import st_folium

st.set_page_config(page_title="旅ゲームメーカー 全国版", page_icon="🗾", layout="wide")


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;500;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'M PLUS Rounded 1c', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 8% 10%, rgba(255,255,255,.92), transparent 24%),
        linear-gradient(180deg, #c9f1ff 0%, #edfaff 48%, #fff6ea 100%);
}

.block-container {
    max-width: 1500px;
    padding-top: 1rem;
    padding-bottom: 5.5rem;
}

header[data-testid="stHeader"] {
    background: transparent;
}

#MainMenu, footer {
    visibility: hidden;
}

.hero {
    background: rgba(255,255,255,.97);
    border: 2px solid #fff;
    border-radius: 28px;
    padding: 18px 24px;
    box-shadow: 0 12px 30px rgba(39,96,130,.14);
    margin-bottom: 14px;
}

.logo {
    font-size: 2.25rem;
    font-weight: 800;
    letter-spacing: .01em;
}

.logo .a { color: #ff5671; }
.logo .b { color: #1e9be6; }
.logo .c { color: #ffa31b; }

.subtitle {
    color: #55717f;
    font-weight: 700;
    margin-top: 4px;
}

.stat-card {
    background: #fffdf8;
    border: 1px solid #eadfce;
    border-radius: 18px;
    padding: 14px;
    min-height: 82px;
    box-shadow: 0 6px 14px rgba(70,75,60,.08);
}

.stat-card .label {
    font-size: .82rem;
    color: #6c7880;
    font-weight: 700;
}

.stat-card .value {
    font-size: 1.16rem;
    color: #2d3d48;
    font-weight: 800;
    margin-top: 6px;
}

.panel {
    background: rgba(255,255,255,.97);
    border: 1px solid #e8ddd0;
    border-radius: 24px;
    padding: 16px;
    box-shadow: 0 12px 26px rgba(32,90,117,.12);
    margin-bottom: 12px;
}

.panel-title {
    font-size: 1.15rem;
    font-weight: 800;
    color: #28404d;
    margin-bottom: 10px;
}

.map-wrap {
    background: #fff;
    border-radius: 28px;
    padding: 10px;
    box-shadow: 0 14px 30px rgba(37,91,120,.20);
    border: 4px solid rgba(255,255,255,.95);
    overflow: hidden;
}

.day-card {
    background: #fff;
    border: 1px solid #ecdcca;
    border-radius: 18px;
    overflow: hidden;
    margin-bottom: 11px;
}

.day-head {
    color: #fff;
    padding: 10px 14px;
    font-weight: 800;
    background: linear-gradient(90deg,#ff6077,#ff8f9d);
}

.day-head.orange {
    background: linear-gradient(90deg,#ff9f2f,#ffc156);
}

.day-head.blue {
    background: linear-gradient(90deg,#4ca9ff,#68c6ff);
}

.timeline {
    padding: 12px 14px;
}

.timeline-row {
    display: grid;
    grid-template-columns: 58px minmax(0,1fr) auto;
    gap: 10px;
    padding: 8px 0;
    border-bottom: 1px dashed #eadfda;
    font-size: .89rem;
    align-items: start;
}

.timeline-row:last-child {
    border-bottom: none;
}

.time {
    font-weight: 800;
    color: #52616a;
}

.badge {
    background: #edf7f1;
    color: #3e8c65;
    padding: 3px 8px;
    border-radius: 9px;
    font-size: .72rem;
    font-weight: 800;
    white-space: nowrap;
}

.spot-card {
    background: #fff;
    border: 1px solid #eadfd4;
    border-radius: 20px;
    padding: 13px;
    margin-bottom: 12px;
    box-shadow: 0 5px 14px rgba(53,83,99,.08);
}

.spot-title {
    font-weight: 800;
    color: #263e4b;
}

.spot-meta {
    font-size: .82rem;
    color: #6f7e86;
    margin-top: 3px;
}

.fixedtag {
    display: inline-block;
    background: #ffe4e8;
    color: #d83f5c;
    border-radius: 10px;
    padding: 2px 7px;
    font-size: .73rem;
    font-weight: 800;
}

.freetag {
    display: inline-block;
    background: #e8f5ee;
    color: #2b8a57;
    border-radius: 10px;
    padding: 2px 7px;
    font-size: .73rem;
    font-weight: 800;
}

.navbar {
    position: sticky;
    bottom: 10px;
    z-index: 10;
    background: rgba(255,255,255,.95);
    border: 1px solid #eadfce;
    padding: 10px;
    border-radius: 22px;
    box-shadow: 0 10px 26px rgba(34,72,94,.18);
    backdrop-filter: blur(10px);
}

div.stButton > button,
div.stDownloadButton > button,
div.stLinkButton > a {
    border-radius: 16px !important;
    font-weight: 800 !important;
    min-height: 42px;
}

div.stButton > button[kind="primary"] {
    background: linear-gradient(90deg,#ff4f6d,#ff7a8f);
    border: none;
}

div[data-testid="stMetric"] {
    background: #fffdf8;
    border: 1px solid #eadfce;
    border-radius: 16px;
    padding: 10px 12px;
}

div[data-testid="stExpander"] {
    background: rgba(255,255,255,.92);
    border: 1px solid #e6ddd3;
    border-radius: 16px;
    overflow: hidden;
}

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div {
    border-radius: 14px;
}

iframe {
    border-radius: 20px !important;
}

@media (max-width: 900px) {
    .block-container {
        max-width: 100%;
        padding: .6rem .7rem 5.5rem;
    }

    .hero {
        padding: 14px 16px;
        border-radius: 20px;
    }

    .logo {
        font-size: 1.5rem;
    }

    .subtitle {
        font-size: .86rem;
        line-height: 1.45;
    }

    .stat-card {
        min-height: 68px;
        padding: 10px;
    }

    .panel {
        border-radius: 18px;
        padding: 12px;
    }

    .map-wrap {
        border-radius: 20px;
        padding: 6px;
    }

    div[data-testid="stHorizontalBlock"] {
        flex-wrap: wrap;
        gap: .5rem;
    }

    div[data-testid="column"] {
        min-width: min(100%, 260px);
        flex: 1 1 260px;
    }

    .timeline-row {
        grid-template-columns: 48px minmax(0,1fr) auto;
        gap: 6px;
        font-size: .8rem;
    }

    iframe {
        min-height: 520px !important;
    }
}
</style>
""", unsafe_allow_html=True)





NOMINATIM = "https://nominatim.openstreetmap.org/search"
OVERPASS = "https://overpass-api.de/api/interpreter"
OSRM = "https://router.project-osrm.org"
UA = "tabigame-japan-realmap-integrated/2.0"
AUTO_BACKUP_FILE = Path(__file__).with_name("trip_backup_latest.json")
REGISTERED_PLACES_FILE = Path(__file__).with_name("registered_places.json")

CATEGORIES = {
    "カフェ": ['["amenity"="cafe"]'],
    "ランチ・レストラン": ['["amenity"="restaurant"]'],
    "観光スポット": ['["tourism"="attraction"]', '["tourism"="museum"]', '["historic"]'],
    "ビーチ": ['["natural"="beach"]'],
    "ホテル": ['["tourism"="hotel"]'],
    "コンビニ": ['["shop"="convenience"]'],
    "スーパー": ['["shop"="supermarket"]'],
    "温泉・スパ": ['["amenity"="public_bath"]', '["leisure"="spa"]'],
}
ICON_BY_CAT = {
    "カフェ": "☕", "ランチ・レストラン": "🍽️", "観光スポット": "📍",
    "ビーチ": "🏖️", "ホテル": "🏨", "コンビニ": "🏪",
    "スーパー": "🛒", "温泉・スパ": "♨️", "固定予定": "🧷", "レンタカー": "🚗",
}
MODE_PROFILE = {"車": "driving", "徒歩": "foot", "自転車": "bike"}
MODE_EMOJI = {"車": "🚗", "徒歩": "🚶", "自転車": "🚲"}


CATEGORY_META_DEFAULTS = {
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

REGION_CENTERS = {
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

REGION_BOUNDS = {
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

def region_for(lat: float, lon: float) -> str:
    for name, ((lat0, lon0), (lat1, lon1)) in REGION_BOUNDS.items():
        if lat0 <= lat <= lat1 and lon0 <= lon <= lon1:
            return name
    if lat < 30:
        return "沖縄"
    if lat > 40:
        return "北海道"
    if lon < 133:
        return "九州"
    return "関東"

def init_state() -> None:
    defaults = {
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
        "budget_settings": {
            "hotel_paid": True,
            "rental_paid": True,
            "flight_paid": True,
            "unregistered_meals": 22000,
            "gasoline": 5000,
            "tolls": 2000,
            "parking": 3000,
            "convenience_snacks": 6000,
            "souvenirs": 15000,
            "contingency": 10000,
        },
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if not st.session_state.spots:
        st.session_state.spots = [
            {
                "_uid": uuid.uuid4().hex,
                "name": "ABCレンタカー那覇空港営業所",
                "address": "沖縄県那覇市周辺",
                "lat": 26.1905,
                "lon": 127.6555,
                "day": "2026-07-17",
                "start": "10:00",
                "stay": 45,
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
                "stay": 30,
                "fixed": True,
                "memo": "16:00までに返却",
                "category": "レンタカー",
            },
        ]

init_state()


def spot_defaults(spot: dict) -> dict:
    category = spot.get("category", "観光スポット")
    defaults = CATEGORY_META_DEFAULTS.get(category, CATEGORY_META_DEFAULTS["観光スポット"])
    spot.setdefault("_uid", uuid.uuid4().hex)
    spot.setdefault("address", "")
    spot.setdefault("fixed", False)
    spot.setdefault("memo", "")
    spot.setdefault("category", category)
    spot.setdefault("cost", int(defaults["cost"]))
    spot.setdefault("open", str(defaults["open"]))
    spot.setdefault("close", str(defaults["close"]))
    spot.setdefault("indoor", bool(defaults["indoor"]))
    spot.setdefault("priority", int(defaults["priority"]))
    spot.setdefault("must_visit", False)
    spot.setdefault("map_url", "")
    spot.setdefault("manual_order", 9999)
    return spot

for _spot in st.session_state.spots:
    spot_defaults(_spot)

def get_lan_ip() -> str:
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

def qr_png_bytes(value: str) -> bytes:
    image = qrcode.make(value)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()

def parse_google_map_lines(raw_text: str) -> list[dict]:
    results = []
    seen = set()
    for raw_line in str(raw_text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = re.search(r"https?://[^\\s<>\\\"]+", line)
        if not match:
            results.append({"ok": False, "reason": "URLが見つかりません", "original": raw_line})
            continue
        url = match.group(0).rstrip("),。、]")
        if url in seen:
            results.append({"ok": False, "reason": "同じURLが重複しています", "url": url})
            continue
        seen.add(url)
        before = re.sub(r"[\\s|｜:：\\t]+$", "", line[:match.start()].strip())
        results.append({"ok": True, "url": url, "name_override": before[:100]})
    return results


def clean_google_name(value: str) -> str:
    value = html.unescape(urlparse.unquote_plus(str(value or ""))).strip()
    value = re.sub(r"\s*[-–—]\s*Google\s*Maps.*$", "", value, flags=re.I)
    value = re.sub(r"\s*·\s*Google.*$", "", value, flags=re.I)
    value = re.sub(r"\s+", " ", value).strip(" /|-")
    return value

def extract_meta_content(page_html: str, key: str) -> str:
    patterns = [
        rf'<meta[^>]+property=["\']{re.escape(key)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{re.escape(key)}["\']',
        rf'<meta[^>]+name=["\']{re.escape(key)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']{re.escape(key)}["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, page_html, flags=re.I)
        if match:
            return html.unescape(match.group(1)).strip()
    return ""

def extract_canonical_url(page_html: str) -> str:
    patterns = [
        r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
        r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']',
        r'<meta[^>]+property=["\']og:url["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:url["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, page_html, flags=re.I)
        if match:
            return html.unescape(match.group(1)).strip()
    return ""

def exact_coords_from_google_url(value: str):
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

def infer_category_from_name(name: str, address: str = "") -> str:
    target = f"{name} {address}".lower()

    hotel_words = [
        "hotel", "ホテル", "inn", "イン", "旅館", "民宿", "resort", "リゾート",
        "villa", "ヴィラ", "ロッジ", "hostel", "ホステル", "ゲストハウス",
        "terrace", "テラス", "tower", "タワー", "hilton", "ハイアット",
        "marriott", "マリオット", "nikko", "日航", "ana", "プリンス",
    ]
    rental_words = ["レンタカー", "rent a car", "car rental", "貸渡", "返却"]
    cafe_words = ["cafe", "coffee", "カフェ", "珈琲", "コーヒー"]
    restaurant_words = ["restaurant", "レストラン", "食堂", "そば", "寿司", "焼肉", "居酒屋"]

    if any(word in target for word in rental_words):
        return "レンタカー"
    if any(word in target for word in hotel_words):
        return "ホテル"
    if any(word in target for word in cafe_words):
        return "カフェ"
    if any(word in target for word in restaurant_words):
        return "ランチ・レストラン"
    return "観光スポット"

def resolve_google_maps_url(raw_url: str, name_override: str = "") -> dict:
    url = str(raw_url or "").strip()
    if not re.match(r"^https?://", url):
        raise ValueError("https:// から始まるGoogleマップURLを貼ってください。")

    final_url = url
    page_html = ""
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
            final_url = response.geturl()
            content_type = response.headers.get("Content-Type", "")
            if "text/html" in content_type:
                page_html = response.read(1_500_000).decode("utf-8", errors="ignore")
    except Exception:
        final_url = url

    canonical_url = extract_canonical_url(page_html)

    coords = None
    for candidate_url in [final_url, canonical_url, url]:
        if candidate_url:
            coords = exact_coords_from_google_url(candidate_url)
            if coords:
                break

    name = name_override.strip()
    address = ""

    for candidate_url in [final_url, canonical_url, url]:
        if not candidate_url or name:
            continue
        parsed = urlparse.urlparse(candidate_url)
        path_match = re.search(r"/maps/(?:place|search)/([^/]+)", parsed.path)
        if path_match:
            candidate = clean_google_name(path_match.group(1))
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
                    name = clean_google_name(candidate)
                    break

    og_title = clean_google_name(extract_meta_content(page_html, "og:title"))
    if og_title and (not name or name in {"Google Maps", "Googleマップ"}):
        name = og_title

    if not name and page_html:
        title_match = re.search(r"<title[^>]*>(.*?)</title>", page_html, flags=re.I | re.S)
        if title_match:
            name = clean_google_name(title_match.group(1))

    description = (
        extract_meta_content(page_html, "og:description")
        or extract_meta_content(page_html, "description")
    )
    if description:
        address = re.sub(r"\s+", " ", html.unescape(description)).strip()[:240]

    # If URL has no coordinate, fall back to geocoding by resolved name.
    if coords is None and name:
        query_text = name if not address else f"{name} {address}"
        candidates = geocode(query_text)
        if not candidates:
            candidates = geocode(name)
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
        reverse_name_candidates = geocode(f"{coords[0]},{coords[1]}")
        if reverse_name_candidates:
            name = reverse_name_candidates[0]["name"]
            if not address:
                address = reverse_name_candidates[0].get("address", "")
        else:
            name = "Googleマップの場所"

    category = infer_category_from_name(name, address)

    return {
        "name": name[:100],
        "address": address,
        "lat": float(coords[0]),
        "lon": float(coords[1]),
        "map_url": final_url or canonical_url or url,
        "category": category,
    }

def load_registered_places() -> list[dict]:
    if not REGISTERED_PLACES_FILE.exists():
        return []
    try:
        data = json.loads(REGISTERED_PLACES_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []

def save_registered_places() -> None:
    REGISTERED_PLACES_FILE.write_text(
        json.dumps(st.session_state.registered_places, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

if not st.session_state.registered_places:
    st.session_state.registered_places = load_registered_places()


EXCEL_SCHEDULE_COLUMNS = {
    "UID": "_uid",
    "日付": "day",
    "順番": "manual_order",
    "場所名": "name",
    "カテゴリ": "category",
    "住所": "address",
    "緯度": "lat",
    "経度": "lon",
    "到着": "arrival",
    "出発": "departure",
    "滞在分": "stay",
    "移動分": "travel_minutes_from_previous",
    "距離km": "distance_km_from_previous",
    "予算円": "cost",
    "人数": "cost_people",
    "予算区分": "cost_group",
    "予算根拠": "cost_basis",
    "メモ": "memo",
    "GoogleマップURL": "map_url",
    "固定予定": "fixed",
}


def _excel_value(value):
    if value is None:
        return ""
    if hasattr(value, "to_pydatetime"):
        value = value.to_pydatetime()
    if isinstance(value, datetime):
        return value
    return value


def current_state_payload() -> dict:
    return {
        "version": 10,
        "trip_start": str(st.session_state.trip_start),
        "trip_days": int(st.session_state.trip_days),
        "spots": st.session_state.spots,
        "day_modes": st.session_state.day_modes,
        "map_region": st.session_state.map_region,
        "day_start_times": st.session_state.day_start_times,
        "registered_places": st.session_state.registered_places,
        "budget_settings": st.session_state.budget_settings,
    }


def excel_bytes_from_state() -> bytes:
    """現在の画面データを、Excel編集しやすい複数シートへ出力する。"""
    payload = current_state_payload()
    schedule_rows = []
    for spot in payload["spots"]:
        schedule_rows.append({
            "UID": spot.get("_uid", ""),
            "日付": spot.get("day", ""),
            "順番": int(spot.get("manual_order", 9999) or 9999),
            "場所名": spot.get("name", ""),
            "カテゴリ": spot.get("category", "観光スポット"),
            "住所": spot.get("address", ""),
            "緯度": float(spot.get("lat", 0) or 0),
            "経度": float(spot.get("lon", 0) or 0),
            "到着": spot.get("arrival", spot.get("start", "")),
            "出発": spot.get("departure", ""),
            "滞在分": int(spot.get("stay", 0) or 0),
            "移動分": int(spot.get("travel_minutes_from_previous", 0) or 0),
            "距離km": float(spot.get("distance_km_from_previous", 0) or 0),
            "予算円": int(spot.get("cost", 0) or 0),
            "人数": int(spot.get("cost_people", 2) or 2),
            "予算区分": spot.get("cost_group", "要確認"),
            "予算根拠": spot.get("cost_basis", spot.get("cost_note", "")),
            "メモ": spot.get("memo", ""),
            "GoogleマップURL": spot.get("map_url", ""),
            "固定予定": bool(spot.get("fixed", False)),
            "拡張JSON": json.dumps(spot, ensure_ascii=False),
        })

    registered_rows = []
    for place in payload["registered_places"]:
        registered_rows.append({
            "UID": place.get("_uid", ""),
            "場所名": place.get("name", ""),
            "カテゴリ": place.get("category", "観光スポット"),
            "住所": place.get("address", ""),
            "緯度": float(place.get("lat", 0) or 0),
            "経度": float(place.get("lon", 0) or 0),
            "予算円": int(place.get("cost", 0) or 0),
            "営業時間": place.get("open", ""),
            "閉店時間": place.get("close", ""),
            "優先度": int(place.get("priority", 3) or 3),
            "GoogleマップURL": place.get("map_url", ""),
            "拡張JSON": json.dumps(place, ensure_ascii=False),
        })

    budget_rows = [
        {"キー": key, "項目": label, "値": payload["budget_settings"].get(key, default), "説明": note}
        for key, label, default, note in [
            ("unregistered_meals", "未登録の食事", 22000, "予定に登録していない朝・昼・夜ご飯"),
            ("gasoline", "ガソリン", 5000, "現地で支払うガソリン代"),
            ("tolls", "高速料金", 2000, "沖縄自動車道など"),
            ("parking", "駐車場", 3000, "各施設の駐車料金"),
            ("convenience_snacks", "コンビニ・おやつ", 6000, "飲み物・軽食・間食"),
            ("souvenirs", "お土産", 15000, "お土産予算"),
            ("contingency", "予備費", 10000, "想定外の支出"),
            ("hotel_paid", "ホテル支払済み", True, "TRUEなら現地予算に含めない"),
            ("rental_paid", "レンタカー支払済み", True, "TRUEなら現地予算に含めない"),
            ("flight_paid", "飛行機支払済み", True, "TRUEなら現地予算に含めない"),
        ]
    ]

    trip_rows = [
        {"キー": "trip_start", "項目": "旅行開始日", "値": str(payload["trip_start"])},
        {"キー": "trip_days", "項目": "旅行日数", "値": payload["trip_days"]},
        {"キー": "map_region", "項目": "地図地域", "値": payload["map_region"]},
    ]
    trip_rows.extend(
        {"キー": f"day_mode:{day}", "項目": f"{day} 移動手段", "値": mode}
        for day, mode in payload["day_modes"].items()
    )
    trip_rows.extend(
        {"キー": f"day_start:{day}", "項目": f"{day} 開始時間", "値": value}
        for day, value in payload["day_start_times"].items()
    )

    breakdown = budget_breakdown()
    summary_rows = [{"区分": k, "金額": int(v)} for k, v in breakdown.items()]
    summary_rows.append({"区分": "現地予算合計", "金額": int(sum(breakdown.values()))})

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(schedule_rows).to_excel(writer, sheet_name="Schedule", index=False)
        pd.DataFrame(registered_rows).to_excel(writer, sheet_name="RegisteredPlaces", index=False)
        pd.DataFrame(budget_rows).to_excel(writer, sheet_name="BudgetSettings", index=False)
        pd.DataFrame(trip_rows).to_excel(writer, sheet_name="TripSettings", index=False)
        pd.DataFrame(summary_rows).to_excel(writer, sheet_name="Dashboard", index=False)

        for sheet_name, worksheet in writer.book.items():
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions
            for cell in worksheet[1]:
                cell.font = cell.font.copy(bold=True, color="FFFFFF")
                cell.fill = cell.fill.copy(fill_type="solid", fgColor="0F766E")
            for column_cells in worksheet.columns:
                length = min(42, max(10, max(len(str(c.value or "")) for c in column_cells) + 2))
                worksheet.column_dimensions[column_cells[0].column_letter].width = length

        schedule_ws = writer.book["Schedule"]
        schedule_headers = {cell.value: cell.column for cell in schedule_ws[1]}
        if "日付" in schedule_headers:
            col = schedule_headers["日付"]
            for row in range(2, schedule_ws.max_row + 1):
                schedule_ws.cell(row, col).number_format = "yyyy-mm-dd"
        if "予算円" in schedule_headers:
            col = schedule_headers["予算円"]
            for row in range(2, schedule_ws.max_row + 1):
                schedule_ws.cell(row, col).number_format = '#,##0"円"'

    return output.getvalue()


def apply_excel_upload(uploaded_file) -> tuple[int, int]:
    """Excelの編集内容を画面へ反映する。JSON拡張列で元データも保持する。"""
    excel = pd.ExcelFile(uploaded_file)
    if "Schedule" not in excel.sheet_names:
        raise ValueError("Scheduleシートがありません")

    schedule_df = pd.read_excel(excel, sheet_name="Schedule")
    spots = []
    for _, row in schedule_df.iterrows():
        if pd.isna(row.get("場所名")):
            continue
        spot = {}
        raw_json = row.get("拡張JSON")
        if isinstance(raw_json, str) and raw_json.strip():
            try:
                spot = json.loads(raw_json)
            except Exception:
                spot = {}

        for excel_col, state_key in EXCEL_SCHEDULE_COLUMNS.items():
            if excel_col not in row.index or pd.isna(row[excel_col]):
                continue
            value = row[excel_col]
            if excel_col == "日付":
                value = pd.to_datetime(value).date().isoformat()
            elif excel_col in {"順番", "滞在分", "移動分", "予算円", "人数"}:
                value = int(value)
            elif excel_col in {"緯度", "経度", "距離km"}:
                value = float(value)
            elif excel_col == "固定予定":
                value = bool(value)
            else:
                value = str(value)
            spot[state_key] = value

        spot.setdefault("_uid", uuid.uuid4().hex)
        spot.setdefault("start", spot.get("到着", spot.get("arrival", "09:00")))
        spot_defaults(spot)
        spots.append(spot)

    registered = []
    if "RegisteredPlaces" in excel.sheet_names:
        reg_df = pd.read_excel(excel, sheet_name="RegisteredPlaces")
        for _, row in reg_df.iterrows():
            if pd.isna(row.get("場所名")):
                continue
            place = {}
            raw_json = row.get("拡張JSON")
            if isinstance(raw_json, str) and raw_json.strip():
                try:
                    place = json.loads(raw_json)
                except Exception:
                    place = {}
            mapping = {
                "UID":"_uid", "場所名":"name", "カテゴリ":"category", "住所":"address",
                "緯度":"lat", "経度":"lon", "予算円":"cost", "営業時間":"open",
                "閉店時間":"close", "優先度":"priority", "GoogleマップURL":"map_url",
            }
            for col, key in mapping.items():
                if col in row.index and not pd.isna(row[col]):
                    val = row[col]
                    if col in {"緯度","経度"}: val = float(val)
                    elif col in {"予算円","優先度"}: val = int(val)
                    else: val = str(val)
                    place[key] = val
            place.setdefault("_uid", uuid.uuid4().hex)
            registered.append(place)

    if "BudgetSettings" in excel.sheet_names:
        bdf = pd.read_excel(excel, sheet_name="BudgetSettings")
        for _, row in bdf.iterrows():
            key = str(row.get("キー", "")).strip()
            if not key or pd.isna(row.get("値")):
                continue
            value = row["値"]
            if key.endswith("_paid"):
                if isinstance(value, str):
                    value = value.strip().lower() in {"true", "1", "yes", "はい"}
                else:
                    value = bool(value)
            else:
                value = int(value)
            st.session_state.budget_settings[key] = value

    if "TripSettings" in excel.sheet_names:
        tdf = pd.read_excel(excel, sheet_name="TripSettings")
        for _, row in tdf.iterrows():
            key = str(row.get("キー", "")).strip()
            value = row.get("値")
            if not key or pd.isna(value):
                continue
            if key == "trip_start":
                st.session_state.trip_start = pd.to_datetime(value).date()
            elif key == "trip_days":
                st.session_state.trip_days = int(value)
            elif key == "map_region":
                st.session_state.map_region = str(value)
            elif key.startswith("day_mode:"):
                st.session_state.day_modes[key.split(":", 1)[1]] = str(value)
            elif key.startswith("day_start:"):
                day = key.split(":", 1)[1]
                if hasattr(value, "strftime"):
                    value = value.strftime("%H:%M")
                st.session_state.day_start_times[day] = str(value)

    st.session_state.spots = spots
    if registered:
        st.session_state.registered_places = registered
        save_registered_places()
    ensure_ids()
    cleanup_duplicate_hotels()
    recalculate_all_days(reorder=False)
    auto_backup()
    return len(spots), len(registered)


def auto_backup() -> None:
    payload = {
        "version": 7,
        "trip_start": str(st.session_state.trip_start),
        "trip_days": int(st.session_state.trip_days),
        "spots": st.session_state.spots,
        "day_modes": st.session_state.day_modes,
        "map_region": st.session_state.map_region,
        "day_start_times": st.session_state.day_start_times,
        "registered_places": st.session_state.registered_places,
        "budget_settings": st.session_state.budget_settings,
    }
    try:
        AUTO_BACKUP_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass



BUDGET_CATALOG = {
    # 支払済み
    "ABCレンタカー那覇空港営業所": {
        "cost": 0, "group": "支払済み", "basis": "レンタカー代は支払い済み",
    },
    "ABCレンタカー那覇空港営業所（返却）": {
        "cost": 0, "group": "支払済み", "basis": "レンタカー代は支払い済み",
    },
    "ザ・ブセナテラス（The Busena Terrace）": {
        "cost": 0, "group": "支払済み", "basis": "ホテル代は支払い済み",
    },
    "ロワジールホテル 那覇": {
        "cost": 0, "group": "支払済み", "basis": "ホテル代は支払い済み",
    },
    "ビーチフロントタワーミハマ": {
        "cost": 0, "group": "支払済み", "basis": "ホテル代は支払い済み",
    },

    # 公式料金・体験
    "万座毛": {
        "cost": 200, "group": "観光・体験",
        "basis": "観覧料 大人100円×2人",
    },
    "PANZA沖縄": {
        "cost": 5500, "group": "観光・体験",
        "basis": "MegaZIP通常料金2,750円×2人",
    },
    "ビオスの丘": {
        "cost": 4400, "group": "観光・体験",
        "basis": "湖水観賞舟付き入園料2,200円×2人",
    },
    "CAVE OKINAWA神秘の鍾乳洞": {
        "cost": 2400, "group": "観光・体験",
        "basis": "通常入場料1,200円×2人",
    },
    "株式会社 琉球ガラス煌工房": {
        "cost": 7400, "group": "観光・体験",
        "basis": "吹きガラス基本料金3,700円×2人。追加オプション・送料別",
    },

    # 飲食は2人分の現実的な目安
    "なかざ屋": {
        "cost": 2400, "group": "飲食",
        "basis": "沖縄そば・定食など2人分の概算",
    },
    "A&W 牧港店": {
        "cost": 3200, "group": "飲食",
        "basis": "バーガー・サイド・飲物を2人分",
    },
    "ブルーシール 牧港本店": {
        "cost": 1400, "group": "飲食",
        "basis": "アイス・サンデー等を2人分",
    },
    "バンタカフェ by 星野リゾート": {
        "cost": 3600, "group": "飲食",
        "basis": "食事・飲物を2人分の概算",
    },

    # 入場自体は無料
    "首里金城町石畳道": {
        "cost": 0, "group": "無料スポット", "basis": "散策無料",
    },
    "美浜タウンリゾート・アメリカンビレッジ": {
        "cost": 0, "group": "無料スポット", "basis": "入場無料。飲食・買物は別",
    },
    "やちむんの里": {
        "cost": 0, "group": "無料スポット", "basis": "散策無料。陶器購入・体験は別",
    },
    "The Sinmay": {
        "cost": 0, "group": "無料・未計上", "basis": "立寄り費用は未計上",
    },
    "古宇利島": {
        "cost": 0, "group": "無料スポット", "basis": "島への入場料なし",
    },
    "ウミカジテラス": {
        "cost": 0, "group": "無料スポット", "basis": "入場無料。飲食・買物は別",
    },
}


def apply_budget_catalog() -> tuple[int, int]:
    """登録済みの全予定に、公式料金または明示した概算根拠を反映する。"""
    updated = 0
    unknown = 0

    for spot in st.session_state.spots:
        name = str(spot.get("name", ""))
        info = BUDGET_CATALOG.get(name)

        if info is not None:
            spot["cost"] = int(info["cost"])
            spot["cost_group"] = str(info["group"])
            spot["cost_basis"] = str(info["basis"])
            spot["cost_people"] = 2
            updated += 1
            continue

        if is_hotel_spot(spot) and st.session_state.budget_settings.get("hotel_paid", True):
            spot["cost"] = 0
            spot["cost_group"] = "支払済み"
            spot["cost_basis"] = "ホテル代は支払い済み"
            updated += 1
        elif is_rental_spot(spot) and st.session_state.budget_settings.get("rental_paid", True):
            spot["cost"] = 0
            spot["cost_group"] = "支払済み"
            spot["cost_basis"] = "レンタカー代は支払い済み"
            updated += 1
        else:
            spot["cost_group"] = "要確認"
            spot["cost_basis"] = "料金を確認できていないため手動確認が必要"
            unknown += 1

    auto_backup()
    return updated, unknown


def budget_breakdown() -> dict:
    """予定に紐づく費用と、旅行全体の追加費用を分けて集計する。"""
    result = {
        "飲食": 0,
        "観光・体験": 0,
        "無料スポット": 0,
        "支払済み": 0,
        "要確認": 0,
    }

    for spot in st.session_state.spots:
        group = str(spot.get("cost_group", "要確認"))
        cost = int(spot.get("cost", 0) or 0)
        result[group] = result.get(group, 0) + cost

    settings = st.session_state.budget_settings
    result["未登録の食事"] = int(settings.get("unregistered_meals", 0))
    result["ガソリン"] = int(settings.get("gasoline", 0))
    result["高速料金"] = int(settings.get("tolls", 0))
    result["駐車場"] = int(settings.get("parking", 0))
    result["コンビニ・おやつ"] = int(settings.get("convenience_snacks", 0))
    result["お土産"] = int(settings.get("souvenirs", 0))
    result["予備費"] = int(settings.get("contingency", 0))
    return result


def budget_total() -> int:
    return sum(budget_breakdown().values())


def is_rental_spot(spot: dict) -> bool:
    name = str(spot.get("name", ""))
    return str(spot.get("category", "")) == "レンタカー" or "レンタカー" in name or "返却" in name

def is_hotel_spot(spot: dict) -> bool:
    return str(spot.get("category", "")) == "ホテル"

def day_sections(day: str):
    items = [s for s in st.session_state.spots if s.get("day") == day]
    rental_start = [s for s in items if is_rental_spot(s) and "返却" not in str(s.get("name", ""))]
    rental_return = [s for s in items if is_rental_spot(s) and "返却" in str(s.get("name", ""))]
    hotels = [s for s in items if is_hotel_spot(s)]
    sightseeing = [s for s in items if s not in rental_start and s not in rental_return and s not in hotels]
    sightseeing.sort(key=lambda s: int(s.get("manual_order", 9999)))
    return rental_start, sightseeing, hotels, rental_return

def normalize_manual_order(day: str) -> None:
    for i, spot in enumerate(day_sections(day)[1]):
        spot["manual_order"] = i

def move_sightseeing(day: str, uid: str, direction: int) -> None:
    spots = day_sections(day)[1]
    ids = [s["_uid"] for s in spots]
    if uid not in ids: return
    i = ids.index(uid); j = i + direction
    if j < 0 or j >= len(spots): return
    spots[i]["manual_order"], spots[j]["manual_order"] = spots[j].get("manual_order",j), spots[i].get("manual_order",i)
    normalize_manual_order(day)

def ordered_day(day: str):
    a,b,c,d = day_sections(day)
    return a+b+c+d

def get_day_start_time(day: str) -> str:
    return st.session_state.day_start_times.get(day, "09:00")

def set_day_start_time(day: str, value: str) -> None:
    st.session_state.day_start_times[day] = value

def hhmm_to_minutes(value: str) -> int:
    try:
        hour, minute = str(value).split(":")
        return int(hour) * 60 + int(minute)
    except Exception:
        return 9 * 60

def minutes_to_hhmm(value: int) -> str:
    value = max(0, int(value))
    return f"{(value // 60) % 24:02d}:{value % 60:02d}"

def recalculate_day_schedule(day: str, mode: str, reorder: bool = False) -> None:
    rental_start, sightseeing, hotels, rental_return = day_sections(day)
    if reorder and len(sightseeing) > 1:
        ordered=[]; remaining=sightseeing[:]
        current = rental_start[-1] if rental_start else remaining.pop(0)
        if not rental_start: ordered.append(current)
        while remaining:
            nxt=min(remaining,key=lambda x:haversine(current,x)); ordered.append(nxt); remaining.remove(nxt); current=nxt
        for i,s in enumerate(ordered): s["manual_order"]=i
        sightseeing=ordered
    items=rental_start+sightseeing+hotels+rental_return
    if not items: return
    cursor=hhmm_to_minutes(get_day_start_time(day)); previous=None
    for i,item in enumerate(items):
        if i==0:
            item["travel_minutes_from_previous"]=0; item["distance_km_from_previous"]=0.0
        else:
            route=route_data(previous["lat"],previous["lon"],item["lat"],item["lon"],mode)
            cursor += int(route["minutes"]); item["travel_minutes_from_previous"]=int(route["minutes"]); item["distance_km_from_previous"]=float(route["km"]); item["route_estimated"]=bool(route.get("estimated",False))
        item["arrival"]=minutes_to_hhmm(cursor); item["start"]=item["arrival"]
        cursor += int(item.get("stay",60)); item["departure"]=minutes_to_hhmm(cursor); previous=item

def recalculate_all_days(reorder: bool = False) -> None:
    for day in trip_dates():
        day_str = str(day)
        mode = st.session_state.day_modes.get(day_str, "車")
        recalculate_day_schedule(day_str, mode, reorder=reorder)

def day_route_totals(day: str) -> tuple[int, float]:
    items = ordered_day(day)
    total_minutes = sum(int(item.get("travel_minutes_from_previous", 0)) for item in items)
    total_km = sum(float(item.get("distance_km_from_previous", 0.0)) for item in items)
    return total_minutes, round(total_km, 1)

def reorder_day_nearest(day: str, mode: str) -> None:
    recalculate_day_schedule(day, mode, reorder=True)


def hotel_candidates() -> list[dict]:
    return [
        place for place in st.session_state.registered_places
        if place.get("category") == "ホテル"
    ]

def scheduled_hotels() -> list[dict]:
    return [
        spot for spot in st.session_state.spots
        if spot.get("category") == "ホテル"
    ]

def remove_registered_place(uid: str) -> None:
    st.session_state.registered_places = [
        place for place in st.session_state.registered_places
        if place.get("_uid") != uid
    ]
    save_registered_places()


def remove_scheduled_hotel(uid: str) -> None:
    """自動追加・手動追加・旧データを問わず、指定ホテルを日程から外す。"""
    removed_days = {
        spot.get("day")
        for spot in st.session_state.spots
        if spot.get("_uid") == uid and spot.get("category") == "ホテル"
    }
    st.session_state.spots = [
        spot for spot in st.session_state.spots
        if not (spot.get("_uid") == uid and spot.get("category") == "ホテル")
    ]
    for day in removed_days:
        if day:
            recalculate_day_schedule(day, st.session_state.day_modes.get(day, "車"), reorder=False)
    auto_backup()


def remove_all_hotels_from_day(day: str) -> int:
    """指定日のホテルをすべて日程から外す。候補一覧は消さない。"""
    before = len(st.session_state.spots)
    st.session_state.spots = [
        spot for spot in st.session_state.spots
        if not (spot.get("category") == "ホテル" and spot.get("day") == day)
    ]
    removed = before - len(st.session_state.spots)
    recalculate_day_schedule(day, st.session_state.day_modes.get(day, "車"), reorder=False)
    auto_backup()
    return removed


def cleanup_duplicate_hotels() -> dict[str, int]:
    """各日にホテルを1軒だけ残し、残りを日程から外す。"""
    grouped: dict[str, list[dict]] = {}
    for spot in st.session_state.spots:
        if spot.get("category") == "ホテル" and spot.get("day"):
            grouped.setdefault(str(spot["day"]), []).append(spot)

    keep_ids: set[str] = set()
    removed_by_day: dict[str, int] = {}
    for day, hotels in grouped.items():
        hotels_sorted = sorted(
            hotels,
            key=lambda item: (
                0 if item.get("scheduled_hotel") else 1,
                0 if item.get("auto_hotel") else 1,
                int(item.get("manual_order", 9999)),
                str(item.get("start", "23:59")),
            ),
        )
        keep_ids.add(hotels_sorted[0]["_uid"])
        if len(hotels_sorted) > 1:
            removed_by_day[day] = len(hotels_sorted) - 1

    if removed_by_day:
        st.session_state.spots = [
            spot for spot in st.session_state.spots
            if spot.get("category") != "ホテル" or spot.get("_uid") in keep_ids
        ]
        for day in removed_by_day:
            recalculate_day_schedule(day, st.session_state.day_modes.get(day, "車"), reorder=False)
        auto_backup()
    return removed_by_day


def add_hotel_to_night(candidate: dict, night_index: int) -> None:
    dates = trip_dates()
    if night_index < 0 or night_index >= max(0, len(dates) - 1):
        raise ValueError("宿泊日が範囲外です。")

    day = str(dates[night_index])

    # 同じ日にはホテルを1軒だけ残す。旧データ由来も含めて置き換える。
    st.session_state.spots = [
        spot for spot in st.session_state.spots
        if not (spot.get("category") == "ホテル" and spot.get("day") == day)
    ]

    event = copy.deepcopy(candidate)
    event["_uid"] = uuid.uuid4().hex
    event["day"] = day
    event["start"] = "19:00"
    event["stay"] = 30
    event["fixed"] = True
    event["scheduled_hotel"] = True
    event["auto_hotel"] = True
    event["memo"] = f"{night_index + 1}泊目"
    event["manual_order"] = 9999
    st.session_state.spots.append(event)

    recalculate_day_schedule(
        day,
        st.session_state.day_modes.get(day, "車"),
        reorder=False,
    )
    auto_backup()

def assign_hotels_to_nights(hotel_ids: list[str]) -> None:
    dates = trip_dates()
    nights = max(0, len(dates) - 1)
    candidate_map = {
        place["_uid"]: place
        for place in hotel_candidates()
    }

    # Remove only hotel events created through the hotel scheduler.
    st.session_state.spots = [
        spot for spot in st.session_state.spots
        if not spot.get("scheduled_hotel", False)
    ]

    for night_index in range(min(nights, len(hotel_ids))):
        candidate = candidate_map.get(hotel_ids[night_index])
        if candidate:
            add_hotel_to_night(candidate, night_index)

    recalculate_all_days(reorder=False)
    auto_backup()

def req_json(url, params=None, method="get", data=None, timeout=30):
    headers = {"User-Agent": UA, "Accept-Language": "ja"}
    if method == "post":
        response = requests.post(url, data=data, headers=headers, timeout=timeout)
    else:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()

@st.cache_data(ttl=86400, show_spinner=False)
def geocode(query):
    data = req_json(
        NOMINATIM,
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
def nearby(lat, lon, category, radius):
    clauses = []
    for rule in CATEGORIES[category]:
        clauses.extend([
            f"node{rule}(around:{radius},{lat},{lon});",
            f"way{rule}(around:{radius},{lat},{lon});",
            f"relation{rule}(around:{radius},{lat},{lon});",
        ])
    query = f"[out:json][timeout:25];({''.join(clauses)});out center tags 40;"
    data = req_json(OVERPASS, method="post", data={"data": query})
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
            "category": category,
        })
    unique = {}
    for item in result:
        unique[(item["name"], round(item["lat"], 5), round(item["lon"], 5))] = item
    return list(unique.values())

def haversine(a, b):
    radius = 6371
    p1 = math.radians(a["lat"])
    p2 = math.radians(b["lat"])
    dp = math.radians(b["lat"] - a["lat"])
    dl = math.radians(b["lon"] - a["lon"])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))

@st.cache_data(ttl=3600, show_spinner=False)
def route_data(a_lat, a_lon, b_lat, b_lon, mode):
    profile = MODE_PROFILE.get(mode, "driving")
    try:
        data = req_json(
            f"{OSRM}/route/v1/{profile}/{a_lon},{a_lat};{b_lon},{b_lat}",
            params={"overview": "full", "geometries": "geojson"},
        )
        route = data["routes"][0]
        coords = [[lat, lon] for lon, lat in route["geometry"]["coordinates"]]
        return {
            "minutes": round(route["duration"] / 60),
            "km": round(route["distance"] / 1000, 1),
            "coords": coords,
            "estimated": False,
        }
    except Exception:
        distance = haversine({"lat": a_lat, "lon": a_lon}, {"lat": b_lat, "lon": b_lon})
        speed = {"車": 35, "徒歩": 4.5, "自転車": 15}[mode]
        factor = {"車": 1.25, "徒歩": 1.15, "自転車": 1.2}[mode]
        road_distance = distance * factor
        return {
            "minutes": max(1, round(road_distance / speed * 60)),
            "km": round(road_distance, 1),
            "coords": [[a_lat, a_lon], [b_lat, b_lon]],
            "estimated": True,
        }

def format_duration(minutes):
    hours, mins = divmod(int(minutes), 60)
    if hours and mins:
        return f"{hours}時間{mins}分"
    if hours:
        return f"{hours}時間"
    return f"{mins}分"

def gmap_url(spot):
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(str(spot['lat']) + ',' + str(spot['lon']))}"

def trip_dates():
    return [
        st.session_state.trip_start + timedelta(days=i)
        for i in range(int(st.session_state.trip_days))
    ]

def ensure_ids():
    seen = set()
    for spot in st.session_state.spots:
        uid = str(spot.get("_uid", "")).strip()
        if not uid or uid in seen:
            uid = uuid.uuid4().hex
            spot["_uid"] = uid
        seen.add(uid)

def add_spot(spot, day, start, stay, category):
    defaults = CATEGORY_META_DEFAULTS.get(category, CATEGORY_META_DEFAULTS["観光スポット"])
    st.session_state.spots.append({
        "_uid": uuid.uuid4().hex,
        "name": spot["name"],
        "address": spot.get("address", ""),
        "lat": float(spot["lat"]),
        "lon": float(spot["lon"]),
        "day": day,
        "start": start,
        "stay": int(stay),
        "fixed": False,
        "memo": "",
        "category": category,
        "cost": int(defaults["cost"]),
        "open": str(defaults["open"]),
        "close": str(defaults["close"]),
        "indoor": bool(defaults["indoor"]),
        "priority": int(defaults["priority"]),
        "must_visit": False,
        "map_url": spot.get("map_url", ""),
        "manual_order": len(day_sections(day)[1]) if category not in ("ホテル", "レンタカー") else 9999,
    })
    st.session_state.map_region = region_for(float(spot["lat"]), float(spot["lon"]))
    mode = st.session_state.day_modes.get(day, "車")
    recalculate_day_schedule(day, mode, reorder=False)
    auto_backup()

def map_for_current_state(selected_day=None):
    region = st.session_state.map_region
    center_lat, center_lon, zoom = REGION_CENTERS.get(region, REGION_CENTERS["日本全体"])
    fmap = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        control_scale=True,
        tiles="OpenStreetMap",
    )

    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
        attr="OpenStreetMap HOT",
        name="見やすい地図",
    ).add_to(fmap)

    display_spots = st.session_state.spots
    if region != "日本全体":
        display_spots = [
            spot for spot in st.session_state.spots
            if region_for(spot["lat"], spot["lon"]) == region
        ]

    cluster = MarkerCluster(name="登録地点").add_to(fmap)
    for index, spot in enumerate(display_spots, start=1):
        icon_color = "red" if spot.get("fixed") else "blue"
        popup_html = f"""
        <b>{index}. {spot['name']}</b><br>
        {spot.get('address', '')}<br>
        {spot['day']} {spot['start']}<br>
        滞在 {spot['stay']}分 / 予算 {spot.get('cost',0):,}円<br>
        営業 {spot.get('open','?')}〜{spot.get('close','?')} / 優先度 {spot.get('priority',3)}
        """
        folium.Marker(
            [spot["lat"], spot["lon"]],
            tooltip=f"{index}. {spot['name']}",
            popup=folium.Popup(popup_html, max_width=320),
            icon=folium.Icon(color=icon_color, icon="info-sign"),
        ).add_to(cluster)

    if selected_day:
        day_spots = ordered_day(selected_day)
        mode = st.session_state.day_modes.get(selected_day, "車")
        for i in range(1, len(day_spots)):
            origin = day_spots[i - 1]
            destination = day_spots[i]
            route = route_data(
                origin["lat"], origin["lon"],
                destination["lat"], destination["lon"],
                mode,
            )
            tooltip = f"{origin['name']} → {destination['name']}｜{format_duration(route['minutes'])}｜{route['km']}km"
            AntPath(
                locations=route["coords"],
                tooltip=tooltip,
                color="#ff5f70",
                pulse_color="#ffffff",
                weight=7,
                opacity=0.9,
                delay=900,
            ).add_to(fmap)

    if display_spots:
        fmap.fit_bounds([
            [min(s["lat"] for s in display_spots), min(s["lon"] for s in display_spots)],
            [max(s["lat"] for s in display_spots), max(s["lon"] for s in display_spots)],
        ], padding=(35, 35))

    folium.LayerControl(collapsed=True).add_to(fmap)
    return fmap

def go(page):
    st.session_state.page = page
    st.rerun()

ensure_ids()
for day in trip_dates():
    st.session_state.day_modes.setdefault(str(day), "車")

h1, h2, h3, h4, h5 = st.columns([2.6, 1, 1, 1.15, 1.1])
with h1:
    st.markdown(
        '<div class="hero"><div class="logo"><span class="a">旅</span><span class="b">ゲーム</span><span class="c">メーカー</span> 全国版</div><div class="subtitle">正確な実地図を使って、全国の旅行プランをゲーム感のある画面で組み立てる</div></div>',
        unsafe_allow_html=True,
    )
with h2:
    st.markdown(
        f'<div class="stat-card"><div class="label">📅 旅行日数</div><div class="value">{len(trip_dates())}日</div></div>',
        unsafe_allow_html=True,
    )
with h3:
    st.markdown(
        f'<div class="stat-card"><div class="label">📍 登録地点</div><div class="value">{len(st.session_state.spots)}件</div></div>',
        unsafe_allow_html=True,
    )
with h4:
    st.markdown(
        f'<div class="stat-card"><div class="label">🗺️ 表示地域</div><div class="value">{st.session_state.map_region}</div></div>',
        unsafe_allow_html=True,
    )
with h5:
    st.markdown(
        '<div class="stat-card"><div class="label">🧭 地図</div><div class="value">実地図</div></div>',
        unsafe_allow_html=True,
    )

if st.session_state.page == "旅程":
    left, center, right = st.columns([1, 2.35, 1.35])

    with left:
        st.markdown('<div class="panel"><div class="panel-title">🛠 旅行設定</div>', unsafe_allow_html=True)
        st.session_state.trip_start = st.date_input("旅行開始日", st.session_state.trip_start)
        st.session_state.trip_days = st.number_input("旅行日数", 1, 14, int(st.session_state.trip_days))

        region_options = list(REGION_CENTERS)
        st.session_state.map_region = st.selectbox(
            "地図の表示範囲",
            region_options,
            index=region_options.index(st.session_state.map_region),
        )

        if st.button("🔎 場所を検索", type="primary", use_container_width=True, key="button_769_1"):
            go("スポット検索")
        if st.button("📍 近くを探す", use_container_width=True, key="button_771_2"):
            go("近くを探す")
        if st.button("🧰 便利機能", use_container_width=True, key="button_773_3"):
            go("便利機能")

        selected_day = st.selectbox(
            "ルートを表示する日",
            [str(day) for day in trip_dates()],
            format_func=lambda value: date.fromisoformat(value).strftime("%m月%d日"),
        )
        day_start_value = st.time_input(
            "その日の開始時間",
            datetime.strptime(get_day_start_time(selected_day), "%H:%M").time(),
            key=f"day_start_{selected_day}",
        ).strftime("%H:%M")
        set_day_start_time(selected_day, day_start_value)

        modes = ["車", "徒歩", "自転車"]
        selected_mode = st.radio(
            "移動手段",
            modes,
            index=modes.index(st.session_state.day_modes.get(selected_day, "車")),
            horizontal=True,
        )
        st.session_state.day_modes[selected_day] = selected_mode
        recalculate_day_schedule(selected_day, selected_mode, reorder=False)

        if st.button("✨ 近い順に並べて全時刻を再計算", use_container_width=True, key="button_798_4"):
            recalculate_day_schedule(selected_day, selected_mode, reorder=True)
            auto_backup()
            st.success("距離・移動時間・到着時刻を自動計算しました。")
            st.rerun()

        day_items = ordered_day(selected_day)
        if day_items:
            total_minutes, total_km = day_route_totals(selected_day)
            st.markdown("#### 自動計算結果")
            c1, c2 = st.columns(2)
            c1.metric("合計移動時間", format_duration(total_minutes))
            c2.metric("合計距離", f"{total_km:.1f}km")
            for item in day_items:
                if item.get("travel_minutes_from_previous", 0):
                    suffix = "（概算）" if item.get("route_estimated") else ""
                    st.caption(
                        f"{MODE_EMOJI[selected_mode]} {item['name']}："
                        f"前の場所から {format_duration(item['travel_minutes_from_previous'])} / "
                        f"{item.get('distance_km_from_previous', 0):.1f}km {suffix}"
                    )
        st.markdown("</div>", unsafe_allow_html=True)

    with center:
        st.markdown('<div class="map-wrap">', unsafe_allow_html=True)
        st_folium(
            map_for_current_state(selected_day),
            width=None,
            height=720,
            returned_objects=[],
            key=f"main_map_{st.session_state.map_region}_{selected_day}_{selected_mode}",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### ✏️ 予定を編集")
        for day in trip_dates():
            day_str=str(day)
            rental_start, sightseeing, hotels, rental_return = day_sections(day_str)
            with st.expander(day.strftime("%m月%d日")+"の予定", expanded=False):
                if rental_start:
                    st.markdown("#### 🚗 レンタカー受取")
                    for item in rental_start:
                        st.markdown(f"**{item['name']}**　{item.get('arrival',item.get('start','--:--'))}着 → {item.get('departure','--:--')}発")
                st.markdown("#### 📍 観光・食事")
                for index,item in enumerate(sightseeing):
                    uid=item["_uid"]
                    c0,c1,c2,c3,c4=st.columns([.55,2.7,1.1,1.1,1.1])
                    with c0:
                        if st.button("↑",key=f"up_{uid}",disabled=index==0,use_container_width=True):
                            move_sightseeing(day_str,uid,-1); recalculate_day_schedule(day_str,st.session_state.day_modes.get(day_str,"車")); auto_backup(); st.rerun()
                        if st.button("↓",key=f"down_{uid}",disabled=index==len(sightseeing)-1,use_container_width=True):
                            move_sightseeing(day_str,uid,1); recalculate_day_schedule(day_str,st.session_state.day_modes.get(day_str,"車")); auto_backup(); st.rerun()
                    with c1:
                        st.markdown(f"**{index+1}. {item['name']}**")
                        item["memo"]=st.text_input("メモ",item.get("memo",""),key=f"memo_{uid}",label_visibility="collapsed")
                    with c2: st.metric("到着",item.get("arrival",item.get("start","--:--")))
                    with c3: item["stay"]=st.number_input("滞在分",10,600,int(item.get("stay",60)),10,key=f"stay_{uid}")
                    with c4:
                        st.link_button("地図",item.get("map_url") or gmap_url(item),use_container_width=True)
                        if st.button("削除",key=f"del_{uid}",use_container_width=True):
                            st.session_state.spots=[s for s in st.session_state.spots if s["_uid"]!=uid]; normalize_manual_order(day_str); recalculate_day_schedule(day_str,st.session_state.day_modes.get(day_str,"車")); auto_backup(); st.rerun()
                if hotels:
                    st.markdown("#### 🏨 宿泊ホテル")
                    if len(hotels) > 1:
                        st.error(f"この日にホテルが{len(hotels)}軒入っています。")
                    if st.button(
                        "この日のホテルを全部外す",
                        key=f"remove_all_hotels_{day_str}",
                        use_container_width=True,
                    ):
                        removed_count = remove_all_hotels_from_day(day_str)
                        st.success(f"{removed_count}軒の日程ホテルを外しました。")
                        st.rerun()
                    for item in hotels:
                        st.markdown(f"**{item['name']}**　{item.get('arrival',item.get('start','--:--'))}到着")
                if rental_return:
                    st.markdown("#### 🚗 レンタカー返却")
                    for item in rental_return:
                        st.markdown(f"**{item['name']}**　{item.get('arrival',item.get('start','--:--'))}着")

    with right:
        st.markdown('<div class="panel"><div class="panel-title">📖 旅のしおり</div>', unsafe_allow_html=True)
        for index, day in enumerate(trip_dates(), start=1):
            items = ordered_day(str(day))
            rows = "".join(
                f'<div class="timeline-row"><div class="time">{item.get("arrival",item.get("start","--:--"))}</div>'
                f'<div>{ICON_BY_CAT.get(item.get("category"),"📍")} {"【レンタカー】" if is_rental_spot(item) else ("【ホテル】" if is_hotel_spot(item) else "")} {item["name"]}'
                f'<br><span style="font-size:.75rem;color:#6f7e86;">'
                f'{format_duration(item.get("travel_minutes_from_previous",0)) if item.get("travel_minutes_from_previous",0) else "開始地点"}'
                f' / {item.get("distance_km_from_previous",0):.1f}km</span></div>'
                f'<div class="badge">{item.get("departure","--:--")}発</div></div>'
                for item in items
            ) or '<div class="timeline-row"><div>-</div><div>予定なし</div><div class="badge">自由</div></div>'
            css_class = "orange" if index % 3 == 2 else ("blue" if index % 3 == 0 else "")
            mode = st.session_state.day_modes.get(str(day), "車")
            st.markdown(
                f'<div class="day-card"><div class="day-head {css_class}">DAY {index}｜{day.strftime("%m/%d")} {MODE_EMOJI[mode]} {mode}</div><div class="timeline">{rows}</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "スポット検索":
    left, center, right = st.columns([1, 2.2, 1.35])

    with left:
        st.markdown('<div class="panel"><div class="panel-title">🔎 全国の場所を検索</div>', unsafe_allow_html=True)
        query = st.text_input("施設名・住所・地域", placeholder="沖縄美ら海水族館 / 金閣寺 / 札幌時計台")
        add_day = st.selectbox("追加する日", [str(day) for day in trip_dates()])
        add_stay = st.number_input("滞在分", 10, 600, 60, 10)
        add_category = st.selectbox("分類", list(CATEGORIES), index=2)

        if st.button("検索する", type="primary", use_container_width=True, key="button_919_5"):
            if query.strip():
                with st.spinner("全国から検索中…"):
                    st.session_state.search_results = geocode(query)
                if st.session_state.search_results:
                    first = st.session_state.search_results[0]
                    st.session_state.map_region = region_for(first["lat"], first["lon"])
                    st.rerun()

        if st.button("← 旅程へ戻る", use_container_width=True, key="button_928_6"):
            go("旅程")
        st.markdown("</div>", unsafe_allow_html=True)

    with center:
        temp_map = folium.Map(
            location=REGION_CENTERS[st.session_state.map_region][:2],
            zoom_start=REGION_CENTERS[st.session_state.map_region][2],
            control_scale=True,
        )
        for result in st.session_state.search_results:
            folium.Marker(
                [result["lat"], result["lon"]],
                tooltip=result["name"],
                popup=result["address"],
                icon=folium.Icon(color="green", icon="search"),
            ).add_to(temp_map)
        if st.session_state.search_results:
            temp_map.fit_bounds([
                [min(x["lat"] for x in st.session_state.search_results), min(x["lon"] for x in st.session_state.search_results)],
                [max(x["lat"] for x in st.session_state.search_results), max(x["lon"] for x in st.session_state.search_results)],
            ], padding=(35, 35))

        st.markdown('<div class="map-wrap">', unsafe_allow_html=True)
        st_folium(temp_map, width=None, height=720, returned_objects=[], key="search_map")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel"><div class="panel-title">検索結果</div>', unsafe_allow_html=True)
        for index, result in enumerate(st.session_state.search_results):
            region = region_for(result["lat"], result["lon"])
            st.markdown(
                f'<div class="spot-card"><div class="spot-title">{result["name"]}</div><div class="spot-meta">{region}｜{result["address"]}</div></div>',
                unsafe_allow_html=True,
            )
            a, b = st.columns(2)
            a.link_button("地図で確認", gmap_url(result), use_container_width=True)
            if b.button("日程に追加", key=f"search_add_{index}", use_container_width=True):
                add_spot(result, add_day, get_day_start_time(add_day), add_stay, add_category)
                st.success("追加しました")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "近くを探す":
    left, center, right = st.columns([1, 2.2, 1.35])

    with left:
        st.markdown('<div class="panel"><div class="panel-title">📍 登録地点の近くを検索</div>', unsafe_allow_html=True)
        if st.session_state.spots:
            names = [
                f'{spot["name"]}（{region_for(spot["lat"], spot["lon"])}）'
                for spot in st.session_state.spots
            ]
            base_index = st.selectbox("基準地点", range(len(names)), format_func=lambda i: names[i])
            base = st.session_state.spots[base_index]
            st.session_state.map_region = region_for(base["lat"], base["lon"])

            category = st.selectbox("ジャンル", list(CATEGORIES))
            radius = st.slider("範囲", 500, 10000, 3000, 500)
            add_day = st.selectbox("追加日", [str(day) for day in trip_dates()])

            if st.button("近くを検索", type="primary", use_container_width=True, key="button_989_7"):
                with st.spinner("周辺検索中…"):
                    result = nearby(base["lat"], base["lon"], category, radius)
                    for item in result:
                        item["distance"] = haversine(base, item)
                    st.session_state.nearby_results = sorted(result, key=lambda x: x["distance"])[:20]

        if st.button("← 旅程へ戻る", use_container_width=True, key="button_996_8"):
            go("旅程")
        st.markdown("</div>", unsafe_allow_html=True)

    with center:
        near_map = folium.Map(location=[base["lat"], base["lon"]], zoom_start=13, control_scale=True)
        folium.Marker(
            [base["lat"], base["lon"]],
            tooltip=f"基準地点：{base['name']}",
            icon=folium.Icon(color="red", icon="flag"),
        ).add_to(near_map)
        for item in st.session_state.nearby_results:
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
        for index, item in enumerate(st.session_state.nearby_results):
            st.markdown(
                f'<div class="spot-card"><div class="spot-title">{ICON_BY_CAT.get(item.get("category"),"📍")} {item["name"]}</div><div class="spot-meta">約{item["distance"]:.1f}km｜{item.get("address","")}</div></div>',
                unsafe_allow_html=True,
            )
            a, b = st.columns(2)
            a.link_button("地図で確認", gmap_url(item), use_container_width=True)
            if b.button("日程に追加", key=f"near_add_{index}", use_container_width=True):
                add_spot(item, add_day, get_day_start_time(add_day), 60, item.get("category", "観光スポット"))
                st.success("追加しました")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


elif st.session_state.page == "便利機能":
    left, center, right = st.columns([1.05, 2.15, 1.35])

    with left:
        st.markdown('<div class="panel"><div class="panel-title">🧰 便利機能</div>', unsafe_allow_html=True)
        tool = st.radio(
            "使う機能",
            ["GoogleマップURL登録", "ホテル順", "自動旅程", "予算", "スマホ接続"],
        )
        if st.button("← 旅程へ戻る", use_container_width=True, key="button_1043_9"):
            go("旅程")
        st.markdown("</div>", unsafe_allow_html=True)

    with center:
        if tool == "GoogleマップURL登録":
            st.markdown('<div class="panel"><div class="panel-title">🔗 GoogleマップURL一括登録</div>', unsafe_allow_html=True)
            raw_urls = st.text_area(
                "1行1URL。『場所名 | URL』にも対応",
                height=220,
                placeholder="ロワジールホテル那覇 | https://www.google.com/maps/place/...",
            )
            category = st.selectbox("登録時の分類", ["自動判定"] + list(CATEGORIES), index=0, key="url_category")
            if st.button("URLを読み取って登録", type="primary", use_container_width=True, key="button_1056_10"):
                results = []
                for parsed in parse_google_map_lines(raw_urls):
                    if not parsed.get("ok"):
                        results.append({"状態": "失敗", "場所名": "", "理由": parsed.get("reason", "")})
                        continue
                    try:
                        resolved = resolve_google_maps_url(parsed["url"], parsed.get("name_override", ""))
                        resolved_category = resolved.get("category") or category
                        if category != "自動判定":
                            resolved_category = category
                        defaults = CATEGORY_META_DEFAULTS.get(
                            resolved_category,
                            CATEGORY_META_DEFAULTS["観光スポット"],
                        )
                        record = {
                            "_uid": uuid.uuid4().hex,
                            **resolved,
                            "category": resolved_category,
                            "cost": defaults["cost"],
                            "open": defaults["open"],
                            "close": defaults["close"],
                            "indoor": defaults["indoor"],
                            "priority": defaults["priority"],
                            "must_visit": False,
                        }
                        duplicate = any(
                            abs(float(x["lat"]) - record["lat"]) < 0.00002
                            and abs(float(x["lon"]) - record["lon"]) < 0.00002
                            for x in st.session_state.registered_places
                        )
                        if duplicate:
                            results.append({"状態": "重複", "場所名": record["name"], "理由": "すでに登録済み"})
                        else:
                            st.session_state.registered_places.append(record)
                            results.append({"状態": "登録完了", "場所名": record["name"], "理由": f'{record["category"]}として登録 / 座標取得済み'})
                    except Exception as exc:
                        results.append({"状態": "失敗", "場所名": parsed.get("name_override", ""), "理由": str(exc)})
                st.session_state.url_import_results = results
                save_registered_places()
                st.rerun()

            if st.session_state.url_import_results:
                st.dataframe(st.session_state.url_import_results, use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="panel"><div class="panel-title">登録済み候補</div>', unsafe_allow_html=True)
            for index, place in enumerate(st.session_state.registered_places):
                st.markdown(
                    f'<div class="spot-card"><div class="spot-title">{place["name"]}</div>'
                    f'<div class="spot-meta">{region_for(place["lat"],place["lon"])}｜'
                    f'{place.get("category","観光スポット")}｜{place["lat"]:.5f},{place["lon"]:.5f}</div></div>',
                    unsafe_allow_html=True,
                )
                a, b, c = st.columns(3)
                a.link_button("Googleマップ", place.get("map_url") or gmap_url(place), use_container_width=True)
                if b.button("日程へ追加", key=f"registered_add_{index}", use_container_width=True):
                    dates_now = trip_dates()
                    add_spot(
                        place,
                        str(dates_now[0]),
                        get_day_start_time(str(dates_now[0])),
                        30 if place.get("category") == "ホテル" else 60,
                        place.get("category", "観光スポット"),
                    )
                    auto_backup()
                    st.success("初日に追加しました。旅程画面で日付と時刻を変更できます。")
                if c.button("候補を削除", key=f"registered_delete_{index}", use_container_width=True):
                    remove_registered_place(place["_uid"])
                    st.success("候補一覧から削除しました。")
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        elif tool == "ホテル順":
            st.markdown('<div class="panel"><div class="panel-title">🏨 ホテル管理</div>', unsafe_allow_html=True)

            candidates = hotel_candidates()
            nights = max(0, int(st.session_state.trip_days) - 1)
            dates_now = trip_dates()

            st.markdown("### 登録済みホテル候補")
            st.caption("ここは候補一覧です。日程へ入れなくても残せます。不要な候補は削除できます。")

            if not candidates:
                st.info("ホテル候補がありません。GoogleマップURL登録でホテルを追加してください。")
            else:
                for index, hotel in enumerate(candidates):
                    uid = hotel["_uid"]
                    st.markdown(
                        f'<div class="spot-card"><div class="spot-title">🏨 {hotel["name"]}</div>'
                        f'<div class="spot-meta">{hotel.get("address","")}｜'
                        f'{hotel.get("lat",0):.5f},{hotel.get("lon",0):.5f}</div></div>',
                        unsafe_allow_html=True,
                    )
                    c1, c2, c3 = st.columns([1.2, 1.4, 1.1])
                    with c1:
                        st.link_button(
                            "Googleマップ",
                            hotel.get("map_url") or gmap_url(hotel),
                            use_container_width=True,
                        )
                    with c2:
                        night_options = list(range(nights))
                        if night_options:
                            selected_night = st.selectbox(
                                "追加する宿泊日",
                                night_options,
                                format_func=lambda n: f"{n+1}泊目｜{dates_now[n].strftime('%m/%d')}",
                                key=f"hotel_candidate_night_{uid}",
                                label_visibility="collapsed",
                            )
                            if st.button(
                                "この泊に設定",
                                key=f"set_hotel_night_{uid}",
                                use_container_width=True,
                            ):
                                add_hotel_to_night(hotel, selected_night)
                                st.success(f"{selected_night+1}泊目へ設定しました。")
                                st.rerun()
                    with c3:
                        if st.button(
                            "候補から削除",
                            key=f"delete_hotel_candidate_{uid}",
                            use_container_width=True,
                        ):
                            remove_registered_place(uid)
                            st.success("ホテル候補から削除しました。")
                            st.rerun()

            st.divider()
            st.markdown("### 日程に入っているホテル")
            if st.button(
                "重複ホテルを自動整理する",
                key="cleanup_duplicate_hotels_button",
                use_container_width=True,
            ):
                removed_map = cleanup_duplicate_hotels()
                removed_total = sum(removed_map.values())
                if removed_total:
                    st.success(f"{removed_total}軒の重複ホテルを整理しました。")
                else:
                    st.info("重複ホテルはありませんでした。")
                st.rerun()
            st.caption("各ホテルを日程から外せます。候補一覧には残ります。")

            scheduled = sorted(
                scheduled_hotels(),
                key=lambda x: (x.get("day", ""), x.get("start", "19:00")),
            )
            if not scheduled:
                st.info("日程にホテルは入っていません。")
            else:
                for hotel in scheduled:
                    uid = hotel["_uid"]
                    st.markdown(
                        f'<div class="spot-card"><div class="spot-title">🏨 {hotel["name"]}</div>'
                        f'<div class="spot-meta">{hotel.get("memo","宿泊")}｜'
                        f'{hotel.get("day","")}｜到着 {hotel.get("arrival",hotel.get("start","--:--"))}</div></div>',
                        unsafe_allow_html=True,
                    )
                    a, b = st.columns([1.4, 1.1])
                    with a:
                        st.link_button(
                            "Googleマップ",
                            hotel.get("map_url") or gmap_url(hotel),
                            use_container_width=True,
                        )
                    with b:
                        if st.button(
                            "日程から外す",
                            key=f"remove_scheduled_hotel_{uid}",
                            use_container_width=True,
                        ):
                            remove_scheduled_hotel(uid)
                            st.success("日程から外しました。候補一覧には残っています。")
                            st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        elif tool == "自動旅程":
            st.markdown('<div class="panel"><div class="panel-title">✨ 自動旅程調整</div>', unsafe_allow_html=True)
            st.write("各日の開始時間だけを基準に、順番・距離・移動時間・到着時刻・出発時刻をすべて自動計算します。")
            if st.button("全日程を自動調整", type="primary", use_container_width=True, key="button_1139_12"):
                for day in trip_dates():
                    day_str = str(day)
                    reorder_day_nearest(day_str, st.session_state.day_modes.get(day_str, "車"))
                auto_backup()
                st.success("全日程を調整しました。")
                st.rerun()
            st.warning("営業時間や予約時刻は完全自動ではないため、調整後に確認してください。")
            st.markdown("</div>", unsafe_allow_html=True)

        elif tool == "予算":
            st.markdown('<div class="panel"><div class="panel-title">💰 旅行予算</div>', unsafe_allow_html=True)
            st.caption("夫婦2人分。ホテル・飛行機・レンタカーは支払い済みとして、現地でこれから使う金額を集計します。")

            if st.button(
                "全予定の料金を反映",
                type="primary",
                use_container_width=True,
                key="apply_all_budget_prices",
            ):
                updated, unknown = apply_budget_catalog()
                st.success(f"{updated}件の料金を反映しました。未確認は{unknown}件です。")
                st.rerun()

            settings = st.session_state.budget_settings
            c1, c2 = st.columns(2)
            with c1:
                settings["unregistered_meals"] = st.number_input(
                    "未登録の朝・昼・夜ご飯",
                    0, 100000, int(settings.get("unregistered_meals", 22000)), 1000,
                    key="budget_unregistered_meals",
                )
                settings["gasoline"] = st.number_input(
                    "ガソリン",
                    0, 50000, int(settings.get("gasoline", 5000)), 500,
                    key="budget_gasoline",
                )
                settings["tolls"] = st.number_input(
                    "高速料金",
                    0, 50000, int(settings.get("tolls", 2000)), 500,
                    key="budget_tolls",
                )
                settings["parking"] = st.number_input(
                    "駐車場",
                    0, 50000, int(settings.get("parking", 3000)), 500,
                    key="budget_parking",
                )
            with c2:
                settings["convenience_snacks"] = st.number_input(
                    "コンビニ・おやつ",
                    0, 50000, int(settings.get("convenience_snacks", 6000)), 500,
                    key="budget_snacks",
                )
                settings["souvenirs"] = st.number_input(
                    "お土産",
                    0, 100000, int(settings.get("souvenirs", 15000)), 1000,
                    key="budget_souvenirs",
                )
                settings["contingency"] = st.number_input(
                    "予備費",
                    0, 100000, int(settings.get("contingency", 10000)), 1000,
                    key="budget_contingency",
                )

            if st.button("追加予算を保存", use_container_width=True, key="save_budget_settings"):
                auto_backup()
                st.success("追加予算を保存しました。")

            breakdown = budget_breakdown()
            st.markdown("#### 現地予算の内訳")
            for label, amount in breakdown.items():
                if label == "支払済み":
                    continue
                st.write(f"**{label}**：{amount:,}円")

            st.metric("現地で使う予算合計", f"{budget_total():,}円")

            st.markdown("#### 予定ごとの金額")
            for day in trip_dates():
                day_str = str(day)
                st.markdown(f"**{day.strftime('%m月%d日')}**")
                for spot in day_schedule_view(day_str):
                    if spot.get("is_day_start_anchor"):
                        continue
                    cost = int(spot.get("cost", 0) or 0)
                    basis = str(spot.get("cost_basis", "未確認"))
                    st.caption(f"{spot['name']}：{cost:,}円｜{basis}")

            st.warning("飲食は注文内容、体験はオプション、駐車場は利用時間で増減します。表示額は上限ではありません。")
            st.markdown("</div>", unsafe_allow_html=True)

        else:
            st.markdown('<div class="panel"><div class="panel-title">📱 スマホで開く</div>', unsafe_allow_html=True)
            lan_ip = get_lan_ip()
            if lan_ip:
                mobile_url = f"http://{lan_ip}:8501"
                st.write(f"同じWi-Fiのスマホで開くURL：`{mobile_url}`")
                st.image(qr_png_bytes(mobile_url), width=230)
            else:
                st.warning("MacのWi-Fi内IPを取得できませんでした。")
            st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel"><div class="panel-title">📊 旅行情報</div>', unsafe_allow_html=True)
        total_cost = budget_total()
        must_count = sum(bool(spot.get("must_visit")) for spot in st.session_state.spots)
        hotel_count = sum(spot.get("category") == "ホテル" for spot in st.session_state.spots)
        st.metric("現地予算合計", f"{total_cost:,}円")
        st.metric("必須スポット", f"{must_count}件")
        st.metric("ホテル候補", f"{hotel_count}件")
        st.metric("URL登録候補", f"{len(st.session_state.registered_places)}件")
        st.markdown("</div>", unsafe_allow_html=True)


st.markdown("### 💾 Excel・JSON 保存／読み込み")
excel_save_col, excel_load_col = st.columns([1, 1.4])

with excel_save_col:
    st.download_button(
        "📗 現在のデータをExcelで保存",
        data=excel_bytes_from_state(),
        file_name="旅ゲームメーカー旅行データ.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        key="download_trip_excel",
    )
    st.caption("Excelで予定・予算を自由に編集できます。編集後は右側から読み込んでください。")

with excel_load_col:
    excel_uploaded = st.file_uploader(
        "編集したExcelを読み込む",
        type=["xlsx"],
        key="trip_excel_uploader",
    )
    if excel_uploaded is not None and st.button(
        "このExcelを画面へ反映",
        type="primary",
        use_container_width=True,
        key="apply_trip_excel",
    ):
        try:
            spot_count, registered_count = apply_excel_upload(excel_uploaded)
            st.success(f"Excelを読み込みました。予定{spot_count}件・登録スポット{registered_count}件を反映しました。")
            st.rerun()
        except Exception as exc:
            st.error(f"Excel読み込み失敗: {exc}")

with st.expander("旧JSONの保存・読み込み（移行用）"):
    json_save_col, json_load_col = st.columns([1, 1.4])
    with json_save_col:
        payload = current_state_payload()
        st.download_button(
            "JSONを保存",
            json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="tabigame_japan_realmap_data.json",
            mime="application/json",
            use_container_width=True,
            key="download_trip_json",
        )

    with json_load_col:
        uploaded = st.file_uploader("旧JSONを読み込む", type=["json"], key="legacy_json_uploader")
        if uploaded is not None and st.button(
            "このJSONを読み込む",
            use_container_width=True,
            key="apply_legacy_json",
        ):
            try:
                loaded = json.load(uploaded)
                if isinstance(loaded, dict) and "spots" in loaded:
                    st.session_state.spots = loaded["spots"]
                    st.session_state.trip_start = date.fromisoformat(loaded.get("trip_start", "2026-07-17"))
                    st.session_state.trip_days = int(loaded.get("trip_days", 4))
                    st.session_state.day_modes = loaded.get("day_modes", {})
                    st.session_state.map_region = loaded.get("map_region", loaded.get("selected_region", "沖縄"))
                    st.session_state.registered_places = loaded.get("registered_places", st.session_state.registered_places)
                    st.session_state.day_start_times = loaded.get("day_start_times", st.session_state.day_start_times)
                    st.session_state.budget_settings = loaded.get("budget_settings", st.session_state.budget_settings)
                    save_registered_places()
                elif isinstance(loaded, list):
                    st.session_state.spots = loaded
                else:
                    raise ValueError("未対応の保存形式です")
                ensure_ids()
                for _spot in st.session_state.spots:
                    spot_defaults(_spot)
                cleanup_duplicate_hotels()
                recalculate_all_days(reorder=False)
                auto_backup()
                st.success("JSONを読み込みました。")
                st.rerun()
            except Exception as exc:
                st.error(f"JSON読み込み失敗: {exc}")

st.markdown('<div class="navbar">', unsafe_allow_html=True)
n1, n2, n3, n4 = st.columns(4)
with n1:
    if st.button("🗓️ 旅程", use_container_width=True, key="button_1225_13"):
        go("旅程")
with n2:
    if st.button("🔎 全国検索", use_container_width=True, key="button_1228_14"):
        go("スポット検索")
with n3:
    if st.button("📍 近くを探す", use_container_width=True, key="button_1231_15"):
        go("近くを探す")
with n4:
    if st.button("🧰 便利機能", use_container_width=True, key="button_1234_16"):
        go("便利機能")
st.markdown("</div>", unsafe_allow_html=True)

st.caption("地図: OpenStreetMap / 経路: OSRM / 周辺検索: Overpass。Googleマップのリンクで最終確認できます。")
