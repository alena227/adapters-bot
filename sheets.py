import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from config import (
    PARTNERSHIP_SPREADSHEET_ID, MEETINGS_SPREADSHEET_ID,
    PARTNERSHIP_HEADERS, MEETING_HEADERS,
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _get_client():
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    return gspread.authorize(creds)


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
