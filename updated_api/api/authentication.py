import os
import requests
from fastapi import Request, HTTPException

def get_user_info(request: Request):
    """
    Get the user's identity from headers (Azure App Service injects claims in headers).
    """
    headers = dict(request.headers)
    user_info = {
        "user_name": headers.get("X-MS-CLIENT-PRINCIPAL-NAME"),
        "identity_provider": headers.get("X-MS-CLIENT-PRINCIPAL-IDP"),
        "user_id": headers.get("X-MS-CLIENT-PRINCIPAL-ID")
    }

    access_token = headers.get("X-MS-TOKEN-AAD-ACCESS-TOKEN")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token missing")

    url = "https://graph.microsoft.com/v1.0/me"
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=auth_headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch user info from Microsoft Graph")

    user_info.update(response.json())
    return user_info


    