import streamlit as st
import googleapiclient.discovery
import pandas as pd
from datetime import datetime, timedelta
import re
import isodate
import urllib.parse

# 1. САЙТ СОЗЛАМАЛАРИ
st.set_page_config(page_title="ABS Viral Tracker", page_icon="🚀", layout="wide")

# СЕССИЯ ХОТИРАСИ
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "search_count" not in st.session_state:
    st.session_state.search_count = 0 
if "saved_api_key" not in st.session_state:
    st.session_state.saved_api_key = ""

# ФОЙДАЛАНУВЧИЛАР БАЗАСИ
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
    st.title("🛡️ ABS Viral System")
    if st.session_state.authenticated:
        st.success(f"👤 {st.session_state.current_user}")
        if st.button("🚪 ТИЗИМДАН ЧИҚИШ", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
    else:
        with st.expander("🔑 Кириш"):
            u = st.text_input("Логин:")
            p = st.text_input("Пароль:", type="password")
            if st.button("Кириш"):
                if u in USER_DB and USER_DB[u]["pass"] == p:
                    st.session_state.authenticated = True
                    st.session_state.current_user = u
                    st.rerun()
    st.divider()
    api_key = st.text_input("🔑 API Key:", value=st.session_state.saved_api_key, type="password")
    st.session_state.saved_api_key = api_key
    topic = st.text_input("🔍 Мавзу:", "Survival")
    region = st.selectbox("🌍 Давлат:", list(REGION_LANGS.keys()))
    days_back = st.select_slider("📅 Давр (кун):", options=[7, 30, 90, 180, 365], value=180)
    min_outl = st.slider("Min Outlier:", 1, 50, 5)
    
    # ЛИМИТ
    FREE_LIMIT = 3
    can_search = True
    if not st.session_state.authenticated:
        remaining = FREE_LIMIT - st.session_state.search_count
        if remaining <= 0:
            st.error("🚨 Лимит тугади!")
            can_search = False
        else: st.warning(f"🎁 Имконият: {remaining}")
    search_btn = st.button("🚀 ТАҲЛИЛНИ БОШЛАШ", use_container_width=True, disabled=not can_search)

# --- АСОСИЙ ПАНЕЛ ---
tab1, tab2 = st.tabs(["📊 Viral Analysis", "📖 Қўлланма"])

with tab1:
    # КЎРИНИШ ТУРИНИ ТАНЛАШ
    view_mode = st.radio("👀 Кўриниш формати:", ["Катта формат (Карточка)", "Рўйхат (Жадвал)"], horizontal=True)
    
    if search_btn:
        if not api_key: st.error("API калитни киритинг!")
        else:
            if not st.session_state.authenticated: st.session_state.search_count += 1
            try:
                youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
                pub_after = (datetime.utcnow() - timedelta(days=days_back)).isoformat() + "Z"
                res = youtube.search().list(q=topic, part="snippet", type="video", maxResults=25, order="viewCount", publishedAfter=pub_after, regionCode=region, relevanceLanguage=REGION_LANGS.get(region, "en")).execute()
                
                data = []
                for item in res['items']:
                    v_id = item['id']['videoId']
                    v_inf = youtube.videos().list(part="statistics,contentDetails,snippet", id=v_id).execute()['items'][0]
                    c_inf = youtube.channels().list(part="statistics,snippet", id=item['snippet']['channelId']).execute()['items'][0]
                    views, subs = int(v_inf['statistics'].get('viewCount', 0)), int(c_inf['statistics'].get('subscriberCount', 1))
                    outlier = round(views / (subs if subs > 1000 else 1000), 1)
                    if outlier >= min_outl:
                        data.append({"Расм": v_inf['snippet']['thumbnails']['high']['url'], "Вираллик": outlier, "Сарлавҳа": item['snippet']['title'], "Кўрилишлар": format_numbers(views), "Обуначилар": format_numbers(subs), "Сана": get_full_uzb_date(v_inf['snippet']['publishedAt']), "Канал": item['snippet']['channelTitle'], "Ҳавола": f"https://www.youtube.com/watch?v={v_id}"})

                if data:
                    df = pd.DataFrame(data).sort_values(by="Вираллик", ascending=False)
                    
                    # 1. КАТТА ФОРМАТ (КАРТОЧКА)
                    if view_mode == "Катта формат (Карточка)":
                        for idx, row in df.iterrows():
                            c1, c2 = st.columns([1, 2])
                            with c1: st.image(row['Расм'], use_container_width=True)
                            with c2:
                                st.subheader(row['Сарлавҳа'])
                                st.write(f"📈 **Вираллик:** {row['Вираллик']}x | 📅 **Сана:** {row['Сана']}")
                                b1, b2 = st.columns(2)
                                with b1: st.link_button("📺 Кўриш", row['Ҳавола'], use_container_width=True)
                                with b2:
                                    msg = urllib.parse.quote(f"Вираллик: {row['Вираллик']}x\n{row['Ҳавола']}")
                                    st.link_button("✈️ Telegram", f"https://t.me/share/url?url={row['Ҳавола']}&text={msg}", use_container_width=True)
                            st.divider()
                    
                    # 2. РЎЙХАТ (ЖАДВАЛ)
                    else:
                        st.dataframe(df, column_config={"Расм": st.column_config.ImageColumn("Превью"), "Ҳавола": st.column_config.LinkColumn("🔗")}, use_container_width=True, hide_index=True)
                else: st.warning("Видео топилмади.")
            except Exception as e: st.error(f"Хато: {e}")

with tab2:
    st.header("📖 Қўлланма")
    st.write("Google Cloud Console-дан API калит олинг.")
