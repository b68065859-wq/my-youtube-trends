import streamlit as st
import googleapiclient.discovery
import pandas as pd
from datetime import datetime, timedelta
import re, json, os, hashlib, base64, uuid

# ============================================================
# КОНФИГ
# ============================================================
PAYME_MERCHANT_ID  = "YOUR_PAYME_MERCHANT_ID"
CLICK_SERVICE_ID   = "YOUR_CLICK_SERVICE_ID"
CLICK_MERCHANT_ID  = "YOUR_CLICK_MERCHANT_ID"
SUBSCRIPTION_PRICE = 50000
SUBSCRIPTION_DAYS  = 30
FREE_TRIAL_LIMIT   = 3
USERS_FILE         = "users_db.json"
ADMIN_DB           = {"baho123": "qWe83664323546"}

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(page_title="ABS Viral 777", page_icon="📈", layout="wide")

# ============================================================
# CSS — барча матнлар оқ, sidebar ҳам тўғри
# ============================================================
st.markdown("""
<style>
/* ===== GLOBAL ===== */
html, body, [class*="css"], .stApp {
    background-color: #0e1117 !important;
    color: #ffffff !important;
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"] {
    background-color: #161b22 !important;
}
section[data-testid="stSidebar"] * {
    color: #ffffff !important;
}
section[data-testid="stSidebar"] .stTextInput input {
    background-color: #1c1f26 !important;
    color: #ffffff !important;
    border: 1px solid #444 !important;
}
section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {
    background-color: #1c1f26 !important;
    color: #ffffff !important;
}
section[data-testid="stSidebar"] .stSelectbox svg { fill: #ffffff !important; }
section[data-testid="stSidebar"] label { color: #ffffff !important; }
section[data-testid="stSidebar"] p { color: #ffffff !important; }

/* ===== MAIN INPUTS ===== */
.stTextInput input, .stSelectbox div {
    background-color: #1c1f26 !important;
    color: #ffffff !important;
    border: 1px solid #333 !important;
}

/* ===== RADIO ===== */
.stRadio label, .stRadio div, .stRadio p,
div[data-testid="stRadio"] label,
div[data-testid="stRadio"] p {
    color: #ffffff !important;
}

/* ===== TABS ===== */
.stTabs [data-baseweb="tab"] {
    color: #aaaaaa !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    color: #FF0000 !important;
    border-bottom: 2px solid #FF0000 !important;
}

/* ===== BUTTONS ===== */
.stButton > button {
    background: linear-gradient(90deg, #FF0000, #CC0000) !important;
    color: #ffffff !important;
    border-radius: 12px !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    border: none !important;
    height: 3.2em !important;
    transition: 0.3s !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(255,0,0,0.45) !important;
}
.stButton > button:disabled {
    background: #333 !important;
    color: #666 !important;
}

/* ===== DATAFRAME ===== */
.stDataFrame, div[data-testid="stTable"] {
    background-color: #1c1f26 !important;
    color: #ffffff !important;
    border-radius: 10px !important;
}

/* ===== METRIC CARD ===== */
.metric-card {
    background: #1c1f26;
    border: 1px solid #2d3139;
    border-radius: 14px;
    padding: 18px;
    text-align: center;
}
.metric-value { font-size: 24px; font-weight: 900; color: #FF0000; }
.metric-label { color: #8a8d97; font-size: 12px; text-transform: uppercase; margin-top: 4px; }

/* ===== VIRAL SCORE ===== */
.niche-score {
    background: linear-gradient(135deg, #1e1e26, #111116);
    border: 2px solid #FF0000;
    color: white;
    padding: 30px;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 24px;
}

/* ===== SUBSCRIPTION BOX ===== */
.subscription-box {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 2px solid #FF0000;
    border-radius: 20px;
    padding: 40px;
    text-align: center;
    margin: 20px 0;
}
.pay-btn-payme {
    display: inline-block;
    background: #00AAFF;
    color: #ffffff !important;
    padding: 14px 32px;
    border-radius: 12px;
    font-weight: 900;
    font-size: 16px;
    text-decoration: none !important;
    margin: 8px 6px;
}
.pay-btn-click {
    display: inline-block;
    background: #FF6600;
    color: #ffffff !important;
    padding: 14px 32px;
    border-radius: 12px;
    font-weight: 900;
    font-size: 16px;
    text-decoration: none !important;
    margin: 8px 6px;
}

/* ===== STATUS BADGES ===== */
.badge-trial {
    background: #1c1f26;
    border: 1px solid #FF9944;
    border-radius: 10px;
    padding: 10px 14px;
    color: #FF9944 !important;
    font-weight: 700;
    font-size: 14px;
    margin-top: 8px;
}
.badge-active {
    background: #0d2818;
    border: 1px solid #00FF88;
    border-radius: 10px;
    padding: 10px 14px;
    color: #00FF88 !important;
    font-weight: 700;
    font-size: 14px;
    margin-top: 8px;
}
.badge-expired {
    background: #2a1010;
    border: 1px solid #FF4444;
    border-radius: 10px;
    padding: 10px 14px;
    color: #FF4444 !important;
    font-weight: 700;
    font-size: 14px;
    margin-top: 8px;
}

/* ===== MISC ===== */
.stMarkdown p, .stCaption, .stInfo, .stSuccess, .stWarning, .stError {
    color: #ffffff !important;
}
code { color: #aaaaaa !important; }
hr { border-color: #333 !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# МАЪЛУМОТЛАР БАЗАСИ (JSON — persistent)
# ============================================================
def load_db():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_db(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_uid():
    """IP yoki session UUID orqali barqaror UID olish"""
    try:
        from streamlit.web.server.websocket_headers import _get_websocket_headers
        headers = _get_websocket_headers()
        ip = headers.get("X-Forwarded-For", headers.get("X-Real-Ip", ""))
        ip = ip.split(",")[0].strip()
        if ip and ip != "unknown":
            return "ip_" + hashlib.sha256(ip.encode()).hexdigest()[:28]
    except:
        pass
    # Fallback: localStorage simulation via query_params
    uid_from_url = st.query_params.get("uid", "")
    if uid_from_url and len(uid_from_url) == 32:
        return uid_from_url
    # Yangi UID yaratib URL ga yozish
    new_uid = "s_" + uuid.uuid4().hex[:30]
    st.query_params["uid"] = new_uid
    return new_uid

def get_user(uid):
    db = load_db()
    if uid not in db:
        db[uid] = {"trial_used": 0, "subscribed": False, "sub_until": None, "orders": []}
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
    user = get_user(uid)
    return max(0, FREE_TRIAL_LIMIT - user.get("trial_used", 0))

def use_trial(uid):
    user = get_user(uid)
    user["trial_used"] = user.get("trial_used", 0) + 1
    save_user(uid, user)

def activate_subscription(uid, order_id):
    user = get_user(uid)
    user["subscribed"] = True
    user["sub_until"] = (datetime.now() + timedelta(days=SUBSCRIPTION_DAYS)).isoformat()
    user.setdefault("orders", []).append({"id": order_id, "date": datetime.now().isoformat()})
    save_user(uid, user)

def submit_pending(uid, order_id):
    db = load_db()
    db.setdefault("pending_orders", {})[order_id] = {
        "uid": uid, "created": datetime.now().isoformat(), "status": "pending"
    }
    save_db(db)

def admin_activate(order_id):
    db = load_db()
    p = db.get("pending_orders", {})
    if order_id in p and p[order_id]["status"] == "pending":
        uid = p[order_id]["uid"]
        activate_subscription(uid, order_id)
        p[order_id]["status"] = "activated"
        db["pending_orders"] = p
        save_db(db)
        return True, uid
    return False, None

# ============================================================
# ТЎЛОВ URL
# ============================================================
def gen_order_id():
    return f"V777_{uuid.uuid4().hex[:10].upper()}"

def payme_url(order_id, amount):
    params = f"m={PAYME_MERCHANT_ID};ac.order_id={order_id};a={amount * 100}"
    return f"https://checkout.paycom.uz/{base64.b64encode(params.encode()).decode()}"

def click_url(order_id, amount):
    return (f"https://my.click.uz/services/pay?"
            f"service_id={CLICK_SERVICE_ID}&merchant_id={CLICK_MERCHANT_ID}"
            f"&amount={amount}&transaction_param={order_id}")

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
        dt = datetime.strptime(re.sub(r'\.\d+Z','Z', iso), '%Y-%m-%dT%H:%M:%SZ')
        return f"{dt.day}-{M[dt.month]}, {dt.year}"
    except:
        return iso[:10]

REGIONS = {"US":"en","GB":"en","UZ":"uz","RU":"ru","TR":"tr"}

# ============================================================
# СЕССИЯ
# ============================================================
for k, v in [("authenticated", False), ("last_results", None),
             ("search_history", []), ("pending_order", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

uid = get_uid()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/d/db/MrBeast_logo.svg", width=90)
    st.markdown("## 777 VIRAL ENGINE")

    # --- ADMIN LOGIN ---
    if not st.session_state.authenticated:
        with st.expander("🔐 ADMIN КИРИШ"):
            u = st.text_input("Логин", key="login_u")
            p = st.text_input("Пароль", type="password", key="login_p")
            if st.button("КИРИШ", key="login_btn"):
                if ADMIN_DB.get(u) == p:
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

    # --- ОБУНА СТАТУСИ ---
    if not st.session_state.authenticated:
        if is_subscribed(uid):
            ud = get_user(uid)
            until_str = datetime.fromisoformat(ud["sub_until"]).strftime("%d.%m.%Y")
            st.markdown(f"<div class='badge-active'>✅ Обуна фаол · {until_str} гача</div>",
                        unsafe_allow_html=True)
        else:
            rem = get_trial_remaining(uid)
            if rem > 0:
                st.markdown(f"<div class='badge-trial'>🎁 Синов: {rem}/{FREE_TRIAL_LIMIT} қолди</div>",
                            unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='badge-expired'>🔒 Синов тугади — обуна керак</div>",
                            unsafe_allow_html=True)

    st.divider()

    # --- API KEY (URL да сақланади) ---
    saved_key = st.query_params.get("apikey", "")
    api_input = st.text_input("🔑 YouTube API Key:", value=saved_key, type="password")
    if api_input and api_input != saved_key:
        st.query_params["apikey"] = api_input

    topic    = st.text_input("🔍 Қидирув мавзуси:", "Survival")
    region   = st.selectbox("🌍 Давлат:", list(REGIONS.keys()))
    days_sel = st.select_slider("📅 Давр (кун):", options=[7, 30, 90, 180, 365], value=30)
    min_views = st.selectbox("👁️ Min Кўришлар:", [0, 100000, 500000, 1000000],
                             format_func=lambda x: fmt(x) if x > 0 else "Ҳаммаси")
    min_outl = st.slider("🔥 Min Outlier:", 1, 50, 15)

    can_search = (st.session_state.authenticated or
                  is_subscribed(uid) or
                  get_trial_remaining(uid) > 0)
    search_btn = st.button("🚀 ТАҲЛИЛНИ БОШЛАШ", disabled=not can_search)

# ============================================================
# ТАБЛАР
# ============================================================
t1, t2, t3 = st.tabs(["🚀 АСОСИЙ ТАҲЛИЛ", "📜 ҚИДИРУВ ТАРИХИ", "🛡️ ADMIN ПАНЕЛ"])

# ─────────── TAB 1 ───────────
with t1:

    # ── ТЎЛОВ БЛОКИ (лимит тугаганда) ──
    if (not st.session_state.authenticated and
            not is_subscribed(uid) and
            get_trial_remaining(uid) == 0):

        if not st.session_state.pending_order:
            st.session_state.pending_order = gen_order_id()
        oid   = st.session_state.pending_order
        p_url = payme_url(oid, SUBSCRIPTION_PRICE)
        c_url = click_url(oid, SUBSCRIPTION_PRICE)

        st.markdown(f"""
        <div class='subscription-box'>
            <div style='font-size:56px;'>🔒</div>
            <h2 style='color:#ffffff; margin:12px 0 8px;'>Синов муддати тугади</h2>
            <p style='color:#aaaaaa; font-size:15px; margin-bottom:20px;'>
                Сиз <b>{FREE_TRIAL_LIMIT} та текин қидирув</b>дан фойдаландингиз.<br>
                Давом этиш учун ойлик обуна сотиб олинг.
            </p>
            <div style='font-size:50px; font-weight:900; color:#FF0000; margin:20px 0;'>
                {SUBSCRIPTION_PRICE:,} сўм
            </div>
            <p style='color:#666666; font-size:13px; margin-bottom:28px;'>
                📅 30 кун &nbsp;·&nbsp; ♾️ Чексиз қидирув &nbsp;·&nbsp; 🚀 Тўлиқ имкониятлар
            </p>
            <a href='{p_url}' target='_blank' class='pay-btn-payme'>💳 &nbsp;Payme орқали</a>
            <a href='{c_url}' target='_blank' class='pay-btn-click'>⚡ &nbsp;Click орқали</a>
            <br><br>
            <p style='color:#444444; font-size:11px;'>
                Буюртма ID: <code style='color:#666;'>{oid}</code>
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.info("💡 Тўлов амалга оширилгандан сўнг қуйидаги тугмани босинг:")
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("✅ Тўловни тасдиқлаш — Admin текширади"):
                submit_pending(uid, oid)
                st.success(f"✅ Сўровингиз қабул қилинди!\n\n"
                           f"Буюртма: `{oid}`\n\n"
                           f"Admin тасдиқлагач обунангиз фаоллашади.")

    # ── ҚИДИРУВ ──
    if search_btn:
        current_key = st.query_params.get("apikey", "") or api_input
        if not current_key:
            st.error("‼️ YouTube API Key киритилмаган!")
        else:
            try:
                with st.spinner("📊 YouTube таҳлил қилинмоқда..."):
                    yt = googleapiclient.discovery.build("youtube", "v3", developerKey=current_key)
                    pub_after = (datetime.utcnow() - timedelta(days=days_sel)).isoformat() + "Z"
                    res = yt.search().list(q=topic, part="snippet", type="video",
                                          maxResults=50, order="viewCount",
                                          publishedAfter=pub_after, regionCode=region).execute()
                    results = []
                    for item in res['items']:
                        vid = item['id']['videoId']
                        vi  = yt.videos().list(part="statistics,snippet", id=vid).execute()['items'][0]
                        ci  = yt.channels().list(part="statistics,snippet",
                                  id=item['snippet']['channelId']).execute()['items'][0]
                        views = int(vi['statistics'].get('viewCount', 0))
                        subs  = int(ci['statistics'].get('subscriberCount', 1))
                        outl  = round(views / (subs if subs > 1000 else 1000), 1)
                        if outl >= min_outl and views >= min_views:
                            results.append({
                                "Расм":     vi['snippet']['thumbnails']['default']['url'],
                                "Вираллик": outl,
                                "Сарлавҳа": vi['snippet']['title'],
                                "Просмотр": views,
                                "Обуначи":  subs,
                                "Юкланган": uzb_date(vi['snippet']['publishedAt']),
                                "Ҳавола":   f"https://www.youtube.com/watch?v={vid}",
                                "Канал":    item['snippet']['channelTitle']
                            })

                    st.session_state.last_results = results
                    st.session_state.search_history.append({
                        "Вақт": datetime.now().strftime("%H:%M"),
                        "Мавзу": topic,
                        "Топилди": len(results)
                    })

                    # ── Синов ҳисобини JSON га сақлаш ──
                    if not st.session_state.authenticated and not is_subscribed(uid):
                        use_trial(uid)
                        rem = get_trial_remaining(uid)
                        if rem > 0:
                            st.info(f"🎁 Яна **{rem}** та текин қидирув қолди")
                        else:
                            st.warning("⚠️ Охирги текин қидирув ишлатилди! Обуна сотиб олинг.")

            except Exception as e:
                st.error(f"⚠️ Хато: {e}")

    # ── НАТИЖАЛАР ──
    if st.session_state.last_results:
        df = pd.DataFrame(st.session_state.last_results).sort_values("Вираллик", ascending=False)
        avg_v = round(df["Вираллик"].mean(), 1) if not df.empty else 0

        st.markdown(f"""
        <div class='niche-score'>
            <h1 style='color:#FF0000; font-size:52px; margin:0;'>{avg_v}x</h1>
            <p style='color:#aaa; font-size:16px; margin:8px 0 0;'>VIRAL POTENTIAL SCORE</p>
            <p style='color:#666; font-size:13px; margin:6px 0 0;'>
                Ушбу мавзудаги видеолар обуначилар сонига нисбатан ўртача {avg_v} баравар кўпроқ кўрилмоқда!
            </p>
        </div>
        """, unsafe_allow_html=True)

        mode = st.radio("👀 Кўриниш:", ["Карточка", "Жадвал"], horizontal=True)

        if mode == "Карточка":
            for _, row in df.iterrows():
                c1, c2 = st.columns([1, 3])
                with c1:
                    st.image(row['Расм'], use_container_width=True)
                with c2:
                    st.markdown(f"### [{row['Сарлавҳа']}]({row['Ҳавола']})")
                    st.caption(f"📺 {row['Канал']}  |  📅 {row['Юкланган']}")
                    m1, m2, m3 = st.columns(3)
                    for col, lbl, val in [
                        (m1, "Вираллик", f"{row['Вираллик']}x"),
                        (m2, "Просмотр",  fmt(row['Просмотр'])),
                        (m3, "Обуначи",   fmt(row['Обуначи']))
                    ]:
                        col.markdown(
                            f"<div class='metric-card'>"
                            f"<div class='metric-label'>{lbl}</div>"
                            f"<div class='metric-value'>{val}</div>"
                            f"</div>", unsafe_allow_html=True)
                st.divider()
        else:
            dd = df.copy()
            dd['Просмотр'] = dd['Просмотр'].apply(fmt)
            dd['Обуначи']  = dd['Обуначи'].apply(fmt)
            st.dataframe(
                dd[["Расм","Сарлавҳа","Вираллик","Просмотр","Обуначи","Юкланган","Канал","Ҳавола"]],
                column_config={
                    "Расм":   st.column_config.ImageColumn("Превью"),
                    "Ҳавола": st.column_config.LinkColumn("YouTube", display_text="📺")
                },
                use_container_width=True, hide_index=True
            )

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

    # Pending tўlovlar
    pending = {oid: d for oid, d in db.get("pending_orders", {}).items()
               if d["status"] == "pending"}
    st.markdown(f"### 📋 Тасдиқ кутаётган тўловлар: **{len(pending)}**")

    if pending:
        for oid, odata in pending.items():
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            c1.code(oid)
            c2.write(odata.get("created", "")[:16])
            c3.write(f"UID: `{odata['uid'][:10]}...`")
            if c4.button("✅ Фаол", key=f"act_{oid}"):
                ok, _ = admin_activate(oid)
                if ok:
                    st.success(f"✅ {oid} фаоллашди!")
                    st.rerun()
                else:
                    st.error("Хато!")
    else:
        st.success("✅ Тасдиқ кутаётган тўлов йўқ.")

    st.divider()

    # Qo'lda aktivatsiya
    st.markdown("### ⚡ Қўлда Фаоллаштириш")
    c1, c2 = st.columns(2)
    m_uid  = c1.text_input("Foydalanuvchi UID:")
    m_note = c2.text_input("Изоҳ (чек №):")
    if st.button("🔓 Обуна Фаоллаштириш"):
        if m_uid:
            fake_id = f"MANUAL_{uuid.uuid4().hex[:8].upper()}"
            activate_subscription(m_uid, fake_id)
            st.success(f"✅ Обуна {SUBSCRIPTION_DAYS} кунга фаоллашди!")
        else:
            st.error("UID киритинг!")

    st.divider()

    # Barcha foydalanuvchilar
    st.markdown("### 👥 Барча Фойдаланувчилар")
    all_users = {k: v for k, v in db.items() if k != "pending_orders"}
    if all_users:
        rows = []
        for uh, ud in all_users.items():
            rows.append({
                "UID":      uh[:16] + "...",
                "Синов":    f"{ud.get('trial_used',0)}/{FREE_TRIAL_LIMIT}",
                "Обуна":    "✅ Фаол" if ud.get("subscribed") else "❌",
                "Муддат":   ud.get("sub_until", "—")[:10] if ud.get("sub_until") else "—",
                "Тўловлар": len(ud.get("orders", []))
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Ҳали фойдаланувчилар йўқ.")
