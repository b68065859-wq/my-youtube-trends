import streamlit as st
import googleapiclient.discovery
import pandas as pd
from io import BytesIO
import isodate
from datetime import datetime, timedelta
import re
import plotly.express as px

# 1. САЙТ СОЗЛАМАЛАРИ
st.set_page_config(page_title="ABS - Business Intelligence", page_icon="🛡️", layout="wide")

# СЕССИЯ ХОТИРАСИ
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_db" not in st.session_state:
    st.session_state.user_db = {
        "baho123": {"pass": "qWe83664323546", "role": "superadmin"},
        "user_pro": {"pass": "abs_user_2026", "role": "user"}
    }
if "search_history" not in st.session_state:
    st.session_state.search_history = []

# --- КИРИШ ТИЗИМИ ---
def login_page():
    st.title("🚀 ABS - Тизимга кириш")
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.markdown('<div style="padding: 2.5rem; border-radius: 15px; background-color: white; border: 1px solid #ddd; box-shadow: 0 10px 20px rgba(0,0,0,0.1);">', unsafe_allow_html=True)
        u = st.text_input("Логин:")
        p = st.text_input("Пароль:", type="password")
        if st.button("ТИЗИМГА КИРИШ"):
            if u in st.session_state.user_db and st.session_state.user_db[u]["pass"] == p:
                st.session_state.authenticated = True
                st.session_state.current_user = u
                st.session_state.user_role = st.session_state.user_db[u]["role"]
                st.rerun()
            else: st.error("Логин ёки пароль хато!")
        st.markdown('</div>', unsafe_allow_html=True)

# --- ЁРДАМЧИ ФУНКЦИЯЛАР ---
def format_numbers(n):
    if n >= 1000000: return f"{round(n/1000000, 1)}M"
    elif n >= 1000: return f"{round(n/1000, 1)}K"
    return str(n)

