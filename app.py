import streamlit as st
import googleapiclient.discovery
import pandas as pd
from io import BytesIO
import isodate
from datetime import datetime, timedelta
import re

# 1. САЙТ СОЗЛАМАЛАРИ
st.set_page_config(page_title="ABS - Automation Business System", page_icon="🛡️", layout="wide")

# ДИЗАЙН УЧУН CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #FF0000; color: white; font-weight: bold; }
    .login-box { padding: 2rem; border-radius: 10px; background-color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 1px solid #eee; }
    .guide-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #007bff; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- КИРИШ ТИЗИМИ ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🚀 ABS - Тизимга кириш")
        col1, col2, col3 = st.columns([1,1.5,1])
        with col2:
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            user = st.text_input("Логин:")
            password = st.text_input("Пароль:", type="password")
            if st.button("КИРИШ"):
                if user == "admin" and password == "abs2026":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Логин ёки пароль хато!")
            st.markdown('</div>', unsafe_allow_html=True)
            st.info("Бу тизим YouTube трендларини автоматик таҳлил қилиш учун яратилган.")
        return False
    return True

# --- ЁРДАМЧИ ФУНКЦИЯЛАР ---
def format_numbers(n):
    if n >= 1000000: return f"{round(n/1000000, 1)}M"
    elif n >= 1000: return f"{round(n/1000, 1)}K"
    return str(n)

def get_uzb_month(iso_date):
    months = {1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь", 7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"}
    try:
        clean_date = re.sub(r'\.\d+Z', 'Z', iso_date)
        dt = datetime.strptime(clean_date, '%Y-%m-%dT%H:%M:%SZ')
        return f"{dt.year}-{months[dt.month]}"
    except: return iso_date[:7]

# --- АСОСИЙ ИНТЕРФЕЙС ---
if check_password():
    # Таблар (Варақлар) яратамиз: Асосий таҳлил ва Қўлланма
    tab_main, tab_guide = st.tabs(["🚀 Вирал Таҳлил", "📖 Қўлланма ва API олиш"])

    # --- ҚЎЛЛАНМА ВАРАҒИ ---
    with tab_guide:
        st.header("📚 ABS Тизимидан фойдаланиш қўлланмаси")
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("1. YouTube API Key олиш (Текин)")
            st.markdown("""
            Тизим ишлаши учун сизга шахсий API калит керак. Уни олиш мутлақо бепул:
            1. **[Google Cloud Console](https://console.cloud.google.com/)** сайтига киринг.
            2. Янги лойиҳа очинг (Create Project).
            3. **'Enabled APIs & Services'** бўлимига кириб, **'YouTube Data API v3'** ни қидириб топинг ва **Enable** тугмасини босинг.
            4. **'Credentials'** бўлимига ўтинг ва **'+ Create Credentials'** -> **'API Key'** ни танланг.
            5. Тайёр бўлган кодни нусхалаб олинг ва ABS тизимига қўйинг.
            """)
            
        with col_g2:
            st.subheader("2. Телефонга илова қилиб ўрнатиш")
            st.markdown("""
            ABS-ни Play Market-сиз телефонга ўрнатиш учун:
            1. Сайтни телефонингиз браузерида (Chrome ёки Safari) очинг.
            2. Браузер менюсини (3 нуқта ёки улашиш тугмаси) босинг.
            3. **'Экранга қўшиш' (Добавить на гл. экран / Add to Home Screen)** ни танланг.
            4. Энди сайт телефонингизда алоҳида илова бўлиб кўринади!
            """)
        
        st.divider()
        st.warning("⚠️ Эслатма: Битта бепул API калит кунига 10,000 бирлик (тахминан 100-200 қидирув) учун етади.")

    # --- АСОСИЙ ТАҲЛИЛ ВАРАҒИ ---
    with tab_main:
        with st.sidebar:
            st.title("🛡️ ABS Панел")
            st.write("Фойдаланувчи: **Admin**")
            st.markdown("---")
            api_key = st.text_input("🔑 API Key:", value="AIzaSyAE-vwmdFa4Royu56-GArSpm93fg-DOUtM", type="password", help="API калитни 'Қўлланма' бўлимидан олишингиз мумкин.")
            topic = st.text_input("🔍 Мавзу:", "Survival Challenge")
            region = st.selectbox("🌍 Давлат:", ["US", "GB", "DE", "RU", "UZ", "TR", "KZ"])
            days_back = st.select_slider("📅 Давр (кун):", options=[7, 30, 90, 180, 365], value=180)
            st.markdown("#### ⚙️ Фильтрлар")
            min_outlier = st.slider("Минимал Вираллик (Outlier):", 1, 50, 5)
            content_filter = st.radio("Формат:", ["Ҳаммаси", "Фақат Узун", "Фақат Shorts"])
            
            if st.button("🚪 Тизимдан чиқиш"):
                st.session_state.authenticated = False
                st.rerun()

        st.title("📊 ABS: YouTube Вирал Интеллект")
        search_btn = st.sidebar.button("🚀 ТАҲЛИЛНИ БОШЛАШ")

        if search_btn:
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
                    outlier = round(views / (subs if subs > 1000 else 1000), 1)
                    
                    if outlier >= min_outlier:
                        data.append({
                            "Расм": v_inf['snippet']['thumbnails']['default']['url'],
                            "Вираллик": outlier,
                            "Сарлавҳа": item['snippet']['title'],
                            "Кўрилишлар": format_numbers(views),
                            "Обуначилар": format_numbers(subs),
                            "Канал ёши": get_uzb_month(c_inf['snippet']['publishedAt']),
                            "Юкланган": get_uzb_month(v_inf['snippet']['publishedAt']),
                            "Канал": item['snippet']['channelTitle'],
                            "Ҳавола": f"https://www.youtube.com/watch?v={v_id}"
                        })

                if data:
                    df = pd.DataFrame(data).sort_values(by="Вираллик", ascending=False)
                    st.dataframe(df, column_config={"Расм": st.column_config.ImageColumn(), "Ҳавола": st.column_config.LinkColumn("📺"), "Вираллик": st.column_config.ProgressColumn(min_value=0, max_value=30, format="%.1f x")}, use_container_width=True, hide_index=True)
                    
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False)
                    st.download_button("📥 Натижаларни Excel юклаш", output.getvalue(), "abs_report.xlsx", use_container_width=True)
                else:
                    st.warning("Бу фильтрлар бўйича ҳеч нима топилмади.")
            except Exception as e:
                st.error(f"Хато: {e}. API калитни текшириб кўринг.")
