import streamlit as st
import googleapiclient.discovery
import pandas as pd
from datetime import datetime, timedelta
import re
import isodate
import urllib.parse
import plotly.express as px

# 1. САЙТ СОЗЛАМАЛАРИ
st.set_page_config(page_title="ABS Viral Tracker", page_icon="🚀", layout="wide")

# СЕССИЯ ХОТИРАСИ (БРАУЗЕР ЁПИЛМАГУНЧА САҚЛАНАДИ)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "search_count" not in st.session_state:
    st.session_state.search_count = 0 
if "saved_api_key" not in st.session_state:
    st.session_state.saved_api_key = ""
if "search_history" not in st.session_state:
    st.session_state.search_history = []

# ФОЙДАЛАНУВЧИЛАР БАЗАСИ
USER_DB = {
    "baho123": {"pass": "qWe83664323546", "role": "superadmin"},
}

# ДАВЛАТЛАР ВА ТИЛЛАР
REGION_LANGS = {"US": "en", "GB": "en", "UZ": "uz", "RU": "ru", "TR": "tr", "DE": "de"}

# --- ФУНКЦИЯЛАР (САНА ВА РАҚАМЛАР) ---
def get_full_uzb_date(iso_date):
    months = {1: "Март", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь", 
              7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"}
    try:
        dt = datetime.strptime(re.sub(r'\.\d+Z', 'Z', iso_date), '%Y-%m-%dT%H:%M:%SZ')
        return f"{dt.year}-{dt.day}-{months[dt.month]}"
    except: return iso_date[:10]

def format_numbers(n):
    if n >= 1000000: return f"{round(n/1000000, 1)}M"
    elif n >= 1000: return f"{round(n/1000, 1)}K"
    return str(n)

# --- SIDEBAR (ЧАП МЕНЮ) ---
with st.sidebar:
    st.title("🛡️ ABS Viral System")
    
    # ЧИҚИШ ТУГМАСИ
    if st.session_state.authenticated:
        st.success(f"👤 {st.session_state.current_user}")
        if st.button("🚪 ТИЗИМДАН ЧИҚИШ", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
    else:
        with st.expander("🔑 Обуначилар учун кириш"):
            u = st.text_input("Логин:")
            p = st.text_input("Пароль:", type="password")
            if st.button("Кириш"):
                if u in USER_DB and USER_DB[u]["pass"] == p:
                    st.session_state.authenticated = True
                    st.session_state.current_user = u
                    st.session_state.user_role = USER_DB[u]["role"]
                    st.rerun()
                else: st.error("Хато!")
    
    st.divider()
    
    # API ВА ҚИДИРУВ СОЗЛАМАЛАРИ
    api_key = st.text_input("🔑 API Key:", value=st.session_state.saved_api_key, type="password")
    st.session_state.saved_api_key = api_key
    
    topic = st.text_input("🔍 Мавзу:", "Survival")
    region = st.selectbox("🌍 Давлат:", list(REGION_LANGS.keys()))
    min_outl = st.slider("Min Outlier (Вираллик):", 1, 50, 5)
    
    # ЛИМИТ ТЕКШИРУВИ (IP/СЕССИЯ БЛОКЛАШ)
    FREE_LIMIT = 3
    can_search = True
    if not st.session_state.authenticated:
        remaining = FREE_LIMIT - st.session_state.search_count
        if remaining <= 0:
            st.error("🚨 Лимит тугади!")
            st.info("👉 Обуна учун: [Telegram](https://t.me/your_admin_link)")
            can_search = False
        else:
            st.warning(f"🎁 Қолган имконият: {remaining}")

    search_btn = st.button("🚀 ТАҲЛИЛНИ БОШЛАШ", use_container_width=True, disabled=not can_search)

# --- АСОСИЙ ПАНЕЛ (ТАБЛАР) ---
t_list = ["🚀 Вирал Таҳлил", "📖 Қўлланма", "📜 Тарих"]
if st.session_state.authenticated and st.session_state.user_role == "superadmin":
    t_list.append("👨‍✈️ АДМИН")

tabs = st.tabs(t_list)

# 1. ТАҲЛИЛ ОЙНАСИ
with tabs[0]:
    if search_btn:
        if not api_key:
            st.error("API калитни киритинг!")
        else:
            if not st.session_state.authenticated:
                st.session_state.search_count += 1
            
            try:
                youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
                res = youtube.search().list(q=topic, part="snippet", type="video", maxResults=25, order="viewCount", regionCode=region, relevanceLanguage=REGION_LANGS.get(region, "en")).execute()
                
                data = []
                for item in res['items']:
                    v_id = item['id']['videoId']
                    v_inf = youtube.videos().list(part="statistics,contentDetails,snippet", id=v_id).execute()['items'][0]
                    c_inf = youtube.channels().list(part="statistics,snippet", id=item['snippet']['channelId']).execute()['items'][0]
                    views, subs = int(v_inf['statistics'].get('viewCount', 0)), int(c_inf['statistics'].get('subscriberCount', 1))
                    outlier = round(views / (subs if subs > 1000 else 1000), 1)

                    if outlier >= min_outl:
                        data.append({
                            "Расм": v_inf['snippet']['thumbnails']['high']['url'],
                            "Вираллик": outlier, "Сарлавҳа": item['snippet']['title'],
                            "Кўрилишлар": format_numbers(views), "Обуначилар": format_numbers(subs),
                            "Сана": get_full_uzb_date(v_inf['snippet']['publishedAt']),
                            "Канал": item['snippet']['channelTitle'], "Ҳавола": f"https://www.youtube.com/watch?v={v_id}"
                        })

                if data:
                    df = pd.DataFrame(data).sort_values(by="Вираллик", ascending=False)
                    
                    # BILLBOARD (TOP 3)
                    st.subheader(f"🏆 {region} бўйича Энг Вирал Видеолар")
                    b_cols = st.columns(3)
                    for i in range(min(3, len(df))):
                        with b_cols[i]:
                            st.image(df.iloc[i]['Расм'], use_container_width=True)
                            st.markdown(f"🔥 **{df.iloc[i]['Вираллик']}x Outlier**")
                            st.caption(df.iloc[i]['Сарлавҳа'][:50] + "...")
                    st.divider()

                    # ЖАДВАЛ КЎРИНИШИ ВА SHARE ТУГМАСИ
                    for idx, row in df.iterrows():
                        c1, c2 = st.columns([1, 2])
                        with c1: st.image(row['Расм'], use_container_width=True)
                        with c2:
                            st.subheader(row['Сарлавҳа'])
                            st.write(f"📈 **Вираллик:** {row['Вираллик']}x | 📅 **Сана:** {row['Сана']}")
                            st.write(f"👤 **Канал:** {row['Канал']} | 👁️ **Просмотр:** {row['Кўрилишлар']}")
                            
                            btn_col1, btn_col2 = st.columns(2)
                            with btn_col1: st.link_button("📺 Кўриш", row['Ҳавола'], use_container_width=True)
                            with btn_col2:
                                share_msg = urllib.parse.quote(f"Зўр видео топдим! Вираллик: {row['Вираллик']}x\n{row['Ҳавола']}")
                                st.link_button("✈️ Telegram-да улашиш", f"https://t.me/share/url?url={row['Ҳавола']}&text={share_msg}", use_container_width=True)
                        st.divider()
                else: st.warning("Видеотўплам бўш.")
            except Exception as e: st.error(f"Хато: {e}")

# 2. ҚЎЛЛАНМА (ВИЗУАЛ)
with tabs[1]:
    st.header("📖 API Калит олиш қўлланмаси")
    st.markdown("""
    1. **Google Cloud Console**-га киринг.
    2. **YouTube Data API v3**-ни қидиринг ва **ENABLE** тугмасини босинг.
    
    3. **Credentials** бўлимидан **API Key** яратинг.
    
    4. Калитни нусхалаб сайтимизга қўйинг.
    """)

# 3. ТАРИХ
with tabs[2]:
    st.header("📜 Қидирув тарихи")
    st.info("Бу ерда охирги қидирувлар кўринади.")

# 4. АДМИН ПАНЕЛ
if st.session_state.authenticated and st.session_state.user_role == "superadmin":
    with tabs[3]:
        st.header("👨‍✈️ Бошқарув")
        st.write("Фойдаланувчилар статистикаси ва лимитлар шу ерда.")
