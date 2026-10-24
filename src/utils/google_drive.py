'''
Google Drive sync: OAuth (installed-app flow) and one-way push of APP_DATA_PATH to a "Story Board" Drive folder.
All functions here are blocking; call them with asyncio.to_thread from the UI.
'''

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from contexts.constants import APP_DATA_PATH

# drive.file only grants access to files/folders this app created
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
DRIVE_FOLDER_NAME = "Story Board"
FOLDER_MIME = "application/vnd.google-apps.folder"

TOKEN_FILE_NAME = "google_token.json"
TOKEN_PATH = os.path.join(APP_DATA_PATH, TOKEN_FILE_NAME)
CLIENT_SECRET_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "google_client_secret.json")

# Never upload credentials
EXCLUDED_FILES = {TOKEN_FILE_NAME}


def _load_credentials() -> Credentials | None:
    ''' Loads saved credentials, refreshing them if expired. Returns None if unavailable/invalid '''
    if not os.path.exists(TOKEN_PATH):
        return None
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        if creds.valid:
            return creds
        if creds.refresh_token:
            creds.refresh(Request())
            _save_credentials(creds)
            return creds
    except Exception as e:
        print(f"Google credentials invalid: {e}")
    return None


def _save_credentials(creds: Credentials) -> None:
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        f.write(creds.to_json())


def is_authenticated() -> bool:
    return _load_credentials() is not None


def authenticate() -> bool:
    ''' Opens the browser for Google sign-in. Blocks until the user finishes or closes the flow '''
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")
    _save_credentials(creds)
    return True


def _escape(name: str) -> str:
    return name.replace("\\", "\\\\").replace("'", "\\'")


def _find(service, name: str, parent_id: str | None, mime: str | None = None) -> str | None:
    q = f"name = '{_escape(name)}' and trashed = false"
    if parent_id:
        q += f" and '{parent_id}' in parents"
    q += f" and mimeType = '{FOLDER_MIME}'" if mime == FOLDER_MIME else f" and mimeType != '{FOLDER_MIME}'"
    res = service.files().list(q=q, fields="files(id)", pageSize=1).execute()
    files = res.get("files", [])
    return files[0]["id"] if files else None


def _get_or_create_folder(service, name: str, parent_id: str | None) -> str:
    existing = _find(service, name, parent_id, FOLDER_MIME)
    if existing:
        return existing
    body = {"name": name, "mimeType": FOLDER_MIME}
    if parent_id:
        body["parents"] = [parent_id]
    return service.files().create(body=body, fields="id").execute()["id"]


def _upload_file(service, local_path: str, parent_id: str) -> None:
    name = os.path.basename(local_path)
    media = MediaFileUpload(local_path, resumable=False)
    existing = _find(service, name, parent_id)
    if existing:
        service.files().update(fileId=existing, media_body=media).execute()
    else:
        service.files().create(body={"name": name, "parents": [parent_id]}, media_body=media, fields="id").execute()


def _upload_directory(service, local_dir: str, parent_id: str) -> int:
    count = 0
    for entry in os.scandir(local_dir):
        if entry.is_dir():
            sub_id = _get_or_create_folder(service, entry.name, parent_id)
            count += _upload_directory(service, entry.path, sub_id)
        elif entry.is_file() and entry.name not in EXCLUDED_FILES:
            _upload_file(service, entry.path, parent_id)
            count += 1
    return count


def push_to_drive() -> int:
    ''' Uploads everything in APP_DATA_PATH to Drive/Story Board. Returns number of files uploaded '''
    creds = _load_credentials()
    if creds is None:
        raise PermissionError("Not authenticated with Google")
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    root_id = _get_or_create_folder(service, DRIVE_FOLDER_NAME, None)
    return _upload_directory(service, APP_DATA_PATH, root_id)
