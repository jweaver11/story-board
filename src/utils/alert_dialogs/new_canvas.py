''' Used to open the overlay for creating a new canvas '''

import flet as ft
from models.views.story import Story
import os
from utils.check_widget_unique import check_widget_unique


def new_canvas_alert_dlg(page: ft.Page, story: Story, directory_path: str=None) -> ft.AlertDialog:
    ''' Creates a new alert dialog for the canvas '''

    if directory_path is None:
        directory_path = story.data.get('content_directory_path', "")

    def _size_text_field_changed(e):
        ''' Handles when the text field is changed '''
        # Set our nonlocal variables
        nonlocal canvas_data, create_button
        
        # Grab out data (key) and pass in the value to our data dict
        key = e.control.data

        # Reset error text and create_button status
        e.control.error_text = None
        create_button.disabled = False

        # If there is no value (user deleted it all), set to None
        if e.control.value == "":
            value = None
        # Otherwise, set the value
        else:
            value = int(e.control.value)

        # Check if value is 0. If it is, set error text and disable create button
        if value is not None:
            if value == 0:
                e.control.error = f"{key.capitalize()} cannot be 0"
                create_button.disabled = True
                e.control.update()  
                create_button.update()
                return
    
        # Set our data
        canvas_data[key] = value

        #print("Canvas data updated: ", canvas_data)

        if canvas_data.get('width') is None and canvas_data.get('height') is None:
            create_button.disabled = False
            create_button.update()
            return
        elif canvas_data.get('width') is None or canvas_data.get('height') is None:
            create_button.disabled = True
            create_button.update()
        

    def _new_template_selected(e):

        # Set our data for when creating the canvas
        nonlocal canvas_data
        data = e.control.data

        width_textfield.value = str(data.get('width', "")) if data.get('width') is not None else ""
        height_textfield.value = str(data.get('height', "")) if data.get('height') is not None else ""

        # Update our data we will pass into creating the canvas based on selected template
        canvas_data.update(data)
        

        # Reset the rest of the templates borders
        for control in template_controls:
            if control != e.control and isinstance(control, ft.Container):
                control.border = ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
                control.update()

        # Update our selected template border
        e.control.border = ft.Border.all(2, ft.Colors.PRIMARY)
        e.control.update()  

        # Check that the title is unique for this drawing. 
        if _check_title():
            create_button.disabled = False
        else:
            create_button.disabled = True
            page.run_task(title_textfield.focus)


    def _check_title(e=None):

        if title_textfield.value == "":
            title_textfield.error = "Name your Canvas"
            create_button.disabled = True
            title_textfield.update()
            create_button.update()
            return False
    
        # Set submitting to false, and unique to True
        nonlocal submitting, is_unique
        submitting = False
        is_unique = True

        # Grab out title and tag from the textfield, and set our new key to compare
        title = title_textfield.value
        
        # Generate our new key to compare. Requires normalization
        nk = directory_path + "\\" + title + "_" + "canvas"
        new_key = os.path.normpath(nk)

        error_text, is_unique = check_widget_unique(story, new_key)

        # If we are NOT unique, show our error text
        if not is_unique:
            title_textfield.error = error_text
            create_button.disabled = True
            title_textfield.update()
            create_button.update()
            return False
            

        # Otherwise remove our error text
        else:
            title_textfield.error = None
            create_button.disabled = False
            title_textfield.update()
            create_button.update()
            return True
            
      
    def _create_button_clicked(e):
        ''' Handles creating a new canvas when create is clicked '''
        nonlocal canvas_data
        nonlocal submitting
        nonlocal is_unique

        submitting = True

        if not _check_title():
            page.run_task(title_textfield.focus)
            return

        title = title_textfield.value if title_textfield.value != "" else f"Canvas {len(story.canvases) + 1}"

        story.create_widget(
            title=title,
            tag="canvas",
            directory_path=directory_path,
            data=canvas_data
        )

        story.data['selected_rail'] = 'canvas'
        story.save_dict()
        story.workspaces_rail.reload_rail(story)
        story.active_rail.reload_rail()

        # Build the canvas here
        page.pop_dialog()

    # Track if our name is unique for checks, and if we're submitting or not
    is_unique = True
    submitting = False

    canvas_data = {'width': None, 'height': None, 'aspect_ratio': None}       # Data we will pass set to pass in whenever a different template is selected

    create_button = ft.TextButton("Create", on_click=_create_button_clicked, disabled=True, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK))  # Button to create the canvas

    width_textfield = ft.TextField(
        label="Width", data="width", width=140, dense=True, input_filter=ft.NumbersOnlyInputFilter(), 
        max_length=4, on_change=_size_text_field_changed
    )
    height_textfield = ft.TextField(
        label="Height", data="height", width=140, dense=True, input_filter=ft.NumbersOnlyInputFilter(), 
        max_length=4, on_change=_size_text_field_changed
    )  
    title_textfield = ft.TextField(
        label="Title", data="title", width=300, autofocus=True, on_submit=_create_button_clicked,
        on_change=_check_title, capitalization=ft.TextCapitalization.WORDS,
        error="Name your Canvas"
    )

    title_textfield_container = ft.Container(title_textfield, margin=ft.Margin.only(top=6))

    template_controls = [
        ft.Container(
            content=ft.Text("Blank", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(5), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected,
            height=120, alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, width=120,
            data={'width': None, 'height': None, 'aspect_ratio': None}
        ),
        ft.Container(
            content=ft.Text("4k (3840x2160)", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(5), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected,
            height=90, alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, width=160,
            data={'width': 3840, 'height': 2160, 'aspect_ratio': None}
        ),
        ft.Container(
            content=ft.Text("2k (2560x1440)",text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(5), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected,
            height=90, alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, width=160,
            data={'width': 2560, 'height': 1440, 'aspect_ratio': None}
        ),
        ft.Container(
            content=ft.Text("HD (1920x1080)", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(5), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected,
            height=90, alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, width=160,
            data={'width': 1920, 'height': 1080, 'aspect_ratio': None}
        ),
        ft.Container(
            content=ft.Text("Banner (1500x500)", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(5), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected,
            height=90, alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, width=270,
            data={'width': 1500, 'height': 500, 'aspect_ratio': None}
        ),
        ft.Container(
            content=ft.Text("4k (2160x3840)", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(4), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected, 
            height=160, alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, width=90,
            data={'width': 2160, 'height': 3840, 'aspect_ratio': None}
        ),
        ft.Container(
            content=ft.Text("2k (1440x2560)", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(4), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected,
            height=160, alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, width=90,
            data={'width': 1440, 'height': 2560, 'aspect_ratio': None}
        ),
        ft.Container(
            content=ft.Text("HD (1080x1920)", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(4), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected, 
            height=160, alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, width=90,
            data={'width': 1080, 'height': 1920, 'aspect_ratio': None}
        ),
        ft.Container(
            content=ft.Text("Banner (500x1500)", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(4), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected,
            height=270, alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, width=90,
            data={'width': 500, 'height': 1500, 'aspect_ratio': None}
        ),
        ft.Container(
            content=ft.Text("16:9", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(4), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected,
            alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, height=90, width=160,
            data={'width': None, 'height': None, 'aspect_ratio': '16:9'}
        ),
        
        ft.Container(
            content=ft.Text("2:1", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(4), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected,
            alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, height=90, width=160,
            data={'width': None, 'height': None, 'aspect_ratio': '2:1'}
        ),
        ft.Container(
            content=ft.Text("4:3", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(4), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected,
            alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, height=120, width=160,
            data={'width': None, 'height': None, 'aspect_ratio': '4:3'}
        ),
        ft.Container(
            content=ft.Text("9:16", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(4), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected,
            alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, height=160, width=90,
            data={'width': None, 'height': None, 'aspect_ratio': '9:16'}
        ),
        
        ft.Container(
            content=ft.Text("1:2", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(4), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected,
            alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, width=90, height=160,
            data={'width': None, 'height': None, 'aspect_ratio': '1:2'}
        ),
        ft.Container(
            content=ft.Text("3:4", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(4), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected,
            alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, width=90, height=120,
            data={'width': None, 'height': None, 'aspect_ratio': '3:4'}
        ),
        ft.Container(
            content=ft.Text("1:1", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(4), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected,
            alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, width=90, height=90,
            data={'width': None, 'height': None, 'aspect_ratio': '1:1'}
        )
    ]
    

    alert_dialog = ft.AlertDialog(
        title=ft.Text("Build Your Canvas", weight=ft.FontWeight.BOLD),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor=ft.MouseCursor.CLICK)),
            create_button
        ],

        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                title_textfield_container,
                ft.Divider(),
                ft.Row([
                    template_controls[0],
                    ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER, 
                        controls=[
                            ft.Text("Custom Size:", weight=ft.FontWeight.BOLD, theme_style=ft.TextThemeStyle.LABEL_LARGE, text_align=ft.TextAlign.RIGHT, width=88),
                            width_textfield,
                            height_textfield,
                    ])
                ]),
                ft.Divider(),
                ft.Text("Common Resolutions", weight=ft.FontWeight.BOLD, theme_style=ft.TextThemeStyle.TITLE_MEDIUM, text_align=ft.TextAlign.RIGHT),
                
                ft.Row([
                    ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                        ft.Row([
                            template_controls[1],
                            template_controls[2],
                            template_controls[3],
                        ]),
                        template_controls[4],
                    
                    ]),
                    template_controls[5],
                    template_controls[6],
                    template_controls[7],
                    template_controls[8],
                ]),  

                ft.Text("Common Aspect Ratios", weight=ft.FontWeight.BOLD, theme_style=ft.TextThemeStyle.TITLE_MEDIUM, text_align=ft.TextAlign.RIGHT),
                ft.Row([
                    ft.Column([
                        template_controls[9],
                        template_controls[10],
                    ]),
                    template_controls[11],
                    template_controls[12],
                    template_controls[13],
                    template_controls[14],
                    template_controls[15],
                ])
            ])
        
    )


    return alert_dialog