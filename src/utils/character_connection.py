import flet as ft

def new_character_connection_clicked(character):

    # Closes our dialog and saves our character data
    async def _close_dialog(e):
        nonlocal dlg, existing_connections
        character.data['character_data']['Connections'] = existing_connections
        character.save_dict()
        character.p.close(dlg)

    # Grabs all our characters except ourselves
    def _get_char_list() -> list[ft.DropdownOption]:
        options = []
        for char in character.story.characters.values():
            if char != character:
                options.append(
                    ft.DropdownOption(
                        char.data.get('title'),   
                        content=ft.Text(char.data.get('title'), color=char.data.get('color', "primary")),
                        data=lambda e, c=char: c.key        # Save their key
                    )
                )

        return options
    

    
    # When we click to add a new connection
    def _add_new_connection(e):
        nonlocal content

        idx = len(character.data.get('character_data', {}).get('Connections', []))

        # Give us a temporary key for the new connection
        existing_connections.append({'title', 'key', 'type'})

        new_conn_ctrl = ft.Row([
            ft.Dropdown(options=_get_char_list(), label="Select Character", expand=True, dense=True, data={'idx': idx, 'key': ""}),
            ft.TextField(label="Connection Type", expand=True, data={'idx': idx, 'key': ""})
        ])


        content.controls.insert(-1, new_conn_ctrl)
        content.update()


    def _update_connection(e):
        nonlocal existing_connections

        idx = e.control.data
        if isinstance(e.control, ft.Dropdown):
            selected_char_key = e.control.value
            # Find the character by title to get their key
            for char in character.story.characters.values():
                if char.data.get('title') == selected_char_key:
                    existing_connections[idx]['Title'] = char.data.get('title')
                    existing_connections[idx]['Key'] = char.key
                    break
        elif isinstance(e.control, ft.TextField):
            existing_connections[idx]['Type'] = e.control.value

        print("Updated Connections:", existing_connections)

    # Sets our content to add too
    content = ft.Column(
        [
            ft.Row([
                ft.Text("Name", expand=True, theme_style=ft.TextThemeStyle.LABEL_LARGE), 
                ft.Text("Type", expand=True, theme_style=ft.TextThemeStyle.LABEL_LARGE),
                ft.Container(width=25)  # Spacer for the remove buttons
            ]),
            ft.Divider()
        ], 
        scroll="auto",
        width=character.p.width * .5,
    )
        
    
    # Grab our existing connections
    existing_connections = character.data.get('character_data', {}).get('Connections', [])
    print("Existing Connections:", existing_connections)

    for idx, conn in enumerate(existing_connections):
        content.controls.append(
            ft.Row([
                ft.Dropdown(
                    options=_get_char_list(), value=conn.get('Title'), expand=True, dense=True, data={'idx': idx, 'key': conn.get('key')},
                    on_change=_update_connection,
                ),
                ft.TextField(label="Connection Type", expand=True, value=conn.get('Type'), data={'idx': idx, 'key': conn.get('key')})
            ])
        )




    # Add button to add new connections
    content.controls.append(
        ft.IconButton(
            ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, tooltip="Add New Connection",
            on_click=_add_new_connection
        )
    )


    dlg = ft.AlertDialog(
        title=ft.Text(f"{character.title}'s Connections:"),
        content=content,
        actions=[
            ft.TextButton("Cancel", on_click=_close_dialog, style=ft.ButtonStyle(color=ft.Colors.ERROR)),
            ft.TextButton("Done", on_click=_close_dialog),
        ],
    )
    
    
    dlg.open = True
    character.p.open(dlg)