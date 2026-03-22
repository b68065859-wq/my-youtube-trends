"""
╔══════════════════════════════════════════════════════╗
║         ABS VIRAL 777 — Professional Edition         ║
║         ViewStats-style YouTube Analytics            ║
╚══════════════════════════════════════════════════════╝

pip install streamlit google-api-python-client pandas pyTelegramBotAPI plotly

Streamlit Cloud → Settings → Secrets:
[general]
BOT_TOKEN         = "123456:ABC..."
ADMIN_CHAT_ID     = "123456789"
PAYME_MERCHANT    = "your_id"
CLICK_SERVICE     = "your_id"
CLICK_MERCHANT    = "your_id"
TELEGRAM_BOT_LINK = "https://t.me/your_bot"
"""

import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re, json, os, base64, uuid, threading, random, string, time

try:
    import telebot
    BOT_AVAILABLE = True
except:
    BOT_AVAILABLE = False

# ══════════════════════════════════════════
# КОНФИГ
# ══════════════════════════════════════════
FREE_TRIAL_LIMIT   = 3
SUBSCRIPTION_PRICE = 50000
SUBSCRIPTION_DAYS  = 30
ADMIN_DB           = {"baho123": "qWe83664323546"}
DB_FILE            = "/tmp/viral777_db.json"

def cfg(key, default=""):
    try:    return st.secrets["general"][key]
    except: return os.environ.get(key, default)

BOT_TOKEN         = cfg("BOT_TOKEN")
ADMIN_CHAT_ID     = cfg("ADMIN_CHAT_ID")
PAYME_MERCHANT    = cfg("PAYME_MERCHANT")
CLICK_SERVICE     = cfg("CLICK_SERVICE")
CLICK_MERCHANT    = cfg("CLICK_MERCHANT")
TELEGRAM_BOT_LINK = cfg("TELEGRAM_BOT_LINK", "https://t.me/your_bot")

# ══════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════
st.set_page_config(
    page_title="Viral 777 — YouTube Analytics",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get Help":None,"Report a bug":None,"About":None}
)

