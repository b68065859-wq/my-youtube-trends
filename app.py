import streamlit as st
import googleapiclient.discovery
import pandas as pd
from io import BytesIO
import isodate

# Сайт созламалари
st.set_page_config(page_title="YouTube Viral Analyzer", layout="wide")

# --- ЁРДАМЧИ ФУНКЦИЯЛАР ---
def format_numbers(n):
    if n >= 1000000:
        return f"{round(n/1000000, 1)}M"
    elif n >= 1000:
        return f"{round(n/1000, 1)}K"
    return str(n)

def get_video_type(duration_iso):
    try:
        duration = isodate.parse_duration(duration_iso).total_seconds()
        return "📱 Shorts" if duration <= 60 else "🎥 Long"
    except: return "🎥 Long"

# --- САЙТНИНГ ВИЗУАЛ ҚИСМИ ---
st.title("🚀 YouTube Профессионал Аналитика")

with st.sidebar:
    st.header("⚙️ Созламалар")
    api_key = st.text_input("API Key", value="AIzaSyAE-vwmdFa4Royu56-GArSpm93fg-DOUtM", type="password")
    max_results = st.slider("Қидирув сони", 10, 50, 25)

col1, col2 = st.columns([2, 1])
with col1:
    topic = st.text_input("Мавзуни ёзинг:", "Historical Mysteries Documentary")
with col2:
    min_views = st.number_input("Минимал кўрилиш:", value=100000)

if st.button("📈 Трендларни таҳлил қилиш"):
    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
        
        search_res = youtube.search().list(q=topic, part="snippet", type="video", maxResults=max_results, order="viewCount").execute()
        
        final_data = []
        for item in search_res['items']:
            v_id = item['id']['videoId']
            c_id = item['snippet']['channelId']
            
            v_info = youtube.videos().list(part="statistics,contentDetails", id=v_id).execute()['items'][0]
            c_info = youtube.channels().list(part="statistics", id=c_id).execute()['items'][0]
            
            views = int(v_info['statistics'].get('viewCount', 0))
            subs = int(c_info['statistics'].get('subscriberCount', 1))
            v_type = get_video_type(v_info['contentDetails']['duration'])
            viral_score = round(views / subs, 2) if subs > 0 else 0
            
            if views >= min_views:
                final_data.append({
                    "Ҳолати": "🔥 ВИРАЛ" if viral_score > 5 else "✅ Одатий",
                    "Типи": v_type,
                    "Видео номи": item['snippet']['title'],
                    "Кўрилишлар": format_numbers(views),
                    "Обуначилар": format_numbers(subs),
                    "Viral Score": viral_score,
                    "Канал": item['snippet']['channelTitle'],
                    "Ҳавола": f"https://www.youtube.com/watch?v={v_id}"
                })
        
        if final_data:
            df = pd.DataFrame(final_data)
            
            # Жадвални чиройли қилиб кўрсатиш (Ҳаволани босиладиган қилиш)
            st.success(f"Топ натижалар: {len(final_data)} та")
            
            # Сонлар ва линк учун махсус формат
            st.dataframe(
                df,
                column_config={
                    "Ҳавола": st.column_config.LinkColumn("Видеога ўтиш", display_text="Кўриш 📺"),
                    "Viral Score": st.column_config.NumberColumn("Вираллик", format="%.2f ⭐"),
                },
                use_container_width=True,
                hide_index=True
            )

            # Excel юклаш
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Натижаларни Excel қилиб олиш", output.getvalue(), f"{topic}_report.xlsx")
            
        else:
            st.warning("Натижа топилмади.")
            
    except Exception as e:
        st.error(f"Хатолик: {str(e)}")

st.divider()
st.caption("Керакли маълумотлар автоматик сараланди.")
