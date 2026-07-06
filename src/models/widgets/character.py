'''
Most model classes really container 2 models: the character model itself and the associated widget model.
Inside of the 'data' dict, we store our characters model for the manipulative data...
the app will change. Everything else is built upon program launch so we can display it in the UI.
'''

import flet as ft
import os
from models.widget import Widget
from models.views.story import Story
from utils.verify_data import verify_data
from models.mini_widgets.character_connection import CharacterConnection
from models.app import app
from utils.safe_string_checker import return_safe_name
from models.dataclasses.character_template import default_character_template_data_dict
from utils.alert_dialogs.character_connection import new_character_connection_clicked
import flet.canvas as cv
import asyncio
from styles.text_fields import TextField, NoLabelTextField
from styles.snack_bar import SnackBar




# Sets our Character as an extended Widget object, which is a subclass of a flet Container
# Widget requires a title, tag, page reference, and a pin location
class Character(Widget):
    # Constructor
    def __init__(self, name: str, directory_path: str, story: Story, data: dict=None, is_new: bool = False):

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
                'color': app.settings.data.get('default_character_color'),
 
                # State and view data
                'image_base64': str(),    # Saves our icon as img64 string 

                # Character data
                'about': "",
                # If this dict doesn't exist, we create it with our active template data. If we fail to pull that, we use a default template (which has quite a lot)
                'character_data': app.settings.data.get('character_templates', {}).get(app.settings.data.get('active_character_template', ""), default_character_template_data_dict()) 
                if data is None or 'character_data' not in data else data['character_data'],

                'charts': {}
            }) 

        


    # TODO: RENAME AND DELETE Will need to be unique here, to alter ccm and connections that used our old name and key
        

    # Called after any changes happen to the data that need to be reflected in the UI
    def build(self): #this is the edit view currently
        ''' Reloads/Rebuilds our widget based on current data '''

        self.padding = ft.Padding.all(16)   # Set padding

        # Rebuild out tab to reflect any changes
        self.create_tab()


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
        async def new_section_clicked(e: ft.Event=None):
            nonlocal new_section_tf, new_section_button
            new_section_button.visible = False
            new_section_tf.visible = True
            new_section_tf.value = ""
            new_section_tf.error = None
            new_section_tf.update()
            await new_section_tf.focus()
            new_section_button.update()

        # Called when bluring the new section text field
        async def hide_new_section_tf(e: ft.Event=None):
            nonlocal new_section_tf, new_section_button
            new_section_button.visible = True
            new_section_button.update()
            new_section_tf.visible = False
            new_section_tf.value = ""
            new_section_tf.error = None
            new_section_tf.update()

        # Called when pressing enter on the new section text field or when it loses focus
        async def create_new_section(e: ft.Event=None):
            nonlocal new_section_tf, body
            

            # Grab our section name
            section_name = return_safe_name(new_section_tf.value)
            
            # If name is empty, just hide the text field and return
            if not section_name:
                return  
            
            # If section name already exists, show that as error
            if section_name in self.data['character_data']:
                self.page.show_dialog(SnackBar("Section name already exists!"))
                return  
            
            # Otherwise we passed checks, add it to data
            self.data['character_data'][section_name] = {}
            self.update_data(**{'character_data': self.data['character_data']})  # Save our updated character data dict 

            # Add new label for the section name
            body.controls.append(
                ft.Row([
                    ft.Text(f"\t\t{section_name}", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=18), color=self.data.get('color', None)),
                    ft.IconButton(
                        tooltip="Add New Field", icon=ft.Icons.NEW_LABEL_OUTLINED, mouse_cursor="click",
                        on_click=new_field_clicked, icon_color=self.data.get('color', None),
                        data=section_name
                    ),
                ], spacing=0, data=section_name))
            
            new_section_button.visible = True
            new_section_button.update()
            
            # Add new container for the section info
            body.controls.append(
                ft.Container(         # For template data
                    padding=ft.Padding.all(6), border_radius=ft.BorderRadius.all(10), expand=True,
                    border=ft.Border.all(2, ft.Colors.OUTLINE_VARIANT),
                    margin=ft.Margin.only(left=10, bottom=10, right=10),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    content=ft.Column(
                        [
                            ft.Row([
                                ft.Text("No fields yet. Click the button above to add one, or", italic=True, color=ft.Colors.ON_SURFACE_VARIANT),
                                ft.TextButton(
                                    "Delete Section",
                                    on_click=delete_section, data=section_name,
                                    style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ERROR)
                                )
                            ], spacing=0)
                        ], tight=True, spacing=0),
                    data=section_name
                )
            )
            
            body.update()
            await body.scroll_to(offset=-1, duration=200)  # Scroll to bottom
            
        # Deletes an entire section from our data dict
        async def delete_section(e: ft.Event):
            ''' Deletes an entire section from the character data dict '''
            nonlocal body
            section = e.control.data
            del self.data['character_data'][section]
            self.update_data(**{'character_data': self.data['character_data']})  # Save our updated character data dict

            # Grab the body's column control to remove the label and section container from the UI and update
            for ctrl in reversed(body.controls): # Work backwards so we don't skip any controls when removing
                if ctrl.data == section:
                    body.controls.remove(ctrl)
            body.update()   

        async def new_field_clicked(e: ft.Event):
            ''' Opens the new field text field when clicking the add new field button on a section '''
            nonlocal new_field_tf, new_section_button
            new_section_button.visible = False
            new_section_button.update()
            section = e.control.data
            new_field_tf.data = section   # Set the section as data on the text field so we know which section to add the field to when we submit
            new_field_tf.visible = True
            new_field_tf.value = ""
            new_field_tf.error = None
            new_field_tf.update()
            await new_field_tf.focus()
        
        # Creates the new field
        async def create_new_field(e: ft.Event): #show in edit view 
            '''Called when user confirms the field name'''
            nonlocal new_field_tf, body
            section = e.control.data
            field_name = return_safe_name(e.control.value)
            
            # Add the field to data if it doesn't exist
            if field_name and field_name not in self.data['character_data'][section]:
                empty_section = self.data['character_data'].get(section, {}) == {}  # Check if this is the first field being added
                self.data['character_data'][section][field_name] = ""
            else:
                self.page.show_dialog(SnackBar("Field name already exists or is invalid!"))
                return
            
            # Save and reload
            self.update_data(**{'character_data': self.data['character_data']})  # Save our updated character data dict
            
            # Add new field to the UI
            # Find the parent column for this section so we can add field info to it
            parent_column = None  
            for ctrl in body.controls:
                if isinstance(ctrl, ft.Container) and ctrl.data == section:
                    parent_column = ctrl.content
            if not parent_column:
                return
            
            
            # Set new control to add
            row_ctrl = ft.Row(spacing=0, vertical_alignment=ft.CrossAxisAlignment.START)

            # Add text label for the field name
            row_ctrl.controls.append(
                ft.Text(f"{field_name}:\t", size=16, selectable=True, weight=ft.FontWeight.BOLD)
            )
            # Add textfield we can change
            row_ctrl.controls.append(
                NoLabelTextField(
                    "", expand=True, cursor_color=self.data.get('color', None),
                    on_blur=lambda e, k=field_name: update_character_data(**{k: e.control.value}), 
                ),
            )
            # Add delete button at the end which is small
            row_ctrl.controls.append(
                ft.Container(
                    ft.Icon(
                        ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR,
                    ),
                    on_click=delete_field, 
                    data=(section, field_name), ink=True, shape=ft.BoxShape.CIRCLE,
                    tooltip=f"Delete Field: {field_name}", 
                )
            )
            # If this is the first field being added, remove the no fields text and delete section button
            if empty_section:   
                parent_column.controls.pop(0)
            parent_column.controls.append(row_ctrl)
            parent_column.update()  

            new_section_button.visible = True
            new_section_button.update()


        # Deletes a field from our character data dict
        async def delete_field(e: ft.Event):
            ''' Deletes fields from the character data dict or up to one sub dict '''
            section, key = e.control.data

            del self.data['character_data'][section][key]
            self.update_data(**{'character_data': self.data['character_data']})  # Save our updated character data dict

            # Reference the column that holds this field in case we're the last field being deleted so we can reference it later
            body = e.control.parent.parent 

            # Remove the row from the column UI and update
            body.controls.remove(e.control.parent)  
            body.parent.update()   

            # Check the length of parent, if its empty, add our no fields text and delete section button
            if len(self.data['character_data'][section]) == 0:
                body.controls.append(
                    ft.Row([
                        ft.Text("No fields yet. Click the button above to add one, or", italic=True, color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.TextButton(
                            "Delete Section",
                            on_click=delete_section, data=section,
                            style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ERROR)
                        )
                    ], spacing=0, data=section)
                )
                body.update()

        # Hides the new field text field when it loses focus
        async def hide_new_field_tf(e: ft.Event):
            nonlocal new_field_tf, new_section_button
            new_section_button.visible = True
            new_section_button.update()
            new_field_tf.visible = False
            new_field_tf.value = ""
            new_field_tf.error = None
            new_field_tf.data = None
            new_field_tf.update()


        def _load_character_data_controls() -> list[ft.Control]:
            ''' Loads data from a dict into a given container '''


            # Our list of controls that will be added to the body column
            control_list = []   
            
            # Go through our sections inside of our character data
            for section, values in self.data.get('character_data', {}).items():

                # Skip non-dict sections 
                if not isinstance(values, dict):
                    continue

                # Set a label and container to hold our text spans for each section
                label = ft.Row([
                    ft.Text(f"\t\t{section}", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=18), color=self.data.get('color', None)),
                    ft.IconButton(
                        tooltip="Add New Field", icon=ft.Icons.NEW_LABEL_OUTLINED, mouse_cursor="click",
                        on_click=new_field_clicked, icon_color=self.data.get('color', None),
                        data=section
                    ),
                ], spacing=0, data=section)
                

                # Container to hold the text control of our section info
                container = ft.Container(         # For template data
                    padding=ft.Padding.all(6), border_radius=ft.BorderRadius.all(10), expand=True,
                    border=ft.Border.all(2, ft.Colors.OUTLINE_VARIANT), 
                    margin=ft.Margin.only(left=10, bottom=10, right=10),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    content=ft.Column(tight=True, spacing=0),
                    data=section
                )
                for key, value in values.items():

                    row_ctrl = ft.Row(spacing=0, vertical_alignment=ft.CrossAxisAlignment.START)

                    if isinstance(value, str):
                        # Add text label for the field name
                        row_ctrl.controls.append(
                            ft.Text(f"{key}:\t", size=16, selectable=True, weight=ft.FontWeight.BOLD,)
                        )
                        # Add textfield we can change
                        row_ctrl.controls.append(
                            NoLabelTextField(
                                value, expand=True, cursor_color=self.data.get('color', None),
                                on_blur=lambda e, k=key: update_character_data(**{k: e.control.value}), 
                            ),
                        )
                        # Add delete button at the end which is small
                        row_ctrl.controls.append(
                            ft.Container(
                                ft.Icon(
                                    ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR,
                                ),
                                on_click=delete_field, 
                                data=(section, key), ink=True, shape=ft.BoxShape.CIRCLE,
                                tooltip=f"Delete Field: {key}", 
                            )
                        )
                        container.content.controls.append(row_ctrl)

                if len(values) == 0:
                    container.content.controls.append(
                        ft.Row([
                            ft.Text("No fields yet. Click the button above to add one, or", italic=True, color=ft.Colors.ON_SURFACE_VARIANT),
                            ft.TextButton(
                                "Delete Section",
                                on_click=delete_section, data=section,
                                style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ERROR)
                            )
                        ], spacing=0)
                    )
                

                # Add the label and container with our text spans to the control list for this section
                control_list.append(label)
                control_list.append(container)

            return control_list


        

        about_section = ft.Column([
            ft.Row([
                ft.Text(f"About", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=18), color=self.data.get('color', None)),
                
            ], spacing=0),
            ft.TextField(
                self.data.get('about', ""), on_blur=lambda e: self.update_data(**{"about": e.control.value}), expand=True, 
                dense=True, capitalization=ft.TextCapitalization.SENTENCES, multiline=True,
                border_color=ft.Colors.OUTLINE_VARIANT, margin=ft.Margin.only(right=10),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, border=ft.Border.all(2, ft.Colors.OUTLINE_VARIANT), border_radius=10,
                content_padding=ft.Padding.all(6), min_lines=3, cursor_color=self.data.get('color', None)
            )
            
        ], expand=True, spacing=0, alignment=ft.MainAxisAlignment.CENTER)

        
        # Header that holds our image, edit mode button, and about section
        header = ft.Row([
            self.select_image_button,
            about_section
        ], vertical_alignment=ft.CrossAxisAlignment.START)


        # Body that holds the rest of our widget
        body = ft.Column(
            controls=[header],
            scroll="auto", expand=True, spacing=0
        )

        # Load in our character data controls after the header
        body.controls.extend(_load_character_data_controls())

        new_section_button = ft.Button(
            "New Section", #ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
            on_click=new_section_clicked,
            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, text_style=ft.TextStyle(weight=ft.FontWeight.W_500, size=20)),
        )

        new_section_tf = ft.TextField(
            autofocus=True, label="Section Name", capitalization=ft.TextCapitalization.WORDS, visible=False,
            on_submit=create_new_section, on_blur=hide_new_section_tf, dense=True, bgcolor=ft.Colors.SURFACE_CONTAINER,
        )

        new_field_tf = ft.TextField(
            label="New Field Name", capitalization=ft.TextCapitalization.SENTENCES, visible=False,
            on_submit=create_new_field, on_blur=hide_new_field_tf, dense=True, bgcolor=ft.Colors.SURFACE_CONTAINER,
            #data=section   # Gets set when we click the new field button for a specific section
        )

        self.content = ft.Stack([
            body,
            ft.Column([
                new_section_button,
                new_section_tf, 
                new_field_tf
            ], alignment=ft.MainAxisAlignment.END, horizontal_alignment=ft.CrossAxisAlignment.END, expand=True,)
        ], alignment=ft.Alignment.TOP_RIGHT, expand=True)

    def reload_widget(self):    # TEMP TO PREVENT ERRORS FROM CALLS
        return

# DONE BUILD