# Dark/Light mode — butun sahifaga ta'sir qiladi
def apply_theme():
    if not st.session_state.get("dark_mode", True):
        st.markdown("""<style>
        /* ══ LIGHT MODE — FULL PAGE ══ */
        html, body, .stApp, .main, .block-container,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewBlockContainer"] {
            background-color: #f0f2f8 !important;
            color: #1a1a2e !important;
        }
        header[data-testid="stHeader"] { background: #f0f2f8 !important; }
        [data-testid="stSidebar"], [data-testid="stSidebar"] > div {
            background: linear-gradient(180deg, #e8eaf6 0%, #dde1f5 100%) !important;
            border-right: 1px solid #c5cae9 !important;
        }
        [data-testid="stSidebar"] * { color: #1a1a2e !important; }
        [data-testid="stSidebar"] input { background: #ffffff !important; color: #1a1a2e !important; border-color: #c5cae9 !important; }
        [data-testid="stSidebar"] [data-baseweb="select"] > div { background: #ffffff !important; color: #1a1a2e !important; border-color: #c5cae9 !important; }
        /* Main content */
        .stat-card { background: #ffffff !important; border-color: #c5cae9 !important; box-shadow: 0 2px 16px rgba(63,81,181,0.08) !important; }
        .stat-label { color: #7986cb !important; }
        .stat-value { color: #1a1a2e !important; }
        .stat-sub   { color: #9fa8da !important; }
        .stat-icon  { opacity: 0.08 !important; }
        .video-card { background: #ffffff !important; border-color: #c5cae9 !important; box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important; }
        .vc-title   { color: #1a1a2e !important; }
        .vc-channel { color: #7986cb !important; }
        .vc-stat-val { color: #1a1a2e !important; }
        .vc-stat-lbl { color: #9fa8da !important; }
        .vs-logo { background: linear-gradient(135deg,#3f51b5,#e91e63) !important; -webkit-background-clip:text !important; -webkit-text-fill-color:transparent !important; }
        .vs-tagline { color: #9fa8da !important; }
        .section-title { color: #1a1a2e !important; }
        .section-title span { color: #7986cb !important; }
        .viral-score-box { background: #ffffff !important; border-color: #c5cae9 !important; }
        .vs-score { background: linear-gradient(135deg,#3f51b5,#e91e63) !important; -webkit-background-clip:text !important; -webkit-text-fill-color:transparent !important; }
        .vs-score-label { color: #7986cb !important; }
        .vs-score-desc  { color: #9fa8da !important; }
        .sub-box  { background: #ffffff !important; border-color: #c5cae9 !important; }
        .act-box  { background: #f5f5ff !important; border-color: #9fa8da !important; }
        .search-hint { background: #e8eaf6 !important; border-color: #c5cae9 !important; color: #3f51b5 !important; }
        /* Tabs */
        [data-baseweb="tab-list"] { background: #e8eaf6 !important; border-bottom: 1px solid #c5cae9 !important; }
        [data-baseweb="tab"] { color: #7986cb !important; background: transparent !important; }
        [aria-selected="true"][data-baseweb="tab"] { color: #3f51b5 !important; border-bottom: 2px solid #3f51b5 !important; background: #dde1f5 !important; }
        /* Inputs */
        input, textarea { background: #ffffff !important; color: #1a1a2e !important; border-color: #c5cae9 !important; }
        [data-baseweb="select"] > div { background: #ffffff !important; color: #1a1a2e !important; border-color: #c5cae9 !important; }
        [data-baseweb="select"] div, [data-baseweb="select"] span, [data-baseweb="select"] p { color: #1a1a2e !important; }
        [data-baseweb="select"] svg { fill: #3f51b5 !important; }
        [data-baseweb="option"] { background: #ffffff !important; color: #1a1a2e !important; }
        [data-baseweb="option"]:hover { background: #e8eaf6 !important; }
        [data-baseweb="popover"], [data-baseweb="popover"] * { background: #ffffff !important; color: #1a1a2e !important; }
        [data-baseweb="menu"], [data-baseweb="menu"] * { background: #ffffff !important; color: #1a1a2e !important; }
        li[role="option"], li[role="option"] * { background: #ffffff !important; color: #1a1a2e !important; }
        li[role="option"]:hover { background: #e8eaf6 !important; }
        /* Buttons */
        .stButton > button { background: linear-gradient(135deg,#3f51b5,#5c6bc0) !important; color: #fff !important; }
        /* Alerts, dataframe */
        [data-testid="stAlert"] { background: #e8eaf6 !important; color: #1a1a2e !important; border-color: #c5cae9 !important; }
        [data-testid="stDataFrame"] { background: #ffffff !important; }
        [data-testid="stDataFrame"] * { background: #ffffff !important; color: #1a1a2e !important; }
        [data-testid="stDataFrame"] th { background: #e8eaf6 !important; color: #3f51b5 !important; }
        [data-testid="stDataFrame"] tr:hover td { background: #f0f2f8 !important; }
        [data-testid="stMarkdownContainer"] p { color: #3a3a5e !important; }
        .stCaption { color: #7986cb !important; }
        hr { border-color: #c5cae9 !important; }
        /* Expander */
        [data-testid="stExpander"] { background: #ffffff !important; border-color: #c5cae9 !important; }
        [data-testid="stExpander"] summary { color: #1a1a2e !important; }
        [data-testid="stExpander"] p { color: #3a3a5e !important; }
        /* Niche buttons */
        .stButton > button[kind="secondary"] { background: #e8eaf6 !important; color: #3f51b5 !important; border: 1px solid #c5cae9 !important; }
        </style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# CSS — ViewStats Dark Pro Style
# ══════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

/* ── RESET ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; }

/* ── HEADER, MANAGE APP, FOOTER YASHIRISH ── */
#MainMenu { visibility: hidden !important; display: none !important; }
header[data-testid="stHeader"] { 
    background: #0a0a0f !important;
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}
[data-testid="stToolbar"] { display: none !important; visibility: hidden !important; }
[data-testid="manage-app-button"] { display: none !important; visibility: hidden !important; }
button[data-testid="manage-app-button"] { display: none !important; }
[class*="manage"] { display: none !important; }
[title="Manage app"] { display: none !important; }
iframe[title="streamlit_app"] { border: none !important; }
.reportview-container .main footer { display: none !important; }
footer, footer * { display: none !important; visibility: hidden !important; }
.viewerBadge_container__r5tak { display: none !important; }
[data-testid="stBottom"] { display: none !important; }

/* ── GLOBAL ── */
html, body, .stApp, .main, .block-container {
    background-color: #0a0a0f !important;
    color: #e8e8f0 !important;
    font-family: 'Inter', sans-serif !important;
}
.block-container { 
    padding: 1.5rem 2rem !important; 
    max-width: 1400px !important;
    padding-top: 1rem !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f1a 0%, #0a0a12 100%) !important;
    border-right: 1px solid #1e1e2e !important;
}
[data-testid="stSidebar"] * { color: #e8e8f0 !important; }
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] input {
    background: #1a1a2e !important;
    border: 1px solid #2a2a4a !important;
    color: #fff !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #1a1a2e !important;
    border: 1px solid #2a2a4a !important;
    border-radius: 8px !important;
}

/* ── ALL INPUTS ── */
input, textarea, [data-baseweb="input"] input {
    background: #1a1a2e !important;
    color: #ffffff !important;
    border: 1px solid #2a2a4a !important;
    border-radius: 8px !important;
}

/* ── SELECTBOX FULL FIX ── */
[data-baseweb="select"] { color: #ffffff !important; }
[data-baseweb="select"] > div {
    background: #1a1a2e !important;
    color: #ffffff !important;
    border: 1px solid #2a2a4a !important;
    border-radius: 8px !important;
}
[data-baseweb="select"] div,
[data-baseweb="select"] span,
[data-baseweb="select"] p,
[data-baseweb="select"] input,
[data-baseweb="select"] [class*="placeholder"],
[data-baseweb="select"] [class*="singleValue"],
[data-baseweb="select"] [class*="ValueContainer"] { color: #ffffff !important; }
[data-baseweb="select"] svg { fill: #ffffff !important; }
[data-baseweb="option"] { background: #1a1a2e !important; color: #ffffff !important; }
[data-baseweb="option"]:hover,
[data-baseweb="option"][aria-selected="true"] { background: #2a2a4a !important; color: #ffffff !important; }
[data-baseweb="popover"] { background: #1a1a2e !important; border: 1px solid #2a2a4a !important; }
[data-baseweb="popover"] * { background: #1a1a2e !important; color: #ffffff !important; }
[data-baseweb="menu"] { background: #1a1a2e !important; }
[data-baseweb="menu"] * { color: #ffffff !important; }
li[role="option"], li[role="option"] * { color: #ffffff !important; background: #1a1a2e !important; }
li[role="option"]:hover { background: #2a2a4a !important; }
[data-testid="stSelectbox"] label { color: #e8e8f0 !important; }

/* ── RADIO ── */
[role="radiogroup"] label, [role="radiogroup"] p,
div[data-testid="stRadio"] label, div[data-testid="stRadio"] p { color: #e8e8f0 !important; }

/* ── SLIDER ── */
[data-testid="stSlider"] p, [data-testid="stSlider"] span,
[data-testid="stSlider"] label { color: #e8e8f0 !important; }

/* ── TABS ── */
[data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #1e1e2e !important;
    gap: 4px !important;
}
[data-baseweb="tab"] {
    color: #666688 !important;
    background: transparent !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 10px 20px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    transition: all 0.2s !important;
}
[data-baseweb="tab"]:hover { color: #aaaacc !important; background: #1a1a2e !important; }
[aria-selected="true"][data-baseweb="tab"] {
    color: #ffffff !important;
    background: #1a1a2e !important;
    border-bottom: 2px solid #6c63ff !important;
}

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, #6c63ff 0%, #5a54e8 100%) !important;
    color: #ffffff !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    border: none !important;
    height: 2.8em !important;
    width: 100% !important;
    transition: all 0.25s !important;
    font-size: 14px !important;
    letter-spacing: 0.3px !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(108,99,255,0.45) !important;
    background: linear-gradient(135deg, #7c73ff 0%, #6a64f8 100%) !important;
}
.stButton > button:disabled { background: #1e1e2e !important; color: #444466 !important; }

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] { border-radius: 12px !important; overflow: hidden !important; }
[data-testid="stDataFrame"] * { background: #0f0f1a !important; color: #e8e8f0 !important; }
[data-testid="stDataFrame"] th { background: #1a1a2e !important; color: #aaaacc !important; font-weight: 600 !important; }
[data-testid="stDataFrame"] tr:hover td { background: #1a1a2e !important; }

/* ── ALERTS ── */
[data-testid="stAlert"] { background: #1a1a2e !important; border-radius: 10px !important; color: #e8e8f0 !important; border: 1px solid #2a2a4a !important; }

/* ── EXPANDER ── */
[data-testid="stExpander"] { background: #0f0f1a !important; border: 1px solid #1e1e2e !important; border-radius: 12px !important; }
[data-testid="stExpander"] summary { color: #e8e8f0 !important; }
[data-testid="stExpander"] p { color: #aaaacc !important; }

/* ── MARKDOWN ── */
[data-testid="stMarkdownContainer"] p { color: #ccccdd !important; }
.stCaption { color: #666688 !important; }

/* ── DIVIDER ── */
hr { border-color: #1e1e2e !important; }

/* ══════════════════════════════════
   CUSTOM COMPONENTS
══════════════════════════════════ */

/* Header Logo */
.vs-header {
    display: flex; align-items: center; gap: 12px;
    padding: 4px 0 16px; border-bottom: 1px solid #1e1e2e; margin-bottom: 16px;
}
.vs-logo {
    font-size: 22px; font-weight: 900; letter-spacing: -0.5px;
    background: linear-gradient(135deg, #6c63ff, #ff6b6b);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.vs-tagline { font-size: 11px; color: #555577; font-weight: 500; }

/* Stat Cards */
.stat-card {
    background: linear-gradient(135deg, #0f0f1a 0%, #12121f 100%);
    border: 1px solid #1e1e2e;
    border-radius: 16px; padding: 20px 24px;
    transition: all 0.3s; position: relative; overflow: hidden;
}
.stat-card:hover { border-color: #3a3a5e; transform: translateY(-2px); box-shadow: 0 8px 32px rgba(0,0,0,0.4); }
.stat-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
}
.stat-card.purple::before { background: linear-gradient(90deg, #6c63ff, #9c93ff); }
.stat-card.red::before    { background: linear-gradient(90deg, #ff4757, #ff6b81); }
.stat-card.green::before  { background: linear-gradient(90deg, #2ed573, #7bed9f); }
.stat-card.gold::before   { background: linear-gradient(90deg, #ffa502, #ffcc02); }
.stat-label { font-size: 11px; font-weight: 600; color: #555577; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
.stat-value { font-size: 28px; font-weight: 900; color: #ffffff; line-height: 1; }
.stat-sub   { font-size: 12px; color: #555577; margin-top: 6px; }
.stat-icon  { position: absolute; right: 20px; top: 20px; font-size: 28px; opacity: 0.15; }

/* Viral Score */
.viral-score-box {
    background: linear-gradient(135deg, #0f0f1a, #12121f);
    border: 1px solid #2a2a4a;
    border-radius: 20px; padding: 32px; text-align: center;
    position: relative; overflow: hidden;
}
.viral-score-box::after {
    content: ''; position: absolute;
    top: -50%; left: -50%; width: 200%; height: 200%;
    background: radial-gradient(circle, rgba(108,99,255,0.05) 0%, transparent 70%);
    pointer-events: none;
}
.vs-score { font-size: 72px; font-weight: 900; line-height: 1;
    background: linear-gradient(135deg, #6c63ff, #ff6b6b);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.vs-score-label { font-size: 13px; font-weight: 700; color: #555577; letter-spacing: 2px; text-transform: uppercase; margin-top: 8px; }
.vs-score-desc  { font-size: 14px; color: #888899; margin-top: 12px; }

/* Video Card */
.video-card {
    background: #0f0f1a; border: 1px solid #1e1e2e;
    border-radius: 16px; padding: 0; overflow: hidden;
    transition: all 0.3s; cursor: pointer;
}
.video-card:hover { border-color: #3a3a5e; transform: translateY(-3px); box-shadow: 0 12px 40px rgba(0,0,0,0.5); }
.vc-thumbnail { width: 100%; aspect-ratio: 16/9; object-fit: cover; }
.vc-body { padding: 14px 16px; }
.vc-title { font-size: 13px; font-weight: 600; color: #e8e8f0; line-height: 1.4; margin-bottom: 8px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.vc-channel { font-size: 11px; color: #555577; margin-bottom: 10px; }
.vc-stats { display: flex; gap: 12px; }
.vc-stat { display: flex; flex-direction: column; }
.vc-stat-val { font-size: 15px; font-weight: 800; color: #ffffff; }
.vc-stat-lbl { font-size: 10px; color: #444466; text-transform: uppercase; letter-spacing: 0.5px; }
.vc-badge {
    display: inline-block;
    padding: 3px 8px; border-radius: 6px;
    font-size: 11px; font-weight: 700;
    margin-bottom: 8px;
}
.vc-badge.fire { background: rgba(255,71,87,0.15); color: #ff4757; border: 1px solid rgba(255,71,87,0.3); }
.vc-badge.hot  { background: rgba(255,165,2,0.15);  color: #ffa502; border: 1px solid rgba(255,165,2,0.3); }
.vc-badge.ok   { background: rgba(46,213,115,0.15); color: #2ed573; border: 1px solid rgba(46,213,115,0.3); }

/* Trend Badge */
.trend-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(108,99,255,0.1); border: 1px solid rgba(108,99,255,0.3);
    border-radius: 20px; padding: 4px 12px;
    font-size: 12px; font-weight: 600; color: #9c93ff;
}

/* Subscription Box */
.sub-box {
    background: linear-gradient(135deg, #0f0f1a, #12121f);
    border: 1px solid #2a2a4a; border-radius: 20px;
    padding: 48px 40px; text-align: center; margin: 20px 0;
    position: relative; overflow: hidden;
}
.sub-box::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 3px; background: linear-gradient(90deg, #6c63ff, #ff6b6b, #ffa502);
}
.act-box {
    background: #0f0f1a; border: 1px solid #2a2a4a;
    border-radius: 16px; padding: 28px; text-align: center; margin: 16px 0;
}
.tg-pay-btn {
    display: inline-flex; align-items: center; gap: 10px;
    background: linear-gradient(135deg, #229ED9, #1a8fc2);
    color: #fff !important; padding: 16px 40px; border-radius: 12px;
    font-weight: 800; font-size: 16px; text-decoration: none !important;
    transition: 0.3s; margin: 12px 0;
}
.tg-pay-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(34,158,217,0.4); }

/* Badges */
.badge-trial   { background: rgba(255,165,2,0.1);  border: 1px solid rgba(255,165,2,0.3);  border-radius: 10px; padding: 10px 14px; color: #ffa502; font-weight: 700; font-size: 13px; }
.badge-active  { background: rgba(46,213,115,0.1); border: 1px solid rgba(46,213,115,0.3); border-radius: 10px; padding: 10px 14px; color: #2ed573; font-weight: 700; font-size: 13px; }
.badge-expired { background: rgba(255,71,87,0.1);  border: 1px solid rgba(255,71,87,0.3);  border-radius: 10px; padding: 10px 14px; color: #ff4757; font-weight: 700; font-size: 13px; }

/* Section titles */
.section-title {
    font-size: 18px; font-weight: 800; color: #ffffff;
    margin: 24px 0 16px; display: flex; align-items: center; gap: 10px;
}
.section-title span { font-size: 14px; font-weight: 500; color: #555577; }

/* Niche pills */
.niche-grid { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }
.niche-pill {
    background: #1a1a2e; border: 1px solid #2a2a4a;
    border-radius: 20px; padding: 6px 14px;
    font-size: 13px; color: #aaaacc; cursor: pointer;
    transition: all 0.2s; font-weight: 500;
}
.niche-pill:hover { background: #2a2a4a; color: #fff; border-color: #6c63ff; }
.niche-pill.active { background: rgba(108,99,255,0.2); border-color: #6c63ff; color: #9c93ff; }

/* Autocomplete hint */
.search-hint {
    background: #1a1a2e; border: 1px solid #2a2a4a;
    border-radius: 8px; padding: 8px 14px; margin-top: 4px;
    font-size: 12px; color: #666688;
}

/* ── LIGHT MODE ── */
.light-mode html, .light-mode body,
body.light .stApp, body.light .main, body.light .block-container {
    background-color: #f5f5f5 !important;
    color: #1a1a2e !important;
}

/* Theme toggle button */
.theme-toggle {
    position: fixed; top: 12px; right: 16px; z-index: 9999;
    background: #1a1a2e; border: 1px solid #2a2a4a;
    border-radius: 20px; padding: 6px 14px;
    font-size: 13px; cursor: pointer; color: #fff;
    transition: all 0.3s;
}
.theme-toggle:hover { background: #2a2a4a; }

/* Light mode overrides */
.light-bg html, .light-bg body,
.light-bg .stApp, .light-bg .main, .light-bg .block-container {
    background-color: #f0f2f8 !important;
    color: #1a1a2e !important;
}
.light-bg [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #e8eaf6, #dde1f5) !important;
    border-right: 1px solid #c5cae9 !important;
}
.light-bg [data-testid="stSidebar"] * { color: #1a1a2e !important; }
.light-bg .stat-card {
    background: #ffffff !important;
    border-color: #c5cae9 !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08) !important;
}
.light-bg .stat-label { color: #7986cb !important; }
.light-bg .stat-value { color: #1a1a2e !important; }
.light-bg .video-card { background: #ffffff !important; border-color: #c5cae9 !important; }
.light-bg .vc-title   { color: #1a1a2e !important; }
.light-bg .vc-channel { color: #7986cb !important; }
.light-bg .vc-stat-val { color: #1a1a2e !important; }
.light-bg .vc-stat-lbl { color: #9fa8da !important; }
.light-bg .section-title { color: #1a1a2e !important; }
.light-bg [data-baseweb="tab-list"] { background: #e8eaf6 !important; border-bottom: 1px solid #c5cae9 !important; }
.light-bg [data-baseweb="tab"] { color: #7986cb !important; }
.light-bg [aria-selected="true"][data-baseweb="tab"] { color: #3f51b5 !important; border-bottom-color: #3f51b5 !important; }
.light-bg input, .light-bg textarea { background: #ffffff !important; color: #1a1a2e !important; border-color: #c5cae9 !important; }
.light-bg [data-baseweb="select"] > div { background: #ffffff !important; color: #1a1a2e !important; border-color: #c5cae9 !important; }
.light-bg [data-baseweb="select"] span, .light-bg [data-baseweb="select"] div { color: #1a1a2e !important; }
.light-bg [data-baseweb="option"] { background: #ffffff !important; color: #1a1a2e !important; }
.light-bg [data-baseweb="option"]:hover { background: #e8eaf6 !important; }
.light-bg [data-baseweb="popover"], .light-bg [data-baseweb="popover"] * { background: #ffffff !important; color: #1a1a2e !important; }
.light-bg .niche-pill { background: #e8eaf6 !important; border-color: #c5cae9 !important; color: #3f51b5 !important; }
.light-bg .search-hint { background: #e8eaf6 !important; border-color: #c5cae9 !important; color: #7986cb !important; }
.light-bg .vs-logo { background: linear-gradient(135deg, #3f51b5, #e91e63); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.light-bg .vs-tagline { color: #9fa8da !important; }
.light-bg .viral-score-box { background: #ffffff !important; border-color: #c5cae9 !important; }
.light-bg [data-testid="stMarkdownContainer"] p { color: #3a3a5e !important; }
.light-bg hr { border-color: #c5cae9 !important; }
.light-bg [data-testid="stAlert"] { background: #e8eaf6 !important; color: #1a1a2e !important; }
.light-bg [data-testid="stDataFrame"] * { background: #ffffff !important; color: #1a1a2e !important; }
.light-bg [data-testid="stDataFrame"] th { background: #e8eaf6 !important; color: #3f51b5 !important; }
.light-bg .stButton > button {
    background: linear-gradient(135deg, #3f51b5, #5c6bc0) !important;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE) as f: return json.load(f)
        except: pass
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_user(uid):
    db = load_db()
    if uid not in db:
        db[uid] = {"trial_used":0,"subscribed":False,"sub_until":None,"orders":[]}
        save_db(db)
    return db[uid]

def save_user(uid, data):
    db = load_db(); db[uid] = data; save_db(db)

def is_subscribed(uid):
    u = get_user(uid)
    if not u.get("subscribed"): return False
    if u.get("sub_until"):
        if datetime.now() > datetime.fromisoformat(u["sub_until"]):
            u["subscribed"]=False; u["sub_until"]=None; save_user(uid,u); return False
    return True

def get_trial(uid):
    return max(0, FREE_TRIAL_LIMIT - get_user(uid).get("trial_used",0))

def use_trial(uid):
    u = get_user(uid); u["trial_used"] = u.get("trial_used",0)+1; save_user(uid,u)

def activate_sub(uid, order_id):
    u = get_user(uid)
    u["subscribed"] = True
    u["sub_until"]  = (datetime.now()+timedelta(days=SUBSCRIPTION_DAYS)).isoformat()
    u.setdefault("orders",[]).append({"id":order_id,"date":datetime.now().isoformat()})
    save_user(uid,u)

def gen_code():
    db = load_db(); codes = db.get("activation_codes",{})
    for _ in range(200):
        c = ''.join(random.choices(string.ascii_uppercase+string.digits, k=6))
        if c not in codes: return c
    return uuid.uuid4().hex[:6].upper()

def save_code(code, tg_id, order_id, note="", days=30):
    db = load_db()
    db.setdefault("activation_codes",{})[code] = {
        "telegram_id":str(tg_id), "order_id":order_id, "note":note,
        "created":datetime.now().isoformat(),
        "expires":(datetime.now()+timedelta(days=days)).isoformat(), "used":False
    }
    save_db(db)

def activate_by_code(code, uid):
    db = load_db(); codes = db.get("activation_codes",{})
    code = code.strip().upper()
    if code not in codes: return False,"❌ Код топилмади."
    c = codes[code]
    if c.get("used"):    return False,"❌ Бу код аллақачон ишлатилган."
    if datetime.now() > datetime.fromisoformat(c["expires"]): return False,"❌ Код муддати тугаган."
    activate_sub(uid, code)
    codes[code].update({"used":True,"used_by":uid,"used_at":datetime.now().isoformat()})
    db["activation_codes"] = codes; save_db(db)
    return True,"✅ Обуна муваффақиятли фаоллашди!"

# ══════════════════════════════════════════
# PAYMENT URLS
# ══════════════════════════════════════════
def payme_url(oid):
    p = f"m={PAYME_MERCHANT};ac.order_id={oid};a={SUBSCRIPTION_PRICE*100}"
    return f"https://checkout.paycom.uz/{base64.b64encode(p.encode()).decode()}"

def click_url(oid):
    return (f"https://my.click.uz/services/pay?service_id={CLICK_SERVICE}"
            f"&merchant_id={CLICK_MERCHANT}&amount={SUBSCRIPTION_PRICE}&transaction_param={oid}")

# ══════════════════════════════════════════
# TELEGRAM BOT — background thread
# ══════════════════════════════════════════
def start_bot():
    if not BOT_AVAILABLE or not BOT_TOKEN: return
    bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

    @bot.message_handler(commands=['start'])
    def h_start(msg):
        oid = f"V777_{uuid.uuid4().hex[:10].upper()}"
        mk = telebot.types.InlineKeyboardMarkup(row_width=1)
        mk.add(
            telebot.types.InlineKeyboardButton("💳 Payme орқали тўлаш",  url=payme_url(oid)),
            telebot.types.InlineKeyboardButton("⚡ Click орқали тўлаш",   url=click_url(oid)),
            telebot.types.InlineKeyboardButton("✅ Тўлов қилдим — код олиш",
                                               callback_data=f"paid:{oid}"),
        )
        bot.send_message(msg.chat.id,
            f"👋 *Viral 777 Analytics*га хуш келибсиз!\n\n"
            f"🔥 YouTube вирал таҳлил платформаси\n\n"
            f"💰 *Ойлик обуна:* `{SUBSCRIPTION_PRICE:,} сўм`\n"
            f"📅 30 кун · ♾️ Чексиз қидирув · 📊 Тренд таҳлили\n\n"
            f"Тўловни амалга ошириб, *\"Тўлов қилдим\"* тугмасини босинг:",
            parse_mode="Markdown", reply_markup=mk)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("paid:"))
    def h_paid(call):
        oid = call.data.split(":",1)[1]
        tg_id = call.from_user.id
        bot.answer_callback_query(call.id, "⏳ Текширилмоқда...")
        code = gen_code()
        save_code(code, tg_id, oid)
        bot.send_message(tg_id,
            f"✅ *Тўлов қабул қилинди!*\n\n"
            f"🔑 Активация кодингиз:\n\n"
            f"```\n{code}\n```\n\n"
            f"📌 Сайтга қайтинг ва ушбу кодни киритинг.\n"
            f"⏰ Код *24 соат* амал қилади.",
            parse_mode="Markdown")
        if ADMIN_CHAT_ID:
            try:
                bot.send_message(int(ADMIN_CHAT_ID),
                    f"💰 *Янги тўлов!*\n👤 {call.from_user.first_name} (`{tg_id}`)\n"
                    f"📋 `{oid}`\n🔑 `{code}`\n💵 {SUBSCRIPTION_PRICE:,} сўм\n"
                    f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                    parse_mode="Markdown")
            except: pass

    @bot.message_handler(commands=['admin'])
    def h_admin(msg):
        if str(msg.chat.id)!=str(ADMIN_CHAT_ID): return
        db=load_db(); u={k:v for k,v in db.items() if k!="activation_codes"}
        c=db.get("activation_codes",{})
        bot.send_message(msg.chat.id,
            f"📊 *Статистика*\n\n"
            f"👥 Фойдаланувчи: `{len(u)}`\n"
            f"✅ Фаол обуна: `{sum(1 for x in u.values() if x.get('subscribed'))}`\n"
            f"🔑 Ишлатилган: `{sum(1 for x in c.values() if x.get('used'))}`\n"
            f"⏳ Кутилаётган: `{sum(1 for x in c.values() if not x.get('used'))}`",
            parse_mode="Markdown")

    @bot.message_handler(commands=['kod'])
    def h_kod(msg):
        if str(msg.chat.id)!=str(ADMIN_CHAT_ID): return
        parts=msg.text.split()
        if len(parts)<2: bot.send_message(msg.chat.id,"Format: /kod TELEGRAM\\_ID",parse_mode="Markdown"); return
        code=gen_code(); save_code(code, parts[1], f"MANUAL_{uuid.uuid4().hex[:6]}", note="manual")
        try:
            bot.send_message(int(parts[1]),
                f"✅ *Активация кодингиз:*\n\n```\n{code}\n```\n\nСайтга киринг ва кодни киритинг.",
                parse_mode="Markdown")
            bot.send_message(msg.chat.id, f"✅ Юборildi: `{code}`", parse_mode="Markdown")
        except Exception as e:
            bot.send_message(msg.chat.id, f"❌ {e}")

    def poll():
        while True:
            try: bot.infinity_polling(timeout=20, long_polling_timeout=15)
            except: time.sleep(5)

    threading.Thread(target=poll, daemon=True).start()

if "bot_started" not in st.session_state:
    st.session_state.bot_started = True
    threading.Thread(target=start_bot, daemon=True).start()

# ══════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════
def fmt(n):
    if n>=1_000_000_000: return f"{round(n/1_000_000_000,1)}B"
    if n>=1_000_000:     return f"{round(n/1_000_000,1)}M"
    if n>=1_000:         return f"{round(n/1_000,1)}K"
    return str(n)

def uzb_date(iso):
    M={1:"Янв",2:"Фев",3:"Мар",4:"Апр",5:"Май",6:"Июн",
       7:"Июл",8:"Авг",9:"Сен",10:"Окт",11:"Ноя",12:"Дек"}
    try:
        dt=datetime.strptime(re.sub(r'\.\d+Z','Z',iso),'%Y-%m-%dT%H:%M:%SZ')
        now=datetime.utcnow(); diff=now-dt
        if diff.days==0:    return "Бугун"
        if diff.days==1:    return "Кеча"
        if diff.days<7:     return f"{diff.days} кун олdin"
        if diff.days<30:    return f"{diff.days//7} ҳафта олdin"
        if diff.days<365:   return f"{diff.days//30} ой олdin"
        return f"{dt.day} {M[dt.month]} {dt.year}"
    except: return iso[:10]

def get_uid():
    if "uid" in st.session_state and st.session_state.uid:
        return st.session_state.uid
    p = st.query_params.get("uid","")
    if p and len(p)>=10:
        st.session_state.uid=p; return p
    new = "u_"+uuid.uuid4().hex
    st.session_state.uid=new; st.query_params["uid"]=new; return new

def viral_badge(score):
    if score>=100: return '<span class="vc-badge fire">🔥 Мега Вирал</span>'
    if score>=50:  return '<span class="vc-badge fire">🚀 Вирал</span>'
    if score>=20:  return '<span class="vc-badge hot">⚡ Трендда</span>'
    return '<span class="vc-badge ok">✅ Яхши</span>'

# Niche suggestions
NICHES = [
    "Survival","Cooking","Finance","Gaming","Science","Travel",
    "Fitness","Tech","Psychology","History","Cars","Football",
    "DIY","Comedy","Documentary","Music","Fashion","Business",
]

REGIONS = {"🇺🇸 US":"US","🇬🇧 GB":"GB","🇺🇿 UZ":"UZ",
           "🇷🇺 RU":"RU","🇹🇷 TR":"TR","🇩🇪 DE":"DE","🇯🇵 JP":"JP"}

# ══════════════════════════════════════════
# SESSION
# ══════════════════════════════════════════
for k,v in [("authenticated",False),("results",None),
             ("history",[]),("last_topic",""),("search_done",False),
             ("dark_mode",True),("current_topic","Survival")]:
    if k not in st.session_state: st.session_state[k]=v

uid = get_uid()

# ══════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════
with st.sidebar:
    # Theme toggle
    apply_theme()
    dark_icon = "🌙 Dark" if st.session_state.dark_mode else "☀️ Light"
    if st.button(dark_icon, key="theme_btn", use_container_width=False):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    # Logo
    st.markdown("""
    <div class="vs-header">
        <div>
            <div class="vs-logo">🔥 Viral 777</div>
            <div class="vs-tagline">YouTube Analytics Platform</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Auth
    if not st.session_state.authenticated:
        with st.expander("🔐 Admin Кириш"):
            u_in = st.text_input("Логин", key="login_u")
            p_in = st.text_input("Пароль", type="password", key="login_p")
            if st.button("Кириш", key="login_btn"):
                if ADMIN_DB.get(u_in)==p_in:
                    st.session_state.authenticated=True; st.rerun()
                else: st.error("❌ Нотўғри!")
    else:
        col1,col2 = st.columns([2,1])
        col1.success("✅ Admin")
        if col2.button("Чиқиш"): st.session_state.authenticated=False; st.rerun()

    st.divider()

    # Subscription status
    if not st.session_state.authenticated:
        if is_subscribed(uid):
            ud=get_user(uid)
            until=datetime.fromisoformat(ud["sub_until"]).strftime("%d.%m.%Y")
            st.markdown(f"<div class='badge-active'>✅ PRO · {until} гача</div>",
                        unsafe_allow_html=True)
        else:
            rem=get_trial(uid)
            if rem>0:
                st.markdown(f"<div class='badge-trial'>🎁 Синов: {rem}/{FREE_TRIAL_LIMIT}</div>",
                            unsafe_allow_html=True)
            else:
                st.markdown("<div class='badge-expired'>🔒 Обуна керак</div>",
                            unsafe_allow_html=True)

    st.divider()

    # API Key
    saved_key = st.query_params.get("apikey","")
    api_key   = st.text_input("🔑 YouTube API Key", value=saved_key,
                               type="password", placeholder="AIza...")
    if api_key and api_key!=saved_key:
        st.query_params["apikey"]=api_key

    st.markdown("**🔍 Мавзу / Ниша**")

    # Niche quick select — session_state orqali to'g'ri ishlaydi
    niche_cols = st.columns(3)
    for i, niche in enumerate(NICHES[:9]):
        if niche_cols[i%3].button(niche, key=f"n_{niche}", use_container_width=True):
            st.session_state["current_topic"] = niche
            st.rerun()

    # topic — session_state dan olish
    if "current_topic" not in st.session_state:
        st.session_state["current_topic"] = "Survival"

    topic = st.text_input(
        "Ёки қидирув матнини киритинг:",
        value=st.session_state["current_topic"],
        placeholder="Масалан: Survival, Finance...",
        key="topic_input"
    )
    # Foydalanuvchi o'zi yozsa ham session_state yangilansin
    if topic != st.session_state["current_topic"]:
        st.session_state["current_topic"] = topic

    # Search suggestions — faqat ko'rsatadi, bosilganda topic o'zgaradi
    if topic and len(topic)>=2:
        hints = [n for n in NICHES if topic.lower() in n.lower() and n.lower()!=topic.lower()][:4]
        if hints:
            hint_cols = st.columns(len(hints))
            for hi, hn in enumerate(hints):
                if hint_cols[hi].button(f"🔍 {hn}", key=f"hint_{hn}", use_container_width=True):
                    st.session_state["current_topic"] = hn
                    st.rerun()

    region_label = st.selectbox("🌍 Бозор:", list(REGIONS.keys()))
    region_code  = REGIONS[region_label]

    days_sel  = st.select_slider("📅 Давр:", options=[1,7,14,30,60,90,180,365],
                                  value=30, format_func=lambda x: f"{x} кун")
    min_outl  = st.slider("⚡ Min Outlier Score:", 1, 200, 10,
                           help="Вираллик коэффициенти — видео кўришлари / обуначилар")
    min_views = st.select_slider("👁 Min Кўришлар:",
                                  options=[0,1000,10000,50000,100000,500000,1000000],
                                  value=0, format_func=lambda x: fmt(x) if x>0 else "Ҳаммаси")
    max_res   = st.select_slider("📦 Натижалар сони:", options=[10,25,50], value=25)

    can_search = (st.session_state.authenticated or
                  is_subscribed(uid) or get_trial(uid)>0)
    search_btn = st.button("🚀 ТАҲЛИЛНИ БОШЛАШ", disabled=not can_search,
                            use_container_width=True)

    if not can_search:
        st.markdown("<div style='text-align:center;margin-top:8px;font-size:12px;color:#555577;'>"
                    "Обуна сотиб олинг ↓</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════
# MAIN TABS
# ══════════════════════════════════════════
TAB_TREND, TAB_CARDS, TAB_TABLE, TAB_CHART, TAB_HISTORY = st.tabs([
    "🔥 Тренд Таҳлили",
    "🎬 Видео Карточкалар",
    "📊 Жадвал",
    "📈 Графиклар",
    "🕐 Тарих",
])

# ══════════════════════════════════════════
# SUBSCRIPTION BLOCK (shown in all tabs when needed)
# ══════════════════════════════════════════
def show_sub_block(tab_id="main"):
    oid = st.session_state.get("pending_order") or gen_code()
    st.session_state.pending_order = oid
    st.markdown(f"""
    <div class='sub-box'>
        <div style='font-size:48px;margin-bottom:12px;'>🔒</div>
        <h2 style='color:#fff;font-size:24px;margin-bottom:8px;'>Синов муддати тугади</h2>
        <p style='color:#888899;font-size:14px;margin-bottom:24px;'>
            Давом этиш учун <b>Pro обуна</b> сотиб олинг.<br>
            Тўловдан сўнг Telegram бот активация кодини <b>дарҳол</b> юборади.
        </p>
        <div style='font-size:52px;font-weight:900;background:linear-gradient(135deg,#6c63ff,#ff6b6b);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:16px 0;'>
            {SUBSCRIPTION_PRICE:,} сўм
        </div>
        <p style='color:#444466;font-size:13px;margin-bottom:28px;'>
            📅 30 кун &nbsp;·&nbsp; ♾️ Чексиз қидирув &nbsp;·&nbsp; 📊 Тренд таҳлили &nbsp;·&nbsp; 📈 Графиклар
        </p>
        <a href='{TELEGRAM_BOT_LINK}' target='_blank' class='tg-pay-btn'>
            ✈️ Telegram орқали тўлаш ва код олиш
        </a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='act-box'>
        <div style='font-size:28px;margin-bottom:8px;'>🔑</div>
        <h4 style='color:#fff;margin-bottom:4px;'>Активация кодини киритинг</h4>
        <p style='color:#555577;font-size:13px;'>Telegram ботдан олган 6 та белгили код</p>
    </div>
    """, unsafe_allow_html=True)

    c1,c2,c3 = st.columns([1,2,1])
    with c2:
        code = st.text_input("", placeholder="4X9K2M",
                              max_chars=6, key=f"code_inp_{tab_id}",
                              label_visibility="collapsed").strip().upper()
        if st.button("🔓 КОДНИ ТАСДИҚЛАШ", key=f"code_btn_{tab_id}", use_container_width=True):
            if len(code)<6: st.error("❌ Код 6 та белгидан иборат!")
            else:
                ok,msg = activate_by_code(code, uid)
                if ok: st.success(msg); st.balloons(); time.sleep(1); st.rerun()
                else:  st.error(msg)

# ══════════════════════════════════════════
# SEARCH LOGIC
# ══════════════════════════════════════════
if search_btn:
    topic = st.session_state.get("current_topic", "Survival")
    current_key = st.query_params.get("apikey","") or api_key
    if not current_key:
        st.error("‼️ YouTube API Key киритилмаган!")
    else:
        with st.spinner("🔍 YouTube маълумотлари таҳлил қилинмоқда..."):
            try:
                yt = googleapiclient.discovery.build("youtube","v3",developerKey=current_key)
                pub_after = (datetime.utcnow()-timedelta(days=days_sel)).isoformat()+"Z"

                res = yt.search().list(
                    q=topic, part="snippet", type="video",
                    maxResults=max_res, order="viewCount",
                    publishedAfter=pub_after, regionCode=region_code
                ).execute()

                results = []
                vid_ids = [item['id']['videoId'] for item in res.get('items',[])]
                ch_ids  = [item['snippet']['channelId'] for item in res.get('items',[])]

                # Batch video stats
                vi_batch = yt.videos().list(
                    part="statistics,snippet", id=",".join(vid_ids)
                ).execute()
                vi_map = {i['id']:i for i in vi_batch.get('items',[])}

                # Batch channel stats (deduplicated)
                unique_chs = list(set(ch_ids))
                ci_batch = yt.channels().list(
                    part="statistics,snippet", id=",".join(unique_chs)
                ).execute()
                ci_map = {i['id']:i for i in ci_batch.get('items',[])}

                for item in res.get('items',[]):
                    vid = item['id']['videoId']
                    cid = item['snippet']['channelId']
                    vi  = vi_map.get(vid, {})
                    ci  = ci_map.get(cid, {})
                    if not vi or not ci: continue

                    views = int(vi.get('statistics',{}).get('viewCount',0))
                    subs  = int(ci.get('statistics',{}).get('subscriberCount',1))
                    likes = int(vi.get('statistics',{}).get('likeCount',0))
                    comments = int(vi.get('statistics',{}).get('commentCount',0))
                    outl  = round(views/(subs if subs>500 else 500),1)

                    # Thumbnail — high quality
                    thumbs = vi.get('snippet',{}).get('thumbnails',{})
                    thumb  = (thumbs.get('maxres') or thumbs.get('high') or
                              thumbs.get('medium') or thumbs.get('default',{})).get('url','')

                    if outl>=min_outl and views>=min_views:
                        results.append({
                            "id":        vid,
                            "thumbnail": thumb,
                            "title":     vi.get('snippet',{}).get('title',''),
                            "channel":   item['snippet']['channelTitle'],
                            "channel_id":cid,
                            "views":     views,
                            "subs":      subs,
                            "likes":     likes,
                            "comments":  comments,
                            "outlier":   outl,
                            "published": vi.get('snippet',{}).get('publishedAt',''),
                            "url":       f"https://www.youtube.com/watch?v={vid}",
                            "ch_url":    f"https://www.youtube.com/channel/{cid}",
                        })

                results.sort(key=lambda x: x['outlier'], reverse=True)
                st.session_state.results = results
                st.session_state.last_topic = topic
                st.session_state.search_done = True

                # Тарих — UTC ни UZ вақтга ўтказиш (+5)
                now_uz = datetime.utcnow() + timedelta(hours=5)
                st.session_state.history.append({
                    "Вақт":    now_uz.strftime("%H:%M"),
                    "Сана":    now_uz.strftime("%d.%m"),
                    "Мавзу":   topic,
                    "Бозор":   region_label,
                    "Давр":    f"{days_sel} кун",
                    "Топилди": len(results),
                })

                if not st.session_state.authenticated and not is_subscribed(uid):
                    use_trial(uid)
                    rem = get_trial(uid)
                    if rem>0: st.toast(f"🎁 Яна {rem} та текин қидирув қолди")
                    else:     st.toast("⚠️ Охирги синов ишлатилди!")

            except Exception as e:
                st.error(f"⚠️ Хато: {e}")

# ══════════════════════════════════════════
# TAB 1: TREND ANALYSIS
# ══════════════════════════════════════════
with TAB_TREND:
    need_sub = (not st.session_state.authenticated and
                not is_subscribed(uid) and get_trial(uid)==0)

    if need_sub:
        show_sub_block()
    elif not st.session_state.results:
        # Welcome screen
        st.markdown("""
        <div style='text-align:center;padding:60px 20px;'>
            <div style='font-size:64px;margin-bottom:16px;'>🔥</div>
            <h2 style='color:#fff;font-size:28px;margin-bottom:12px;'>
                YouTube Тренд Таҳлилчиси
            </h2>
            <p style='color:#555577;font-size:16px;max-width:500px;margin:0 auto 32px;'>
                Чap панелдан мавзу ва параметрларни танланг,<br>
                сўнг <b>"Таҳлилни бошлаш"</b> тугмасини босинг.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Quick niches
        st.markdown("<div class='section-title'>⚡ Тез Қидирув — Машҳур Нишалар</div>",
                    unsafe_allow_html=True)
        nc = st.columns(6)
        niche_emojis = {"Survival":"🏕️","Cooking":"🍳","Finance":"💰","Gaming":"🎮",
                        "Science":"🔬","Travel":"✈️","Fitness":"💪","Tech":"💻",
                        "Psychology":"🧠","History":"📜","Cars":"🚗","Football":"⚽"}
        for i,n in enumerate(NICHES[:12]):
            if nc[i%6].button(f"{niche_emojis.get(n,'🔥')} {n}", key=f"qn_{n}",
                               use_container_width=True):
                st.session_state.last_topic = n
                st.rerun()
    else:
        df = pd.DataFrame(st.session_state.results)
        if df.empty: st.info("Натижа топилмади. Параметрларни ўзгартиринг."); st.stop()

        avg_outl = round(df['outlier'].mean(),1)
        total_views = df['views'].sum()
        max_outl    = df['outlier'].max()
        top_channel = df.iloc[0]['channel']

        # ── Top KPI ──
        st.markdown(f"<div class='section-title'>📊 <b>{topic}</b> Нишаси — Умумий Таҳлил "
                    f"<span>({len(df)} та вирал видео топилди)</span></div>",
                    unsafe_allow_html=True)

        k1,k2,k3,k4 = st.columns(4)
        k1.markdown(f"""<div class='stat-card purple'>
            <div class='stat-icon'>⚡</div>
            <div class='stat-label'>O'rtacha Viral Score</div>
            <div class='stat-value'>{avg_outl}x</div>
            <div class='stat-sub'>Обуначиларга нисбатан</div>
        </div>""", unsafe_allow_html=True)

        k2.markdown(f"""<div class='stat-card red'>
            <div class='stat-icon'>👁</div>
            <div class='stat-label'>Жами Кўришлар</div>
            <div class='stat-value'>{fmt(total_views)}</div>
            <div class='stat-sub'>{days_sel} кундаги натижа</div>
        </div>""", unsafe_allow_html=True)

        k3.markdown(f"""<div class='stat-card gold'>
            <div class='stat-icon'>🔥</div>
            <div class='stat-label'>Eng Yuqori Score</div>
            <div class='stat-value'>{max_outl}x</div>
            <div class='stat-sub'>Мега вирал</div>
        </div>""", unsafe_allow_html=True)

        k4.markdown(f"""<div class='stat-card green'>
            <div class='stat-icon'>📺</div>
            <div class='stat-label'>Top Канал</div>
            <div class='stat-value' style='font-size:16px;'>{top_channel[:16]}...</div>
            <div class='stat-sub'>Энг вирал канал</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Viral Score Gauge ──
        col_gauge, col_bar = st.columns([1,2])

        with col_gauge:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=avg_outl,
                title={'text': "Ниша Куч Коэффициенти", 'font':{'color':'#aaaacc','size':13}},
                number={'font':{'color':'#ffffff','size':40},'suffix':'x'},
                gauge={
                    'axis':{'range':[0, max(200, avg_outl*1.5)],
                            'tickcolor':'#333355','tickfont':{'color':'#666688'}},
                    'bar':{'color':'#6c63ff','thickness':0.3},
                    'bgcolor':'#0f0f1a',
                    'bordercolor':'#1e1e2e',
                    'steps':[
                        {'range':[0,10],   'color':'#1a1a2e'},
                        {'range':[10,50],  'color':'#1e1e38'},
                        {'range':[50,100], 'color':'#242448'},
                        {'range':[100,max(200,avg_outl*1.5)], 'color':'#2a2a58'},
                    ],
                    'threshold':{'line':{'color':'#ff4757','width':3},'value':50}
                }
            ))
            fig_gauge.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                height=260, margin=dict(l=20,r=20,t=40,b=10),
                font=dict(family='Inter')
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        with col_bar:
            # Top 10 by outlier
            top10 = df.nlargest(10,'outlier')[['title','outlier','channel']]
            top10['short_title'] = top10['title'].str[:35]+"..."
            fig_bar = px.bar(
                top10, x='outlier', y='short_title', orientation='h',
                color='outlier',
                color_continuous_scale=['#2a2a58','#6c63ff','#ff4757'],
                labels={'outlier':'Viral Score','short_title':''},
            )
            fig_bar.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                height=260, margin=dict(l=0,r=20,t=20,b=10),
                font=dict(color='#aaaacc', family='Inter', size=11),
                xaxis=dict(gridcolor='#1e1e2e', color='#666688'),
                yaxis=dict(gridcolor='#1e1e2e', color='#ccccdd'),
                coloraxis_showscale=False,
            )
            fig_bar.update_traces(marker_line_width=0)
            st.plotly_chart(fig_bar, use_container_width=True)

        # ── Top 3 Highlight ──
        st.markdown("<div class='section-title'>🏆 Энг Вирал Видеолар</div>",
                    unsafe_allow_html=True)
        top3 = df.head(3)
        cols = st.columns(3)
        for i,(_, row) in enumerate(top3.iterrows()):
            with cols[i]:
                badge_html = viral_badge(row['outlier'])
                st.markdown(f"""
                <div class='video-card'>
                    <img class='vc-thumbnail' src='{row['thumbnail']}' 
                         onerror="this.src='https://via.placeholder.com/320x180/1a1a2e/6c63ff?text=No+Image'">
                    <div class='vc-body'>
                        {badge_html}
                        <div class='vc-title'>{row['title']}</div>
                        <div class='vc-channel'>📺 {row['channel']} · {uzb_date(row['published'])}</div>
                        <div class='vc-stats'>
                            <div class='vc-stat'>
                                <span class='vc-stat-val'>{row['outlier']}x</span>
                                <span class='vc-stat-lbl'>Score</span>
                            </div>
                            <div class='vc-stat'>
                                <span class='vc-stat-val'>{fmt(row['views'])}</span>
                                <span class='vc-stat-lbl'>Кўришлар</span>
                            </div>
                            <div class='vc-stat'>
                                <span class='vc-stat-val'>{fmt(row['subs'])}</span>
                                <span class='vc-stat-lbl'>Обуначи</span>
                            </div>
                        </div>
                    </div>
                </div>
                <a href='{row['url']}' target='_blank' style='display:block;text-align:center;
                   margin-top:8px;font-size:12px;color:#6c63ff;text-decoration:none;'>
                   ▶ YouTube да кўриш</a>
                """, unsafe_allow_html=True)

        # ── Channels analysis ──
        st.markdown("<div class='section-title'>📺 Энг Фаол Каналлар</div>",
                    unsafe_allow_html=True)
        ch_stats = df.groupby('channel').agg(
            Видеолар=('id','count'),
            Ўртача_Score=('outlier','mean'),
            Жами_Кўришлар=('views','sum')
        ).round(1).sort_values('Ўртача_Score',ascending=False).head(10)
        ch_stats['Жами_Кўришлар'] = ch_stats['Жами_Кўришлар'].apply(fmt)

        fig_ch = px.scatter(
            ch_stats.reset_index(),
            x='Видеолар', y='Ўртача_Score',
            size='Видеолар', color='Ўртача_Score',
            hover_name='channel',
            color_continuous_scale=['#2a2a58','#6c63ff','#ff4757'],
            labels={'Ўртача_Score':'Ўртача Viral Score','Видеолар':'Видеолар сони'},
            size_max=40,
        )
        fig_ch.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=300, margin=dict(l=0,r=0,t=10,b=0),
            font=dict(color='#aaaacc',family='Inter'),
            xaxis=dict(gridcolor='#1e1e2e',color='#666688'),
            yaxis=dict(gridcolor='#1e1e2e',color='#666688'),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_ch, use_container_width=True)

