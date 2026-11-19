'''
The main file to run the application.
Initializes the app, settings, page data, and renders our UI onto the page
'''

import flet as ft
from pathlib import Path
from models.app import app
from styles.snack_bar import SnackBar
from utils import google_drive
from models.views.home import create_home_view
from models.views.loading import create_loading_view
from models.views.welcome import create_welcome_view
import asyncio

# Remove auto updates so we can improve performance
ft.context.disable_auto_update()

# Test commit

# Main function
async def main(page: ft.Page):
     
    # Load settings and previous story (if one exists)
    app.load_settings(page) 
 
    # If its our first launch, show the welcome view
    if app.settings.data.get("is_first_launch", True):
        await page.push_route("/welcome")

    # Otherwise start loading the previous story
    else: 
        await page.push_route("/loading")

        # Loads the previous story's view, or the home view if we can't find it
        await app.load_previous_story(page)     


    


# Runs the app
ft.run(main)
