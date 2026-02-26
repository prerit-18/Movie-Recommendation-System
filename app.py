import streamlit as st
import requests
import pandas as pd

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(
    page_title="What to Binge",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================
# CONFIG
# =============================
API_BASE = "https://movie-recommendation-system-hg5q.onrender.com"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

# =============================
# STYLES (Netflix Style)
# =============================
st.markdown("""
<style>
.stApp { background-color: #141414; color: white; }
header { background-color: #141414 !important; }
[data-testid="stToolbar"] { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1500px; }

h1, h2, h3, p { color: white; font-weight: 700; }
.small-muted { color: #b3b3b3; font-size: 0.9rem; }

.movie-title {
    font-size: 0.85rem;
    margin-top: 8px;
    color: #e5e5e5;
    text-align: center;
    height: 2.3rem;
    overflow: hidden;
}

.card {
    background-color: #181818;
    border-radius: 12px;
    padding: 14px;
    border: 1px solid rgba(255,255,255,0.05);
}

img {
    border-radius: 10px;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

img:hover {
    transform: scale(1.05);
    box-shadow: 0 15px 35px rgba(0,0,0,0.6);
}

div.stButton > button {
    background-color: #e50914;
    color: white;
    border-radius: 6px;
    border: none;
    padding: 6px 12px;
    font-weight: 600;
    transition: 0.2s ease;
}

div.stButton > button:hover {
    background-color: #f6121d;
    transform: scale(1.05);
}

section[data-testid="stSidebar"] {
    background-color: #000000;
    border-right: 1px solid rgba(255,255,255,0.1);
}
</style>
""", unsafe_allow_html=True)

# =============================
# SESSION STATE
# =============================
if "view" not in st.session_state:
    st.session_state.view = "home"
if "selected_tmdb_id" not in st.session_state:
    st.session_state.selected_tmdb_id = None

# =============================
# ROUTING
# =============================
def goto_home():
    st.session_state.view = "home"
    st.session_state.selected_tmdb_id = None
    st.rerun()

def goto_details(tmdb_id: int):
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = tmdb_id
    st.rerun()

# =============================
# API HELPER
# =============================
@st.cache_data(ttl=30)
def api_get_json(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=25)
        if r.status_code >= 400:
            return None
        return r.json()
    except:
        return None

# =============================
# GRID RENDER
# =============================
def poster_grid(cards, cols=6, key_prefix="grid"):
    if not cards:
        st.info("No movies found.")
        return

    rows = (len(cards) + cols - 1) // cols
    idx = 0
    for r in range(rows):
        columns = st.columns(cols)
        for c in range(cols):
            if idx >= len(cards):
                break
            movie = cards[idx]
            idx += 1

            with columns[c]:
                if movie.get("poster_url"):
                    st.image(movie["poster_url"], use_column_width=True)
                else:
                    st.write("🖼️ No poster")

                if st.button("Open", key=f"{key_prefix}_{r}_{c}_{idx}"):
                    goto_details(movie["tmdb_id"])

                st.markdown(
                    f"<div class='movie-title'>{movie.get('title','Untitled')}</div>",
                    unsafe_allow_html=True
                )

# =============================
# SIDEBAR (NAV ONLY)
# =============================
with st.sidebar:
    st.markdown("## 🎬 Menu")
    if st.button("🏠 Home"):
        goto_home()

# =============================
# HEADER
# =============================
st.title("🎬 What to Binge")
st.markdown(
    "<div class='small-muted'>Search movies or browse categories</div>",
    unsafe_allow_html=True
)
st.divider()

# ==========================================================
# HOME VIEW
# ==========================================================
# ==========================================================
# HOME VIEW
# ==========================================================
if st.session_state.view == "home":

    # Search
    typed = st.text_input(
        "Search by movie title",
        placeholder="Type: avenger, batman, love..."
    )

    st.divider()

    # If searching → show results
    if typed.strip():
        data = api_get_json("/tmdb/search", {"query": typed})
        if data and isinstance(data, list):
            poster_grid(data, cols=6, key_prefix="search")
        else:
            st.warning("No results found.")
        st.stop()

    # =============================
    # CATEGORY MAPPING (Display → API value)
    # =============================
    CATEGORY_MAP = {
        "Trending": "trending",
        "Popular": "popular",
        "Top Rated": "top_rated",
        "Now Playing": "now_playing",
        "Upcoming": "upcoming",
    }

    # Main page controls
    col1, col2 = st.columns([2, 1])

    with col1:
        selected_label = st.selectbox(
            "🎭 Browse Category",
            list(CATEGORY_MAP.keys())
        )
        home_category = CATEGORY_MAP[selected_label]

    with col2:
        grid_cols = st.slider("Grid Columns", 4, 8, 6)

    st.divider()

    st.markdown(f"## {selected_label} Movies")

    home_cards = api_get_json(
        "/home",
        {"category": home_category, "limit": 24}
    )

    if not home_cards:
        st.warning("Unable to fetch movies.")
    else:
        poster_grid(home_cards, cols=grid_cols, key_prefix="home")
# ==========================================================
# DETAILS VIEW
# ==========================================================
elif st.session_state.view == "details":

    tmdb_id = st.session_state.selected_tmdb_id
    if not tmdb_id:
        st.warning("No movie selected.")
        st.stop()

    if st.button("← Back to Home"):
        goto_home()

    data = api_get_json(f"/movie/id/{tmdb_id}")

    if not data:
        st.warning("Could not load movie details.")
        st.stop()

    left, right = st.columns([1, 2])

    with left:
        if data.get("poster_url"):
            st.image(data["poster_url"], use_column_width=True)

    with right:
        st.markdown(f"## {data.get('title')}")
        st.markdown(data.get("overview", "No overview available."))

        if data.get("trailer_url"):
            if st.button("▶ Watch Trailer"):
                st.video(data["trailer_url"])

    st.divider()
    st.markdown("### 🎯 Recommendations")

    recs = api_get_json("/recommend/genre", {"tmdb_id": tmdb_id, "limit": 18})

    if recs:
        poster_grid(recs, cols=6, key_prefix="recommend")
    else:
        st.info("No recommendations available.")