# ══════════════════════════════════════════
# TAB 2: VIDEO CARDS
# ══════════════════════════════════════════
with TAB_CARDS:
    need_sub2 = (not st.session_state.authenticated and
                 not is_subscribed(uid) and get_trial(uid)==0)
    if need_sub2:
        show_sub_block("cards")
    elif not st.session_state.results:
        st.info("🔍 Аввал чап панелдан қидирув бошланг.")
    else:
        df = pd.DataFrame(st.session_state.results)
        # Filter controls
        fc1,fc2,fc3 = st.columns(3)
        sort_by  = fc1.selectbox("Саралаш:", ["Viral Score","Кўришлар","Лайклар"], key="sort_c")
        min_s    = fc2.slider("Min Score:", 0, int(df['outlier'].max()+1), 0, key="min_s")
        cols_cnt = fc3.select_slider("Устунлар:", [2,3,4], value=3, key="cols_c")

        sort_map = {"Viral Score":"outlier","Кўришлар":"views","Лайклар":"likes"}
        filtered = df[df['outlier']>=min_s].sort_values(sort_map[sort_by],ascending=False)

        st.caption(f"Кўрсатилмоқда: {len(filtered)} та видео")

        rows = [filtered.iloc[i:i+cols_cnt] for i in range(0,len(filtered),cols_cnt)]
        for row_df in rows:
            cols = st.columns(cols_cnt)
            for ci,(_, row) in enumerate(row_df.iterrows()):
                with cols[ci]:
                    badge_html = viral_badge(row['outlier'])
                    engage = round((row['likes']+row['comments'])/max(row['views'],1)*100,2)
                    st.markdown(f"""
                    <div class='video-card'>
                        <img class='vc-thumbnail' src='{row['thumbnail']}'
                             onerror="this.src='https://via.placeholder.com/320x180/1a1a2e/6c63ff?text=📺'">
                        <div class='vc-body'>
                            {badge_html}
                            <div class='vc-title'>{row['title']}</div>
                            <div class='vc-channel'>📺 {row['channel']} · {uzb_date(row['published'])}</div>
                            <div class='vc-stats'>
                                <div class='vc-stat'>
                                    <span class='vc-stat-val'>{row['outlier']}x</span>
                                    <span class='vc-stat-lbl'>Score</span>
                                </div>
                                <div class='vc-stat'>
                                    <span class='vc-stat-val'>{fmt(row['views'])}</span>
                                    <span class='vc-stat-lbl'>Кўришлар</span>
                                </div>
                                <div class='vc-stat'>
                                    <span class='vc-stat-val'>{engage}%</span>
                                    <span class='vc-stat-lbl'>Engage</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <a href='{row['url']}' target='_blank'
                       style='display:block;text-align:center;margin:6px 0 14px;
                              font-size:12px;color:#6c63ff;text-decoration:none;
                              padding:6px;background:#1a1a2e;border-radius:8px;'>
                       ▶ YouTube да кўриш</a>
                    """, unsafe_allow_html=True)

