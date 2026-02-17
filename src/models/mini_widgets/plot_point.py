import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
from utils.verify_data import verify_data
import math
from styles.text_styles import text_style
import flet.canvas as cv

# Plotpoint mini widget object that appear on plotlines and arcs
class PlotPoint(MiniWidget):

    # Constructor. Requires title, owner widget, page reference, and optional data dictionary
    def __init__(
        self, 
        title: str, 
        owner: Widget, 
        page: ft.Page, 
        key: str,                           # Key is plot_points for plotlines
        x_alignment: float = None,          # Position of plot point on plotline if we pass one in (between -1 and 1)
        left: int = None,                   # Absolute left position on plotline. If not provided, will be calculated from x_alignment
        data: dict = None       
    ):
        
        if left is not None:
            side_location = 'right' if left <= owner.plotline_width // 2 else 'left'
        else:
            side_location = 'right'

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
                'tag': "plot_point",            # Tag to identify what type of object this is
                'summary': str,
                'x_alignment': x_alignment if x_alignment is not None else float,           # Float between -1 and 1 on x axis of plotline. 0 is center
                'left': left, 
                'is_major': bool,               # If this plot point is a major event
                'date': str,                    # Date of the plot point
                'time': str,                    # Time of the plot point
                'color': "secondary",           # Color of the plot point on the plotline
                'involved_characters': list,
                'related_locations': list,
                'related_items': list,
            },
        )

        # Set our x alignment to position on our plotline. -1 is left, 0 is center, 1 is right. Default 0
        self.x_alignment = ft.Alignment(self.data.get('x_alignment', 0), 0)

        # UI elements
        self.plotline_control: ft.Container = None    # Circle container to show our plot point on the plotline

        # State variables
        self.is_dragging: bool = False              # If we are currently dragging our plot point

        # Build our slider for moving our plot point
        self.reload_plotline_control()
        self.reload_mini_widget(no_update=True)

    def delete_dict(self, e=None):

        self.owner.plot_points.pop(self.data.get('title', None), None)
        super().delete_dict()

    
    async def move_plot_point(self, e=None):
        ''' Changes our x position on the slider, and saves it to our data dictionary, but not to our file yet '''

        if e is None:
            delta_x = 0
        else:
            delta_x = e.delta_x

        if not isinstance(delta_x, (int, float)):
            delta_x = 0
        
        
        # Calculate our new absolute positioning based on our delta x from dragging
        new_left = self.plotline_control.left + delta_x

        # Clamp sides and use timeline padding
        if new_left < 0:        # Padding on left because canvas draws in middle (5px)
            new_left = 0
        elif new_left > self.owner.plotline_width - 16:  # No padding needed on right
            new_left = self.owner.plotline_width - 16
        
        # Set our new left position within our stack
        self.plotline_control.left = new_left

        self.data['left'] = new_left

        self.save_dict()
        self.plotline_control.page = self.p
        self.plotline_control.update()
        
            
    # Called when toggling whether this plot point is shown on the plotline in the plotline filters
    def toggle_plotline_control(self, value: bool):
        ''' Toggles whether this plot point is shown on the plotline '''

        # Change the control visibility, data, and save it
        self.plotline_control.visible = value
        self.data['is_shown_on_widget'] = value
        self.save_dict()
        
        # If we're hiding it, also hide our mini widget if it's open
        if value == False:
            self.hide_mini_widget()

        self.owner.reload_widget()
          
    # Called when we start dragging
    async def _drag_start(self, e=None):
        ''' Called when we start dragging our plot point. Sets our state to dragging and changes our mouse cursor '''

        self.plotline_control.content.mouse_cursor = ft.MouseCursor.RESIZE_LEFT_RIGHT
        self.is_dragging = True

        # Hide all other info displays while dragging
        for mw in self.owner.mini_widgets:
            mw.visible = False

        self.p.update()

    # Quick fixer for the mouse cursor and highlight is we just clicked the plotpoint without dragging
    async def _tap_up(self, e=None):
        self.plotline_control.content.mouse_cursor = ft.MouseCursor.CLICK
        await self._highlight()

    # Called when we finish dragging our plotline_marker to save our position
    async def _drag_end(self, e=None):
        ''' Updates our alignment and side location, and applies the updadte to the canvas for our label '''

        self.plotline_control.content.mouse_cursor = ft.MouseCursor.CLICK
        self.is_dragging = False
        if not self.visible:        # Turn of highlight if we're not visilbe
            self.plotline_control.shadow = None
        
        x_alignment = (self.data.get('left', 0) / (self.owner.plotline_width - 10)) * 2.0 - 1.0

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
        await self.owner.rebuild_plotline_canvas(no_update=False)

        self.owner.story.active_rail.content.reload_rail()

    # Called when hovering over our plot point to show the slider
    async def _highlight(self, e=None):
        ''' Shows our slider and hides our plotline_marker. Makes sure all other sliders are hidden '''

        # Gives us a focused shadow
        self.plotline_control.shadow = ft.BoxShadow(5, 10, ft.Colors.with_opacity(.6, self.data.get('color'))) #if self.plotline_control.shadow is None else None
        self.plotline_control.page = self.p
        self.plotline_control.update()

    # Hides are shadow unless our info display is visible, then stay highlighted
    async def _stop_highlight(self, e=None):

        if self.is_dragging:
            return

        if not self.visible:
            self.plotline_control.shadow = None
            self.plotline_control.page = self.p
            self.plotline_control.update()


    # Called from reload_mini_widget
    def reload_plotline_control(self):
        """ Rebuilds our plotline control that holds our plot point and slider """

        # Our container that is our plot point on the plotline, and contains our gesture detector for hovering and right clicking
        self.plotline_control = ft.Container(
            margin=ft.Margin(16, 0, 16, 0), expand=False, 
            width=16, height=16, opacity=1.0, bgcolor=self.data.get('color'),
            shape=ft.BoxShape.CIRCLE,
            alignment=ft.alignment.center, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            left=self.data.get('left', 0), animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            content=ft.GestureDetector(
                width=16, mouse_cursor=ft.MouseCursor.CLICK, on_tap_up=self._tap_up,
                on_enter=self._highlight, on_exit=self._stop_highlight, on_pan_start=self._drag_start,
                on_pan_update=self.move_plot_point, drag_interval=20, on_pan_end=self._drag_end,
                on_secondary_tap=lambda e: print("Right click on PP"),
                on_tap=self.show_mini_widget, on_tap_down=self._drag_start
            ),
        )


    # Called when reloading changes to our plot point and in constructor
    def reload_mini_widget(self, no_update: bool=False):
        ''' Rebuilds any parts of our UI and information that may have changed when we update our data '''

        async def _toggle_pin(e):
            ''' Pins or unpins our information display '''
            is_pinned = self.data.get('is_pinned', False)
            self.data['is_pinned'] = not is_pinned
            self.save_dict()
            self.reload_mini_widget()
            self.owner.reload_widget()

        # Reload our plotline control
        #self.reload_plotline_control()

        self.title_control = ft.Row([
            ft.Icon(ft.Icons.LOCATION_PIN, self.owner.data.get('color', None)),
            ft.Text(self.data['title'], weight=ft.FontWeight.BOLD),
            ft.IconButton(
                ft.Icons.PUSH_PIN_OUTLINED if not self.data.get('is_pinned', False) else ft.Icons.PUSH_PIN_ROUNDED,
                self.owner.data.get('color', None),
                tooltip="Pin Information Display" if not self.data.get('is_pinned', False) else "Unpin Information Display",
                on_click=_toggle_pin
            ),
            ft.Container(expand=True),
            ft.IconButton(
                ft.Icons.CLOSE, ft.Colors.ON_SURFACE_VARIANT,   
                tooltip=f"Close {self.title}",
                on_click=lambda e: self.hide_mini_widget(update=True),
            ),
        ])
        

        content = ft.Column([
            self.title_control,
            ft.Divider(height=2, thickness=2),
            ft.Container(height=10)  # Spacing 
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
