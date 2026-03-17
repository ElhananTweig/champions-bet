# pages/admin.py
import streamlit as st
from auth import require_admin
from sheets import (
    get_all_groups, get_user_groups, create_group,
    add_member_to_group, get_group_members,
    get_all_matches, add_match, set_match_result,
    get_wallet, admin_adjust_wallet,
    sheet_to_df, get_sheet, create_user
)
from auth import hash_password
import pytz
from datetime import datetime

ISRAEL_TZ = pytz.timezone("Asia/Jerusalem")

st.set_page_config(page_title="⚙️ פאנל אדמין", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800;900&display=swap');

:root {
    --bg-base:        #040816;
    --bg-surface:     #0a1128;
    --bg-surface-2:   #0f1a38;
    --bg-elevated:    #162040;
    --blue-primary:   #2563eb;
    --blue-light:     #3b82f6;
    --blue-glow:      rgba(37, 99, 235, 0.35);
    --gold:           #f59e0b;
    --green:          #22c55e;
    --red:            #ef4444;
    --text-primary:   #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted:     #64748b;
    --border-glass:   rgba(148, 163, 184, 0.15);
    --border-subtle:  rgba(148, 163, 184, 0.08);
    --radius-md:      12px;
    --radius-lg:      16px;
    --transition:     all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

html, body {
    overflow-x: hidden !important;
    max-width: 100vw !important;
}

html, body, .stApp {
    direction: rtl !important;
    font-family: 'Heebo', 'Segoe UI', sans-serif !important;
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
}

/* Overflow */
html, body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stVerticalBlock"],
.main {
    overflow-x: hidden !important;
    max-width: 100vw !important;
}

/* RTL על קונטיינרים בלבד */
.stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stForm"],
.stApp [data-testid="stVerticalBlock"],
.stApp [data-testid="stHorizontalBlock"],
.stApp [data-testid="stSidebarContent"],
.stApp .element-container,
.stApp .stMarkdown,
.stApp .stTextInput,
.stApp .stNumberInput,
.stApp .stSelectbox,
.stApp .stRadio,
.stApp .stCheckbox,
.stApp .stTabs {
    direction: rtl !important;
}

/* Material Icons — LTR בלבד */
.material-symbols-rounded,
.material-symbols-outlined,
.material-icons,
[data-testid="collapsedControl"] span,
button[kind="header"] span {
    direction: ltr !important;
    font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
    text-align: left !important;
}

/* Heebo רק על טקסט */
.stApp p,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
.stApp label,
.stApp input,
.stApp textarea,
.stApp select,
.stApp [data-testid="stMarkdownContainer"],
.stApp [data-baseweb="tab"],
.stApp [data-baseweb="menu"] li {
    font-family: 'Heebo', 'Segoe UI', sans-serif !important;
}

/* יישור ימין */
.stApp p,
.stApp label,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] ul,
[data-testid="stMarkdownContainer"] li {
    text-align: right !important;
}

.stApp h1, .stApp h2, .stApp h3,
.stApp h4, .stApp h5, .stApp h6 {
    text-align: right !important;
}

.stTextInput label, .stNumberInput label,
.stSelectbox label, .stRadio > label,
.stCheckbox label, .stDateInput label, .stTimeInput label {
    text-align: right !important;
    width: 100% !important;
    display: block !important;
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
    text-align: right !important;
    direction: rtl !important;
}

[data-testid="stMetric"] { text-align: center !important; }
[data-testid="stCaptionContainer"] p { text-align: right !important; }

.stApp {
    overflow-x: hidden !important;
    background-image:
        radial-gradient(ellipse at 20% 50%, rgba(37,99,235,0.07) 0%, transparent 55%);
    background-size: 100% 100%;
}

.main .block-container,
[data-testid="block-container"] {
    max-width: 1100px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    padding-left: 16px !important;
    padding-right: 16px !important;
    width: 100% !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #060d20 0%, #0a1128 50%, #060d20 100%) !important;
    border-right: 1px solid rgba(37, 99, 235, 0.3) !important;
}

[data-testid="stSidebar"] * {
    font-family: 'Heebo', sans-serif !important;
}

.stTextInput input,
.stNumberInput input {
    background: rgba(15, 26, 56, 0.85) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-primary) !important;
    font-family: 'Heebo', sans-serif !important;
    font-size: 16px !important;
    padding: 12px 16px !important;
    min-height: 48px !important;
    text-align: right !important;
    transition: var(--transition) !important;
}

