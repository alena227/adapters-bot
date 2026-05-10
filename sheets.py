import os
import json
import base64
import time
import gspread
import requests as _req
import rsa as _rsa
from google.oauth2.credentials import Credentials as OAuthCreds
from datetime import datetime
from config import (
    PARTNERSHIP_SPREADSHEET_ID, MEETINGS_SPREADSHEET_ID,
    PARTNERSHIP_HEADERS, MEETING_HEADERS,
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


_CREDENTIALS_B64 = "ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAiYWRhcHRlcnNpa25rYm90IiwKICAicHJpdmF0ZV9rZXlfaWQiOiAiNjZiMWI1MzJmYTUyMjU2YTMwZmYwNmUwNGU2M2Q3NWQ5YjMxMjVkNyIsCiAgInByaXZhdGVfa2V5IjogIi0tLS0tQkVHSU4gUFJJVkFURSBLRVktLS0tLVxuTUlJRXV3SUJBREFOQmdrcWhraUc5dzBCQVFFRkFBU0NCS1V3Z2dTaEFnRUFBb0lCQVFEQXhCL09MMjZpMnBvRlxuOEZqQ2FSdVhKY0xqenpvbWRROXZnS3R1a1lyVlh0TS8xTmdWb3YzV25INGRNamVoMGE3aldiZUVKNGV1cGhOeFxubC9vam52VmhldnpDRzdUWCtDV1QvbEFjeWhyci9ub3phM1BiUkV5QjFXTVErUTB3ZmdTWVV6bmpuQkI2UnVCWlxuVENLSHlJbm9PMlFKSHc5K1RzNGxMbmF2NG5rQngvcmxCZlpOcTl5ampldW96YjZoUXU2TU1xUUpBNVVvY1VRQVxuaCtTU0NUcVN6K0loZW0ySFllQnRDeVdpR3N5VU1tN2l4dldhNTN6QjBZRU5SdjFYK1RQcHk1cEh3MzEwMVhpZ1xueVJiWnNnbGhyL2x2RzUvODBxRGt4cTE4STJhY1NmTGcwSnVJRmF2bzFsbXNHN1o0T3FueENqN0pVUEJsTm83MVxuVDd6UTN1MGpBZ01CQUFFQ2dmOEN0a2Y4ak9mcVRaV2x3U0RDS1U4Z2t6Uno0UWFSRzhYVHlZOEtTRmRCVDN0S1xuRXhDRDlXRWkrU3RFdjR6dlZRdWwxMnBROUhCbVppbGp2NGxVVzlEbEFGbllSSGVUV2NTNlVvVnJZKzlQQ2dVK1xuTHZoZFFmS0F0ZWJxd0pxeWdKQ2NMUFdLRFh6VUdCM2lmWUc4WG5RZDR5a1BxMUxuV29pMDh6eW1ncWcydC9GNlxuNVpOVTVlbjNVOHBnZzlhRkZLUjh6T1lBSlh2bWh6bG95U0pSSkNBNlhvVTdqVHg4ZXl1Wk9UdjhjZDFva0ZQdlxuRklQaHpHcDY1Qlk3Nkt4d202NnBycVppRC9LdnlUSU9ySmJEQnhiemFvTHlqZGJPRTcxaTAxZWt3djYzQ3F5S1xuZkh6eHJWVXgvbW8wa01tampGMGNicXpSR2c0aEZESHN0Unc2T0FFQ2dZRUE4cFBsL0RlVXFHRmUxaWFReFpUWVxuMkYxOWs0bUpzTXpDbDlrYmdJT0dWOFN5WUoxcUdHSk5FeGhMZVNIVzlsV3Z2NUwxSlFpNTA2ZE5tVlRGKytMZ1xuZkh5bVhTMEU4L3lBeXJPdDRxRHpWb0dxNXdQejV5TU1zUDNISk5aTjBkd25aWmZzREFhbVdScnVXZWRTNzVaRVxuN2hJRGtYRXlmSGh4WWQ4RVRJbkw1OUVDZ1lFQXkyNmxrSjdqbUsybkpqZVpZcEtCN2h2WGVxVTE2YU51SE9hM1xubmE5Q3kxYWQyT1I1ZDE2MG1PWktvWmpyV2VnSzl3TytOQzcyQlU0OWRVeC80VWpEdWdPTG45bGFGWGVORFdBMlxuZ0ozWGFMVk9YT01jSDZOc0k1bEcxcStyUlFXSE5nWnNwc1Baek15SjNMRHhsVVpqdEdQOENFQ1llVnBSTlNUclxuSEprNTlyTUNnWUVBcExSTENjOXJQbEN1cGRVVm96SUhjaEU0Zkg1OFlQRUdoemZBZHFmWEJhem1PTGRwSEJsU1xubjg1MUlGQWJ0ckpEWEY0WjJRVnR0d24zcEU1dEJ6UHFuRnUrVWJHSmxXZ3l3bTd4ZDlrMG45MzIvbGd1dVJlUlxuUEhOelRjMjhsT3RZVEtDMGd3M1kwTk42VnN5OEFUVVVwRmpTMTJQMmxaRHAyendqblJ4S3VLRUNnWUFaMlFJeVxuWU8zY0xWeEtqOC91WlYwYTZ2Q3pCYURYQWN2dzRpTzhabE5mVUs4WHF0Z0FJY2xpa0FnMWhoK0pPZUdDeHpmNFxubTJybys2cjFaM1hzSXZtemZkWFV4cUlhamlrZTVQV24yK1pOeUpPZlc3L3NDVENwU1VWbDY4WWdLL2FsRjZYZ1xuZm93QzZJNHZ1MC9HdnIzV1lzbllKcFQ0L2svSko5cXp0SWhYM3dLQmdIRjNqM3FlZ0pFL25RMlE3MEp6bWhVaVxuUThOWElGU0lRS3BBWER5K1lkT0lqQ1JONWd6ZE5XdjlOZDd3eDJGT1lLdHUvdHlaS1B0bEQ1dFBqWFkvQmtMK1xuVFlTYzFHNStjWk5oSGtsalVOSzI2b3BDdUZvODhnV0pwWm1jaE1keW9DV1VNZkFwTVp3cDNDcUxNRTB5VVVrblxubkZRZmtFMnA4c2ZzWVlOUXF6THpcbi0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS1cbiIsCiAgImNsaWVudF9lbWFpbCI6ICJhZGFwdGVycy1ib3RAYWRhcHRlcnNpa25rYm90LmlhbS5nc2VydmljZWFjY291bnQuY29tIiwKICAiY2xpZW50X2lkIjogIjEwMjM2OTgyMjQ4MDY5MzA5ODM3OCIsCiAgImF1dGhfdXJpIjogImh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbS9vL29hdXRoMi9hdXRoIiwKICAidG9rZW5fdXJpIjogImh0dHBzOi8vb2F1dGgyLmdvb2dsZWFwaXMuY29tL3Rva2VuIiwKICAiYXV0aF9wcm92aWRlcl94NTA5X2NlcnRfdXJsIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL29hdXRoMi92MS9jZXJ0cyIsCiAgImNsaWVudF94NTA5X2NlcnRfdXJsIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL3JvYm90L3YxL21ldGFkYXRhL3g1MDkvYWRhcHRlcnMtYm90JTQwYWRhcHRlcnNpa25rYm90LmlhbS5nc2VydmljZWFjY291bnQuY29tIiwKICAidW5pdmVyc2VfZG9tYWluIjogImdvb2dsZWFwaXMuY29tIgp9Cg=="

def _b64url(data):
    if not isinstance(data, bytes):
        data = json.dumps(data, separators=(',', ':')).encode()
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()


def _get_client():
    creds_b64 = os.getenv("GOOGLE_CREDENTIALS_BASE64") or _CREDENTIALS_B64
    creds_info = json.loads(base64.b64decode(creds_b64).decode("utf-8"))

    now = int(time.time())
    header = _b64url({"alg": "RS256", "typ": "JWT"})
    payload = _b64url({
        "iss": creds_info["client_email"],
        "scope": " ".join(SCOPES),
        "aud": "https://oauth2.googleapis.com/token",
        "exp": now + 3600,
        "iat": now,
    })
    signing_input = f"{header}.{payload}".encode()
    privkey = _rsa.PrivateKey.load_pkcs1_openssl_pem(creds_info["private_key"].encode())
    signature = _rsa.sign(signing_input, privkey, "SHA-256")
    jwt_token = f"{header}.{payload}.{_b64url(signature)}"

    resp = _req.post(
        "https://oauth2.googleapis.com/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": jwt_token,
        },
        timeout=30,
    )
    token_data = resp.json()
    if "access_token" not in token_data:
        raise RuntimeError(f"OAuth error: {token_data}")

    return gspread.Client(auth=OAuthCreds(token=token_data["access_token"]))


