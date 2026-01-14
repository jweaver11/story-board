'''
Alert Dialog for creating new character templates. For now, this only has the ability...
to add keys to 'character_data' with string values. More complex data types may be added later.
'''

import flet as ft
from models.app import app

def new_character_template_alert_dlg(page: ft.Page) -> ft.AlertDialog:

    def _check_template_name_unique(e):
        title = e.control.value.strip() 

        if title == "":
            create_button.disabled = True
            e.control.error_text = "Template name cannot be empty"
            page.update()
            return
        
        for template in app.settings.data.get('character_templates', {}).values():
            
            if template.get('title', "") == title:
                create_button.disabled = True
                e.control.error_text = "Template name must be unique"
                page.update()
                return
            
        e.control.error_text = None
        create_button.disabled = False
        nonlocal template_name  
        template_name = title
        page.update()

    def _new_template_name_submitted(e):
        app.settings.create_character_template(template_name, template_data)
        page.close(alert_dialog)


    def _new_field_submitted(e):
        field_name = new_field_textfield.value.strip()

        if field_name == "":
            return
        
        # Check for uniqueness
        for key in template_data.keys():
            if key == field_name:
                new_field_textfield.error_text = "Field name must be unique"
                new_field_textfield.focus()
                return  # Not unique, do nothing
            

        # Add the field to our template data
        template_data[field_name] = ""

        # If we passed the checks, add our field to the list
        alert_dialog.content.controls.insert(-1, ft.Row([ft.Container(width=0), ft.Text(field_name)]))
        new_field_textfield.value = ""
        page.update()
        new_field_textfield.focus()

    # Our data we will maniuplate before creating the template
    template_data = {}

    new_field_textfield = ft.TextField(
        label="New Field Name", expand=True,
        capitalization=ft.TextCapitalization.SENTENCES,
        on_submit=_new_field_submitted, dense=True,
        #on_change=_check_field_name_unique
    ) 

    # Buttons for submitting new fields and for creating the template
    new_field_submit_button = ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, on_click=_new_field_submitted)
    create_button = ft.TextButton(text="Create", disabled=True, on_click=_new_template_name_submitted)  

    template_name: str = ""

    alert_dialog = ft.AlertDialog(
        title=ft.Text("New Character Template"),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: page.close(alert_dialog), style=ft.ButtonStyle(color=ft.Colors.ERROR)),
            create_button
        ],
        content=ft.Column([
             ft.TextField(
                label="Template Name", capitalization=ft.TextCapitalization.SENTENCES,
                hint_text="e.g. 'Shonen Hero'", #expand=True,
                autofocus=True, on_change=_check_template_name_unique
            ),
            ft.Text("Current Fields:", theme_style=ft.TextThemeStyle.LABEL_LARGE),
            ft.Row([new_field_textfield, new_field_submit_button]),
        ])
    )
    


    return alert_dialog