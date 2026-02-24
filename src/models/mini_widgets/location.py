'''
Class for marking any point of interest (location) on a map
'''

# Needs coordinates
# Allow user to pick icon
# Allow users to connect to a map


# Cities, towns, villages, landmarks, buildings, rooms, natural features, geography, regions, POI

# Data {
#       map_key -- only sub maps have a map key value, and they will just render the maps info display instead of building a new one
#}

import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
from utils.verify_data import verify_data
import math
from styles.text_styles import text_style
import flet.canvas as cv 
from styles.icons import icons

# Locations that appear on our map
class Location(MiniWidget):

    # Constructor. Requires title, owner widget, page reference, and optional data dictionary
    def __init__(
        self, 
        title: str, 
        owner: Widget, 
        page: ft.Page, 
        key: str,                          
        alignment: float = None,          
        left: int = None,                   
        top: int = None,                   
        data: dict = None       
    ):
        
        if left is not None:
            side_location = 'right' if left <= owner.map_width // 2 else 'left'
        else:
            side_location = data.get('side_location', 'right') if data is not None else 'right'


        # Parent constructor
        super().__init__(
            title=title,        
            owner=owner,        
            page=page,          
            key=key,  
            side_location=side_location,
            data=data,    
        ) 

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {   
                'tag': "location",            # Tag to identify what type of object this is
                'x_alignment': alignment if alignment is not None else (),           # Float between -1 and 1 on x axis of map. 0 is center
                'icon': "circle",
                'left': left, 
                'top': top,
                'color': "secondary",           # Color of the plot point on the map

                # Information for our information display
                'Description': str,
                'When': str,
                'Where': str,
                'Involved Characters': list,
                'Related Objects': list,
            },
        )

        # Set our x alignment to position on our map. -1 is left, 0 is center, 1 is right. Default 0
        self.alignment = ft.Alignment(self.data.get('alignment', 0), 0)

        # UI elements
        self.map_control: ft.Container    # Circle container to shows our location icon on the map
        self.map_label = ft.Text(           # Label that appears above our icon on the map, shows our title and appears on hover
            self.title, theme_style=ft.TextThemeStyle.LABEL_LARGE, text_align=ft.TextAlign.CENTER, 
            color=self.data.get('color', None), weight=ft.FontWeight.BOLD, 
            left=self.data.get('left', 0), top=self.data.get('top', 0) - 30 if self.data.get('top', 0) > 30 else self.data.get('top', 0) + 30,
            animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN), 
            overflow=ft.TextOverflow.CLIP,
        )
        self.map_label = cv.Text(
            self.data.get('left', 0) + 12, 
            self.data.get('top', 0) - 30 if self.data.get('top', 0) > 30 else self.data.get('top', 0) + 30,
            self.title, 
            ft.TextStyle(14, weight=ft.FontWeight.BOLD, color=self.data.get('color', "secondary"), overflow=ft.TextOverflow.VISIBLE),
            alignment=ft.alignment.center,
            max_width=100,
            text_align=ft.TextAlign.CENTER
        )
                      
        self.icon_button = ft.PopupMenuButton(      # Button to change the plot points icon on the map
            icon=self.data.get('icon', 'location_pin'),
            tooltip="Location Icon", icon_color=self.data.get('color', 'secondary'),
            menu_padding=ft.Padding(0,0,0,0), 
            items=self._get_icon_options()
        )

        # State variables
        self.is_dragging: bool = False              # If we are currently dragging our plot point

        # Build our slider for moving our plot point
        self.reload_map_control()
        self.reload_mini_widget(no_update=True)

    
    async def move_location(self, e: ft.DragUpdateEvent):
        ''' Changes our x position on the slider, and saves it to our data dictionary, but not to our file yet '''

        
        # Calculate our new absolute positioning based on our delta x from dragging
        new_left = self.map_control.left + e.delta_x
        new_top = self.map_control.top + e.delta_y

        # Clamp our position to the bounds of our map
        if new_left < 20:        
            new_left = 20
        elif new_left > self.owner.map_width - 20:  
            new_left = self.owner.map_width - 20
        if new_top < 20:
            new_top = 20
        elif new_top > self.owner.map_height - 20:
            new_top = self.owner.map_height - 20
        
        # Apply to data
        self.data['left'] = new_left
        self.data['top'] = self.map_control.top


        # Set our new position and animate it there
        self.map_control.left = new_left
        self.map_control.top = new_top
        self.map_label.x = new_left + 12
        self.map_label.y = new_top - 30 if new_top > 30 else new_top + 30
        #self.map_label.left = new_left - 50 if new_left > 50 else new_left + 50 
        #self.map_label.top = new_top - 30 if new_top > 30 else new_top + 30

        
        self.map_control.page = self.p
        self.map_label.page = self.p
        self.map_control.update()
        self.map_label.update()
        
          
    # Called when we start dragging
    async def _drag_start(self, e=None):
        ''' Called when we start dragging our plot point. Sets our state to dragging and changes our mouse cursor '''

        self.map_control.content.mouse_cursor = ft.MouseCursor.MOVE
        self.is_dragging = True

        # Hide all other info displays while dragging
        for mw in self.owner.mini_widgets:
            mw.visible = False

        self.p.update()

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
        
        x_alignment = (self.data.get('left', 0) / (self.owner.map_width - 10)) * 2.0 - 1.0

        self.data['x_alignment'] = x_alignment

        if self.data.get('x_alignment', 0) <= 0:
            self.data['side_location'] = "right"
        else:
            self.data['side_location'] = "left"

        self.save_dict()

        # Re-show all the info displays we hid while dragging
        for mw in self.owner.mini_widgets:
            if mw.data.get('visible', True):
                mw.visible = True

        if self.owner.information_display.visible:
            self.owner.information_display.reload_mini_widget(no_update=True)
        self.map_control.page = self.p
        self.map_control.update()
        await self.owner._rebuild_map_canvas()

    # Called when hovering over our plot point to show the slider
    async def _highlight(self, e=None):
        ''' Shows our slider and hides our map_marker. Makes sure all other sliders are hidden '''

        # Gives us a focused shadow
        self.map_control.shadow = ft.BoxShadow(5, 10, ft.Colors.with_opacity(.6, self.data.get('color'))) #if self.map_control.shadow is None else None
        self.map_control.page = self.p
        self.map_control.update()

    # Hides are shadow unless our info display is visible, then stay highlighted
    async def _stop_highlight(self, e=None):

        # If we're dragging, keep highlighted
        if self.is_dragging:
            return

        # If our info display is visible, keep highlighted
        if not self.visible:
            self.map_control.shadow = None
            self.map_control.page = self.p
            self.map_control.update()

    def _get_icon_options(self) -> list[ft.Control]:
        ''' Returns a list of all available icons for icon changing '''

        # Called when an icon option is clicked on popup menu to change icon
        def _change_icon(icon: str, e):
            ''' Passes in our kwargs to the widget, and applies the updates '''

            # Set our data and update our button icon
            self.data['icon'] = icon
            self.save_dict()

            # Update the UI to match. Map control needs owner to reload as well
            self.icon_button.icon = icon
            self.reload_map_control()
            self.owner.reload_widget()

        # List for our icons when formatted
        icon_controls = [] 

        # Create our controls for our icon options
        for icon in icons:
            icon_controls.append(
                ft.PopupMenuItem(
                    content=ft.Icon(icon, self.data.get('color', 'secondary')),
                    on_click=lambda e, ic=icon: _change_icon(ic, e)
                )
            )

        return icon_controls
    
    # Makes sure we stop highlighting
    def hide_mini_widget(self, e=None, update: bool=False):
        self.map_control.shadow = None
        self.map_control.page = self.p
        self.map_control.update()
        return super().hide_mini_widget(e, update)


    # Called from reload_mini_widget
    def reload_map_control(self):
        """ Rebuilds our map control that holds our plot point and slider """

        # Our container that is our plot point on the map, and contains our gesture detector for hovering and right clicking
        self.map_control = ft.Container(
            expand=False, 
            shape=ft.BoxShape.CIRCLE,
            alignment=ft.alignment.center, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            left=self.data.get('left', 0), animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            top=self.data.get('top', 0),
            content=ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK, on_tap_up=self._tap_up,
                on_enter=self._highlight, on_exit=self._stop_highlight, on_pan_start=self._drag_start,
                on_pan_update=self.move_location, drag_interval=20, on_pan_end=self._drag_end,
                on_secondary_tap=lambda e: self.owner.story.open_menu(self._get_menu_options()),
                on_tap=self.show_mini_widget, on_tap_down=self._drag_start,
                content=ft.Icon(self.data.get('icon', 'location_pin'), self.data.get('color', None))
            ),
        )


    # Called when reloading changes to our plot point and in constructor
    def reload_mini_widget(self, no_update: bool=False):
        ''' Rebuilds any parts of our UI and information that may have changed when we update our data '''

        
        title_control = ft.Row([
            self.icon_button,
            ft.GestureDetector(
                ft.Text(f"\t\t{self.data['title']}\t\t", weight=ft.FontWeight.BOLD, tooltip=f"Rename {self.title}"),
                on_double_tap=self._rename_clicked,
                on_tap=self._rename_clicked,
                on_secondary_tap=lambda e: self.owner.story.open_menu(self._get_menu_options()),
                mouse_cursor="click", on_hover=self.owner._hover_tab, hover_interval=500
            ),
            ft.IconButton(
                ft.Icons.PUSH_PIN_OUTLINED if not self.owner.data.get('information_display_is_pinned', False) else ft.Icons.PUSH_PIN_ROUNDED,
                self.data.get('color', None),
                tooltip="Pin Information Display" if not self.owner.data.get('information_display_is_pinned', False) else "Unpin Information Display",
                on_click=self._toggle_pin
            ),
            ft.Container(expand=True),
            ft.IconButton(
                ft.Icons.CLOSE, ft.Colors.OUTLINE,
                tooltip=f"Close {self.title}",
                on_click=lambda e: self.hide_mini_widget(update=True),
            ),
        ], spacing=0)


        description_tf = ft.TextField(
            value=self.data.get('Description', ''), multiline=True, expand=True, 
            on_blur=lambda e: self.change_data(**{'Description': e.control.value}), 
            label="Description", capitalization=ft.TextCapitalization.SENTENCES,
            tooltip="Brief description of this plot point"
        )

        custom_fields_label = ft.Row([
            ft.Container(width=6),
            ft.Text("Custom Fields", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
            ft.IconButton(
                ft.Icons.NEW_LABEL_OUTLINED, tooltip="Add Custom Field",
                on_click=lambda e: self._new_custom_field_clicked())
        ], spacing=0)

        custom_fields_column = self._build_custom_fields_column()

        content = ft.Column(
            expand=True, tight=True, scroll="auto", alignment=ft.MainAxisAlignment.START, 
            controls=[
                ft.Container(height=1),
                description_tf,
                
                
                custom_fields_label,
                ft.Container(custom_fields_column, margin=ft.margin.symmetric(horizontal=20)),
            ]
        )

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
