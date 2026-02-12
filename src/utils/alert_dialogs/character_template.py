''' Alert dialog for creating and editing existing character templates '''
import flet as ft
from models.app import app
from models.views.story import Story

def character_template_alert_dialog(story: Story):

    async def _save_and_close(e):
        pass

    def _get_template_names() -> ft.Column:
        nonlocal existing_templates
        column = ft.Column([])

        # Delete the template
        def _delete_template(name: str):
            pass
        

        for template_name in existing_templates.keys():
            if template_name != "Default":
                column.controls.append(
                    ft.Container(
                        ft.Row([
                            ft.Text(template_name, theme_style=ft.TextThemeStyle.LABEL_LARGE, overflow=ft.TextOverflow.ELLIPSIS, width=100),
                            ft.PopupMenuButton(
                                icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.ERROR, tooltip="Delete Template", menu_padding=ft.padding.all(0),
                                items=[ft.PopupMenuItem("Confirm Delete", on_click=lambda e, name=template_name: _delete_template(name))]
                            )
                        ]),
                        on_click=lambda e: None,
                    )
                )

        return column
    
    # Grab all our existing templates
    existing_templates = app.settings.data.get('character_templates', {}).copy()

    # Set our content
    content = ft.Row(
        expand=False, height=story.p.height * .7, width=story.p.width * .5, scroll="auto",
        controls=[_get_template_names(), ft.VerticalDivider()]
    )

    # Alert dialog to show everything we've built
    dlg = ft.AlertDialog(
        title=ft.Column([ft.Text(f"Character Templates Editor"), ft.Divider()]),
        content=content,
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: story.p.close(dlg), style=ft.ButtonStyle(color=ft.Colors.ERROR), scale=1.2),
            ft.Container(width=12),   # Spacer
            ft.TextButton("Save", on_click=_save_and_close, scale=1.2),   # Start enabled to just save existing connections
        ],
    )

    return dlg