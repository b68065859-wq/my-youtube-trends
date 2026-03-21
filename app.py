import streamlit as st
import googleapiclient.discovery
import pandas as pd
from datetime import datetime, timedelta
import re
import json
import os
import hashlib
import base64
import uuid

# ============================================================
# КОНФИГ — ўзингизнинг маълумотларингизни киритинг
# ============================================================
PAYME_MERCHANT_ID  = "YOUR_PAYME_MERCHANT_ID"   # Payme merchant ID
CLICK_SERVICE_ID   = "YOUR_CLICK_SERVICE_ID"     # Click service ID
CLICK_MERCHANT_ID  = "YOUR_CLICK_MERCHANT_ID"    # Click merchant ID

SUBSCRIPTION_PRICE = 50000       # 50,000 сўм
SUBSCRIPTION_DAYS  = 30          # Обуна муддати (кун)
FREE_TRIAL_LIMIT   = 3           # Текин синов сони
USERS_FILE         = "users_db.json"

ADMIN_DB = {"baho123": "qWe83664323546"}

# ============================================================
# СТИЛЛАР
# ============================================================
st.set_page_config(page_title="ABS Viral 777", page_icon="📈", layout="wide")
st.markdown("""
<style>
.stApp { background-color: #0e1117; color: #ffffff; }
.stButton>button {
    background: linear-gradient(90deg, #FF0000, #CC0000) !important;
    color: white !important; border-radius: 12px !important;
    font-weight: 800 !important; text-transform: uppercase;
    border: none !important; transition: 0.3s ease all; height: 3.5em !important;
}
.stButton>button:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(255,0,0,0.4); }
.pay-btn-payme {
    display: inline-block; background: #00AAFF; color: white !important;
    padding: 14px 32px; border-radius: 12px; font-weight: 900;
    font-size: 16px; text-decoration: none !important; margin: 8px 6px;
}
.pay-btn-click {
    display: inline-block; background: #FF6600; color: white !important;
    padding: 14px 32px; border-radius: 12px; font-weight: 900;
    font-size: 16px; text-decoration: none !important; margin: 8px 6px;
}
.subscription-box {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 2px solid #FF0000; border-radius: 20px;
    padding: 40px; text-align: center; margin: 20px 0;
}
.trial-badge {
    background: #1c1f26; border: 1px solid #FF6600;
    border-radius: 10px; padding: 10px 16px;
    color: #FF9944; font-weight: 700; font-size: 14px;
}
.active-badge {
    background: #0d2818; border: 1px solid #00FF88;
    border-radius: 10px; padding: 10px 16px;
    color: #00FF88; font-weight: 700; font-size: 14px;
}
.metric-card {
    background: #1c1f26; border: 1px solid #2d3139;
    border-radius: 16px; padding: 20px; text-align: center;
}
.metric-value { font-size: 26px; font-weight: 900; color: #FF0000; }
.metric-label { color: #8a8d97; font-size: 13px; text-transform: uppercase; }
.niche-score {
    background: linear-gradient(135deg, #1e1e26, #111116);
    border: 2px solid #FF0000; color: white;
    padding: 30px; border-radius: 20px; text-align: center; margin-bottom: 30px;
}
.stTextInput>div>div>input {
    background-color: #1c1f26 !important; color: white !important;
    border: 1px solid #2d3139 !important;
}
.stDataFrame { background-color: #1c1f26 !important; border-radius: 10px !important; }
.stRadio label, .stMarkdown p, .stCaption { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# МАЪЛУМОТЛАР БАЗАСИ
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
    """Foydalanuvchini IP yoki session UUID orqali aniqlash"""
    try:
        from streamlit.web.server.websocket_headers import _get_websocket_headers
        headers = _get_websocket_headers()
        ip = headers.get("X-Forwarded-For", headers.get("X-Real-Ip", ""))
        ip = ip.split(",")[0].strip()
        if ip:
            return hashlib.sha256(ip.encode()).hexdigest()[:32]
    except:
        pass
    if "uid" not in st.session_state:
        st.session_state.uid = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:32]
    return st.session_state.uid

def get_user(uid):
    db = load_db()
    return db.get(uid, {"trial_used": 0, "subscribed": False, "sub_until": None, "orders": []})

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

# ============================================================
# ТЎЛОВ URL ГЕНЕРАТОРЛАРИ
# ============================================================
def generate_order_id():
    return f"V777_{uuid.uuid4().hex[:10].upper()}"

def get_payme_url(order_id, amount_uzs):
    amount_tiyin = amount_uzs * 100
    params = f"m={PAYME_MERCHANT_ID};ac.order_id={order_id};a={amount_tiyin}"
    encoded = base64.b64encode(params.encode()).decode()
    return f"https://checkout.paycom.uz/{encoded}"

def get_click_url(order_id, amount_uzs):
    return (
        f"https://my.click.uz/services/pay?"
        f"service_id={CLICK_SERVICE_ID}"
        f"&merchant_id={CLICK_MERCHANT_ID}"
        f"&amount={amount_uzs}"
        f"&transaction_param={order_id}"
    )

def submit_pending_order(uid, order_id):
    db = load_db()
    db.setdefault("pending_orders", {})[order_id] = {
        "uid": uid,
        "created": datetime.now().isoformat(),
        "status": "pending"
    }
    save_db(db)

def admin_activate_order(order_id):
    db = load_db()
    pending = db.get("pending_orders", {})
    if order_id in pending and pending[order_id]["status"] == "pending":
        uid = pending[order_id]["uid"]
        activate_subscription(uid, order_id)
        pending[order_id]["status"] = "activated"
        db["pending_orders"] = pending
        save_db(db)
        return True, uid
    return False, None

# ============================================================
# ЁРДАМЧИЛАР
# ============================================================
def format_num(n):
    if n >= 1_000_000: return f"{round(n/1_000_000,1)}M"
    elif n >= 1_000:   return f"{round(n/1_000,1)}K"
    return str(n)

def uzb_date(iso):
    months = {1:"Янв",2:"Фев",3:"Мар",4:"Апр",5:"Май",6:"Июн",
              7:"Июл",8:"Авг",9:"Сен",10:"Окт",11:"Ноя",12:"Дек"}
    try:
        dt = datetime.strptime(re.sub(r'\.\d+Z','Z',iso),'%Y-%m-%dT%H:%M:%SZ')
        return f"{dt.day} {months[dt.month]} {dt.year}"
    except:
        return iso[:10]

REGIONS = {"US":"en","GB":"en","UZ":"uz","RU":"ru","TR":"tr"}

# ============================================================
# СЕССИЯ
# ============================================================
for key, val in [("authenticated",False),("last_results",None),
                 ("search_history",[]),("pending_order",None)]:
    if key not in st.session_state:
        st.session_state[key] = val

uid = get_uid()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/d/db/MrBeast_logo.svg", width=90)
    st.title("777 VIRAL ENGINE")

    if not st.session_state.authenticated:
        with st.expander("🔐 ADMIN КИРИШ"):
            u = st.text_input("Логин:")
            p = st.text_input("Пароль:", type="password")
            if st.button("КИРИШ"):
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

    # Обуна статуси
    if not st.session_state.authenticated:
        if is_subscribed(uid):
            user_d = get_user(uid)
            until_str = datetime.fromisoformat(user_d["sub_until"]).strftime("%d.%m.%Y")
            st.markdown(f"<div class='active-badge'>✅ Обуна: {until_str} гача</div>", unsafe_allow_html=True)
        else:
            rem = get_trial_remaining(uid)
            color = "#FF4444" if rem == 0 else "#FF9944"
            st.markdown(f"<div class='trial-badge' style='border-color:{color}; color:{color};'>"
                        f"🎁 Синов: {rem}/{FREE_TRIAL_LIMIT} қолди</div>", unsafe_allow_html=True)

    st.divider()

    # API Key (URL да сақланади)
    saved_key = st.query_params.get("apikey", "")
    api_input = st.text_input("🔑 YouTube API Key:", value=saved_key, type="password")
    if api_input and api_input != saved_key:
        st.query_params["apikey"] = api_input

    topic    = st.text_input("🔍 Мавзу:", "Survival")
    region   = st.selectbox("🌍 Давлат:", list(REGIONS.keys()))
    days_sel = st.select_slider("📅 Давр:", options=[7,30,90,180,365], value=30)
    min_views = st.selectbox("👁️ Min Кўришлар:", [0,100000,500000,1000000],
                             format_func=lambda x: format_num(x) if x>0 else "Ҳаммаси")
    min_outl = st.slider("🔥 Min Outlier:", 1, 50, 15)

    can_search = (st.session_state.authenticated or
                  is_subscribed(uid) or
                  get_trial_remaining(uid) > 0)
    search_btn = st.button("🚀 ТАҲЛИЛНИ БОШЛАШ", disabled=not can_search)

# ============================================================
# ТАБЛАР
# ============================================================
t1, t2, t3 = st.tabs(["🚀 ТАҲЛИЛ", "📜 ТАРИХ", "🛡️ ADMIN ПАНЕЛ"])

# ──────────── TAB 1 ────────────
with t1:

    # ── ЛИМИТ ТУГАГАН БЛОК ──
    if (not st.session_state.authenticated and
        not is_subscribed(uid) and
        get_trial_remaining(uid) == 0):

        if not st.session_state.pending_order:
            st.session_state.pending_order = generate_order_id()
        order_id  = st.session_state.pending_order
        payme_url = get_payme_url(order_id, SUBSCRIPTION_PRICE)
        click_url = get_click_url(order_id, SUBSCRIPTION_PRICE)

        st.markdown(f"""
        <div class='subscription-box'>
            <div style='font-size:60px;'>🔒</div>
            <h2 style='color:white; margin:10px 0;'>Синов муддати тугади</h2>
            <p style='color:#aaa; font-size:15px;'>
                Сиз <b>{FREE_TRIAL_LIMIT} та текин қидирув</b>дан фойдаландингиз.<br>
                Давом этиш учун ойлик обуна сотиб олинг.
            </p>
            <h1 style='color:#FF0000; font-size:52px; margin:24px 0;'>
                {SUBSCRIPTION_PRICE:,} сўм
            </h1>
            <p style='color:#666; font-size:14px; margin-bottom:24px;'>
                📅 30 кун · ♾️ Чексиз қидирув · 🚀 Тўлиқ имкониятлар
            </p>
            <a href='{payme_url}' target='_blank' class='pay-btn-payme'>💳 Payme</a>
            <a href='{click_url}' target='_blank' class='pay-btn-click'>⚡ Click</a>
            <br><br>
            <p style='color:#444; font-size:11px;'>
                Буюртма: <code style='color:#666;'>{order_id}</code>
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.info("💡 Тўлов амалга оширилгандан сўнг қуйидаги тугмани босинг:")
        if st.button("✅ Тўловни тасдиқлаш"):
            submit_pending_order(uid, order_id)
            st.success(f"✅ Сўровингиз қабул қилинди!\n\n"
                       f"Буюртма ID: `{order_id}`\n\n"
                       f"Admin тасдиқлагач обунангиз автоматик фаоллашади.")

    # ── QIDIRUV ──
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
                        vid   = item['id']['videoId']
                        vi    = yt.videos().list(part="statistics,snippet",id=vid).execute()['items'][0]
                        ci    = yt.channels().list(part="statistics,snippet",
                                    id=item['snippet']['channelId']).execute()['items'][0]
                        views  = int(vi['statistics'].get('viewCount',0))
                        subs   = int(ci['statistics'].get('subscriberCount',1))
                        outl   = round(views/(subs if subs>1000 else 1000),1)
                        if outl >= min_outl and views >= min_views:
                            results.append({
                                "Расм":vi['snippet']['thumbnails']['default']['url'],
                                "Вираллик":outl,
                                "Сарлавҳа":vi['snippet']['title'],
                                "Просмотр":views, "Обуначи":subs,
                                "Юкланган":uzb_date(vi['snippet']['publishedAt']),
                                "Ҳавола":f"https://www.youtube.com/watch?v={vid}",
                                "Канал":item['snippet']['channelTitle']
                            })

                    st.session_state.last_results = results
                    st.session_state.search_history.append({
                        "Вақт": datetime.now().strftime("%H:%M"),
                        "Мавзу": topic, "Топилди": len(results)
                    })

                    # Синов ҳисоби
                    if not st.session_state.authenticated and not is_subscribed(uid):
                        use_trial(uid)
                        rem = get_trial_remaining(uid)
                        if rem > 0:
                            st.info(f"🎁 Яна **{rem}** та текин қидирув қолди")
                        else:
                            st.warning("⚠️ Охирги текин қидирув ишлатилди. Обуна сотиб олинг!")

            except Exception as e:
                st.error(f"⚠️ Хато: {e}")

    # ── НАТИЖАЛАР ──
    if st.session_state.last_results:
        df = pd.DataFrame(st.session_state.last_results).sort_values("Вираллик", ascending=False)
        avg_v = round(df["Вираллик"].mean(), 1) if not df.empty else 0
        st.markdown(f"<div class='niche-score'><h1 style='color:#FF0000;'>{avg_v}x</h1>"
                    f"<p>VIRAL POTENTIAL SCORE</p></div>", unsafe_allow_html=True)

        mode = st.radio("👀 Кўриниш:", ["Карточка","Жадвал"], horizontal=True)
        if mode == "Карточка":
            for _, row in df.iterrows():
                c1,c2 = st.columns([1,2])
                with c1: st.image(row['Расм'], use_container_width=True)
                with c2:
                    st.markdown(f"### [{row['Сарлавҳа']}]({row['Ҳавола']})")
                    st.caption(f"📺 {row['Канал']} | 📅 {row['Юкланган']}")
                    m1,m2,m3 = st.columns(3)
                    for col,label,val in [(m1,"Вираллик",f"{row['Вираллик']}x"),
                                          (m2,"Просмотр",format_num(row['Просмотр'])),
                                          (m3,"Обуначи",format_num(row['Обуначи']))]:
                        col.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div>"
                                     f"<div class='metric-value'>{val}</div></div>", unsafe_allow_html=True)
                st.divider()
        else:
            dd = df.copy()
            dd['Просмотр'] = dd['Просмотр'].apply(format_num)
            dd['Обуначи']  = dd['Обуначи'].apply(format_num)
            st.dataframe(dd[["Расм","Сарлавҳа","Вираллик","Просмотр","Обуначи","Юкланган","Канал","Ҳавола"]],
                column_config={"Расм":st.column_config.ImageColumn("Превью"),
                               "Ҳавола":st.column_config.LinkColumn("YouTube",display_text="📺")},
                use_container_width=True, hide_index=True)

