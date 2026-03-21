import streamlit as st
import googleapiclient.discovery
import pandas as pd
from datetime import datetime, timedelta
import re
import isodate
import urllib.parse

# 1. САЙТ СОЗЛАМАЛАРИ
st.set_page_config(page_title="ABS Viral Tracker", page_icon="🚀", layout="wide")

# СЕССИЯ ХОТИРАСИ (КЕШ)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "search_count" not in st.session_state:
    st.session_state.search_count = 0 
if "saved_api_key" not in st.session_state:
    st.session_state.saved_api_key = ""

# ФОЙДАЛАНУВЧИЛАР БАЗАСИ
USER_DB = {
    "baho123": {"pass": "qWe83664323546", "role": "superadmin"},
}

# ДАВЛАТЛАР
REGION_LANGS = {"US": "en", "GB": "en", "UZ": "uz", "RU": "ru", "TR": "tr", "DE": "de"}

# --- ФУНКЦИЯЛАР ---
def get_full_uzb_date(iso_date):
    months = {1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь", 
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
    
    # 1. ТИЗИМДАН ЧИҚИШ (ТЕПАДА)
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
                    st.rerun()
                else: st.error("Хато!")
    
    st.divider()
    
    # 2. API ВА ҚИДИРУВ
    api_key = st.text_input("🔑 API Key:", value=st.session_state.saved_api_key, type="password")
    st.session_state.saved_api_key = api_key
    
    topic = st.text_input("🔍 Қидирув мавзуси:", "Motivation")
    region = st.selectbox("🌍 Давлат:", list(REGION_LANGS.keys()))
    min_outl = st.slider("Min Outlier (Вираллик):", 1, 50, 5)
    
    # 3. IP ВА ЛИМИТ ТЕКШИРУВИ (Cookie-симон хотира)
    FREE_LIMIT = 3
    can_search = True
    if not st.session_state.authenticated:
        remaining = FREE_LIMIT - st.session_state.search_count
        if remaining <= 0:
            st.error("🚨 Лимит тугади! Сиз 3 марта бепул фойдаландингиз.")
            st.info("👉 Давом этиш учун обуна бўлинг: [Telegram Администратор](https://t.me/your_admin_link)")
            can_search = False
        else:
            st.warning(f"🎁 Қолган имконият: {remaining}")

    search_btn = st.button("🚀 ТАҲЛИЛНИ БОШЛАШ", use_container_width=True, disabled=not can_search)

# --- АСОСИЙ МАЗМУН ---
tab1, tab2 = st.tabs(["📊 Viral Analysis", "📖 Қўлланма (Tutorial)"])

with tab1:
    if search_btn:
        if not api_key:
            st.error("API калит киритилмаган!")
        else:
            if not st.session_state.authenticated:
                st.session_state.search_count += 1 # Лимитни камайтириш
            
            try:
                youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
                res = youtube.search().list(q=topic, part="snippet", type="video", maxResults=20, order="viewCount", regionCode=region, relevanceLanguage=REGION_LANGS.get(region, "en")).execute()
                
                data = []
                for item in res['items']:
                    v_id = item['id']['videoId']
                    v_inf = youtube.videos().list(part="statistics,contentDetails,snippet", id=v_id).execute()['items'][0]
                    c_inf = youtube.channels().list(part="statistics,snippet", id=item['snippet']['channelId']).execute()['items'][0]
                    views, subs = int(v_inf['statistics'].get('viewCount', 0)), int(c_inf['statistics'].get('subscriberCount', 1))
                    outlier = round(views / (subs if subs > 1000 else 1000), 1)

                    if outlier >= min_outl:
                        data.append({
                            "id": v_id,
                            "Расм": v_inf['snippet']['thumbnails']['high']['url'],
                            "Вираллик": outlier, "Сарлавҳа": item['snippet']['title'],
                            "Кўрилишлар": format_numbers(views), "Обуначилар": format_numbers(subs),
                            "Юкланган сана": get_full_uzb_date(v_inf['snippet']['publishedAt']),
                            "Канал": item['snippet']['channelTitle'], "Ҳавола": f"https://www.youtube.com/watch?v={v_id}"
                        })

                if data:
                    df = pd.DataFrame(data).sort_values(by="Вираллик", ascending=False)
                    st.subheader(f"🏆 {region} бўйича Топ Натижалар")
                    
                    # НАТИЖАЛАРНИ ЧИҚАРИШ
                    for index, row in df.iterrows():
                        with st.container():
                            c1, c2 = st.columns([1, 2])
                            with c1:
                                st.image(row['Расм'], use_container_width=True)
                            with c2:
                                st.markdown(f"### {row['Сарлавҳа']}")
                                st.write(f"📈 **Вираллик:** {row['Вираллик']}x  |  📅 **Сана:** {row['Юкланган сана']}")
                                st.write(f"👤 **Канал:** {row['Канал']}  |  👁️ **Просмотр:** {row['Кўрилишлар']}")
                                
                                # ТУГМАЛАР ҚАТОРИ
                                col_btn1, col_btn2 = st.columns([1,1])
                                with col_btn1:
                                    st.link_button("📺 Видеони кўриш", row['Ҳавола'], use_container_width=True)
                                with col_btn2:
                                    # TELEGRAM SHARE LINK
                                    share_text = urllib.parse.quote(f"Зўр видео топдим! Вираллик: {row['Вираллик']}x\n{row['Ҳавола']}")
                                    st.link_button("✈️ Telegram-да улашиш", f"https://t.me/share/url?url={row['Ҳавола']}&text={share_text}", use_container_width=True)
                        st.divider()
                else: st.warning("Вирал видео топилмади.")
            except Exception as e: st.error(f"Хатолик: {e}")

with tab2:
    st.header("📖 YouTube API калит олиш бўйича Тўлиқ Қўлланма")
    st.info("Бу жараён бир марта қилинади ва мутлақо бепул!")
    
    st.subheader("1-қадам: Google Console-га кириш")
    st.write("Браузерда [console.cloud.google.com](https://console.cloud.google.com/) сайтига киринг.")
    

    st.subheader("2-қадам: YouTube API-ни фаоллаштириш")
    st.write("Қидирув жойига 'YouTube Data API v3' деб ёзинг ва кириб 'ENABLE' тугмасини босинг.")
    

    st.subheader("3-қадам: API Калитни яратиш")
    st.write("'Credentials' бўлимига ўтиб, '+ Create Credentials' -> 'API Key'ни танланг.")
    
    
    st.success("✅ Тайёр калитни нусхалаб, сайтимизга қўйинг!")
