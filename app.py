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

# СЕССИЯ ХОТИРАСИ (БАЗА)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_db" not in st.session_state:
    # СИЗНИНГ ЯНГИ МАЪЛУМОТЛАРИНГИЗ ВА ФОЙДАЛАНУВЧИЛАР
    st.session_state.user_db = {
        "baho123": {"pass": "qWe83664323546", "role": "superadmin"},
        "user_pro": {"pass": "abs_user_2026", "role": "user"},
        "guest": {"pass": "guest123", "role": "user"}
    }
if "search_history" not in st.session_state:
    st.session_state.search_history = []

# --- КИРИШ ТИЗИМИ ---
def login_page():
    st.title("🚀 ABS - Тизимга кириш")
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.markdown('<div style="padding: 2rem; border-radius: 15px; background-color: white; border: 1px solid #ddd; box-shadow: 0 10px 20px rgba(0,0,0,0.1);">', unsafe_allow_html=True)
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

# --- АДМИН ПАНЕЛ ВА ГРАФИКЛАР ---
def admin_panel_ui():
    st.header("👨‍✈️ Админ Стратегик Бошқаруви")
    
    t1, t2, t3 = st.tabs(["📊 Мавзулар Аналитикаси", "👥 Фойдаланувчилар", "📜 Тўлиқ Тарих"])
    
    with t1:
        st.subheader("📈 Энг кўп қидирилган мавзулар (Trend Analysis)")
        if st.session_state.search_history:
            df_hist = pd.DataFrame(st.session_state.search_history)
            # Мавзулар бўйича график чизиш
            topic_counts = df_hist['Мавзу'].value_counts().reset_index()
            topic_counts.columns = ['Мавзу', 'Қидирув сони']
            
            fig = px.bar(topic_counts, x='Мавзу', y='Қидирув сони', 
                         color='Қидирув сони', title="Қайси мавзуларга талаб катта?",
                         color_continuous_scale='Reds')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("График чизиш учун ҳали маълумот етарли эмас.")

    with t2:
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("Фойдаланувчилар Базаси")
            u_list = [{"Логин": k, "Пароли": v["pass"], "Роли": v["role"]} for k, v in st.session_state.user_db.items()]
            st.dataframe(pd.DataFrame(u_list), use_container_width=True)
        with col_r:
            st.subheader("Янги фойдаланувчи қўшиш")
            new_u = st.text_input("Янги Логин:")
            new_p = st.text_input("Янги Пароль:")
            if st.button("ҚЎШИШ"):
                st.session_state.user_db[new_u] = {"pass": new_p, "role": "user"}
                st.success("Фойдаланувчи қўшилди!")
                st.rerun()

    with t3:
        if st.session_state.search_history:
            st.dataframe(pd.DataFrame(st.session_state.search_history), use_container_width=True)
        else:
            st.write("Тарих бўш.")

# --- ЁРДАМЧИ ФУНКЦИЯЛАР ---
def format_numbers(n):
    if n >= 1000000: return f"{round(n/1000000, 1)}M"
    elif n >= 1000: return f"{round(n/1000, 1)}K"
    return str(n)

# --- АСОСИЙ ЛОГИКА ---
if not st.session_state.authenticated:
    login_page()
else:
    t_list = ["🚀 Вирал Таҳлил", "📜 Менинг тарихим", "⚙️ Созламалар"]
    if st.session_state.user_role == "superadmin":
        t_list.append("👨‍✈️ АДМИН ПАНЕЛ")
    
    tabs = st.tabs(t_list)

    if st.session_state.user_role == "superadmin":
        with tabs[3]:
            admin_panel_ui()

    with tabs[2]:
        st.subheader(f"Профиль: {st.session_state.current_user}")
        if st.button("🚪 Чиқиш"):
            st.session_state.authenticated = False
            st.rerun()

    with tabs[1]:
        st.header("📜 Сизнинг тарихингиз")
        my_h = [x for x in st.session_state.search_history if x["Ким"] == st.session_state.current_user]
        if my_h: st.table(pd.DataFrame(my_h))
        else: st.info("Тарих бўш.")

    with tabs[0]:
        with st.sidebar:
            st.title("🛡️ ABS Панел")
            api_key = st.text_input("🔑 API Key:", type="password")
            topic = st.text_input("🔍 Мавзу:", "Space Secrets")
            region = st.selectbox("🌍 Давлат:", ["US", "GB", "DE", "UZ", "RU"])
            min_outl = st.slider("Min Outlier:", 1, 50, 5)
            search_btn = st.button("🚀 ТАҲЛИЛНИ БОШЛАШ")

        if search_btn:
            # Тарихга ёзиш
            st.session_state.search_history.append({
                "Вақт": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Ким": st.session_state.current_user,
                "Мавзу": topic,
                "Давлат": region
            })
            
            try:
                youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
                res = youtube.search().list(q=topic, part="snippet", type="video", maxResults=30, order="viewCount", regionCode=region).execute()
                
                data = []
                for item in res['items']:
                    v_id = item['id']['videoId']
                    v_inf = youtube.videos().list(part="statistics,snippet", id=v_id).execute()['items'][0]
                    c_inf = youtube.channels().list(part="statistics", id=item['snippet']['channelId']).execute()['items'][0]
                    v_count = int(v_inf['statistics'].get('viewCount', 0))
                    s_count = int(c_inf['statistics'].get('subscriberCount', 1))
                    outlier = round(v_count / (s_count if s_count > 1000 else 1000), 1)
                    
                    if outlier >= min_outl:
                        data.append({
                            "Расм": v_inf['snippet']['thumbnails']['default']['url'],
                            "Вираллик": outlier,
                            "Сарлавҳа": item['snippet']['title'],
                            "Кўрилишлар": format_numbers(v_count),
                            "Канал": item['snippet']['channelTitle'],
                            "Ҳавола": f"https://www.youtube.com/watch?v={v_id}"
                        })

                if data:
                    st.dataframe(pd.DataFrame(data), column_config={"Расм": st.column_config.ImageColumn(), "Ҳавола": st.column_config.LinkColumn("📺")}, use_container_width=True, hide_index=True)
                else: st.warning("Натижа йўқ.")
            except: st.error("Хато: API калитни текширинг.")
