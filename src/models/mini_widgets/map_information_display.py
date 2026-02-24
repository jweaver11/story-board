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

        self.show_info_button = ft.GestureDetector(
            ft.IconButton(
                ft.Icons.MENU_ROUNDED, scale=1.5,
                on_click=self.toggle_visibility, 
                tooltip="Show Map Info. Drag to move",
            ),
            drag_interval=20, 
            on_pan_start=self._drag_start, 
            on_pan_update=self.move_show_info_button, on_pan_end=self._drag_end,
            mouse_cursor=ft.MouseCursor.CLICK,
            left=self.data.get('left', 0), top=self.data.get('top', 0),
        )

        # Reloads the information display of the map
        self.reload_mini_widget()

    # Called when saving changes to our timeline object
    def save_dict(self):
        ''' Overwrites standard mini widget save and save our timelines data instead '''
        try:
            self.owner.save_dict()
        except Exception as e:
            print(f"Error saving map information display data to {self.owner.title}: {e}")

    async def toggle_visibility(self, e=None):
        if self.visible:
            self.hide_mini_widget()
            self.show_info_button.content.icon = ft.Icons.MENU_ROUNDED
        else:
            self.show_mini_widget()
            self.show_info_button.content.icon = ft.Icons.REMOVE
        self.show_info_button.page = self.p
        self.show_info_button.update()
        self.p.update()

    # Called to toggle our drawing mode on/off
    def _toggle_drawing_mode(self, e=None):
        ''' Toggles our drawing mode on/off '''

        # Change our data value for drawing mode and save it
        self.data['drawing_mode'] = not self.data.get('drawing_mode', False)
        self.save_dict()

        e.control.icon = ft.Icons.DRAW_OUTLINED if not self.data['drawing_mode'] else ft.Icons.DONE

        # If we entered drawing mode, show our drawing canvas rail. Otherwise, go back to the previous rail
        if self.data.get('drawing_mode', False):
            self.owner.story.workspaces_rail.change_workspace(None, self.owner.story, force_rail="canvas")
            self.owner.canvas.content.mouse_cursor = ft.MouseCursor.PRECISE
        else:
            
            self.owner.canvas.content.mouse_cursor = ft.MouseCursor.CLICK

        self.owner.canvas.content.page = self.p
        self.owner.canvas.content.update()


    # Called when we start dragging
    async def _drag_start(self, e=None):
        ''' Called when we start dragging our plot point. Sets our state to dragging and changes our mouse cursor '''

        self.show_info_button.mouse_cursor = ft.MouseCursor.CLICK
        #self.show_info_button.page = self.p
        self.show_info_button.update()

        # Hide all other info displays while dragging
        for mw in self.owner.mini_widgets:
            mw.visible = False

        self.p.update()

    async def move_show_info_button(self, e: ft.DragUpdateEvent):
        ''' Changes our x position on the slider, and saves it to our data dictionary, but not to our file yet '''

        
        # Calculate our new absolute positioning based on our delta x from dragging
        new_left = self.show_info_button.left + e.delta_x
        new_top = self.show_info_button.top + e.delta_y

        # Clamp our position to the bounds of our map
        if new_left < 20:        
            new_left = 20
        elif new_left > self.owner.map_width - 40:  
            new_left = self.owner.map_width - 40
        if new_top < 20:
            new_top = 20
        elif new_top > self.owner.map_height - 40:
            new_top = self.owner.map_height - 40
        
        # Apply to data
        self.data['left'] = new_left
        self.data['top'] = self.show_info_button.top


        # Set our new position and animate it there
        self.show_info_button.left = new_left
        self.show_info_button.top = new_top

        self.show_info_button.page = self.p
        self.show_info_button.update()

    # Called when we finish dragging our map_marker to save our position
    async def _drag_end(self, e=None):
        ''' Updates our alignment and side location, and applies the updadte to the canvas for our label '''

        self.show_info_button.mouse_cursor = ft.MouseCursor.GRAB
        
        x_alignment = (self.data.get('left', 0) / (self.owner.map_width - 10)) * 2.0 - 1.0
        y_alignment = (self.data.get('top', 0) / (self.owner.map_height - 10)) * 2.0 - 1.0  

        self.data['alignment'] = (x_alignment, y_alignment)

        if self.data.get('alignment', 0)[0] <= 0:
            self.data['side_location'] = "right"
        else:
            self.data['side_location'] = "left"

        print("Side Location:", self.data['side_location'])

        self.save_dict()

        # Re-show all the info displays we hid while dragging
        for mw in self.owner.mini_widgets:
            if mw.data.get('visible', True):
                mw.visible = True

        self.show_info_button.page = self.p
        self.show_info_button.update()
        self.owner._render_widget()
    
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

        # Create our header
        header = ft.Row([
            ft.IconButton(
                ft.Icons.DRAW_OUTLINED if not self.data.get('drawing_mode') else ft.Icons.DONE,
                tooltip="Enter Drawing Mode" if not self.data.get('drawing_mode') else "Exit Drawing Mode",
                on_click=self._toggle_drawing_mode,
            ),
            # Undo and redo buttons
            ft.PopupMenuButton(
                icon=ft.Icons.IMAGE_ASPECT_RATIO_OUTLINED, tooltip="Set the background of your canvas. If one is set, it will be exported with the canvas",
                menu_padding=ft.padding.all(0), 
                #on_cancel=self._set_color,
                items=[
                    #ft.PopupMenuItem("None", on_click=self._set_canvas_background, tooltip="No background"),
                    #ft.PopupMenuItem("Color", on_click=self._set_canvas_background, tooltip="Set a solid color background"),
                    #ft.PopupMenuItem("Image", on_click=self._set_canvas_background, tooltip="Set an image as the background"),
                ]
            ),
           
            # Button to hide markers
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
            ft.Container(height=1),  # Spacing 
            header,
            description_tf
        ], expand=True, tight=True, scroll="auto", alignment=ft.MainAxisAlignment.START)

        
        column = ft.Column([
            title_control,
            ft.Divider(height=2, thickness=2),
            content
        ], expand=True, scroll="none", tight=True, alignment=ft.MainAxisAlignment.START)
        
        self.content = column

        if no_update:
            return
        else:
            self.p.update()



        