# sheets.py
import gspread
import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import uuid


ISRAEL_TZ = pytz.timezone("Asia/Jerusalem")

@st.cache_resource
def get_client():
    import json
    import tempfile
    import os

    creds_dict = dict(st.secrets["gcp_service_account"])

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(creds_dict, f)
        temp_path = f.name

    try:
        gc = gspread.service_account(filename=temp_path)
    finally:
        os.unlink(temp_path)

    return gc

def get_sheet(sheet_name: str):
    client = get_client()
    spreadsheet = client.open(st.secrets["sheets"]["spreadsheet_name"])
    return spreadsheet.worksheet(sheet_name)

@st.cache_data(ttl=30)
def sheet_to_df(sheet_name: str) -> pd.DataFrame:
    ws = get_sheet(sheet_name)
    data = ws.get_all_records()
    return pd.DataFrame(data) if data else pd.DataFrame()

# ─── USERS ────────────────────────────────────────────────────────────────────

def get_user(username: str) -> dict | None:
    df = sheet_to_df("users")
    if df.empty:
        return None
    row = df[df["username"] == username]
    return row.iloc[0].to_dict() if not row.empty else None

def create_user(username: str, hashed_password: str, is_admin: bool = False):
    ws = get_sheet("users")
    ws.append_row([username, hashed_password, str(is_admin)])

# ─── GROUPS ───────────────────────────────────────────────────────────────────

def get_all_groups() -> pd.DataFrame:
    return sheet_to_df("groups")

def get_user_groups(username: str) -> pd.DataFrame:
    members_df = sheet_to_df("group_members")
    if members_df.empty:
        return pd.DataFrame()
    user_groups = members_df[members_df["username"] == username]["group_id"].tolist()
    groups_df = sheet_to_df("groups")
    if groups_df.empty:
        return pd.DataFrame()
    return groups_df[groups_df["group_id"].isin(user_groups)]

def create_group(group_name: str, created_by: str) -> str:
    group_id = str(uuid.uuid4())[:8]
    ws = get_sheet("groups")
    ws.append_row([group_id, group_name, created_by])
    return group_id

def add_member_to_group(group_id: str, username: str, initial_wallet: float = 1000.0):
    # בדוק שלא כבר חבר
    df = sheet_to_df("group_members")
    if not df.empty:
        exists = df[(df["group_id"] == group_id) & (df["username"] == username)]
        if not exists.empty:
            return False
    ws = get_sheet("group_members")
    ws.append_row([group_id, username, initial_wallet, initial_wallet])
    return True

def get_group_members(group_id: str) -> pd.DataFrame:
    df = sheet_to_df("group_members")
    if df.empty:
        return pd.DataFrame()
    return df[df["group_id"] == group_id]

# ─── WALLET ───────────────────────────────────────────────────────────────────

def get_wallet(username: str, group_id: str) -> dict:
    df = sheet_to_df("group_members")
    if df.empty:
        return {"wallet_real": 0, "wallet_visible": 0}
    row = df[(df["group_id"] == group_id) & (df["username"] == username)]
    if row.empty:
        return {"wallet_real": 0, "wallet_visible": 0}
    return row.iloc[0][["wallet_real", "wallet_visible"]].to_dict()

def _update_member_wallet(group_id: str, username: str, wallet_real: float, wallet_visible: float):
    ws = get_sheet("group_members")
    df = sheet_to_df("group_members")
    # מציאת השורה הנכונה (שורה 1 היא headers, אז +2)
    mask = (df["group_id"] == group_id) & (df["username"] == username)
    idx = df[mask].index[0] + 2
    ws.update_cell(idx, 3, round(wallet_real, 2))
    ws.update_cell(idx, 4, round(wallet_visible, 2))

def _sync_visible_wallets_for_match(match_id: str, matches_df=None):
    """
    מחשב מחדש wallet_visible לכל מי שהימר על המשחק שנסגר.
    wallet_visible = wallet_real + סכום הימורים על משחקים שעדיין פתוחים
    """
    bets_df = sheet_to_df("bets")
    if bets_df.empty:
        return

    match_bets = bets_df[bets_df["match_id"] == match_id]
    if matches_df is None:
        matches_df = get_all_matches()

    for _, bet in match_bets.iterrows():
        username = bet["username"]
        group_id = bet["group_id"]

        wallets = get_wallet(username, group_id)
        real = float(wallets["wallet_real"])

        # חשב כמה כסף עדיין נעול על משחקים פתוחים
        user_bets = bets_df[
            (bets_df["username"] == username) &
            (bets_df["group_id"] == group_id) &
            (bets_df["result"] == "")
        ]

        still_hidden = 0.0
        for _, ub in user_bets.iterrows():
            m = matches_df[matches_df["match_id"] == ub["match_id"]]
            if not m.empty and m.iloc[0]["status"] == "open":
                still_hidden += float(ub["amount"])

        # visible = real + מה שעדיין מוסתר (הימורים על משחקים פתוחים)
        new_visible = round(real + still_hidden, 2)
        _update_member_wallet(group_id, username, real, new_visible)

