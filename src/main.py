'''
The main file to run the application.
Initializes the app, settings, page data, and renders our UI onto the page
'''

import flet as ft
from models.app import app

# Remove auto updates so we can improve performance
ft.context.disable_auto_update()

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
