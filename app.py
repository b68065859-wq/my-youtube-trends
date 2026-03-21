import streamlit as st
import googleapiclient.discovery
import pandas as pd
from io import BytesIO
import isodate
from datetime import datetime, timedelta
import re
import plotly.express as px

# 1. САЙТ СОЗЛАМАЛАРИ (БРЕНДИНГ)
st.set_page_config(page_title="ABS - Business Intelligence", page_icon="🛡️", layout="wide")

# СЕССИЯ ХОТИРАСИ (БАЗА)
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
            else:
                st.error("Логин ёки пароль хато!")
        st.markdown('</div>', unsafe_allow_html=True)

# --- ЁРДАМЧИ ФУНКЦИЯЛАР ---
def format_numbers(n):
    if n >= 1000000: return f"{round(n/1000000, 1)}M"
    elif n >= 1000: return f"{round(n/1000, 1)}K"
    return str(n)

def get_uzb_month(iso_date):
    months = {1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь", 7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"}
    try:
        dt = datetime.strptime(re.sub(r'\.\d+Z', 'Z', iso_date), '%Y-%m-%dT%H:%M:%SZ')
        return f"{dt.year}-{months[dt.month]}"
    except: return iso_date[:7]

def get_video_type(duration_iso):
    try:
        duration = isodate.parse_duration(duration_iso).total_seconds()
        return "📱 Shorts" if duration <= 60 else "🎥 Узун видео"
    except: return "🎥 Узун видео"

# --- АДМИН ПАНЕЛ ---
def admin_panel_ui():
    st.header("👨‍✈️ Админ Бошқаруви")
    t1, t2, t3 = st.tabs(["📊 Мавзулар Аналитикаси", "👥 Фойдаланувчилар", "📜 Тўлиқ Тарих"])
    
    with t1:
        if st.session_state.search_history:
            df_hist = pd.DataFrame(st.session_state.search_history)
            topic_counts = df_hist['Мавзу'].value_counts().reset_index()
            topic_counts.columns = ['Мавзу', 'Қидирув сони']
            fig = px.bar(topic_counts, x='Мавзу', y='Қидирув сони', color='Қидирув сони', title="Энг кўп қидирилган мавзулар", color_continuous_scale='Reds')
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Маълумот етарли эмас.")

    with t2:
        u_list = [{"Логин": k, "Пароли": v["pass"], "Роли": v["role"]} for k, v in st.session_state.user_db.items()]
        st.dataframe(pd.DataFrame(u_list), use_container_width=True)
        
    with t3:
        if st.session_state.search_history: st.dataframe(pd.DataFrame(st.session_state.search_history), use_container_width=True)

# --- АСОСИЙ ЛОГИКА ---
if not st.session_state.authenticated:
    login_page()
else:
    # ТАБЛАР (Хаммаси жойида)
    t_list = ["🚀 Вирал Таҳлил", "📖 Қўлланма", "📜 Менинг тарихим", "⚙️ Созламалар"]
    if st.session_state.user_role == "superadmin":
        t_list.append("👨‍✈️ АДМИН ПАНЕЛ")
    
    tabs = st.tabs(t_list)

    # 1. АДМИН ПАНЕЛ
    if st.session_state.user_role == "superadmin":
        with tabs[4]: admin_panel_ui()

    # 2. СОЗЛАМАЛАР
    with tabs[3]:
        st.subheader(f"👤 Профиль: {st.session_state.current_user}")
        if st.button("🚪 Тизимдан чиқиш"):
            st.session_state.authenticated = False
            st.rerun()

    # 3. ТАРИХ
    with tabs[2]:
        st.header("📜 Қидирув тарихингиз")
        my_h = [x for x in st.session_state.search_history if x["Ким"] == st.session_state.current_user]
        if my_h: st.table(pd.DataFrame(my_h))
        else: st.info("Тарих бўш.")

    # 4. ҚЎЛЛАНМА (Бояги Инструкция)
    with tabs[1]:
        st.header("📖 ABS Тизими Қўлланмаси")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("🔑 YouTube API калит олиш")
            st.markdown("""
            1. [Google Cloud Console](https://console.cloud.google.com/)га киринг.
            2. 'YouTube Data API v3'ни фаоллаштиринг (Enable).
            3. 'Credentials' бўлимидан API Key яратинг ва нусхалаб сайтимизга қўйинг.
            """)
        with col_g2:
            st.subheader("📱 Телефонга ўрнатиш")
            st.markdown("""
            1. Браузер менюсидан 'Экранга қўшиш' (Add to Home Screen)ни танланг.
            2. Сайт телефонингизда илова бўлиб кўринади.
            """)

    # 5. АСОСИЙ ТАҲЛИЛ
    with tabs[0]:
        with st.sidebar:
            st.title("🛡️ ABS Панел")
            api_key = st.text_input("🔑 API Key:", type="password")
            topic = st.text_input("🔍 Мавзу:", "Survival")
            region = st.selectbox("🌍 Давлат:", ["US", "GB", "DE", "UZ", "RU", "TR"])
            days_back = st.select_slider("📅 Давр (кун):", options=[7, 30, 90, 180, 365], value=180)
            min_outl = st.slider("Min Outlier:", 1, 50, 5)
            content_filter = st.radio("Формат:", ["Ҳаммаси", "Фақат Узун", "Фақат Shorts"])
            search_btn = st.button("🚀 ТАҲЛИЛНИ БОШЛАШ")

        if search_btn:
            st.session_state.search_history.append({"Вақт": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ким": st.session_state.current_user, "Мавзу": topic, "Давлат": region})
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
                            "Юкланган": get_uzb_month(v_inf['snippet']['publishedAt']),
                            "Канал": item['snippet']['channelTitle'],
                            "Ҳавола": f"https://www.youtube.com/watch?v={v_id}"
                        })

                if data:
                    df = pd.DataFrame(data).sort_values(by="Вираллик", ascending=False)
                    
                    # --- BILLBOARD (TOP 3) ---
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
                else: st.warning("Бу фильтрлар билан видео топилмади.")
            except: st.error("Хато: API калитни текширинг!")
