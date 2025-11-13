import requests

url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"

data = {
    "client_id": "90dede77-a858-442d-ba05-39e37c1694ac",
    "scope": "Files.Read offline_access",
    "code": "M.C509_SN1.2.U.a6120e1e-5296-7715-14ce-6d6e265e6033",  # seu code
    "redirect_uri": "http://localhost:8501",
    "grant_type": "authorization_code",
    "client_secret": "ce76d0f2-ee35-49d1-84a4-6e4fb906e0c7"
}

res = requests.post(url, data=data)
print(res.status_code)
print(res.json())
