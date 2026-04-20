""" WIP """

import flet as ft
from models.views.story import Story
from ui.rails.rail import Rail
from styles.menu_option_style import MenuOptionStyle
from utils.tree_view import load_directory_data
from models.isolated_controls.column import IsolatedColumn


class WorldBuildingRail(Rail):

    # Constructor
    def __init__(self, page: ft.Page, story: Story):
        
        # Initialize the parent Rail class first
        super().__init__(
            page=page,
            story=story,
            directory_path=story.data.get('content_directory_path', '')
        )

        self.top_row_buttons = [
            ft.PopupMenuButton(
                icon=ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                tooltip="New", menu_padding=0,
                items=[
                    ft.PopupMenuItem(
                        "Map", icon=ft.Icons.MAP_OUTLINED,
                        on_click=self.new_item_clicked, data="map"
                    ),
                    ft.PopupMenuItem(
                        "World", icon=ft.Icons.PUBLIC_OUTLINED,
                        on_click=self.new_item_clicked, data="world"
                    ),
                ]
            ),
             ft.PopupMenuButton(
                icon=ft.Icons.FILE_UPLOAD_OUTLINED,
                tooltip="Upload", menu_padding=0,
                items=[
                    ft.PopupMenuItem(
                        "Map", icon=ft.Icons.MAP_OUTLINED,
                        on_click=self.new_item_clicked, data="map"
                    ),
                    ft.PopupMenuItem(
                        "World", icon=ft.Icons.PUBLIC_OUTLINED,
                        on_click=self.new_item_clicked, data="world"
                    ),
                ]
            ),
        ]

        self.reload_rail()

    # Called when new character button or menu option is clicked
    def new_map_clicked(self, e=None, is_sub_map: bool = None):
        ''' Handles setting our textfield for new character creation '''
        
        # Makes sure the right textfield is visible and the others are hidden
        self.new_item_textfield.visible = True

        # Set our textfield value to none, and the hint and data
        self.new_item_textfield.value = None
        self.new_item_textfield.hint_text = "Map Title"
        self.new_item_textfield.data = "map"

        # Close the menu (if ones is open), which will update the page as well
        self.story.close_menu()

    # Called to have our create new map option called
    def new_item_clicked(self, type: str):
        ''' Same function name as the tree_view_directory style in order to give functionality'''

        self.new_map_clicked()
        

    # Called to return our list of menu options for the content rail
    def get_menu_options(self) -> list[ft.Control]:
            
        # Builds our buttons that are our options in the menu
        return [
            MenuOptionStyle(
                content=ft.PopupMenuButton(
                    content=ft.Container(
                        ft.Row([ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED), ft.Text("New", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD)]),
                        padding=ft.padding.all(8), border_radius=ft.border_radius.all(6),
                    ),
                    tooltip="New", menu_padding=0,
                    items=[
                        ft.PopupMenuItem(
                            "Map", icon=ft.Icons.MAP_OUTLINED,
                            on_click=self.new_item_clicked, data="map"
                        ),
                        ft.PopupMenuItem(
                            "World", icon=ft.Icons.PUBLIC_OUTLINED,
                            on_click=self.new_item_clicked, data="world"
                        ),
                    ]
                ),
                no_padding=True
            ),
            MenuOptionStyle(
                content=ft.PopupMenuButton(
                    content=ft.Container(
                        ft.Row([ft.Icon(ft.Icons.FILE_UPLOAD_OUTLINED), ft.Text("Upload", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD)]),
                        padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(6),
                    ),
                    tooltip="Upload", menu_padding=0,
                    items=[
                        ft.PopupMenuItem("Map", icon=ft.Icons.MAP_OUTLINED,),
                        ft.PopupMenuItem("World Building", icon=ft.Icons.PUBLIC_OUTLINED,),
                    ]
                ),
                no_padding=True
            )

            # New and upload options? or just upload?? or how do i wanna do this?? Compact vs spread out view??
        ]
    
    def get_directory_menu_options(self) -> list[ft.Control]:
        return [
            MenuOptionStyle(
                data="map",
                content=ft.Row([
                    ft.Icon(ft.Icons.MAP_OUTLINED),
                    ft.Text("Map", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
                ])
            ),
        ]

    def get_file_menu_options(self) -> list[ft.Control]:
        return [
            MenuOptionStyle(
                data="map",
                content=ft.Row([
                    ft.Icon(ft.Icons.MAP_OUTLINED),
                    ft.Text("Sub-Map", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
                ])
            ),
        ]


    # Called on startup and when we have changes to the rail that have to be reloaded 
    def reload_rail(self):
        ''' Reloads/Rebuilds our rail based on current data '''

        #TODO: Add charts to this section
        # Add items to this section

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
            column=content,
            rail=self,
            additional_directory_menu_options=self.get_directory_menu_options(),
            additional_file_menu_options=self.get_file_menu_options()
        )

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


        # Gesture detector to put on top of stack on the rail to pop open menus on right click
        menu_gesture_detector = ft.GestureDetector(
            content=dt,
            expand=True,
            on_hover=self._set_menu_coords,
            on_secondary_tap=lambda _: self.story.open_menu(self.get_menu_options()),
            hover_interval=20,
        )

        # Set our content to be a column
        self.controls = [
            header,
            ft.Divider(),
            menu_gesture_detector
        ]

        self.controls = [
            #header,
            #ft.Divider(),
            ft.Text("Coming Soon")
            #menu_gesture_detector
        ]
        
        
        # Apply the update
        try:
            self.update()
        except Exception:
            pass


        
