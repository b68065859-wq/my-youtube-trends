import streamlit as st
import googleapiclient.discovery
import pandas as pd
from io import BytesIO
import isodate
from datetime import datetime, timedelta
import re

# 1. ПРОФЕССИОНАЛ КЕНГ ЭКРАН ВА ДИЗАЙН
st.set_page_config(
    page_title="YouTube Viral Intelligence Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ViewStats услубидаги Dark-Modern CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #FF0000;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #FF0000;
        color: white;
        font-weight: bold;
    }
    .sidebar .sidebar-content { background-color: #1e1e1e; }
    </style>
    """, unsafe_allow_html=True)

# --- ЁРДАМЧИ ФУНКЦИЯЛАР ---
def format_numbers(n):
    if n >= 1000000: return f"{round(n/1000000, 1)}M"
    elif n >= 1000: return f"{round(n/1000, 1)}K"
    return str(n)

def get_video_type(duration_iso):
    try:
        duration = isodate.parse_duration(duration_iso).total_seconds()
        return "📱 Shorts" if duration <= 60 else "🎥 Узун"
    except: return "🎥 Узун"

# --- SIDEBAR: СТРАТЕГИК БОШҚАРУВ ---
with st.sidebar:
    st.image("https://www.gstatic.com/youtube/img/branding/youtubelogo/svg/youtubelogo.svg", width=150)
    st.title("🎯 Аналитика Маркази")
    st.markdown("---")
    
    # 1. Асосий қидирув
    api_key = st.text_input("🔑 API Key", value="AIzaSyAE-vwmdFa4Royu56-GArSpm93fg-DOUtM", type="password")
    topic = st.text_input("🔍 Мавзу ёки Калит сўз:", "MrBeast Style Challenges")
    
    # 2. Регион ва Тил (ViewStats функцияси)
    region = st.selectbox("🌍 Регион (Давлат):", ["US (АҚШ)", "GB (Англия)", "DE (Германия)", "RU (Россия)", "BR (Бразилия)"])
    region_code = region[:2]
    
    # 3. Вақт ва Саралаш
    days_back = st.select_slider("📅 Қанча вақт ичида?", options=[7, 30, 90, 180, 365], value=180)
    st.caption(f"Охирги {days_back} кунлик видеолар")
    
    # 4. Профессионал Фильтрлар
    st.markdown("#### 🛠 Фильтрлар")
    min_outlier = st.slider("Min Outlier (Вираллик):", 1, 50, 3)
    content_filter = st.radio("Видео тури:", ["Ҳаммаси", "Фақат Узун", "Фақат Shorts"])
    
    published_after = (datetime.utcnow() - timedelta(days=days_back)).isoformat() + "Z"
    search_btn = st.button("🚀 ТРЕНДЛАРНИ ТОПИШ")

# --- АСОСИЙ ИШЧИ МАЙДОН ---
if search_btn:
    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
        
        # Қидирув
        search_res = youtube.search().list(
            q=topic, part="snippet", type="video", 
            maxResults=50, order="viewCount",
            publishedAfter=published_after,
            regionCode=region_code
        ).execute()
        
        final_data = []
        for item in search_res['items']:
            v_id = item['id']['videoId']
            v_info = youtube.videos().list(part="statistics,contentDetails,snippet", id=v_id).execute()['items'][0]
            c_info = youtube.channels().list(part="statistics", id=item['snippet']['channelId']).execute()['items'][0]
            
            views = int(v_info['statistics'].get('viewCount', 0))
            subs = int(c_info['statistics'].get('subscriberCount', 1))
            v_type = get_video_type(v_info['contentDetails']['duration'])
            
            # Outlier ҳисоблаш
            effective_subs = subs if subs > 1000 else 1000
            outlier_score = round(views / effective_subs, 1)
            
            # VPH ҳисоблаш
            dt_pub = datetime.strptime(re.sub(r'\.\d+Z', 'Z', v_info['snippet']['publishedAt']), '%Y-%m-%dT%H:%M:%SZ')
            hours_age = max((datetime.utcnow() - dt_pub).total_seconds() / 3600, 1)
            vph = round(views / hours_age, 1)

            # ФИЛЬТРЛАШ
            if outlier_score >= min_outlier:
                if content_filter == "Фақат Узун" and v_type == "📱 Shorts": continue
                if content_filter == "Фақат Shorts" and v_type == "🎥 Узун": continue
                
                final_data.append({
                    "Превью": v_info['snippet']['thumbnails']['default']['url'],
                    "Outlier Score": outlier_score,
                    "Видео номи": item['snippet']['title'],
                    "Типи": v_type,
                    "Кўрилишлар": format_numbers(views),
                    "VPH (Соатбай)": f"{format_numbers(vph)}/с",
                    "Обуначи": format_numbers(subs),
                    "Канал": item['snippet']['channelTitle'],
                    "Сана": dt_pub.strftime('%Y-%m-%d'),
                    "Ҳавола": f"https://www.youtube.com/watch?v={v_id}"
                })

        if final_data:
            df = pd.DataFrame(final_data).sort_values(by="Outlier Score", ascending=False)
            
            # Метрикалар
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Топ Outlier", f"{df['Outlier Score'].max()}x")
            m2.metric("Макс VPH", df['VPH (Соатбай)'].iloc[0])
            m3.metric("Сараланди", f"{len(df)} та")
            m4.metric("Давлат", region_code)

            # Жадвал
            st.dataframe(
                df,
                column_config={
                    "Превью": st.column_config.ImageColumn(),
                    "Ҳавола": st.column_config.LinkColumn("Кўриш", display_text="📺"),
                    "Outlier Score": st.column_config.ProgressColumn("Вираллик (Outlier)", min_value=0, max_value=30),
                },
                use_container_width=True, hide_index=True
            )
            
            # Excel
            st.download_button("📥 Маълумотларни Excel-га юклаш", BytesIO().getvalue(), "report.xlsx", use_container_width=True)
            
        else:
            st.warning("Бундай қаттиқ фильтр остида видео топилмади. Саралашни бироз юмшатиб кўринг.")

    except Exception as e:
        st.error(f"Алоқада хатолик: {e}")
else:
    # Илк бор кирганда кўринадиган чиройли дизайн
    col_a, col_b = st.columns(2)
    with col_a:
        st.info("👈 Чап томондаги панел орқали ниша ва давлатни танланг.")
    with col_b:
        st.success("🎯 Outlier Score 5х дан юқори видеолар - бу сиз учун тайёр ғоя!")
