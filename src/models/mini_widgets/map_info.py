'''
The map class for all maps inside of the world_building widget
Maps are extended mini widgets, with their 'display' being the view of the map, and their mini widget being the maps info display
Maps don't save like mini widgets. They save their data inside one file, and their drawing data in another file.
Since maps could have hundreds of sub-maps, we give them each their own file to avoid corruption
'''

# BLANK NO TEMPLATE MAPS EXIST AS WELL
# ADD DUPLICATE OPTION AS WELL
# Users can choose to create their image or use some default ones, or upload their own
# When hovering over a map, display it on the rail as well so we can see where new sub maps would


import flet as ft
from models.widget import Widget
from models.mini_widget import MiniWidget
from utils.verify_data import verify_data
from styles.text_fields import TextField

class MapInformationDisplay(MiniWidget):

    # Constructor.
    def __init__(
        self, 
        title: str, 
        widget: Widget,                  # The widget is always our map widget
        page: ft.Page, 
        key: str,                       # Not used, but its required so just whatever works
        data: dict = None               # No data is used here, so NEVER reference it. Use self.widget.data instead
    ):
        
        # Check if we're new and need to create file
        is_new = False
        if data is None:
            is_new = True
        

        # Parent constructor
        super().__init__(
            title=title,           
            widget=widget, 
            page=page,              
            data=data,              
            key=key     
        ) 

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   # Pass in our object so we can access its data and change it
            {   
                'title': self.title,          # Title of the mini widget, should match the object title
                'tag': "map_information_display",        
                'left': 40,
                'top': 40,
                'alignment': None,
                'show_bg_map': True,                   # Whether to show the background map image or not

                # Map info
                'Description': str,
                'Lore': str,
                'History': str,
            },
        )

        if is_new:
            self.p.run_task(self.save_dict)

        # Reloads the information display of the map
        self.reload_mini_widget()

    # Called when saving changes in our mini widgets data to the widgetS json file
    async def save_dict(self):
        ''' Saves our current data to the widgetS json file using this objects dictionary path '''

        try:
            # Our data is correct, so we update our immidiate parents data to match
            self.widget.data[self.key] = self.data

            # Recursively updates the parents data until widget=widget (widget), which saves to file
            await self.widget.save_dict()

        except Exception as e:
            print(f"Error saving mini widget data to {self.title}: {e}")

    
    def _map_info_view(self) -> ft.Column:

        # TODO: Add export button functionality?, show locations type / description

        async def _toggle_show_bg_map(e=None):
            self.data['show_bg_map'] = e.control.value
            await self.save_dict()
            self.widget.reload_widget()  # Reload our widget to update the background image visibility
        
        
        
        show_map_bg_switch = ft.Switch(
            True, "Show Map Background",
            label_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=12),
            value=self.data.get('show_bg_map', True), on_change=_toggle_show_bg_map,
            tooltip="Whether to use the background image for the map or not",
        )

        def _get_locations() -> list[ft.Control]:
            controls = []
            for location in self.widget.locations.values():
                title = location.data.get('title', 'Unknown Location')
                color = location.data.get('color', None)
                controls.append(
                    ft.Row([
                        ft.Container(
                            ft.Text(title, color=color, expand=True, overflow=ft.TextOverflow.ELLIPSIS, weight=ft.FontWeight.BOLD), 
                            on_click=lambda _, l=location: self.p.run_task(l.show_mini_widget), 
                            expand=True, padding=ft.Padding.only(left=10)
                        ),
                        ft.Container(
                            ft.IconButton(
                                ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, on_click=lambda _, l=location: l._delete_clicked(),
                                tooltip="Delete Location", style=ft.ButtonStyle(padding=ft.Padding.all(0), mouse_cursor="click")
                            ), margin=ft.Margin.only(right=10)
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                )
            if not controls:
                controls.append(ft.Text("No Locations added yet.", color=ft.Colors.OUTLINE))
                
            return controls

        description_tf = TextField(
            expand=True, label="Description", value=self.data.get('Description', ""), dense=True, multiline=True,
            capitalization=ft.TextCapitalization.SENTENCES,
            on_blur=lambda e: self.change_data(**{'Description': e.control.value}),   # When we click out of the text field, we save our changes
        )
        lore_tf = TextField(
            expand=True, label="Lore", value=self.data.get('Lore', ""), dense=True, multiline=True,
            capitalization=ft.TextCapitalization.SENTENCES,
            on_blur=lambda e: self.change_data(**{'Lore': e.control.value}),   # When we click out of the text field, we save our changes
        )
        history_tf = TextField(
            expand=True, label="History", value=self.data.get('History', ""), dense=True, multiline=True,
            capitalization=ft.TextCapitalization.SENTENCES,
            on_blur=lambda e: self.change_data(**{'History': e.control.value}),   # When we click out of the text field, we save our changes
        )

        notes_label = ft.Row([
            ft.Container(width=6),
            ft.Text("Notes", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.widget.data.get('color', None), selectable=True),
            ft.IconButton(
                ft.Icons.NEW_LABEL_OUTLINED, self.widget.data.get('color', "primary"), tooltip="Add Note",
                on_click=self._new_note_clicked,
                mouse_cursor="click"
            )
        ], spacing=0)

        export_button = ft.TextButton(
            "Export", ft.Icons.FILE_DOWNLOAD_OUTLINED, tooltip="Export canvas as image",
            #on_click=self.widget.export_canvas_clicked, 
            style=ft.ButtonStyle(mouse_cursor="click")
        )

        notes_column = self._build_notes_column()

        return ft.Column([
            #show_map_bg_switch,
            ft.Container(description_tf, margin=ft.Margin.only(right=10)),
            ft.Container(lore_tf, margin=ft.Margin.only(right=10)),
            ft.Container(history_tf, margin=ft.Margin.only(right=10)),
            #ft.Row([export_button, show_map_bg_switch]),
            show_map_bg_switch,
            
            ft.Divider(2, 2),
            
            ft.Text("Locations", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.widget.data.get('color', None),),
                    
            ] 
            + _get_locations() + [
                notes_label,
                ft.Container(notes_column, margin=ft.Margin.symmetric(horizontal=20)),
                # Notes
            ]
            
            
        , expand=True, scroll="auto", spacing=10)
    

    
    # Called when reloading our mini widget UI
    def reload_mini_widget(self):

        title_control = ft.Row([
           
     
            ft.Text(
                f"{self.widget.title}", theme_style=ft.TextThemeStyle.TITLE_LARGE, 
                color=self.widget.data.get('color', None), weight=ft.FontWeight.BOLD, 
            ),
                
            ft.IconButton(
                ft.Icons.UNDO, self.widget.data.get('color', None), tooltip="Undo", mouse_cursor=ft.MouseCursor.CLICK, 
                #on_click=self.undo, #disabled=True if len(self.widget.state.undo_list) == 0 else False
            ),
            ft.IconButton(
                ft.Icons.REDO_OUTLINED, self.widget.data.get('color', None), tooltip="Redo", mouse_cursor=ft.MouseCursor.CLICK, 
                #on_click=self.redo, #disabled=True if len(self.widget.state.redo_list) == 0 else False
            ),
            ft.Container(expand=True),
            ft.IconButton(
                ft.Icons.CLOSE, ft.Colors.ON_SURFACE_VARIANT,
                tooltip=f"Close {self.title}",
                mouse_cursor=ft.MouseCursor.CLICK,
                on_click=self.hide_mini_widget,
            ),
        ], spacing=0)


        content = ft.Column(
            expand=True, tight=True, scroll="auto", alignment=ft.MainAxisAlignment.START, spacing=0,
            controls=[
                ft.Container(height=10), # Spacer
            ]
        )


       
        content.controls.append(self._map_info_view())

        
        
        
        
        self.content = ft.Column([
            title_control,
            ft.Divider(),
            content,
                        
        ], expand=True, scroll="none", alignment=ft.MainAxisAlignment.START, spacing=0)

        try:
            self.update()
        except Exception as _:
            pass



        