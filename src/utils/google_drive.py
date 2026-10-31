'''
Google Drive sync: OAuth (installed-app flow) and manual push/pull that mirrors APP_DATA_PATH with a "Story Board" Drive folder (the receiving side is overwritten).
All functions here are blocking; call them with asyncio.to_thread from the UI.
'''

import io
import json
import os
import socket
import httplib2
from google.auth.exceptions import RefreshError, TransportError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
import shutil
from constants import APP_DATA_PATH, STORIES_DIRECTORY_PATH

# drive.file only grants access to files/folders this app created
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
DRIVE_FOLDER_NAME = "Story Board"
FOLDER_MIME = "application/vnd.google-apps.folder"
SETTINGS_FILE_NAME = "settings.json"
STORIES_FOLDER_NAME = "stories"

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
    except TransportError:
        raise   # Offline. Not the same as being signed out
    except Exception as e:
        print(f"Google credentials invalid: {e}")
    return None


def _save_credentials(creds: Credentials) -> None:
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        f.write(creds.to_json())


def is_authenticated() -> bool:
    ''' Local check only (works offline): True if saved credentials exist that can be used or refreshed '''
    if not os.path.exists(TOKEN_PATH):
        return False
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        return bool(creds.valid or creds.refresh_token)
    except Exception:
        return False


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


def _ensure_folder(service, children: dict, parent_id: str, name: str) -> str:
    for item in children.get(parent_id, []):
        if item["name"] == name and item["mimeType"] == FOLDER_MIME:
            return item["id"]
    folder_id = _create_folder(service, name, parent_id)
    children.setdefault(parent_id, []).append({"id": folder_id, "name": name, "mimeType": FOLDER_MIME})
    return folder_id


def _upload_settings(service, children: dict, root_id: str, settings_data: dict) -> None:
    ''' Uploads settings.json to the Drive root, leaving out the device specific 'page' settings '''
    data = {k: v for k, v in settings_data.items() if k != "page"}
    media = MediaIoBaseUpload(io.BytesIO(json.dumps(data, indent=4).encode("utf-8")), mimetype="application/json", resumable=False)
    existing = [i for i in children.get(root_id, []) if i["name"] == SETTINGS_FILE_NAME and i["mimeType"] != FOLDER_MIME]
    if existing:
        service.files().update(fileId=existing[0]["id"], media_body=media).execute()
        for duplicate in existing[1:]:
            _trash(service, duplicate["id"])
    else:
        service.files().create(body={"name": SETTINGS_FILE_NAME, "parents": [root_id]}, media_body=media, fields="id").execute()


def push_settings(settings_data: dict) -> int:
    ''' Uploads all settings except 'page'. Returns the number of files uploaded '''
    service = _service()
    children = _list_all(service)
    root_id = _find_root(service) or _create_folder(service, DRIVE_FOLDER_NAME, None)
    _upload_settings(service, children, root_id, settings_data)
    return 1


def push_story(story_dir: str) -> int:
    ''' Makes this story's folder in the cloud an exact copy of the local one. Returns the number of files uploaded '''
    service = _service()
    children = _list_all(service)
    root_id = _find_root(service) or _create_folder(service, DRIVE_FOLDER_NAME, None)
    stories_id = _ensure_folder(service, children, root_id, STORIES_FOLDER_NAME)
    story_id = _ensure_folder(service, children, stories_id, os.path.basename(os.path.normpath(story_dir)))
    return _push_dir(service, children, story_dir, story_id, False)


def push_all(settings_data: dict, story_dir: str | None = None) -> int:
    ''' Pushes settings (minus 'page') and, if given, the current story '''
    service = _service()
    children = _list_all(service)
    root_id = _find_root(service) or _create_folder(service, DRIVE_FOLDER_NAME, None)
    _upload_settings(service, children, root_id, settings_data)
    count = 1
    if story_dir and os.path.isdir(story_dir):
        stories_id = _ensure_folder(service, children, root_id, STORIES_FOLDER_NAME)
        story_id = _ensure_folder(service, children, stories_id, os.path.basename(os.path.normpath(story_dir)))
        count += _push_dir(service, children, story_dir, story_id, False)
    return count


def _collect_remote(service, children: dict, folder_id: str, rel: str, files: dict, dirs: set) -> None:
    for item in children.get(folder_id, []):
        item_rel = os.path.join(rel, item["name"]) if rel else item["name"]
        if item["mimeType"] == FOLDER_MIME:
            dirs.add(item_rel)
            _collect_remote(service, children, item["id"], item_rel, files, dirs)
        elif item_rel not in files:
            files[item_rel] = service.files().get_media(fileId=item["id"]).execute()


