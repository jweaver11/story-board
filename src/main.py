'''
The main file to run the application.
Initializes the app, settings, page data, and renders our UI onto the page
'''

import flet as ft
from pathlib import Path
from models.app import App, AppView
from models.views.welcome import create_welcome_view, animate_welcome_text

# Remove auto updates so we can improve performance
#ft.context.disable_auto_update()#

def main(page: ft.Page):
    page.render_views(AppView)
    

# Runs the app
if __name__ == "__main__":
    ft.run(main)
