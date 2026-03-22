"""
===================================================
ABS VIRAL 777 — app.py
Streamlit sайт + Telegram бот (background thread)
===================================================

O'rnatish:
    pip install streamlit google-api-python-client pandas pyTelegramBotAPI

Streamlit Cloud da secrets.toml (Settings > Secrets):
    [general]
    BOT_TOKEN        = "123456:ABC..."
    ADMIN_CHAT_ID    = "123456789"
    PAYME_MERCHANT   = "your_merchant_id"
    CLICK_SERVICE    = "your_service_id"
    CLICK_MERCHANT   = "your_merchant_id"
    TELEGRAM_BOT_LINK = "https://t.me/your_bot"

    [users]
    data = "{}"
"""

import streamlit as st
import googleapiclient.discovery
import pandas as pd
from datetime import datetime, timedelta
import re, json, os, base64, uuid, hashlib
import threading
import random
import string

# ── Telegram bot ──
try:
    import telebot
    BOT_AVAILABLE = True
except ImportError:
    BOT_AVAILABLE = False

# ============================================================
# КОНФИГ
# ============================================================
SUBSCRIPTION_PRICE = 50000
SUBSCRIPTION_DAYS  = 30
FREE_TRIAL_LIMIT   = 3
ADMIN_DB           = {"baho123": "qWe83664323546"}

def get_secret(key, default=""):
    try:
        return st.secrets["general"][key]
    except:
        return os.environ.get(key, default)

BOT_TOKEN         = get_secret("BOT_TOKEN")
ADMIN_CHAT_ID     = get_secret("ADMIN_CHAT_ID")
PAYME_MERCHANT    = get_secret("PAYME_MERCHANT")
CLICK_SERVICE     = get_secret("CLICK_SERVICE")
CLICK_MERCHANT    = get_secret("CLICK_MERCHANT")
TELEGRAM_BOT_LINK = get_secret("TELEGRAM_BOT_LINK", "https://t.me/your_bot")

# ============================================================
# МАЪЛУМОТЛАР БАЗАСИ — st.secrets ichida saqlanadi
# Streamlit Cloud restart bo'lganda ham qoladi
# ============================================================
# Secrets o'zgartirish mumkin emas runtime da,
# shuning uchun server memory + JSON file kombinatsiyasini ishlatamiz.
# Streamlit Cloud da /tmp papkasi restart gacha saqlanadi.

DB_FILE = "/tmp/viral777_db.json"

def load_db():
    # 1. /tmp fayldan olish
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    # 2. secrets dan olish (backup)
    try:
        raw = st.secrets["users"]["data"]
        return json.loads(raw)
    except:
        pass
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_user(uid):
    db = load_db()
    if uid not in db:
        db[uid] = {"trial_used": 0, "subscribed": False,
                   "sub_until": None, "orders": []}
        save_db(db)
    return db[uid]

def save_user(uid, data):
    db = load_db()
    db[uid] = data
    save_db(db)

def is_subscribed(uid):
    user = get_user(uid)
    if not user.get("subscribed"):
        return False
    if user.get("sub_until"):
        until = datetime.fromisoformat(user["sub_until"])
        if datetime.now() > until:
            user["subscribed"] = False
            user["sub_until"] = None
            save_user(uid, user)
            return False
    return True

def get_trial_remaining(uid):
    return max(0, FREE_TRIAL_LIMIT - get_user(uid).get("trial_used", 0))

def use_trial(uid):
    user = get_user(uid)
    user["trial_used"] = user.get("trial_used", 0) + 1
    save_user(uid, user)

def activate_subscription(uid, order_id):
    user = get_user(uid)
    user["subscribed"] = True
    user["sub_until"] = (datetime.now() + timedelta(days=SUBSCRIPTION_DAYS)).isoformat()
    user.setdefault("orders", []).append({
        "id": order_id, "date": datetime.now().isoformat()
    })
    save_user(uid, user)

def gen_code():
    chars = string.ascii_uppercase + string.digits
    db = load_db()
    codes = db.get("activation_codes", {})
    for _ in range(100):
        code = ''.join(random.choices(chars, k=6))
        if code not in codes:
            return code
    return ''.join(random.choices(chars, k=8))

