''' Alert dialog for creating and editing existing character templates '''
import flet as ft
from models.app import app
from models.views.story import Story
from models.dataclasses.character_template import default_character_template_data_dict


def character_template_alert_dialog(story: Story):

    async def _save_and_close(e):
        pass

    def _check_template_name_unique(e):
        nonlocal existing_templates, edit_container, editing_current_template, new_template_tf, can_create_template
        name = e.control.value.strip() or ""
        is_unique = name not in existing_templates.keys()
        can_create_template = is_unique and name != ""
        if not is_unique:
            e.control.error_text = "Template name already exists"
        else:
            e.control.error_text = None
            
        e.control.update()
        
    # Called when clicking create template button or pressing enter in the text field
    def _new_template_clicked(e=None):
        ''' Determines if name is valid and creates the template if it is'''
        nonlocal new_template_tf, can_create_template
        if can_create_template:
            name = new_template_tf.value.strip() or ""
            if name != "":
                _create_template(name)
                story.p.update()

    def _create_template(name: str):
        nonlocal existing_templates, edit_container, editing_current_template, new_template_tf, content
        new_template_tf.value = ""

        existing_templates[name] = default_character_template_data_dict() | {'Template Data': {}}      # Create a new empty template


        # Rebuild our template names list on the left with our newly created template selected
        new_name_column = _get_template_names()
        new_name_column.controls[-2].bgcolor = ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE_VARIANT)   # Highlight the new template
        content.controls[0] = new_name_column      # Rebuild the template names list

        # Rebuild our edit container with new template
        edit_container.content = ft.Text(f"{name}", expand=True, theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM, text_align=ft.TextAlign.CENTER)
        content.update()

    def load_template(name: str = None) -> ft.Control:

        if name is None:
            return ft.Column(
                [ft.Text("Select a template to start editing", expand=True, theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM, text_align=ft.TextAlign.CENTER)],
                expand=True, scroll="auto", alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        
        # Load our name and data for the template we're loading/editing
        template_name, template_data = None, None
        for tn, td in existing_templates.items():
            if tn == name:
                template_name = tn
                template_data = td
                break
                
        # Error handling
        if template_name is None or template_data is None:
            return
        
        column1, column2 = ft.Column([], expand=True), ft.Column([], expand=True)
        
        column = ft.Column([
            ft.Text(f"Editing template: {name}", expand=True, theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM, text_align=ft.TextAlign.CENTER),
            ft.Row([column1, ft.Divider(), column2], expand=True,)
        ], expand=True, scroll="auto", alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        return column


    # Gets our template names as a column on the left side of the dialog
    def _get_template_names() -> ft.Column:
        nonlocal existing_templates, edit_container, editing_current_template, new_template_tf
        column = ft.Column([], width=200)


        def _edit_template(name: str, e):
            nonlocal existing_templates, edit_container, editing_current_template, column
            
            editing_current_template = name
            e.control.bgcolor = ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE_VARIANT)
            for ctrl in column.controls:   
                if isinstance(ctrl, ft.Container) and ctrl != e.control:
                    ctrl.bgcolor = "transparent"
            
            # Load the template into our edit container
            edit_container.content = load_template(name)
            story.p.update()
           

        # Delete the template
        def _delete_template(name: str):
            nonlocal existing_templates, edit_container, editing_current_template
            if name in existing_templates:
                del existing_templates[name]        # Remove it from our local data we're manipulating
                for ctrl in column.controls:        # Remove it visually
                    if isinstance(ctrl, ft.Container) and ctrl.content and isinstance(ctrl.content, ft.Row) and ctrl.content.controls and isinstance(ctrl.content.controls[0], ft.Text) and ctrl.content.controls[0].value == name:
                        column.controls.remove(ctrl)
                        break

                if editing_current_template == name:     # If we're currently editing this template, reset our edit container
                    edit_container.content = ft.Text("Select a template to edit it or click the + button to create a new one.")
                    editing_current_template = ""

                story.p.update()
            
        
        # Create a nameplace for each template
        for template_name in existing_templates.keys():
            if template_name != "Default":
                column.controls.append(
                    ft.Container(
                        ft.Row([
                            ft.Text(
                                template_name, theme_style=ft.TextThemeStyle.LABEL_LARGE, expand=True,
                                tooltip=f"Edit {template_name}", overflow=ft.TextOverflow.ELLIPSIS, 
                            ),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, tooltip="Delete Template", on_click=lambda e, name=template_name: _delete_template(name))
                        ]),
                        on_click=lambda e, name=template_name: _edit_template(name, e), padding=ft.padding.only(left=6), border_radius=6
                    )
                )

        
            
        column.controls.append(
           
            ft.Row([
                new_template_tf,
                ft.IconButton(ft.Icons.ADD, on_click=_new_template_clicked),
            ], alignment=ft.MainAxisAlignment.CENTER)
            
        )

        return column
    
    # Grab all our existing templates
    existing_templates = app.settings.data.get('character_templates', {}).copy()        # Copy our data for ez manipulation without saving until the end
    editing_current_template: str = ""
    can_create_template = False     # Check if we can create a template based on unique name or not

    edit_container = ft.Container(
        expand=True, 
        content=load_template()
    )
    new_template_tf = ft.TextField(
        label="Template Name", dense=True, expand=True, capitalization=ft.TextCapitalization.WORDS, 
        on_change=_check_template_name_unique, on_submit=_new_template_clicked,
    )

    
    # Set our content
    content = ft.Row(
        expand=False, height=story.p.height * .7, width=story.p.width * .5, scroll="auto",
        controls=[_get_template_names(), ft.VerticalDivider(width=2), edit_container]
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