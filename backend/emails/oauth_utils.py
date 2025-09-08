import json
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from django.conf import settings
from django.urls import reverse
import requests


class GmailOAuthHelper:
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    
    @staticmethod
    def get_authorization_url(tenant_id):
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
                }
            },
            scopes=GmailOAuthHelper.SCOPES
        )
        
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=tenant_id
        )
        
        return authorization_url, state
    
    @staticmethod
    def exchange_code_for_token(code, state):
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
                }
            },
            scopes=GmailOAuthHelper.SCOPES
        )
        
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        return json.loads(credentials.to_json()), state


class OutlookOAuthHelper:
    SCOPES = ['https://graph.microsoft.com/mail.send']
    
    @staticmethod
    def get_authorization_url(tenant_id):
        auth_url = (
            f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
            f"?client_id={settings.MICROSOFT_CLIENT_ID}"
            f"&response_type=code"
            f"&redirect_uri={settings.MICROSOFT_REDIRECT_URI}"
            f"&response_mode=query"
            f"&scope={' '.join(OutlookOAuthHelper.SCOPES)}"
            f"&state={tenant_id}"
        )
        
        return auth_url, tenant_id
    
    @staticmethod
    def exchange_code_for_token(code, state):
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        
        data = {
            'client_id': settings.MICROSOFT_CLIENT_ID,
            'client_secret': settings.MICROSOFT_CLIENT_SECRET,
            'code': code,
            'redirect_uri': settings.MICROSOFT_REDIRECT_URI,
            'grant_type': 'authorization_code',
            'scope': ' '.join(OutlookOAuthHelper.SCOPES)
        }
        
        response = requests.post(token_url, data=data)
        
        if response.status_code == 200:
            return response.json(), state
        else:
            raise Exception(f"Failed to exchange code for token: {response.text}")


def refresh_google_token(credentials_data):
    creds = Credentials.from_authorized_user_info(credentials_data)
    
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        return json.loads(creds.to_json())
    
    return credentials_data


def refresh_outlook_token(credentials_data):
    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    
    data = {
        'client_id': settings.MICROSOFT_CLIENT_ID,
        'client_secret': settings.MICROSOFT_CLIENT_SECRET,
        'refresh_token': credentials_data['refresh_token'],
        'grant_type': 'refresh_token',
        'scope': ' '.join(OutlookOAuthHelper.SCOPES)
    }
    
    response = requests.post(token_url, data=data)
    
    if response.status_code == 200:
        new_tokens = response.json()
        credentials_data.update(new_tokens)
        return credentials_data
    else:
        raise Exception(f"Failed to refresh token: {response.text}")