.stTextInput input:focus,
.stNumberInput input:focus {
    border-color: var(--blue-primary) !important;
    box-shadow: 0 0 0 3px var(--blue-glow) !important;
    outline: none !important;
}

.stTextInput label,
.stNumberInput label {
    color: var(--text-secondary) !important;
    font-family: 'Heebo', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}

[data-baseweb="select"] > div {
    background: rgba(15, 26, 56, 0.85) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-primary) !important;
    font-family: 'Heebo', sans-serif !important;
    font-size: 16px !important;
    min-height: 48px !important;
    transition: var(--transition) !important;
}

[data-baseweb="select"] > div:hover {
    border-color: var(--blue-primary) !important;
}

[data-baseweb="popover"] {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: 0 16px 48px rgba(0,0,0,0.5) !important;
}

[data-baseweb="menu"] li {
    color: var(--text-primary) !important;
    font-family: 'Heebo', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 10px 16px !important;
}

[data-baseweb="menu"] li:hover {
    background: rgba(37, 99, 235, 0.2) !important;
}

[data-baseweb="tab-list"] {
    background: var(--bg-surface) !important;
    border-radius: 20px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid var(--border-glass) !important;
}

[data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 16px !important;
    color: var(--text-secondary) !important;
    font-family: 'Heebo', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    padding: 10px 20px !important;
    min-height: 44px !important;
    transition: var(--transition) !important;
    border: none !important;
}

[data-baseweb="tab"]:hover {
    color: var(--text-primary) !important;
    background: rgba(37, 99, 235, 0.15) !important;
}

[aria-selected="true"][data-baseweb="tab"] {
    background: linear-gradient(135deg, var(--blue-primary), #1d4ed8) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 15px var(--blue-glow) !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--blue-primary) 0%, #1d4ed8 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
    font-family: 'Heebo', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    min-height: 48px !important;
    padding: 12px 24px !important;
    width: 100% !important;
    transition: var(--transition) !important;
    cursor: pointer !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
    box-shadow: 0 6px 24px var(--blue-glow) !important;
    transform: translateY(-1px) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
}

.stRadio label {
    background: rgba(15, 26, 56, 0.6) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    font-family: 'Heebo', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 10px 18px !important;
    cursor: pointer !important;
    transition: var(--transition) !important;
    min-height: 44px !important;
}

.stRadio label:hover {
    border-color: var(--blue-primary) !important;
    background: rgba(37, 99, 235, 0.15) !important;
}

h1 {
    font-family: 'Heebo', sans-serif !important;
    font-weight: 900 !important;
    color: var(--text-primary) !important;
    font-size: 1.8rem !important;
}

h3 {
    font-family: 'Heebo', sans-serif !important;
    font-size: 1.15rem !important;
    font-weight: 800 !important;
    color: var(--text-primary) !important;
    margin: 20px 0 14px 0 !important;
    padding-bottom: 8px !important;
    border-bottom: 2px solid transparent !important;
    background: linear-gradient(var(--bg-base), var(--bg-base)) padding-box,
                linear-gradient(90deg, var(--blue-primary), var(--gold)) border-box !important;
    display: inline-block !important;
    width: 100% !important;
}

.admin-card {
    background: rgba(10, 17, 40, 0.75);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--border-glass);
    border-radius: var(--radius-lg);
    padding: 20px;
    margin-bottom: 14px;
    font-family: 'Heebo', sans-serif;
    transition: var(--transition);
}

.admin-card:hover {
    border-color: rgba(37, 99, 235, 0.35);
    box-shadow: 0 4px 20px rgba(37, 99, 235, 0.1);
}

