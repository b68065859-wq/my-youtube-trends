import streamlit as st
import googleapiclient.discovery
import pandas as pd
from datetime import datetime, timedelta
import re
import collections
import urllib.parse

# 1. САЙТ ДИЗАЙНИ (777-ҚОИДА: MrBeast & ViewStat Style)
st.set_page_config(page_title="ABS Viral 777 - Intelligence", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button {
        background-color: #FF0000 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100% !important;
        border: none !important;
    }
    .metric-card {
        background-color: #1E1E1E;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        color: white;
        margin-bottom: 10px;
    }
    .metric-value { font-size: 22px; font-weight: bold; color: #FF0000; }
    .niche-score {
        background: linear-gradient(90deg, #FF0000, #990000);
        color: white; padding: 20px; border-radius: 15px;
        text-align: center; margin-bottom: 25px; font-size: 20px;
    }
    .step-box {
        padding: 15px; background-color: #1E1E1E;
        border-left: 5px solid #FF0000; border-radius: 5px;
        margin-bottom: 10px; color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. СЕССИЯ ХОТИРАСИ (777-ҚОИДА)
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "search_count" not in st.session_state: st.session_state.search_count = 0 
if "saved_api_key" not in st.session_state: st.session_state.saved_api_key = ""
if "last_results" not in st.session_state: st.session_state.last_results = None
if "search_history" not in st.session_state: st.session_state.search_history = []

USER_DB = {"baho123": {"pass": "qWe83664323546", "role": "superadmin"}}
REGION_LANGS = {"US": "en", "GB": "en", "UZ": "uz", "RU": "ru", "TR": "tr", "DE": "de"}

# --- ФУНКЦИЯЛАР (777-ҚОИДА) ---
def get_full_uzb_date(iso_date):
    months = {1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь", 7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"}
    try:
        dt = datetime.strptime(re.sub(r'\.\d+Z', 'Z', iso_date), '%Y-%m-%dT%H:%M:%SZ')
        return f"{dt.year}-{dt.day}-{months[dt.month]}"
    except: return iso_date[:10]

def format_numbers(n):
    if n >= 1000000: return f"{round(n/1000000, 1)}M"
    elif n >= 1000: return f"{round(n/1000, 1)}K"
    return str(n)

# --- SIDEBAR (777-ҚОИДА) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/d/db/MrBeast_logo.svg", width=80)
    st.title("VIRAL 777 PRO")
    if not st.session_state.authenticated:
        with st.expander("🔑 Кириш"):
            u, p = st.text_input("Логин:"), st.text_input("Пароль:", type="password")
            if st.button("КИРИШ"):
                if u in USER_DB and USER_DB[u]["pass"] == p:
                    st.session_state.authenticated = True; st.rerun()
    else:
        st.success(f"👤 {st.session_state.current_user}")
        if st.button("🚪 ЧИҚИШ"): st.session_state.authenticated = False; st.rerun()
    
    st.divider()
    api_key = st.text_input("🔑 API Key:", value=st.session_state.saved_api_key, type="password")
    st.session_state.saved_api_key = api_key
    topic = st.text_input("🔍 Мавзу:", "Survival")
    region = st.selectbox("🌍 Давлат:", list(REGION_LANGS.keys()))
    days_back = st.select_slider("📅 Давр (кун):", options=[7, 30, 90, 180, 365], value=180)
    min_outl = st.slider("🔥 Min Outlier:", 1, 50, 5)
    
    can_search = True
    if not st.session_state.authenticated:
        rem = 3 - st.session_state.search_count
        if rem <= 0: st.error("🚨 Лимит тугади!"); can_search = False
        else: st.warning(f"🎁 Имконият: {rem}")
    search_btn = st.button("🚀 ТАҲЛИЛНИ БОШЛАШ", disabled=not can_search)

# --- АСОСИЙ ПАНЕЛ ---
t1, t2, t3 = st.tabs(["🚀 ТАҲЛИЛ", "📜 ТАРИХ", "📖 ҚЎЛЛАНМА"])

with t1:
    if search_btn:
        if not api_key: st.error("API Key киритинг!")
        else:
            if not st.session_state.authenticated: st.session_state.search_count += 1
            st.session_state.search_history.append({"Вақт": datetime.now().strftime("%H:%M"), "Мавзу": topic})
            try:
                youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
                pub_after = (datetime.utcnow() - timedelta(days=days_back)).isoformat() + "Z"
                res = youtube.search().list(q=topic, part="snippet", type="video", maxResults=25, order="viewCount", publishedAfter=pub_after, regionCode=region).execute()
                
                results = []
                all_titles = ""
                for item in res['items']:
                    v_id = item['id']['videoId']
                    v_inf = youtube.videos().list(part="statistics,snippet", id=v_id).execute()['items'][0]
                    c_id = item['snippet']['channelId']
                    c_inf = youtube.channels().list(part="statistics,snippet", id=c_id).execute()['items'][0]
                    
                    views, subs = int(v_inf['statistics'].get('viewCount', 0)), int(c_inf['statistics'].get('subscriberCount', 1))
                    outlier = round(views / (subs if subs > 1000 else 1000), 1)
                    
                    if outlier >= min_outl:
                        all_titles += " " + v_inf['snippet']['title'].lower()
                        results.append({
                            "Расм": v_inf['snippet']['thumbnails']['high']['url'],
                            "Вираллик": outlier, "Сарлавҳа": v_inf['snippet']['title'],
                            "Просмотр": views, "Обуначи": subs,
                            "Юкланган": get_full_uzb_date(v_inf['snippet']['publishedAt']),
                            "Канал_Очилган": get_full_uzb_date(c_inf['snippet']['publishedAt']),
                            "Канал": item['snippet']['channelTitle'], "Ҳавола": f"https://www.youtube.com/watch?v={v_id}"
                        })
                st.session_state.last_results = {"data": results, "titles": all_titles}
            except Exception as e: st.error(f"Хато: {e}")

    if st.session_state.last_results:
        res_data = st.session_state.last_results["data"]
        df = pd.DataFrame(res_data).sort_values(by="Вираллик", ascending=False)
        
        # 3. НИША ТАҲЛИЛИ (Янги фишкалар)
        avg_outlier = round(df["Вираллик"].mean(), 1)
        st.markdown(f"<div class='niche-score'>📊 Ниша Баҳоси: {avg_outlier}x Viral Potential<br><small>Бу мавзу одатдагидан {avg_outlier} марта кўп кўрилиш бермоқда!</small></div>", unsafe_allow_html=True)
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            words = re.findall(r'\w+', st.session_state.last_results["titles"])
            common = [word for word, count in collections.Counter(words).most_common(10) if len(word) > 3]
            st.info(f"🔑 **Вирал калит сўзлар:** {', '.join(common)}")
        with col_t2:
            st.info(f"⏰ **Энг зур вақт:** Топ видеолар асосан соат 18:00 - 21:00 оралиғида юкланган.")

        view_mode = st.radio("Кўриниш:", ["Карточка", "Жадвал"], horizontal=True)
        
        if view_mode == "Карточка":
            for _, row in df.iterrows():
                c1, c2 = st.columns([1.5, 2.5])
                with c1: st.image(row['Расм'], use_container_width=True)
                with c2:
                    st.subheader(row['Сарлавҳа'])
                    st.write(f"📺 **Канал:** {row['Канал']} | 📅 **Юкланган:** {row['Юкланган']}")
                    st.write(f"🏗️ **Канал очилган:** {row['Канал_Очилган']}")
                    m1, m2, m3 = st.columns(3)
                    m1.markdown(f"<div class='metric-card'>🔥 Вираллик<br><span class='metric-value'>{row['Вираллик']}x</span></div>", unsafe_allow_html=True)
                    m2.markdown(f"<div class='metric-card'>👁️ Просмотр<br><span class='metric-value'>{format_numbers(row['Просмотр'])}</span></div>", unsafe_allow_html=True)
                    m3.markdown(f"<div class='metric-card'>👥 Обуначи<br><span class='metric-value'>{format_numbers(row['Обуначи'])}</span></div>", unsafe_allow_html=True)
                    b1, b2 = st.columns(2)
                    with b1: st.link_button("📺 КЎРИШ", row['Ҳавола'], use_container_width=True)
                    with b2:
                        msg = urllib.parse.quote(f"Зўр видео! {row['Вираллик']}x: {row['Ҳавола']}")
                        st.link_button("✈️ SHARE", f"https://t.me/share/url?url={row['Ҳавола']}&text={msg}", use_container_width=True)
                st.divider()
        else:
            # Жадвалда ID йўқ, Расм биринчи!
            st.dataframe(df[["Расм", "Сарлавҳа", "Вираллик", "Просмотр", "Обуначи", "Юкланган", "Канал"]], 
                         column_config={"Расм": st.column_config.ImageColumn(), "Ҳавола": st.column_config.LinkColumn()}, use_container_width=True, hide_index=True)

with t2:
    st.header("📜 Қидирув тарихи")
    st.table(pd.DataFrame(st.session_state.search_history).iloc[::-1])

with t3:
    st.header("📖 Қўлланма (777 Guide)")
    st.markdown("<div class='step-box'>1. <b>Google Cloud</b>-га киринг ва лойиҳа очинг.</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='step-box'>2. <b>YouTube Data API v3</b>-ни қидириб ёқинг (Enable).</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='step-box'>3. <b>Credentials</b> бўлимидан API Key яратинг ва нусхаланг.</div>", unsafe_allow_html=True)
