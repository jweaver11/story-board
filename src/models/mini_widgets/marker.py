# Markers that have a title and notes that show up as vertical lines on the Timeline
# Essentially, very simple plot points

# TODO: Add Breaks to timelines, like end book 1, end book 2, etc.
# Can be used for character deaths


import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
from utils.verify_data import verify_data
from styles.text_styles import text_style
import flet.canvas as cv

# Plotpoint mini widget object that appear on plotlines and arcs
class Marker(MiniWidget):

    # Constructor. Requires title, owner widget, page reference, and optional data dictionary
    def __init__(
        self, 
        title: str, 
        owner: Widget, 
        page: ft.Page, 
        key: str,                           # Key is plot_points for plotlines
        x_alignment: float = None,          # Position of plot point on plotline if we pass one in (between -1 and 1)
        data: dict = None       
    ):
        
        if x_alignment is not None:
            side_location = 'right' if x_alignment <= 0 else 'left'
            left_pos = int((x_alignment + 1.0) / 2.0 * (owner.plotline_width - 10)) + 5
        else:
            side_location = None
            left_pos = None

    

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
                'tag': "marker",            # Tag to identify what type of object this is
                'title': str,
                'x_alignment': x_alignment if x_alignment is not None else float,  # Float between -1 and 1 for relative positioning on plotline. Just used for calculations, not rendering
                'left': left_pos,                    # Integer Absolute left position on plotline
                'color': "secondary",           # Color of the plot point on the plotline
            },
        )
        

        # Set our x alignment to position on our plotline. -1 is left, 0 is center, 1 is right. Default 0

        # UI elements
        self.plotline_marker: ft.Container = None    # Circle container to show our plot point on the plotline
        self.slider: ft.Column = None               # Slider to drag our plot point along the plotline

        # State variables
        self.is_dragging: bool = False              # If we are currently dragging our plot point

        # Build our slider for moving our plot point
        self.reload_mini_widget()

    def delete_dict(self, e=None):

        self.owner.plot_points.pop(self.data.get('title', None), None)
        super().delete_dict()

    # Called when actively dragging our slider thumb to change our x position
    async def change_x_position(self, e=None):
        ''' Changes our x position on the slider, and saves it to our data dictionary, but not to our file yet '''

        if e is None:
            delta_x = 0
        else:
            delta_x = e.delta_x

        if not isinstance(delta_x, (int, float)):
            delta_x = 0
        
        
        # Calculate our new absolute positioning based on our delta x from dragging
        new_left = self.plotline_marker.left + delta_x

        # Clamp sides and use timeline padding
        if new_left < 0:        # Padding on left because canvas draws in middle (5px)
            new_left = 0
        elif new_left > self.owner.plotline_width - 10:  # No padding needed on right
            new_left = self.owner.plotline_width - 10
        
        # Set our new left position within our stack
        self.plotline_marker.left = new_left

        self.data['left'] = new_left

        self.save_dict()
        self.plotline_marker.page = self.p
        self.plotline_marker.update()

    # Called when we finish dragging our plotline_marker to save our position
    async def _drag_end(self, e=None):
        ''' Updates our alignment and side location, and applies the updadte to the canvas for our label '''
        
        x_alignment = (self.data.get('left', 0) / (self.owner.plotline_width - 10)) * 2.0 - 1.0

        self.data['x_alignment'] = x_alignment

        if self.data.get('x_alignment', 0) <= 0:
            self.data['side_location'] = "right"
        else:
            self.data['side_location'] = "left"

        self.save_dict()
        if self.owner.information_display.visible:
            self.owner.information_display.reload_mini_widget(no_update=True)
        await self.owner.rebuild_plotline_canvas(no_update=False)
        
        
    # Called when hovering over our plot point to show the slider
    async def highlight(self, e=None):
        ''' Shows our slider and hides our plotline_marker. Makes sure all other sliders are hidden '''

        self.plotline_marker.content.content.opacity = .7 if self.plotline_marker.content.content.opacity != .7 else 1

        # Apply it to the UI
        self.p.update()

            
    # Called when toggling whether this plot point is shown on the plotline in the plotline filters
    def toggle_plotline_control(self, value: bool):
        ''' Toggles whether this plot point is shown on the plotline '''

        # Change the control visibility, data, and save it
        self.plotline_marker.visible = value
        self.data['is_shown_on_widget'] = value
        self.save_dict()
        
        # If we're hiding it, also hide our mini widget if it's open
        if value == False:
            self.hide_mini_widget(update=True)
        # Otherwise, just update the page
        else:
            self.p.update()
          

    # Called from reload_mini_widget
    def reload_plotline_control(self):
        """ Rebuilds our plotline control that holds our plot point and slider """

        # Our container that is our plot point on the plotline, and contains our gesture detector for hovering and right clicking
        self.plotline_marker = ft.Container(
            margin=ft.Margin(16, 0, 16, 0), expand=False, 
            width=10, alignment=ft.alignment.center, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            left=self.data.get('left', 0),
            content=ft.GestureDetector(
                width=10, mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
                on_enter=self.highlight, on_exit=self.highlight,
                on_pan_update=self.change_x_position, drag_interval=20, on_pan_end=self._drag_end,
                on_secondary_tap=lambda e: print("Right click on Marker"),
                on_tap=self.show_mini_widget,
                content=cv.Canvas(
                    width=10,  opacity=.7, resize_interval=20,    
                    content=ft.Container(ignore_interactions=True, expand=True), #on_resize=_resize_plotline_canvas, 
                    shapes=[],    # Set shapes empty so timeline knows to set its dashed line
                ),
            ),
        )

        # Rebuild our stack to hold our plotline point and slider
        self.plotline_control = ft.Stack(
            visible=self.data.get('is_shown_on_widget', True),
            expand=True,            # Make sure it fills the whole plotline width
            controls=[
                ft.Container(expand=True, ignore_interactions=True),        # Make sure our stack is always expanded to full size
                self.plotline_marker,                                        # Our plot point on the plotline
                self.slider,                                                # Our slider that appears when we hover over the plot point
            ]
        ) 

        self.plotline_control = self.plotline_marker


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
        self.reload_plotline_control()

        self.title_control = ft.Row([
            ft.Icon(ft.Icons.FLAG_OUTLINED, self.owner.data.get('color', None)),
            ft.Text(self.data['title'], weight=ft.FontWeight.BOLD),
            ft.IconButton(
                ft.Icons.PUSH_PIN_OUTLINED if not self.data.get('is_pinned', False) else ft.Icons.PUSH_PIN_ROUNDED,
                self.owner.data.get('color', None),
                tooltip="Pin Information Display" if not self.data.get('is_pinned', False) else "Unpin Information Display",
                on_click=_toggle_pin
            ),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.CLOSE,
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
