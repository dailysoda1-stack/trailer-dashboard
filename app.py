import streamlit as st
import pandas as pd
import re
import json
import os
import hashlib

st.set_page_config(page_title="Trailer Dashboard", page_icon="🎬", layout="wide")

# ── Persistence ───────────────────────────────────────────────────────────────
DATA_DIR  = os.path.join(os.path.dirname(__file__), ".data")
CSV_CACHE = os.path.join(DATA_DIR, "csv_cache.json")
USER_DATA = os.path.join(DATA_DIR, "user_data.json")
os.makedirs(DATA_DIR, exist_ok=True)

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except: return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def video_key(item):
    url = item.get('video_url') or item.get('url') or item.get('webpage_url') or item.get('link') or item.get('youtube_url') or ''
    return hashlib.md5((url or item.get('title','')).encode()).hexdigest()[:12]

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

/* ── Card shell ── */
.vcard {
    background:#fff;
    border:1px solid #e5e5e5;
    border-radius:14px;
    overflow:hidden;
    box-shadow:0 1px 4px rgba(0,0,0,0.07);
    margin-bottom:18px;
    transition:box-shadow .15s;
}
.vcard:hover { box-shadow:0 6px 20px rgba(0,0,0,0.11); }
.vcard.is-saved    { border:2px solid #0095f6; }
.vcard.is-dup      { border:2px solid #f5a623; }

/* ── Thumbnail ── */
.vthumb {
    position:relative;
    width:100%;
    background:#000;
    overflow:hidden;
    cursor:pointer;
}
.vthumb img {
    width:100%; display:block;
    aspect-ratio:16/9; object-fit:cover;
    transition:transform .3s ease;
}
.vcard:hover .vthumb img { transform:scale(1.03); }
.vthumb-placeholder { width:100%; aspect-ratio:16/9; background:linear-gradient(135deg,#1a1a2e,#16213e); }

/* Play overlay */
.play-overlay {
    position:absolute; inset:0;
    display:flex; align-items:center; justify-content:center;
    background:rgba(0,0,0,0.18);
    opacity:0; transition:opacity .2s;
}
.vcard:hover .play-overlay { opacity:1; }
.play-circle {
    width:52px; height:52px; border-radius:50%;
    background:rgba(255,255,255,0.88);
    display:flex; align-items:center; justify-content:center;
    box-shadow:0 2px 12px rgba(0,0,0,0.25);
}
.play-arrow {
    width:0; height:0;
    border-top:10px solid transparent;
    border-bottom:10px solid transparent;
    border-left:18px solid #e00;
    margin-left:4px;
}

/* Badges on thumbnail */
.tbadge-cat {
    position:absolute; top:10px; left:10px;
    background:rgba(0,0,0,0.72); backdrop-filter:blur(4px);
    color:#fff; font-size:10px; font-weight:700;
    border-radius:5px; padding:3px 8px;
    letter-spacing:.07em; text-transform:uppercase;
}
.tbadge-dur {
    position:absolute; bottom:8px; right:8px;
    background:#cc0000; color:#fff;
    font-size:11px; font-weight:700;
    border-radius:4px; padding:2px 7px;
    letter-spacing:.02em;
}
.tbadge-dup {
    position:absolute; top:10px; right:10px;
    background:#f5a623; color:#fff;
    font-size:10px; font-weight:700;
    border-radius:5px; padding:3px 8px;
    letter-spacing:.05em; text-transform:uppercase;
}

/* ── Card body ── */
.vbody { padding:14px 16px 0 16px; }

.vmeta { display:flex; align-items:flex-start; gap:10px; margin-bottom:10px; }
.vavatar {
    width:34px; height:34px; border-radius:50%; flex-shrink:0;
    background:linear-gradient(135deg,#833ab4,#fd1d1d,#fcb045);
    display:flex; align-items:center; justify-content:center;
    color:#fff; font-size:13px; font-weight:700;
}
.vtitle {
    font-size:13.5px; font-weight:600; color:#111;
    line-height:1.35; margin:0 0 3px 0;
    display:-webkit-box; -webkit-line-clamp:2;
    -webkit-box-orient:vertical; overflow:hidden;
}
.vchannel { font-size:12px; color:#737373; font-weight:400; }

/* Tags row */
.vtags { margin:0 0 8px 0; }
.vtag {
    display:inline-block; font-size:11px; font-weight:500;
    color:#0095f6; background:rgba(0,149,246,.1);
    border-radius:20px; padding:2px 10px; margin:2px 4px 2px 0;
}
.vtag-custom {
    display:inline-block; font-size:11px; font-weight:500;
    color:#23a55a; background:rgba(35,165,90,.1);
    border-radius:20px; padding:2px 10px; margin:2px 4px 2px 0;
}
.vtag-mtype {
    display:inline-block; font-size:11px; font-weight:600;
    color:#7c3aed; background:rgba(124,58,237,.09);
    border-radius:20px; padding:2px 10px; margin:2px 4px 2px 0;
}

/* Description */
.vdesc {
    font-size:12px; line-height:1.55; color:#737373;
    display:-webkit-box; -webkit-line-clamp:3;
    -webkit-box-orient:vertical; overflow:hidden;
    margin:0 0 12px 0;
}

/* ── Action bar ── */
.vactions {
    display:flex; align-items:center; gap:0;
    border-top:1px solid #f0f0f0;
    padding:0;
}
.vbtn {
    flex:1; display:inline-flex; align-items:center; justify-content:center;
    gap:5px; border:none; background:none;
    color:#555; font-size:12px; font-weight:600;
    font-family:inherit; cursor:pointer;
    padding:10px 6px; transition:background .12s, color .12s;
    border-radius:0;
}
.vbtn:hover { background:#f7f7f7; color:#111; }
.vbtn.saved { color:#0095f6; }
.vbtn svg { flex-shrink:0; }
.vbtn-divider { width:1px; background:#f0f0f0; height:20px; flex-shrink:0; }
.vbtn-watch { color:#e00; }
.vbtn-watch:hover { color:#cc0000; background:#fff5f5; }

/* ── Stats pills ── */
.stat-pill {
    display:inline-flex; align-items:center; gap:8px;
    background:#fff; border:1px solid #efefef;
    border-radius:100px; padding:8px 18px;
    margin-right:8px; margin-bottom:8px;
}
.stat-num { font-size:18px; font-weight:700; color:#0a0a0a; }
.stat-lbl { font-size:12px; color:#737373; font-weight:500; }
.dot { width:8px;height:8px;border-radius:50%;display:inline-block; }
.dot-blue{background:#0095f6} .dot-gray{background:#a8a8a8}
.dot-gold{background:#f5a623} .dot-red{background:#ed4956}
.dot-green{background:#23a55a}

#MainMenu{visibility:hidden} footer{visibility:hidden} .stDeployButton{display:none}
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def normalize_key(k):
    return re.sub(r'\s+','_', str(k or '').strip().lower().lstrip('\ufeff'))

def get_video_id(url):
    if not url: return ""
    m = re.search(r'[?&]v=([^&]+)', url)
    if m: return m.group(1)
    s = re.search(r'youtu\.be/([^?&]+)', url)
    return s.group(1) if s else ""

def extract_channel(title):
    if not title: return "YouTube Video"
    if " | " in title:
        parts = title.split(" | ")
        return re.sub(r'Official Trailer.*','',parts[-1],flags=re.I).strip()
    m = re.search(r'\(([^)]+)\)', title)
    return m.group(1) if m else "YouTube Video"

def parse_date(val):
    if not val: return pd.NaT
    s = str(val).strip()
    m = re.match(r'^(\d{4})(\d{2})(\d{2})$', s)
    if m: s = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    try: return pd.to_datetime(s)
    except: return pd.NaT

def format_duration(val):
    if not val: return ""
    try:
        secs = int(float(str(val).strip()))
        if secs <= 0: return ""
        h, rem = divmod(secs, 3600)
        m, s   = divmod(rem, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
    except:
        return str(val)[:8] if val else ""

def find_duplicates(records):
    seen_urls, seen_titles, dup_keys = {}, {}, set()
    for r in records:
        k = video_key(r)
        url   = r.get('video_url') or r.get('url') or r.get('webpage_url') or ''
        title = (r.get('title') or '').strip().lower()
        if url and url in seen_urls:   dup_keys.add(k); dup_keys.add(seen_urls[url])
        elif url:                       seen_urls[url] = k
        if title and title in seen_titles: dup_keys.add(k); dup_keys.add(seen_titles[title])
        elif title:                        seen_titles[title] = k
    return dup_keys

def esc(v):
    return str(v or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

# ── Session state ─────────────────────────────────────────────────────────────
if 'user_data' not in st.session_state:
    st.session_state.user_data = load_json(USER_DATA, {"watchlist":[], "custom_tags":{}, "media_types":{}})
if 'csv_cache'  not in st.session_state:
    st.session_state.csv_cache = load_json(CSV_CACHE, {})
if 'playing'    not in st.session_state: st.session_state.playing = None
if 'page'       not in st.session_state: st.session_state.page    = 0

def save_user(): save_json(USER_DATA, st.session_state.user_data)

def toggle_watchlist(k):
    wl = st.session_state.user_data["watchlist"]
    if k in wl: wl.remove(k)
    else: wl.append(k)
    save_user()

def set_media_type(k, v):
    st.session_state.user_data["media_types"][k] = v; save_user()

def add_custom_tag(k, tag):
    tags = st.session_state.user_data["custom_tags"].get(k, [])
    if tag and tag not in tags: tags.append(tag)
    st.session_state.user_data["custom_tags"][k] = tags; save_user()

def remove_custom_tag(k, tag):
    tags = st.session_state.user_data["custom_tags"].get(k, [])
    if tag in tags: tags.remove(tag)
    st.session_state.user_data["custom_tags"][k] = tags; save_user()

MEDIA_TYPES = ["Movie","TV Show","Streaming","Short Film","Documentary","Anime","Other"]

# ── Header + Upload ───────────────────────────────────────────────────────────
st.markdown("## 🎬 Trailer Dashboard")

uploaded_files = st.file_uploader("Upload CSV", type=["csv"], accept_multiple_files=True, label_visibility="collapsed")

cache = st.session_state.csv_cache
if uploaded_files:
    for f in uploaded_files:
        try:
            content = f.read().decode("utf-8", errors="replace")
            df = pd.read_csv(pd.io.common.StringIO(content), dtype=str).fillna('')
            df.columns = [normalize_key(c) for c in df.columns]
            tc = 'title' if 'title' in df.columns else df.columns[0]
            uc = next((c for c in ['video_url','url','webpage_url'] if c in df.columns), None)
            mask = df[tc].str.strip().ne('')
            if uc: mask = mask | df[uc].str.strip().ne('')
            cache[f.name] = df[mask].to_dict('records')
        except Exception as e:
            st.warning(f"Could not read {f.name}: {e}")
    save_json(CSV_CACHE, cache)
    st.session_state.csv_cache = cache

if not cache:
    st.markdown("""
    <div style="text-align:center;padding:80px 20px;">
      <div style="font-size:52px;margin-bottom:16px;">🎬</div>
      <div style="font-size:18px;font-weight:600;color:#555;margin-bottom:8px;">No trailers yet</div>
      <div style="font-size:14px;color:#aaa;">Upload your YouTube CSV file above to get started</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

with st.expander(f"📂  {len(cache)} file(s) loaded", expanded=False):
    for fname in list(cache.keys()):
        c1, c2 = st.columns([6,1])
        c1.markdown(f"**{fname}** — {len(cache[fname])} rows")
        if c2.button("Remove", key=f"rm_{fname}"):
            del cache[fname]; save_json(CSV_CACHE, cache)
            st.session_state.csv_cache = cache; st.rerun()

records_all = [r for rows in cache.values() for r in rows]
dup_keys    = find_duplicates(records_all)

# ── Filters ───────────────────────────────────────────────────────────────────
c1,c2,c3,c4,c5,c6 = st.columns([3,1.4,1.4,1.3,1.3,1])
with c1: search      = st.text_input("Search", placeholder="Search title, tags, description…", label_visibility="collapsed")
with c2:
    cats = sorted(set(r.get('category') or '' for r in records_all if r.get('category')))
    cat_filter = st.selectbox("Category", ["All categories"]+cats, label_visibility="collapsed")
with c3: mtype_filter = st.selectbox("Type", ["All types"]+MEDIA_TYPES, label_visibility="collapsed")
with c4: view_mode   = st.selectbox("View", ["All videos","Watchlist only","Duplicates only"], label_visibility="collapsed")
with c5: sort_by     = st.selectbox("Sort", ["Date: Newest","Date: Oldest","Title A–Z","Category A–Z"], label_visibility="collapsed")
with c6:
    cols_map = {"3":3,"2":2,"4":4,"5":5}
    layout   = st.selectbox("Cols", ["3","2","4","5"], label_visibility="collapsed")

per_page = st.select_slider("Videos per page", options=[12,24,36,48,60], value=24)

# ── Filter & sort ─────────────────────────────────────────────────────────────
wl = st.session_state.user_data["watchlist"]
mt = st.session_state.user_data["media_types"]

filtered = records_all
if search:
    q = search.lower()
    filtered = [r for r in filtered if q in ' '.join([r.get('title',''),r.get('category',''),r.get('description',''),r.get('tags','')]).lower()]
if cat_filter != "All categories":
    filtered = [r for r in filtered if (r.get('category') or '') == cat_filter]
if mtype_filter != "All types":
    filtered = [r for r in filtered if mt.get(video_key(r)) == mtype_filter]
if view_mode == "Watchlist only":
    filtered = [r for r in filtered if video_key(r) in wl]
elif view_mode == "Duplicates only":
    filtered = [r for r in filtered if video_key(r) in dup_keys]

if   sort_by == "Date: Newest":  filtered.sort(key=lambda r: parse_date(r.get('upload_date') or r.get('date') or ''), reverse=True)
elif sort_by == "Date: Oldest":  filtered.sort(key=lambda r: parse_date(r.get('upload_date') or r.get('date') or ''))
elif sort_by == "Title A–Z":     filtered.sort(key=lambda r: r.get('title','').lower())
elif sort_by == "Category A–Z":  filtered.sort(key=lambda r: r.get('category','').lower())

# ── Stats ─────────────────────────────────────────────────────────────────────
cat_count = len(set(r.get('category') for r in records_all if r.get('category')))
st.markdown(f"""
<div style="margin:12px 0 20px;">
  <span class="stat-pill"><span class="dot dot-blue" style="margin-right:6px"></span><span class="stat-num">{len(records_all)}</span>&nbsp;<span class="stat-lbl">Total</span></span>
  <span class="stat-pill"><span class="dot dot-gray" style="margin-right:6px"></span><span class="stat-num">{len(filtered)}</span>&nbsp;<span class="stat-lbl">Visible</span></span>
  <span class="stat-pill"><span class="dot dot-gold" style="margin-right:6px"></span><span class="stat-num">{cat_count}</span>&nbsp;<span class="stat-lbl">Categories</span></span>
  <span class="stat-pill"><span class="dot dot-blue" style="margin-right:6px"></span><span class="stat-num">{len(wl)}</span>&nbsp;<span class="stat-lbl">Watchlist</span></span>
  <span class="stat-pill"><span class="dot dot-red" style="margin-right:6px"></span><span class="stat-num">{len(dup_keys)}</span>&nbsp;<span class="stat-lbl">Duplicates</span></span>
</div>""", unsafe_allow_html=True)

# ── Pagination ────────────────────────────────────────────────────────────────
total_pages = max(1, -(-len(filtered) // per_page))
if st.session_state.page >= total_pages: st.session_state.page = 0
page_items = filtered[st.session_state.page*per_page : (st.session_state.page+1)*per_page]

def pagination_controls(suffix=""):
    if total_pages <= 1: return
    p1,p2,p3 = st.columns([1,4,1])
    with p1:
        if st.button("← Prev", key=f"prev{suffix}", disabled=st.session_state.page==0):
            st.session_state.page -= 1; st.rerun()
    with p2:
        st.markdown(f"<div style='text-align:center;padding:8px 0;font-size:13px;color:#888;'>Page {st.session_state.page+1} of {total_pages} · {len(filtered)} videos</div>", unsafe_allow_html=True)
    with p3:
        if st.button("Next →", key=f"next{suffix}", disabled=st.session_state.page>=total_pages-1):
            st.session_state.page += 1; st.rerun()

pagination_controls("_top")

# ── Grid ──────────────────────────────────────────────────────────────────────
if not page_items:
    st.info("No videos match your current filters.")
else:
    num_cols  = cols_map[layout]
    grid_rows = [page_items[i:i+num_cols] for i in range(0, len(page_items), num_cols)]

    for row in grid_rows:
        cols = st.columns(num_cols)
        for col, item in zip(cols, row):
            with col:
                key        = video_key(item)
                url        = item.get('video_url') or item.get('url') or item.get('webpage_url') or item.get('link') or item.get('youtube_url') or ''
                video_id   = get_video_id(url)
                thumbnail  = item.get('thumbnail') or (f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else "")
                title      = item.get('title') or 'Untitled'
                channel    = extract_channel(title)
                initial    = channel[0].upper() if channel else "Y"
                category   = item.get('category') or ''
                tags       = [t.strip() for t in str(item.get('tags') or '').split(',') if t.strip()][:3]
                desc       = item.get('description') or ''
                duration   = format_duration(item.get('duration') or item.get('duration_string') or '')
                is_saved   = key in wl
                is_dup     = key in dup_keys
                cur_mtype  = mt.get(key, '')
                ctags      = st.session_state.user_data["custom_tags"].get(key, [])
                is_playing = st.session_state.playing == key

                card_cls  = "vcard" + (" is-saved" if is_saved else " is-dup" if is_dup else "")
                thumb_html = f'<img src="{esc(thumbnail)}" alt="{esc(title)}" loading="lazy"/>' if thumbnail else '<div class="vthumb-placeholder"></div>'
                cat_badge  = f'<span class="tbadge-cat">{esc(category)}</span>' if category else ''
                dur_badge  = f'<span class="tbadge-dur">{esc(duration)}</span>' if duration else ''
                dup_badge  = '<span class="tbadge-dup">Duplicate</span>' if is_dup else ''
                tags_html  = ''.join(f'<span class="vtag">{esc(t)}</span>' for t in tags)
                ctags_html = ''.join(f'<span class="vtag-custom">🏷 {esc(t)}</span>' for t in ctags)
                mtype_html = f'<span class="vtag-mtype">{esc(cur_mtype)}</span>' if cur_mtype else ''
                desc_html  = f'<div class="vdesc">{esc(desc[:220])}</div>' if desc else ''

                # Save icon SVG
                save_icon = '<svg width="14" height="14" viewBox="0 0 24 24" fill="%s" stroke="%s" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'
                save_svg   = save_icon % ("#0095f6","#0095f6") if is_saved else save_icon % ("none","#888")
                save_label = "Saved" if is_saved else "Save"

                st.markdown(f"""
                <div class="{card_cls}">
                  <div class="vthumb">
                    {thumb_html}
                    <div class="play-overlay">
                      <div class="play-circle"><div class="play-arrow"></div></div>
                    </div>
                    {cat_badge}{dur_badge}{dup_badge}
                  </div>
                  <div class="vbody">
                    <div class="vmeta">
                      <div class="vavatar">{esc(initial)}</div>
                      <div style="flex:1;min-width:0;">
                        <div class="vtitle" title="{esc(title)}">{esc(title)}</div>
                        <div class="vchannel">{esc(channel)}</div>
                      </div>
                    </div>
                    <div class="vtags">{tags_html}{ctags_html}{mtype_html}</div>
                    {desc_html}
                  </div>
                  <div class="vactions">
                    <button class="vbtn" onclick="void(0)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
                      Copy
                    </button>
                    <div class="vbtn-divider"></div>
                    <a class="vbtn vbtn-watch" href="{esc(url)}" target="_blank" rel="noopener" style="text-decoration:none;{'display:none' if not url else ''}">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8" fill="currentColor" stroke="none"/></svg>
                      Watch
                    </a>
                    <div class="vbtn-divider"></div>
                    <button class="vbtn {'saved' if is_saved else ''}" onclick="void(0)">
                      {save_svg} {save_label}
                    </button>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # Inline player (triggered by Streamlit button below card)
                if is_playing and video_id:
                    st.video(f"https://www.youtube.com/watch?v={video_id}")

                # Functional buttons (Streamlit handles interactivity)
                b1, b2, b3 = st.columns(3)
                with b1:
                    play_lbl = "⏹ Close" if is_playing else "▶ Play here"
                    if st.button(play_lbl, key=f"play_{key}", use_container_width=True):
                        st.session_state.playing = None if is_playing else key; st.rerun()
                with b2:
                    save_lbl = "★ Saved" if is_saved else "☆ Save"
                    if st.button(save_lbl, key=f"save_{key}", use_container_width=True):
                        toggle_watchlist(key); st.rerun()
                with b3:
                    mtype_opts = [""]+MEDIA_TYPES
                    cur_idx    = mtype_opts.index(cur_mtype) if cur_mtype in mtype_opts else 0
                    new_mtype  = st.selectbox("Type", mtype_opts, index=cur_idx, key=f"mt_{key}", label_visibility="collapsed")
                    if new_mtype != cur_mtype: set_media_type(key, new_mtype); st.rerun()

                # Custom tag expander
                with st.expander("🏷 Add tag", expanded=False):
                    new_tag = st.text_input("Tag", key=f"ti_{key}", placeholder="e.g. Must Watch", label_visibility="collapsed")
                    if st.button("Add", key=f"ta_{key}") and new_tag.strip():
                        add_custom_tag(key, new_tag.strip()); st.rerun()
                    for ct in ctags:
                        tc1,tc2 = st.columns([4,1])
                        tc1.markdown(f"`{ct}`")
                        if tc2.button("✕", key=f"td_{key}_{ct}"):
                            remove_custom_tag(key, ct); st.rerun()

st.markdown("---")
pagination_controls("_bot")