def pull_all() -> tuple[dict | None, int]:
    '''
    Downloads the cloud settings and stories. Stories in the cloud replace their local folders; local only stories are kept.
    Returns (cloud settings or None, number of story files written). Nothing local changes if a download fails.
    '''
    service = _service()
    root_id = _find_root(service)
    if root_id is None:
        raise FileNotFoundError("No 'Story Board' folder was found in your Google Drive. Push to the cloud first.")

    children = _list_all(service)
    settings_data = None
    stories_id = None
    for item in children.get(root_id, []):
        if item["name"] == SETTINGS_FILE_NAME and item["mimeType"] != FOLDER_MIME and settings_data is None:
            settings_data = json.loads(service.files().get_media(fileId=item["id"]).execute().decode("utf-8"))
        elif item["name"] == STORIES_FOLDER_NAME and item["mimeType"] == FOLDER_MIME:
            stories_id = item["id"]

    files: dict[str, bytes] = {}
    dirs: set[str] = set()
    if stories_id:
        _collect_remote(service, children, stories_id, "", files, dirs)

    story_names = {rel.split(os.sep)[0] for rel in list(files) + list(dirs)}
    for name in story_names:
        shutil.rmtree(os.path.join(STORIES_DIRECTORY_PATH, name), ignore_errors=True)
    for rel in dirs:
        os.makedirs(os.path.join(STORIES_DIRECTORY_PATH, rel), exist_ok=True)
    for rel, data in files.items():
        path = os.path.join(STORIES_DIRECTORY_PATH, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    return settings_data, len(files)


def _get_settings(service, children: dict, root_id: str) -> dict | None:
    for item in children.get(root_id, []):
        if item["name"] == SETTINGS_FILE_NAME and item["mimeType"] != FOLDER_MIME:
            return json.loads(service.files().get_media(fileId=item["id"]).execute().decode("utf-8"))
    return None


def pull_settings() -> dict:
    ''' Downloads the cloud settings. Raises FileNotFoundError if none were pushed yet '''
    service = _service()
    root_id = _find_root(service)
    settings_data = _get_settings(service, _list_all(service), root_id) if root_id else None
    if settings_data is None:
        raise FileNotFoundError("No settings were found in your Google Drive. Push your settings first.")
    return settings_data


def pull_story(story_dir: str) -> int:
    ''' Replaces the local story folder with its cloud copy. Nothing local changes if a download fails '''
    service = _service()
    root_id = _find_root(service)
    story_name = os.path.basename(os.path.normpath(story_dir))
    children = _list_all(service)
    stories_id = next((i["id"] for i in children.get(root_id, []) if i["name"] == STORIES_FOLDER_NAME and i["mimeType"] == FOLDER_MIME), None) if root_id else None
    story_id = next((i["id"] for i in children.get(stories_id, []) if i["name"] == story_name and i["mimeType"] == FOLDER_MIME), None) if stories_id else None
    if story_id is None:
        raise FileNotFoundError("This story was not found in your Google Drive. Push it first.")

    files: dict[str, bytes] = {}
    dirs: set[str] = set()
    _collect_remote(service, children, story_id, "", files, dirs)

    shutil.rmtree(story_dir, ignore_errors=True)
    os.makedirs(story_dir, exist_ok=True)
    for rel in dirs:
        os.makedirs(os.path.join(story_dir, rel), exist_ok=True)
    for rel, data in files.items():
        path = os.path.join(story_dir, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
    return len(files)


def disconnect() -> None:
    ''' Forgets the saved Google credentials on this device '''
    if os.path.exists(TOKEN_PATH):
        os.remove(TOKEN_PATH)


def describe_error(ex: Exception) -> str:
    ''' Turns a cloud failure into a message the user can act on '''
    if isinstance(ex, (ConnectionError, TimeoutError, socket.gaierror, socket.timeout, httplib2.ServerNotFoundError, TransportError)):
        return "No internet connection. Check your connection and try again."
    if isinstance(ex, RefreshError):
        return "Your Google connection expired. Please reconnect to Google Drive."
    if isinstance(ex, PermissionError):
        return "Not connected to Google Drive."
    if isinstance(ex, HttpError):
        status = getattr(ex.resp, "status", None)
        if status in (401, 403):
            return "Google Drive denied access (or the quota was exceeded). Try reconnecting."
        return f"Google Drive error ({status})."
    if isinstance(ex, OSError) and ex.errno is None and "getaddrinfo" in str(ex):
        return "No internet connection. Check your connection and try again."
    return f"Google Drive error: {ex}"
