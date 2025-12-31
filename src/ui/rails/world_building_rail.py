""" WIP """

import flet as ft
from models.views.story import Story
from ui.rails.rail import Rail
from styles.menu_option_style import Menu_Option_Style
from handlers.tree_view import load_directory_data


class World_Building_Rail(Rail):

    # Constructor
    def __init__(self, page: ft.Page, story: Story):
        
        # Initialize the parent Rail class first
        super().__init__(
            page=page,
            story=story,
            directory_path=story.data.get('content_directory_path', '')
        )

        # Reload the rail on start
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
            Menu_Option_Style(
                on_click=self.new_category_clicked,
                data="category",
                content=ft.Row([
                    ft.Icon(ft.Icons.CREATE_NEW_FOLDER_OUTLINED),
                    ft.Text("Category", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
                ])
            ),
            Menu_Option_Style(
                on_click=self.new_map_clicked,
                data="map",
                content=ft.Row([
                    ft.Icon(ft.Icons.MAP_OUTLINED),
                    ft.Text("Map", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
                ])
            ),

            # New and upload options? or just upload?? or how do i wanna do this?? Compact vs spread out view??
        ]
    
    def get_directory_menu_options(self) -> list[ft.Control]:
        return [
            Menu_Option_Style(
                data="map",
                content=ft.Row([
                    ft.Icon(ft.Icons.MAP_OUTLINED),
                    ft.Text("Map", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
                ])
            ),
        ]

    def get_file_menu_options(self) -> list[ft.Control]:
        return [
            Menu_Option_Style(
                data="map",
                content=ft.Row([
                    ft.Icon(ft.Icons.MAP_OUTLINED),
                    ft.Text("Sub-Map", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
                ])
            ),
        ]
    
    def show_world_building_widget(self):
        ''' Shows the world building widget '''

        if self.story.world_building is not None:
            self.story.world_building.toggle_visibility()


    # Called on startup and when we have changes to the rail that have to be reloaded 
    def reload_rail(self):
        # Button to 'Create New World'
        # TODO: Option to create new world map depending on if multiplanetory or not
        # Reads the maps categories for each level, and adds them to a list of categories. Then displays them in the rail
        # This is how we get semi tree view for maps and pass categories in.
        # Users can only create categories, maps, and markers on existing maps on the rail?
        # Use the world building widget to create the categories of stuff on the rail, and have a maps as well.

        header = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            
            controls=[
            ft.IconButton(
                tooltip="New Category",
                icon=ft.Icons.CREATE_NEW_FOLDER_OUTLINED,
                on_click=self.new_category_clicked
            ),
            
            ft.IconButton(
                tooltip="New Map",
                icon=ft.Icons.MAP_OUTLINED,
                on_click=self.new_map_clicked
            ),
        ])
                 
        # Build the content of our rail
        content = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            controls=[]
        )


        # Maps showing up on the rail.........
        # Categories rendered normal.
        # Maps with no sub maps, get rendered as normal files.
        # Maps with sub maps (saved in their data for reference) get drop downs like categories
        

        # Load our content directory data into the rail
        #load_directory_data(
            #page=self.p,
            #story=self.story,
            #directory=self.directory_path,
            #column=content,
            #rail=self,
            #additional_directory_menu_options=self.get_directory_menu_options(),
            #additional_file_menu_options=self.get_file_menu_options()
        #)

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


        
