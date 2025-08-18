# StoryBoard App

A comprehensive creative writing tool to help authors organize and develop their stories, novels, comics, and animations.

## Mission

StoryBoard helps creators of novels, comics, and animations organize and develop their stories. It provides a visual workspace with draggable widgets to manage all aspects of storytelling from characters to plot timelines.

## Features

### Story Management ✨ NEW
- **Create Multiple Stories**: Manage multiple story projects simultaneously
- **Story Switching**: Easily switch between different story projects
- **Auto-Save**: Stories are automatically saved with metadata
- **Story Import/Export**: Built-in backup and restore functionality

### Workspace Organization
- **Navigation Rails**: Visual Studio Code-style interface with workspace categories:
  - **Content**: Organize documents, chapters, scenes, images, and animations
  - **Characters**: Expandable character management with detailed profiles
  - **Plot & Timeline**: Visual timeline for story arcs and character journeys
  - **World Building**: Visual representation of locations and settings
  - **Drawing Board**: Integrated drawing tools for artists
  - **Notes**: Free-form notes and story planning

### Creative Workspace
- **Draggable Widgets**: Rearrange and resize story elements anywhere on screen
- **Pin Locations**: Organize widgets in top, left, main, right, and bottom areas
- **Multiple Views**: Tab-based and split-view workspace like VS Code
- **Character Widgets**: Detailed character profiles with age, description, family, goals, etc.

### File Management
- **Project Organization**: Everything stored in organized project files
- **Data Persistence**: All story data automatically saved and restored
- **External File Integration**: Link to external documents, images, and videos

## Getting Started

### Creating Your First Story

1. Launch StoryBoard
2. Click **File > New** in the menu bar
3. Enter your story name and click "Create Story"
4. Start adding characters, plot points, and other story elements

### Managing Multiple Stories

- **Create New Story**: File > New
- **Open Existing Story**: File > Open
- **Save Current Story**: File > Save
- **Switch Between Stories**: File > Open and select from your stories

### Working with Characters

1. Click on the **Characters** workspace in the left rail
2. Click "Create Character" to add a new character
3. Fill in character details (name, age, appearance, backstory, etc.)
4. Drag character widgets around the workspace to organize them
5. Characters automatically save when you create or modify them

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