def admin_adjust_wallet(group_id: str, username: str, amount: float, reason: str):
    """האדמין מוסיף/מחסיר כסף ידנית"""
    wallets = get_wallet(username, group_id)
    new_real = wallets["wallet_real"] + amount
    new_visible = wallets["wallet_visible"] + amount
    _update_member_wallet(group_id, username, new_real, new_visible)
    # לוג
    ws = get_sheet("wallet_log")
    now = datetime.now(ISRAEL_TZ).strftime("%Y-%m-%d %H:%M:%S")
    ws.append_row([str(uuid.uuid4())[:8], username, group_id, amount, reason, now])

# ─── MATCHES ──────────────────────────────────────────────────────────────────

def get_all_matches() -> pd.DataFrame:
    df = sheet_to_df("matches")
    if df.empty:
        return df
    # עדכון סטטוס אוטומטי לפי שעה
    now = datetime.now(ISRAEL_TZ)
    for i, row in df.iterrows():
        try:
            match_time = datetime.fromisoformat(str(row["match_datetime"]))
            if match_time.tzinfo is None:
                match_time = ISRAEL_TZ.localize(match_time)
            if row["status"] == "open" and now >= match_time:
                df.at[i, "status"] = "closed"
                # עדכן גם בשיטס
                _update_match_status(row["match_id"], "closed")
                # עדכן wallet_visible לכל מי שהימר על המשחק הזה (מעביר df כדי למנוע recursion)
                _sync_visible_wallets_for_match(row["match_id"], matches_df=df)
        except Exception:
            pass
    return df

def _update_match_status(match_id: str, status: str):
    ws = get_sheet("matches")
    df = sheet_to_df("matches")
    mask = df["match_id"] == match_id
    if mask.any():
        idx = df[mask].index[0] + 2
        # עמודה 9 היא status
        ws.update_cell(idx, 9, status)

def add_match(stage: str, team_a: str, team_b: str,
              odds_a: float, odds_draw: float, odds_b: float,
              match_datetime: str):
    match_id = str(uuid.uuid4())[:8]
    ws = get_sheet("matches")
    ws.append_row([
        match_id, stage, team_a, team_b,
        odds_a, odds_draw, odds_b,
        match_datetime, "open", ""
    ])
    return match_id

def set_match_result(match_id: str, winner: str):
    """winner: 'a' | 'draw' | 'b'"""
    ws = get_sheet("matches")
    df = sheet_to_df("matches")
    mask = df["match_id"] == match_id
    if not mask.any():
        return
    idx = df[mask].index[0] + 2
    ws.update_cell(idx, 9, "finished")   # status
    ws.update_cell(idx, 10, winner)      # winner
    # חישוב זכיות — ניקוי cache אחרי הכתיבה כדי ש-_sync יקרא ערכים מעודכנים
    _process_payouts(match_id, winner)
    st.cache_data.clear()
    _sync_visible_wallets_for_match(match_id)

def _process_payouts(match_id: str, winner: str):
    matches_df = sheet_to_df("matches")
    match = matches_df[matches_df["match_id"] == match_id].iloc[0]
    odds_map = {"a": float(match["odds_a"]), "draw": float(match["odds_draw"]), "b": float(match["odds_b"])}
    winning_odds = odds_map[winner]

    bets_df = sheet_to_df("bets")
    if bets_df.empty:
        return
    match_bets = bets_df[bets_df["match_id"] == match_id]

    ws_bets = get_sheet("bets")
    bets_all = sheet_to_df("bets")

    for _, bet in match_bets.iterrows():
        if bet["result"] != "":  # כבר עובד
            continue
        won = bet["choice"] == winner
        payout = round(float(bet["amount"]) * winning_odds, 2) if won else 0.0
        result_str = "win" if won else "loss"

        # עדכן שורת הימור
        b_mask = bets_all["bet_id"] == bet["bet_id"]
        b_idx = bets_all[b_mask].index[0] + 2
        ws_bets.update_cell(b_idx, 7, result_str)   # result
        ws_bets.update_cell(b_idx, 8, payout)        # payout

        # עדכן ארנק — wallet_real: מחזיר את ה-payout (אם הפסיד, 0)
        wallets = get_wallet(bet["username"], bet["group_id"])
        new_real = wallets["wallet_real"] + payout
        # wallet_visible מתעדכן עכשיו גם כן (המשחק נגמר, הכל גלוי)
        new_visible = new_real
        _update_member_wallet(bet["group_id"], bet["username"], new_real, new_visible)

# ─── BETS ─────────────────────────────────────────────────────────────────────

def get_user_bets(username: str, group_id: str) -> pd.DataFrame:
    df = sheet_to_df("bets")
    if df.empty:
        return pd.DataFrame()
    return df[(df["username"] == username) & (df["group_id"] == group_id)]

def get_match_bets(match_id: str, group_id: str) -> pd.DataFrame:
    df = sheet_to_df("bets")
    if df.empty:
        return pd.DataFrame()
    return df[(df["match_id"] == match_id) & (df["group_id"] == group_id)]

