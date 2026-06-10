import streamlit as st
import pandas as pd
import re

st.set_page_config(
    page_title="Trailer Dashboard",
    page_icon="🎬",
    layout="wide"
)

# ── Styles ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.card {
    background: #ffffff;
    border: 1px solid #efefef;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    transition: box-shadow 0.15s;
    height: 100%;
    margin-bottom: 16px;
}
.card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.10); }

.thumb-wrap {
    position: relative;
    width: 100%;
    aspect-ratio: 16/9;
    background: #111;
    overflow: hidden;
}
.thumb-wrap img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}
.thumb-placeholder {
    width: 100%;
    padding-top: 56.25%;
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    position: relative;
}
.category-badge {
    display: inline-block;
    background: rgba(0,0,0,0.65);
    color: #fff;
    font-size: 10px;
    font-weight: 700;
    border-radius: 4px;
    padding: 3px 7px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.card-body { padding: 14px 16px 16px; }

.avatar {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, #833ab4, #fd1d1d, #fcb045);
    color: #fff;
    font-size: 13px;
    font-weight: 700;
    flex-shrink: 0;
    margin-right: 10px;
    vertical-align: middle;
}
.card-title {
    font-size: 13px;
    font-weight: 600;
    color: #0a0a0a;
    line-height: 1.35;
    margin: 0 0 2px 0;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.card-channel {
    font-size: 12px;
    color: #737373;
    margin: 0 0 8px 0;
}
.tag {
    display: inline-block;
    font-size: 11px;
    font-weight: 500;
    color: #0095f6;
    background: rgba(0,149,246,0.08);
    border-radius: 4px;
    padding: 2px 7px;
    margin: 2px 3px 2px 0;
}
.card-desc {
    font-size: 12px;
    line-height: 1.5;
    color: #737373;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    margin: 8px 0 10px 0;
}
.watch-btn {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #ff0000;
    color: #fff !important;
    border-radius: 6px;
    padding: 5px 11px;
    font-size: 12px;
    font-weight: 600;
    text-decoration: none !important;
}
.watch-btn:hover { background: #cc0000; }

.stat-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #fff;
    border: 1px solid #efefef;
    border-radius: 100px;
    padding: 8px 18px;
    margin-right: 8px;
    margin-bottom: 8px;
}
.stat-num { font-size: 18px; font-weight: 700; color: #0a0a0a; }
.stat-lbl { font-size: 12px; color: #737373; font-weight: 500; }
.dot { width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:2px; }
.dot-blue  { background:#0095f6; }
.dot-gray  { background:#a8a8a8; }
.dot-gold  { background:#f5a623; }
.dot-red   { background:#ed4956; }

/* Hide Streamlit default elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────
def normalize_key(k):
    return re.sub(r'\s+', '_', str(k or '').strip().lower().lstrip('\ufeff'))

def get_video_id(url):
    if not url:
        return ""
    m = re.search(r'[?&]v=([^&]+)', url)
    if m:
        return m.group(1)
    s = re.search(r'youtu\.be/([^?&]+)', url)
    return s.group(1) if s else ""

def extract_channel(title):
    if not title:
        return "YouTube Video"
    if " | " in title:
        parts = title.split(" | ")
        return re.sub(r'Official Trailer.*', '', parts[-1], flags=re.I).strip()
    m = re.search(r'\(([^)]+)\)', title)
    return m.group(1) if m else "YouTube Video"

def parse_date(val):
    if not val:
        return pd.NaT
    s = str(val).strip()
    m = re.match(r'^(\d{4})(\d{2})(\d{2})$', s)
    if m:
        s = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    try:
        return pd.to_datetime(s)
    except:
        return pd.NaT

def render_card(item):
    url = item.get('video_url') or item.get('url') or item.get('webpage_url') or item.get('link') or item.get('youtube_url') or ''
    video_id = get_video_id(url)
    thumbnail = item.get('thumbnail') or (f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else "")
    title = item.get('title') or 'Untitled'
    channel = extract_channel(title)
    initial = channel[0].upper() if channel else "Y"
    category = item.get('category') or ''
    tags = [t.strip() for t in str(item.get('tags') or '').split(',') if t.strip()][:3]
    desc = item.get('description') or ''

    thumb_html = f'<img src="{thumbnail}" alt="{title}" />' if thumbnail else '<div class="thumb-placeholder"></div>'
    badge_html = f'<div style="position:absolute;top:8px;left:8px;"><span class="category-badge">{category}</span></div>' if category else ''
    tags_html = ''.join([f'<span class="tag">{t}</span>' for t in tags])
    desc_html = f'<div class="card-desc">{desc[:200]}</div>' if desc else ''
    watch_html = f'<a class="watch-btn" href="{url}" target="_blank">▶ Watch</a>' if url else ''

    st.markdown(f"""
    <div class="card">
        <div class="thumb-wrap" style="position:relative;">
            {thumb_html}
            {badge_html}
        </div>
        <div class="card-body">
            <div style="display:flex;align-items:flex-start;margin-bottom:8px;">
                <span class="avatar">{initial}</span>
                <div>
                    <div class="card-title" title="{title}">{title}</div>
                    <div class="card-channel">{channel}</div>
                </div>
            </div>
            <div>{tags_html}</div>
            {desc_html}
            {watch_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── App ───────────────────────────────────────────────────────────────────────
st.markdown("## 🎬 Trailer Dashboard")

uploaded_files = st.file_uploader(
    "Upload CSV file(s)",
    type=["csv"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

if not uploaded_files:
    st.markdown("""
    <div style="text-align:center;padding:80px 20px;color:#a8a8a8;">
        <div style="font-size:48px;margin-bottom:16px;">🎬</div>
        <div style="font-size:18px;font-weight:600;color:#737373;margin-bottom:8px;">No trailers yet</div>
        <div style="font-size:14px;">Upload your YouTube CSV file to view your metadata cards</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Load and combine all CSVs
frames = []
for f in uploaded_files:
    try:
        df = pd.read_csv(f, dtype=str).fillna('')
        df.columns = [normalize_key(c) for c in df.columns]
        df = df[df['title'].str.strip().ne('') | df.get('video_url', pd.Series(dtype=str)).str.strip().ne('')]
        frames.append(df)
    except Exception as e:
        st.warning(f"Could not read {f.name}: {e}")

if not frames:
    st.error("No usable data found in uploaded files.")
    st.stop()

data = pd.concat(frames, ignore_index=True)
records = data.to_dict('records')

# ── Filters ───────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns([3, 1.5, 1.5, 1])

with col1:
    search = st.text_input("Search", placeholder="Search title, category, tags…", label_visibility="collapsed")
with col2:
    categories = sorted(set(r.get('category') or 'Unknown' for r in records if r.get('category')))
    cat_filter = st.selectbox("Category", ["All categories"] + categories, label_visibility="collapsed")
with col3:
    sort_by = st.selectbox("Sort", ["Date: Newest First", "Date: Oldest First", "Title A–Z", "Category A–Z"], label_visibility="collapsed")
with col4:
    cols_map = {"3 columns": 3, "4 columns": 4, "5 columns": 5, "2 columns": 2}
    layout = st.selectbox("Layout", list(cols_map.keys()), label_visibility="collapsed")

# ── Filter & Sort ─────────────────────────────────────────────────────────────
filtered = records
if search:
    q = search.lower()
    filtered = [r for r in filtered if q in ' '.join([
        r.get('title',''), r.get('category',''), r.get('description',''), r.get('tags','')
    ]).lower()]
if cat_filter != "All categories":
    filtered = [r for r in filtered if (r.get('category') or 'Unknown') == cat_filter]

if sort_by == "Date: Newest First":
    filtered.sort(key=lambda r: parse_date(r.get('upload_date') or r.get('date') or r.get('published_at') or ''), reverse=True)
elif sort_by == "Date: Oldest First":
    filtered.sort(key=lambda r: parse_date(r.get('upload_date') or r.get('date') or r.get('published_at') or ''))
elif sort_by == "Title A–Z":
    filtered.sort(key=lambda r: r.get('title','').lower())
elif sort_by == "Category A–Z":
    filtered.sort(key=lambda r: r.get('category','').lower())

# ── Stats ─────────────────────────────────────────────────────────────────────
cat_count = len(set(r.get('category') for r in records if r.get('category')))
st.markdown(f"""
<div style="margin: 12px 0 20px;">
    <span class="stat-pill"><span class="dot dot-blue"></span><span class="stat-num">{len(records)}</span><span class="stat-lbl">Total Videos</span></span>
    <span class="stat-pill"><span class="dot dot-gray"></span><span class="stat-num">{len(filtered)}</span><span class="stat-lbl">Visible</span></span>
    <span class="stat-pill"><span class="dot dot-gold"></span><span class="stat-num">{cat_count}</span><span class="stat-lbl">Categories</span></span>
</div>
""", unsafe_allow_html=True)

# ── Grid ──────────────────────────────────────────────────────────────────────
if not filtered:
    st.info("No videos match your search or filters.")
else:
    num_cols = cols_map[layout]
    rows = [filtered[i:i+num_cols] for i in range(0, len(filtered), num_cols)]
    for row in rows:
        cols = st.columns(num_cols)
        for col, item in zip(cols, row):
            with col:
                render_card(item)