def save_code(code, telegram_id, order_id, note="", days=30):
    db = load_db()
    db.setdefault("activation_codes", {})[code] = {
        "telegram_id": str(telegram_id),
        "order_id":    order_id,
        "note":        note,
        "created":     datetime.now().isoformat(),
        "expires":     (datetime.now() + timedelta(days=days)).isoformat(),
        "used":        False
    }
    save_db(db)

def activate_by_code(code, uid):
    db = load_db()
    codes = db.get("activation_codes", {})
    code = code.strip().upper()

    if code not in codes:
        return False, "❌ Код топилмади. Тўғри киритганингизни текширинг."
    c = codes[code]
    if c.get("used"):
        return False, "❌ Бу код аллақачон ишлатилган."
    expires = datetime.fromisoformat(c["expires"])
    if datetime.now() > expires:
        return False, "❌ Код муддати тугаган. Телеграм ботдан янги код олинг."

    activate_subscription(uid, code)
    codes[code]["used"] = True
    codes[code]["used_by"] = uid
    codes[code]["used_at"] = datetime.now().isoformat()
    db["activation_codes"] = codes
    save_db(db)
    return True, "✅ Обуна муваффақиятли фаоллашди!"

# ============================================================
# ТЎЛОВ URL
# ============================================================
def make_payme_url(order_id):
    params = f"m={PAYME_MERCHANT};ac.order_id={order_id};a={SUBSCRIPTION_PRICE * 100}"
    return f"https://checkout.paycom.uz/{base64.b64encode(params.encode()).decode()}"

def make_click_url(order_id):
    return (f"https://my.click.uz/services/pay?"
            f"service_id={CLICK_SERVICE}&merchant_id={CLICK_MERCHANT}"
            f"&amount={SUBSCRIPTION_PRICE}&transaction_param={order_id}")

# ============================================================
# TELEGRAM BOT — background thread
# ============================================================
_bot_started = False

def start_bot():
    global _bot_started
    if not BOT_AVAILABLE or not BOT_TOKEN or BOT_TOKEN == "":
        return
    if _bot_started:
        return
    _bot_started = True

    bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

    @bot.message_handler(commands=['start'])
    def cmd_start(msg):
        order_id = f"V777_{uuid.uuid4().hex[:10].upper()}"
        p_url = make_payme_url(order_id)
        c_url = make_click_url(order_id)

        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            telebot.types.InlineKeyboardButton("💳 Payme орқали тўлаш",  url=p_url),
            telebot.types.InlineKeyboardButton("⚡ Click орқали тўлаш",  url=c_url),
            telebot.types.InlineKeyboardButton("✅ Тўлов қилдим — код олиш",
                                               callback_data=f"paid:{order_id}"),
        )
        bot.send_message(
            msg.chat.id,
            f"👋 *ABS Viral 777* га хуш келибсиз!\n\n"
            f"🚀 YouTube вирал таҳлил воситаси\n\n"
            f"💰 *Ойлик обуна:* `{SUBSCRIPTION_PRICE:,} сўм`\n"
            f"📅 30 кун · ♾️ Чексиз қидирув\n\n"
            f"Тўловни амалга ошириб, *\"Тўлов қилдим\"* тугмасини босинг:",
            parse_mode="Markdown",
            reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("paid:"))
    def cb_paid(call):
        order_id    = call.data.split(":", 1)[1]
        telegram_id = call.from_user.id
        first_name  = call.from_user.first_name or "Фойдаланувчи"

        bot.answer_callback_query(call.id, "⏳ Текширилмоқда...")

        # Код яратиш ва сақлаш
        code = gen_code()
        save_code(code, telegram_id, order_id)

        # Мижозга код юборish
        bot.send_message(
            telegram_id,
            f"✅ *Тўлов қабул қилинди!*\n\n"
            f"🔑 Сизнинг активация кодингиз:\n\n"
            f"```\n{code}\n```\n\n"
            f"📌 Сайтга қайтинг ва ушбу кодни киритинг.\n"
            f"⏰ Код *24 соат* амал қилади.\n\n"
            f"🌐 {TELEGRAM_BOT_LINK.replace('t.me/', 'viral777.streamlit.app')}",
            parse_mode="Markdown"
        )

        # Adminga xabar
        if ADMIN_CHAT_ID:
            try:
                bot.send_message(
                    int(ADMIN_CHAT_ID),
                    f"💰 *Янги тўлов!*\n\n"
                    f"👤 {first_name} (ID: `{telegram_id}`)\n"
                    f"📋 Буюртма: `{order_id}`\n"
                    f"🔑 Код: `{code}`\n"
                    f"💵 {SUBSCRIPTION_PRICE:,} сўм\n"
                    f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                    parse_mode="Markdown"
                )
            except:
                pass

    @bot.message_handler(commands=['admin'])
    def cmd_admin(msg):
        if str(msg.chat.id) != str(ADMIN_CHAT_ID):
            return
        db       = load_db()
        users    = {k:v for k,v in db.items() if k not in ("activation_codes",)}
        codes    = db.get("activation_codes", {})
        active   = sum(1 for u in users.values() if u.get("subscribed"))
        used_c   = sum(1 for c in codes.values() if c.get("used"))
        unused_c = sum(1 for c in codes.values() if not c.get("used"))
        bot.send_message(
            msg.chat.id,
            f"📊 *Статистика*\n\n"
            f"👥 Жами фойдаланувчи: `{len(users)}`\n"
            f"✅ Фаол обуналар: `{active}`\n"
            f"🔑 Ишлатилган кодлар: `{used_c}`\n"
            f"⏳ Кутилаётган кодлар: `{unused_c}`",
            parse_mode="Markdown"
        )

    @bot.message_handler(commands=['kod'])
    def cmd_kod(msg):
        """Admin qo'lda kod yuborish: /kod TELEGRAM_ID"""
        if str(msg.chat.id) != str(ADMIN_CHAT_ID):
            return
        parts = msg.text.split()
        if len(parts) < 2:
            bot.send_message(msg.chat.id, "Format: /kod TELEGRAM\\_ID", parse_mode="Markdown")
            return
        target = parts[1]
        code   = gen_code()
        save_code(code, target, f"MANUAL_{uuid.uuid4().hex[:6]}", note="admin_manual")
        try:
            bot.send_message(
                int(target),
                f"✅ *Активация кодингиз:*\n\n```\n{code}\n```\n\nСайтга киринг ва кодни киритинг.",
                parse_mode="Markdown"
            )
            bot.send_message(msg.chat.id, f"✅ Юборildi: `{code}`", parse_mode="Markdown")
        except Exception as e:
            bot.send_message(msg.chat.id, f"❌ Хато: {e}")

    def polling_thread():
        while True:
            try:
                bot.infinity_polling(timeout=20, long_polling_timeout=15)
            except Exception as e:
                import time
                time.sleep(5)

    t = threading.Thread(target=polling_thread, daemon=True)
    t.start()

