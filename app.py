import streamlit as st
import googleapiclient.discovery
import pandas as pd
from io import BytesIO
import isodate
from datetime import datetime

# 1. САЙТНИ ТЎЛИҚ ЭКРАН ҚИЛИШ
st.set_page_config(page_title="YouTube Pro Dashboard", layout="wide")

# --- ЁРДАМЧИ ФУНКЦИЯЛАР ---
def format_numbers(n):
    if n >= 1000000: return f"{round(n/1000000, 1)}M"
    elif n >= 1000: return f"{round(n/1000, 1)}K"
    return str(n)

def format_date(iso_date):
    dt = datetime.strptime(iso_date, '%Y-%m-%dT%H:%M:%SZ')
    return dt.strftime('%Y-%m-%d | %H:%M') # Кун ва Соат

def get_video_type(duration_iso):
    try:
        duration = isodate.parse_duration(duration_iso).total_seconds()
        return "📱 Shorts" if duration <= 60 else "🎥 Long"
    except: return "🎥 Long"

# --- САЙТ ДИЗАЙНИ ---
st.title("📊 YouTube Global Trends Dashboard")
st.markdown("---")

# Сон томондаги бошқарув
with st.sidebar:
    st.header("🔍 Қидирув Созламалари")
    api_key = st.text_input("API Key", value="AIzaSyAE-vwmdFa4Royu56-GArSpm93fg-DOUtM", type="password")
    topic = st.text_input("Мавзу:", "AI Documentaries")
    min_views = st.number_input("Минимал кўрилиш:", value=100000)
    max_results = st.slider("Натижалар сони", 10, 50, 30)
    search_btn = st.button("🚀 ТАҲЛИЛНИ БОШЛАШ", use_container_width=True)

if search_btn:
    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
        res = youtube.search().list(q=topic, part="snippet", type="video", maxResults=max_results, order="viewCount").execute()
        
        final_data = []
        for item in res['items']:
            v_id = item['id']['videoId']
            v_info = youtube.videos().list(part="statistics,contentDetails,snippet", id=v_id).execute()['items'][0]
            c_info = youtube.channels().list(part="statistics", id=item['snippet']['channelId']).execute()['items'][0]
            
            views = int(v_info['statistics'].get('viewCount', 0))
            subs = int(c_info['statistics'].get('subscriberCount', 1))
            viral_score = round(views / subs, 2)
            
            if views >= min_views:
                final_data.append({
                    "Расм": v_info['snippet']['thumbnails']['default']['url'],
                    "Ҳолати": "🔥 ВИРАЛ" if viral_score > 5 else "✅ Одатий",
                    "Типи": get_video_type(v_info['contentDetails']['duration']),
                    "Видео номи": item['snippet']['title'],
                    "Юкланган вақти": format_date(v_info['snippet']['publishedAt']),
                    "Кўрилишлар": format_numbers(views),
                    "Обуначилар": format_numbers(subs),
                    "Viral Score": viral_score,
                    "Канал": item['snippet']['channelTitle'],
                    "Ҳавола": f"https://www.youtube.com/watch?v={v_id}"
                })

        if final_data:
            # ВАРАҚЛАРГА БЎЛИШ (TABS)
            tab1, tab2 = st.tabs(["📋 Асосий Жадвал", "📊 Визуал Таҳлил"])
            
            with tab1:
                df = pd.DataFrame(final_data)
                st.dataframe(
                    df,
                    column_config={
                        "Расм": st.column_config.ImageColumn("Превью"),
                        "Ҳавола": st.column_config.LinkColumn("YouTube", display_text="Кўриш"),
                        "Viral Score": st.column_config.ProgressColumn("Вираллик", min_value=0, max_value=20, format="%.2f"),
                    },
                    use_container_width=True, 
                    hide_index=True
                )
                
                # Excel юклаш
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                st.download_button("📥 Excel-га сақлаш", output.getvalue(), "trends.xlsx", use_container_width=True)

            with tab2:
                st.subheader("Вираллик бўйича топ каналлар")
                st.bar_chart(df.set_index('Канал')['Viral Score'])

        else:
            st.warning("Натижа топилмади.")

    except Exception as e:
        st.error(f"Хатолик: {str(e)}")
