import json

with open("championsbet-490323-59706f5de67b.json") as f:
    d = json.load(f)

# הדפס בפורמט מוכן להעתקה ל-Streamlit
print("[gcp_service_account]")
for key, value in d.items():
    if key == "private_key":
        # חשוב: המר newlines לתווי escape
        escaped = value.replace("\n", "\\n")
        print(f'{key} = "{escaped}"')
    else:
        print(f'{key} = "{value}"')

print()
print("[sheets]")
print('spreadsheet_name = "ChampionsBetDB"')
