import json

with open("championsbet-490323-59706f5de67b.json") as f:
    d = json.load(f)

toml = f"""[gcp_service_account]
type = "{d['type']}"
project_id = "{d['project_id']}"
private_key_id = "{d['private_key_id']}"
private_key = "{d['private_key'].replace(chr(10), '\\n')}"
client_email = "{d['client_email']}"
client_id = "{d['client_id']}"
auth_uri = "{d['auth_uri']}"
token_uri = "{d['token_uri']}"
auth_provider_x509_cert_url = "{d['auth_provider_x509_cert_url']}"
client_x509_cert_url = "{d['client_x509_cert_url']}"

[sheets]
spreadsheet_name = "ChampionsBetDB"
"""

print(toml)