# Botni faqat bir marta ishga tushirish
if "bot_started" not in st.session_state:
    st.session_state["bot_started"] = True
    threading.Thread(target=start_bot, daemon=True).start()

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(page_title="ABS Viral 777", page_icon="📈", layout="wide")

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
*, *::before, *::after { box-sizing: border-box; }
html, body, .stApp, .main, .block-container {
    background-color: #0e1117 !important; color: #ffffff !important;
}
[data-testid="stSidebar"], [data-testid="stSidebar"] > div {
    background-color: #161b22 !important;
}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span,
[data-testid="stSidebar"] label, [data-testid="stSidebar"] div,
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] small {
    color: #ffffff !important;
}
input, textarea { background-color: #1c1f26 !important; color: #ffffff !important; border-color: #444 !important; }
[data-baseweb="input"] { background-color: #1c1f26 !important; }
[data-baseweb="select"] > div, [data-baseweb="popover"] { background-color: #1c1f26 !important; color: #ffffff !important; }
[data-baseweb="select"] span, [data-baseweb="option"] { color: #ffffff !important; }
[role="radiogroup"] label, [role="radiogroup"] p, [role="radiogroup"] span,
div[data-testid="stRadio"] label, div[data-testid="stRadio"] p { color: #ffffff !important; }
[data-testid="stSlider"] p, [data-testid="stSlider"] label,
[data-testid="stSlider"] span { color: #ffffff !important; }
[data-baseweb="tab-list"] { background-color: #0e1117 !important; border-bottom: 1px solid #333 !important; }
[data-baseweb="tab"] { color: #aaaaaa !important; background-color: transparent !important; }
[aria-selected="true"][data-baseweb="tab"] { color: #FF0000 !important; border-bottom: 3px solid #FF0000 !important; }
.stButton > button {
    background: linear-gradient(90deg, #FF0000, #CC0000) !important;
    color: #ffffff !important; border-radius: 12px !important;
    font-weight: 800 !important; text-transform: uppercase !important;
    border: none !important; height: 3.2em !important; width: 100% !important;
    transition: all 0.3s !important; font-size: 14px !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 24px rgba(255,0,0,0.5) !important; }
.stButton > button:disabled { background: #2a2a2a !important; color: #555 !important; }
[data-testid="stDataFrame"], [data-testid="stDataFrame"] * { background-color: #1c1f26 !important; color: #ffffff !important; }
[data-testid="stAlert"] { background-color: #1c1f26 !important; color: #ffffff !important; border-radius: 10px !important; }
[data-testid="stMarkdownContainer"] p, .stCaption { color: #cccccc !important; }
[data-testid="stExpander"] { background-color: #1c1f26 !important; border: 1px solid #333 !important; border-radius: 10px !important; }
[data-testid="stExpander"] summary p, [data-testid="stExpander"] p { color: #ffffff !important; }
table { background-color: #1c1f26 !important; color: #ffffff !important; }
th { background-color: #252830 !important; color: #ffffff !important; }
td { color: #dddddd !important; }
hr { border-color: #333 !important; margin: 12px 0 !important; }
.metric-card { background: #1c1f26; border: 1px solid #2d3139; border-radius: 14px; padding: 16px; text-align: center; }
.metric-value { font-size: 22px; font-weight: 900; color: #FF0000; }
.metric-label { color: #8a8d97; font-size: 11px; text-transform: uppercase; margin-top: 4px; }
.niche-score { background: linear-gradient(135deg,#1e1e26,#111116); border: 2px solid #FF0000; padding: 28px; border-radius: 18px; text-align: center; margin-bottom: 22px; }
.subscription-box { background: linear-gradient(135deg,#1a1a2e,#16213e); border: 2px solid #FF0000; border-radius: 20px; padding: 40px; text-align: center; margin: 20px 0; }
.activation-box { background: #1c1f26; border: 2px solid #00AAFF; border-radius: 16px; padding: 28px; text-align: center; margin: 16px 0; }
.tg-btn { display: inline-block; background: #229ED9; color: #fff !important; padding: 16px 36px; border-radius: 14px; font-weight: 900; font-size: 16px; text-decoration: none !important; margin: 10px 0; }
.badge-trial { background:#1c1f26; border:1px solid #FF9944; border-radius:10px; padding:10px 14px; color:#FF9944; font-weight:700; font-size:13px; }
.badge-active { background:#0d2818; border:1px solid #00FF88; border-radius:10px; padding:10px 14px; color:#00FF88; font-weight:700; font-size:13px; }
.badge-expired { background:#2a1010; border:1px solid #FF4444; border-radius:10px; padding:10px 14px; color:#FF4444; font-weight:700; font-size:13px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# UID
# ============================================================
def get_uid():
    if "uid" in st.session_state and st.session_state["uid"]:
        return st.session_state["uid"]
    uid_param = st.query_params.get("uid", "")
    if uid_param and len(uid_param) >= 10:
        st.session_state["uid"] = uid_param
        return uid_param
    new_uid = "u_" + uuid.uuid4().hex
    st.session_state["uid"] = new_uid
    st.query_params["uid"] = new_uid
    return new_uid

# ============================================================
# ЁРДАМЧИЛАР
# ============================================================
def fmt(n):
    if n >= 1_000_000: return f"{round(n/1_000_000,1)}M"
    elif n >= 1_000:   return f"{round(n/1_000,1)}K"
    return str(n)

def uzb_date(iso):
    M = {1:"Янв",2:"Фев",3:"Мар",4:"Апр",5:"Май",6:"Июн",
         7:"Июл",8:"Авг",9:"Сен",10:"Окт",11:"Ноя",12:"Дек"}
    try:
        dt = datetime.strptime(re.sub(r'\.\d+Z','Z',iso),'%Y-%m-%dT%H:%M:%SZ')
        return f"{dt.day}-{M[dt.month]}, {dt.year}"
    except:
        return iso[:10]

REGIONS = {"US":"en","GB":"en","UZ":"uz","RU":"ru","TR":"tr"}

# ============================================================
# СЕССИЯ
# ============================================================
for k,v in [("authenticated",False),("last_results",None),("search_history",[])]:
    if k not in st.session_state:
        st.session_state[k] = v

uid = get_uid()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("## 🎯 777 VIRAL ENGINE")
    st.divider()

    if not st.session_state.authenticated:
        with st.expander("🔐 Admin Кириш"):
            u_in = st.text_input("Логин", key="sb_login")
            p_in = st.text_input("Пароль", type="password", key="sb_pass")
            if st.button("КИРИШ", key="sb_btn"):
                if ADMIN_DB.get(u_in) == p_in:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Нотўғри!")
    else:
        st.success("✅ Admin режим фаол")
        if st.button("🚪 ЧИҚИШ"):
            st.session_state.authenticated = False
            st.rerun()

    st.divider()

    if not st.session_state.authenticated:
        if is_subscribed(uid):
            ud = get_user(uid)
            until_str = datetime.fromisoformat(ud["sub_until"]).strftime("%d.%m.%Y")
            st.markdown(f"<div class='badge-active'>✅ Обуна · {until_str} гача</div>",
                        unsafe_allow_html=True)
        else:
            rem = get_trial_remaining(uid)
            if rem > 0:
                st.markdown(f"<div class='badge-trial'>🎁 Синов: {rem}/{FREE_TRIAL_LIMIT} қолди</div>",
                            unsafe_allow_html=True)
            else:
                st.markdown("<div class='badge-expired'>🔒 Синов тугади</div>",
                            unsafe_allow_html=True)

    st.divider()

    saved_key = st.query_params.get("apikey", "")
    api_input = st.text_input("🔑 YouTube API Key:", value=saved_key, type="password")
    if api_input and api_input != saved_key:
        st.query_params["apikey"] = api_input

    topic     = st.text_input("🔍 Мавзу:", "Survival")
    region    = st.selectbox("🌍 Давлат:", list(REGIONS.keys()))
    days_sel  = st.select_slider("📅 Давр (кун):", options=[7,30,90,180,365], value=30)
    min_views = st.selectbox("👁️ Min Кўришлар:", [0,100000,500000,1000000],
                              format_func=lambda x: fmt(x) if x > 0 else "Ҳаммаси")
    min_outl  = st.slider("🔥 Min Outlier:", 1, 50, 15)

    can_search = (st.session_state.authenticated or
                  is_subscribed(uid) or get_trial_remaining(uid) > 0)
    search_btn = st.button("🚀 ТАҲЛИЛНИ БОШЛАШ", disabled=not can_search)

# ============================================================
# ТАБЛАР
# ============================================================
t1, t2, t3 = st.tabs(["🚀 АСОСИЙ ТАҲЛИЛ", "📜 ҚИДИРУВ ТАРИХИ", "🛡️ ADMIN ПАНЕЛ"])

# ─────────── TAB 1 ───────────
with t1:

    # ОБУНА БЛОКИ
    if (not st.session_state.authenticated and
            not is_subscribed(uid) and
            get_trial_remaining(uid) == 0):

        st.markdown(f"""
        <div class='subscription-box'>
            <div style='font-size:52px;'>🔒</div>
            <h2 style='color:#fff; margin:10px 0 6px;'>Синов муддати тугади</h2>
            <p style='color:#aaa; font-size:14px; margin-bottom:16px;'>
                Давом этиш учун Telegram бот орқали обуна сотиб олинг.<br>
                Тўловдан сўнг бот сизга <b>активация кодини дарҳол</b> юборади.
            </p>
            <div style='font-size:44px; font-weight:900; color:#FF0000; margin:14px 0;'>
                {SUBSCRIPTION_PRICE:,} сўм
            </div>
            <p style='color:#555; font-size:13px; margin-bottom:20px;'>
                📅 30 кун &nbsp;·&nbsp; ♾️ Чексиз қидирув
            </p>
            <a href='{TELEGRAM_BOT_LINK}' target='_blank' class='tg-btn'>
                ✈️ &nbsp;Telegram ботга ўтиш
            </a>
            <br>
            <p style='color:#444; font-size:11px; margin-top:14px;'>
                /start → тўлов → "Тўлов қилдим" → код → сайтга киритинг
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class='activation-box'>
            <div style='font-size:32px;'>🔑</div>
            <h3 style='color:#fff; margin:6px 0 4px;'>Активация кодини киритинг</h3>
            <p style='color:#666; font-size:13px; margin-bottom:0;'>
                Телеграм ботдан олган 6 та белгили кодингизни киритинг
            </p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            code_input = st.text_input(
                "Код:", placeholder="Масалан: 4X9K2M",
                max_chars=6, key="code_input"
            ).strip().upper()
            if st.button("🔓 КОДНИ ТАСДИҚЛАШ"):
                if len(code_input) < 6:
                    st.error("❌ Код 6 та белгидан иборат!")
                else:
                    ok, msg = activate_by_code(code_input, uid)
                    if ok:
                        st.success(msg)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(msg)

    # ҚИДИРУВ
    if search_btn:
        current_key = st.query_params.get("apikey","") or api_input
        if not current_key:
            st.error("‼️ YouTube API Key киритилмаган!")
        else:
            try:
                with st.spinner("📊 YouTube таҳлил қилинмоқда..."):
                    yt = googleapiclient.discovery.build("youtube","v3",developerKey=current_key)
                    pub_after = (datetime.utcnow()-timedelta(days=days_sel)).isoformat()+"Z"
                    res = yt.search().list(q=topic, part="snippet", type="video",
                                          maxResults=50, order="viewCount",
                                          publishedAfter=pub_after, regionCode=region).execute()
                    results = []
                    for item in res['items']:
                        vid = item['id']['videoId']
                        vi  = yt.videos().list(part="statistics,snippet",id=vid).execute()['items'][0]
                        ci  = yt.channels().list(part="statistics,snippet",
                                  id=item['snippet']['channelId']).execute()['items'][0]
                        views = int(vi['statistics'].get('viewCount',0))
                        subs  = int(ci['statistics'].get('subscriberCount',1))
                        outl  = round(views/(subs if subs>1000 else 1000),1)
                        if outl >= min_outl and views >= min_views:
                            results.append({
                                "Расм":     vi['snippet']['thumbnails']['default']['url'],
                                "Вираллик": outl,
                                "Сарлавҳа": vi['snippet']['title'],
                                "Просмотр": views, "Обуначи": subs,
                                "Юкланган": uzb_date(vi['snippet']['publishedAt']),
                                "Ҳавола":   f"https://www.youtube.com/watch?v={vid}",
                                "Канал":    item['snippet']['channelTitle']
                            })
                    st.session_state.last_results = results
                    st.session_state.search_history.append({
                        "Вақт": datetime.now().strftime("%H:%M"),
                        "Мавзу": topic, "Топилди": len(results)
                    })
                    if not st.session_state.authenticated and not is_subscribed(uid):
                        use_trial(uid)
                        rem = get_trial_remaining(uid)
                        if rem > 0:
                            st.info(f"🎁 Яна **{rem}** та текин қидирув қолди")
                        else:
                            st.warning("⚠️ Охирги синов ишлатилди!")
            except Exception as e:
                st.error(f"⚠️ Хато: {e}")

    # НАТИЖАЛАР
    if st.session_state.last_results:
        df = pd.DataFrame(st.session_state.last_results).sort_values("Вираллик",ascending=False)
        avg_v = round(df["Вираллик"].mean(),1) if not df.empty else 0
        st.markdown(f"""
        <div class='niche-score'>
            <h1 style='color:#FF0000;font-size:50px;margin:0;'>{avg_v}x</h1>
            <p style='color:#aaa;font-size:15px;margin:8px 0 0;'>VIRAL POTENTIAL SCORE</p>
            <p style='color:#555;font-size:12px;margin:4px 0 0;'>
                Ушбу мавзудаги видеолар ўртача {avg_v} баравар кўпроқ кўрилмоқда!
            </p>
        </div>""", unsafe_allow_html=True)

        mode = st.radio("👀 Кўриниш:", ["Карточка","Жадвал"], horizontal=True)
        if mode == "Карточка":
            for _, row in df.iterrows():
                c1,c2 = st.columns([1,3])
                with c1: st.image(row['Расм'], use_container_width=True)
                with c2:
                    st.markdown(f"### [{row['Сарлавҳа']}]({row['Ҳавола']})")
                    st.caption(f"📺 {row['Канал']}  |  📅 {row['Юкланган']}")
                    m1,m2,m3 = st.columns(3)
                    for col,lbl,val in [(m1,"Вираллик",f"{row['Вираллик']}x"),
                                        (m2,"Просмотр",fmt(row['Просмотр'])),
                                        (m3,"Обуначи",fmt(row['Обуначи']))]:
                        col.markdown(f"<div class='metric-card'><div class='metric-label'>{lbl}</div>"
                                     f"<div class='metric-value'>{val}</div></div>",
                                     unsafe_allow_html=True)
                st.divider()
        else:
            dd = df.copy()
            dd['Просмотр'] = dd['Просмотр'].apply(fmt)
            dd['Обуначи']  = dd['Обуначи'].apply(fmt)
            st.dataframe(dd[["Расм","Сарлавҳа","Вираллик","Просмотр","Обуначи","Юкланган","Канал","Ҳавола"]],
                column_config={"Расм":st.column_config.ImageColumn("Превью"),
                               "Ҳавола":st.column_config.LinkColumn("YouTube",display_text="📺")},
                use_container_width=True, hide_index=True)

# ─────────── TAB 2 ───────────
with t2:
    if st.session_state.search_history:
        st.table(pd.DataFrame(st.session_state.search_history).iloc[::-1])
    else:
        st.info("Ҳали қидирув амалга оширилмаган.")

# ─────────── TAB 3: ADMIN ───────────
with t3:
    if not st.session_state.authenticated:
        st.warning("🔒 Бу бўлим фақат Admin учун!")
        st.stop()

    st.subheader("🛡️ Admin Бошқаруви")
    db = load_db()
    all_users = {k:v for k,v in db.items() if k != "activation_codes"}
    all_codes = db.get("activation_codes", {})

    # Статистика
    active_sub = sum(1 for u in all_users.values() if u.get("subscribed"))
    used_c     = sum(1 for c in all_codes.values() if c.get("used"))
    unused_c   = sum(1 for c in all_codes.values() if not c.get("used"))

    s1,s2,s3,s4 = st.columns(4)
    for col,lbl,val in [(s1,"Фойдаланувчи",len(all_users)),
                         (s2,"Фаол обуна",active_sub),
                         (s3,"Ишлатилган код",used_c),
                         (s4,"Кутилаётган код",unused_c)]:
        col.markdown(f"<div class='metric-card'><div class='metric-label'>{lbl}</div>"
                     f"<div class='metric-value'>{val}</div></div>", unsafe_allow_html=True)

    st.divider()

    # Qo'lda kod yaratish
    st.markdown("### ⚡ Қўлда Активация Коди Яратиш")
    c1,c2,c3 = st.columns(3)
    m_note  = c1.text_input("Изоҳ (исм/чек):")
    m_days  = c2.number_input("Муддат (кун):", min_value=1, max_value=365, value=30)
    m_count = c3.number_input("Нечта код:", min_value=1, max_value=10, value=1)

    if st.button("🔑 Код Яратиш"):
        new_codes = []
        for _ in range(int(m_count)):
            code = gen_code()
            save_code(code, "manual", f"MANUAL_{uuid.uuid4().hex[:6]}", note=m_note, days=int(m_days))
            new_codes.append(code)
        codes_str = "  ·  ".join(f"`{c}`" for c in new_codes)
        st.success(f"✅ Яратилди: {codes_str}")

    st.divider()

    # Kodlar jadvali
    st.markdown("### 📋 Активация Кодлари")
    if all_codes:
        rows = [{
            "Код":       c,
            "Ҳолат":     "✅ Ишлатилган" if d.get("used") else "⏳ Кутмоқда",
            "Яратилган": d.get("created","")[:16],
            "Муддат":    d.get("expires","")[:10],
            "Изоҳ":      d.get("note","—"),
        } for c,d in sorted(all_codes.items(),
                             key=lambda x: x[1].get("created",""), reverse=True)]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.divider()

    # Foydalanuvchilar
    st.markdown("### 👥 Фойдаланувчилар")
    if all_users:
        rows = [{
            "UID":      uh[:18]+"...",
            "Синов":    f"{ud.get('trial_used',0)}/{FREE_TRIAL_LIMIT}",
            "Обуна":    "✅" if ud.get("subscribed") else "❌",
            "Муддат":   ud.get("sub_until","—")[:10] if ud.get("sub_until") else "—",
            "Тўловлар": len(ud.get("orders",[]))
        } for uh,ud in all_users.items()]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Ҳали фойдаланувчилар йўқ.")
