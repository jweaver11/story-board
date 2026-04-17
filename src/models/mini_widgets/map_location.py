'''
Class for marking any point of interest (location) on a map
'''

import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
from utils.verify_data import verify_data
import math
from styles.text_styles import text_style
import flet.canvas as cv 
from styles.icons import icons
from styles.text_field import TextField

# Locations that appear on our map
class Location(MiniWidget):

    # Constructor. Requires title, widget widget, page reference, and optional data dictionary
    def __init__(
        self, 
        title: str, 
        widget: Widget, 
        page: ft.Page, 
        key: str,                          
        left: int = None,                   
        top: int = None,                   
        data: dict = None,
        icon: str = "label"       
    ):

        # Parent constructor
        super().__init__(
            title=title,        
            widget=widget,        
            page=page,          
            key=key,  
            data=data,    
        ) 

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {   
                'tag': "location",            # Tag to identify what type of object this is
                'icon': icon,
                'left': left, 
                'top': top,
                'color': "secondary",           # Color of the plot point on the map

                # Information for our information display
                'Type': str,   # Type of location (city, town, dungeon, mountain, etc)
                'Description': str, 
                'History': str,
                'image_base64': str,  
            },
        )

        # Set our x alignment to position on our map. -1 is left, 0 is center, 1 is right. Default 0
        self.alignment = ft.Alignment(self.data.get('alignment', 0), 0)

        # UI elements
        self.map_control: ft.Container    # Circle container to shows our location icon on the map
        self.map_label: ft.Text
        
        
                    

        # State variables
        self.is_dragging: bool = False              # If we are currently dragging our plot point

        # Build our slider for moving our plot point
        self.reload_map_control()
        self.reload_mini_widget()

    
    async def move_location(self, e: ft.DragUpdateEvent):
        ''' Changes our x position on the slider, and saves it to our data dictionary, but not to our file yet '''

        if e is None:
            delta_x = 0
            delta_y = 0
        else:
            delta_x = e.local_delta.x
            delta_y = e.local_delta.y

        if not isinstance(delta_x, (int, float)):
            delta_x = 0
        if not isinstance(delta_y, (int, float)):
            delta_y = 0

        # Calculate our new absolute positioning based on our delta x from dragging
        new_left = self.map_control.left + delta_x
        new_top = self.map_control.top + delta_y


        #self.map_label.offset = ft.Offset(-0.5, -1)

        # Clamp our position to the bounds of our map
        if new_left <= 20:        
            new_left = 20
        elif new_left > self.widget.map_width - 25:  
            new_left = self.widget.map_width - 25
        if new_top <= 45:
            new_top = 45
            
        if new_top > self.widget.map_height - 45:
            new_top = self.widget.map_height - 45
        
        
        
        # Set our new position and animate it there
        self.map_control.left = new_left
        self.map_control.top = new_top
        self.map_label.left = new_left + 12 # Offset half the width of the icon
        self.map_label.top = new_top

        
        
        self.data['left'] = self.map_control.left
        self.data['top'] = self.map_control.top

        if self.data.get('icon', "") != "label":
            self.map_control.update()
        self.map_label.update()
        
          
    # Called when we start dragging
    async def _drag_start(self, e=None):
        ''' Called when we start dragging our plot point. Sets our state to dragging and changes our mouse cursor '''

        if self.data.get('icon', "") != "label":
            self.map_control.content.mouse_cursor = ft.MouseCursor.MOVE
            self.is_dragging = True

            self.map_control.update()

    # Quick fixer for the mouse cursor and highlight is we just clicked the plotpoint without dragging
    async def _tap_up(self, e=None):
        self.map_control.content.mouse_cursor = ft.MouseCursor.CLICK
        await self._highlight()

    # Called when we finish dragging our map_marker to save our position
    async def _drag_end(self, e=None):
        ''' Updates our alignment and side location, and applies the updadte to the canvas for our label '''

        self.map_control.content.mouse_cursor = ft.MouseCursor.CLICK
        self.is_dragging = False
        if not self.visible:        # Turn of highlight if we're not visilbe
            self.map_control.shadow = None
        
        x_alignment = (self.data.get('left', 0) / (self.widget.map_width - 10)) * 2.0 - 1.0

        self.data['x_alignment'] = x_alignment

        await self.save_dict()

        if self.data.get('icon', "") != "label":
            self.map_control.update()

    # Called when hovering over our plot point to show the slider
    async def _highlight(self, e=None):
        ''' Shows our slider and hides our map_marker. Makes sure all other sliders are hidden '''

        # Gives us a focused shadow
        if self.data.get('icon', "") != "label":
            self.map_control.shadow = ft.BoxShadow(4, 4, ft.Colors.with_opacity(.6, self.data.get('color'))) #if self.map_control.shadow is None else None
            self.map_control.update()

    # Hides are shadow unless our info display is visible, then stay highlighted
    async def _stop_highlight(self, e=None):

        # If we're dragging, keep highlighted
        if self.is_dragging:
            return

        # If our info display is visible, keep highlighted
        if not self.visible and self.data.get('icon', "") != "label":
            self.map_control.shadow = None
            self.map_control.update()

    
    
    # Makes sure we stop highlighting
    async def hide_mini_widget(self, e=None, update: bool=True):
        if self.data.get('icon', "") != "label":
            self.map_control.shadow = None
            self.map_control.update()
        return await super().hide_mini_widget(e, update)
    
    # Called when clicking our upload image button
    async def _upload_location_image(self, e=None):

        files = await ft.FilePicker().pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "webp"])
        if files:

            file_path = files[0].path
            try:
                import base64

                with open(file_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    # Save to our data
                    self.data['image_base64'] = f"{encoded_string}"
                    await self.save_dict()
                    self.reload_mini_widget()

            except Exception as _:
                pass


    # Called from reload_mini_widget
    def reload_map_control(self, no_update: bool=False):
        """ Rebuilds our map control that holds our plot point and slider """

        
        icon = self._set_icon()

        # Our container that is our plot point on the map, and contains our gesture detector for hovering and right clicking
        self.map_control = ft.Container(
            #border=ft.Border.all(1, "blue"),
            expand=True,
            width=25,
            height=25,
            shape=ft.BoxShape.CIRCLE,
            alignment=ft.Alignment.CENTER, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            left=self.data.get('left', 0), 
            top=self.data.get('top', 0),
            shadow=ft.BoxShadow(4, 4, ft.Colors.with_opacity(.6, self.data.get('color'))) if self.visible else None,
            content=ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK, on_tap_up=self._tap_up,
                on_enter=self._highlight, on_exit=self._stop_highlight, on_pan_start=self._drag_start,
                on_pan_update=self.move_location, drag_interval=20, on_pan_end=self._drag_end,
                on_secondary_tap=lambda _: self.widget.story.open_menu(self._get_menu_options()),
                on_tap=self.show_mini_widget, on_tap_down=self._drag_start,
                content=ft.Icon(
                    icon, self.data.get('color', None), expand=True,
                    visible=True if self.data.get('icon', "label") != "label" else False,
                ), 
                expand=True,
            ),
        )


        self.map_label = ft.Container(
            expand=True,
            width=150,
            height=40,
            #border=ft.Border.all(1, "red"),
            alignment=ft.Alignment.CENTER, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            left=self.data.get('left', 0) + 12, # Offset half the width of the icon
            top=self.data.get('top', 0),
            offset=ft.Offset(-0.5, -1),
            content=ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK, on_tap_up=self._tap_up,
                on_enter=self._highlight, on_exit=self._stop_highlight, on_pan_start=self._drag_start,
                on_pan_update=self.move_location, drag_interval=20, on_pan_end=self._drag_end,
                on_secondary_tap=lambda _: self.widget.story.open_menu(self._get_menu_options()),
                on_tap=self.show_mini_widget, on_tap_down=self._drag_start, expand=True,
                content=ft.Text(           # Label that appears above our icon on the map, shows our title and appears on hover
                    self.title, theme_style=ft.TextThemeStyle.LABEL_LARGE, text_align=ft.TextAlign.CENTER, 
                    color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, expand=True,
                    #overflow=ft.TextOverflow.ELLIPSIS,
                    #left=self.data.get('left', 0),
                    #top=self.data.get('top', 0) - 30 if self.data.get('top', 0) > 30 else self.data.get('top', 0) + 30,
                )
            )
        )
        

        if no_update:
            return

        try:
            self.map_control.update()
            self.map_label.update()
        except Exception as _:
            pass


    # Called when reloading changes to our plot point and in constructor
    def reload_mini_widget(self):
        ''' Rebuilds any parts of our UI and information that may have changed when we update our data '''

        # TODO: Change icon, title, color, description
        # Allow user to pick icon

        # Cities, towns, villages, landmarks, buildings, rooms, natural features, geography, regions, POI



        location_title_text = ft.GestureDetector(
            ft.Text(
                f"\t{self.data['title']}", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, 
                color=self.data.get('color', None), expand=True
            ),
            on_double_tap=self._rename_clicked,
            on_secondary_tap=lambda _: self.widget.story.open_menu(self._get_menu_options()),
            mouse_cursor="click", hover_interval=500, expand=True
        )

        
        close_button = ft.IconButton(
            ft.Icons.CLOSE, ft.Colors.ON_SURFACE_VARIANT,
            tooltip=f"Close {self.title}",
            on_click=self.hide_mini_widget,
            mouse_cursor="click"
        )

            
        title_control = ft.Row([
            location_title_text,
            close_button
        ], spacing=0)
        
        
        if self.data.get('image_base64', ""):
            img = ft.Container(
                ft.Image(
                    src=self.data.get('image_base64', ""),
                    width=100,
                    height=100,
                    fit=ft.BoxFit.FILL,
                ), shape=ft.BoxShape.CIRCLE, clip_behavior=ft.ClipBehavior.ANTI_ALIAS
            )
        else:
            img = ft.Icon(ft.Icons.LOCATION_PIN, size=100, color=self.data.get('color', "primary"), expand=False)

        upload_image_button = ft.IconButton(img, tooltip="Upload Image", on_click=self._upload_location_image, mouse_cursor="click")

        type_tf = TextField(
            value=self.data.get('Type', ''), multiline=False, expand=True,
            on_blur=lambda e: self.change_data(**{'Type': e.control.value}),
            label="Type", capitalization=ft.TextCapitalization.WORDS, dense=True,
            hint_text="Village, Mountains, Dungeon, etc"
        )

        description_tf = TextField(
            value=self.data.get('Description', ''), multiline=True, expand=True, 
            on_blur=lambda e: self.change_data(**{'Description': e.control.value}), 
            label="Description", capitalization=ft.TextCapitalization.SENTENCES, dense=True
        )

        history_tf = TextField(
            value=self.data.get('History', ''), multiline=True, expand=True,
            on_blur=lambda e: self.change_data(**{'History': e.control.value}),
            label="History", capitalization=ft.TextCapitalization.SENTENCES, dense=True
        )

        notes_label = ft.Row([
            ft.Container(width=6),
            ft.Text("Notes", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
            ft.IconButton(
                ft.Icons.NEW_LABEL_OUTLINED, self.data.get('color', "primary"), tooltip="Add Note",
                on_click=self._new_note_clicked,
                mouse_cursor="click"
            )
        ], spacing=0)

        notes_column = self._build_notes_column()

        column = ft.Column(
            expand=True, tight=True, scroll="auto", alignment=ft.MainAxisAlignment.START, 
            controls=[
                ft.Container(height=1),

                ft.Row([upload_image_button, type_tf], spacing=0),

                description_tf,
                history_tf,
                
                notes_label,
                ft.Container(notes_column, margin=ft.Margin.symmetric(horizontal=20)),
            ]
        )

        
        self.content = ft.Column([
            title_control,
            ft.Divider(),
            column
        ], expand=True, scroll="none", spacing=0)

         
        

        try:
            self.update()
        except Exception as _:
            pass
