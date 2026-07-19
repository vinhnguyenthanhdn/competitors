#!/usr/bin/env python3
"""
Rebuilds data/tours-data.js from every data/raw/cards-*.json file.

Each cards-*.json file is a JSON array of "normalized card" objects:
  { platform, color, title, img, href, price, duration, rating, cardText }
(price/duration/rating/img/cardText may be null — see scripts/README.md for
where each field comes from per platform.)

This script does NOT scrape. To add new tours:
  1. Scrape a listing page with the matching scripts/extractors/<platform>.js
     snippet via `agent-browser eval --stdin`.
  2. Turn the raw result into the normalized card shape above (one JSON
     object per tour) and save it as data/raw/cards-<description>.json.
  3. Re-run this script: `python3 scripts/build_unified_data.py`.
  4. Reload the two HTML pages — no HTML editing needed, they read
     data/tours-data.js at runtime.

Dedup key is (platform, title, href) — NOT href alone: guide-profile
platforms (ShowAround, Tubudd, GoWithGuide) link every profile to the same
generic listing-page URL, so href by itself collapses distinct guides into
one. A tour already present under the same key is kept (first file wins,
by glob/sort order) rather than duplicated.
"""
import glob
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, 'data', 'raw')
OUT_FILE = os.path.join(ROOT, 'data', 'tours-data.js')

# ShowAround/Tubudd are pure guide-profile marketplaces (every card is an
# hourly guide, not a fixed-itinerary tour) — always bucket them into the
# guide-rate group regardless of what their profile blurb/title says.
# GoWithGuide is a hybrid: 37 fixed-itinerary packaged tours (classify normally)
# + 8 guide profiles (title suffixed " (guide)" by build script when scraped) —
# only the guide-profile cards get force-bucketed there, see is_guide_profile().
GUIDE_PROFILE_PLATFORMS = {'ShowAround', 'Tubudd'}


def is_guide_profile(card):
    return card['platform'] in GUIDE_PROFILE_PLATFORMS or card['title'].endswith(' (guide)')

GROUP_ORDER = [
    "Thuê HDV theo giờ / gói giờ (không lịch trình cố định)",
    "Bà Nà Hills / Cầu Vàng",
    "Ngũ Hành Sơn / Marble & Monkey Mountain",
    "Mỹ Sơn Sanctuary",
    "Huế / Hải Vân Pass",
    "Hội An (phố cổ, thuyền, đèn lồng)",
    "Food tour / Ẩm thực / Cooking class",
    "Thác nước / Trekking / Rafting / Outdoor",
    "Tour thành phố Đà Nẵng / Highlights chung",
    "Khác / Dịch vụ đặc thù",
]


def classify(title_html):
    """Destination-group keyword classifier, priority order top -> bottom.
    Order matters: e.g. a title mentioning both Ba Na and Hoi An lands in
    Ba Na Hills (more specific/valuable destination wins over Hoi An)."""
    t = html.unescape(title_html).lower()
    if 'my son' in t or 'mỹ sơn' in t:
        return "Mỹ Sơn Sanctuary"
    if 'hue' in t or 'huế' in t or 'hai van' in t or 'hải vân' in t:
        return "Huế / Hải Vân Pass"
    if 'ba na' in t or 'bana' in t or 'golden bridge' in t or 'cầu vàng' in t or 'cable car' in t:
        return "Bà Nà Hills / Cầu Vàng"
    if 'marble' in t or 'monkey mountain' in t or 'am phu' in t or 'lady buddha' in t or 'son tra' in t or 'ngu hanh son' in t:
        return "Ngũ Hành Sơn / Marble & Monkey Mountain"
    if 'hoi an' in t or 'hội an' in t or 'lantern' in t or 'basket boat' in t or 'tra que' in t or 'eco village' in t:
        return "Hội An (phố cổ, thuyền, đèn lồng)"
    if any(k in t for k in ['food', 'cooking', 'coffee', 'cocktail', 'culinary', 'tasting', 'cuisine', 'street food']) or ('market' in t and 'night market' not in t):
        return "Food tour / Ẩm thực / Cooking class"
    if any(k in t for k in ['waterfall', 'trek', 'rafting', 'jungle', 'surf', 'diving', 'snorkel', 'kayak', 'jeep', 'motorbike', 'easy rider', 'wildlife']):
        return "Thác nước / Trekking / Rafting / Outdoor"
    if any(k in t for k in ['city tour', 'sightseeing', 'highlight', 'dragon bridge', 'cruise', 'river', 'night market', 'museum', 'photo']):
        return "Tour thành phố Đà Nẵng / Highlights chung"
    return "Khác / Dịch vụ đặc thù"


def parse_price(price_text, platform):
    """Returns (vnd:int|None, forced_unit:str|None). vnd=0 means free/tip-based."""
    if not price_text:
        return None, None
    p = price_text.strip()
    if p.lower() in ('free', 'miễn phí'):
        return 0, ('giờ' if platform in GUIDE_PROFILE_PLATFORMS else None)
    m = re.search(r'₫\s*([\d,\.]+)', p)
    if m:
        return int(re.sub(r'[,\.]', '', m.group(1))), None
    m = re.search(r'\$\s*([\d,\.]+)', p)
    if m:
        return int(float(re.sub(r',', '', m.group(1))) * 26000), None
    m = re.search(r'€\s*([\d,\.]+)', p)
    if m:
        return int(float(re.sub(r',', '', m.group(1))) * 30000), None
    return None, None


def guess_unit(card_text, platform, vnd):
    if vnd == 0:
        return 'giờ'
    ct = (card_text or '').lower()
    if '/nhóm' in (card_text or '') or 'per group' in ct:
        return 'nhóm'
    if '/khách' in (card_text or '') or 'per guest' in ct or 'per person' in ct:
        return 'khách'
    if platform in ('ToursByLocals', 'Viator', 'GetYourGuide', 'Klook'):
        return 'tour'
    return None


def load_cards():
    files = sorted(glob.glob(os.path.join(RAW_DIR, 'cards-*.json')))
    if not files:
        raise SystemExit(f'No data/raw/cards-*.json files found in {RAW_DIR}')
    seen = {}
    for fpath in files:
        items = json.load(open(fpath, encoding='utf-8'))
        for c in items:
            key = (c['platform'], c['title'], c['href'])
            if key not in seen:
                seen[key] = c
    print(f'Loaded {len(files)} cards-*.json file(s), {len(seen)} unique tours')
    return list(seen.values())


def enrich(card):
    vnd, forced_unit = parse_price(card.get('price'), card['platform'])
    if is_guide_profile(card):
        unit = 'giờ'
        group = GROUP_ORDER[0]
    elif vnd is not None:
        unit = forced_unit or guess_unit(card.get('cardText'), card['platform'], vnd)
        group = classify(card['title'])
    else:
        unit = None
        group = None
    return {**card, 'vnd': vnd, 'unit': unit, 'group': group}


def main():
    cards = [enrich(c) for c in load_cards()]
    cards.sort(key=lambda c: (c['platform'], c['title']))

    priced = sum(1 for c in cards if c['vnd'] is not None)
    print(f'{len(cards)} total tours, {priced} with a readable price, {len(cards) - priced} without')

    js = 'const TOURS_DATA = ' + json.dumps(cards, ensure_ascii=False, indent=1) + ';\n'
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    open(OUT_FILE, 'w', encoding='utf-8').write(js)
    print(f'Wrote {OUT_FILE}')


if __name__ == '__main__':
    main()
