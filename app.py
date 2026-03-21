import streamlit as st
import googleapiclient.discovery
import pandas as pd

# 1. Сайтнинг чиройли сарлавҳаси
st.set_page_config(page_title="YouTube Trend Топгич")
st.title("🎥 Менинг YouTube Трендларим")

# 2. Калит сўз ва Фильтр
topic = st.text_input("Нимани қидирамиз?", "Psychology of Wealth")
limit = st.number_input("Минимал кўрилиш сони (Глобал учун)", value=5000000)

# 3. Қидириш тугмаси
if st.button("Қидиришни бошлаш"):
    # Бу ерга ўзингизнинг API KEY-ингизни қўясиз
    api_key = "AIzaSyAE-vwmdFa4Royu56-GArSpm93fg-DOUtM" 
    
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    
    # YouTube-дан маълумот олиш
    res = youtube.search().list(q=topic, part="snippet", type="video", maxResults=20, order="viewCount").execute()
    
    final_list = []
    for item in res['items']:
        v_id = item['id']['videoId']
        stats = youtube.videos().list(part="statistics", id=v_id).execute()['items'][0]
        views = int(stats['statistics'].get('viewCount', 0))
        
        # Фақат белгиланган сондан юқориларини кўрсатамиз
        if views >= limit:
            final_list.append({
                "Номи": item['snippet']['title'],
                "Кўрилиш": f"{views:,}",
                "Ҳавола": f"https://www.youtube.com/watch?v={v_id}"
            })
    
    # Натижани чиқариш
    if final_list:
        st.write(f"✅ {len(final_list)} та видео топилди!")
        st.dataframe(pd.DataFrame(final_list))
    else:
        st.error("Бундай кўп кўрилган видео топилмади.")
