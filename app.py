import streamlit as st
import googleapiclient.discovery
import pandas as pd
from io import BytesIO
import isodate
from datetime import datetime, timedelta
import re

# 1. САЙТНИ ТЎЛИҚ КЕНГ ЭКРАН ҚИЛИШ
st.set_page_config(
    page_title="YouTube Вирал Таҳлил",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ўзбекча интерфейс учун махсус CSS ва дизайн
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
    footer {visibility: hidden;}
    /* Жадвалдаги 3 нуқта менюсини ва интерфейсни созлаш */
    div[data-testid="stDataFrame"] button { font-family: 'Arial'; }
    </style>
    """, unsafe_allow_html=True)

# --- ЁРДАМЧИ ФУНКЦИЯЛАР ---
def format_numbers(n):
    if n >= 1000000: return f"{round(n/1000000, 1)}M"
    elif n >= 1000: return f"{round(n/1000, 1)}K"
    return str(n)

def get_uzb_month(iso_date):
    months = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }
    try:
        clean_date = re.sub(r'\.\d+Z', 'Z', iso_date)
        dt = datetime.strptime(clean_date, '%Y-%m-%dT%H:%M:%SZ')
        return f"{dt.year}-{months[dt.month]}"
    except:
        return iso_date[:7]

def get_video_type(duration_iso):
    try:
        duration = isodate.parse_duration(duration_iso).total_seconds()
        return "📱 Shorts" if duration <= 60 else "🎥 Узун видео"
    except: return "🎥 Узун видео"

# --- SIDEBAR: ЎЗБЕКЧА СОЗЛАМАЛАР ---
with st.sidebar:
    st.image("https://www.gstatic.com/youtube/img/branding/youtubelogo/svg/youtubelogo.svg", width=130)
    st.title("🎯 Бошқарув панели")
    st.markdown("---")
    
    api_key = st.text_input("🔑 API калит:", value="AIzaSyAE-vwmdFa4Royu56-GArSpm93fg-DOUtM", type="password")
    topic = st.text_input("🔍 Қидирув мавзуси:", "Historical Mysteries")
    
    region = st.selectbox("🌍 Давлатни танланг:", 
                          ["US (Америка)", "GB (Англия)", "DE (Германия)", "RU (Россия)", "TR (Туркия)", "UZ (Ўзбекистон)"])
    region_code = region[:2]
    
    days_back = st.select_slider("📅 Қанча вақт оралиғида?", options=[7, 30, 90, 180, 365], value=180)
    st.caption(f"Охирги {days_back} кунлик видеолар сараланади")
    
    st.markdown("#### 🛠 Фильтрлар")
    min_outlier = st.slider("Минимал Вираллик (Outlier):", 1, 50, 5)
    content_filter = st.radio("Форматни танланг:", ["Ҳаммаси", "Фақат Узун", "Фақат Shorts"])
    
    published_after = (datetime.utcnow() - timedelta(days=days_back)).isoformat() + "Z"
    search_btn = st.button("🚀 ТАҲЛИЛНИ БОШЛАШ", use_container_width=True)

# --- АСОСИЙ ИШЧИ МАЙДОН ---
st.title("📊 YouTube Вирал Интеллект Дашборди")

if search_btn:
    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
        
        search_res = youtube.search().list(
            q=topic, part="snippet", type="video", 
            maxResults=50, order="viewCount",
            publishedAfter=published_after,
            regionCode=region_code
        ).execute()
        
        final_data = []
        for item in search_res['items']:
            v_id = item['id']['videoId']
            c_id = item['snippet']['channelId']
            
            v_info = youtube.videos().list(part="statistics,contentDetails,snippet", id=v_id).execute()['items'][0]
            c_info = youtube.channels().list(part="statistics,snippet", id=c_id).execute()['items'][0]
            
            views = int(v_info['statistics'].get('viewCount', 0))
            subs = int(c_info['statistics'].get('subscriberCount', 1))
            v_type = get_video_type(v_info['contentDetails']['duration'])
            
            # Outlier ҳисоблаш (MrBeast мантиғи)
            effective_subs = subs if subs > 1000 else 1000
            outlier_score = round(views / effective_subs, 1)
            
            # Соатбай кўрилиш (VPH)
            clean_pub = re.sub(r'\.\d+Z', 'Z', v_info['snippet']['publishedAt'])
            dt_pub = datetime.strptime(clean_pub, '%Y-%m-%dT%H:%M:%SZ')
            hours_age = max((datetime.utcnow() - dt_pub).total_seconds() / 3600, 1)
            vph = round(views / hours_age, 1)

            if outlier_score >= min_outlier:
                if content_filter == "Фақат Узун" and v_type == "📱 Shorts": continue
                if content_filter == "Фақат Shorts" and v_type == "🎥 Узун видео": continue
                
                final_data.append({
                    "Превью": v_info['snippet']['thumbnails']['default']['url'],
                    "Вираллик": outlier_score,
                    "Видео номи": item['snippet']['title'],
                    "Формати": v_type,
                    "Кўрилишлар": format_numbers(views),
                    "Соатбай (VPH)": f"{format_numbers(vph)}/с",
                    "Обуначилар": format_numbers(subs),
                    "Канал очилган": get_uzb_month(c_info['snippet']['publishedAt']),
                    "Юкланган сана": get_uzb_month(v_info['snippet']['publishedAt']),
                    "Канал номи": item['snippet']['channelTitle'],
                    "Ҳавола": f"https://www.youtube.com/watch?v={v_id}"
                })

        if final_data:
            df = pd.DataFrame(final_data).sort_values(by="Вираллик", ascending=False)
            
            # Метрикалар (Юқори панел)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Топ Вираллик", f"{df['Вираллик'].max()}x")
            col2.metric("Топ Соатбай (VPH)", df['Соатбай (VPH)'].iloc[0])
            col3.metric("Сараланган видеолар", len(df))
            col4.metric("Танланган Давлат", region_code)

            # ЖАДВАЛ (Ўзбекча созламалар билан)
            st.dataframe(
                df,
                column_config={
                    "Превью": st.column_config.ImageColumn("Расм"),
                    "Ҳавола": st.column_config.LinkColumn("Кўриш", display_text="📺 Ўтиш"),
                    "Вираллик": st.column_config.ProgressColumn("Outlier Даражаси", min_value=0, max_value=30, format="%.1f x"),
                    "Видео номи": st.column_config.TextColumn("Сарлавҳа", width="large"),
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Excel юклаш тугмаси
            st.markdown("---")
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Натижаларни Excel файл қилиб юклаб олиш", output.getvalue(), "youtube_viral_report.xlsx", use_container_width=True)
            
        else:
            st.warning("Кечирасиз, танланган давр ва фильтр бўйича вирал видеолар топилмади. Саралашни бироз юмшатиб кўринг.")

    except Exception as e:
        st.error(f"Хатолик юз берди: {e}")
else:
    st.info("👈 Қидирувни бошлаш учун чап томондаги 'ТАҲЛИЛНИ БОШЛАШ' тугмасини босинг.")
