import streamlit as st
import pandas as pd
import requests
import urllib.parse
import urllib.request
import re
import os
import time
import random
from datetime import datetime

# ==========================================
# 1. API CONFIG & INITIALIZATION
# ==========================================
TMDB_API_KEY = "e8b0c5c461c6e0357a1de99efdb1595b"
BASE_URL = "https://api.tmdb.org/3"

st.set_page_config(page_title="StreamSense AI", page_icon="🍿", layout="wide")

try:
    from ytmusicapi import YTMusic
    @st.cache_resource
    def init_ytmusic(): return YTMusic()
    ytmusic = init_ytmusic()
except:
    st.error("Terminal me chalao: pip install ytmusicapi")
    st.stop()

# ==========================================
# 2. CINEMATIC LOADING SCREEN
# ==========================================
if 'splash_shown' not in st.session_state:
    splash = st.empty()
    splash.markdown("""
        <div class="splash-bg"><h1 class="splash-logo">STREAMSENSE</h1><h2 class="splash-sub">YOUR AI ENTERTAINMENT HUB</h2></div>
        <style>
            .splash-bg {position:fixed; top:0; left:0; width:100vw; height:100vh; background:#0a0a0a; z-index:9999; display:flex; justify-content:center; align-items:center; flex-direction:column; animation: fadeOut 1.5s forwards; animation-delay: 2s;}
            .splash-logo { color:#E50914; font-size:70px; font-weight:900; letter-spacing: 5px; animation: glow 1.5s ease-in-out infinite alternate; }
            .splash-sub { color:white; font-size:15px; letter-spacing:8px; margin-top:10px; opacity:0.7; }
            @keyframes glow { from { text-shadow: 0 0 10px #E50914; } to { text-shadow: 0 0 25px #E50914, 0 0 5px #E50914; } }
            @keyframes fadeOut { 100% { opacity: 0; visibility: hidden; } }
        </style>
    """, unsafe_allow_html=True)
    time.sleep(3)
    splash.empty()
    st.session_state.splash_shown = True

