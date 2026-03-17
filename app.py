# app.py
import streamlit as st
from components import _render_matches
from auth import require_auth, logout
from sheets import get_user_groups, get_group_members, get_wallet, get_available_balance
from sheets import get_all_matches, get_user_bets, get_match_bets
from sheets import place_bet, update_bet, cancel_bet
from datetime import datetime
import pytz

ISRAEL_TZ = pytz.timezone("Asia/Jerusalem")

st.set_page_config(
    page_title="🏆 Champions Bet",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS מלא — Champions League Premium Theme ───────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800;900&display=swap');

/* ── CSS Variables ────────────────────────────────────────────────────────── */
:root {
    --bg-base:        #040816;
    --bg-surface:     #0a1128;
    --bg-surface-2:   #0f1a38;
    --bg-elevated:    #162040;
    --blue-primary:   #2563eb;
    --blue-light:     #3b82f6;
    --blue-glow:      rgba(37, 99, 235, 0.35);
    --gold:           #f59e0b;
    --gold-light:     #fbbf24;
    --gold-glow:      rgba(245, 158, 11, 0.3);
    --green:          #22c55e;
    --green-glow:     rgba(34, 197, 94, 0.25);
    --red:            #ef4444;
    --red-glow:       rgba(239, 68, 68, 0.25);
    --text-primary:   #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted:     #64748b;
    --border-subtle:  rgba(148, 163, 184, 0.08);
    --border-glass:   rgba(148, 163, 184, 0.15);
    --radius-sm:      8px;
    --radius-md:      12px;
    --radius-lg:      16px;
    --radius-xl:      20px;
    --transition:     all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ── Global RTL + Font ─────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

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

/* ── Overflow מוחלט — מונע סרגל אופקי ───────────────────────────────────── */
html, body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stVerticalBlock"],
.main {
    overflow-x: hidden !important;
    max-width: 100vw !important;
}

/* ── RTL — רק על קונטיינרים ועל טקסט, לא על אייקונים ────────────────────── */
/* אסור לשים direction: rtl על * כי שובר Material Icons ligatures */
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
.stApp .stDateInput,
.stApp .stTimeInput,
.stApp .stTabs {
    direction: rtl !important;
}

/* ── Material Icons — שמור על LTR ─────────────────────────────────────────── */
.material-symbols-rounded,
.material-symbols-outlined,
.material-icons,
[data-testid="collapsedControl"] span,
[data-testid="collapsedControl"] button span,
button[kind="header"] span {
    direction: ltr !important;
    font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
    text-align: left !important;
}

/* ── Heebo רק על טקסט אמיתי ────────────────────────────────────────────────── */
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

/* ── יישור ימין לטקסט ──────────────────────────────────────────────────────── */
.stApp p,
.stApp label,
.stApp div.stMarkdown,
.stApp .stMarkdown p,
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

.stTextInput label,
.stNumberInput label,
.stSelectbox label,
.stRadio > label,
.stCheckbox label,
.stDateInput label,
.stTimeInput label,
.stTextArea label {
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
[data-testid="stExpander"] summary p { text-align: right !important; }

.stApp {
    overflow-x: hidden !important;
    background-image:
        radial-gradient(ellipse at 20% 50%, rgba(37,99,235,0.08) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 20%, rgba(245,158,11,0.05) 0%, transparent 50%);
    background-size: 100% 100%, 100% 100%;
}

/* מרכוז תוכן ראשי */
.main .block-container,
[data-testid="block-container"] {
    max-width: 860px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    padding-left: 16px !important;
    padding-right: 16px !important;
    width: 100% !important;
}

/* ── Sidebar ───────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #060d20 0%, #0a1128 50%, #060d20 100%) !important;
    border-right: 1px solid rgba(37, 99, 235, 0.3) !important;
}

[data-testid="stSidebar"] * {
    font-family: 'Heebo', sans-serif !important;
}

[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] .stSelectbox label {
    color: var(--text-secondary) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

/* ── Tabs ──────────────────────────────────────────────────────────────────── */
[data-baseweb="tab-list"] {
    background: var(--bg-surface) !important;
    border-radius: var(--radius-xl) !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid var(--border-glass) !important;
}

[data-baseweb="tab"] {
    background: transparent !important;
    border-radius: var(--radius-lg) !important;
    color: var(--text-secondary) !important;
    font-family: 'Heebo', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    padding: 10px 20px !important;
    transition: var(--transition) !important;
    border: none !important;
    min-height: 44px !important;
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

/* ── Buttons ───────────────────────────────────────────────────────────────── */
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
    letter-spacing: 0.3px !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
    box-shadow: 0 6px 24px var(--blue-glow) !important;
    transform: translateY(-1px) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
}

/* ── Inputs ────────────────────────────────────────────────────────────────── */
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

/* ── Select Boxes ──────────────────────────────────────────────────────────── */
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

/* ── Expanders ─────────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: rgba(10, 17, 40, 0.7) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: var(--radius-lg) !important;
    margin-bottom: 12px !important;
    overflow: hidden !important;
    transition: var(--transition) !important;
}

[data-testid="stExpander"]:hover {
    border-color: rgba(37, 99, 235, 0.4) !important;
    box-shadow: 0 4px 20px rgba(37, 99, 235, 0.1) !important;
}

[data-testid="stExpander"] summary {
    font-family: 'Heebo', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    color: var(--text-primary) !important;
    padding: 14px 18px !important;
    min-height: 52px !important;
    display: flex !important;
    align-items: center !important;
}

/* ── Metrics (Odds) ────────────────────────────────────────────────────────── */
[data-testid="stMetricValue"] {
    color: var(--gold) !important;
    font-family: 'Heebo', sans-serif !important;
    font-size: 1.8rem !important;
    font-weight: 800 !important;
    text-shadow: 0 0 20px var(--gold-glow) !important;
    line-height: 1.1 !important;
}

[data-testid="stMetricLabel"] {
    color: var(--text-secondary) !important;
    font-family: 'Heebo', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

/* ── Radio Buttons ─────────────────────────────────────────────────────────── */
.stRadio label {
    background: rgba(15, 26, 56, 0.6) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-family: 'Heebo', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 10px 18px !important;
    cursor: pointer !important;
    transition: var(--transition) !important;
    min-height: 44px !important;
    display: flex !important;
    align-items: center !important;
}

.stRadio label:hover {
    border-color: var(--blue-primary) !important;
    background: rgba(37, 99, 235, 0.15) !important;
}

/* ── Section Headers ───────────────────────────────────────────────────────── */
h3 {
    font-family: 'Heebo', sans-serif !important;
    font-size: 1.2rem !important;
    font-weight: 800 !important;
    color: var(--text-primary) !important;
    margin: 24px 0 16px 0 !important;
    padding-bottom: 10px !important;
    border-bottom: 2px solid transparent !important;
    background: linear-gradient(var(--bg-base), var(--bg-base)) padding-box,
                linear-gradient(90deg, var(--blue-primary), var(--gold)) border-box !important;
    display: inline-block !important;
    width: 100% !important;
}

/* ── Misc ──────────────────────────────────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid var(--border-subtle) !important;
    margin: 16px 0 !important;
}

.stCaption, [data-testid="stCaptionContainer"] {
    color: var(--text-muted) !important;
    font-family: 'Heebo', sans-serif !important;
    font-size: 0.8rem !important;
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

/* ══════════════════════════════════════════════════════════════════════════════
   CUSTOM COMPONENT CLASSES
   ══════════════════════════════════════════════════════════════════════════ */

/* Wallet Widget */
.cb-wallet {
    background: linear-gradient(135deg, rgba(10,17,40,0.95) 0%, rgba(15,26,56,0.9) 100%);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 0 0 1px rgba(37,99,235,0.25), inset 0 1px 0 rgba(255,255,255,0.05), 0 8px 32px rgba(0,0,0,0.4);
}

.cb-wallet::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 16px;
    padding: 1px;
    background: linear-gradient(135deg, rgba(37,99,235,0.5), rgba(245,158,11,0.3));
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events: none;
}

.cb-wallet-label {
    font-family: 'Heebo', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 8px;
}

.cb-wallet-total {
    font-family: 'Heebo', sans-serif;
    font-size: 2.2rem;
    font-weight: 900;
    color: #f59e0b;
    text-shadow: 0 0 24px rgba(245,158,11,0.5);
    line-height: 1.1;
    margin-bottom: 10px;
}

.cb-wallet-available {
    font-family: 'Heebo', sans-serif;
    font-size: 0.85rem;
    color: #94a3b8;
    padding-top: 10px;
    border-top: 1px solid rgba(148,163,184,0.12);
}

.cb-wallet-available b {
    color: #22c55e;
    font-weight: 700;
    font-size: 0.95rem;
}

/* Leaderboard Rows */
.cb-lb-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-radius: 12px;
    margin-bottom: 6px;
    background: rgba(10, 17, 40, 0.5);
    border: 1px solid rgba(148, 163, 184, 0.08);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    font-family: 'Heebo', sans-serif;
    min-height: 52px;
}

.cb-lb-row:hover {
    background: rgba(37, 99, 235, 0.08);
    border-color: rgba(37, 99, 235, 0.2);
    transform: translateX(-2px);
}

.cb-lb-me {
    background: rgba(37, 99, 235, 0.12) !important;
    border: 1px solid rgba(37, 99, 235, 0.45) !important;
    box-shadow: 0 0 16px rgba(37, 99, 235, 0.2);
}

.cb-lb-rank {
    font-size: 1.1rem;
    margin-left: 10px;
}

.cb-lb-name {
    font-size: 0.95rem;
    font-weight: 600;
    color: #f1f5f9;
}

.cb-lb-me .cb-lb-name {
    color: #93c5fd;
}

.cb-lb-badge {
    font-size: 0.7rem;
    background: rgba(37,99,235,0.3);
    color: #93c5fd;
    border-radius: 9999px;
    padding: 2px 8px;
    margin-left: 8px;
    font-weight: 600;
    vertical-align: middle;
}

.cb-lb-amount {
    font-size: 1rem;
    font-weight: 800;
    color: #f59e0b;
    text-shadow: 0 0 12px rgba(245,158,11,0.35);
}

/* My Bets Cards */
.cb-bet-card {
    background: rgba(10, 17, 40, 0.75);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-radius: 16px;
    padding: 18px 20px;
    margin-bottom: 12px;
    border: 1px solid rgba(148, 163, 184, 0.1);
    font-family: 'Heebo', sans-serif;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.cb-bet-win  { border-color: rgba(34, 197, 94, 0.45) !important; box-shadow: 0 0 20px rgba(34,197,94,0.1); }
.cb-bet-loss { border-color: rgba(239, 68, 68, 0.4) !important;  box-shadow: 0 0 20px rgba(239,68,68,0.08); }
.cb-bet-pending { border-color: rgba(37, 99, 235, 0.4) !important; box-shadow: 0 0 20px rgba(37,99,235,0.1); }

.cb-bet-teams {
    font-size: 1.05rem;
    font-weight: 700;
    color: #f1f5f9;
    margin-bottom: 4px;
}

.cb-bet-stage {
    font-size: 0.72rem;
    color: #64748b;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 14px;
}

.cb-bet-stats {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    margin-bottom: 12px;
}

.cb-bet-stat { display: flex; flex-direction: column; gap: 2px; }

.cb-bet-stat-label {
    font-size: 0.68rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 500;
}

.cb-bet-stat-value {
    font-size: 0.95rem;
    font-weight: 700;
    color: #f1f5f9;
}

.cb-bet-stat-value.gold { color: #f59e0b; }
.cb-bet-stat-value.blue { color: #60a5fa; }

.cb-bet-result {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 14px;
    border-radius: 9999px;
    font-size: 0.88rem;
    font-weight: 700;
}

.cb-bet-result.win  { background: rgba(34,197,94,0.15); color: #22c55e; border: 1px solid rgba(34,197,94,0.3); }
.cb-bet-result.loss { background: rgba(239,68,68,0.12); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); }

/* Group Bets List */
.cb-group-bets { display: flex; flex-direction: column; gap: 6px; margin-top: 10px; }

.cb-group-bet {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(15, 26, 56, 0.6);
    border: 1px solid rgba(148, 163, 184, 0.08);
    border-radius: 8px;
    padding: 8px 14px;
    font-family: 'Heebo', sans-serif;
    font-size: 0.875rem;
    transition: all 0.2s ease;
    flex-wrap: wrap;
    gap: 4px;
}

.cb-group-bet:hover { background: rgba(37,99,235,0.1); border-color: rgba(37,99,235,0.2); }
.cb-group-bet-user  { font-weight: 700; color: #f1f5f9; }
.cb-group-bet-choice { color: #94a3b8; flex: 1; text-align: center; }
.cb-group-bet-amount { font-weight: 700; color: #f59e0b; }

.cb-group-bet-result {
    font-size: 0.78rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 9999px;
    margin-right: 6px;
}

.cb-group-bet-result.win  { background: rgba(34,197,94,0.15); color: #22c55e; }
.cb-group-bet-result.loss { background: rgba(239,68,68,0.12); color: #ef4444; }

/* ══════════════════════════════════════════════════════════════════════════════
   MOBILE OVERRIDES  @media (max-width: 768px)
   ══════════════════════════════════════════════════════════════════════════ */
@media (max-width: 768px) {
    h3 { font-size: 1.05rem !important; }

    [data-testid="stMetricValue"] { font-size: 1.5rem !important; }

    [data-baseweb="tab"] {
        font-size: 0.8rem !important;
        padding: 8px 12px !important;
    }

    .cb-wallet { padding: 16px; }
    .cb-wallet-total { font-size: 1.9rem; }

    .cb-lb-row { padding: 10px 12px; }
    .cb-lb-amount { font-size: 0.9rem; }

    .cb-bet-card { padding: 14px 16px; }
    .cb-bet-stats { gap: 14px; }
    .cb-bet-stat-value { font-size: 0.875rem; }

    .stButton > button {
        min-height: 52px !important;
        font-size: 1rem !important;
    }

    .stTextInput input,
    .stNumberInput input {
        font-size: 16px !important;
    }

    .main .block-container,
    [data-testid="block-container"] {
        padding-left: 8px !important;
        padding-right: 8px !important;
        max-width: 100% !important;
    }

    .cb-group-bet-choice { text-align: right; flex: unset; }
}
</style>
""", unsafe_allow_html=True)

# ── Auth ───────────────────────────────────────────────────────────────────────
require_auth()

username = st.session_state["username"]
is_admin = st.session_state["is_admin"]

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### 👤 שלום, {username}")
    if is_admin:
        st.markdown("🔑 **אדמין**")

    # בחירת קבוצה
    user_groups = get_user_groups(username)

    if user_groups.empty:
        st.warning("אינך משויך לאף קבוצת הימור")
        if st.button("🚪 יציאה"):
            logout()
        st.stop()

    group_options = dict(zip(user_groups["group_name"], user_groups["group_id"]))
    selected_group_name = st.selectbox("🏠 קבוצת הימור", list(group_options.keys()))
    selected_group_id = group_options[selected_group_name]
    st.session_state["current_group"] = selected_group_id

    # ארנק
    wallets = get_wallet(username, selected_group_id)
    available = get_available_balance(username, selected_group_id)

    st.markdown("---")
    st.markdown(f"""
    <div class="cb-wallet">
        <div class="cb-wallet-label">&#9917; ארנק</div>
        <div class="cb-wallet-total">&#8362;{wallets['wallet_real']:.0f}</div>
        <div class="cb-wallet-available">זמין להימור: <b>&#8362;{available:.0f}</b></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    if is_admin:
        if st.button("⚙️ פאנל אדמין"):
            st.switch_page("pages/admin.py")

    if st.button("🚪 יציאה"):
        logout()

# ── תוכן ראשי ─────────────────────────────────────────────────────────────────
tab_matches, tab_mybets, tab_leaderboard = st.tabs(["⚽ משחקים", "🎯 ההימורים שלי", "🏅 טבלת מנהיגים"])

# ────────────────────────────────────────────────────────────────────────────────
# TAB 1 — משחקים
# ────────────────────────────────────────────────────────────────────────────────
with tab_matches:
    matches_df = get_all_matches()
    user_bets_df = get_user_bets(username, selected_group_id)

    if matches_df.empty:
        st.info("אין משחקים פעילים כרגע")
    else:
        # חלוקה לפי סטטוס
        open_matches = matches_df[matches_df["status"] == "open"]
        closed_matches = matches_df[matches_df["status"] == "closed"]
        finished_matches = matches_df[matches_df["status"] == "finished"]

        if not open_matches.empty:
            st.markdown("### 🟢 פתוח להימורים")
            _render_matches(open_matches, user_bets_df, username, selected_group_id, is_admin, editable=True)

        if not closed_matches.empty:
            st.markdown("### 🔴 סגור — ממתין לתוצאה")
            _render_matches(closed_matches, user_bets_df, username, selected_group_id, is_admin, editable=False)

        if not finished_matches.empty:
            st.markdown("### ✅ הסתיים")
            _render_matches(finished_matches, user_bets_df, username, selected_group_id, is_admin, editable=False)

# ────────────────────────────────────────────────────────────────────────────────
# TAB 2 — ההימורים שלי
# ────────────────────────────────────────────────────────────────────────────────
with tab_mybets:
    user_bets_df = get_user_bets(username, selected_group_id)
    matches_df = get_all_matches()

    if user_bets_df.empty:
        st.info("עדיין לא שמת הימורים בקבוצה הזו")
    else:
        for _, bet in user_bets_df.iterrows():
            match = matches_df[matches_df["match_id"] == bet["match_id"]]
            if match.empty:
                continue
            match = match.iloc[0]

            choice_label = {
                "a": match["team_a"],
                "draw": "תיקו",
                "b": match["team_b"]
            }.get(bet["choice"], bet["choice"])

            odds_map = {"a": match["odds_a"], "draw": match["odds_draw"], "b": match["odds_b"]}
            odds_val = odds_map.get(bet["choice"], "-")

            if bet["result"] == "win":
                card_state = "cb-bet-win"
                result_html = f'<div class="cb-bet-result win">&#9989; זכית &#8362;{float(bet["payout"]):.0f}</div>'
            elif bet["result"] == "loss":
                card_state = "cb-bet-loss"
                result_html = '<div class="cb-bet-result loss">&#10060; הפסדת</div>'
            else:
                card_state = "cb-bet-pending"
                result_html = ""

            st.markdown(f"""
            <div class="cb-bet-card {card_state}">
                <div class="cb-bet-teams">{match['team_a']} vs {match['team_b']}</div>
                <div class="cb-bet-stage">{match['stage']}</div>
                <div class="cb-bet-stats">
                    <div class="cb-bet-stat">
                        <span class="cb-bet-stat-label">בחירה</span>
                        <span class="cb-bet-stat-value blue">{choice_label}</span>
                    </div>
                    <div class="cb-bet-stat">
                        <span class="cb-bet-stat-label">יחס</span>
                        <span class="cb-bet-stat-value gold">&#215;{odds_val}</span>
                    </div>
                    <div class="cb-bet-stat">
                        <span class="cb-bet-stat-label">סכום</span>
                        <span class="cb-bet-stat-value">&#8362;{float(bet['amount']):.0f}</span>
                    </div>
                </div>
                {result_html}
            </div>
            """, unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────────────────
# TAB 3 — לוח מנהיגים
# ────────────────────────────────────────────────────────────────────────────────
with tab_leaderboard:
    if st.button("🔄 רענן טבלה"):
        st.cache_data.clear()
        st.rerun()
    members_df = get_group_members(selected_group_id)
    if members_df.empty:
        st.info("אין חברים בקבוצה")
    else:
        # מיון לפי wallet_visible (מה שאחרים רואים)
        members_df = members_df.sort_values("wallet_visible", ascending=False).reset_index(drop=True)
        st.markdown(f"### 🏅 {selected_group_name}")

        for i, row in members_df.iterrows():
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}."
            is_me = row["username"] == username
            me_class = "cb-lb-me" if is_me else ""
            me_badge = '<span class="cb-lb-badge">אני</span>' if is_me else ""

            st.markdown(f"""
            <div class="cb-lb-row {me_class}">
                <span>
                    <span class="cb-lb-rank">{medal}</span>
                    <span class="cb-lb-name">{me_badge}{row['username']}</span>
                </span>
                <span class="cb-lb-amount">&#8362;{float(row['wallet_visible']):.0f}</span>
            </div>
            """, unsafe_allow_html=True)


