'''
Connection mini widget to show information about a characters connections
'''

# BLANK NO TEMPLATE MAPS EXIST AS WELL
# ADD DUPLICATE OPTION AS WELL
# Users can choose to create their image or use some default ones, or upload their own
# When hovering over a map, display it on the rail as well so we can see where new sub maps would


import flet as ft
from models.widget import Widget
from models.mini_widget import MiniWidget
from utils.verify_data import verify_data
from models.app import app
from models.dataclasses.connection import ConnectionDataClass




class Connection(MiniWidget):

    # Constructor.
    def __init__(
        self, 
        title: str, 
        owner: Widget,                  # The owner is the Character Connection Map widget that loads this mini widget FROM a characters data
        page: ft.Page, 
        key: str,                       # Not used, but its required so just whatever works
        primary_character_key: str = None,   # Key of the primary character this connection belongs to
        secondary_character_key: str = None, # Key of the secondary character this connection belongs to
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

        verify_data(
            self,
            ConnectionDataClass().__dict__ | {'tag': "connection"}
        )

        
        # Set our visibility based on our owners data
        self.visible = self.data.get('visible', True)

        # Reloads the information display of the map
        self.reload_mini_widget()

    # Called when saving changes to our timeline object
    def save_dict(self):
        ''' Overwrites standard mini widget save and save our timelines data instead '''
        try:
            self.owner.data.get('character_data', {}).get('Connections', {})[self.key] = self.data
            self.owner.save_dict()
        except Exception as e:
            print(f"Error saving map information display data to {self.owner.title}: {e}")

    def show_mini_widget(self, e=None):
        ''' Shows our mini widget '''

        if self.visible:
            return

        self.data['visible'] = True
        self.visible = True
        self.save_dict()

        for mw in self.owner.mini_widgets:
            if mw != self and mw.data.get('is_pinned', False) == False:
                mw.hide_mini_widget()   

        self.reload_mini_widget(no_update=True)
        #self.owner.reload_widget()

    def hide_mini_widget(self, e=None, update: bool=False):
        ''' Hides our mini widget '''
        
        if not self.visible:
            return
        
        self.data['visible'] = False
        self.visible = False

        if self.data.get('is_pinned', False):
            self.data['is_pinned'] = False

        self.save_dict()

        if update:
            self.reload_mini_widget()
            #self.owner.reload_widget()

    # Called to toggle pin
    async def _toggle_pin(self, e):
        ''' Pins or unpins our information display '''
            
        self.data['is_pinned'] = not self.data.get('is_pinned', False)
        self.save_dict()
        self.reload_mini_widget()
        self.owner.reload_widget()
    
    # Called when reloading our mini widget UI
    def reload_mini_widget(self, no_update: bool=False):
            
        title_control = ft.Row([
            ft.Icon(self.data.get('icon'), self.owner.data.get('color', None)),
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



        