import streamlit as st
import pandas as pd
import re
import json
import os
import hashlib

st.set_page_config(
    page_title="Trailer Dashboard",
    page_icon="🎬",
    layout="wide"
)

# ── Persistence paths ─────────────────────────────────────────────────────────
DATA_DIR   = os.path.join(os.path.dirname(__file__), ".data")
CSV_CACHE  = os.path.join(DATA_DIR, "csv_cache.json")
USER_DATA  = os.path.join(DATA_DIR, "user_data.json")
os.makedirs(DATA_DIR, exist_ok=True)

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def video_key(item):
    url = item.get('video_url') or item.get('url') or item.get('webpage_url') or item.get('link') or item.get('youtube_url') or ''
    return hashlib.md5((url or item.get('title','')).encode()).hexdigest()[:12]

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.card {
    background: #ffffff;
    border: 1px solid #efefef;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    margin-bottom: 16px;
}
.card.duplicate { border: 2px solid #f5a623; }
.card.saved     { border: 2px solid #0095f6; }

.thumb-wrap { position:relative; width:100%; background:#111; overflow:hidden; }
.thumb-wrap img { width:100%; display:block; aspect-ratio:16/9; object-fit:cover; }
.thumb-placeholder { width:100%; aspect-ratio:16/9; background:linear-gradient(135deg,#1a1a2e,#16213e); }

.cat-badge {
    position:absolute; top:8px; left:8px;
    background:rgba(0,0,0,0.65); backdrop-filter:blur(4px);
    color:#fff; font-size:10px; font-weight:700;
    border-radius:4px; padding:3px 7px;
    letter-spacing:.06em; text-transform:uppercase;
}
.dur-badge {
    position:absolute; bottom:8px; right:8px;
    background:rgba(0,0,0,0.75);
    color:#fff; font-size:11px; font-weight:600;
    border-radius:4px; padding:2px 6px;
}
.dup-badge {
    position:absolute; top:8px; right:8px;
    background:#f5a623; color:#fff;
    font-size:10px; font-weight:700;
    border-radius:4px; padding:3px 7px;
}

.card-body { padding:14px 16px 16px; }
.avatar {
    display:inline-flex; align-items:center; justify-content:center;
    width:32px; height:32px; border-radius:50%;
    background:linear-gradient(135deg,#833ab4,#fd1d1d,#fcb045);
    color:#fff; font-size:13px; font-weight:700;
    flex-shrink:0; margin-right:10px; vertical-align:middle;
}
.card-title {
    font-size:13px; font-weight:600; color:#0a0a0a;
    line-height:1.35; margin:0 0 2px 0;
    display:-webkit-box; -webkit-line-clamp:2;
    -webkit-box-orient:vertical; overflow:hidden;
}
.card-channel { font-size:12px; color:#737373; margin:0 0 8px 0; }

.tag {
    display:inline-block; font-size:11px; font-weight:500;
    color:#0095f6; background:rgba(0,149,246,.08);
    border-radius:4px; padding:2px 7px; margin:2px 3px 2px 0;
}
.tag-custom {
    display:inline-block; font-size:11px; font-weight:500;
    color:#23a55a; background:rgba(35,165,90,.1);
    border-radius:4px; padding:2px 7px; margin:2px 3px 2px 0;
}
.card-desc {
    font-size:12px; line-height:1.5; color:#737373;
    display:-webkit-box; -webkit-line-clamp:3;
    -webkit-box-orient:vertical; overflow:hidden;
    margin:8px 0 10px 0;
}

.stat-pill {
    display:inline-flex; align-items:center; gap:8px;
    background:#fff; border:1px solid #efefef;
    border-radius:100px; padding:8px 18px;
    margin-right:8px; margin-bottom:8px;
}
.stat-num { font-size:18px; font-weight:700; color:#0a0a0a; }
.stat-lbl { font-size:12px; color:#737373; font-weight:500; }
.dot { width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:2px; }
.dot-blue { background:#0095f6; }
.dot-gray { background:#a8a8a8; }
.dot-gold { background:#f5a623; }
.dot-red  { background:#ed4956; }
.dot-green{ background:#23a55a; }

#MainMenu{visibility:hidden;} footer{visibility:hidden;} .stDeployButton{display:none;}
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
        url = r.get('video_url') or r.get('url') or r.get('webpage_url') or ''
        title = (r.get('title') or '').strip().lower()
        if url and url in seen_urls:
            dup_keys.add(k); dup_keys.add(seen_urls[url])
        elif url:
            seen_urls[url] = k
        if title and title in seen_titles:
            dup_keys.add(k); dup_keys.add(seen_titles[title])
        elif title:
            seen_titles[title] = k
    return dup_keys

# ── Session state init ────────────────────────────────────────────────────────
if 'user_data' not in st.session_state:
    st.session_state.user_data = load_json(USER_DATA, {"watchlist": [], "custom_tags": {}, "media_types": {}})
if 'csv_cache' not in st.session_state:
    st.session_state.csv_cache = load_json(CSV_CACHE, {})
if 'playing' not in st.session_state:
    st.session_state.playing = None
if 'page' not in st.session_state:
    st.session_state.page = 0

def save_user_data():
    save_json(USER_DATA, st.session_state.user_data)

def toggle_watchlist(key):
    wl = st.session_state.user_data["watchlist"]
    if key in wl: wl.remove(key)
    else: wl.append(key)
    save_user_data()

def set_media_type(key, mtype):
    st.session_state.user_data["media_types"][key] = mtype
    save_user_data()

def add_custom_tag(key, tag):
    tags = st.session_state.user_data["custom_tags"].get(key, [])
    if tag and tag not in tags:
        tags.append(tag)
    st.session_state.user_data["custom_tags"][key] = tags
    save_user_data()

def remove_custom_tag(key, tag):
    tags = st.session_state.user_data["custom_tags"].get(key, [])
    if tag in tags: tags.remove(tag)
    st.session_state.user_data["custom_tags"][key] = tags
    save_user_data()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 🎬 Trailer Dashboard")

# ── CSV Upload + Cache ────────────────────────────────────────────────────────
uploaded_files = st.file_uploader(
    "Upload CSV", type=["csv"], accept_multiple_files=True,
    label_visibility="collapsed"
)

cache = st.session_state.csv_cache

# Merge newly uploaded files into cache
if uploaded_files:
    for f in uploaded_files:
        try:
            content = f.read().decode("utf-8", errors="replace")
            df = pd.read_csv(pd.io.common.StringIO(content), dtype=str).fillna('')
            df.columns = [normalize_key(c) for c in df.columns]
            title_col = 'title' if 'title' in df.columns else df.columns[0]
            url_col   = next((c for c in ['video_url','url','webpage_url'] if c in df.columns), None)
            mask = df[title_col].str.strip().ne('')
            if url_col: mask = mask | df[url_col].str.strip().ne('')
            df = df[mask]
            cache[f.name] = df.to_dict('records')
        except Exception as e:
            st.warning(f"Could not read {f.name}: {e}")
    save_json(CSV_CACHE, cache)
    st.session_state.csv_cache = cache

if not cache:
    st.markdown("""
    <div style="text-align:center;padding:80px 20px;color:#a8a8a8;">
        <div style="font-size:48px;margin-bottom:16px;">🎬</div>
        <div style="font-size:18px;font-weight:600;color:#737373;margin-bottom:8px;">No trailers yet</div>
        <div style="font-size:14px;">Upload your YouTube CSV file to view your metadata cards</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

# Show loaded file chips + remove buttons
with st.expander(f"📂 {len(cache)} file(s) loaded — click to manage", expanded=False):
    for fname in list(cache.keys()):
        c1, c2 = st.columns([5,1])
        c1.markdown(f"**{fname}** — {len(cache[fname])} rows")
        if c2.button("Remove", key=f"rm_{fname}"):
            del cache[fname]
            save_json(CSV_CACHE, cache)
            st.session_state.csv_cache = cache
            st.rerun()

records_all = []
for rows in cache.values():
    records_all.extend(rows)

dup_keys = find_duplicates(records_all)

# ── Filters ───────────────────────────────────────────────────────────────────
MEDIA_TYPES = ["Movie", "TV Show", "Streaming", "Short Film", "Documentary", "Anime", "Other"]

c1, c2, c3, c4, c5, c6 = st.columns([3, 1.4, 1.4, 1.2, 1.2, 1])
with c1:
    search = st.text_input("Search", placeholder="Search title, tags, description…", label_visibility="collapsed")
with c2:
    categories = sorted(set(r.get('category') or '' for r in records_all if r.get('category')))
    cat_filter = st.selectbox("Category", ["All categories"] + categories, label_visibility="collapsed")
with c3:
    mtype_filter = st.selectbox("Media type", ["All types"] + MEDIA_TYPES, label_visibility="collapsed")
with c4:
    view_mode = st.selectbox("View", ["All videos", "Watchlist only", "Duplicates only"], label_visibility="collapsed")
with c5:
    sort_by = st.selectbox("Sort", ["Date: Newest", "Date: Oldest", "Title A–Z", "Category A–Z"], label_visibility="collapsed")
with c6:
    cols_map = {"2":2,"3":3,"4":4,"5":5}
    layout = st.selectbox("Cols", ["3","2","4","5"], label_visibility="collapsed")

per_page = st.select_slider("Videos per page", options=[12,24,36,48,60], value=24)

# ── Filter & Sort ─────────────────────────────────────────────────────────────
wl  = st.session_state.user_data["watchlist"]
mt  = st.session_state.user_data["media_types"]

filtered = records_all
if search:
    q = search.lower()
    filtered = [r for r in filtered if q in ' '.join([
        r.get('title',''), r.get('category',''),
        r.get('description',''), r.get('tags','')
    ]).lower()]
if cat_filter != "All categories":
    filtered = [r for r in filtered if (r.get('category') or '') == cat_filter]
if mtype_filter != "All types":
    filtered = [r for r in filtered if mt.get(video_key(r)) == mtype_filter]
if view_mode == "Watchlist only":
    filtered = [r for r in filtered if video_key(r) in wl]
elif view_mode == "Duplicates only":
    filtered = [r for r in filtered if video_key(r) in dup_keys]

if sort_by == "Date: Newest":
    filtered.sort(key=lambda r: parse_date(r.get('upload_date') or r.get('date') or ''), reverse=True)
elif sort_by == "Date: Oldest":
    filtered.sort(key=lambda r: parse_date(r.get('upload_date') or r.get('date') or ''))
elif sort_by == "Title A–Z":
    filtered.sort(key=lambda r: r.get('title','').lower())
elif sort_by == "Category A–Z":
    filtered.sort(key=lambda r: r.get('category','').lower())

# ── Stats ─────────────────────────────────────────────────────────────────────
cat_count = len(set(r.get('category') for r in records_all if r.get('category')))
st.markdown(f"""
<div style="margin:12px 0 20px;">
  <span class="stat-pill"><span class="dot dot-blue"></span><span class="stat-num">{len(records_all)}</span><span class="stat-lbl">Total</span></span>
  <span class="stat-pill"><span class="dot dot-gray"></span><span class="stat-num">{len(filtered)}</span><span class="stat-lbl">Visible</span></span>
  <span class="stat-pill"><span class="dot dot-gold"></span><span class="stat-num">{cat_count}</span><span class="stat-lbl">Categories</span></span>
  <span class="stat-pill"><span class="dot dot-blue"></span><span class="stat-num">{len(wl)}</span><span class="stat-lbl">Watchlist</span></span>
  <span class="stat-pill"><span class="dot dot-red"></span><span class="stat-num">{len(dup_keys)}</span><span class="stat-lbl">Duplicates</span></span>
</div>
""", unsafe_allow_html=True)

# ── Pagination ────────────────────────────────────────────────────────────────
total_pages = max(1, -(-len(filtered) // per_page))
if st.session_state.page >= total_pages:
    st.session_state.page = 0

page_start = st.session_state.page * per_page
page_items = filtered[page_start: page_start + per_page]

# Pagination controls
if total_pages > 1:
    pcols = st.columns([1,4,1])
    with pcols[0]:
        if st.button("← Prev", disabled=st.session_state.page == 0):
            st.session_state.page -= 1; st.rerun()
    with pcols[1]:
        st.markdown(f"<div style='text-align:center;padding:8px 0;font-size:13px;color:#737373;'>Page {st.session_state.page+1} of {total_pages} &nbsp;·&nbsp; {len(filtered)} videos</div>", unsafe_allow_html=True)
    with pcols[2]:
        if st.button("Next →", disabled=st.session_state.page >= total_pages-1):
            st.session_state.page += 1; st.rerun()

# ── Grid ──────────────────────────────────────────────────────────────────────
if not page_items:
    st.info("No videos match your current filters.")
else:
    num_cols = cols_map[layout]
    grid_rows = [page_items[i:i+num_cols] for i in range(0, len(page_items), num_cols)]

    for row in grid_rows:
        cols = st.columns(num_cols)
        for col, item in zip(cols, row):
            with col:
                key       = video_key(item)
                url       = item.get('video_url') or item.get('url') or item.get('webpage_url') or item.get('link') or item.get('youtube_url') or ''
                video_id  = get_video_id(url)
                thumbnail = item.get('thumbnail') or (f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else "")
                title     = item.get('title') or 'Untitled'
                channel   = extract_channel(title)
                initial   = channel[0].upper() if channel else "Y"
                category  = item.get('category') or ''
                tags      = [t.strip() for t in str(item.get('tags') or '').split(',') if t.strip()][:3]
                desc      = item.get('description') or ''
                duration  = format_duration(item.get('duration') or item.get('duration_string') or '')
                is_saved  = key in wl
                is_dup    = key in dup_keys
                cur_mtype = mt.get(key, '')
                ctags     = st.session_state.user_data["custom_tags"].get(key, [])
                is_playing= st.session_state.playing == key

                # Card border class
                card_class = "card"
                if is_saved: card_class += " saved"
                elif is_dup: card_class += " duplicate"

                # Thumbnail / player
                thumb_html = f'<img src="{thumbnail}" alt="{title}" />' if thumbnail else '<div class="thumb-placeholder"></div>'
                cat_badge  = f'<span class="cat-badge">{category}</span>' if category else ''
                dur_badge  = f'<span class="dur-badge">{duration}</span>' if duration else ''
                dup_badge  = '<span class="dup-badge">DUPLICATE</span>' if is_dup else ''

                st.markdown(f"""
                <div class="{card_class}">
                  <div class="thumb-wrap" style="position:relative;">
                    {thumb_html}
                    {cat_badge}{dur_badge}{dup_badge}
                  </div>
                  <div class="card-body">
                    <div style="display:flex;align-items:flex-start;margin-bottom:8px;">
                      <span class="avatar">{initial}</span>
                      <div style="flex:1;min-width:0;">
                        <div class="card-title" title="{title}">{title}</div>
                        <div class="card-channel">{channel}</div>
                      </div>
                    </div>
                    <div>{''.join(f'<span class="tag">{t}</span>' for t in tags)}</div>
                    {''.join(f'<span class="tag-custom">🏷 {t}</span>' for t in ctags)}
                    {f'<div class="card-desc">{desc[:200]}</div>' if desc else ''}
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # Inline YouTube player
                if is_playing and video_id:
                    st.video(f"https://www.youtube.com/watch?v={video_id}")

                # Action buttons row
                b1, b2, b3 = st.columns(3)
                with b1:
                    save_label = "★ Saved" if is_saved else "☆ Save"
                    if st.button(save_label, key=f"save_{key}", use_container_width=True):
                        toggle_watchlist(key); st.rerun()
                with b2:
                    play_label = "⏹ Close" if is_playing else "▶ Watch"
                    if st.button(play_label, key=f"play_{key}", use_container_width=True):
                        st.session_state.playing = None if is_playing else key
                        st.rerun()
                with b3:
                    if url:
                        st.link_button("↗ Open", url, use_container_width=True)

                # Media type selector
                mtype_options = [""] + MEDIA_TYPES
                cur_idx = mtype_options.index(cur_mtype) if cur_mtype in mtype_options else 0
                new_mtype = st.selectbox(
                    "Type", mtype_options, index=cur_idx,
                    key=f"mt_{key}", label_visibility="collapsed"
                )
                if new_mtype != cur_mtype:
                    set_media_type(key, new_mtype); st.rerun()

                # Custom tag input
                with st.expander("🏷 Tags", expanded=False):
                    new_tag = st.text_input("Add tag", key=f"taginput_{key}", placeholder="e.g. Must Watch", label_visibility="collapsed")
                    if st.button("Add", key=f"tagadd_{key}") and new_tag.strip():
                        add_custom_tag(key, new_tag.strip()); st.rerun()
                    for ct in ctags:
                        tc1, tc2 = st.columns([4,1])
                        tc1.markdown(f"`{ct}`")
                        if tc2.button("✕", key=f"tagdel_{key}_{ct}"):
                            remove_custom_tag(key, ct); st.rerun()

# ── Bottom pagination ─────────────────────────────────────────────────────────
if total_pages > 1:
    st.markdown("---")
    pcols = st.columns([1,4,1])
    with pcols[0]:
        if st.button("← Prev ", disabled=st.session_state.page == 0, key="prev2"):
            st.session_state.page -= 1; st.rerun()
    with pcols[1]:
        st.markdown(f"<div style='text-align:center;padding:8px 0;font-size:13px;color:#737373;'>Page {st.session_state.page+1} of {total_pages}</div>", unsafe_allow_html=True)
    with pcols[2]:
        if st.button("Next → ", disabled=st.session_state.page >= total_pages-1, key="next2"):
            st.session_state.page += 1; st.rerun()
