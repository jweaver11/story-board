''' Used to open the overlay for creating a new canvas '''

import flet as ft
from models.views.story import Story
import os


def new_canvas_alert_dlg(page: ft.Page, story: Story, directory_path: str=None) -> ft.AlertDialog:
    ''' Creates a new alert dialog for the canvas '''

    if directory_path is None:
        directory_path = story.data.get('content_directory_path', "")

    def show_error(message: str):
        nonlocal error_text, create_button
        create_button.disabled = True
        error_text.value = message
        error_text.visible = True
        create_button.update()
        error_text.update()
        pass

    def check_width(e=None) -> bool:
        nonlocal canvas_data, create_button, width_textfield, error_text
        new_width = width_textfield.value

        # If there is no value (user deleted it all), set to None
        if new_width == "":
            new_width = None
        else:
            new_width = int(new_width)

        # Check width not empty
        if new_width is None:
            show_error("Width must be set")
            return False

        # Check width not 0
        if new_width < 400:
            show_error("Width must be greater than 400")
            return False
                
        # Update data
        canvas_data.update({'width': new_width})

        # Reset errors
        error_text.value = ""
        error_text.visible = False
        create_button.disabled = False
        create_button.update()
        error_text.update()

        #print("Canvas data updated: ", canvas_data)

        return True
        

    def check_height(e=None) -> bool:
        ''' Handles when the text field is changed '''
        # Set our nonlocal variables
        nonlocal canvas_data, create_button, height_textfield, error_text
        new_height = height_textfield.value

        # If there is no value (user deleted it all), set to None
        if new_height == "":
            new_height = None
        else:
            new_height = int(new_height)

        # Check height not empty
        if new_height is None:
            show_error("Height must be set")
            return False
        # Check height not 0
        if new_height < 400:
            show_error("Height must be greater than 400")
            return False

        # Update data
        canvas_data.update({'height': new_height})

        # Reset errors
        error_text.value = ""
        error_text.visible = False
        create_button.disabled = False
        create_button.update()
        error_text.update()

        print("Canvas data updated: ", canvas_data)
        return True

    # When we select one of our template boxes. Updates data and UI to reflect
    def _new_template_selected(e: ft.Event[ft.Container]):

        # Set our data for when creating the canvas
        nonlocal canvas_data, width_textfield, height_textfield
        data = e.control.data

        width_textfield.value = str(data.get('width', "")) if data.get('width') is not None else ""
        height_textfield.value = str(data.get('height', "")) if data.get('height') is not None else ""

        # Update our data we will pass into creating the canvas based on selected template
        canvas_data.update(data)
        print("Canvas data updated: ", canvas_data)
        

        # Reset the rest of the templates borders
        for control in template_controls:
            if control != e.control and isinstance(control, ft.Container):
                control.border = ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
                control.update()

        # Update our selected template border
        e.control.border = ft.Border.all(2, ft.Colors.PRIMARY)
        e.control.update()  
        width_textfield.update()
        height_textfield.update()


        
    # Does final size checks then creates the canvas and closes the dialog
    async def create_canvas(e=None):
        ''' Handles creating a new canvas when create is clicked '''
        nonlocal canvas_data

        # Check sizing is valid
        if check_width() is False:
            return
        if check_height() is False:
            return
        

        title = title_textfield.value if title_textfield.value != "" else f"New canvas"

        await story.create_widget(
            title=title,
            tag="canvas",
            directory_path=directory_path,
            data=canvas_data
        )

        # Build the canvas here
        page.pop_dialog()


    canvas_data = {'width': None, 'height': None}       # Data we will pass set to pass in whenever a different template is selected

    create_button = ft.TextButton("Create", on_click=create_canvas, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK))  # Button to create the canvas

    width_textfield = ft.TextField(
        value=str(1920), label="Width", data="width", width=140, dense=True, input_filter=ft.NumbersOnlyInputFilter(), 
        max_length=4, on_change=check_width
    )
    height_textfield = ft.TextField(
        value=str(1080),label="Height", data="height", width=140, dense=True, input_filter=ft.NumbersOnlyInputFilter(), 
        max_length=4, on_change=check_height
    )  
    title_textfield = ft.TextField(
        label="Title", data="title", autofocus=True, on_submit=create_canvas,
        capitalization=ft.TextCapitalization.WORDS, margin=ft.Margin.only(top=6)
    )
    error_text = ft.Text("", visible=False, color=ft.Colors.ERROR, size=14, italic=True, weight=ft.FontWeight.W_500)

    template_controls = [
        ft.Container(
            content=ft.Text("4k\n3840 x 2160\n16:9", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(5), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected,
            height=90, alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, width=160,
            data={'width': 3840, 'height': 2160, 'aspect_ratio': None}
        ),
        ft.Container(
            content=ft.Text("2k\n2560 x 1440\n16:9",text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(5), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected,
            height=90, alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, width=160,
            data={'width': 2560, 'height': 1440, 'aspect_ratio': None}
        ),
        ft.Container(
            content=ft.Text("HD\n1920 x 1080\n16:9", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(5), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected,
            height=90, alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, width=160,
            data={'width': 1920, 'height': 1080, 'aspect_ratio': None}
        ),
        ft.Container(
            content=ft.Text("Banner\n1500 x 500\n3:1", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(5), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected,
            height=90, alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, width=270,
            data={'width': 1500, 'height': 500, 'aspect_ratio': None}
        ),
        ft.Container(
            content=ft.Text("4k\n2160 x 3840\n9:16", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(4), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected, 
            height=160, alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, width=90,
            data={'width': 2160, 'height': 3840, 'aspect_ratio': None}
        ),
        ft.Container(
            content=ft.Text("2k\n1440 x 2560\n9:16", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(4), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected,
            height=160, alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, width=90,
            data={'width': 1440, 'height': 2560, 'aspect_ratio': None}
        ),
        ft.Container(
            content=ft.Text("HD\n1080 x 1920\n9:16", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(4), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected, 
            height=160, alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, width=90,
            data={'width': 1080, 'height': 1920, 'aspect_ratio': None}
        ),
        ft.Container(
            content=ft.Text("Vertical Banner\n500 x 1500\n1:3", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(4), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected,
            height=270, alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, width=90,
            data={'width': 500, 'height': 1500, 'aspect_ratio': None}
        ),
        ft.Container(
            content=ft.Text("Logo\n(400x400)\n1:3", text_align=ft.TextAlign.CENTER), padding=ft.Padding.all(4), border_radius=4,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), on_click=_new_template_selected,
            height=90, alignment=ft.Alignment.TOP_CENTER, bgcolor=ft.Colors.SURFACE, width=90,
            data={'width': 400, 'height': 400, 'aspect_ratio': None}
        ),
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
                title_textfield,
                ft.Divider(),
                
                    
                ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER, 
                    controls=[
                        ft.Text("Custom Size:", weight=ft.FontWeight.BOLD, theme_style=ft.TextThemeStyle.LABEL_LARGE, text_align=ft.TextAlign.RIGHT, width=88),
                        width_textfield,
                        height_textfield,
                        error_text
                    ], tight=True),
                
                ft.Divider(),
                ft.Text("Common Resolutions", weight=ft.FontWeight.BOLD, theme_style=ft.TextThemeStyle.TITLE_MEDIUM, text_align=ft.TextAlign.RIGHT),
                
                ft.Row([
                    ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER, tight=True,
                        controls=[
                        ft.Row([
                            template_controls[0],
                            template_controls[1],
                            template_controls[2],
                        ]),
                        template_controls[3],
                    
                    ]),
                    template_controls[4],
                    template_controls[5],
                    template_controls[6],
                    template_controls[7],
                    template_controls[8],
                ]),  

               
            ])
        
    )


    return alert_dialog