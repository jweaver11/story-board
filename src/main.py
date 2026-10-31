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
from models.views.welcome import create_welcome_view, animate_welcome_text
import asyncio

# Remove auto updates so we can improve performance
ft.context.disable_auto_update()

# Main function
async def main(page: ft.Page):
     
    # Load settings and previous story (if one exists)
    app.load_settings(page) 
 
    # Either welcome to storyboard view, or our loading view
    if app.settings.data.get("is_first_launch", True):
        # Create the view and add it the page
        welcome_view = create_welcome_view(page)
        page.views.append(welcome_view)     # Add welcome view to the page
        page.update()

        # Grab our text and begin animating it
        text = welcome_view.controls[1]   
        await asyncio.sleep(0.5)   # Wait a bit before animating the text so it doesn't feel too abrupt
        await animate_welcome_text(text)  

        button: ft.Button = welcome_view.controls[2]
        button.visible = True
        button.update()

        text: ft.Text = welcome_view.controls[3]
        text.visible = True
        text.update()

        # Wait here until user clicks either tutorial or skip tutorial button
        while app.settings.data.get("is_first_launch", True):
            await asyncio.sleep(0.1)


    # Otherwise they are not new to storyboard, show our loading view
    else:
        page.views.append(create_loading_view(page))
        page.update()

        sync_on = app.is_cloud_authenticated and app.settings.data.get('sync_with_cloud_on_close', False)
        pull_on_launch = sync_on and app.settings.data.get('sync_with_cloud_on_launch', False)

        # Pull the latest cloud data before loading stories from disk
        if pull_on_launch:
            try:
                await app.pull_cloud()
            except Exception as ex:
                page.show_dialog(SnackBar(f"Could not pull from the cloud, using local data. {google_drive.describe_error(ex)}"))
 
        # If a previous story was loaded, we load its route/view here
        await app.load_previous_story(page)     

        # Not pulling on launch, so push our data up instead
        if sync_on and not pull_on_launch:
            try:
                await app.push_cloud()
            except Exception as ex:
                page.show_dialog(SnackBar(f"Could not push to the cloud. {google_drive.describe_error(ex)}"))

    # If no story was loaded, Give us a basic home view
    if page.route == "/":
        page.views.append(create_home_view(page))   # Simple view so we just use a function, not a class
        page.update()


# Runs the app
ft.run(main)
