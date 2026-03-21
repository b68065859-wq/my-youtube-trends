import streamlit as st
import googleapiclient.discovery
import pandas as pd
from io import BytesIO
import isodate
from datetime import datetime
import re

# 1. САЙТНИ ТЎЛИҚ КЕНГ ЭКРАН ҚИЛИШ
st.set_page_config(
    page_title="YouTube Pro Viral Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Дизайн учун CSS
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 0rem; padding-left: 2rem; padding-right: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- ВАҚТНИ ТЎҒРИЛАШ ФУНКЦИЯСИ (ХАТО ШУ ЕРДА ЭДИ) ---
def format_date(iso_date):
    try:
        # Миллисекундларни (агар бўлса) олиб ташлаймиз
        clean_date = re.sub(r'\.\d+Z', 'Z', iso_date)
        dt = datetime.strptime(clean_date, '%Y-%m-%dT%H:%M:%SZ')
        return dt.strftime('%Y-%m-%d | %H:%M')
    except:
        return iso_date[:10] # Агар ўхшамаса, фақат кунини қайтаради

def format_numbers(n):
    if n >= 1000000: return f"{round(n/1000000, 1)}M"
    elif n >= 1000: return f"{round(n/1000, 1)}K"
    return str(n)

def get_video_type(duration_iso):
    try:
        duration = isodate.parse_duration(duration_iso).total_seconds()
        return "📱 Shorts" if duration <= 60 else "🎥 Long"
    except: return "🎥 Long"

# --- САЙТНИНГ ЧАП ТОМОНИ ---
with st.sidebar:
    st.title("🔍 Қидирув")
    api_key = st.text_input("API Key", value="AIzaSyAE-vwmdFa4Royu56-GArSpm93fg-DOUtM", type="password")
    topic = st.text_input("Мавзу:", "Historical Documentary")
    min_views = st.number_input("Минимал кўрилиш:", value=500000)
    max_results = st.slider("Натижалар сони", 10, 50, 30)
    search_btn = st.sidebar.button("🚀 ТАҲЛИЛНИ БОШЛАШ", use_container_width=True)

# --- АСОСИЙ ОЙНА ---
st.title("📊 YouTube Global Trends Dashboard")

if search_btn:
    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
        search_res = youtube.search().list(q=topic, part="snippet", type="video", maxResults=max_results, order="viewCount").execute()
        
        final_data = []
        for item in search_res['items']:
            v_id = item['id']['videoId']
            c_id = item['snippet']['channelId']
            
            v_info = youtube.videos().list(part="statistics,contentDetails,snippet", id=v_id).execute()['items'][0]
            c_info = youtube.channels().list(part="snippet,statistics", id=c_id).execute()['items'][0]
            
            views = int(v_info['statistics'].get('viewCount', 0))
            subs = int(c_info['statistics'].get('subscriberCount', 1))
            viral_score = round(views / subs, 2)
            
            if views >= min_views:
                final_data.append({
                    "Расм": v_info['snippet']['thumbnails']['default']['url'],
                    "Ҳолати": "🔥 ВИРАЛ" if viral_score > 5 else "✅ Одатий",
                    "Типи": get_video_type(v_info['contentDetails']['duration']),
                    "Видео номи": item['snippet']['title'],
                    "Канал очилган": format_date(c_info['snippet']['publishedAt']),
                    "Жойланган вақти": format_date(v_info['snippet']['publishedAt']),
                    "Кўрилишлар": format_numbers(views),
                    "Обуначилар": format_numbers(subs),
                    "Viral Score": viral_score,
                    "Канал номи": item['snippet']['channelTitle'],
                    "Ҳавола": f"https://www.youtube.com/watch?v={v_id}"
                })

        if final_data:
            df = pd.DataFrame(final_data)
            tab1, tab2 = st.tabs(["📋 Асосий Жадвал", "📊 Графиклар"])
            
            with tab1:
                st.dataframe(
                    df,
                    column_config={
                        "Расм": st.column_config.ImageColumn(),
                        "Ҳавола": st.column_config.LinkColumn("YouTube", display_text="Кўриш"),
                        "Viral Score": st.column_config.ProgressColumn(min_value=0, max_value=20, format="%.2f ⭐")
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                st.download_button("📥 Excel-га юклаш", output.getvalue(), "trends.xlsx", use_container_width=True)

            with tab2:
                st.bar_chart(df.set_index('Канал номи')['Viral Score'])

        else:
            st.warning("Натижа топилмади.")

    except Exception as e:
        st.error(f"Хатолик: {str(e)}")
