import flet as ft
from models.dataclasses.connection import ConnectionDataClass
from styles.colors import colors



def new_character_connection_clicked(story):

    # Simple class to handle our connection row controls since we manipulate a lot of unreadable data otherwise
    class ConnectionCtrl(ft.Row):
        def __init__(
            self, 
            data: dict,
            index: int
        ):
            
            self.idx = index        # Save our position for more effecient data updating and deleting
            
            # Row constructor
            super().__init__(data=data)

            # Controls -------------------------
            # Display our names
            self.name1_button = ft.PopupMenuButton(
                ft.Container(
                    ft.Text(
                        self.data.get('char1_name', "Select Character 1"), width=150, 
                        overflow=ft.TextOverflow.ELLIPSIS, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER
                    ),
                    padding=ft.padding.all(6), border_radius=ft.border_radius.all(8), ink=True,
                ), tooltip="Select Character 1"
            )
            self.name2_button = ft.PopupMenuButton(
                ft.Container(
                    ft.Text(
                        self.data.get('char1_name', "Select Character 2"), width=150, 
                        overflow=ft.TextOverflow.ELLIPSIS, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER
                    ),
                    padding=ft.padding.all(6), border_radius=ft.border_radius.all(8), ink=True
                ), tooltip="Select Character 2"
            )

            self.tags_textfield= ft.TextField(      # Textfield to enter connection tags
                hint_text="Connection Type (Friend, Father, Classmate, etc.)", on_blur=self._update_tags, dense=True,
                autofill_hints=[ft.AutofillHint.NICKNAME, ft.AutofillHint.GIVEN_NAME], expand=True, value=self.data.get('tags', ''),
            )

            self.icon_button = ft.PopupMenuButton(      # Button to change the connection icon 
                icon=ft.Icons.CONNECT_WITHOUT_CONTACT,
                tooltip="Change Connection's Icon",
                padding=ft.Padding(0,0,0,0),
                #items=self._get_icon_options()
            )

            # Change color
            self.color_button = ft.PopupMenuButton(     # Button to change the connection color
                icon=ft.Icons.COLOR_LENS_OUTLINED,
                tooltip="Change Connection's Color",
                padding=ft.Padding(0,0,0,0),
                #items=self._get_color_options()
            )

            # Add our controls to the row
            self.controls.extend([
                self.name1_button,   
                self.icon_button,  
                self.name2_button,        
                self.tags_textfield,        
                self.color_button, 
                ft.IconButton(ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, tooltip="Delete Connection", on_click=self._delete_connection),     # Delete button
            ])

        # Set name and key
        def _set_name_and_key(self, e):
            name = e.control.content.text   
            key = e.control.data

            # Update the data
            if e.control == self.name1_button: 
                self.data['char1_name'] = name
                self.data['char1_key'] = key
            else:
                self.data['char2_name'] = name
                self.data['char2_key'] = key

            # Update the existing connections dict we are working with
            update_connection(self)

            # Update the controls
            self.name1_button.content.text = self.data.get('char1_name', "Select Character 1")
            self.name2_button.content.text = self.data.get('char2_name', "Select Character 2")
            #TODO Change color as well

            
        # Updates our tags when tf changes
        def _update_tags(self, e):
            self.data['tags'] = e.control.value
            update_connection(self)

        # Deletes this connection control and updates our existing connections
        def _delete_connection(self, e):
            nonlocal content

            # Remove from existing connections
            existing_connections.pop(self.idx)
                    
            # Remove ourselves from the content controls and apply update
            content.controls.remove(self)   
            story.p.update()

        # Grabs all our character options for the dropdown. Exclude already existing connections with those characters
        def _get_char_options(self) -> list[ft.PopupMenuButton]:
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
                        data=character.data.get('key')          # Set key for easy retrievel
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
        
    def update_connection(ctrl: ConnectionCtrl):
        ''' Updates our existing connections data with the data from the passed in control '''
        nonlocal existing_connections

        # Update our existing connections data at the control's index with the new data
        existing_connections[ctrl.idx] = ctrl.data.copy()    
        

    #TODO: Somewhere - When one character is selected, remove that option for a connection from the matching dropdown

    # Closes our dialog and saves our character data
    async def _save_and_close(e):
        nonlocal dlg, existing_connections

        story.data['connections'] = existing_connections.copy()   # Save our updated connections back to the story data
        story.save_dict()

        # Reload all our character widgets to update their connections
        for char in story.characters.values():
            if char.visible:
                char.reload_widget()    

        # Reload all our character connection maps to update their connections
        for ccm in story.character_connection_maps:
            if ccm.visible:
                #TODO: Update any connection mini widgets as well
                ccm.reload_widget()     

        story.p.close(dlg)

   
    # Button clicked to add a new connection. Adds a dropdown + textfield row
    def _add_new_connection(e):
        nonlocal content, existing_connections

        new_connection_dict = ConnectionDataClass().__dict__


        existing_connections.append(new_connection_dict)   # Add empty connection to our existing connections to be filled out
        new_conn_ctrl = ConnectionCtrl(new_connection_dict, len(existing_connections)-1)   # Create new connection control
        content.controls.insert(-1, new_conn_ctrl)
        content.update()

    # Sets our content to add too
    content = ft.Column(
        [
            ft.Row([
                ft.Container(width=40),  # Spacer for the Drop down buttons
                ft.Text("Character 1", expand=True, theme_style=ft.TextThemeStyle.LABEL_LARGE), 
                ft.Text("Character 2", expand=True, theme_style=ft.TextThemeStyle.LABEL_LARGE), 
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
        title=ft.Text(f"Connections Editor"),
        content=ft.AutofillGroup(content),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: story.p.close(dlg), style=ft.ButtonStyle(color=ft.Colors.ERROR)),
            ft.TextButton("Save", on_click=_save_and_close),   # Start enabled to just save existing connections
        ],
    )
    

    story.p.open(dlg)