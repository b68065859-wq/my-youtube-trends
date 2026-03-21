import streamlit as st
import googleapiclient.discovery
import pandas as pd
from datetime import datetime, timedelta
import re
import collections

# 1. САЙТ ДИЗАЙНИ (MrBeast & ViewStat Style)
st.set_page_config(page_title="ABS Viral 777 - Intelligence", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    /* Асосий фон ва шрифтлар */
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* Тўгмачалар услуби (MrBeast Red) */
    .stButton>button {
        background: linear-gradient(90deg, #FF0000, #CC0000) !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        border: none !important;
        transition: 0.3s ease all;
        height: 3.5em !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(255, 0, 0, 0.3);
    }

    /* Метрика карточкалари */
    .metric-card {
        background: #1c1f26;
        border: 1px solid #2d3139;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        transition: 0.3s;
    }
    .metric-card:hover { border-color: #FF0000; }
    .metric-value { 
        font-size: 28px; 
        font-weight: 900; 
        color: #FF0000; 
        font-family: 'Inter', sans-serif;
    }
    .metric-label { color: #8a8d97; font-size: 14px; text-transform: uppercase; }

    /* Ниша баҳоси */
    .niche-score {
        background: linear-gradient(135deg, #1e1e26 0%, #111116 100%);
        border: 2px solid #FF0000;
        color: white; padding: 30px; border-radius: 20px;
        text-align: center; margin-bottom: 30px;
        box-shadow: 0 15px 35px rgba(255, 0, 0, 0.1);
    }
    
    /* Input майдонларини чиройли қилиш */
    .stTextInput>div>div>input {
        background-color: #1c1f26 !important;
        color: white !important;
        border: 1px solid #2d3139 !important;
        border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. СЕССИЯНИ МУСТАҲКАМЛАШ (777-ҚОИДА)
# Бу қисм API ва Лимит "ўлиб" қолмаслигини таъминлайди
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "search_count" not in st.session_state: st.session_state.search_count = 0
if "saved_api_key" not in st.session_state: st.session_state.saved_api_key = ""
if "last_results" not in st.session_state: st.session_state.last_results = None
if "search_history" not in st.session_state: st.session_state.search_history = []

USER_DB = {"baho123": {"pass": "qWe83664323546"}}
REGION_LANGS = {"US": "en", "GB": "en", "UZ": "uz", "RU": "ru", "TR": "tr"}

def format_numbers(n):
    if n >= 1000000: return f"{round(n/1000000, 1)}M"
    elif n >= 1000: return f"{round(n/1000, 1)}K"
    return str(n)

# --- SIDEBAR (ХОТИРА ВА СОЗЛАМАЛАР) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/d/db/MrBeast_logo.svg", width=100)
    st.title("777 VIRAL ENGINE")
    
    if not st.session_state.authenticated:
        with st.expander("🔐 ТИЗИМГА КИРИШ"):
            u = st.text_input("Логин:")
            p = st.text_input("Пароль:", type="password")
            if st.button("КИРИШ"):
                if u in USER_DB and USER_DB[u]["pass"] == p:
                    st.session_state.authenticated = True
                    st.rerun()
    else:
        st.success("✅ SuperAdmin Фаол")
        if st.button("🚪 ЧИҚИШ"):
            st.session_state.authenticated = False
            st.rerun()

    st.divider()
    
    # API KEY ЭНДИ ЎЧИБ КЕТМАЙДИ
    api_input = st.text_input("🔑 YouTube API Key:", value=st.session_state.saved_api_key, type="password")
    if api_input != st.session_state.saved_api_key:
        st.session_state.saved_api_key = api_input

    topic = st.text_input("🔍 Қидирув мавзуси:", "Survival")
    region = st.selectbox("🌍 Давлат:", list(REGION_LANGS.keys()))
    days = st.select_slider("📅 Давр (кун):", options=[7, 30, 90, 180, 365], value=90)
    min_views = st.selectbox("👁️ Min Кўришлар:", [0, 100000, 500000, 1000000], format_func=lambda x: format_numbers(x) if x>0 else "Ҳаммаси")
    min_outl = st.slider("🔥 Min Outlier:", 1, 50, 5)

    # ЛИМИТ ТЕКШИРУВИ
    can_search = True
    if not st.session_state.authenticated:
        remaining = 3 - st.session_state.search_count
        if remaining <= 0:
            st.error("🚨 Бугунги лимит тугади!")
            can_search = False
        else:
            st.warning(f"🎁 Текин имконият: {remaining}/3")
    
    search_btn = st.button("🚀 ТАҲЛИЛНИ БОШЛАШ", disabled=not can_search)

# --- АСОСИЙ ПАНЕЛ ---
if search_btn:
    if not st.session_state.saved_api_key:
        st.error("‼️ API Key киритилмаган! Чап менюдан калитни қўйинг.")
    else:
        try:
            with st.spinner("YouTube маълумотлари таҳлил қилинмоқда..."):
                youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=st.session_state.saved_api_key)
                pub_after = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
                
                res = youtube.search().list(q=topic, part="snippet", type="video", maxResults=50, order="viewCount", publishedAfter=pub_after, regionCode=region).execute()
                
                results = []
                all_titles = ""
                for item in res['items']:
                    v_id = item['id']['videoId']
                    v_inf = youtube.videos().list(part="statistics,snippet", id=v_id).execute()['items'][0]
                    c_inf = youtube.channels().list(part="statistics,snippet", id=item['snippet']['channelId']).execute()['items'][0]
                    
                    views, subs = int(v_inf['statistics'].get('viewCount', 0)), int(c_inf['statistics'].get('subscriberCount', 1))
                    outlier = round(views / (subs if subs > 1000 else 1000), 1)
                    
                    if outlier >= min_outl and views >= min_views:
                        all_titles += " " + v_inf['snippet']['title'].lower()
                        results.append({
                            "Расм": v_inf['snippet']['thumbnails']['high']['url'],
                            "Вираллик": outlier, 
                            "Видео_Номи": v_inf['snippet']['title'],
                            "Просмотр": views, 
                            "Обуначи": subs,
                            "Ҳавола": f"https://www.youtube.com/watch?v={v_id}",
                            "Канал": item['snippet']['channelTitle']
                        })
                
                st.session_state.last_results = {"data": results, "titles": all_titles}
                # Қидирув муваффақиятли бўлсагина лимитдан чегирилади
                if not st.session_state.authenticated:
                    st.session_state.search_count += 1
                    
        except Exception as e:
            st.error(f"⚠️ Хатолик юз берди: {e}")

# НАТИЖАЛАРНИ ЧИҚАРИШ
if st.session_state.last_results:
    res_data = st.session_state.last_results["data"]
    if not res_data:
        st.warning("Бу филтрлар бўйича вирал видео топилмади.")
    else:
        df = pd.DataFrame(res_data).sort_values(by="Вираллик", ascending=False)
        
        # Ниша баҳоси (MrBeast Style)
        avg_v = round(df["Вираллик"].mean(), 1)
        st.markdown(f"""
            <div class='niche-score'>
                <h1 style='color:#FF0000; margin:0;'>{avg_v}x</h1>
                <p style='font-size:20px; margin:0;'>VIRAL POTENTIAL SCORE</p>
                <p style='color:#8a8d97;'>Ушбу мавзудаги видеолар обуначилар сонига нисбатан {avg_v} баравар кўпроқ кўрилмоқда!</p>
            </div>
        """, unsafe_allow_html=True)

        # Кўриниш режими
        view_mode = st.radio("👀 Кўриниш:", ["Карточка", "Жадвал"], horizontal=True)
        
        if view_mode == "Карточка":
            for _, row in df.iterrows():
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(row['Расм'], use_container_width=True)
                with col2:
                    st.markdown(f"### [{row['Видео_Номи']}]({row['Ҳавола']})")
                    st.caption(f"📺 Канал: {row['Канал']}")
                    
                    m1, m2, m3 = st.columns(3)
                    m1.markdown(f"<div class='metric-card'><div class='metric-label'>Вираллик</div><div class='metric-value'>{row['Вираллик']}x</div></div>", unsafe_allow_html=True)
                    m2.markdown(f"<div class='metric-card'><div class='metric-label'>Кўришлар</div><div class='metric-value'>{format_numbers(row['Просмотр'])}</div></div>", unsafe_allow_html=True)
                    m3.markdown(f"<div class='metric-card'><div class='metric-label'>Обуначи</div><div class='metric-value'>{format_numbers(row['Обуначи'])}</div></div>", unsafe_allow_html=True)
                st.divider()
        else:
            st.dataframe(df, column_config={
                "Расм": st.column_config.ImageColumn(),
                "Видео_Номи": st.column_config.LinkColumn(display_text="Видео очиш"),
                "Ҳавола": None
            }, use_container_width=True, hide_index=True)
