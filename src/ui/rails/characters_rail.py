''' 
Rail for the character workspace. 
Includes the filter options at the top, a list of characters, and 
the create 'character button' at the bottom.
'''

import flet as ft
from styles.menu_option_style import MenuOptionStyle
from ui.rails.rail import Rail
from models.views.story import Story
from styles.rail.widget_rail_item import WidgetRailItem
import json
from utils.alert_dialogs.character_connection import new_character_connection_clicked
from models.isolated_controls.column import IsolatedColumn
from models.isolated_controls.list_view import IsolatedListView



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
            
            ft.SubmenuButton(
                ft.Container(
                    ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, "primary"),
                    shape=ft.BoxShape.CIRCLE,
                    alignment=ft.Alignment.CENTER
                ),
                [
                    ft.SubmenuButton(
                        ft.Row([ft.Icon(ft.Icons.PERSON_OUTLINED, ft.Colors.PRIMARY), ft.Text("Character", color=ft.Colors.ON_SURFACE, expand=True)], expand=True),
                        self.get_template_options("character"), 
                        menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                        style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        tooltip="Create a new character for your story. Choose from templates or create a default character."
                    ),
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.FAMILY_RESTROOM_OUTLINED, ft.Colors.PRIMARY), content="Character Connection Map", 
                        data="character_connection_map", on_click=self.new_item_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True,
                        tooltip="Visualize the connections between the characters in your story"
                    ),  
                ],
                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10)),
                style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
            ),
            ft.SubmenuButton(
                ft.Container(
                    ft.Icon(ft.Icons.FILE_UPLOAD_OUTLINED, ft.Colors.PRIMARY),
                    shape=ft.BoxShape.CIRCLE,
                    alignment=ft.Alignment.CENTER
                ),
                [     
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.PERSON_OUTLINED, ft.Colors.PRIMARY), content="Character", 
                        data="character", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new character for your story. Choose from templates or create a default character.",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    ),
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.FAMILY_RESTROOM_OUTLINED, ft.Colors.PRIMARY), content="Character Connection Map", 
                        data="character_connection_map", on_click=self.new_item_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True,
                        tooltip="Visualize the connections between the characters in your story"
                    ),  
                ],
                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10)),
                style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
            ),
            
        ]

        self.reload_rail()



    # Open our settings to the templates tab
    async def _open_templates_editor(self, e):    
        from models.app import app
        app.settings.selected_index = 3     # Set settings to open on the character templates tab
        self.p.overlay.clear()              # If opened from menu, make sure its closed
        await self.p.push_route("/settings")
        

    # Called to return our list of menu options for the content rail
    def get_menu_options(self) -> list[ft.Control]:
            
        # Builds our buttons that are our options in the menu
        return [
            MenuOptionStyle(
                content=ft.PopupMenuButton(
                    content=ft.Container(
                        ft.Row([ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED), ft.Text("New", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD)], expand=True),
                        padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(6),
                    ),
                    tooltip="New", menu_padding=0, expand=True, padding=ft.padding.all(0),
                    items=[
                        ft.PopupMenuItem(
                            "Character", ft.Icons.PERSON_OUTLINED,
                            on_click=self.new_item_clicked, data="character"
                        ),  
                        ft.PopupMenuItem(
                            "Character Connection Map", ft.Icons.FAMILY_RESTROOM_OUTLINED,
                            on_click=self.new_item_clicked, data="character_connection_map"
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
                    tooltip="Upload", menu_padding=0, expand=True,
                    items=[
                        ft.PopupMenuItem(
                            "Character", ft.Icons.PERSON_OUTLINED, 
                        ),
                        ft.PopupMenuItem(
                            "Character Connection Map", ft.Icons.FAMILY_RESTROOM_OUTLINED,
                        ),
                    ]
                ),
                no_padding=True
            ),
            MenuOptionStyle(
                ft.Row([
                    ft.Icon(ft.Icons.CONNECT_WITHOUT_CONTACT),
                    ft.Text(f"Edit Character\nTemplates", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
                ]),
                on_click=self._open_templates_editor
            ),      
            MenuOptionStyle(
                ft.Row([
                    ft.Icon(ft.Icons.MANAGE_SEARCH_OUTLINED, tooltip="Edit Character Connections"),
                    ft.Text("Edit Character\nConnections", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
                ]),
                on_click=lambda e: new_character_connection_clicked(self.story),
            )
        ]
    
    # Called when the sort method button is clicked at the top of the rail
    async def _change_sort_method(self, e=None):

        # Grabs our newly selected sort method and enables the confirm button if needed
        async def _sort_method_change(e):
            nonlocal sort_method
            sort_method = e.data
            if confirm_sort_button.disabled:
                confirm_sort_button.disabled = False
                confirm_sort_button.style.color = ft.Colors.ON_SURFACE
                confirm_sort_button.update()

        # Sets our selected sort method and saves it, reloads the rail
        async def _confirm_sort_method(e):
            if sort_method is None:
                return
            self.story.data['settings']['character_rail_sort_by'] = sort_method
            await self.story.save_dict()
            self.story.active_rail.reload_rail()
            self.p.pop_dialog()

        # Returns our list of options for sorting characters
        def _get_sort_options() -> list[ft.Control]:
            options = [
                ft.Radio("Default", value="Default", mouse_cursor="click", tooltip="Whatever order they are stored as files in the system. Windows is alphabetical, but Mac is the order they were created in."),
                ft.Radio("Role", value="Role", mouse_cursor="click"), 
                ft.Radio("Morality", value="Morality", mouse_cursor="click"), 
                ft.Radio("Age", value="Age", mouse_cursor="click"), 
                ft.Radio("Name", value="Name", mouse_cursor="click")
            ]

            #all_options = self.story.data.get('settings', {}).get('character_rail_sort_options', [])


            return options

        column = ft.Column(_get_sort_options(), tight=True)
        sort_method = None

        dlg = ft.AlertDialog(
            title=ft.Text("Sort Characters by: "),
            content=ft.RadioGroup(column, on_change=_sort_method_change),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.p.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ERROR)),
                confirm_sort_button := ft.TextButton("Confirm", disabled=True, on_click=_confirm_sort_method, style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.OUTLINE)),
            ]
        )
        self.p.show_dialog(dlg)


    # Called when we reorder our characters on the rail
    async def _handle_character_reorder(self, e):
        ''' Handles the reordering and reloading of characters based on their new positions on the rail when we drag and drop them '''
        old_index = e.old_index
        new_idx = e.new_index

        # If we didn't move, return out
        if old_index == new_idx:
            return

        # Grab which character we dragged and update its index
        rlv = e.control
        dragged_character = rlv.controls[old_index].content.widget
        dragged_character.data['rail_index'] = new_idx
        await dragged_character.save_dict()

        # If we dragged down
        if old_index < new_idx:
            for widget in self.story.widgets:
                if widget.data.get('tag', "") == "character":
                    if widget.data.get('rail_index', 0) > old_index and widget.data.get('rail_index', 0) <= new_idx and widget != dragged_character:
                        widget.data['rail_index'] -= 1
                        await widget.save_dict()
        
        # If we dragged up
        elif old_index > new_idx:
            for widget in self.story.widgets:
                if widget.data.get('tag', "") == "character":
                    if widget.data.get('rail_index', 0) >= new_idx and widget.data.get('rail_index', 0) < old_index and widget != dragged_character:
                        widget.data['rail_index'] += 1
                        await widget.save_dict()
                    
        # Reload the rail
        self.story.active_rail.reload_rail()
        


    # Called on startup and when we have changes to the rail that have to be reloaded 
    def reload_rail(self):
        ''' Builds or rebuilds the character rail content '''

        # Top menu bar for creating characters or character connection maps
        menubar = ft.MenuBar(
            self.top_row_buttons,
            style=ft.MenuStyle(
                bgcolor="transparent", shadow_color="transparent",
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
        )

        # Hold the menubar for formatting
        header = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[menubar]
        )

        # Button to open our character (and world) templates settings page
        character_templates_button = ft.IconButton(
            ft.Icons.MANAGE_SEARCH_OUTLINED, "primary", mouse_cursor="click",  
            tooltip="Edit Character Templates", on_click=self._open_templates_editor
        )
        
        # Button to change our sort by method
        sort_by_button = ft.TextButton(
            f"Sort by: {self.story.data.get('settings', {}).get('character_rail_sort_by', "Role")}", on_click=self._change_sort_method, expand=True,
            style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ON_SURFACE)
        )
        
        # Button to open our character connections editor
        character_connections_button = ft.IconButton(
            ft.Icons.CONNECT_WITHOUT_CONTACT, "primary", mouse_cursor="click",
            tooltip="Edit Character Connections", on_click=lambda e: new_character_connection_clicked(self.story)
        )
                    
        # Hold our Tree View File controls for our two widget types
        characters = []
        character_connection_maps = []

        for widget in self.story.widgets:
            if widget.data.get('tag', "") == "character":
                characters.append(widget)
            elif widget.data.get('tag', "") == "character_connection_map":
                character_connection_maps.append(WidgetRailItem(widget))       
        

        characters.sort(key=lambda c: c.data.get('rail_index', 0))
        reorderable_sorted_characters = [ft.ReorderableDragHandle(WidgetRailItem(char)) for char in characters]
        
        

        # Build the content of our rail
        content = IsolatedListView(
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            expand=True,
            controls=[
                # Spacer and new item text field
                ft.Container(height=6),
                self.new_item_textfield,

                # Top row buttons for char templates, sort method, and character connections
                ft.Row([
                    character_templates_button,
                    #sort_by_button,
                    character_connections_button,
                ], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=0),

                ft.ReorderableListView(reorderable_sorted_characters, on_reorder=self._handle_character_reorder, show_default_drag_handles=False)

            ] + [

                # Spacer and label for Character Connection Maps Section
                ft.Divider(),
                ft.Text("Character Connection Maps", theme_style=ft.TextThemeStyle.LABEL_LARGE, weight=ft.FontWeight.BOLD, italic=True, color=ft.Colors.ON_SURFACE_VARIANT, expand=True),
                
            ] + [ccm for ccm in character_connection_maps] 
                
        )

        menu_gesture_detector = ft.GestureDetector(
            content=content, expand=True, on_hover=self.on_hovers,
            on_secondary_tap=lambda e: self.story.open_menu(self.get_menu_options()), 
            hover_interval=20,
        )

        self.controls = [
            header,
            ft.Divider(),
            menu_gesture_detector
        ]
        
        
        # Apply the update
        try:
            self.update()
        except Exception as e:
            pass
