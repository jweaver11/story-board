'''
Most model classes really container 2 models: the character model itself and the associated widget model.
Inside of the 'data' dict, we store our characters model for the manipulative data...
the app will change. Everything else is built upon program launch so we can display it in the UI.
'''

import flet as ft
import os
from models.widget import Widget
from models.views.story import Story
from models.app import app
from utils.safe_string_checker import return_safe_name

import flet.canvas as cv
import asyncio
from styles.text_fields import TextField, NoLabelTextField
from models.dataclasses.character_template import default_character_template_data
import flet_shadcn_ui as shad
from styles.highlight_button import HighlightButton



class Character(Widget):
    # Constructor
    def __init__(self, name: str, directory_path: str, story: Story, data: dict={}, is_new: bool = False):

        # Parent class constructor
        super().__init__(
            title = name,  
            directory_path = directory_path, 
            story = story,   
            data = data,   
            is_new = is_new 
        )

        # If we're new, give default values for our data 
        if self.is_new == True:
            self.data.update({
                # Widget data
                'tag': "character",
                'color': app.settings.data.get('widget_defaults', {}).get('character', {}).get('color'),

                'character_data': app.settings.data.get('character_template', default_character_template_data()),

            })         

    # Called after any changes happen to the data that need to be reflected in the UI
    def build(self): #this is the edit view currently
        ''' Reloads/Rebuilds our widget based on current data '''

        super().build()

        if self.page.platform.is_mobile() != True:
            self.padding = ft.Padding.all(10)


        # Called when a field is changed in edit mode
        def update_character_data(**kwargs):
            ''' Updates the character data dict or up to one sub dict '''

            for key, value in kwargs.items():
                if 'character_data' not in self.data:
                    self.data['character_data'] = {}

                if key in self.data['character_data']:
                    self.data['character_data'][key] = value
                else:
                    # Check if this key is in a sub dict, and update it there if it is
                    for sub_key, sub_dict in self.data['character_data'].items():
                        if isinstance(sub_dict, dict) and key in sub_dict:
                            self.data['character_data'][sub_key][key] = value
                            break
            
            self.update_data(**{'character_data': self.data['character_data']})  # Save our updated character data dict
        
        # Called by button to create a new section. Just shows our text field to enter the section name
        async def add_section_clicked(e: ft.Event=None):
            nonlocal new_section_tf, new_section_button
            new_section_button.visible = False
            new_section_tf.visible = True
            new_section_tf.value = ""
            new_section_tf.error = None
            new_section_button.update()
            new_section_tf.update()
            await new_section_tf.focus()

        # Called when bluring the new section text field
        async def hide_new_section_tf(e: ft.Event=None):
            nonlocal new_section_tf, new_section_button
            new_section_tf.visible = False
            new_section_tf.value = ""
            new_section_tf.error = None
            new_section_tf.update()
            new_section_button.visible = True
            new_section_button.update()

        # Called when pressing enter on the new section text field or when it loses focus
        async def create_new_section(e: ft.Event=None):
            nonlocal new_section_tf, data_column
            

            # Grab our section name
            section_name = return_safe_name(new_section_tf.value)
            
            # If name is empty, just hide the text field and return
            if not section_name:
                self.page.show_dialog(shad.Toast("Section name cannot be empty.", variant=shad.ToastVariant.DESTRUCTIVE))
                return  
            
            # If section name already exists, show that as error
            if section_name in self.data['character_data']:
                self.page.show_dialog(shad.Toast("Section name already exists.", variant=shad.ToastVariant.DESTRUCTIVE))
                return  
            
            # Otherwise we passed checks, add it to data
            self.data['character_data'][section_name] = {}
            self.update_data(**{'character_data': self.data['character_data']})  # Save our updated character data dict 

            new_section_button.visible = True
            new_section_button.update()
            
            # Add new container for the section info
            data_column.controls.pop()
            data_column.controls.pop()
            data_column.controls.extend(create_section_ctrl(section_name, self.data['character_data'][section_name]))
            data_column.controls.append(new_section_button)
            data_column.controls.append(new_section_tf)
            
            data_column.update()
            await asyncio.sleep(0.02)
            await data_column.scroll_to(offset=-1, duration=200)  # Scroll to bottom
            
        # Deletes an entire section from our data dict
        async def delete_section(e: ft.Event):
            ''' Deletes an entire section from the character data dict '''
            nonlocal data_column
            section_name = e.control.data
            del self.data['character_data'][section_name]
            self.update_data(**{'character_data': self.data['character_data']})  # Save our updated character data dict

            # Grab the data_column's column control to remove the label and section container from the UI and update
            for ctrl in reversed(data_column.controls): # Work backwards so we don't skip any controls when removing
                if ctrl.data == section_name:
                    data_column.controls.remove(ctrl)
            data_column.update()   

        # Creates the new field
        async def create_new_field(e: ft.Event[ft.TextField]): #show in edit view 
            '''Called when user confirms the field name'''
            nonlocal data_column
            section = e.control.data
            field_name = return_safe_name(e.control.value)
            
            # Add the field to data if it doesn't exist
            if field_name and field_name not in self.data['character_data'][section]:
                empty_section = self.data['character_data'].get(section, {}) == {}  # Check if this is the first field being added
                self.data['character_data'][section][field_name] = ""
            else:
                self.page.show_dialog(shad.Toast("Field name already exists or is blank.", variant=shad.ToastVariant.DESTRUCTIVE))
                return
            
            # Save and reload
            self.update_data(**{'character_data': self.data['character_data']})  # Save our updated character data dict
            
            # Add new field to the UI
            # Find the parent column for this section so we can add field info to it
            parent_column = None  
            for ctrl in data_column.controls:
                if isinstance(ctrl, ft.Container) and ctrl.data == section:
                    parent_column = ctrl.content
            if not parent_column:
                return
            
            # Set new control to add
            row_ctrl = create_field_ctrl(section, field_name, "")
            # If this is the first field being added, remove the no fields text and delete section button
            if empty_section:   
                parent_column.controls.pop(0)
            parent_column.controls.append(row_ctrl)
            parent_column.update()  

            new_section_button.visible = True
            new_section_button.update()


        # Deletes a field from our character data dict
        async def delete_field(e: ft.Event[ft.Button]):
            ''' Deletes fields from the character data dict or up to one sub dict '''
            section_name, field_name = e.control.data

            del self.data['character_data'][section_name][field_name]
            self.update_data(**{'character_data': self.data['character_data']})  # Save our updated character data dict

            # Reference the column that holds this field in case we're the last field being deleted so we can reference it later
            body: ft.Column = e.control.parent.parent 

            # Remove the row from the column UI and update
            body.controls.remove(e.control.parent)  
            body.parent.update()   

            # Check the length of parent, if its empty, add our no fields text and delete section button
            if len(self.data['character_data'][section_name]) == 0:
                body.controls.append(
                    ft.Row([ft.Text("Click the button above to add fields to this section", italic=True, color=ft.Colors.ON_SURFACE_VARIANT)])
                )
                body.update()

        def create_field_ctrl(section_name: str, field_name: str, field_value: str) -> ft.Control:
            return ft.Row(
                spacing=0, vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Text(f"{field_name}:", size=14, selectable=True, weight=ft.FontWeight.BOLD,),    # Label
                    NoLabelTextField(   # Field value tf
                        field_value, expand=True, cursor_color=ft.Colors.PRIMARY,
                        on_blur=lambda e, fn=field_name: update_character_data(**{fn: e.control.value}), 
                    ),
                    ft.Container(   # Delete button
                        ft.Icon(ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR),
                        on_click=delete_field, 
                        data=(section_name, field_name), ink=True, shape=ft.BoxShape.CIRCLE,
                        tooltip=f"Delete Field: {field_name}", 
                    )
                ]
            )

        def create_section_ctrl(section_name: str, section_data: dict) -> list[ft.Control]:

            def hide_new_field_tf(e=None):
                new_field.visible = False
                new_field.value = ""
                new_field.update()

            async def show_new_field_tf(e=None):
                new_field.visible = True
                new_field.update()
                await new_field.focus()

            # Set a label and container to hold our text spans for each section
            label_ctrl = ft.Row([
                ft.Text(f"\t\t{section_name}", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=18)),   # Title
                shad.ContextMenu(   # Options button
                    HighlightButton(ft.Icon(ft.Icons.MORE_VERT, ft.Colors.PRIMARY), use_padding=True, is_round=True),
                    [
                        shad.MenuItem("New Field", ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY, 20), on_click=show_new_field_tf),
                        shad.Separator(ft.Margin.symmetric(vertical=4)),
                        shad.MenuItem("Delete Section", ft.Icon(ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR, 20), on_click=delete_section, data=section_name,),
                    ],
                    open_on_tap=True
                ),
                new_field := ft.TextField(  # Tf for naming new fields
                    label="New Field Name", capitalization=ft.TextCapitalization.SENTENCES, visible=False,
                    on_submit=create_new_field, on_blur=hide_new_field_tf, dense=True, bgcolor=ft.Colors.SURFACE,
                    data=section_name   # Gets set when we click the new field button for a specific section
                )
            ], spacing=0, data=section_name)

            data_ctrl = ft.Container(         # For template data
                padding=ft.Padding.all(6), border_radius=4, expand=True,
                #border=ft.Border.all(2, ft.Colors.OUTLINE_VARIANT), 
                margin=ft.Margin.only(left=10, bottom=10, right=10),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                content=ft.Column(
                    [
                        create_field_ctrl(section_name, field_name, field_value) for field_name, field_value in section_data.items()
                    ] if section_data else [
                        ft.Row([ft.Text("Click the button above to add fields to this section", italic=True, color=ft.Colors.ON_SURFACE_VARIANT)])
                    ],
                    tight=True, spacing=4
                ),
                data=section_name
            )

            return [label_ctrl, data_ctrl]


        def load_data_ctrls() -> list[ft.Control]:
            ''' Loads data from a dict into a given container '''

            # Our list of controls that will be added to the body column
            control_list = []   
            
            # Go through our sections inside of our character data
            for section_name, section_data in self.data.get('character_data', {}).items():

                # Error handling
                if not isinstance(section_data, dict):
                    continue       

                control_list.extend(create_section_ctrl(section_name, section_data))         

                # Container to hold the text control of our section info
                

            return control_list


        # Adjust our description text field to match the theme outside of a sidebar
        self.description_tf.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
        
        # Header that holds our image, edit mode button
        header = ft.Row([
            self.select_image_button,
            self.description_tf
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)


        # Body that holds the rest of our widget
        data_column = ft.Column(
            controls=[header],
            scroll="auto", expand=True, spacing=0
        )
        new_section_button = ft.Button(
            "Add Section", bgcolor=ft.Colors.SURFACE,
            on_click=add_section_clicked, margin=ft.Margin.only(left=10),
            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, shape=ft.RoundedRectangleBorder(radius=4), text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=20)),
        )

        new_section_tf = ft.TextField(
            autofocus=True, label="Section Name", capitalization=ft.TextCapitalization.WORDS, visible=False,
            on_submit=create_new_section, on_blur=hide_new_section_tf, dense=True, bgcolor=ft.Colors.SURFACE,
            margin=ft.Margin.only(left=10),
        )

        # Load in our character data controls after the header
        data_column.controls.extend(load_data_ctrls())
        data_column.controls.append(new_section_button)
        data_column.controls.append(new_section_tf)

        self.content = ft.Stack([
            data_column,
            ft.Column([
                new_section_button,
                new_section_tf, 
            ], alignment=ft.MainAxisAlignment.END, horizontal_alignment=ft.CrossAxisAlignment.END, expand=True,)
        ], alignment=ft.Alignment.TOP_RIGHT, expand=True)

        self.content = data_column
            