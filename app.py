client_id = "90dede77-a858-442d-ba05-39e37c1694ac"
client_secret = "ce76d0f2-ee35-49d1-84a4-6e4fb906e0c7"
authorization_code = "NOVO_CODE_AQUI"

import requests

url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

data = {
    "client_id": client_id,
    "scope": "Files.Read offline_access",
    "code": authorization_code,
    "redirect_uri": "http://localhost:8501",
    "grant_type": "authorization_code",
    "client_secret": client_secret
}

res = requests.post(url, data=data)
print(res.json())
