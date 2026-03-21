import streamlit as st
import googleapiclient.discovery
import pandas as pd
from datetime import datetime, timedelta
import re
import isodate
import urllib.parse

# 1. САЙТ ДИЗАЙНИ (MrBeast & ViewStat Style)
st.set_page_config(page_title="ABS Viral - MrBeast Edition", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    /* MrBeast Red Theme */
    .stButton>button {
        background-color: #FF0000 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
        height: 3em !important;
        width: 100% !important;
    }
    .stButton>button:hover {
        background-color: #CC0000 !important;
        border: 2px solid white !important;
    }
    /* ViewStat Card Style */
    .metric-card {
        background-color: #1E1E1E;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        color: white;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #FF0000;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. СЕССИЯ ХОТИРАСИ
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "search_count" not in st.session_state: st.session_state.search_count = 0 
if "saved_api_key" not in st.session_state: st.session_state.saved_api_key = ""
if "last_results" not in st.session_state: st.session_state.last_results = None
if "search_history" not in st.session_state: st.session_state.search_history = []

USER_DB = {"baho123": {"pass": "qWe83664323546", "role": "superadmin"}}
REGION_LANGS = {"US": "en", "GB": "en", "UZ": "uz", "RU": "ru", "TR": "tr", "DE": "de"}

# --- ФУНКЦИЯЛАР ---
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

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/d/db/MrBeast_logo.svg", width=100)
    st.title("ABS VIRAL SYSTEM")
    if st.session_state.authenticated:
        st.success(f"✅ Алоқада: {st.session_state.current_user}")
        if st.button("🚪 ЧИҚИШ"):
            st.session_state.authenticated = False
            st.rerun()
    else:
        with st.expander("🔑 Кириш"):
            u = st.text_input("Логин:")
            p = st.text_input("Пароль:", type="password")
            if st.button("КИРИШ"):
                if u in USER_DB and USER_DB[u]["pass"] == p:
                    st.session_state.authenticated = True
                    st.session_state.current_user = u
                    st.rerun()
    st.divider()
    api_key = st.text_input("🔑 API Key:", value=st.session_state.saved_api_key, type="password")
    st.session_state.saved_api_key = api_key
    topic = st.text_input("🔍 Қидирув:", "MrBeast Challenge")
    region = st.selectbox("🌍 Давлат:", list(REGION_LANGS.keys()))
    days_back = st.select_slider("📅 Давр (кун):", options=[7, 30, 90, 180, 365], value=180)
    min_outl = st.slider("🔥 Min Outlier:", 1, 50, 5)
    
    FREE_LIMIT = 3
    can_search = True
    if not st.session_state.authenticated:
        rem = FREE_LIMIT - st.session_state.search_count
        if rem <= 0:
            st.error("🚨 Лимит тугади!")
            can_search = False
        else: st.warning(f"🎁 Бепул имконият: {rem}")
    
    search_btn = st.button("🚀 ТАҲЛИЛНИ БОШЛАШ", disabled=not can_search)

# --- АСОСИЙ ПАНЕЛ ---
tab1, tab2, tab3 = st.tabs(["🚀 ТАҲЛИЛ", "📜 ТАРИХ", "📖 ҚЎЛЛАНМА"])

with tab1:
    view_mode = st.radio("👀 Кўриниш:", ["Катта (ViewStat Style)", "Жадвал (List)"], horizontal=True)
    
    if search_btn:
        if not api_key: st.error("API калитни киритинг!")
        else:
            if not st.session_state.authenticated: st.session_state.search_count += 1
            # ТАРИХГА ҚЎШИШ
            st.session_state.search_history.append({"Сана": datetime.now().strftime("%Y-%m-%d %H:%M"), "Мавзу": topic, "Ҳудуд": region})
            
            try:
                youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
                pub_after = (datetime.utcnow() - timedelta(days=days_back)).isoformat() + "Z"
                res = youtube.search().list(q=topic, part="snippet", type="video", maxResults=25, order="viewCount", publishedAfter=pub_after, regionCode=region).execute()
                
                results = []
                for item in res['items']:
                    v_id = item['id']['videoId']
                    v_inf = youtube.videos().list(part="statistics,snippet", id=v_id).execute()['items'][0]
                    c_inf = youtube.channels().list(part="statistics,snippet", id=item['snippet']['channelId']).execute()['items'][0]
                    
                    views = int(v_inf['statistics'].get('viewCount', 0))
                    subs = int(c_inf['statistics'].get('subscriberCount', 1))
                    outlier = round(views / (subs if subs > 1000 else 1000), 1)
                    
                    if outlier >= min_outl:
                        results.append({
                            "id": v_id, "Расм": v_inf['snippet']['thumbnails']['high']['url'],
                            "Вираллик": outlier, "Сарлавҳа": v_inf['snippet']['title'],
                            "Кўрилишлар": views, "Обуначилар": subs,
                            "Сана": get_full_uzb_date(v_inf['snippet']['publishedAt']),
                            "Канал": item['snippet']['channelTitle'],
                            "Ҳавола": f"https://www.youtube.com/watch?v={v_id}"
                        })
                st.session_state.last_results = results
            except Exception as e: st.error(f"Хато: {e}")

    if st.session_state.last_results:
        df = pd.DataFrame(st.session_state.last_results).sort_values(by="Вираллик", ascending=False)
        
        if view_mode == "Катта (ViewStat Style)":
            for _, row in df.iterrows():
                with st.container():
                    col1, col2 = st.columns([1.5, 2.5])
                    with col1:
                        st.image(row['Расм'], use_container_width=True)
                    with col2:
                        st.subheader(row['Сарлавҳа'])
                        st.write(f"📺 **Канал:** {row['Канал']} | 📅 **Сана:** {row['Сана']}")
                        # VIEWSTAT ВИЖЕТЛАРИ
                        m1, m2, m3 = st.columns(3)
                        m1.markdown(f"<div class='metric-card'>🔥 Вираллик<br><span class='metric-value'>{row['Вираллик']}x</span></div>", unsafe_allow_html=True)
                        m2.markdown(f"<div class='metric-card'>👁️ Просмотр<br><span class='metric-value'>{format_numbers(row['Кўрилишлар'])}</span></div>", unsafe_allow_html=True)
                        m3.markdown(f"<div class='metric-card'>👥 Обуначи<br><span class='metric-value'>{format_numbers(row['Обуначилар'])}</span></div>", unsafe_allow_html=True)
                        
                        st.write("")
                        b1, b2 = st.columns(2)
                        with b1: st.link_button("📺 ВИДЕОНИ КЎРИШ", row['Ҳавола'], use_container_width=True)
                        with b2:
                            msg = urllib.parse.quote(f"Зўр видео! {row['Вираллик']}x Вираллик: {row['Ҳавола']}")
                            st.link_button("✈️ SHARE", f"https://t.me/share/url?url={row['Ҳавола']}&text={msg}", use_container_width=True)
                st.divider()
        else:
            # ЖАДВАЛ КЎРИНИШИ (Рақамларни форматлаб чиқариш)
            list_df = df.copy()
            list_df['Кўрилишлар'] = list_df['Кўрилишлар'].apply(format_numbers)
            list_df['Обуначилар'] = list_df['Обуначилар'].apply(format_numbers)
            st.dataframe(list_df[["Расм", "Вираллик", "Сарлавҳа", "Кўрилишлар", "Сана", "Канал", "Ҳавола"]], 
                         column_config={"Расм": st.column_config.ImageColumn(), "Ҳавола": st.column_config.LinkColumn()}, use_container_width=True, hide_index=True)

with tab2:
    st.header("📜 Қидирув тарихи")
    if st.session_state.search_history:
        st.table(pd.DataFrame(st.session_state.search_history).iloc[::-1]) # Охиргиси тепада
    else: st.info("Тарих ҳали бўш.")

with tab3:
    st.header("📖 Қўлланма")
    st.markdown("""
    1. **Google Cloud**-га киринг.
    2. **YouTube Data API v3**-ни ёқинг.
    3. **API Key** олиб чап менюга қўйинг.
    """)
