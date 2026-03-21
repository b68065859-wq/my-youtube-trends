import streamlit as st
import googleapiclient.discovery
import pandas as pd
from io import BytesIO
import isodate
from datetime import datetime

# 1. САЙТНИ ТЎЛИҚ КЕНГ ЭКРАН ҚИЛИШ (ЭНГ ТЕПАДА ТУРИШИ ШАРТ)
st.set_page_config(
    page_title="YouTube Pro Viral Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Сайтни янада кенгайтириш учун махсус дизайн (CSS)
st.markdown("""
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    stDataFrame {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ЁРДАМЧИ ФУНКЦИЯЛАР ---
def format_numbers(n):
    if n >= 1000000: return f"{round(n/1000000, 1)}M"
    elif n >= 1000: return f"{round(n/1000, 1)}K"
    return str(n)

def format_date(iso_date):
    try:
        dt = datetime.strptime(iso_date, '%Y-%m-%dT%H:%M:%SZ')
        return dt.strftime('%Y-%m-%d | %H:%M')
    except: return iso_date

def get_video_type(duration_iso):
    try:
        duration = isodate.parse_duration(duration_iso).total_seconds()
        return "📱 Shorts" if duration <= 60 else "🎥 Long"
    except: return "🎥 Long"

# --- САЙТНИНГ ЧАП ТОМОНИ (SIDEBAR) ---
with st.sidebar:
    st.title("🔍 Қидирув Созламалари")
    api_key = st.text_input("API Key", value="AIzaSyAE-vwmdFa4Royu56-GArSpm93fg-DOUtM", type="password")
    topic = st.text_input("Мавзу (инглизча):", "Mystery & History")
    min_views = st.number_input("Минимал кўрилиш:", value=500000)
    max_results = st.slider("Натижалар сони", 10, 50, 30)
    st.divider()
    st.info("Viral Score 5 дан баланд бўлса, бу видео трендда!")

# --- АСОСИЙ ОЙНА ---
st.title("📊 YouTube Global Trends Dashboard")

if st.sidebar.button("🚀 ТАҲЛИЛНИ БОШЛАШ", use_container_width=True):
    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
        
        # Видео қидириш
        search_res = youtube.search().list(
            q=topic, 
            part="snippet", 
            type="video", 
            maxResults=max_results, 
            order="viewCount"
        ).execute()
        
        final_data = []
        
        for item in search_res['items']:
            v_id = item['id']['videoId']
            c_id = item['snippet']['channelId']
            
            # Видео ва Канал тафсилотлари
            v_info = youtube.videos().list(part="statistics,contentDetails,snippet", id=v_id).execute()['items'][0]
            c_info = youtube.channels().list(part="snippet,statistics", id=c_id).execute()['items'][0]
            
            views = int(v_info['statistics'].get('viewCount', 0))
            subs = int(c_info['statistics'].get('subscriberCount', 1))
            viral_score = round(views / subs, 2)
            
            if views >= min_views:
                final_data.append({
                    "Превью": v_info['snippet']['thumbnails']['default']['url'],
                    "Ҳолати": "🔥 ВИРАЛ" if viral_score > 5 else "✅ Одатий",
                    "Типи": get_video_type(v_info['contentDetails']['duration']),
                    "Видео номи": item['snippet']['title'],
                    "Канал очилган": datetime.strptime(c_info['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d'),
                    "Жойланган вақти": format_date(v_info['snippet']['publishedAt']),
                    "Кўрилишлар": format_numbers(views),
                    "Обуначилар": format_numbers(subs),
                    "Viral Score": viral_score,
                    "Канал номи": item['snippet']['channelTitle'],
                    "Ҳавола": f"https://www.youtube.com/watch?v={v_id}"
                })

        if final_data:
            df = pd.DataFrame(final_data)
            
            # Натижаларни варақларга бўлиб кўрсатиш
            tab1, tab2 = st.tabs(["📋 Батафсил Жадвал", "📊 Визуал Аналитика"])
            
            with tab1:
                st.dataframe(
                    df,
                    column_config={
                        "Превью": st.column_config.ImageColumn("Расм"),
                        "Ҳавола": st.column_config.LinkColumn("YouTube", display_text="Кўриш 📺"),
                        "Viral Score": st.column_config.ProgressColumn("Вираллик", min_value=0, max_value=20, format="%.2f ⭐"),
                        "Канал очилган": st.column_config.DateColumn("Канал очилган")
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                # Excel юклаш тугмаси
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                st.download_button(
                    "📥 Ҳамма маълумотни Excel-га юклаб олиш", 
                    output.getvalue(), 
                    f"youtube_{topic}.xlsx", 
                    use_container_width=True
                )

            with tab2:
                col_chart1, col_chart2 = st.columns(2)
                with col_chart1:
                    st.subheader("Вираллик бўйича каналлар")
                    st.bar_chart(df.set_index('Канал номи')['Viral Score'])
                with col_chart2:
                    st.subheader("Видео типлари тақсимоти")
                    st.write(df['Типи'].value_count())

        else:
            st.warning("Кўрсатилган фильтр бўйича видео топилмади. Кўрилиш сонини камайтириб кўринг.")

    except Exception as e:
        st.error(f"Хатолик юз берди: {str(e)}")
else:
    st.info("Чап томондаги созламаларни тўлдиринг ва 'Таҳлилни бошлаш' тугмасини босинг.")
