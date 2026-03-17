import gspread
from google.oauth2.service_account import Credentials

# הגדרת הרשאות
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file("championsbet-490323-59706f5de67b.json", scopes=scopes)
client = gspread.authorize(creds)

# פתיחת ה-Sheet
spreadsheet_name = "ChampionsBetDB"
sh = client.open(spreadsheet_name)

# הגדרת הטאבים והכותרות
tabs = {
    "users": ["username", "hashed_password", "is_admin"],
    "groups": ["group_id", "group_name", "created_by"],
    "group_members": ["group_id", "username", "wallet_real", "wallet_visible"],
    "matches": ["match_id", "stage", "team_a", "team_b", "odds_a", "odds_draw", "odds_b", "match_datetime", "status", "winner"],
    "bets": ["bet_id", "username", "group_id", "match_id", "choice", "amount", "result", "payout", "placed_at"],
    "wallet_log": ["log_id", "username", "group_id", "amount", "reason", "timestamp"]
}

for tab_name, headers in tabs.items():
    try:
        worksheet = sh.add_worksheet(title=tab_name, rows="100", cols="20")
    except:
        worksheet = sh.worksheet(tab_name)
    worksheet.update('A1', [headers])
    print(f"✅ טאב {tab_name} מוכן!")

# מחיקת הטאב הריק הראשון (Sheet1)
try:
    sh.del_worksheet(sh.worksheet("Sheet1"))
except:
    pass

print("\n🔥 הכל מוכן! השיטס שלך מדוגם.")