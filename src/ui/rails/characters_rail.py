''' 
Rail for the character workspace. 
Includes the filter options at the top, a list of characters, and 
the create 'character button' at the bottom.
'''

import flet as ft
from models.widgets.character import Character
from styles.menu_option_style import MenuOptionStyle
from ui.rails.rail import Rail
from models.views.story import Story
from handlers.tree_view import load_directory_data
from styles.tree_view.tree_view_directory import TreeViewDirectory
from models.app import app

class CharactersRail(Rail):
    def __init__(self, page: ft.Page, story: Story):

        # Initialize the parent Rail class first
        super().__init__(
            page=page,
            story=story,
            directory_path=story.data.get('content_directory_path', '')
        )

        # UI elements
        self.top_row_buttons = [
            ft.PopupMenuButton(
                icon=ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                tooltip="New", menu_padding=0,
                items=[
                    ft.PopupMenuItem(
                        text="Character", icon=ft.Icons.PERSON_ADD_ALT_OUTLINED,
                        on_click=self.new_item_clicked, data="character"
                    ),
                    ft.PopupMenuItem(
                        text="Family Tree", icon=ft.Icons.FAMILY_RESTROOM_OUTLINED,
                        on_click=self.new_item_clicked, data="family_tree"
                    ),
                ]
            ),
            ft.IconButton(
                icon=ft.Icons.FILE_UPLOAD_OUTLINED,
                tooltip="Upload Character",
            ),
        ]

        # Reload the rail on start
        self.reload_rail() 

    # Called to return our list of menu options for the content rail
    def get_menu_options(self) -> list[ft.Control]:
            
        # Builds our buttons that are our options in the menu
        return [
            MenuOptionStyle(
                content=ft.PopupMenuButton(
                    content=ft.Row([ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED), ft.Text("New", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD)]),
                    tooltip="New", menu_padding=0,
                    items=[
                        ft.PopupMenuItem(
                            text="Character", icon=ft.Icons.PERSON_OUTLINED,
                            on_click=self.new_item_clicked, data="character"
                        ),  
                        ft.PopupMenuItem(
                            text="Family Tree", icon=ft.Icons.FAMILY_RESTROOM_OUTLINED,
                            on_click=self.new_item_clicked, data="family_tree"
                        ),
                    ]
                ),
            ),
            MenuOptionStyle(
                content=ft.PopupMenuButton(
                    content=ft.Row([ft.Icon(ft.Icons.FILE_UPLOAD_OUTLINED), ft.Text("Upload", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD)]),
                    tooltip="Upload", menu_padding=0,
                    items=[
                        ft.PopupMenuItem(
                            text="Character", icon=ft.Icons.PERSON_OUTLINED,
                        ),
                        ft.PopupMenuItem(
                            text="Family Tree", icon=ft.Icons.FAMILY_RESTROOM_OUTLINED,
                        ),
                    ]
                ),
            )
        ]
    
    def get_directory_menu_options(self) -> list[ft.Control]:
        return [
            MenuOptionStyle(
                data="character",
                content=ft.Row([
                    ft.Icon(ft.Icons.PERSON_ADD_ALT_OUTLINED),
                    ft.Text("Character", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
                ])
            ),
        ]
    
    def _default_char_list(self) -> list[ft.Control]:
        direction = self.story.data.get('settings', {}).get('character_rail_sort_by', {}).get('direction', 'descending')
        char_list = [char for char in self.story.characters.values()]

        controls = []
        for char in char_list:
            controls.append(ft.Text(char.title))

        return controls
    
    def _role_char_list(self) -> list[ft.Control]:
        
        main_chars = [char for char in self.story.characters.values() if char.data.get('role', 'background') == 'main']
        side_chars = [char for char in self.story.characters.values() if char.data.get('role', 'background') == 'side']
        background_chars = [char for char in self.story.characters.values() if char.data.get('role', 'background') == 'background']

        direction = self.story.data.get('settings', {}).get('character_rail_sort_by', {}).get('direction', 'descending')

        controls = []

        if len(main_chars) > 0:
            controls.append(ft.Text("Main Characters", weight=ft.FontWeight.BOLD))
            for char in main_chars:
                controls.append(ft.Text(char.title))
            controls.append(ft.Container(height=10))

        if len(side_chars) > 0:
            controls.append(ft.Text("Side Characters", weight=ft.FontWeight.BOLD))
            for char in side_chars:
                controls.append(ft.Text(char.title))
            controls.append(ft.Container(height=10))

        if len(background_chars) > 0:
            controls.append(ft.Text("Background Characters", weight=ft.FontWeight.BOLD))
            for char in background_chars:
                controls.append(ft.Text(char.title))
            controls.append(ft.Container(height=10))

        return controls


    # Called on startup and when we have changes to the rail that have to be reloaded 
    def reload_rail(self):

        # TODO: Character rail should load from story.characters and organize them by main, side, background, etc. and have filter options to organize them that way.
        # IT should not load from the content directory like other rails.

        header = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=self.top_row_buttons
        )
        
                 

        # Build the content of our rail
        content = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            controls=[]
        )


        

        sort_method = self.story.data.get('settings', {}).get('character_rail_sort_by', {}).get('method', 'none')
        if sort_method is None:
            content.controls = self._default_char_list
        elif sort_method == "role":
            content.controls = self._role_char_list()
                    

        content.controls.append(ft.Container(height=6))
        # Append our hidden textfield for creating new items
        content.controls.append(self.new_item_textfield)

        # Add container to the bottom to make sure the drag target and gesture detector fill the rest of the space
        content.controls.append(ft.Container(expand=True))

        # Wrap the gd in a drag target so we can move characters here
        dt = ft.DragTarget(
            group="widgets",
            content=content,     # Our content is the content we built above
            on_accept=lambda e: self.on_drag_accept(e, self.directory_path)
        )


        menu_gesture_detector = ft.GestureDetector(
            content=dt,
            expand=True,
            on_hover=self.on_hovers,
            on_secondary_tap=lambda e: self.story.open_menu(self.get_menu_options()),
            hover_interval=20,
        )

        # Set our content to be a column
        self.content = ft.Column(
            spacing=0,
            expand=True,
            controls=[
                header,
                ft.Divider(),
                menu_gesture_detector
            ]
        )
        
        # Apply our update
        self.p.update()
