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
from styles.text_fields import TextField

class MapInformationDisplay(MiniWidget):

    # Constructor.
    def __init__(
        self, 
        title: str, 
        widget: Widget,                  # The widget is always our map widget
        key: str,                       # Not used, but its required so just whatever works
        data: dict = {}               # No data is used here, so NEVER reference it. Use self.widget.data instead
    ):
        
        # Parent constructor
        super().__init__(
            title=title,           
            widget=widget, 
            data=data,              
            key=key     
        ) 


    

    
    def _map_info_view(self) -> ft.Column:

        # TODO: Add export button functionality?, show locations type / description

        async def _toggle_show_bg_map(e=None):
            self.update_data(**('show_bg_map', e.control.value))
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
                            on_click=lambda _, l=location: self.page.run_task(l.show_mini_widget), 
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
            on_blur=lambda e: self.update_data(**{'Description': e.control.value}),   # When we click out of the text field, we save our changes
        )
        lore_tf = TextField(
            expand=True, label="Lore", value=self.data.get('Lore', ""), dense=True, multiline=True,
            capitalization=ft.TextCapitalization.SENTENCES,
            on_blur=lambda e: self.update_data(**{'Lore': e.control.value}),   # When we click out of the text field, we save our changes
        )
        history_tf = TextField(
            expand=True, label="History", value=self.data.get('History', ""), dense=True, multiline=True,
            capitalization=ft.TextCapitalization.SENTENCES,
            on_blur=lambda e: self.update_data(**{'History': e.control.value}),   # When we click out of the text field, we save our changes
        )

        

        export_button = ft.TextButton(
            "Export", ft.Icons.FILE_DOWNLOAD_OUTLINED, tooltip="Export canvas as image",
            #on_click=self.widget.export_canvas_clicked, 
            style=ft.ButtonStyle(mouse_cursor="click")
        )


    


        


        


       


        