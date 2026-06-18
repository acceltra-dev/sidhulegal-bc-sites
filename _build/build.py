#!/usr/bin/env python3
"""
Build Sidhu BC city sites from one Surrey-based template.
- make_template(): turns the live Surrey page into _build/template.html with {{TOKENS}}
- generate(slug): writes <dir>/index.html for a city from CITIES data
Layout always = Surrey's. Only city-specific fields change.
"""
import re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SURREY = os.path.join(ROOT, "sidhulegal-surrey", "index.html")
TPL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html")

# master list (order = display order); name, slug, dir
CITIES_INDEX = [
    ("Surrey", "surrey", "sidhulegal-surrey"),
    ("Vancouver", "vancouver", "sidhulegal-vancouver"),
    ("Burnaby", "burnaby", "sidhulegal-burnaby"),
    ("Richmond", "richmond", "sidhulegal-richmond"),
    ("Coquitlam", "coquitlam", "sidhulegal-coquitlam"),
    ("Langley", "langley", "sidhulegal-langley"),
    ("Abbotsford", "abbotsford", "sidhulegal-abbotsford"),
    ("Delta", "delta", "sidhulegal-delta"),
    ("Maple Ridge", "maple-ridge", "sidhulegal-mapleridge"),
    ("New Westminster", "new-westminster", "sidhulegal-newwestminster"),
]

# per-city content. Fill local_* with REAL local facts. (Pilot: New West complete.)
CITIES = {
    "new-westminster": {
        "name": "New Westminster", "slug": "new-westminster", "dir": "sidhulegal-newwestminster",
        "meta_desc": "New Westminster's personal injury lawyers since 2013. Sidhu Legal fights ICBC and wins maximum compensation. Free consultation. No fee unless you win. Call (604) 907-3632.",
        "og_desc": "New Westminster's personal injury and ICBC lawyers since 2013. Free consultation, no fee unless you win.",
        "local_intro": "New Westminster is one of BC's oldest cities, a dense riverfront hub where the Pattullo and Queensborough bridges, Columbia Street, McBride Boulevard and the Highway 1 interchange funnel heavy traffic through tight corridors. If you have been hurt in or around New Westminster, here is the local context that shapes your claim.",
        "local_roads": "The Pattullo and Queensborough bridges, Columbia Street, McBride Boulevard, Stewardson Way, Brunette Avenue and the Highway 1 (Trans-Canada) interchange carry the city's heaviest traffic and are frequent collision points. Congestion through the Sapperton and Uptown corridors and wet conditions on the bridge approaches are common factors.",
        "local_hospital": "Serious injuries in New Westminster are treated at Royal Columbian Hospital, one of BC's busiest trauma centres. Keep every medical record and receipt, they are central to proving your claim.",
        "local_road_short": "the Pattullo Bridge", "local_area": "Sapperton",
    },
}


