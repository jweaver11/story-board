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
- Character (and template) creation
- World (and template) creation
- Radar and bar charts for power scaling and changes in physical growth throughout a story's progression
- Tab system workspace for all widgets in your story

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
