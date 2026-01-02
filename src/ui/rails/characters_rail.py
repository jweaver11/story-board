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
from handlers.remove_empty_categories import remove_empty_categories
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
                tooltip="New Content",
                menu_padding=0,
                items=[
                    ft.PopupMenuItem(
                        text="Category", icon=ft.Icons.CREATE_NEW_FOLDER_OUTLINED,
                        on_click=self.new_item_clicked, data="category"
                    ),
                    ft.PopupMenuItem(
                        text="Character", icon=ft.Icons.PERSON_ADD_ALT_OUTLINED,
                        on_click=self.new_item_clicked, data="character"
                    ),
                ]
            ),
            ft.PopupMenuButton(
                icon=ft.Icons.FILE_UPLOAD_OUTLINED,
                tooltip="Upload Content",
                menu_padding=0,
                items=[
                    ft.PopupMenuItem(
                        text="Character", icon=ft.Icons.PERSON_ADD_ALT_OUTLINED,
                    ),
                ]
            ),
        ]

        # Reload the rail on start
        self.reload_rail() 

    # Called to return our list of menu options for the content rail
    def get_menu_options(self) -> list[ft.Control]:
            
        # Builds our buttons that are our options in the menu
        return [
            MenuOptionStyle(
                on_click=self.new_item_clicked,
                data="category",
                content=ft.Row([
                    ft.Icon(ft.Icons.CREATE_NEW_FOLDER_OUTLINED),
                    ft.Text("Category", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
                ])
            ),
            MenuOptionStyle(
                on_click=self.new_item_clicked,
                data="character",
                content=ft.Row([
                    ft.Icon(ft.Icons.PERSON_ADD_ALT_OUTLINED),
                    ft.Text("Character", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
                ])
            ),
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


    # Called on startup and when we have changes to the rail that have to be reloaded 
    def reload_rail(self):

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

        # Load our content directory data into the rail
        load_directory_data(
            page=self.p,
            story=self.story,
            directory=self.directory_path,
            rail=self,
            tags=["character"],
            column=content,
            additional_directory_menu_options=self.get_directory_menu_options()
        ) 

        # Go through our content controls, and remove any directories that are empty because of tag filtering
        if not app.settings.data.get('show_empty_categories', True):
            for control in content.controls[:]:
                if isinstance(control, TreeViewDirectory):
                    remove_empty_categories(control, parent_column=content)
                    

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
