import streamlit as st
import googleapiclient.discovery
import pandas as pd
from io import BytesIO
import isodate
from datetime import datetime, timedelta
import re

# 1. САЙТНИ ТЎЛИҚ КЕНГ ЭКРАН ҚИЛИШ ВА ЎЗБЕКЧА НОМ
st.set_page_config(
    page_title="YouTube Про-Аналитика",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Экранни кенгайтириш учун CSS
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 0rem; padding-left: 2rem; padding-right: 2rem; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 1px solid #d1d5db; }
    </style>
    """, unsafe_allow_html=True)

# --- ЁРДАМЧИ ФУНКЦИЯЛАР (ЎЗБЕКЧА ФОРМАТ) ---
def format_numbers(n):
    if n >= 1000000: return f"{round(n/1000000, 1)}M"
    elif n >= 1000: return f"{round(n/1000, 1)}K"
    return str(n)

def format_date_str(iso_date):
    try:
        clean_date = re.sub(r'\.\d+Z', 'Z', iso_date)
        dt = datetime.strptime(clean_date, '%Y-%m-%dT%H:%M:%SZ')
        return dt.strftime('%Y-%m-%d | %H:%M')
    except: return iso_date[:10]

def get_video_type(duration_iso):
    try:
        duration = isodate.parse_duration(duration_iso).total_seconds()
        return "📱 Shorts" if duration <= 60 else "🎥 Узун"
    except: return "🎥 Узун"

# --- САЙТНИНГ ЧАП ТОМОНИ (SIDEBAR) ---
with st.sidebar:
    st.title("🔍 Қидирув Созламалари")
    api_key = st.text_input("API калит (Key)", value="AIzaSyAE-vwmdFa4Royu56-GArSpm93fg-DOUtM", type="password")
    topic = st.text_input("Мавзуни ёзинг:", "Mystery Documentary")
    min_views = st.number_input("Минимал кўрилиш:", value=100000)
    
    st.divider()
    st.write("📅 **Давр:** Охирги 6 ой")
    published_after = (datetime.utcnow() - timedelta(days=180)).isoformat() + "Z"
    
    max_results = st.slider("Натижалар сони", 10, 50, 30)
    search_btn = st.button("🚀 ТАҲЛИЛНИ БОШЛАШ", use_container_width=True)

# --- АСОСИЙ ОЙНА ---
st.title("📊 YouTube Вирал Аналитика (ViewStats Dashboard)")

if search_btn:
    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
        
        # Видео қидириш (6 ойлик чегара билан)
        search_res = youtube.search().list(
            q=topic, part="snippet", type="video", 
            maxResults=max_results, order="viewCount",
            publishedAfter=published_after
        ).execute()
        
        final_data = []
        for item in search_res['items']:
            v_id = item['id']['videoId']
            c_id = item['snippet']['channelId']
            
            # Видео ва Канал маълумотлари
            v_info = youtube.videos().list(part="statistics,contentDetails,snippet", id=v_id).execute()['items'][0]
            c_info = youtube.channels().list(part="statistics,snippet", id=c_id).execute()['items'][0]
            
            views = int(v_info['statistics'].get('viewCount', 0))
            subs = int(c_info['statistics'].get('subscriberCount', 1))
            pub_date_raw = v_info['snippet']['publishedAt']
            
            # 1. Velocity (Соатбай кўрилиш)
            clean_date = re.sub(r'\.\d+Z', 'Z', pub_date_raw)
            dt_pub = datetime.strptime(clean_date, '%Y-%m-%dT%H:%M:%SZ')
            hours_age = (datetime.utcnow() - dt_pub).total_seconds() / 3600
            velocity = round(views / hours_age, 1) if hours_age > 0 else 0
            
            # 2. Outlier Score (Вираллик коэффициенти)
            # Агар канал жуда кичик бўлса, ҳисобни тўғрилаш учун минимум 500 та обуначи деб оламиз
            effective_subs = subs if subs > 500 else 500
            outlier_score = round(views / effective_subs, 2)
            
            if views >= min_views:
                final_data.append({
                    "Превью": v_info['snippet']['thumbnails']['default']['url'],
                    "Ҳолати": "⭐ OUTLIER" if outlier_score > 10 else ("🔥 Вирал" if outlier_score > 5 else "✅ Одатий"),
                    "Типи": get_video_type(v_info['contentDetails']['duration']),
                    "Видео номи": item['snippet']['title'],
                    "Кўрилишлар (Сон)": views, # Саралаш учун асл сон керак
                    "Кўрилишлар": format_numbers(views),
                    "Соатбай (VPH)": f"{format_numbers(velocity)}/с",
                    "Outlier Score": outlier_score,
                    "Обуначилар": format_numbers(subs),
                    "Канал очилган": c_info['snippet']['publishedAt'][:10],
                    "Жойланган вақти": format_date_str(pub_date_raw),
                    "Канал номи": item['snippet']['channelTitle'],
                    "Ҳавола": f"https://www.youtube.com/watch?v={v_id}"
                })

        if final_data:
            df = pd.DataFrame(final_data)
            # Энг виралларини тепага чиқариш
            df = df.sort_values(by="Outlier Score", ascending=False)
            
            # ТЕПА ПАНЕЛ (Метрикалар)
            m1, m2, m3 = st.columns(3)
            m1.metric("Энг юқори вираллик", f"{df['Outlier Score'].max()}x")
            m2.metric("Топ Соатбай кўрилиш", df['Соатбай (VPH)'].iloc[0])
            m3.metric("Жами топилди", len(df))

            tab1, tab2 = st.tabs(["📋 Асосий Жадвал", "📊 Аналитика ва Графиклар"])
            
            with tab1:
                st.dataframe(
                    df.drop(columns=["Кўрилишлар (Сон)"]), # Асл сонни жадвалда яширамиз
                    column_config={
                        "Превью": st.column_config.ImageColumn("Расм"),
                        "Ҳавола": st.column_config.LinkColumn("YouTube", display_text="Кўриш 📺"),
                        "Outlier Score": st.column_config.ProgressColumn("Вираллик даражаси", min_value=0, max_value=20, format="%.2f x"),
                        "Канал очилган": st.column_config.DateColumn("Канал очилган")
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                # Excel сақлаш
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                st.download_button("📥 Натижаларни Excel-га юклаш", output.getvalue(), "youtube_pro_report.xlsx", use_container_width=True)

            with tab2:
                st.subheader("Каналлар бўйича Вираллик (Outlier) тақсимоти")
                st.bar_chart(df.set_index('Канал номи')['Outlier Score'])
                
        else:
            st.warning("Охирги 6 ойда бундай кўрилишга эга янги видеолар топилмади.")

    except Exception as e:
        st.error(f"Хатолик юз берди: {str(e)}")
else:
    st.info("Қидирувни бошлаш учун тугмани босинг.")
