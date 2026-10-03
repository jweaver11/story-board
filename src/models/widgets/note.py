''' Class for the Notes widget. Displays as its own tab for easy access to pinning '''

import flet as ft
from models.views.story import Story
from models.widget import Widget, WidgetView
from styles.text_fields import TextField, UnderlinedTextField, NoLabelTextField
from styles.menu_option_style import MenuOptionStyle
import asyncio
from styles.colors import colors
from dataclasses import field
from contexts.contexts import StoryContext, OverlayContext
from dataclasses import dataclass
import uuid


# Notes contain cards (note cards) with a label, body, color, and strikethrough option
@ft.observable
@dataclass
class Card:
    label: str = ''
    body: str = ''
    color: str = 'white'
    strikethrough: bool = False

    # Functions for updating the cards attributes
    def set_label(self, value: str):
        self.label = value
    def set_body(self, value: str):
        self.body = value
    def set_color(self, value: str):
        self.color = value
    def toggle_strikethrough(self):
        self.strikethrough = not self.strikethrough


# The note widget, which just contains cards
@ft.observable
@dataclass
class Note(Widget):
    tag: str = "note"
    card_data: dict = field(default_factory=lambda: {str(uuid.uuid4()): Card()})

    def __post_init__(self):
        super().__post_init__()
        # Cards loaded from json arrive as plain dicts, so convert them to Card objects in place
        for card_id, card in self.card_data.items():
            if isinstance(card, dict):
                self.card_data[card_id] = Card(**card)

    # Create a new card
    def create_card(self):
        self.card_data[str(uuid.uuid4())] = Card()

    # Deletes the key for the card
    def delete_card(self, card_id: str):
        if card_id in self.card_data:
            self.card_data.pop(card_id)


# Component for cards that returns a container control for each note card, with label, body, and ability to change its color, strikethrough status, or delete it
@ft.component
def CardView(card: Card, card_id: str, delete_card: callable) -> ft.Container:

    # Returns our popupmenu options for the cards menu on the right side of the label
    def get_card_options() -> list[ft.Control]:
        ''' Pops open a column of the menu options for this tree view item'''

        # Handles changing the color of the card via the popup menu
        async def handle_color_change(e: ft.Event[ft.Control]):
            card.set_color(e.control.data)
        
        return [
            ft.PopupMenuItem(       # Color change options
                ft.SubmenuButton(
                    ft.Row([
                        ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, ft.Colors.PRIMARY), 
                        ft.Text("Color", weight=ft.FontWeight.BOLD, expand=True),
                        ft.Icon(ft.Icons.ARROW_RIGHT),
                    ], expand=True),
                    [ft.MenuItemButton(color.capitalize(), style=ft.ButtonStyle(color), on_click=handle_color_change, data=color) for color in colors],
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    tooltip="Change this widget's color"
                ),
                padding=ft.Padding.all(0)
            ),
            ft.PopupMenuItem(       # Toggle strikethrough
                "Strikethrough",
                ft.Icon(ft.Icons.FORMAT_STRIKETHROUGH_OUTLINED, ft.Colors.PRIMARY),
                on_click=card.toggle_strikethrough
            ),
            ft.PopupMenuItem(       # Delete card   
                "Delete Card", ft.Icon(ft.Icons.DELETE_OUTLINE_OUTLINED, size=20, color=ft.Colors.ERROR), 
                on_click=lambda: delete_card(card_id),
            )
        ]
    

    # Top textfield for the label
    label = ft.TextField(
        value=card.label,
        key=f"{card_id}_label",
        dense=True, multiline=True, width=400,
        border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.TRANSPARENT)),
        capitalization=ft.TextCapitalization.SENTENCES,
        text_style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD, decoration=ft.TextDecoration.LINE_THROUGH if card.strikethrough else ft.TextDecoration.NONE, decoration_thickness=2),
        suffix_icon=ft.PopupMenuButton(items=get_card_options(), tooltip="Card Options", menu_padding=ft.Padding.all(0)),
        on_blur=lambda e: card.set_label(e.control.value),
    )

    # Bottom textfield for the body of the card
    body = ft.TextField(
        dense=True,
        border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.TRANSPARENT)),
        text_style=ft.TextStyle(size=14, decoration=ft.TextDecoration.LINE_THROUGH if card.strikethrough else ft.TextDecoration.NONE, decoration_thickness=2),
        multiline=True,
        capitalization=ft.TextCapitalization.SENTENCES,
        value=card.body, expand=True, 
        key=f"{card_id}_body",
        on_blur=lambda e: card.set_body(e.control.value),
    )  
    
    # Returns the container for the card
    return ft.Container(
        ft.Column([
            label,
            ft.Divider(2, 2, leading_indent=10, trailing_indent=10),
            body
        ], spacing=0, expand=True),
        bgcolor=ft.Colors.with_opacity(0.05, card.color),
        border_radius=4,
        key=f"{card_id}_card",
        height=300, width=400,
    )

# Component for the note view, which contains all the note cards and allows adding new cards
@ft.component
def NoteView(note: Note) -> WidgetView:
    ''' Reloads/Rebuilds our widget based on current data '''

    # Create the card and scroll down
    async def create_card(_):
        note.create_card()
        await card_column.current.scroll_to(-1, duration=500)   # Scroll down the column to see the new note card

    card_column = ft.use_ref(ft.Column())   # Stable ref to the scrollable column, immune to remounts across re-renders

    # Return the parent widget for consistent styling
    return WidgetView(
        note, 
        ft.Container(
            ft.Column([     # Column that holds our roll with stable ref for auto scrolling
                ft.Row(     # Row that holds all the cards
                    controls=[
                        CardView(card, card_id, note.delete_card) for card_id, card in note.card_data.items()
                    ] + [
                        ft.Button(      # Button to add cards
                            "Add Card", ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY,
                            tooltip="Add a new card to your note.", 
                            on_click=create_card, 
                            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, text_style=ft.TextStyle(weight=ft.FontWeight.W_500, size=20)),
                            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST
                        ),
                    ], 
                    wrap=True, alignment=ft.MainAxisAlignment.START, expand=True,
                )
            ], ref=card_column, key=f"{note.id}_note_card_column", expand=True, alignment=ft.MainAxisAlignment.START, scroll=ft.ScrollMode.AUTO),
            
            
            
            padding=ft.Padding.all(10),
            expand=True
        )
    )