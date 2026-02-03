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



class CCMInformationDisplay(MiniWidget):

    # Constructor.
    def __init__(
        self, 
        title: str, 
        owner: Widget,                  # The owner is always our map owner
        page: ft.Page, 
        key: str,                       # Not used, but its required so just whatever works
        data: dict = None               # No data is used here, so NEVER reference it. Use self.owner.data instead
    ):
        

        # Parent constructor
        super().__init__(
            title=title,           
            owner=owner, 
            page=page,              
            data=data,              
            key=key     
        ) 

        # NOT USED
        self.data['visible'] = self.owner.data.get('information_display_visibility', True)

        # Set our visibility based on our owners data
        self.visible = self.owner.data.get('information_display_visibility', True)
        self.data['is_pinned'] = self.owner.data.get('information_display_is_pinned', False)

        # Reloads the information display of the map
        self.reload_mini_widget()

    # Called when saving changes to our timeline object
    def save_dict(self):
        ''' Overwrites standard mini widget save and save our timelines data instead '''
        try:
            self.owner.save_dict()
        except Exception as e:
            print(f"Error saving map information display data to {self.owner.title}: {e}")

    # Called to toggle our visibility
    def show_mini_widget(self, e=None):
        ''' Toggles our visibility and updates our owners data accordingly '''

        if self.visible:
            return
        
        
        # Update our visibility
        self.owner.data['information_display_visibility'] = True
        super().show_mini_widget(e)

    def hide_mini_widget(self, e=None, update: bool=False):
        ''' Hides our mini widget '''

        self.owner.data['information_display_visibility'] = False
        self.owner.data['information_display_is_pinned'] = False
        super().hide_mini_widget(e, update)

    async def _toggle_pin(self, e):
        ''' Pins or unpins our information display '''
            
        self.owner.data['information_display_is_pinned'] = not self.owner.data['information_display_is_pinned']
        self.data['is_pinned'] = self.owner.data['information_display_is_pinned']
        self.save_dict()
        self.reload_mini_widget()
        self.owner.reload_widget()
    
    # Called when reloading our mini widget UI
    def reload_mini_widget(self, no_update: bool=False):

            
        title_control = ft.Row([
            ft.Icon(ft.Icons.MAP, self.owner.data.get('color', None)),
            ft.Text(self.data['title'], weight=ft.FontWeight.BOLD, selectable=True, overflow=ft.TextOverflow.FADE),
            ft.IconButton(
                ft.Icons.PUSH_PIN_OUTLINED if not self.owner.data.get('information_display_is_pinned', False) else ft.Icons.PUSH_PIN_ROUNDED,
                self.owner.data.get('color', None),
                tooltip="Pin Information Display" if not self.owner.data.get('information_display_is_pinned', False) else "Unpin Information Display",
                on_click=self._toggle_pin
            ),
            ft.Container(expand=True),
            ft.IconButton(
                ft.Icons.CLOSE, ft.Colors.ON_SURFACE_VARIANT,
                tooltip=f"Close {self.title}",
                on_click=lambda e: self.hide_mini_widget(update=True),
            ),
        ])
        
        content = ft.Column([
            title_control,
            ft.Divider(height=2, thickness=2),
            ft.Container(height=10),  # Spacing 
            ft.Text("Content"),
        ], expand=True, tight=True, spacing=0)


        


        # Format our final layout so the scrollbar doesn't sit overtop the content
        row = ft.Row(expand=True, controls=[content, ft.Container(width=8)], spacing=0)
    
        column = ft.Column([
            row
        ], expand=True, scroll="auto", tight=True)
        
        self.content = column

        if no_update:
            return
        else:
            self.p.update()



        