hr {
    border: none !important;
    border-top: 1px solid var(--border-subtle) !important;
    margin: 16px 0 !important;
}

.stCaption, [data-testid="stCaptionContainer"] {
    color: var(--text-muted) !important;
    font-family: 'Heebo', sans-serif !important;
}

[data-testid="stAlert"] {
    border-radius: var(--radius-md) !important;
    font-family: 'Heebo', sans-serif !important;
}

[data-testid="stDataFrame"] {
    border-radius: var(--radius-md) !important;
    overflow: hidden !important;
    border: 1px solid var(--border-glass) !important;
}

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg-surface); }
::-webkit-scrollbar-thumb { background: rgba(37,99,235,0.4); border-radius: 4px; }

@media (max-width: 768px) {
    .main .block-container {
        padding-left: 8px !important;
        padding-right: 8px !important;
        max-width: 100% !important;
    }
    .stButton > button { min-height: 52px !important; }
    h3 { font-size: 1rem !important; }
    h1 { font-size: 1.4rem !important; }
    [data-baseweb="tab"] {
        font-size: 0.8rem !important;
        padding: 8px 12px !important;
    }
}
</style>
""", unsafe_allow_html=True)

require_admin()

st.title("⚙️ פאנל ניהול — Champions Bet")

tabs = st.tabs([
    "👥 משתמשים וקבוצות",
    "⚽ ניהול משחקים",
    "💰 ניהול ארנקות",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — משתמשים וקבוצות
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:

    col_left, col_right = st.columns(2)

    # ── יצירת משתמש חדש ──────────────────────────────────────────────────────
    with col_left:
        st.markdown("### ➕ יצירת משתמש חדש")
        with st.form("create_user_form"):
            new_username = st.text_input("שם משתמש")
            new_password = st.text_input("סיסמה", type="password")
            new_is_admin = st.checkbox("הרשאות אדמין")
            if st.form_submit_button("צור משתמש"):
                if not new_username or not new_password:
                    st.error("נא למלא את כל השדות")
                else:
                    from sheets import get_user
                    if get_user(new_username):
                        st.error("שם משתמש כבר קיים")
                    else:
                        hashed = hash_password(new_password)
                        create_user(new_username, hashed, new_is_admin)
                        st.success(f"משתמש {new_username} נוצר בהצלחה!")
                        st.cache_data.clear()
                        st.rerun()

        # רשימת משתמשים קיימים
        st.markdown("### 👤 משתמשים קיימים")
        users_df = sheet_to_df("users")
        if not users_df.empty:
            for _, u in users_df.iterrows():
                admin_tag = " 🔑" if str(u.get("is_admin", "")).lower() == "true" else ""
                st.markdown(f"- **{u['username']}**{admin_tag}")
        else:
            st.info("אין משתמשים עדיין")

    # ── יצירת קבוצה + הוספת חברים ───────────────────────────────────────────
    with col_right:
        st.markdown("### 🏠 יצירת קבוצת הימור")
        with st.form("create_group_form"):
            group_name = st.text_input("שם הקבוצה")
            if st.form_submit_button("צור קבוצה"):
                if not group_name:
                    st.error("נא להזין שם קבוצה")
                else:
                    admin_username = st.session_state["username"]
                    gid = create_group(group_name, admin_username)
                    # הוסף את האדמין עצמו כחבר
                    add_member_to_group(gid, admin_username)
                    st.success(f"קבוצה '{group_name}' נוצרה! ID: {gid}")
                    st.cache_data.clear()
                    st.rerun()

        st.markdown("### 👥 הוספת חבר לקבוצה")
        groups_df = get_all_groups()
        if groups_df.empty:
            st.info("צור קבוצה תחילה")
        else:
            with st.form("add_member_form"):
                group_options = dict(zip(groups_df["group_name"], groups_df["group_id"]))
                selected_group = st.selectbox("קבוצה", list(group_options.keys()))
                users_df = sheet_to_df("users")
                if not users_df.empty:
                    user_list = users_df["username"].tolist()
                    member_to_add = st.selectbox("משתמש", user_list)
                    initial_wallet = st.number_input("ארנק התחלתי (₪)", value=1000, min_value=0)
                    if st.form_submit_button("הוסף לקבוצה"):
                        gid = group_options[selected_group]
                        ok = add_member_to_group(gid, member_to_add, float(initial_wallet))
                        if ok:
                            st.success(f"{member_to_add} נוסף לקבוצה '{selected_group}'")
                        else:
                            st.warning(f"{member_to_add} כבר חבר בקבוצה זו")
                        st.cache_data.clear()
                        st.rerun()

        st.markdown("### 📋 חברי קבוצה")
        if not groups_df.empty:
            view_group = st.selectbox(
                "הצג חברי קבוצה",
                list(group_options.keys()),
                key="view_group"
            )
            members = get_group_members(group_options[view_group])
            if not members.empty:
                for _, m in members.iterrows():
                    st.markdown(f"- **{m['username']}** — ₪{float(m['wallet_real']):.0f}")
            else:
                st.info("אין חברים בקבוצה זו")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ניהול משחקים
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### ➕ הוספת משחק חדש")
        with st.form("add_match_form"):
            stage = st.selectbox("שלב", [
                "שמינית גמר", "רבע גמר", "חצי גמר", "גמר"
            ])
            team_a = st.text_input("קבוצה א'")
            team_b = st.text_input("קבוצה ב'")

            st.markdown("**יחסים:**")
            c1, c2, c3 = st.columns(3)
            odds_a = c1.number_input("ניצחון א'", min_value=1.0, value=2.0, step=0.05)
            odds_draw = c2.number_input("תיקו", min_value=1.0, value=3.0, step=0.05)
            odds_b = c3.number_input("ניצחון ב'", min_value=1.0, value=3.5, step=0.05)

            match_date = st.date_input("תאריך המשחק")
            match_time = st.time_input("שעת המשחק")

            if st.form_submit_button("➕ הוסף משחק"):
                if not team_a or not team_b:
                    st.error("נא להזין שמות קבוצות")
                else:
                    dt = datetime.combine(match_date, match_time)
                    dt_str = ISRAEL_TZ.localize(dt).isoformat()
                    mid = add_match(stage, team_a, team_b, odds_a, odds_draw, odds_b, dt_str)
                    st.success(f"משחק נוסף! ID: {mid}")
                    st.cache_data.clear()
                    st.rerun()

    with col_right:
        st.markdown("### 🏁 הזנת תוצאה")
        matches_df = get_all_matches()

        # רק משחקים סגורים שעדיין אין להם תוצאה
        if not matches_df.empty:
            closed = matches_df[matches_df["status"] == "closed"]
            if closed.empty:
                st.info("אין משחקים שממתינים לתוצאה")
            else:
                with st.form("result_form"):
                    match_labels = {
                        f"{r['team_a']} vs {r['team_b']} ({r['stage']})": r["match_id"]
                        for _, r in closed.iterrows()
                    }
                    selected_match_label = st.selectbox("משחק", list(match_labels.keys()))
                    selected_match_id = match_labels[selected_match_label]

                    # מצא את שמות הקבוצות
                    match_row = closed[closed["match_id"] == selected_match_id].iloc[0]
                    winner_options = {
                        match_row["team_a"]: "a",
                        "תיקו": "draw",
                        match_row["team_b"]: "b"
                    }
                    winner_label = st.radio("תוצאה", list(winner_options.keys()), horizontal=True)

                    if st.form_submit_button("✅ אשר תוצאה וחשב זכיות"):
                        winner_key = winner_options[winner_label]
                        set_match_result(selected_match_id, winner_key)
                        st.success(f"תוצאה נרשמה! זכיות חושבו אוטומטית ✅")
                        st.cache_data.clear()
                        st.rerun()
        else:
            st.info("אין משחקים במערכת")

        # ── עריכת יחסים למשחק פתוח ──────────────────────────────────────────
        st.markdown("### ✏️ עריכת יחסים")
        if not matches_df.empty:
            open_matches = matches_df[matches_df["status"] == "open"]
            if not open_matches.empty:
                with st.form("edit_odds_form"):
                    edit_labels = {
                        f"{r['team_a']} vs {r['team_b']}": r["match_id"]
                        for _, r in open_matches.iterrows()
                    }
                    edit_label = st.selectbox("משחק", list(edit_labels.keys()))
                    edit_id = edit_labels[edit_label]
                    edit_row = open_matches[open_matches["match_id"] == edit_id].iloc[0]

                    c1, c2, c3 = st.columns(3)
                    new_odds_a = c1.number_input("ניצחון א'", value=float(edit_row["odds_a"]), step=0.05)
                    new_odds_draw = c2.number_input("תיקו", value=float(edit_row["odds_draw"]), step=0.05)
                    new_odds_b = c3.number_input("ניצחון ב'", value=float(edit_row["odds_b"]), step=0.05)

                    if st.form_submit_button("💾 עדכן יחסים"):
                        ws = get_sheet("matches")
                        all_m = sheet_to_df("matches")
                        idx = all_m[all_m["match_id"] == edit_id].index[0] + 2
                        ws.update_cell(idx, 5, new_odds_a)
                        ws.update_cell(idx, 6, new_odds_draw)
                        ws.update_cell(idx, 7, new_odds_b)
                        st.success("יחסים עודכנו!")
                        st.cache_data.clear()
                        st.rerun()
            else:
                st.info("אין משחקים פתוחים לעריכה")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ניהול ארנקות
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("### 💰 הוספה/הפחתה ידנית מארנק")

    groups_df = get_all_groups()
    if groups_df.empty:
        st.info("אין קבוצות במערכת")
    else:
        with st.form("wallet_adjust_form"):
            group_options = dict(zip(groups_df["group_name"], groups_df["group_id"]))
            adj_group_name = st.selectbox("קבוצה", list(group_options.keys()))
            adj_group_id = group_options[adj_group_name]

            members_df = get_group_members(adj_group_id)
            if members_df.empty:
                st.warning("אין חברים בקבוצה זו")
            else:
                member_list = members_df["username"].tolist()
                adj_user = st.selectbox("שחקן", member_list)

                # הצג ארנק נוכחי
                wallets = get_wallet(adj_user, adj_group_id)
                st.caption(f"ארנק נוכחי: ₪{float(wallets['wallet_real']):.0f}")

                adj_amount = st.number_input(
                    "סכום (חיובי = הוספה, שלילי = הפחתה)",
                    value=0,
                    step=50
                )
                adj_reason = st.text_input("סיבה (לתיעוד)")

                if st.form_submit_button("✅ בצע פעולה"):
                    if adj_amount == 0:
                        st.warning("סכום הוא 0, לא בוצעה פעולה")
                    else:
                        admin_adjust_wallet(adj_group_id, adj_user, float(adj_amount), adj_reason)
                        direction = "נוסף" if adj_amount > 0 else "הופחת"
                        st.success(f"₪{abs(adj_amount)} {direction} מארנקו של {adj_user}")
                        st.cache_data.clear()
                        st.rerun()

        # ── טבלת ארנקות לפי קבוצה ────────────────────────────────────────────
        st.markdown("### 📊 מצב ארנקות לפי קבוצה")
        view_group_name = st.selectbox("הצג קבוצה", list(group_options.keys()), key="wallet_view")
        view_group_id = group_options[view_group_name]
        members_view = get_group_members(view_group_id)

        if not members_view.empty:
            members_view = members_view.sort_values("wallet_real", ascending=False)
            members_view["wallet_real"] = members_view["wallet_real"].apply(lambda x: f"₪{float(x):.0f}")
            members_view["wallet_visible"] = members_view["wallet_visible"].apply(lambda x: f"₪{float(x):.0f}")
            st.dataframe(
                members_view[["username", "wallet_real", "wallet_visible"]].rename(columns={
                    "username": "שם משתמש",
                    "wallet_real": "ארנק אמיתי",
                    "wallet_visible": "ארנק גלוי לאחרים"
                }),
                use_container_width=True,
                hide_index=True
            )