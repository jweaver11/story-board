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
from styles.icons import connection_icons




class CharacterConnection(MiniWidget):

    # Constructor.
    def __init__(
        self, 
        title: str, 
        owner: Widget,                  # The owner is the Character Connection Map widget that loads this mini widget FROM a characters data
        page: ft.Page, 
        index: int,
        data: dict = None               # No data is used here, so NEVER reference it. Use self.owner.data instead
    ):
        self.idx = index    # The index of this connection in the story connections data list, so we can save back to it

        # Parent constructor
        super().__init__(
            title=title,           
            owner=owner, 
            page=page,              
            data=data,              
            key="",                # Stored as a list in story data, so don't use key
        ) 

        verify_data(
            self,
            ConnectionDataClass().__dict__ | {'tag': "connection"}
        )

        
        # Set our visibility based on our owners data
        self.visible = self.data.get('visible', True)

        self.icon_button = ft.PopupMenuButton(      # Button to change the connection icon 
            icon=self.data.get('icon', ft.Icons.CONNECT_WITHOUT_CONTACT),
            tooltip="Change Connection's Icon",
            menu_padding=ft.Padding(0,0,0,0), icon_color=self.data.get('color', ft.Colors.PRIMARY),
            items=self._get_icon_options()
        )

        # Reloads the information display of the map
        self.reload_mini_widget()

    # Called when saving changes to our timeline object
    def save_dict(self):
        ''' Overwrites standard mini widget save and save our timelines data instead '''
        try:
            self.owner.story.data.get('connections', [])[self.idx] = self.data
            self.owner.story.save_dict()
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
        e.control.icon = ft.Icons.PUSH_PIN_OUTLINED if not self.data.get('is_pinned', False) else ft.Icons.PUSH_PIN_ROUNDED
        e.control.tooltip = "Pin Connection" if not self.data.get('is_pinned', False) else "Unpin Connection"
        self.p.update()

    def _get_icon_options(self) -> list[ft.Control]:
            ''' Returns a list of all available icons for icon changing '''

            # Called when an icon option is clicked on popup menu to change icon
            def _change_icon(icon: str, e):
                ''' Passes in our kwargs to the widget, and applies the updates '''

                # Set our data and update our button icon
                self.data['icon'] = icon
                self.icon_button.icon = icon

                # Update our existing connections data to match our new data
                self.save_dict()
                self.p.update()

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

            return icon_controls
    
    # Called when reloading our mini widget UI
    def reload_mini_widget(self, no_update: bool=False):
            
        title_control = ft.Row([
            ft.Text(self.data.get('char1_name', 'Character 1'), weight=ft.FontWeight.BOLD, selectable=True, overflow=ft.TextOverflow.FADE, text_align=ft.TextAlign.CENTER),
            ft.Icon(self.data.get('icon'), self.owner.data.get('color', None)),
            ft.Text(self.data.get('char2_name', 'Character 2'), weight=ft.FontWeight.BOLD, selectable=True, overflow=ft.TextOverflow.FADE, text_align=ft.TextAlign.CENTER),
            ft.Container(expand=True),
            ft.IconButton(
                ft.Icons.PUSH_PIN_OUTLINED if not self.data.get('is_pinned', False) else ft.Icons.PUSH_PIN_ROUNDED,
                self.owner.data.get('color', None),
                tooltip="Pin Connection" if not self.data.get('is_pinned', False) else "Unpin Connection",
                on_click=self._toggle_pin
            ),
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



        