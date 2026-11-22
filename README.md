# StoryBoard app

StoryBoard is a passion project for authors and illustrators to visualize, organize, and create their novels or comics. Built entirely in Python using the Flet framework.
Also useful for D&D Campaign tracking.

## Features & Tech
- Folder Organization System (Binder/Tree View)
- Manuscript Text Editor (Flutter Quill extension)
- Canvas Drawing capabilities
- Notecard widget for ideas, themes, etc.
- Plotline & Timeline visualization
- Canvas Boards for sketches and live updates on progress for illustrations
- Map and location creation
- Item, weapon, and armor creation
- Plot Chart with node system for alternate plot visualization
- Comic Preview to see your illustrations stitched together as a finished product
- Character Relationship Map for visualizing how characters are connected to other characters in your story
- Kanban boards with editable columns and cards
- Character (and template) creation
- World (and template) creation
- Radar and bar charts for power scaling and changes in physical growth throughout a story's progression
- Tab system workspace for all widgets in your story

In Settings > Templates, customize the character, world, and item templates used
for new widgets. Add or remove fields and sections, drag fields or use the
section arrows to reorder them, or reset each template to its defaults. Existing widgets are not changed.
Older settings retain their saved templates; the active legacy template (or
Default when none is active) becomes the editable template.
Pushing or pulling settings through Google Drive also syncs all three editable
templates. Pulling settings replaces the local templates.
In a Kanban widget, add columns with **Add Column**; each starts with one card.
Use each column's menu to add cards, set its color, or delete it. Edit column titles and card values directly;
card chips toggle strikethrough or delete cards. Drag a column or card to
reorder it. Changes are saved with the widget.
Google Drive sign-in is saved on the device; expired access tokens are refreshed
automatically when cloud features are used. Reconnect if access is revoked.
Google credentials are encrypted on disk using a key in the operating system
credential store (Windows Credential Locker, macOS Keychain, or Linux Secret
Service). Linux requires an available, unlocked Secret Service keyring. Existing
plaintext credentials are migrated when first loaded; if the credential store is
unavailable, migration fails and the original file remains until it can succeed.
Backups of the old plaintext file should be removed separately.

<p align="center">
  <img src="images/Screenshot%201.png" alt="Screenshot 1 of the StoryBoard app" width="700">
  <img src="images/Screenshot%202.png" alt="Screenshot 2 of the StoryBoard app" width="700">
  <img src="images/Screenshot%203.png" alt="Screenshot 3 of the StoryBoard app" width="700">
  <img src="images/Screenshot%204.png" alt="Screenshot 4 of the StoryBoard app" width="700">
  <img src="images/Screenshot%205.png" alt="Screenshot 5 of the StoryBoard app" width="700">
</p>

# For Devs

## Run the app

### uv

Run as a desktop app:

```
uv run flet run
```

Run as a web app:

```
uv run flet run --web
```

### Poetry

Install dependencies from `pyproject.toml`:

```
poetry install
```

Run as a desktop app:

```
poetry run flet run
```

Run as a web app:

```
poetry run flet run --web
```

For more details on running the app, refer to the [Getting Started Guide](https://flet.dev/docs/getting-started/).

## Build the app

### Android

```
flet build apk -v
```

For more details on building and signing `.apk` or `.aab`, refer to the [Android Packaging Guide](https://flet.dev/docs/publish/android/).

### iOS

```
flet build ipa -v
```

For more details on building and signing `.ipa`, refer to the [iOS Packaging Guide](https://flet.dev/docs/publish/ios/).

### macOS

```
flet build macos -v
```

For more details on building macOS package, refer to the [macOS Packaging Guide](https://flet.dev/docs/publish/macos/).

### Linux

```
flet build linux -v
```

For more details on building Linux package, refer to the [Linux Packaging Guide](https://flet.dev/docs/publish/linux/).

### Windows

```
flet build windows -v
```

For more details on building Windows package, refer to the [Windows Packaging Guide](https://flet.dev/docs/publish/windows/).
