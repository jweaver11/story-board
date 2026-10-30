'''
Google Drive sync: OAuth (installed-app flow) and manual push/pull that mirrors APP_DATA_PATH with a "Story Board" Drive folder (the receiving side is overwritten).
All functions here are blocking; call them with asyncio.to_thread from the UI.
'''

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import shutil
from constants import APP_DATA_PATH

# drive.file only grants access to files/folders this app created
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
DRIVE_FOLDER_NAME = "Story Board"
FOLDER_MIME = "application/vnd.google-apps.folder"

TOKEN_FILE_NAME = "google_token.json"
TOKEN_PATH = os.path.join(APP_DATA_PATH, TOKEN_FILE_NAME)
CLIENT_SECRET_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "google_client_secret.json")

# Never uploaded, downloaded, or deleted
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
    # Imported lazily: it needs wsgiref, which the packaged Python runtime lacks
    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")
    _save_credentials(creds)
    return True


def _service():
    creds = _load_credentials()
    if creds is None:
        raise PermissionError("Not authenticated with Google")
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _list_all(service) -> dict[str, list[dict]]:
    ''' Every non-trashed item this app can see, grouped by parent folder id '''
    children: dict[str, list[dict]] = {}
    token = None
    while True:
        res = service.files().list(
            q="trashed = false", fields="nextPageToken, files(id, name, mimeType, parents)",
            pageSize=1000, pageToken=token,
        ).execute()
        for item in res.get("files", []):
            for parent in item.get("parents", []):
                children.setdefault(parent, []).append(item)
        token = res.get("nextPageToken")
        if not token:
            return children


def _find_root(service) -> str | None:
    q = f"name = '{DRIVE_FOLDER_NAME}' and mimeType = '{FOLDER_MIME}' and trashed = false"
    files = service.files().list(q=q, fields="files(id)", pageSize=1).execute().get("files", [])
    return files[0]["id"] if files else None


def _create_folder(service, name: str, parent_id: str | None) -> str:
    body = {"name": name, "mimeType": FOLDER_MIME}
    if parent_id:
        body["parents"] = [parent_id]
    return service.files().create(body=body, fields="id").execute()["id"]


def _trash(service, item_id: str) -> None:
    service.files().update(fileId=item_id, body={"trashed": True}).execute()


def _push_dir(service, children: dict, local_dir: str, folder_id: str, is_root: bool) -> int:
    count = 0
    remote = {}     # name -> item. Duplicate names are trashed
    for item in children.get(folder_id, []):
        if item["name"] in remote:
            _trash(service, item["id"])
        else:
            remote[item["name"]] = item

    local_names = set()
    for entry in os.scandir(local_dir):
        if (is_root and entry.name in EXCLUDED_FILES) or entry.name.endswith(".tmp"):
            continue
        local_names.add(entry.name)
        existing = remote.get(entry.name)
        is_remote_folder = existing is not None and existing["mimeType"] == FOLDER_MIME

        if entry.is_dir():
            if existing is not None and not is_remote_folder:   # A file is in the way of this folder
                _trash(service, existing["id"])
                existing = None
            sub_id = existing["id"] if existing else _create_folder(service, entry.name, folder_id)
            count += _push_dir(service, children, entry.path, sub_id, False)
        elif entry.is_file():
            media = MediaFileUpload(entry.path, resumable=False)
            if existing is not None and not is_remote_folder:
                service.files().update(fileId=existing["id"], media_body=media).execute()
            else:
                if existing is not None:
                    _trash(service, existing["id"])
                service.files().create(body={"name": entry.name, "parents": [folder_id]}, media_body=media, fields="id").execute()
            count += 1

    for name, item in remote.items():   # Mirror: anything on Drive that we don't have locally goes
        if name not in local_names:
            _trash(service, item["id"])
    return count


def push_to_drive() -> int:
    ''' Makes Drive/Story Board an exact copy of APP_DATA_PATH. Returns the number of files uploaded '''
    service = _service()
    root_id = _find_root(service) or _create_folder(service, DRIVE_FOLDER_NAME, None)
    return _push_dir(service, _list_all(service), APP_DATA_PATH, root_id, True)


def _collect_remote(service, children: dict, folder_id: str, rel: str, files: dict, dirs: set) -> None:
    for item in children.get(folder_id, []):
        item_rel = os.path.join(rel, item["name"]) if rel else item["name"]
        if item["mimeType"] == FOLDER_MIME:
            dirs.add(item_rel)
            _collect_remote(service, children, item["id"], item_rel, files, dirs)
        elif item_rel not in files:
            files[item_rel] = service.files().get_media(fileId=item["id"]).execute()


def pull_from_drive() -> int:
    ''' Makes APP_DATA_PATH an exact copy of Drive/Story Board. Returns the number of files written '''
    service = _service()
    root_id = _find_root(service)
    if root_id is None:
        raise FileNotFoundError("No 'Story Board' folder was found in your Google Drive. Push to the cloud first.")

    # Download everything before touching local data, so a failed download changes nothing
    files: dict[str, bytes] = {}
    dirs: set[str] = set()
    _collect_remote(service, _list_all(service), root_id, "", files, dirs)
    files = {rel: data for rel, data in files.items() if rel not in EXCLUDED_FILES}

    for rel in dirs:
        os.makedirs(os.path.join(APP_DATA_PATH, rel), exist_ok=True)
    for rel, data in files.items():
        path = os.path.join(APP_DATA_PATH, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, path)

    keep_files = {os.path.normcase(os.path.join(APP_DATA_PATH, rel)) for rel in files} | {os.path.normcase(TOKEN_PATH)}
    keep_dirs = {os.path.normcase(os.path.join(APP_DATA_PATH, rel)) for rel in dirs}
    for current, dirnames, filenames in os.walk(APP_DATA_PATH, topdown=False):
        for name in filenames:
            path = os.path.join(current, name)
            if os.path.normcase(path) not in keep_files:
                os.remove(path)
        for name in dirnames:
            path = os.path.join(current, name)
            if os.path.normcase(path) not in keep_dirs:
                shutil.rmtree(path, ignore_errors=True)
    return len(files)
