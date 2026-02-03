import flet as ft


def new_character_connection_clicked(character):

    # Simple class to handle our connection row controls since we manipulate a lot of unreadable data otherwise
    class ConnectionCtrl(ft.Row):
        def __init__(self, key: str=None, name: str=None, tags: str=None):

            self.k: str = key if key is not None else ""      # Key of the character we are connecting to (Key is reserved in controls, so use k)
            self.name: str = name if name is not None else "Select a character"     # Set name if we are a previously loaded connection
            self.tags: str = tags if tags is not None else ""     # Tags/Type of connection    

            # Controls
            self.name_text = ft.Text(self.name, expand=True, selectable=True, weight=ft.FontWeight.BOLD)   # Control to display the name

            self.char_select_btn = ft.PopupMenuButton(  # Button to select character for the connection
                icon=ft.Icons.ARROW_DROP_DOWN, tooltip="Select Character",
                items=self._get_char_options(),
                menu_padding=ft.padding.all(0)
            )

            self.tags_textfield= ft.TextField(
                hint_text="Connection Type (Friend, Father, Classmate, etc.)", expand=True, on_blur=self._update_tags, value=self.tags,
                autofill_hints=[ft.AutofillHint.NICKNAME, ft.AutofillHint.GIVEN_NAME],
            )

            # Row constructor
            super().__init__(
                [
                    self.char_select_btn,   # Button to select character will go here
                    self.name_text,        # Name text will go here
                    self.tags_textfield,   # Tags textfield will go here
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, tooltip="Delete Connection", on_click=self._delete_connection),
                ]
            )

        # Set name and key
        def _set_name_and_key(self, e):
            self.name = e.control.text
            self.k = e.control.data
            update_connections()
            
        # Updates our tags when tf changes
        def _update_tags(self, e):
            self.tags = e.control.value
            update_connections()

        # Deletes this connection control and updates our existing connections
        def _delete_connection(self, e):
            nonlocal content
                    
            if self.k in existing_connections:
                del existing_connections[self.k]   # Remove from our existing connections dict

            # 2) Remove the row from UI; existing_connections will be rebuilt by update_connections()
            if self in content.controls:
                content.controls.remove(self)
                content.update()

            update_connections()

        # Grabs all our character options for the dropdown
        def _get_char_options(self) -> list[ft.DropdownOption]:
            ''' Excludes the current character we are editing and any already selected connections '''
            nonlocal character, existing_connections
            options = []

            for char in character.story.characters.values():
                char_key = char.data.get('key')
                if char_key != character.data.get('key') and char_key not in existing_connections:
                    options.append(
                        ft.PopupMenuItem(
                            text=char.data.get('title'),
                            on_click=self._set_name_and_key,
                            content=ft.Text(char.data.get('title'), color=char.data.get('color', ft.Colors.ON_SURFACE)),
                            data=char.data.get('key')
                        )
                    )

            return options

    # Closes our dialog and saves our character data
    async def _save_and_close(e):
        nonlocal dlg, existing_connections

        # Set a dict we can play with to get rid of any empty keys
        safe_connections = existing_connections.copy()

        # Remove any empty keys
        for key in list(safe_connections.keys()):
            if key == "":
                del safe_connections[key]    # Remove any empty keys


        # Set our characters connection data to the safe connections
        character.data['character_data']['Connections'] = safe_connections

        # Update matching characters connections too (to keep both sides of the connection in sync)
        for conn in safe_connections.keys():
            connected_character = character.story.characters.get(conn)

            # Grab the connected character and update their connection data
            if connected_character:
                connected_character.data['character_data']['Connections'][character.data.get('key')] = {
                    'title': character.data.get('title'),
                    'tags': safe_connections[conn].get('tags', '')
                }
                connected_character.save_dict()
                connected_character.reload_widget()

        # Go through all our characters now and remove any connections to us that we don't have anymore
        for char in character.story.characters.values():
            if char.data.get('key') != character.data.get('key') and char.data.get('key') not in safe_connections:

                if character.data.get('key') in char.data.get('character_data', {}).get('Connections', {}):
                    del char.data['character_data']['Connections'][character.data.get('key')]
                    char.save_dict()
                    char.reload_widget()
                

        # Delete connections of us in other characters that we don't have (they were deleted)
                


        character.save_dict()
        character.p.close(dlg)
        character.reload_widget()

   
    # Button clicked to add a new connection. Adds a dropdown + textfield row
    def _add_new_connection(e):
        nonlocal content
        new_conn_ctrl = ConnectionCtrl()
        content.controls.insert(-1, new_conn_ctrl)
        content.update()

    # Updates our keys in our existing connections dict so we can manage the character options in dropdowns
    def update_connections():
        nonlocal existing_connections, content
        
        temp_connections = {}       # Build a temp dict to hold our connections

        # Rebuild our keys based on our current controls
        for ctrl in content.controls:
            if isinstance(ctrl, ConnectionCtrl):
                temp_connections.update({ctrl.k: {'title': ctrl.name, 'tags': ctrl.tags}})

        # Set our existing ocnnections to our newly built temp from most current data
        existing_connections = temp_connections

        # Makes sure our char options are updated and text value is correct
        for ctrl in content.controls:
            if isinstance(ctrl, ConnectionCtrl):
                ctrl.name_text.value = ctrl.name
                ctrl.char_select_btn.items = ctrl._get_char_options()   # Update our dropdown options

                # Update styling
                char = character.story.characters.get(ctrl.k)
                if char:
                    color = char.data.get('color', ft.Colors.ON_SURFACE)
                    ctrl.char_select_btn.icon_color = color
                    ctrl.name_text.color = color
                    ctrl.tags_textfield.cursor_color = color
                    ctrl.tags_textfield.focused_border_color = color

                

        # TODO: Update text, and textfield color and cursor
        character.p.update()
                


    # Sets our content to add too
    content = ft.Column(
        [
            ft.Row([
                ft.Container(width=40),  # Spacer for the Drop down buttons
                ft.Text("Name", expand=True, theme_style=ft.TextThemeStyle.LABEL_LARGE), 
                ft.Container(width=50),  # Spacer
                ft.Text("Type", theme_style=ft.TextThemeStyle.LABEL_LARGE),
                ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.ON_SURFACE, scale=.5, tooltip="Seperate multiple connection types with commas (example: Friend, Classmate)"),
                ft.Container(expand=True),
                ft.Container(width=40)  # Spacer for the remove buttons
            ]),
            ft.Divider()
        ], 
        scroll="auto",
        width=character.p.width * .5,
    )
        
    
    existing_connections = character.data.get('character_data', {}).get('Connections', {})  # Grab our existing connections

    for key, value in existing_connections.items():
        name = value.get('title')
        tags = value.get('tags', '')
        content.controls.append(ConnectionCtrl(key, name, tags))
        
    # Refresh connections now that all our existing ones are loaded
    update_connections()

    # Add button to add new connections
    content.controls.append(
        ft.IconButton(
            ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, tooltip="Add New Connection",
            on_click=_add_new_connection
        )
    )

    # Alert dialog to show everything we've built
    dlg = ft.AlertDialog(
        title=ft.Text(f"{character.title}'s Connections:"),
        content=ft.AutofillGroup(content),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: character.p.close(dlg), style=ft.ButtonStyle(color=ft.Colors.ERROR)),
            ft.TextButton("Save", on_click=_save_and_close),   # Start enabled to just save existing connections
        ],
    )
    

    character.p.open(dlg)