''' Class for the Notes widget. Displays as its own tab for easy access to pinning '''

import flet as ft
from models.views.story import Story
from models.widget import Widget
from models.app import app
from styles.text_fields import TextField, UnderlinedTextField, NoLabelTextField
from styles.menu_option_style import MenuOptionStyle
import asyncio
from styles.colors import colors
import flet_shadcn_ui as shad
from styles.highlight_button import HighlightButton
    

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
                    {"label": "", "value": "", 'color': 'onsurface', 'strikethrough': False},
                ]
            })


    # Called after any changes happen to the data that need to be reflected in the UI, usually just ones that require a rebuild
    def build(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        super().build()

        if self.page.platform.is_mobile() != True:
            self.padding = ft.Padding.all(10)
        
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

            async def delete_card(e: ft.Event[ft.Control]):
                if len(self.data['card_data']) > idx:
                    del self.data['card_data'][idx]
                    self.update_data(**{'card_data': self.data['card_data']})
                    card_row.controls = build_card_row()
                    card_row.update()

            async def handle_color_change(e: ft.Event[ft.Control]):
                new_color = e.control.data
                close_popovers()
                if len(self.data['card_data']) > idx:
                    self.data['card_data'][idx]['color'] = new_color
                    self.update_data(**{'card_data': self.data['card_data']})
                    card_row.controls[idx].content.bgcolor = ft.Colors.with_opacity(0.05, new_color)
                    card_row.controls[idx].content.update()
                    await self.story.close_menu()

            async def handle_strikethrough(e: ft.Event[ft.Control]):
                close_popovers()
                if len(self.data['card_data']) > idx:
                    struck = not self.data['card_data'][idx].get('strikethrough', False)
                    self.data['card_data'][idx]['strikethrough'] = struck
                    self.update_data(**{'card_data': self.data['card_data']})
                    decoration = ft.TextDecoration.LINE_THROUGH if struck else ft.TextDecoration.NONE
                    column = card_row.controls[idx].content.content
                    for tf in (column.controls[0], column.controls[2]):
                        tf.text_style.decoration = decoration
                        tf.update()
                    await self.story.close_menu()

            async def move_card(offset: int):
                
                cards = self.data['card_data']
                target = idx + offset
                if offset == 0 or not 0 <= idx < len(cards) or not 0 <= target < len(cards):
                    return

                cards[idx], cards[target] = cards[target], cards[idx]
                self.update_data(**{'card_data': cards})

                controls = card_row.controls
                controls[idx], controls[target] = controls[target], controls[idx]
                card_row.controls = build_card_row()
                card_row.update()

            async def move_up(e=None):
                await move_card(-1)

            async def move_down(e=None):
                await move_card(1)

            def toggle_color_popover(e=None):
                color_popover.open = not color_popover.open
                color_popover.update()
            def close_popovers(e=None):
                color_popover.open = False
                color_popover.update()


            return [
                color_popover := shad.Popover(
                    shad.MenuItem(
                        leading=ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, ft.Colors.PRIMARY, size=20),
                        content=ft.Row([ft.Text("Color"), ft.Icon(ft.Icons.ARROW_RIGHT, ft.Colors.OUTLINE, size=16)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        trailing=ft.Icons.ARROW_RIGHT,
                        on_click=toggle_color_popover,
                        close_on_click=False,
                    ),
                    ft.Column([
                        shad.MenuItem(
                            content=ft.Icon(ft.Icons.CIRCLE, color=color, size=20),
                            on_click=handle_color_change, close_on_click=True, data=color,
                            expand=True
                        ) for color in colors
                    ], tight=True, spacing=0, width=100, height=min(320, ft.context.page.height * 0.3), scroll=ft.ScrollMode.AUTO),
                    on_dismiss=close_popovers
                ), 
                shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
                shad.MenuItem(
                    leading=ft.Icon(ft.Icons.ARROW_UPWARD_OUTLINED, ft.Colors.PRIMARY),
                    content=ft.Text("Move Up", weight=ft.FontWeight.BOLD),
                    on_click=move_up,
                ),
                shad.MenuItem(
                    leading=ft.Icon(ft.Icons.ARROW_DOWNWARD_OUTLINED, ft.Colors.PRIMARY),
                    content=ft.Text("Move Down", weight=ft.FontWeight.BOLD),
                    on_click=move_down,
                ),
                shad.MenuItem(
                    leading=ft.Icon(ft.Icons.FORMAT_STRIKETHROUGH_OUTLINED, size=20, color=ft.Colors.PRIMARY),
                    content=ft.Text("Mark Done", weight=ft.FontWeight.BOLD),
                    on_click=handle_strikethrough,
                ),
               
               
                shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
                shad.MenuItem(
                    leading=ft.Icon(ft.Icons.DELETE_OUTLINE_OUTLINED, size=20, color=ft.Colors.ERROR),
                    content=ft.Text("Delete Card", weight=ft.FontWeight.BOLD),
                    on_click=delete_card,
                ),
                
            ]

        # Gives us a new textfield for each note card
        def new_card(idx: int, data: dict={}) -> TextField:
            label = data.get('label', '')
            value = data.get('value', '')
            color = data.get('color', 'onsurface')
            strikethrough = data.get('strikethrough', False)

            # Top textfield for the label
            label_tf = ft.TextField(
                value=label,
                dense=True, multiline=True, width=400,
                border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.TRANSPARENT)),
                capitalization=ft.TextCapitalization.SENTENCES,
                text_style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD, decoration=ft.TextDecoration.LINE_THROUGH if strikethrough else ft.TextDecoration.NONE, decoration_thickness=2),
                
                suffix_icon=HighlightButton(
                    content=shad.ContextMenu(
                        ft.Icon(ft.Icons.MORE_VERT, ft.Colors.ON_SURFACE_VARIANT),
                        get_card_options(idx),
                        open_on_tap=True
                    ),
                    is_round=True,
                ),
                on_blur=save_card_label
            )

            # Bottom textfield for the body of the card
            body_tf = ft.TextField(
                dense=True,
                border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.TRANSPARENT)),
                text_style=ft.TextStyle(size=14, decoration=ft.TextDecoration.LINE_THROUGH if strikethrough else ft.TextDecoration.NONE, decoration_thickness=2),
                multiline=True,
                capitalization=ft.TextCapitalization.SENTENCES,
                value=value, expand=True, on_blur=save_card_value,
            )  
            
            
            card = ft.Card(
                ft.Container(
                    ft.Column([
                        label_tf,
                        ft.Divider(ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE), 2, leading_indent=10, trailing_indent=10),
                        body_tf
                    ], spacing=0, expand=True),
                    bgcolor=ft.Colors.with_opacity(0.05, color),
                    border_radius=4,
                    #shadow=ft.BoxShadow(blur_style=ft.BlurStyle.OUTER),
                    height=300, width=300, data=idx
                ),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                height=300, width=400,
                shape=ft.RoundedRectangleBorder(radius=4),
                data=idx
            )
            return card

        def build_card_row() -> list[ft.Control]:
            return [new_card(idx, card_data) for idx, card_data in enumerate(self.data.get('card_data', []))]

        # Column to hold our cards textfields
        card_row = ft.Row(
            controls=build_card_row(), 
            wrap=True, alignment=ft.MainAxisAlignment.START, expand=True,
        )

        # Button to click to add a new card
        add_card_button = ft.Button(
            "Add Card", 
            #icon=ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, icon_color=ft.Colors.PRIMARY,
            tooltip="Add a new card to your note.", 
            on_click=handle_create_card, 
            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, text_style=ft.TextStyle(weight=ft.FontWeight.W_500, size=20)),
            bgcolor=ft.Colors.SURFACE
        )

        
        #self.content = ft.Column([card_row], expand=True, alignment=ft.MainAxisAlignment.START, scroll=ft.ScrollMode.AUTO)

        self.content = ft.Stack([
            ft.Column([card_row], expand=True, alignment=ft.MainAxisAlignment.START, scroll=ft.ScrollMode.AUTO),
            ft.Column([
                add_card_button, 
            ], alignment=ft.MainAxisAlignment.END, horizontal_alignment=ft.CrossAxisAlignment.END, expand=True,)
        ], alignment=ft.Alignment.TOP_LEFT, expand=True)