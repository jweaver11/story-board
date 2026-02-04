import flet as ft
from models.dataclasses.connection import ConnectionDataClass
from styles.colors import colors



def new_character_connection_clicked(char1_key: str, story, char_name: str):

    # Simple class to handle our connection row controls since we manipulate a lot of unreadable data otherwise
    class ConnectionCtrl(ft.Row):
        def __init__(self, char2_key: str=None, name: str=None, tags: str=None, icon: str=None, color: str=None):

            self.char2_key: str = char2_key if char2_key is not None else ""      # Key of the character we are connecting to (Key is reserved in controls, so use k)
            self.name: str = name if name is not None else "Select a character"     # Set name if we are a previously loaded connection
            self.tags: str = tags if tags is not None else ""     # Tags/Type of connection    

            # Controls
            self.name_text = ft.Text(self.name, width=150, overflow=ft.TextOverflow.ELLIPSIS, selectable=True, weight=ft.FontWeight.BOLD)   # Control to display the name

            self.char_select_btn = ft.PopupMenuButton(  # Button to select character for the connection
                icon=ft.Icons.ARROW_DROP_DOWN, tooltip="Select Character",
                items=self._get_char_options(),
                menu_padding=ft.padding.all(0)
            )

            self.tags_textfield= ft.TextField(      # Textfield to enter connection tags
                hint_text="Connection Type (Friend, Father, Classmate, etc.)", on_blur=self._update_tags, value=self.tags,
                autofill_hints=[ft.AutofillHint.NICKNAME, ft.AutofillHint.GIVEN_NAME], expand=True,
            )

            self.icon_button = ft.PopupMenuButton(      # Button to change the connection icon 
                icon=ft.Icons.CONNECT_WITHOUT_CONTACT,
                tooltip="Change this connection's icon",
                padding=ft.Padding(0,0,0,0),
                #items=self._get_icon_options()
            )

            # Change color
            self.color_button = ft.PopupMenuButton(     # Button to change the connection color
                icon=ft.Icons.COLOR_LENS_OUTLINED,
                tooltip="Change this connection's color",
                padding=ft.Padding(0,0,0,0),
                #items=self._get_color_options()
            )
        

            # Row constructor
            super().__init__(
                [
                    self.char_select_btn,      
                    self.name_text,             
                    self.tags_textfield,        
                    self.icon_button,
                    self.color_button,          
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, tooltip="Delete Connection", on_click=self._delete_connection),     # Delete button
                ]
            )

        # Set name and key
        def _set_name_and_key(self, e):
            self.name = e.control.text
            self.char2_key = e.control.data
            update_connections()
            
        # Updates our tags when tf changes
        def _update_tags(self, e):
            self.tags = e.control.value
            update_connections()

        # Deletes this connection control and updates our existing connections
        def _delete_connection(self, e):
            nonlocal content

            # Remove this connection from the data
            for conn in existing_connections:
                if conn.get('char2_key') == self.char2_key or conn.get('char1_key') == self.char2_key:
                    if conn.get('char1_key') == char1_key or conn.get('char2_key') == char1_key:
                        existing_connections.remove(conn)
                        break
                    
            # Remove ourselves from the content controls and apply update
            content.controls.remove(self)   
            story.p.update()

        # Grabs all our character options for the dropdown. Exclude already existing connections with those characters
        def _get_char_options(self) -> list[ft.DropdownOption]:
            ''' Excludes the current character we are editing and any already selected connections '''
            
            options = []        # Character options stored as keys
            ctrl_options = []   # Character options stored as dropdown items
            # Key of all characters in the story
            for char_key in story.characters.keys():
                options.append(char_key)

            options.remove(char1_key)   # Remove our primary character from options

            # Remove any characters we already have connections to
            for connection in story.data.get('connections', {}).values():
                if connection.get('char1_key') == char1_key:
                    options.remove(connection.get('char2_key'))
                elif connection.get('char2_key') == char1_key:
                    options.remove(connection.get('char1_key'))

            # Make controls for every option
            for char_key in options:
                char = story.characters.get(char_key)
                if char:
                    ctrl_options.append(
                        ft.PopupMenuItem(
                            text=char.data.get('title'),
                            on_click=self._set_name_and_key,
                            content=ft.Text(char.data.get('title'), color=char.data.get('color', ft.Colors.ON_SURFACE)),
                            data=char.data.get('key')
                        )
                    )
                    
            return ctrl_options     # Return the formatted controls
        
        # Called when color button is clicked
        def _get_color_options(self) -> list[ft.Control]:
            ''' Returns a list of all available colors for icon changing '''

            # Called when a color option is clicked on popup menu to change icon color
            def _change_icon_color(color: str, e):
                ''' Passes in our kwargs to the widget, and applies the updates '''

                # Change our color data for this connection

                # Change our button icon color                
                pass

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
        


    # Closes our dialog and saves our character data
    async def _save_and_close(e):
        nonlocal dlg, existing_connections

        pass

   
    # Button clicked to add a new connection. Adds a dropdown + textfield row
    def _add_new_connection(e):
        nonlocal content
        new_conn_ctrl = ConnectionCtrl()
        content.controls.insert(-1, new_conn_ctrl)
        content.update()

    # Updates our keys in our existing connections dict so we can manage the character options in dropdowns
    def update_connections():
        nonlocal existing_connections, content
        
        pass


    # Sets our content to add too
    content = ft.Column(
        [
            ft.Row([
                ft.Container(width=40),  # Spacer for the Drop down buttons
                ft.Text("Connect With", expand=True, theme_style=ft.TextThemeStyle.LABEL_LARGE), 
                ft.Text("Type", theme_style=ft.TextThemeStyle.LABEL_LARGE),
                ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.ON_SURFACE, scale=.5, tooltip="Seperate multiple connection types with commas (example: Friend, Classmate)"),
                ft.Container(expand=True),
                ft.Text("Icon", theme_style=ft.TextThemeStyle.LABEL_LARGE, width=40),
                ft.Text("Color", theme_style=ft.TextThemeStyle.LABEL_LARGE, expand=True, text_align=ft.TextAlign.RIGHT),
                ft.Container(width=40)  # Spacer for the remove buttons
            ]),
            ft.Divider()
        ], 
        scroll="auto",
        width=story.p.width * .5,
    )
        
    
    existing_connections = story.data.get('connections', []).copy()  # Grab our existing connections

    for connection in existing_connections:
        if char1_key == connection.get('char1_key') or char1_key == connection.get('char2_key'):
            continue
        else:
            existing_connections.remove(connection)


    for conn in existing_connections:
        key = conn.get('char2_key') if conn.get('char1_key') == char1_key else conn.get('char1_key')    # Key of other character for connection
        name = conn.get('char2_name') if conn.get('char1_key') == char1_key else conn.get('char1_name')   # Name of other character for connection for easier ID
        tags = conn.get('tags', '')     
        icon = conn.get('icon', 'connect_without_contact')      
        color = conn.get('color', 'primary')    
        content.controls.append(ConnectionCtrl(key, name, tags, icon, color))
        
    # Refresh connections now that all our existing ones are loaded
    #update_connections()

    # Add button to add new connections
    content.controls.append(
        ft.IconButton(
            ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, tooltip="Add New Connection",
            on_click=_add_new_connection
        )
    )

    # Alert dialog to show everything we've built
    dlg = ft.AlertDialog(
        title=ft.Text(f"{char_name}'s Connections:"),
        content=ft.AutofillGroup(content),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: story.p.close(dlg), style=ft.ButtonStyle(color=ft.Colors.ERROR)),
            ft.TextButton("Save", on_click=_save_and_close),   # Start enabled to just save existing connections
        ],
    )
    

    story.p.open(dlg)