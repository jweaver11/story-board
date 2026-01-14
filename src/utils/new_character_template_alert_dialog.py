import flet as ft
from models.views.story import Story

def new_character_template_alert_dlg(page: ft.Page, story: Story) -> ft.AlertDialog:
    alert_dialog = ft.AlertDialog(
        title=ft.Text("New Character Template"),
        content=ft.Column(),
    )

    return alert_dialog