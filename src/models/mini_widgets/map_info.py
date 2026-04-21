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
from styles.text_field import TextField

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
                'drawing_mode': bool,            # Whether we are in drawing mode or not

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


    # Called to toggle our drawing mode on/off
    async def _toggle_drawing_mode(self, e=None):
        ''' Toggles our drawing mode on/off '''

        # Change our data value for drawing mode and save it
        self.data['drawing_mode'] = not self.data.get('drawing_mode', False)
        await self.save_dict()

        e.control.icon = ft.Icons.DRAW_OUTLINED if self.data['drawing_mode'] else ft.Icons.LOCATION_SEARCHING_OUTLINED

        # If we entered drawing mode, show our drawing canvas rail. Otherwise, go back to the previous rail
        if self.data.get('drawing_mode', False):
            #self.widget.story.workspaces_rail.change_workspace(None, self.widget.story, force_rail="canvas")
            self.widget.canvas.content.mouse_cursor = ft.MouseCursor.PRECISE
        else:
            self.widget.canvas.content.mouse_cursor = None
        self.widget.canvas.content.update()

        self.reload_mini_widget()


    def _drawing_mode_view(self) -> ft.Column:
        # TODO: 
        # Match canvas info mini widget
        
        # Create our header
        drawing_buttons = ft.Row([
            
            # Undo and redo buttons
            ft.PopupMenuButton(
                icon=ft.Icons.IMAGE_ASPECT_RATIO_OUTLINED, tooltip="Set the background of your canvas. If one is set, it will be exported with the canvas",
                menu_padding=ft.Padding.all(0), 
                #on_cancel=self._set_color,
                items=[
                    #ft.PopupMenuItem("None", on_click=self._set_canvas_background, tooltip="No background"),
                    #ft.PopupMenuItem("Color", on_click=self._set_canvas_background, tooltip="Set a solid color background"),
                    #ft.PopupMenuItem("Image", on_click=self._set_canvas_background, tooltip="Set an image as the background"),
                ]
            ),
           
            # Button to hide markers
        ])
        return ft.Column([
            drawing_buttons
        ], expand=True, scroll="auto", spacing=0)
    
    def _map_info_view(self) -> ft.Column:

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
                            expand=True, padding=ft.Padding.only(left=20)
                        ),
                        ft.Container(
                            ft.IconButton(
                                ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, on_click=lambda _, l=location: l._delete_clicked(),
                                tooltip="Delete Location", style=ft.ButtonStyle(padding=ft.Padding.all(0), mouse_cursor="click")
                            ), margin=ft.Margin.only(right=20)
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
        return ft.Column([
                description_tf,
                lore_tf,
                history_tf,
                ft.Divider(2, 2),
                
                ft.Text("Locations", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.widget.data.get('color', None),),
                    
            ] 
            + _get_locations()
            
            
        , expand=True, scroll="auto", spacing=10)
    

    
    # Called when reloading our mini widget UI
    def reload_mini_widget(self):

        title_control = ft.Row([
            #ft.Icon(ft.Icons.BRUSH, self.widget.data.get('color', None)),
            ft.IconButton(
                ft.Icons.DRAW_OUTLINED if self.data.get('drawing_mode') else ft.Icons.LOCATION_SEARCHING_OUTLINED,
                self.widget.data.get('color', None), mouse_cursor=ft.MouseCursor.CLICK,
                tooltip="Enter Drawing Mode" if not self.data.get('drawing_mode') else "Exit Drawing Mode",
                on_click=self._toggle_drawing_mode,
            ),
     
            ft.GestureDetector(
                ft.Text(f"{self.widget.title}", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, 
                color=self.data.get('color', None)),
                on_double_tap=self.widget.rename_clicked,
                on_secondary_tap=lambda _: self.widget.story.open_menu(self._get_menu_options()),
                mouse_cursor="click", hover_interval=500, 
            ),
                
            ft.IconButton(
                ft.Icons.UNDO, self.widget.data.get('color', None), tooltip="Undo", mouse_cursor=ft.MouseCursor.CLICK, 
                visible=self.data.get('drawing_mode', False) # Only show in drawing mode
                #on_click=self.undo, #disabled=True if len(self.widget.state.undo_list) == 0 else False
            ),
            ft.IconButton(
                ft.Icons.REDO_OUTLINED, self.widget.data.get('color', None), tooltip="Redo", mouse_cursor=ft.MouseCursor.CLICK, 
                visible=self.data.get('drawing_mode', False) # Only show in drawing mode
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


        if self.data.get('drawing_mode', False):
            content.controls.append(self._drawing_mode_view())
        else:
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



        