import os

# Set our data path for the app, and our path to our settings file
APP_DATA_PATH = os.getenv("FLET_APP_STORAGE_DATA")

# Set our path for all stories, and our active story
SETTINGS_FILE_PATH = os.path.join(APP_DATA_PATH, "settings.json")
STORIES_DIRECTOR_PATH = os.path.join(APP_DATA_PATH, "stories")

# Size for stacks with fixed sizes (plot chart and character relationship map)
FIXED_STACK_WIDTH = 5000
FIXED_STACK_HEIGHT = 3000

# Padding when drawing a plotline
PLOTLINE_CANVAS_PADDING = 50