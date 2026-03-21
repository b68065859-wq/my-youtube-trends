"""
pip install streamlit google-api-python-client pandas streamlit-extras
"""
import streamlit as st
import googleapiclient.discovery
import pandas as pd
from datetime import datetime, timedelta
import re, json, os, hashlib, base64, uuid

# ── Cookies uchun: pip install streamlit-extras
try:
    from streamlit_extras.add_vertical_space import add_vertical_space
except:
    pass

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
# CSS — TO'LIQ QAYTA YOZILDI
# ============================================================
st.markdown("""
<style>
/* ===== RESET ===== */
*, *::before, *::after { box-sizing: border-box; }

/* ===== GLOBAL ===== */
html, body { background-color: #0e1117 !important; color: #ffffff !important; }
.stApp, .main, .block-container {
    background-color: #0e1117 !important;
    color: #ffffff !important;
}

/* ===== SIDEBAR ===== */
[data-testid="stSidebar"], [data-testid="stSidebar"] > div {
    background-color: #161b22 !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #ffffff !important;
}

/* ===== INPUTS ===== */
input, textarea, [data-baseweb="input"] input {
    background-color: #1c1f26 !important;
    color: #ffffff !important;
    border-color: #444 !important;
}
[data-baseweb="input"] {
    background-color: #1c1f26 !important;
}

/* ===== SELECTBOX ===== */
[data-baseweb="select"] > div,
[data-baseweb="popover"] {
    background-color: #1c1f26 !important;
    color: #ffffff !important;
}
[data-baseweb="select"] span,
[data-baseweb="option"] {
    color: #ffffff !important;
}

/* ===== RADIO ===== */
[role="radiogroup"] label,
[role="radiogroup"] p,
[role="radiogroup"] span,
div[data-testid="stRadio"] label,
div[data-testid="stRadio"] p {
    color: #ffffff !important;
}

/* ===== SLIDER ===== */
[data-testid="stSlider"] p,
[data-testid="stSlider"] label,
[data-testid="stSlider"] span {
    color: #ffffff !important;
}

/* ===== TABS ===== */
[data-baseweb="tab-list"] {
    background-color: #0e1117 !important;
    border-bottom: 1px solid #333 !important;
}
[data-baseweb="tab"] {
    color: #aaaaaa !important;
    background-color: transparent !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    color: #FF0000 !important;
    border-bottom: 3px solid #FF0000 !important;
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
    width: 100% !important;
    transition: all 0.3s !important;
    font-size: 14px !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(255,0,0,0.5) !important;
}
.stButton > button:disabled {
    background: #2a2a2a !important;
    color: #555 !important;
}

/* ===== DATAFRAME ===== */
[data-testid="stDataFrame"],
[data-testid="stDataFrame"] * {
    background-color: #1c1f26 !important;
    color: #ffffff !important;
}

/* ===== ALERTS ===== */
[data-testid="stAlert"] {
    background-color: #1c1f26 !important;
    color: #ffffff !important;
    border-radius: 10px !important;
}

/* ===== CAPTION / MARKDOWN ===== */
[data-testid="stMarkdownContainer"] p,
[data-testid="stCaptionContainer"] p,
.stCaption { color: #cccccc !important; }

/* ===== EXPANDER ===== */
[data-testid="stExpander"] {
    background-color: #1c1f26 !important;
    border: 1px solid #333 !important;
    border-radius: 10px !important;
}
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] p { color: #ffffff !important; }

/* ===== TABLE ===== */
table { background-color: #1c1f26 !important; color: #ffffff !important; }
th { background-color: #252830 !important; color: #ffffff !important; }
td { color: #dddddd !important; }

/* ===== DIVIDER ===== */
hr { border-color: #333 !important; margin: 12px 0 !important; }

/* ===== CUSTOM CARDS ===== */
.metric-card {
    background: #1c1f26;
    border: 1px solid #2d3139;
    border-radius: 14px;
    padding: 16px;
    text-align: center;
}
.metric-value { font-size: 22px; font-weight: 900; color: #FF0000; }
.metric-label { color: #8a8d97; font-size: 11px; text-transform: uppercase; margin-top: 4px; }

.niche-score {
    background: linear-gradient(135deg, #1e1e26, #111116);
    border: 2px solid #FF0000;
    padding: 28px;
    border-radius: 18px;
    text-align: center;
    margin-bottom: 22px;
}

.subscription-box {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 2px solid #FF0000;
    border-radius: 20px;
    padding: 40px;
    text-align: center;
    margin: 20px 0;
}
.pay-btn-payme {
    display: inline-block; background: #00AAFF;
    color: #ffffff !important; padding: 14px 30px;
    border-radius: 12px; font-weight: 900; font-size: 15px;
    text-decoration: none !important; margin: 8px 6px;
}
.pay-btn-click {
    display: inline-block; background: #FF6600;
    color: #ffffff !important; padding: 14px 30px;
    border-radius: 12px; font-weight: 900; font-size: 15px;
    text-decoration: none !important; margin: 8px 6px;
}
.badge-trial {
    background: #1c1f26; border: 1px solid #FF9944;
    border-radius: 10px; padding: 10px 14px;
    color: #FF9944; font-weight: 700; font-size: 14px;
}
.badge-active {
    background: #0d2818; border: 1px solid #00FF88;
    border-radius: 10px; padding: 10px 14px;
    color: #00FF88; font-weight: 700; font-size: 14px;
}
.badge-expired {
    background: #2a1010; border: 1px solid #FF4444;
    border-radius: 10px; padding: 10px 14px;
    color: #FF4444; font-weight: 700; font-size: 14px;
}
</style>

<script>
// UID ni cookie sifatida saqlash (JavaScript orqali)
function setCookie(name, value, days) {
    var expires = "";
    if (days) {
        var date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/; SameSite=Strict";
}
function getCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}

// API key ni cookie dan olish va input ga yozish
window.addEventListener('load', function() {
    var savedKey = getCookie('yt_api_key');
    if (savedKey) {
        // Streamlit input larini topib qiymat berish
        setTimeout(function() {
            var inputs = document.querySelectorAll('input[type="password"]');
            inputs.forEach(function(inp) {
                if (inp.value === '' || inp.value.length < 5) {
                    var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value').set;
                    nativeInputValueSetter.call(inp, savedKey);
                    inp.dispatchEvent(new Event('input', { bubbles: true }));
                }
            });
        }, 1000);
    }
});
</script>
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
        json.dump(data, f, indent=2, ensure_ascii=False)

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
# UID — eng ishonchli usul: session_state + JSON saqlash
# ============================================================
def get_uid():
    """
    UID ni quyidagi usturvor tartibda olish:
    1. session_state da saqlangan (RAM) — tez
    2. query_params ?uid= — sahifa refresh da ham qoladi
    3. Yangi UUID yaratish + URL ga yozish
    """
    # 1. RAM da bor
    if "uid" in st.session_state and st.session_state["uid"]:
        return st.session_state["uid"]

    # 2. URL da bor
    uid_param = st.query_params.get("uid", "")
    if uid_param and len(uid_param) >= 10:
        st.session_state["uid"] = uid_param
        return uid_param

    # 3. Yangi yaratish
    new_uid = "u_" + uuid.uuid4().hex
    st.session_state["uid"] = new_uid
    st.query_params["uid"] = new_uid
    return new_uid

# ============================================================
# ТЎЛОВ URL
# ============================================================
def gen_order_id():
    return f"V777_{uuid.uuid4().hex[:10].upper()}"

def make_payme_url(order_id, amount):
    params = f"m={PAYME_MERCHANT_ID};ac.order_id={order_id};a={amount * 100}"
    return f"https://checkout.paycom.uz/{base64.b64encode(params.encode()).decode()}"

def make_click_url(order_id, amount):
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
        dt = datetime.strptime(re.sub(r'\.\d+Z','Z',iso),'%Y-%m-%dT%H:%M:%SZ')
        return f"{dt.day}-{M[dt.month]}, {dt.year}"
    except:
        return iso[:10]

REGIONS = {"US":"en","GB":"en","UZ":"uz","RU":"ru","TR":"tr"}

# ============================================================
# СЕССИЯ ИНИЦИАЛИЗАЦИЯ
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
    st.markdown("## 🎯 777 VIRAL ENGINE")
    st.divider()

    # ADMIN LOGIN
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

    # ОБУНА СТАТУСИ
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

    # API KEY
    saved_key = st.query_params.get("apikey", "")
    api_input = st.text_input("🔑 YouTube API Key:", value=saved_key, type="password",
                               help="Саҳифа янгиланса ҳам сақланади")
    if api_input and api_input != saved_key:
        st.query_params["apikey"] = api_input

    topic     = st.text_input("🔍 Мавзу:", "Survival")
    region    = st.selectbox("🌍 Давлат:", list(REGIONS.keys()))
    days_sel  = st.select_slider("📅 Давр (кун):", options=[7, 30, 90, 180, 365], value=30)
    min_views = st.selectbox("👁️ Min Кўришлар:", [0, 100000, 500000, 1000000],
                              format_func=lambda x: fmt(x) if x > 0 else "Ҳаммаси")
    min_outl  = st.slider("🔥 Min Outlier:", 1, 50, 15)

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

    # ТЎЛОВ БЛОКИ
    if (not st.session_state.authenticated and
            not is_subscribed(uid) and
            get_trial_remaining(uid) == 0):

        if not st.session_state.pending_order:
            st.session_state.pending_order = gen_order_id()
        oid   = st.session_state.pending_order
        p_url = make_payme_url(oid, SUBSCRIPTION_PRICE)
        c_url = make_click_url(oid, SUBSCRIPTION_PRICE)

        st.markdown(f"""
        <div class='subscription-box'>
            <div style='font-size:54px;'>🔒</div>
            <h2 style='color:#ffffff; margin:10px 0 6px;'>Синов муддати тугади</h2>
            <p style='color:#aaaaaa; font-size:14px; margin-bottom:18px;'>
                Сиз <b>{FREE_TRIAL_LIMIT} та текин қидирув</b>дан фойдаландингиз.<br>
                Давом этиш учун ойлик обуна сотиб олинг.
            </p>
            <div style='font-size:48px; font-weight:900; color:#FF0000; margin:16px 0;'>
                {SUBSCRIPTION_PRICE:,} сўм
            </div>
            <p style='color:#555; font-size:13px; margin-bottom:24px;'>
                📅 30 кун &nbsp;·&nbsp; ♾️ Чексиз қидирув &nbsp;·&nbsp; 🚀 Тўлиқ имкониятлар
            </p>
            <a href='{p_url}' target='_blank' class='pay-btn-payme'>💳 &nbsp;Payme орқали</a>
            <a href='{c_url}' target='_blank' class='pay-btn-click'>⚡ &nbsp;Click орқали</a>
            <br><br>
            <p style='color:#444; font-size:11px;'>Буюртма: <code style='color:#666;'>{oid}</code></p>
        </div>
        """, unsafe_allow_html=True)

        st.info("💡 Тўлов амалга оширилгандан сўнг қуйидаги тугмани босинг:")
        if st.button("✅ Тўловни тасдиқлаш"):
            submit_pending(uid, oid)
            st.success(f"✅ Сўров қабул қилинди! Admin тасдиқлагач обунангиз фаоллашади.\n\nID: `{oid}`")

    # ҚИДИРУВ
    if search_btn:
        current_key = st.query_params.get("apikey", "") or api_input
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
                                "Просмотр": views,
                                "Обуначи":  subs,
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
                            st.warning("⚠️ Охирги синов ишлатилди! Обуна сотиб олинг.")

            except Exception as e:
                st.error(f"⚠️ Хато: {e}")

    # НАТИЖАЛАР
    if st.session_state.last_results:
        df = pd.DataFrame(st.session_state.last_results).sort_values("Вираллик", ascending=False)
        avg_v = round(df["Вираллик"].mean(), 1) if not df.empty else 0

        st.markdown(f"""
        <div class='niche-score'>
            <h1 style='color:#FF0000;font-size:50px;margin:0;'>{avg_v}x</h1>
            <p style='color:#aaa;font-size:15px;margin:8px 0 0;'>VIRAL POTENTIAL SCORE</p>
            <p style='color:#555;font-size:12px;margin:4px 0 0;'>
                Ушбу мавзудаги видеолар обуначилар сонига нисбатан ўртача {avg_v} баравар кўпроқ кўрилмоқда!
            </p>
        </div>
        """, unsafe_allow_html=True)

        mode = st.radio("👀 Кўриниш:", ["Карточка", "Жадвал"], horizontal=True)

        if mode == "Карточка":
            for _, row in df.iterrows():
                c1, c2 = st.columns([1, 3])
                with c1: st.image(row['Расм'], use_container_width=True)
                with c2:
                    st.markdown(f"### [{row['Сарлавҳа']}]({row['Ҳавола']})")
                    st.caption(f"📺 {row['Канал']}  |  📅 {row['Юкланган']}")
                    m1, m2, m3 = st.columns(3)
                    for col, lbl, val in [
                        (m1,"Вираллик",f"{row['Вираллик']}x"),
                        (m2,"Просмотр", fmt(row['Просмотр'])),
                        (m3,"Обуначи",  fmt(row['Обуначи']))
                    ]:
                        col.markdown(f"<div class='metric-card'>"
                                     f"<div class='metric-label'>{lbl}</div>"
                                     f"<div class='metric-value'>{val}</div></div>",
                                     unsafe_allow_html=True)
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

    pending = {oid: d for oid, d in db.get("pending_orders", {}).items()
               if d["status"] == "pending"}
    st.markdown(f"### 📋 Тасдиқ кутаётган: **{len(pending)}** та тўлов")

    if pending:
        for oid, odata in pending.items():
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            c1.code(oid)
            c2.write(odata.get("created","")[:16])
            c3.write(f"`{odata['uid'][:12]}...`")
            if c4.button("✅", key=f"act_{oid}"):
                ok, _ = admin_activate(oid)
                st.success(f"✅ Фаоллашди!") if ok else st.error("Хато!")
                st.rerun()
    else:
        st.success("✅ Тасдиқ кутаётган тўлов йўқ.")

    st.divider()
    st.markdown("### ⚡ Қўлда Фаоллаштириш")
    c1, c2 = st.columns(2)
    m_uid  = c1.text_input("Foydalanuvchi UID:")
    _      = c2.text_input("Изоҳ:")
    if st.button("🔓 Обуна Фаоллаштириш"):
        if m_uid:
            activate_subscription(m_uid, f"MANUAL_{uuid.uuid4().hex[:8].upper()}")
            st.success(f"✅ {SUBSCRIPTION_DAYS} кунлик обуна фаоллашди!")
        else:
            st.error("UID киритинг!")

    st.divider()
    st.markdown("### 👥 Барча Фойдаланувчилар")
    all_users = {k: v for k, v in db.items() if k != "pending_orders"}
    if all_users:
        rows = [{
            "UID":      uh[:18]+"...",
            "Синов":    f"{ud.get('trial_used',0)}/{FREE_TRIAL_LIMIT}",
            "Обуна":    "✅" if ud.get("subscribed") else "❌",
            "Муддат":   ud.get("sub_until","—")[:10] if ud.get("sub_until") else "—",
            "Тўловлар": len(ud.get("orders",[]))
        } for uh, ud in all_users.items()]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Ҳали фойдаланувчилар йўқ.")
