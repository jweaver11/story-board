''' Class for the Notes widget. Displays as its own tab for easy access to pinning '''

import flet as ft
from models.views.story import Story
from models.widget import Widget
from models.app import app
from styles.text_fields import TextField, UnderlinedTextField, NoLabelTextField
from styles.menu_option_style import MenuOptionStyle
import asyncio
from styles.colors import colors
    

class Note(Widget):

    # Constructor
    def __init__(self, title: str, directory_path: str, story: Story, data: dict={}, is_new: bool=False):
 
        # Initialize from our parent class 'Widget'. 
        super().__init__(
            title = title,                      # Title of the note
            directory_path = directory_path,    # Path to our notes json file
            story = story,                      # Reference to our story object
            data = data,
            is_new = is_new
        )

        # If we're new, give default values for our data 
        if self.is_new == True:
            self.data.update({ 
                'tag': "note", 
                'color': app.settings.data.get('widget_defaults', {}).get('note', {}).get('color'),

                # Note card data. Stored as list so we can duplicate labels
                'card_data': [ 
                    {"label": "", "value": "", 'color': 'onsurface'},
                ]
            })


    # Called after any changes happen to the data that need to be reflected in the UI, usually just ones that require a rebuild
    def build(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        super().build()

        self.padding = ft.Padding.all(10)   # Set padding

        
        # Adds our new card to data and our column
        async def handle_create_card(e=None):
            self.data['card_data'].append({"label": '', "value": "", 'color': "white"})
            self.update_data(**{'card_data': self.data['card_data']})
            card_row.controls.append(new_card(len(self.data['card_data']) - 1, self.data['card_data'][-1]))
            card_row.update()
            await asyncio.sleep(0.02)
            await card_row.parent.scroll_to(offset=-1, duration=200)
            

        # Saves label when text field is unfocused
        def save_card_label(e: ft.Event[ft.TextField]):
            index = e.control.parent.parent.parent.data
            if len(self.data['card_data']) > index:
                self.data['card_data'][index]['label'] = e.control.value
                self.update_data(**{'card_data': self.data['card_data']})
                    

        # Saves content when text field is unfocused
        def save_card_value(e: ft.Event[ft.TextField]):
            index = e.control.parent.parent.parent.data
            
            if len(self.data['card_data']) > index:
                self.data['card_data'][index]['value'] = e.control.value
                self.update_data(**{'card_data': self.data['card_data']})

        def get_card_options(idx: int) -> list[ft.Control]:
            ''' Pops open a column of the menu options for this tree view item'''

            async def handle_delete(e: ft.Event[ft.Control]):
                if len(self.data['card_data']) > idx:
                    del self.data['card_data'][idx]
                    self.update_data(**{'card_data': self.data['card_data']})
                    card_row.controls.pop(idx)
                    card_row.update()
                    for i, ctrl in enumerate(card_row.controls):
                        ctrl.data = i
                    await self.story.close_menu()

            async def handle_color_change(e: ft.Event[ft.Control]):
                new_color = e.control.data
                if len(self.data['card_data']) > idx:
                    self.data['card_data'][idx]['color'] = new_color
                    self.update_data(**{'card_data': self.data['card_data']})
                    card_row.controls[idx].content.bgcolor = ft.Colors.with_opacity(0.05, new_color)
                    card_row.controls[idx].content.update()
                    await self.story.close_menu()


            return [
                MenuOptionStyle(
                    ft.SubmenuButton(
                        ft.Row([
                            ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, ft.Colors.PRIMARY), 
                            ft.Text("Color", weight=ft.FontWeight.BOLD, expand=True),
                            ft.Icon(ft.Icons.ARROW_RIGHT),
                        ], expand=True),
                        [ft.MenuItemButton(color.capitalize(), style=ft.ButtonStyle(color), on_click=handle_color_change, data=color) for color in colors],
                        menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                        style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        tooltip="Change this widget's color"
                    ),
                    no_padding=True, no_effects=True
                ),
                MenuOptionStyle(
                    on_click=handle_delete,
                    content=ft.Row([
                        ft.Icon(ft.Icons.DELETE_OUTLINE_OUTLINED, size=20, color=ft.Colors.ERROR),
                        ft.Text("Delete Card", weight=ft.FontWeight.BOLD)
                    ], alignment=ft.MainAxisAlignment.START, spacing=10),
                )
            ]

        # Gives us a new textfield for each note card
        def new_card(idx: int, data: dict={}) -> TextField:
            label = data.get('label', '')
            value = data.get('value', '')
            color = data.get('color', 'onsurface')

            #ft.IconButton(ft.Icons.DELETE_OUTLINE_OUTLINED, on_click=delete_card, tooltip="Delete this card"),
            # Top textfield for the label
            label_tf = ft.TextField(
                value=label,
                dense=True, multiline=True, width=400,
                border_color=ft.Colors.TRANSPARENT,
                capitalization=ft.TextCapitalization.SENTENCES,
                text_style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD),
                suffix_icon=ft.GestureDetector(
                    ft.IconButton(
                        ft.Icons.MORE_VERT, ft.Colors.ON_SURFACE_VARIANT, 
                        on_click=lambda e: self.story.open_menu(get_card_options(e.control.parent.parent.parent.parent.parent.data)),
                        mouse_cursor=ft.MouseCursor.CLICK,
                    ),
                    on_hover=lambda e: self.set_mouse_coords(e),
                    hover_interval=30,
                ),
                on_blur=save_card_label
            )

            # Bottom textfield for the body of the card
            body_tf = ft.TextField(
                dense=True,
                border_color=ft.Colors.TRANSPARENT,
                text_style=ft.TextStyle(size=14),
                multiline=True,
                capitalization=ft.TextCapitalization.SENTENCES,
                value=value, expand=True, on_blur=save_card_value,
            )  
            
            
            card = ft.Card(
                ft.Container(
                    ft.Column([
                        label_tf,
                        ft.Divider(2, 2, leading_indent=10, trailing_indent=10),
                        body_tf
                    ], spacing=0, expand=True),
                    bgcolor=ft.Colors.with_opacity(0.05, color),
                ),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                height=300, width=400,
                shape=ft.RoundedRectangleBorder(radius=4),
                data=idx
            )
            return card

        # Column to hold our cards textfields
        card_row = ft.Row(
            controls=[], 
            wrap=True, alignment=ft.MainAxisAlignment.START, expand=True,
        )

        # Go through the note data and load the cards
        for idx, card_data in enumerate(self.data.get('card_data', [])):
            card_row.controls.append(new_card(idx, card_data))


        # Button to click to add a new card
        add_card_button = ft.Button(
            "Add Card", #ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY,
            tooltip="Add a new card to your note.", 
            on_click=handle_create_card, 
            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, text_style=ft.TextStyle(weight=ft.FontWeight.W_500, size=20)),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST
        )

        


        self.content = ft.Stack([
            ft.Column([card_row], expand=True, alignment=ft.MainAxisAlignment.START, scroll=ft.ScrollMode.AUTO),
            ft.Column([
                
                add_card_button, 
            ], alignment=ft.MainAxisAlignment.END, horizontal_alignment=ft.CrossAxisAlignment.END, expand=True,)
        ], alignment=ft.Alignment.TOP_LEFT, expand=True)