''' Class for the Item widget. Displays as its own tab for easy access to pinning '''

import flet as ft
from models.views.story import Story
from models.widget import Widget
from styles.menu_option_style import MenuOptionStyle
from models.app import app
from styles.text_fields import TextField
import asyncio
from models.dataclasses.item_template import default_item_template_data


class Item(Widget):

    # Constructor
    def __init__(self, title: str, directory_path: str, story: Story, data: dict={}, is_new: bool = False):

        # Initialize from our parent class 'Widget'. 
        super().__init__(
            title = title,                      
            directory_path = directory_path,    
            story = story,                     
            data = data,
            is_new = is_new
        )

         # If we're new, give default values for our data 
        if self.is_new == True:
            self.data.update({
                # Widget data
                'tag': "item",             # Tag to identify what type of object this is
                'color': app.settings.data.get('widget_defaults', {}).get('item', {}).get('color'),

                'image_base64': str(), 

                # Item data - list of fields with title and string
                'item_data': app.settings.data.get('item_template', default_item_template_data())
            },
        )

    def build(self):

        super().build()

        if self.page.platform.is_mobile() != True:
            self.padding = ft.Padding.all(10)

        # Column to hold our fields textfields
        fields_column = ft.Column(
            expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            controls=[], scroll="auto", alignment=ft.MainAxisAlignment.START,
        )

        
        # Adds our new field to data and our column
        async def create_field(e=None):
            key = self.new_field_tf.value
            if key in self.data.get('item_data', {}):
                return
            self.data['item_data'][self.new_field_tf.value] = ""
            self.update_data(**{'item_data': self.data['item_data']})
            fields_column.controls.append(new_field_textfield(self.new_field_tf.value, ""))
            fields_column.update()
            self.new_field_tf.value = ""
            self.new_field_tf.update()
            add_field_button.visible = True
            add_field_button.update()
            await asyncio.sleep(0.02)
            await fields_column.scroll_to(offset=-1, duration=200)

        # Deletes a field from data and our column
        async def delete_field(e: ft.Event[ft.IconButton]):
            key = e.control.data
            if key in self.data.get('item_data', {}):
                del self.data['item_data'][key]
                self.update_data(**{'item_data': self.data['item_data']})
                for ctrl in fields_column.controls:
                    if ctrl.data == key:
                        fields_column.controls.remove(ctrl)
                        fields_column.update()
                        break
                

        # Saves content when text field is unfocused
        async def save_field(e: ft.Event[ft.TextField]):
            key = e.control.data
            if key in self.data.get('item_data', {}):
                self.data['item_data'][key] = e.control.value
                self.update_data(**{'item_data': self.data['item_data']})

        # Gives us a new textfield for each note field
        def new_field_textfield(key: str='', value: str='') -> TextField:
            tf = TextField(
                value, expand=True, capitalization=ft.TextCapitalization.SENTENCES, 
                multiline=True, label=key, dense=True, 
                on_blur=save_field, 
                data=key,
                suffix_icon=ft.IconButton(
                    ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR,
                    tooltip=f"Delete field {key}",
                    on_click=delete_field,
                    mouse_cursor="click", data=key
                ),
            )
            tf.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
            return tf

        # Go through the note data and load the fields
        for key, value in self.data.get('item_data', {}).items():
            
            fields_column.controls.append(new_field_textfield(key, value))

        # Show the textfield to label the new field
        async def _create_new_field_clicked(e):
            add_field_button.visible = False
            add_field_button.update()
            self.new_field_tf.value = ""
            self.new_field_tf.visible = True
            self.new_field_tf.label = "New Field Label"
            self.new_field_tf.update() 
            await self.new_field_tf.focus()

        # Hide the textfield
        async def _hide_new_field_tf(e):
            self.new_field_tf.visible = False
            self.new_field_tf.update()
            add_field_button.visible = True
            add_field_button.update()

        # Button to click to add a new field
        add_field_button = ft.Button(
            "Add Field", #ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY,
            tooltip="Add a new field to your note.", 
            on_click=_create_new_field_clicked, 
            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, text_style=ft.TextStyle(weight=ft.FontWeight.W_500, size=20)),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST
        )

        self.new_field_tf = ft.TextField(
            label="Add New Field", dense=True, 
            capitalization=ft.TextCapitalization.WORDS,
            on_blur=_hide_new_field_tf, 
            on_submit=create_field, visible=False, autofocus=True,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST
        ) 

        
        
        #self.description_tf.label = ""
        self.description_tf.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST

        body = ft.Column([
            ft.Row([
                self.select_image_button,
                self.description_tf
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            fields_column
        ], expand=True, spacing=0)

        self.content = ft.Stack([
            body,
            
            ft.Column([
                self.new_field_tf,
                add_field_button, 
            ], alignment=ft.MainAxisAlignment.END, horizontal_alignment=ft.CrossAxisAlignment.END, expand=True,)
        ], alignment=ft.Alignment.TOP_RIGHT, expand=True)