# ──────────── TAB 2 ────────────
with t2:
    if st.session_state.search_history:
        st.table(pd.DataFrame(st.session_state.search_history).iloc[::-1])
    else:
        st.info("Ҳали қидирув амалга оширилмаган.")

# ──────────── TAB 3: ADMIN ────────────
with t3:
    if not st.session_state.authenticated:
        st.warning("🔒 Бу бўлим фақат Admin учун!")
        st.stop()

    st.subheader("🛡️ Admin Бошқаруви")

    db = load_db()
    pending = {oid:d for oid,d in db.get("pending_orders",{}).items() if d["status"]=="pending"}

    # ── Pending tўlovlar ──
    st.markdown(f"### 📋 Тасдиқ кутаётган: **{len(pending)}** та тўлов")
    if pending:
        for oid, odata in pending.items():
            c1,c2,c3,c4 = st.columns([3,2,1,1])
            c1.code(oid)
            c2.caption(odata.get("created","")[:16])
            c3.caption(f"UID: {odata['uid'][:8]}...")
            if c4.button("✅", key=f"act_{oid}"):
                ok, auid = admin_activate_order(oid)
                st.success(f"✅ {oid} фаоллашди!") if ok else st.error("Хато!")
                st.rerun()
    else:
        st.success("✅ Тасдиқ кутаётган тўлов йўқ.")

    st.divider()

    # ── Qo'lda aktivatsiya ──
    st.markdown("### ⚡ Қўлда Фаоллаштириш")
    c1,c2 = st.columns(2)
    m_uid  = c1.text_input("Foydalanuvchi UID:")
    m_note = c2.text_input("Изоҳ (чек №):")
    if st.button("🔓 Обуна Фаоллаштириш"):
        if m_uid:
            fake_id = f"MANUAL_{uuid.uuid4().hex[:8].upper()}"
            activate_subscription(m_uid, fake_id)
            st.success(f"✅ {m_uid[:12]}... — 30 кунлик обуна фаоллашди!")
        else:
            st.error("UID киритинг!")

    st.divider()

    # ── Barcha foydalanuvchilar ──
    st.markdown("### 👥 Барча Фойдаланувчилар")
    all_users = {k:v for k,v in db.items() if k != "pending_orders"}
    if all_users:
        rows = []
        for uh, ud in all_users.items():
            rows.append({
                "UID (қисқа)": uh[:14]+"...",
                "Синов":       f"{ud.get('trial_used',0)}/{FREE_TRIAL_LIMIT}",
                "Обуна":       "✅ Фаол" if ud.get("subscribed") else "❌ Йўқ",
                "Муддат":      ud.get("sub_until","—")[:10] if ud.get("sub_until") else "—",
                "Тўловлар":    len(ud.get("orders",[]))
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Ҳали фойдаланувчилар йўқ.")
