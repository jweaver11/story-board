'''
The main file to run the application.
Initializes the app, settings, page data, and renders our UI onto the page
'''

import flet as ft
from pathlib import Path
from models.app import App, AppView
from models.views.welcome import create_welcome_view, animate_welcome_text
import logging
import traceback

#logging.basicConfig(level=logging.INFO)
#logging.getLogger("flet").setLevel(logging.DEBUG)

# Remove auto updates so we can improve performance
#ft.context.disable_auto_update()#

from flet.components.component import Component

#logging.basicConfig(level=logging.INFO)

_orig_update = Component.update
_orig_before_update = Component.before_update

def _traced(orig):
    def wrapper(self):
        try:
            orig(self)
        except Exception:
            fn = getattr(self, "fn", None)
            name = f"{fn.__module__}.{fn.__qualname__}" if fn else "?"
            print(f"\n--- Component render crashed in: {name} ---")
            traceback.print_exc()
            raise
    return wrapper

Component.update = _traced(_orig_update)
Component.before_update = _traced(_orig_before_update)

def main(page: ft.Page):
    page.render_views(AppView)
    #page.on_error = lambda e: print("PAGE ERROR:", e.data)
    

# Runs the app
if __name__ == "__main__":
    ft.run(main)
