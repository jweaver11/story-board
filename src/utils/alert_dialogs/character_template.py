''' Alert dialog for creating and editing existing character templates '''
import flet as ft
from models.app import app

def character_template_alert_dialog(page: ft.Page):

    async def _save_and_close(e):
        pass

    # Set our content
    content = ft.Column(
        expand=False, height=page.height * .7, width=page.width * .5, scroll="auto"
    )

    # Alert dialog to show everything we've built
    dlg = ft.AlertDialog(
        title=ft.Text(f"Character Templates Editor"),
        content=ft.AutofillGroup(content),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: page.close(dlg), style=ft.ButtonStyle(color=ft.Colors.ERROR), scale=1.2),
            ft.Container(width=12),   # Spacer
            ft.TextButton("Save", on_click=_save_and_close, scale=1.2),   # Start enabled to just save existing connections
        ],
    )

    return dlg