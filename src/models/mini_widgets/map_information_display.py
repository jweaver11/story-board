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


class MapInformationDisplay(MiniWidget):

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

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   # Pass in our object so we can access its data and change it
            {   
                'title': self.title,          # Title of the mini widget, should match the object title
                'tag': "map_information_display",         

                # Plotline data
                'Description': str,
                
            },
        )

        self.border = ft.border.only(
            left=ft.BorderSide(2, ft.Colors.SECONDARY_CONTAINER),
            right=ft.BorderSide(2, ft.Colors.SECONDARY_CONTAINER),
            bottom=ft.BorderSide(2, ft.Colors.SECONDARY_CONTAINER),
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

        #TODO: Show preview of the map here in info display so when other maps open this info display, they get a small preview

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

        description_tf = ft.TextField(
            expand=True, label="Description", value=self.data.get('Description', ""), dense=True, multiline=True,
            capitalization=ft.TextCapitalization.SENTENCES,
            on_blur=lambda e: self.change_data(**{'Description': e.control.value}),   # When we click out of the text field, we save our changes
            focus_color=self.owner.data.get('color', None),
            cursor_color=self.owner.data.get('color', None),
            focused_border_color=self.owner.data.get('color', None),
            label_style=ft.TextStyle(color=self.owner.data.get('color', None)),
        )
        
        content = ft.Column([
            title_control,
            ft.Divider(height=2, thickness=2),
            ft.Container(height=10),  # Spacing 
            description_tf
        ], expand=True, tight=True, spacing=0)

        
        self.content = content

        if no_update:
            return
        else:
            self.p.update()



        