def get_available_balance(username: str, group_id: str) -> float:
    """כסף זמין = wallet_real (הכסף כבר יורד ברגע ההימור)"""
    wallets = get_wallet(username, group_id)
    return round(float(wallets["wallet_real"]), 2)

def place_bet(username: str, group_id: str, match_id: str,
              choice: str, amount: float) -> tuple[bool, str]:
    """מחזיר (success, message)"""
    # בדוק שהמשחק פתוח
    matches_df = get_all_matches()
    match = matches_df[matches_df["match_id"] == match_id]
    if match.empty or match.iloc[0]["status"] != "open":
        return False, "המשחק סגור להימורים"

    # בדוק שאין כבר הימור על המשחק הזה
    bets_df = sheet_to_df("bets")
    if not bets_df.empty:
        existing = bets_df[
            (bets_df["username"] == username) &
            (bets_df["group_id"] == group_id) &
            (bets_df["match_id"] == match_id)
        ]
        if not existing.empty:
            return False, "כבר הימרת על המשחק הזה — השתמש בעריכת הימור"

    # בדוק יתרה זמינה
    available = get_available_balance(username, group_id)
    if amount > available:
        return False, f"אין מספיק כסף. יתרה זמינה: ₪{available}"

    # כתוב הימור
    bet_id = str(uuid.uuid4())[:8]
    now = datetime.now(ISRAEL_TZ).strftime("%Y-%m-%d %H:%M:%S")
    ws = get_sheet("bets")
    ws.append_row([bet_id, username, group_id, match_id, choice, amount, "", "", now])

    # הורד wallet_real מיד
    wallets = get_wallet(username, group_id)
    new_real = wallets["wallet_real"] - amount
    # wallet_visible לא משתנה עד פתיחת המשחק
    _update_member_wallet(group_id, username, new_real, wallets["wallet_visible"])

    return True, f"הימור על ₪{amount} נרשם בהצלחה!"

def update_bet(username: str, group_id: str, match_id: str,
               new_choice: str, new_amount: float) -> tuple[bool, str]:
    """עריכת הימור קיים לפני פתיחת המשחק"""
    matches_df = get_all_matches()
    match = matches_df[matches_df["match_id"] == match_id]
    if match.empty or match.iloc[0]["status"] != "open":
        return False, "לא ניתן לערוך הימור לאחר פתיחת המשחק"

    bets_df = sheet_to_df("bets")
    existing = bets_df[
        (bets_df["username"] == username) &
        (bets_df["group_id"] == group_id) &
        (bets_df["match_id"] == match_id)
    ]
    if existing.empty:
        return False, "לא נמצא הימור לעריכה"

    old_amount = float(existing.iloc[0]["amount"])
    bet_id = existing.iloc[0]["bet_id"]

    # בדוק יתרה זמינה (כולל החזרת הסכום הישן)
    available = get_available_balance(username, group_id) + old_amount
    if new_amount > available:
        return False, f"אין מספיק כסף. יתרה זמינה: ₪{round(available, 2)}"

    # עדכן שורת הימור
    ws = get_sheet("bets")
    all_bets = sheet_to_df("bets")
    b_mask = all_bets["bet_id"] == bet_id
    b_idx = all_bets[b_mask].index[0] + 2
    ws.update_cell(b_idx, 5, new_choice)   # choice
    ws.update_cell(b_idx, 6, new_amount)   # amount

    # עדכן wallet_real (הפרש)
    wallets = get_wallet(username, group_id)
    diff = new_amount - old_amount
    new_real = wallets["wallet_real"] - diff
    _update_member_wallet(group_id, username, new_real, wallets["wallet_visible"])

    return True, "הימור עודכן בהצלחה!"

def cancel_bet(username: str, group_id: str, match_id: str) -> tuple[bool, str]:
    matches_df = get_all_matches()
    match = matches_df[matches_df["match_id"] == match_id]
    if match.empty or match.iloc[0]["status"] != "open":
        return False, "לא ניתן לבטל הימור לאחר פתיחת המשחק"

    bets_df = sheet_to_df("bets")
    existing = bets_df[
        (bets_df["username"] == username) &
        (bets_df["group_id"] == group_id) &
        (bets_df["match_id"] == match_id)
    ]
    if existing.empty:
        return False, "לא נמצא הימור לביטול"

    old_amount = float(existing.iloc[0]["amount"])
    bet_id = existing.iloc[0]["bet_id"]

    # מחק שורה
    ws = get_sheet("bets")
    all_bets = sheet_to_df("bets")
    b_mask = all_bets["bet_id"] == bet_id
    b_idx = all_bets[b_mask].index[0] + 2
    ws.delete_rows(b_idx)

    # החזר כסף ל-wallet_real
    wallets = get_wallet(username, group_id)
    new_real = wallets["wallet_real"] + old_amount
    _update_member_wallet(group_id, username, new_real, wallets["wallet_visible"])

    return True, "הימור בוטל והכסף הוחזר לארנק"