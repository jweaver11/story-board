import flet as ft
from models.dataclasses.character_connection import ConnectionDataClass
from styles.colors import colors
from styles.icons import connection_icons



def new_character_connection_clicked(story):

    # Simple class to handle our connection row controls since we manipulate a lot of unreadable data otherwise
    class ConnectionCtrl(ft.Row):
        def __init__(self, data: dict, index: int):
            
            self.idx = index        # Save our position for more effecient data updating and deleting
            
            # Row constructor
            super().__init__(data=data)

            char1 = story.characters.get(data.get('char1_key'))
            char2 = story.characters.get(data.get('char2_key'))
            if char1:
                init_color1 = char1.data.get('color', ft.Colors.ON_SURFACE)
            else:
                init_color1 = ft.Colors.ON_SURFACE
            if char2:
                init_color2 = char2.data.get('color', ft.Colors.ON_SURFACE)
            else:
                init_color2 = ft.Colors.ON_SURFACE

            # Controls -------------------------
            # Display our names
            self.char1_button = ft.PopupMenuButton(
                ft.Container(
                    ft.Text(
                        self.data.get('char1_name', "Select Character 1"), width=150, color=init_color1,
                        overflow=ft.TextOverflow.ELLIPSIS, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER
                    ),
                    padding=ft.padding.all(6), border_radius=ft.border_radius.all(8), ink=True,
                ), tooltip="Select Character 1", items=self.get_char_options(tag="char1"), menu_padding=ft.padding.all(0)
            )
            self.icon_button = ft.PopupMenuButton(      # Button to change the connection icon 
                icon=self.data.get('icon', ft.Icons.CONNECT_WITHOUT_CONTACT),
                tooltip="Change Connection's Icon",
                menu_padding=ft.Padding(0,0,0,0), icon_color=self.data.get('color', ft.Colors.PRIMARY),
                items=self._get_icon_options()
            )
            self.char2_button = ft.PopupMenuButton(
                ft.Container(
                    ft.Text(
                        self.data.get('char2_name', "Select Character 2"), width=150, color=init_color2,
                        overflow=ft.TextOverflow.ELLIPSIS, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER
                    ),
                    padding=ft.padding.all(6), border_radius=ft.border_radius.all(8), ink=True
                ), tooltip="Select Character 2", items=self.get_char_options(tag="char2"), menu_padding=ft.padding.all(0)
            )

            self.desc_textfield= ft.TextField(      # Textfield to enter connection tags
                hint_text="Descriptors (Friend, Rival, etc.)", on_blur=self._update_description, dense=True, capitalization=ft.TextCapitalization.SENTENCES,
                expand=True, value=self.data.get('tags', ''),
                cursor_color=self.data.get('color', ft.Colors.PRIMARY), focused_border_color=self.data.get('color', ft.Colors.PRIMARY)
            )

            
            # Change color
            self.color_button = ft.PopupMenuButton(     # Button to change the connection color
                icon=ft.Icons.COLOR_LENS_OUTLINED,
                tooltip="Change Connection's Color",
                menu_padding=ft.padding.all(0), icon_color=self.data.get('color', ft.Colors.PRIMARY),
                items=self._get_color_options()
            )

            # Add our controls to the row
            self.controls.extend([
                self.char1_button,   
                self.icon_button,  
                self.char2_button,        
                self.desc_textfield,        
                self.color_button, 
                ft.IconButton(ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, tooltip="Delete Connection", on_click=self._delete_connection),     # Delete button
            ])

        # Set name and key
        def _set_name_and_key(self, e):
            name = e.control.content.value  
            data = e.control.data

            key = data[0]        # Character key
            tag = data[1]        # Which character are we setting (char1/char2)

            # Update the data
            if tag == "char1": 
                self.data['char1_name'] = name
                self.data['char1_key'] = key
            else:
                self.data['char2_name'] = name
                self.data['char2_key'] = key

            self.char1_button.items = self.get_char_options(tag="char1")
            self.char2_button.items = self.get_char_options(tag="char2")

            # Update the existing connections dict we are working with to match our data
            update_connection(self)

            # Update the controls
            self.char1_button.content.content.value = self.data.get('char1_name', "Select Character 1")
            self.char2_button.content.content.value = self.data.get('char2_name', "Select Character 2")

            # Grab selected characters to update button colors
            char1 = story.characters.get(self.data.get('char1_key'))
            char2 = story.characters.get(self.data.get('char2_key'))
            if char1:
                self.char1_button.content.content.color = char1.data.get('color', ft.Colors.ON_SURFACE)
            if char2:
                self.char2_button.content.content.color = char2.data.get('color', ft.Colors.ON_SURFACE)

            story.p.update()

        # Updates our tags when tf changes
        def _update_description(self, e):
            self.data['description'] = e.control.value
            update_connection(self)

        # Deletes this connection control and updates our existing connections
        def _delete_connection(self, e):
            nonlocal content

            # Remove our data from the existing connections list and visually
            existing_connections.pop(self.idx)
            content.controls.remove(self) 

            # Go through all remaining connection controls and update their idx to match their new position
            i = 0
            for ctrl in content.controls:
                if isinstance(ctrl, ConnectionCtrl):
                    ctrl.idx = i  
                    i += 1
            story.p.update()

        # Grabs all our character options for the dropdown. Exclude already existing connections with those characters
        def get_char_options(self, tag: str) -> list[ft.PopupMenuButton]:
            ''' Excludes the already selected character (If one exists) and returns a list of all other characters as control items '''
            
            options = []        # Character options stored as keys
            ctrl_options = []   # Character options stored as dropdown items
            # Key of all characters in the story
            for char_key in story.characters.keys():
                options.append(char_key)

            # Make controls for every option
            for key, character in story.characters.items():
              
                ctrl_options.append(
                    ft.PopupMenuItem(
                        text=character.data.get('title'),       # Set title for display
                        on_click=self._set_name_and_key,
                        content=ft.Text(character.data.get('title'), color=character.data.get('color', ft.Colors.ON_SURFACE)),
                        data=[key, tag]         # Set key for easy retrievel
                    )
                )

            # Exclude already selected character from options so they can't connect to themselves
            if tag == "char1":
                if self.data.get('char2_key') in options:
                    # Remove char2 from options
                    remove_key = self.data.get('char2_key')
                    ctrl_options = [ctrl for ctrl in ctrl_options if ctrl.data[0] != remove_key]
            else:
                if self.data.get('char1_key') in options:
                    # Remove char1 from options
                    remove_key = self.data.get('char1_key')
                    ctrl_options = [ctrl for ctrl in ctrl_options if ctrl.data[0] != remove_key]
                    
            return ctrl_options     # Return the formatted controls
        
        def _get_icon_options(self) -> list[ft.Control]:
            ''' Returns a list of all available icons for icon changing '''

            # Called when an icon option is clicked on popup menu to change icon
            def _change_icon(icon: str, e):
                ''' Passes in our kwargs to the widget, and applies the updates '''

                # Set our data and update our button icon
                self.data['icon'] = icon
                self.icon_button.icon = icon

                # Update our existing connections data to match our new data
                update_connection(self)
                story.p.update()

            # List for our icons when formatted
            icon_controls = [] 

            # Create our controls for our icon options
            for icon in connection_icons:
                icon_controls.append(
                    ft.PopupMenuItem(
                        content=ft.Icon(icon),
                        on_click=lambda e, ic=icon: _change_icon(ic, e)
                    )
                )

            return icon_controls        #TODO: SOMETHING BREAKING WHEN SWAPPING CHARACTERS
        
        # Called when color button is clicked
        def _get_color_options(self) -> list[ft.Control]:
            ''' Returns a list of all available colors for icon changing '''

            # Called when a color option is clicked on popup menu to change icon color
            def _change_icon_color(color: str, e):
                ''' Passes in our kwargs to the widget, and applies the updates '''

                # Set our data and update our button colors
                self.data['color'] = color
                self.icon_button.icon_color = color
                self.color_button.icon_color = color
                self.desc_textfield.cursor_color = color
                self.desc_textfield.focused_border_color = color

                # Update our existing connections data to match our new data
                update_connection(self)
                story.p.update()

            # List for our colors when formatted
            color_controls = [] 

            # Create our controls for our color options
            for color in colors:
                color_controls.append(
                    ft.PopupMenuItem(
                        content=ft.Text(color.capitalize(), weight=ft.FontWeight.BOLD, color=color),
                        on_click=lambda e, col=color: _change_icon_color(col, e)
                    )
                )

            return color_controls
        
    def update_connection(ctrl: ConnectionCtrl):
        ''' Updates our existing connections data with the data from the passed in control '''
        nonlocal existing_connections

        # Update our existing connections data at the control's index with the new data
        existing_connections[ctrl.idx] = ctrl.data.copy()    

    # Button clicked to add a new connection. Adds a dropdown + textfield row
    def _add_new_connection(e):
        nonlocal content, existing_connections

        new_connection_dict = ConnectionDataClass().__dict__


        existing_connections.append(new_connection_dict)   # Add empty connection to our existing connections to be filled out
        new_conn_ctrl = ConnectionCtrl(new_connection_dict, len(existing_connections)-1)   # Create new connection control
        content.controls.insert(-1, new_conn_ctrl)
        content.update()

    # Closes our dialog and saves our character data
    async def _save_and_close(e):
        from models.mini_widgets.character_connection import CharacterConnection
        nonlocal dlg, existing_connections
        
        story.data['connections'] = existing_connections.copy()   # Save our updated connections back to the story data
        story.save_dict()

        # Reload all our character widgets to update their connections
        for char in story.characters.values():
            if char.visible:
                char.reload_widget()    

        # Reload all our character connection maps to update their connections
        for ccm in story.character_connection_maps.values():

            # Update any connection mini widgets as well
            for mw in ccm.mini_widgets:
                if mw.visible and isinstance(mw, CharacterConnection):
                    mw.reload_mini_widget()

            # Update any visible character connection maps
            if ccm.visible:
                ccm.reload_widget()     

        story.p.show_dialog(dlg)
        story.p.update()


    # Sets our content to add too
    content = ft.Column(
        [
            ft.Row([
                ft.Text("Character 1", theme_style=ft.TextThemeStyle.LABEL_LARGE, width=162, text_align=ft.TextAlign.CENTER), 
                ft.Text("Icon", theme_style=ft.TextThemeStyle.LABEL_LARGE, width=40, text_align=ft.TextAlign.CENTER),
                ft.Text("Character 2", theme_style=ft.TextThemeStyle.LABEL_LARGE, width=162, text_align=ft.TextAlign.CENTER), 
                ft.Text("Description", text_align=ft.TextAlign.CENTER, theme_style=ft.TextThemeStyle.LABEL_LARGE, tooltip="Connection Type (Friend, Father, Classmate, etc.)", expand=True),
                ft.Text("Color", theme_style=ft.TextThemeStyle.LABEL_LARGE, width=40, text_align=ft.TextAlign.CENTER),
                ft.Container(width=40)
            ]),
            ft.Divider()
        ], 
        scroll="auto",
        width=story.p.width * .5,
    )
        
    existing_connections = story.data.get('connections', []).copy()  # Grab our existing connections

    # Load existing connections into our content
    for idx, conn in enumerate(existing_connections):
        content.controls.append(ConnectionCtrl(conn, idx))
   
    # Add button to add new connections
    content.controls.append(
        ft.IconButton(
            ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, tooltip="Add New Connection",
            on_click=_add_new_connection
        )
    )

    # Alert dialog to show everything we've built
    dlg = ft.AlertDialog(
        title=ft.Text(f"Character Connections Editor"),
        content=content,
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: story.p.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR), scale=1.2),
            ft.Container(width=12),   # Spacer
            ft.TextButton("Save", on_click=_save_and_close, scale=1.2),   # Start enabled to just save existing connections
        ],
    )
    

    story.p.show_dialog(dlg)