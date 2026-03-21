import streamlit as st
import googleapiclient.discovery
import pandas as pd
from io import BytesIO
import isodate
from datetime import datetime, timedelta
import re

# 1. ТЎЛИҚ КЕНГ ЭКРАН ВА ДИЗАЙН
st.set_page_config(page_title="ViewStats Pro - Analytics", layout="wide")

st.markdown("""
    <style>
    .block-container { padding: 1.5rem 2rem; }
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- ЁРДАМЧИ ФУНКЦИЯЛАР ---
def format_date(iso_date):
    try:
        clean_date = re.sub(r'\.\d+Z', 'Z', iso_date)
        dt = datetime.strptime(clean_date, '%Y-%m-%dT%H:%M:%SZ')
        return dt
    except: return datetime.now()

def format_numbers(n):
    if n >= 1000000: return f"{round(n/1000000, 1)}M"
    elif n >= 1000: return f"{round(n/1000, 1)}K"
    return str(n)

# --- АСОСИЙ ОЙНА ---
st.title("🚀 ViewStats Clone: Outlier Finder")

with st.sidebar:
    st.header("📊 Контент Стратегияси")
    api_key = st.text_input("API Key", value="AIzaSyAE-vwmdFa4Royu56-GArSpm93fg-DOUtM", type="password")
    topic = st.text_input("Нишани ёзинг (масалан: Survival):", "Survival Challenges")
    min_views = st.number_input("Минимал кўрилиш:", value=100000)
    
    st.write("📅 Фильтр: Охирги 6 ой (Fresh Content)")
    published_after = (datetime.utcnow() - timedelta(days=180)).isoformat() + "Z"
    
    max_results = st.slider("Таҳлил сони", 10, 50, 20)
    search_btn = st.button("📈 ТАҲЛИЛНИ БОШЛАШ", use_container_width=True)

if search_btn:
    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
        search_res = youtube.search().list(
            q=topic, part="snippet", type="video", 
            maxResults=max_results, order="viewCount",
            publishedAfter=published_after
        ).execute()
        
        final_data = []
        for item in search_res['items']:
            v_id = item['id']['videoId']
            v_info = youtube.videos().list(part="statistics,contentDetails,snippet", id=v_id).execute()['items'][0]
            c_info = youtube.channels().list(part="statistics,snippet", id=item['snippet']['channelId']).execute()['items'][0]
            
            # Маълумотларни йиғиш
            views = int(v_info['statistics'].get('viewCount', 0))
            subs = int(c_info['statistics'].get('subscriberCount', 1))
            pub_date = format_date(v_info['snippet']['publishedAt'])
            
            # 1. Velocity (Соатига кўрилиш)
            hours_since_pub = (datetime.utcnow() - pub_date).total_seconds() / 3600
            velocity = round(views / hours_since_pub, 1) if hours_since_pub > 0 else 0
            
            # 2. Outlier Score (Вираллик даражаси)
            outlier_score = round(views / subs, 2) if subs > 500 else round(views / 500, 2)
            
            if views >= min_views:
                final_data.append({
                    "Превью": v_info['snippet']['thumbnails']['default']['url'],
                    "Рейтинг": "⭐ OUTLIER" if outlier_score > 10 else ("🔥 Viral" if outlier_score > 5 else "✅ Normal"),
                    "Видео номи": item['snippet']['title'],
                    "Кўрилишлар": views,
                    "Velocity (VPH)": velocity, # Views Per Hour
                    "Outlier Score": outlier_score,
                    "Обуначилар": subs,
                    "Жойланган вақти": pub_date.strftime('%Y-%m-%d'),
                    "Канал": item['snippet']['channelTitle'],
                    "Ҳавола": f"https://www.youtube.com/watch?v={v_id}"
                })

        if final_data:
            df = pd.DataFrame(final_data)
            df = df.sort_values(by="Outlier Score", ascending=False)
            
            # Статистика панеллари
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Энг юқори VPH", f"{df['Velocity (VPH)'].max()} v/h")
            col_m2.metric("Топ Outlier", f"{df['Outlier Score'].max()}x")
            col_m3.metric("Жами видео", len(df))

            tab1, tab2 = st.tabs(["📊 Таҳлилий Жадвал", "📈 Ўсиш Графиги"])
            
            with tab1:
                st.dataframe(
                    df,
                    column_config={
                        "Превью": st.column_config.ImageColumn(),
                        "Ҳавола": st.column_config.LinkColumn("YouTube", display_text="Кўриш"),
                        "Outlier Score": st.column_config.ProgressColumn("Outlier Даражаси", min_value=0, max_value=20),
                        "Кўрилишлар": st.column_config.NumberColumn(format="%d"),
                        "Velocity (VPH)": st.column_config.NumberColumn("Соатбай кўрилиш", format="%.1f 🚀")
                    },
                    use_container_width=True, hide_index=True
                )
                
                # Excel сақлаш
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                st.download_button("📥 ViewStats маълумотларини юклаш", output.getvalue(), "viewstats_report.xlsx", use_container_width=True)

            with tab2:
                st.subheader("Каналлар бўйича Outlier таҳлили")
                st.area_chart(df.set_index('Канал')['Outlier Score'])

    except Exception as e:
        st.error(f"Хатолик: {str(e)}")