# ══════════════════════════════════════════
# TAB 3: TABLE
# ══════════════════════════════════════════
with TAB_TABLE:
    need_sub3 = (not st.session_state.authenticated and
                 not is_subscribed(uid) and get_trial(uid)==0)
    if need_sub3:
        show_sub_block("table")
    elif not st.session_state.results:
        st.info("🔍 Аввал чап панелдан қидирув бошланг.")
    else:
        df = pd.DataFrame(st.session_state.results)
        df_show = df.copy()
        df_show['Кўришлар']  = df_show['views'].apply(fmt)
        df_show['Обуначи']   = df_show['subs'].apply(fmt)
        df_show['Лайклар']   = df_show['likes'].apply(fmt)
        df_show['Изоҳлар']   = df_show['comments'].apply(fmt)
        df_show['Сана']      = df_show['published'].apply(uzb_date)
        df_show['Score']     = df_show['outlier']
        df_show['Engage%']   = (
            (df_show['likes']+df_show['comments'])/df_show['views'].clip(lower=1)*100
        ).round(2)

        st.dataframe(
            df_show[['thumbnail','title','channel','Score','Кўришлар',
                      'Обуначи','Лайклар','Engage%','Сана','url']],
            column_config={
                "thumbnail": st.column_config.ImageColumn("🖼", width="small"),
                "title":     st.column_config.TextColumn("Сарлавҳа", width="large"),
                "channel":   st.column_config.TextColumn("Канал"),
                "Score":     st.column_config.NumberColumn("⚡ Score", format="%.1fx"),
                "Engage%":   st.column_config.NumberColumn("💬 Engage", format="%.2f%%"),
                "url":       st.column_config.LinkColumn("🔗 Havola", display_text="▶ Ko'rish"),
            },
            use_container_width=True, hide_index=True,
            height=min(60+len(df_show)*36, 700)
        )

        # CSV export
        _topic_name = st.session_state.get("last_topic","result")
        csv = df_show[['title','channel','Score','views','subs','likes','comments','url']].to_csv(index=False)
        st.download_button("⬇️ CSV да юклаш", csv, f"viral777_{_topic_name}_{datetime.now().strftime('%Y%m%d')}.csv",
                           "text/csv", use_container_width=True)

