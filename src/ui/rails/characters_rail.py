''' 
Rail for the character workspace. 
Includes the filter options at the top, a list of characters, and 
the create 'character button' at the bottom.
'''

import flet as ft
from styles.menu_option_style import MenuOptionStyle
from ui.rails.rail import Rail
from models.views.story import Story
from styles.tree_view.tree_view_file import TreeViewFile
import json
from utils.alert_dialogs.character_connection import new_character_connection_clicked


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
            ft.IconButton(ft.Icons.CONNECT_WITHOUT_CONTACT, tooltip="Edit Character Templates", on_click=self._open_templates_editor),
            ft.PopupMenuButton(
                icon=ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                tooltip="New", menu_padding=0,
                items=[
                    ft.PopupMenuItem(
                        text="Character", icon=ft.Icons.PERSON_ADD_ALT_OUTLINED,
                        on_click=self.new_item_clicked, data="character"
                    ),
                    ft.PopupMenuItem(
                        text="Character Connection Map", icon=ft.Icons.FAMILY_RESTROOM_OUTLINED,
                        on_click=self.new_item_clicked, data="character_connection_map"
                    ),
                ]
            ),
            ft.IconButton(
                icon=ft.Icons.FILE_UPLOAD_OUTLINED,
                tooltip="Upload Character",
            ),
            ft.IconButton(ft.Icons.MANAGE_SEARCH_OUTLINED, tooltip="Edit Character Connections", on_click=lambda e: new_character_connection_clicked(self.story)),
        ]

        # Sort buttons right after the top row
        self.sort_button = ft.Dropdown(
            f"Sorting by: {self.story.data.get('settings', {}).get('character_rail_sort_by', "Role")}", 
            label="Sort method", leading_icon=ft.Icons.SORT_ROUNDED, dense=True, expand=True,
            tooltip="Sort Characters By", on_change=self._new_sort_method_selected,
            options=[
                ft.DropdownOption("Age"), 
                ft.DropdownOption("Alphabetical"), 
                ft.DropdownOption("Morality", disabled=True),
                ft.DropdownOption("Nationality", disabled=True), 
                ft.DropdownOption("Occupation", disabled=True), 
                ft.DropdownOption("Role"), 
                ft.DropdownOption("Tag", disabled=True), 
                ft.DropdownOption("None"),
            ],
        )
        self.sort_button.value = self.story.data.get('settings', {}).get('character_rail_sort_by', "Role")


    # Open our settings to the templates tab
    def _open_templates_editor(self, e):    
        from models.app import app
        app.settings.selected_index = 3     # Set settings to open on the character templates tab
        self.p.overlay.clear()              # If opened from menu, make sure its closed
        self.p.go("/settings")
        

    # Called to return our list of menu options for the content rail
    def get_menu_options(self) -> list[ft.Control]:
            
        # Builds our buttons that are our options in the menu
        return [
            MenuOptionStyle(
                content=ft.PopupMenuButton(
                    content=ft.Container(
                        ft.Row([ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED), ft.Text("New", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD)], expand=True),
                        padding=ft.padding.all(8), border_radius=ft.border_radius.all(6),
                    ),
                    tooltip="New", menu_padding=0, expand=True, padding=ft.padding.all(0),
                    items=[
                        ft.PopupMenuItem(
                            text="Character", icon=ft.Icons.PERSON_OUTLINED,
                            on_click=self.new_item_clicked, data="character"
                        ),  
                        ft.PopupMenuItem(
                            text="Character Connection Map", icon=ft.Icons.FAMILY_RESTROOM_OUTLINED,
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
                        padding=ft.padding.all(8), border_radius=ft.border_radius.all(6),
                    ),
                    tooltip="Upload", menu_padding=0, expand=True,
                    items=[
                        ft.PopupMenuItem(
                            "Character", ft.Icons.PERSON_OUTLINED, 
                        ),
                        ft.PopupMenuItem(
                            text="Family Tree", icon=ft.Icons.FAMILY_RESTROOM_OUTLINED,
                        ),
                    ]
                ),
                no_padding=True
            ),
            MenuOptionStyle(
                ft.Row([
                    ft.Icon(ft.Icons.CONNECT_WITHOUT_CONTACT,),
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
    
    
    # Called when our sort method dropdown is changed
    def _new_sort_method_selected(self, e=None):
        ''' Changes our sort method based on the selected menu item '''
        self.story.data['settings']['character_rail_sort_by'] = self.sort_button.value
        self.story.save_dict()
        self.reload_rail()

    def _on_drag_accept(self, e):
        # Update whatever piece of character data to empty string and reload the rail
        # Load our data (draggables can't just pass in simple data for some reason)
        event_data = json.loads(e.data)
        
        # Grab our draggable from the event
        draggable = e.page.get_control(event_data.get("src_id"))
            
        # Grab our key and set the widget
        widget_key = draggable.data

        widget = None

        for w in self.story.widgets:
            if w.data.get('key', "") == widget_key:
                widget = w
                break

        if widget is None:
            print("Error: Widget not found for drag accept")
            return
        
        # Set our sort method
        sort_method = self.story.data.get('settings', {}).get('character_rail_sort_by', "Role")

        match sort_method:
            case "Role":
                widget.data['character_data']['Role'] = "None"
                widget.save_dict()
                widget.reload_widget()
                self.reload_rail()
            case _:
                pass

        # However we are sorting, lets set that field to an empty string for this character
        pass


    # Called on startup and when we have changes to the rail that have to be reloaded 
    def reload_rail(self):
        ''' Builds or rebuilds the character rail content '''

        header = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.SPACE_EVENLY, wrap=True,
            controls=self.top_row_buttons
        )
        
        header_2 = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[self.sort_button],
        )

             

        # Build the content of our rail
        content = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            controls=[]
        )


        
        # Grab our sort method for readability
        sort_method = self.story.data.get('settings', {}).get('character_rail_sort_by', "Role")

        # Intialize our lists
        characters_list = list(self.story.characters.values())
        non_specified_list = []

        # Build our rail depending on our sort method
        match sort_method:
            case "Age":
                # For sorting our list, sort by age. If no age specified, add to the non-specified list
                def get_age(character):
                    age = character.data.get('character_data', {}).get('Basic Info', {}).get('Age', None)
                    if age is None or age == "":
                        non_specified_list.append(character)
                    return age
                characters_list.sort(key=get_age)   # Returns not set values, then youngest -> oldest

                for character in characters_list:
                    if character not in non_specified_list:
                        content.controls.append(TreeViewFile(character))
                
                content.controls.append(ft.Text("Non-specified Age:", theme_style=ft.TextThemeStyle.LABEL_LARGE))
                for character in non_specified_list:
                    content.controls.append(TreeViewFile(character))

            case "Alphabetical":
                characters_list.sort(key=lambda c: c.data.get('title', '').lower())
                for character in characters_list:
                    content.controls.append(TreeViewFile(character))


            case "Role":
                different_roles = set()
                def get_role(character):
                    role = character.data.get('character_data', {}).get('Basic Info', {}).get('Role', None)
                    if role is None or role == "" or role == "None":
                        non_specified_list.append(character)
                    else:
                        different_roles.add(role)
                    return role
            
                characters_list.sort(key=get_role)   # Returns not set values, then alphabetically by role

                for role in sorted(different_roles):   # Future implimentation use custom roles. For now we just have 3 so we will hardcode it
                    content.controls.append(ft.Text(f"{role}:", theme_style=ft.TextThemeStyle.LABEL_LARGE))
                    for character in characters_list:
                        if role == character.data.get('character_data', {}).get('Basic Info', {}).get('Role', None):
                            content.controls.append(TreeViewFile(character))

                

                content.controls.append(ft.Text("Non-specified Role:", theme_style=ft.TextThemeStyle.LABEL_LARGE))
                for character in non_specified_list:
                    content.controls.append(TreeViewFile(character))


            # Otherwise just add them however they were loaded 
            case _:
                for character in characters_list:
                    content.controls.append(TreeViewFile(character))
        

        content.controls.append(ft.Container(height=6))
        # Append our hidden textfield for creating new items
        content.controls.append(self.new_item_textfield)

        # Add container to the bottom to make sure the drag target and gesture detector fill the rest of the space
        content.controls.append(ft.Container(expand=True))

        # Wrap the gd in a drag target so we can move characters here
        dt = ft.DragTarget(
            group="widgets",
            content=content,     # Our content is the content we built above
            on_accept=self._on_drag_accept
        )

        menu_gesture_detector = ft.GestureDetector(
            content=dt, expand=True, on_hover=self.on_hovers,
            on_secondary_tap=lambda e: self.story.open_menu(self.get_menu_options()), hover_interval=20,
        )

        # Set our content to be a column
        self.content = ft.Column(
            spacing=0,
            expand=True,
            controls=[
                header,
                ft.Divider(),
                ft.Container(height=6),
                header_2,
                ft.Container(height=6),
                menu_gesture_detector
            ]
        )
        
        # Apply our update
        self.p.update()
