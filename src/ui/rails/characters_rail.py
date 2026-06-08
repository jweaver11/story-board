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
from styles.rail.tree_view_file import TreeViewFile
import json
from utils.alert_dialogs.character_connection import new_character_connection_clicked
from models.isolated_controls.column import IsolatedColumn
from models.isolated_controls.list_view import IsolatedListView
import asyncio



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
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), 
                        tooltip="Visualize the connections between the characters in your story"
                    ),  
                ],
                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10)),
                style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
            ),
            ft.SubmenuButton(
                ft.Container(
                    ft.Icon(ft.Icons.FILE_UPLOAD_OUTLINED, ft.Colors.OUTLINE),
                    shape=ft.BoxShape.CIRCLE,
                    alignment=ft.Alignment.CENTER
                ),
                [     
                    
                ],
                disabled=True,
                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10)),
                style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
            ),
            
        ]

        self.reload_rail()



    # Open our settings to the templates tab
    async def _open_templates_editor(self, e=None):    
        from models.app import app
        app.settings.selected_index = 2     # Set settings to open on the character templates tab
        self.p.overlay.clear()              # If opened from menu, make sure its closed
        await self.p.push_route("/settings")
        

    # Called to return our list of menu options for the content rail
    def get_menu_options(self) -> list[ft.Control]:
            
        # Builds our buttons that are our options in the menu
        return [
            MenuOptionStyle(
                content=ft.SubmenuButton(
                    ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY), 
                            ft.Text("New", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Icon(ft.Icons.ARROW_RIGHT),
                        ], expand=True),
                        padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(6), shape=ft.RoundedRectangleBorder(radius=10),
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
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                            tooltip="Visualize the connections between the characters in your story"
                        ),
                    ],
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                ),
                no_padding=True, no_effects=True
            ),

            # Upload options
            MenuOptionStyle(
                content=ft.SubmenuButton(
                    ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.FILE_UPLOAD_OUTLINED, ft.Colors.PRIMARY), 
                            ft.Text("Upload", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Icon(ft.Icons.ARROW_RIGHT),
                        ], expand=True),
                        padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(6), shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                    [
                        
                    ],
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                ),
                no_padding=True, no_effects=True, 
            ),
            #MenuOptionStyle(
                #ft.Row([
                    #ft.Icon(ft.Icons.CONNECT_WITHOUT_CONTACT, ft.Colors.PRIMARY),
                    #ft.Text(f"Edit Character\nTemplates", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
                #]),
                #on_click=self._open_templates_editor
            #),      
            #MenuOptionStyle(
                #ft.Row([
                    #ft.Icon(ft.Icons.MANAGE_SEARCH_OUTLINED, ft.Colors.PRIMARY, tooltip="Edit Character Connections"),
                    #ft.Text("Edit Character\nConnections", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
                #]),
                #on_click=lambda e: new_character_connection_clicked(self.story),
            #)
        ]
        

    # Called on startup and when we have changes to the rail that have to be reloaded 
    def reload_rail(self):
        ''' Builds or rebuilds the character rail content '''

        async def _change_sort_method(e: ft.Event):
            new_sort_method = e.data
            self.story.data['character_rail_sort_method'] = new_sort_method
            await self.story.save_dict()
            self.story.active_rail.reload_rail()

        async def _change_sort_direction(e: ft.Event):

            old_sort_method = self.story.data.get('character_rail_sort_direction', "Ascending")
            if old_sort_method == "Ascending":
                self.story.data['character_rail_sort_direction'] = "Descending"
                e.control.tooltip = "Sort Direction: Descending"
                e.control.icon = ft.CupertinoIcons.SORT_UP
            else:
                self.story.data['character_rail_sort_direction'] = "Ascending"
                e.control.tooltip = "Sort Direction: Ascending"
                e.control.icon = ft.CupertinoIcons.SORT_DOWN

            await self.story.save_dict()

            characters_list_view.reverse = self.story.data.get('character_rail_sort_direction', "Ascending") == "Descending"
            ccm_list_view.reverse = self.story.data.get('character_rail_sort_direction', "Ascending") == "Descending"
            characters_list_view.update()
            ccm_list_view.update()
            e.control.update()

        async def _reorder_widget(e: ft.OnReorderEvent):
            ''' Handles the reordering and reloading of characters based on their new positions on the rail when we drag and drop them '''
            
            # If we didn't move, return out
            if e.old_index == e.new_index:
                return
            
            # Move the control up the list
            e.control.controls.insert(e.new_index, e.control.controls.pop(e.old_index))
            e.control.update()

            # Update the indices of the characters we dragged past as well
            for idx, ctrl in enumerate(e.control.controls):
                widget = ctrl.content.widget
                if widget.data.get('rail_index', 999) != idx:
                    widget.data['rail_index'] = idx 
                    await widget.save_dict()

        # Button to open our character connections editor
        character_connections_button = ft.IconButton(
            ft.Icons.CONNECT_WITHOUT_CONTACT, "primary", mouse_cursor="click",
            tooltip="Edit Character Connections", on_click=lambda e: new_character_connection_clicked(self.story)
        )
        

        menubar = ft.MenuBar(
            self.top_row_buttons,
            #expand=True,
            style=ft.MenuStyle(
                bgcolor="transparent", shadow_color="transparent",
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
        )

        header = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[menubar]
        )

        # Button to open our character (and world) templates settings page
        character_templates_button = ft.IconButton(
            #ft.Icons.MANAGE_SEARCH_OUTLINED, 
            ft.Icons.EDIT_NOTE_OUTLINED,
            "primary", mouse_cursor="click",  
            tooltip="Edit Character Templates", on_click=self._open_templates_editor
        )

        
        # Methods: index, color
        sort_dropdown = ft.Dropdown(
            self.story.data.get('character_rail_sort_method', "Index"),
            [
                ft.DropdownOption(
                    "Default", style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=10)),
                    tooltip="Sort characters by the order they were loaded. On Windows, usually alphabetical. On Mac, usually by creation date."
                ),
                ft.DropdownOption(
                    "Index", style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=10)),
                    tooltip="Sort characters by a reorderable index so you can drag characters up and down on the rail."
                ), 
                ft.DropdownOption(
                    "Color", style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=10)),
                    tooltip="Sort characters by their color."
                )
            ],
            label="Sort by",
            dense=True, expand=True,
            on_select=_change_sort_method,
            border_color=ft.Colors.OUTLINE_VARIANT,
            leading_icon=ft.IconButton(
                ft.CupertinoIcons.SORT_DOWN if self.story.data.get('character_rail_sort_direction', "Ascending") == "Ascending" else ft.CupertinoIcons.SORT_UP,
                ft.Colors.PRIMARY, 
                tooltip=f"Sort Direction: {self.story.data.get('character_rail_sort_direction', 'Ascending')}", 
                on_click=_change_sort_direction, mouse_cursor="click", 
            ),
            menu_style=ft.MenuStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10)),
        )
           
        # List for our characters and character connection maps
        characters = []
        character_connection_maps = []

        # Add all character and CCM widgets to their respective lists
        for widget in self.story.widgets:
            if widget.data.get('tag', "") == "character":
                characters.append(widget)
            elif widget.data.get('tag', "") == "character_connection_map":
                character_connection_maps.append(widget)    

        # Sort lists by color
        if self.story.data.get('character_rail_sort_method', "Index") == "Color":

            # Sort our characters and ccms
            characters.sort(key=lambda c: c.data.get('color', "default"))
            character_connection_maps.sort(key=lambda c: c.data.get('color', "default"))

            # Build our controls for characters and ccms
            character_controls = [WidgetRailItem(char) for char in characters]
            ccm_controls = [WidgetRailItem(ccm) for ccm in character_connection_maps] 

        # Sort lists by index (default)
        elif self.story.data.get('character_rail_sort_method', "Index") == "Index":
            characters.sort(key=lambda c: c.data.get('rail_index', 0))
            character_connection_maps.sort(key=lambda c: c.data.get('rail_index', 0))
            character_controls = [ft.ReorderableDragHandle(WidgetRailItem(char)) for char in characters]
            ccm_controls = [ft.ReorderableDragHandle(WidgetRailItem(ccm)) for ccm in character_connection_maps]

            # Update their index by their actual rail position now, since new characters start with index of 999
            for idx, char in enumerate(characters):
                if char.data.get('rail_index', 999) != idx:
                    char.data['rail_index'] = idx 
                    self.p.run_task(char.save_dict)

            for idx, ccm in enumerate(character_connection_maps):
                if ccm.data.get('rail_index', 999) != idx:
                    ccm.data['rail_index'] = idx 
                    self.p.run_task(ccm.save_dict)

        # Otherwise just sort by the way the system loaded them
        else:
            character_controls = [WidgetRailItem(char) for char in characters]
            ccm_controls = [WidgetRailItem(ccm) for ccm in character_connection_maps]
      
        
        
        characters_list_view = ft.ReorderableListView(
            character_controls, 
            on_reorder=_reorder_widget, 
            spacing=0, show_default_drag_handles=False, 
            reverse=self.story.data.get('character_rail_sort_direction', "Ascending") == "Descending"
        )

        ccm_list_view = ft.ReorderableListView(
            ccm_controls,
            on_reorder=_reorder_widget,
            spacing=0, show_default_drag_handles=False, 
            reverse=self.story.data.get('character_rail_sort_direction', "Ascending") == "Descending"
        )
        

        # Build the content of our rail
        content = IsolatedListView(
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            expand=True,
            controls=[
                # Spacer and new item text field
                ft.Container(height=6),
                self.new_item_textfield,

                ft.Text("\tCharacters", theme_style=ft.TextThemeStyle.LABEL_LARGE, weight=ft.FontWeight.BOLD, italic=True, color=ft.Colors.ON_SURFACE_VARIANT, expand=True),

                # Our characters
                characters_list_view,

                # Spacer and label for Character Connection Maps Section
                ft.Divider(),
                ft.Text("\tCharacter Connection Maps", theme_style=ft.TextThemeStyle.LABEL_LARGE, weight=ft.FontWeight.BOLD, italic=True, color=ft.Colors.ON_SURFACE_VARIANT, expand=True),
                
                # Our CCM's
                ccm_list_view,

                ft.Container(expand=True)
            ] 
                
        )

        menu_gesture_detector = ft.GestureDetector(
            content=content, expand=True, on_hover=self._set_menu_coords,
            on_secondary_tap=lambda _: self.story.open_menu(self.get_menu_options()), 
            hover_interval=20,
        )

        self.controls = [
            header,
            ft.Divider(),
            menu_gesture_detector
        ]

        self.controls = [
            header,
            ft.Divider(leading_indent=8),
            menu_gesture_detector,
            ft.Container(ft.Row([sort_dropdown, character_templates_button]), margin=ft.Margin.symmetric(horizontal=4)),
        ]
        
        
        # Apply the update
        try:
            self.update()
        except Exception:
            pass