# ══════════════════════════════════════════
# TAB 4: CHARTS
# ══════════════════════════════════════════
with TAB_CHART:
    need_sub4 = (not st.session_state.authenticated and
                 not is_subscribed(uid) and get_trial(uid)==0)
    if need_sub4:
        show_sub_block("charts")
    elif not st.session_state.results:
        st.info("🔍 Аввал чап панелдан қидирув бошланг.")
    else:
        df = pd.DataFrame(st.session_state.results)

        ch1, ch2 = st.columns(2)

        # Views vs Outlier scatter
        with ch1:
            st.markdown("<div class='section-title'>👁 Кўришлар vs Viral Score</div>",
                        unsafe_allow_html=True)
            fig1 = px.scatter(
                df, x='views', y='outlier',
                size='likes', color='outlier',
                hover_name='title',
                hover_data={'channel':True,'views':':,.0f','outlier':':.1f'},
                color_continuous_scale=['#2a2a58','#6c63ff','#ff4757'],
                labels={'views':'Кўришлар','outlier':'Viral Score'},
                size_max=30, log_x=True,
            )
            fig1.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                height=320, margin=dict(l=0,r=0,t=10,b=0),
                font=dict(color='#aaaacc',family='Inter'),
                xaxis=dict(gridcolor='#1e1e2e',color='#666688'),
                yaxis=dict(gridcolor='#1e1e2e',color='#666688'),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig1, use_container_width=True)

        # Score distribution
        with ch2:
            st.markdown("<div class='section-title'>📊 Viral Score Тарқалиши</div>",
                        unsafe_allow_html=True)
            fig2 = px.histogram(
                df, x='outlier', nbins=20,
                color_discrete_sequence=['#6c63ff'],
                labels={'outlier':'Viral Score','count':'Видеолар сони'},
            )
            fig2.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                height=320, margin=dict(l=0,r=0,t=10,b=0),
                font=dict(color='#aaaacc',family='Inter'),
                xaxis=dict(gridcolor='#1e1e2e',color='#666688'),
                yaxis=dict(gridcolor='#1e1e2e',color='#666688'),
                bargap=0.1,
            )
            fig2.update_traces(marker_line_width=0, opacity=0.85)
            st.plotly_chart(fig2, use_container_width=True)

        ch3, ch4 = st.columns(2)

        # Top channels bar
        with ch3:
            st.markdown("<div class='section-title'>📺 Энг Кўп Видео Чиқарган Каналлар</div>",
                        unsafe_allow_html=True)
            ch_cnt = df.groupby('channel').size().sort_values(ascending=False).head(10)
            fig3 = px.bar(
                x=ch_cnt.values, y=ch_cnt.index, orientation='h',
                color=ch_cnt.values,
                color_continuous_scale=['#2a2a58','#6c63ff'],
                labels={'x':'Видеолар сони','y':''},
            )
            fig3.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                height=320, margin=dict(l=0,r=0,t=10,b=0),
                font=dict(color='#aaaacc',family='Inter'),
                xaxis=dict(gridcolor='#1e1e2e',color='#666688'),
                yaxis=dict(color='#ccccdd'),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig3, use_container_width=True)

        # Engagement
        with ch4:
            st.markdown("<div class='section-title'>💬 Engagement Rate Таҳлили</div>",
                        unsafe_allow_html=True)
            df['engage'] = ((df['likes']+df['comments'])/df['views'].clip(lower=1)*100).round(2)
            fig4 = px.box(
                df, y='engage', points='all',
                color_discrete_sequence=['#6c63ff'],
                labels={'engage':'Engagement Rate (%)'},
            )
            fig4.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                height=320, margin=dict(l=0,r=0,t=10,b=0),
                font=dict(color='#aaaacc',family='Inter'),
                yaxis=dict(gridcolor='#1e1e2e',color='#666688'),
            )
            st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════
# TAB 5: HISTORY
# ══════════════════════════════════════════
with TAB_HISTORY:
    if st.session_state.history:
        st.markdown("<div class='section-title'>🕐 Қидирув Тарихи</div>",
                    unsafe_allow_html=True)
        hist_df = pd.DataFrame(st.session_state.history).iloc[::-1]
        st.dataframe(hist_df, use_container_width=True, hide_index=True)

        if st.button("🗑 Тарихни тозалаш"):
            st.session_state.history=[]; st.rerun()
    else:
        st.info("🕐 Ҳали қидирув амалга оширилмаган.")
