''' Class for the Item widget. Displays as its own tab for easy access to pinning '''

import flet as ft
from models.views.story import Story
from models.widget import Widget, WidgetView, WidgetDescription, WidgetImageButton
from styles.context_menu_option import MenuOptionStyle
from styles.text_fields import TextField
import asyncio
from dataclasses import dataclass, field
    
@ft.observable
@dataclass
class Item(Widget):

    tag: str = "item"
    data: dict = field(default_factory=lambda: {
        'Type': "",
        'Rarity': "",
        'Effects': "",
        'Material': "",
        'Size': "",
        'Weight': "",
        'Lore': "",
        'Cost': "",
        'Locations': "",
        'Count': "",
        'Notes': "",
    })

    # Creates a new field with passed in title
    def create_field(self, key: str):
        if key not in self.data:
            self.data[key] = ""

    # Deletes a field with the passed in title from the item's data dictionary
    def delete_field(self, key: str):
        if key in self.data:
            del self.data[key]

    # Update the data within the items data dict
    def update_field(self, **kwargs):
        for key, value in kwargs.items():
            self.data[key] = value

@ft.component
def ItemView(item: Item) -> WidgetView:

    print("ItemView component loaded")

    # Gives us a new textfield for each note field
    def field_ctrl(key: str, value: str='') -> TextField:
        tf = TextField(
            value, expand=True, capitalization=ft.TextCapitalization.SENTENCES, 
            multiline=True, label=key, dense=True, 
            on_blur=lambda e: item.update_field(**{key: e.control.value}), 
            data=key,
            suffix_icon=ft.IconButton(
                ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR,
                tooltip=f"Delete field {key}",
                on_click=lambda: item.delete_field(key),
                mouse_cursor="click", data=key
            ),
        )
        tf.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
        return tf

    creating_field, set_creating_field = ft.use_state(False)
    fields_column = ft.use_ref(ft.Column())

    # Column to hold our fields textfields
    fields_column = ft.Column(
        expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
        controls=[field_ctrl(key, value) for key, value in item.data.items()], 
        scroll="auto", alignment=ft.MainAxisAlignment.START,
    )

    body = ft.Column([
        ft.Row([
            WidgetImageButton(item),
            WidgetDescription(item.description, item.save_description),
        ], vertical_alignment=ft.CrossAxisAlignment.START, margin=ft.Margin.only(bottom=10)),
        fields_column
    ], expand=True, spacing=0)

    # Button to click to add a new field
    create_field_button = ft.Button(
        "Add field", #ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY,
        tooltip="Add a new field to your note.", 
        visible=not creating_field,
        on_click=lambda: set_creating_field(True), 
        style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, text_style=ft.TextStyle(weight=ft.FontWeight.W_500, size=20)),
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST
    )

    # Textfield for naming the new field
    create_field_tf = ft.TextField(
        label="Field Name", dense=True, 
        capitalization=ft.TextCapitalization.WORDS,
        on_blur=lambda: set_creating_field(False), 
        on_submit=lambda e: item.create_field(e.control.value), visible=creating_field, autofocus=True,
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST
    ) 

    return WidgetView(
        item,
        ft.Container(
            ft.Stack([
                body,
                
                ft.Column([
                    create_field_tf,
                    create_field_button, 
                ], alignment=ft.MainAxisAlignment.END, horizontal_alignment=ft.CrossAxisAlignment.END, expand=True,)
            ], alignment=ft.Alignment.TOP_RIGHT, expand=True),
            expand=True, padding=ft.Padding.all(10)
        )
    )