def make_template():
    src = open(SURREY, encoding="utf-8").read()
    t = src

    # 1. master city variable
    t = t.replace('window._sidhuCity="Surrey"', 'window._sidhuCity="{{CITY}}"')

    # 2. meta description + og description
    t = re.sub(r'(<meta name="description" content=")(.*?)(">)', r'\1{{META_DESC}}\3', t, count=1)
    t = re.sub(r'(<meta property="og:description" content=")(.*?)(">)', r'\1{{OG_DESC}}\3', t, count=1)

    # 3. self-referential URL slug (canonical / og:url / schema url) -- Surrey isn't in its own link lists
    t = t.replace('surrey-personal-injury-lawyer', '{{SLUG}}-personal-injury-lawyer')

    # 4. local-knowledge section: swap city-specific inner content for tokens
    t = re.sub(r'(data-lx="lx_intro"[^>]*>)(.*?)(</p>)', r'\1{{LOCAL_INTRO}}\3', t, count=1, flags=re.S)
    t = re.sub(r'(data-lx="lx_pa"[^>]*>)(.*?)(</p>)',    r'\1{{LOCAL_ROADS}}\3', t, count=1, flags=re.S)
    t = re.sub(r'(data-lx="lx_pc"[^>]*>)(.*?)(</p>)',    r'\1{{LOCAL_HOSPITAL}}\3', t, count=1, flags=re.S)
    t = re.sub(r'(data-lx="lx_h2"[^>]*>)(.*?)(</h2>)',   r'\1Injury &amp; ICBC Claims in {{CITY}}: What to Know\3', t, count=1, flags=re.S)
    t = re.sub(r'(data-lx="lx_h3a"[^>]*>)(.*?)(</h3>)',  r'\1Where {{CITY}} crashes happen\3', t, count=1, flags=re.S)

    # 4b. local-fact values inside EVERY language's translation object -> city tokens (JS-string context)
    jsval = lambda key, tok: re.sub(key + r":'(?:\\.|[^'])*'", key + ":'" + tok + "'", t)
    t = jsval("lx_pa", "{{LOCAL_ROADS_JS}}")
    t = jsval("lx_pc", "{{LOCAL_HOSPITAL_JS}}")
    t = jsval("lx_intro", "{{LOCAL_INTRO_JS}}")
    t = jsval("lx_h2", "Injury & ICBC Claims in {{CITY}}: What to Know")
    t = jsval("lx_h3a", "Where {{CITY}} crashes happen")

    # 4c. city landmarks hardcoded in testimonials -> tokens
    t = t.replace("After my accident on King George Blvd", "After my accident on {{LOCAL_ROAD_SHORT}}")
    t = t.replace("near Guildford", "near {{LOCAL_AREA}}")

    # 5. tokenize the few literal-"Surrey" values inside the _ST translation table -> {city} (runtime localizes)
    out = []
    for line in t.split("\n"):
        if "_ST[" in line and "Surrey" in line:
            line = line.replace("Surrey", "{city}")
        out.append(line)
    t = "\n".join(out)

    # 6b. blanket-replace the remaining city NAME -> {{CITY}}, protecting firm-HQ lines
    PROTECT = ("13737", "Suite 1104", "addressLocality", "V3V 0C6",
               "output=embed", "maps/dir", "maps/search")
    HQ = ("based in Surrey", "based right here in Surrey", "right here in Surrey", "Based right here in Surrey")
    out2 = []
    for line in t.split("\n"):
        if any(p in line for p in PROTECT) or line.strip() == '"Surrey",':
            out2.append(line); continue
        # preserve HQ "based in Surrey" truth, tokenize the rest of the line
        holders = {}
        for i, h in enumerate(HQ):
            if h in line:
                key = f"\x00HQ{i}\x00"; line = line.replace(h, key); holders[key] = h
        line = line.replace("Serving Surrey", "Serving {{CITY}}")
        line = line.replace("Surrey", "{{CITY}}")
        for key, h in holders.items():
            line = line.replace(key, h)
        out2.append(line)
    t = "\n".join(out2)

    # 6. nearby-city link lists -> tokens (generated per city, excluding self)
    t = re.sub(r'(?:\s*<a href="https://sidhulegal\.com/[a-z-]+-personal-injury-lawyer/" class="serve-link">[^<]+</a>)+',
               '\n      {{SERVE_LINKS}}', t, count=1)
    t = re.sub(r'(?:\s*<a href="https://sidhulegal\.com/[a-z-]+-personal-injury-lawyer/"[^>]*>Personal Injury Lawyer [^<]+</a>)+',
               '\n        {{NETWORK_LINKS}}', t, count=1)

    open(TPL, "w", encoding="utf-8").write(t)
    leftover = t.count("Surrey")
    print(f"template.html written. tokens present:",
          all(tok in t for tok in ["{{CITY}}","{{SLUG}}","{{META_DESC}}","{{LOCAL_ROADS}}","{{SERVE_LINKS}}","{{NETWORK_LINKS}}"]))
    print(f"residual 'Surrey' occurrences in template (should be only firm address/HQ): {leftover}")
    for i,l in enumerate(t.split('\n'),1):
        if 'Surrey' in l:
            print(f"   L{i}: {l.strip()[:90]}")


def serve_links(slug):
    return "\n      ".join(
        f'<a href="https://sidhulegal.com/{s}-personal-injury-lawyer/" class="serve-link">{n}</a>'
        for n, s, _ in CITIES_INDEX if s != slug)

def network_links(slug):
    return "\n        ".join(
        f'<a href="https://sidhulegal.com/{s}-personal-injury-lawyer/" style="color:rgba(255,255,255,0.55);text-decoration:none;font-size:0.8rem">Personal Injury Lawyer {n}</a>'
        for n, s, _ in CITIES_INDEX if s != slug)


def generate(slug, dry=True):
    c = CITIES[slug]
    t = open(TPL, encoding="utf-8").read()
    jsesc = lambda s: s.replace("\\", "\\\\").replace("'", "\\'")
    # JS-escaped variants first (their token names are supersets, so order matters)
    js_repl = {
        "{{LOCAL_INTRO_JS}}": jsesc(c["local_intro"]),
        "{{LOCAL_ROADS_JS}}": jsesc(c["local_roads"]),
        "{{LOCAL_HOSPITAL_JS}}": jsesc(c["local_hospital"]),
    }
    repl = {
        "{{CITY}}": c["name"], "{{SLUG}}": c["slug"],
        "{{META_DESC}}": c["meta_desc"], "{{OG_DESC}}": c["og_desc"],
        "{{LOCAL_INTRO}}": c["local_intro"], "{{LOCAL_ROADS}}": c["local_roads"],
        "{{LOCAL_HOSPITAL}}": c["local_hospital"],
        "{{LOCAL_ROAD_SHORT}}": c["local_road_short"], "{{LOCAL_AREA}}": c["local_area"],
        "{{SERVE_LINKS}}": serve_links(slug), "{{NETWORK_LINKS}}": network_links(slug),
    }
    for k, v in {**js_repl, **repl}.items():
        t = t.replace(k, v)
    assert "{{" not in t, "unfilled token remains: " + t[t.find("{{"):t.find("{{")+40]
    dest = os.path.join(ROOT, c["dir"], "index.new.html" if dry else "index.html")
    open(dest, "w", encoding="utf-8").write(t)
    print(f"generated -> {dest}")
    return dest


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "template"
    if cmd == "template":
        make_template()
    elif cmd == "gen":
        generate(sys.argv[2], dry=(len(sys.argv) < 4 or sys.argv[3] != "live"))
