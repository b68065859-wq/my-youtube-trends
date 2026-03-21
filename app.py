import streamlit as st
import googleapiclient.discovery
import pandas as pd
from io import BytesIO
import isodate

# Сайт созламалари
st.set_page_config(page_title="YouTube Viral Analyzer", layout="wide")
st.title("🚀 YouTube Вирал Контент Топгич")

# 1. СОЗЛАМАЛАР ВА ФИЛЬТРЛАР
with st.sidebar:
    st.header("⚙️ Созламалар")
    api_key = st.text_input("API Key", value="AIzaSyAE-vwmdFa4Royu56-GArSpm93fg-DOUtM", type="password")
    max_results = st.slider("Қидирув сони", 10, 50, 20)
    st.info("Viral Score: Видео кўрилишини канал обуначисига бўлгандаги натижа. Агар 5 дан баланд бўлса - бу жуда зўр!")

col1, col2 = st.columns(2)
with col1:
    topic = st.text_input("Қидирув мавзуси (инглизча тавсия этилади):", "Luxury Life Documentary")
with col2:
    min_views = st.number_input("Минимал кўрилиш сони:", value=500000)

# Функционал қисм
def get_video_type(duration_iso):
    try:
        duration = isodate.parse_duration(duration_iso).total_seconds()
        return "📱 Shorts" if duration <= 60 else "🎥 Long"
    except: return "🎥 Long"

if st.button("📈 Трендларни таҳлил қилиш"):
    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
        
        # Қидирув
        search_res = youtube.search().list(q=topic, part="snippet", type="video", maxResults=max_results, order="viewCount").execute()
        
        final_data = []
        for item in search_res['items']:
            v_id = item['id']['videoId']
            c_id = item['snippet']['channelId']
            
            # Видео ва Канал маълумотларини олиш
            v_info = youtube.videos().list(part="statistics,contentDetails", id=v_id).execute()['items'][0]
            c_info = youtube.channels().list(part="statistics", id=c_id).execute()['items'][0]
            
            views = int(v_info['statistics'].get('viewCount', 0))
            subs = int(c_info['statistics'].get('subscriberCount', 1)) # 0 бўлмаслиги учун 1
            v_type = get_video_type(v_info['contentDetails']['duration'])
            
            # Viral Score ҳисоблаш (Кўрилиш / Обуначи)
            viral_score = round(views / subs, 2) if subs > 0 else 0
            
            if views >= min_views:
                final_data.append({
                    "Ҳолати": "🔥 ВИРАЛ" if viral_score > 5 else "✅ Одатий",
                    "Типи": v_type,
                    "Видео номи": item['snippet']['title'],
                    "Кўрилишлар": views,
                    "Обуначилар": subs,
                    "Viral Score": viral_score,
                    "Канал": item['snippet']['channelTitle'],
                    "Ҳавола": f"https://www.youtube.com/watch?v={v_id}"
                })
        
        if final_data:
            df = pd.DataFrame(final_data)
            # Вирал бўлганларини тепага чиқариш
            df = df.sort_values(by="Viral Score", ascending=False)
            
            st.success(f"Таҳлил якунланди! {len(final_data)} та видео топилди.")
            st.dataframe(df, use_container_width=True)

            # Excel юклаш
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Натижаларни Excel қилиб олиш", output.getvalue(), f"{topic}_trends.xlsx")
            
        else:
            st.warning("Бундай натижа топилмади. Филтрни камайтириб кўринг.")
            
    except Exception as e:
        st.error(f"Хатолик: {str(e)}")