def get_full_uzb_date(iso_date):
    """Санани 2026-21-Март форматига ўтказади"""
    months = {1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь", 
              7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"}
    try:
        dt = datetime.strptime(re.sub(r'\.\d+Z', 'Z', iso_date), '%Y-%m-%dT%H:%M:%SZ')
        return f"{dt.year}-{dt.day}-{months[dt.month]}"
    except: return iso_date[:10]

def get_video_type(duration_iso):
    try:
        duration = isodate.parse_duration(duration_iso).total_seconds()
        return "📱 Shorts" if duration <= 60 else "🎥 Узун видео"
    except: return "🎥 Узун видео"

# --- АСОСИЙ ЛОГИКА ---
if not st.session_state.authenticated:
    login_page()
else:
    t_list = ["🚀 Вирал Таҳлил", "📖 Тўлиқ Қўлланма", "📜 Тарих", "⚙️ Созламалар"]
    if st.session_state.user_role == "superadmin": t_list.append("👨‍✈️ АДМИН ПАНЕЛ")
    tabs = st.tabs(t_list)

    # 1. АДМИН ПАНЕЛ
    if st.session_state.user_role == "superadmin":
        with tabs[4]:
            st.header("👨‍✈️ Стратегик Бошқарув")
            if st.session_state.search_history:
                df_h = pd.DataFrame(st.session_state.search_history)
                st.plotly_chart(px.bar(df_h['Мавзу'].value_counts().reset_index(), x='index', y='Мавзу', title="Тренд мавзулар"), use_container_width=True)
            st.write("Фойдаланувчилар базаси:", st.session_state.user_db)

    # 2. ҚЎЛЛАНМА (МУКАММАЛ)
    with tabs[1]:
        st.header("📖 ABS Тизимидан фойдаланиш бўйича Йўриқнома")
        st.markdown("---")
        st.subheader("1-Қадам: Google Cloud-дан API калит олиш")
        st.write("YouTube маълумотларини олиш учун сизга шахсий 'Ключ' керак:")
        st.markdown("""
        * **Саҳифага киринг:** [Google Cloud Console](https://console.cloud.google.com/) сайтига Google аккаунтингиз билан киринг.
        * **Лойиҳа яратинг:** Тепадаги 'Select a project' -> 'New Project' тугмасини босинг ва ном беринг.
        * **API-ни ёқинг:** Менюдан 'APIs & Services' -> 'Library'га киринг. Қидирувга **'YouTube Data API v3'** деб ёзинг ва кириб **'ENABLE'** тугмасини босинг.
        * **Калит яратинг:** 'Credentials' бўлимига ўтинг, **'+ CREATE CREDENTIALS'** тугмасини босинг ва **'API Key'** ни танланг.
        * **Нусхаланг:** Тайёр бўлган кодни (масалан: AIza...) нусхалаб, ABS сайтидаги чап менюга қўйинг.
        """)
        st.info("💡 Маслаҳат: Битта калит кунига тахминан 150-200 та қидирув учун бепул хизмат қилади.")

    # 3. АСОСИЙ ТАҲЛИЛ
    with tabs[0]:
        with st.sidebar:
            st.title("🛡️ ABS Панел")
            api_key = st.text_input("🔑 API Key:", type="password")
            topic = st.text_input("🔍 Мавзу:", "Survival Challenge")
            region = st.selectbox("🌍 Давлат:", ["US", "GB", "DE", "UZ", "RU", "TR"])
            days_back = st.select_slider("📅 Давр (кун):", options=[7, 30, 90, 180, 365], value=180)
            min_outl = st.slider("Min Outlier:", 1, 50, 5)
            content_filter = st.radio("Формат:", ["Ҳаммаси", "Фақат Узун", "Фақат Shorts"])
            search_btn = st.button("🚀 ТАҲЛИЛНИ БОШЛАШ")

        if search_btn:
            st.session_state.search_history.append({"Вақт": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ким": st.session_state.current_user, "Мавзу": topic})
            try:
                youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
                pub_after = (datetime.utcnow() - timedelta(days=days_back)).isoformat() + "Z"
                res = youtube.search().list(q=topic, part="snippet", type="video", maxResults=50, order="viewCount", publishedAfter=pub_after, regionCode=region).execute()
                
                data = []
                for item in res['items']:
                    v_id = item['id']['videoId']
                    v_inf = youtube.videos().list(part="statistics,contentDetails,snippet", id=v_id).execute()['items'][0]
                    c_inf = youtube.channels().list(part="statistics,snippet", id=item['snippet']['channelId']).execute()['items'][0]
                    
                    views = int(v_inf['statistics'].get('viewCount', 0))
                    subs = int(c_inf['statistics'].get('subscriberCount', 1))
                    v_type = get_video_type(v_inf['contentDetails']['duration'])
                    outlier = round(views / (subs if subs > 1000 else 1000), 1)
                    
                    # VPH ҳисоблаш
                    dt_pub = datetime.strptime(re.sub(r'\.\d+Z', 'Z', v_inf['snippet']['publishedAt']), '%Y-%m-%dT%H:%M:%SZ')
                    hours_age = max((datetime.utcnow() - dt_pub).total_seconds() / 3600, 1)
                    vph = round(views / hours_age, 1)

                    if outlier >= min_outl:
                        if content_filter == "Фақат Узун" and v_type == "📱 Shorts": continue
                        if content_filter == "Фақат Shorts" and v_type == "🎥 Узун видео": continue

                        data.append({
                            "Расм": v_inf['snippet']['thumbnails']['high']['url'],
                            "Вираллик": outlier,
                            "Сарлавҳа": item['snippet']['title'],
                            "Формати": v_type,
                            "Кўрилишлар": format_numbers(views),
                            "Соатбай (VPH)": f"{format_numbers(vph)}/с",
                            "Обуначилар": format_numbers(subs),
                            "Канал очилган": get_uzb_month(c_inf['snippet']['publishedAt']),
                            "Юкланган сана": get_full_uzb_date(v_inf['snippet']['publishedAt']),
                            "Канал": item['snippet']['channelTitle'],
                            "Ҳавола": f"https://www.youtube.com/watch?v={v_id}"
                        })

                if data:
                    df = pd.DataFrame(data).sort_values(by="Вираллик", ascending=False)
                    
                    # BILLBOARD
                    st.subheader("🏆 Энг Вирал Видеолар (TOP 3)")
                    b_cols = st.columns(3)
                    for i in range(min(3, len(df))):
                        with b_cols[i]:
                            st.image(df.iloc[i]['Расм'], use_container_width=True)
                            st.markdown(f"🔥 **{df.iloc[i]['Вираллик']}x Вираллик**")
                            st.caption(df.iloc[i]['Сарлавҳа'][:60] + "...")
                            st.link_button("📺 Кўриш", df.iloc[i]['Ҳавола'])
                    st.divider()

                    # ЖАДВАЛ
                    st.dataframe(df, column_config={
                        "Расм": st.column_config.ImageColumn("Превью"),
                        "Ҳавола": st.column_config.LinkColumn("🔗"),
                        "Вираллик": st.column_config.ProgressColumn("Outlier", min_value=0, max_value=30, format="%.1f x")
                    }, use_container_width=True, hide_index=True)
                else: st.warning("Натижа йўқ.")
            except: st.error("Хато: API калитни текширинг!")
