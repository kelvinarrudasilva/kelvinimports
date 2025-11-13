import requests

url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

data = {
    "client_id": "90dede77-a858-442d-ba05-39e37c1694ac",
    "scope": "Files.Read offline_access",
    "code": "M.C509_BAY.2.U.ff595ce0-0a3f-69e1-5f07-29e80f3726f1",
    "redirect_uri": "http://localhost:8501",
    "grant_type": "authorization_code",
    "client_secret": "ce76d0f2-ee35-49d1-84a4-6e4fb906e0c7"
}

res = requests.post(url, data=data)
print(res.json())
