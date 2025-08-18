# Story-Board Usage Guide

## Story Management Features

The Story-Board app now includes comprehensive story management capabilities that allow you to create, organize, and switch between multiple story projects.

### Creating a New Story

1. **Open the File Menu**: Click on "File" in the top menu bar
2. **Select New**: Click on "New" to open the new story dialog
3. **Enter Story Name**: Type the name for your new story
4. **Create Story**: Click "Create Story" button
   - The story will be created with all necessary folders
   - You'll automatically switch to the new story
   - The story is immediately saved to disk

### Loading an Existing Story

1. **Open the File Menu**: Click on "File" in the top menu bar
2. **Select Open**: Click on "Open" to see available stories
3. **Choose Story**: Select the story you want to load from the list
4. **Load Story**: Click "Load Story" button
   - All story data (characters, notes, etc.) will be loaded
   - The workspace will update to show the selected story's content
   - The app title will update to show the current story

### Saving Your Current Story

1. **Open the File Menu**: Click on "File" in the top menu bar
2. **Select Save**: Click on "Save" to save your current work
   - All characters and story elements are saved
   - Story metadata is updated
   - A confirmation message will appear

### Managing Multiple Stories

- **Story List**: The Open dialog shows all your available stories
- **Active Story Indicator**: Current active stories are marked in the list
- **Story Deletion**: Use the Delete button in the Open dialog (cannot delete default_story)
- **Story Switching**: You can switch between stories at any time without losing work

### Story File Structure

Each story creates its own directory with organized subfolders:
```
MyStoryName/
├── characters/        # Character files (.pkl)
├── notes/            # Story notes
├── pins/             # Widget layout data
├── plotlines/        # Plot and timeline data
├── scenes/           # Scene organization
└── story_metadata.json  # Story information
```

### Character Management

- **Creating Characters**: Use the Character workspace to add new characters
- **Character Persistence**: Characters are automatically saved when created or modified
- **Cross-Story Characters**: Each story maintains its own character roster
- **Character Widgets**: Drag and arrange character widgets in your workspace

### Tips for Effective Story Management

1. **Use Descriptive Names**: Give your stories clear, descriptive names
2. **Regular Saving**: While auto-save is enabled, manually save important work via File > Save
3. **Backup Important Stories**: The story files are stored in the `storage/data/stories` folder
4. **Organize Your Workspace**: Use the drag-and-drop widget system to organize your story elements
5. **Switch Safely**: You can switch between stories without losing unsaved work

### Troubleshooting

**Story Won't Load**: Check that the story folder exists in `storage/data/stories`
**Characters Not Appearing**: Ensure the character files exist in the `characters` folder
**Can't Delete Story**: The "default_story" cannot be deleted - create a new story first
**App Crashes**: Report bugs with the story name and steps that caused the issue

### Data Location

All story data is stored in:
- **Windows**: `<project_folder>/storage/data/stories/`
- Each story has its own folder with all associated files
- Metadata is stored in JSON format for easy reading

The Story-Board app now provides a complete story management system that scales from simple single-story projects to complex multi-story management for prolific authors.