def _get_or_create_sheet(spreadsheet, sheet_name: str, headers: list):
    """Возвращает лист с нужным именем, создаёт его с заголовками если не существует."""
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
        if not worksheet.row_values(1):
            worksheet.update("A1", [headers])
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=sheet_name, rows=1000, cols=len(headers)
        )
        worksheet.update("A1", [headers])
    return worksheet


def save_partnership_response(data: dict):
    client = _get_client()
    spreadsheet = client.open_by_key(PARTNERSHIP_SPREADSHEET_ID)
    sheet_name = f"Собрание {data['meeting_key']}"
    worksheet = _get_or_create_sheet(spreadsheet, sheet_name, PARTNERSHIP_HEADERS)

    row = [
        datetime.now().strftime("%d.%m.%Y %H:%M"),
        data.get("meeting_label", ""),
        data.get("your_name", ""),
        data.get("partner_name", ""),
        data.get("ease", ""),
        data.get("liked", ""),
        data.get("disliked", ""),
        data.get("responsibilities", ""),
        data.get("rating", ""),
        data.get("comments", ""),
    ]
    worksheet.append_row(row, value_input_option="USER_ENTERED")


def save_meeting_response(data: dict):
    client = _get_client()
    spreadsheet = client.open_by_key(MEETINGS_SPREADSHEET_ID)
    sheet_name = f"Собрание {data['meeting_number']}"
    worksheet = _get_or_create_sheet(spreadsheet, sheet_name, MEETING_HEADERS)

    row = [
        datetime.now().strftime("%d.%m.%Y %H:%M"),
        data.get("period_label", ""),
        data.get("meeting_label", ""),
        data.get("lecture_rating", ""),
        data.get("lecture_liked", ""),
        data.get("lecture_disliked", ""),
        data.get("int1_rating", ""),
        data.get("int1_conductor", ""),
        data.get("int1_liked", ""),
        data.get("int1_disliked", ""),
        data.get("int2_rating", ""),
        data.get("int2_conductor", ""),
        data.get("int2_liked", ""),
        data.get("int2_disliked", ""),
        data.get("comments", ""),
    ]
    worksheet.append_row(row, value_input_option="USER_ENTERED")