# ==========================================
# 3. PREMIUM UI CSS (GLASSMORPHISM)
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #0a0a0a; color: white; }
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #222; }
    .sb-heading { font-size: 22px !important; font-weight: 800 !important; color: #ffffff !important; margin-top: 25px !important; display: block; border-left: 5px solid #E50914; padding-left: 12px; margin-bottom: 10px; }
    
    .reco-card { 
        background: rgba(255, 255, 255, 0.03); 
        border-radius: 15px; padding: 15px; 
        border: 1px solid rgba(255, 255, 255, 0.05); 
        transition: 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); 
        min-height: 520px;
    }
    .reco-card:hover { 
        transform: translateY(-12px); 
        background: rgba(255, 255, 255, 0.07);
        border-color: #E50914;
        box-shadow: 0 15px 30px rgba(229, 9, 20, 0.2);
    }
    .card-img { width: 100%; border-radius: 10px; object-fit: cover; aspect-ratio: 2/3; margin-bottom: 15px; }
    .music-img { aspect-ratio: 1/1 !important; }
    
    div[data-testid="stButton"] button { 
        background: #E50914 !important; color: white !important; font-weight: bold !important; 
        border-radius: 8px !important; border: none !important; width: 100%; height: 45px;
        transition: 0.3s;
    }
    div[data-testid="stButton"] button:hover { transform: scale(1.02); background: #b20710 !important; }
    
    .ott-btn { display: block; text-align: center; background: #222; color: #fff !important; padding: 10px; border-radius: 8px; text-decoration: none; font-size: 13px; margin-top: 10px; border: 1px solid #333; transition: 0.3s; }
    .ott-btn:hover { background: #333; border-color: #E50914; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 4. API HELPER FUNCTIONS
# ==========================================
def get_ott_info(item_id, m_type, title):
    try:
        res = requests.get(f"{BASE_URL}/{m_type}/{item_id}/watch/providers?api_key={TMDB_API_KEY}").json()
        india = res.get('results', {}).get('IN', {})
        providers = india.get('flatrate', []) + india.get('free', [])
        logos = [f"https://image.tmdb.org/t/p/original{p['logo_path']}" for p in providers[:3]]
        link = india.get('link', "#")
        safe_t = urllib.parse.quote(title)
        btn_txt = "WATCH NOW ➔"
        if providers:
            top = providers[0]['provider_name'].lower()
            if "netflix" in top: link, btn_txt = f"https://www.netflix.com/search?q={safe_t}", "ON NETFLIX"
            elif "prime" in top: link, btn_txt = f"https://www.primevideo.com/search?phrase={safe_t}", "ON PRIME"
        return logos, link, btn_txt
    except: return [], "#", "CHECK OTT"

@st.cache_data(show_spinner=False)
def fetch_yt_music(query):
    try:
        results = ytmusic.search(query, filter="songs", limit=35)
        formatted = []
        for item in results:
            vid_id = item.get('videoId')
            if vid_id:
                formatted.append({
                    'trackName': item.get('title', 'Unknown'),
                    'artistName': ", ".join([a['name'] for a in item.get('artists', [])]),
                    'artworkUrl': f"https://img.youtube.com/vi/{vid_id}/maxresdefault.jpg",
                    'videoId': vid_id
                })
        return formatted
    except: return []

# ==========================================
# 5. SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color:#E50914; font-weight:900;'>STREAMSENSE</h2>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<span class="sb-heading">Navigate</span>', unsafe_allow_html=True)
    menu = st.radio("Select Section", ["🎥 Movies", "📺 Web Series", "🎵 Music Vibes"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown('<span class="sb-heading">Smart AI Search</span>', unsafe_allow_html=True)
    smart_q = st.text_input("AI Query", placeholder="e.g. Dark Knight", label_visibility="collapsed")
    st.markdown("---")
    st.markdown('<div style="font-size:12px; color:#666; position: fixed; bottom: 20px;">Developed by Abhimanyu & Team</div>', unsafe_allow_html=True)

# ==========================================
# 6. MAIN LOGIC
# ==========================================
if 'movie_res' not in st.session_state: st.session_state.movie_res = []
if 'music_res' not in st.session_state: st.session_state.music_res = []

st.markdown("<h1 style='text-align:center; color:#E50914; margin-top:-40px; margin-bottom: 25px; font-weight:900;'>STREAMSENSE AI</h1>", unsafe_allow_html=True)

if menu in ["🎥 Movies", "📺 Web Series"]:
    m_type = "movie" if menu == "🎥 Movies" else "tv"
    normal_q = st.text_input(f"🔍 Explore {menu}...")
    
    c1, c2, c3, c4 = st.columns([1.5, 1.5, 1.5, 1.2])
    with c1: lang = st.selectbox("🌐 Region", ["Global", "Hindi", "English", "Telugu"])
    with c2: genre_sel = st.selectbox("🎭 Genre", ["All", "Action", "Comedy", "Drama", "Sci-Fi"])
    with c3: sort_date = st.selectbox("📅 Sort Order", ["Latest First", "Old is Gold"])
    with c4: st.write(""); apply_btn = st.button("Refresh ✨")

    if apply_btn or smart_q or normal_q:
        l_map = {"Global": "", "Hindi": "hi", "English": "en", "Telugu": "te"}
        g_map = {"Action": 28, "Comedy": 35, "Drama": 18, "Sci-Fi": 878}
        
        temp_res = []
        if smart_q:
            s_res = requests.get(f"{BASE_URL}/search/{m_type}?api_key={TMDB_API_KEY}&query={smart_q}").json().get('results', [])
            if s_res:
                recos = requests.get(f"{BASE_URL}/{m_type}/{s_res[0]['id']}/recommendations?api_key={TMDB_API_KEY}").json().get('results', [])
                # Smart Filter: Sirf quality data aur 2026 compatible
                temp_res = [m for m in recos if m.get('vote_average', 0) > 0 and m.get('poster_path')]
        elif normal_q:
            temp_res = requests.get(f"{BASE_URL}/search/{m_type}?api_key={TMDB_API_KEY}&query={normal_q}").json().get('results', [])
        else:
            # DYNAMIC ALGORITHM: Popularity + Page Shuffle (No date hard block)
            p = {
                "api_key": TMDB_API_KEY, 
                "sort_by": "popularity.desc", 
                "with_original_language": l_map[lang], 
                "vote_count.gte": 5, 
                "page": random.randint(1, 3) 
            }
            if genre_sel != "All": p["with_genres"] = g_map.get(genre_sel, "")
            temp_res = requests.get(f"{BASE_URL}/discover/{m_type}", params=p).json().get('results', [])

        final_list = [m for m in temp_res if m.get('poster_path')]
        st.session_state.movie_res = sorted(final_list, key=lambda x: (x.get('release_date') or x.get('first_air_date') or "1900"), reverse=(sort_date=="Latest First"))

    if st.session_state.movie_res:
        if 'mv_vid' not in st.session_state: st.session_state.mv_vid = None
        if st.session_state.mv_vid:
            st.video(f"https://www.youtube.com/watch?v={st.session_state.mv_vid}")
            if st.button("Close Player ✖️"): st.session_state.mv_vid = None; st.rerun()

        cols = st.columns(4)
        for i, item in enumerate(st.session_state.movie_res[:12]):
            with cols[i % 4]:
                title = item.get('title') or item.get('name')
                rating = round(item.get("vote_average", 0), 1)
                year = (item.get("release_date") or item.get("first_air_date") or "N/A")[:4]
                img = f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}"
                logos, link, b_txt = get_ott_info(item['id'], m_type, title)
                
                st.markdown(f'''<div class="reco-card"><img src="{img}" class="card-img"><h4>{title[:22]}</h4><p style="color:#E50914; font-weight:bold; margin-top:-10px;">⭐ {rating} | {year}</p><a href="{link}" target="_blank" class="ott-btn">{b_txt}</a></div>''', unsafe_allow_html=True)
                if st.button(f"WATCH TRAILER", key=f"mv_{item['id']}_{i}"):
                    query = urllib.parse.quote(f"{title} official trailer {year}")
                    res = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={query}")
                    st.session_state.mv_vid = re.findall(r'"videoId":"(.{11})"', res.read().decode())[0]
                    st.rerun()

elif menu == "🎵 Music Vibes":
    st.markdown("### 🎧 Discover Fresh Beats")
    m_search = st.text_input("Vibe Search (Artist, Song, Mood)...")
    mc1, mc2, mc3 = st.columns([1.5, 1.5, 1])
    with mc1: m_lang = st.selectbox("🌐 Language", ["Hindi", "English", "Punjabi", "Tamil"])
    with mc2: m_mood = st.selectbox("🎭 Mood", ["Party", "Romantic", "Sad", "Lo-Fi", "Workout"])
    with mc3: st.write(""); m_btn = st.button("Shuffle Music 🎵")

    if m_search or m_btn:
        q = m_search if m_search else f"{m_lang} {m_mood} hits 2026"
        music_data = fetch_yt_music(q)
        random.shuffle(music_data)
        st.session_state.music_res = music_data

    if st.session_state.music_res:
        if 'ms_vid' not in st.session_state: st.session_state.ms_vid = None
        if st.session_state.ms_vid:
            st.video(f"https://www.youtube.com/watch?v={st.session_state.ms_vid}")
            if st.button("Close Music Player ✖️"): st.session_state.ms_vid = None; st.rerun()

        cols = st.columns(4)
        for i, t in enumerate(st.session_state.music_res[:12]):
            with cols[i % 4]:
                name, artist, vid_id = t['trackName'], t['artistName'], t['videoId']
                st.markdown(f'''<div class="reco-card"><img src="{t['artworkUrl']}" onerror="this.src='https://img.youtube.com/vi/{vid_id}/mqdefault.jpg'" class="card-img music-img"><h4>{name[:22]}</h4><p style="color:#E50914; font-weight:bold; margin-top:-10px;">🎧 {artist[:20]}</p><a href="https://music.youtube.com/watch?v={vid_id}" target="_blank" class="ott-btn">YT MUSIC ➔</a></div>''', unsafe_allow_html=True)
                if st.button(f"PLAY NOW", key=f"ms_{vid_id}_{i}"): 
                    st.session_state.ms_vid = vid_id
                    st.rerun()