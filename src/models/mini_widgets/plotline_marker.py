'''
Very simple mini widget that shows markers on the timeline, which are simplified plot points.
Just displayed as a dashed vertical line on the plotline with a label, and a description
'''



import flet as ft
from models.widget import Widget
from models.mini_widget import MiniWidget
import flet.canvas as cv
import uuid

# Plotpoint mini widget object that appear on plotlines and arcs
class PlotlineMarker(MiniWidget):

    # Constructor. Requires title, widget widget, page reference, and optional data dictionary
    def __init__(
        self, 
        widget: Widget, 
        data: dict = None,
        is_new: bool=False       
    ):
        # Set our variables
        super().__init__(widget=widget, data=data, is_new=is_new) # Sets our data to the passed in data

        # If we're new, give default values for our data 
        if self.is_new:
            self.data = {
                'tag': "marker",            # Tag to identify what type of object this is
            }
        
    # Child classes override this
    def create_sidebar_ctrls(self) -> list:
        ''' Creates the controls for the sidebar for this mini widget '''
        return []

    async def start_move(self, e=None):
        ''' Called when we start dragging our plot point. Sets our state to dragging and changes our mouse cursor '''

        self.plotline_control.content.mouse_cursor = ft.MouseCursor.RESIZE_LEFT_RIGHT
        self.is_dragging = True
        self.plotline_control.update()
        

    # Called when actively dragging our slider thumb to change our x position
    async def move_marker(self, e: ft.DragUpdateEvent):
        ''' Changes our x position on the slider, and saves it to our data dictionary, but not to our file yet '''

        if e is None:
            delta_x = 0
        else:
            delta_x = e.local_delta.x

        if not isinstance(delta_x, (int, float)):
            delta_x = 0
        
        # Calculate our new absolute positioning based on our delta x from dragging
        new_left = self.plotline_control.left + delta_x

        # Clamp sides and use timeline padding
        if new_left < 10:        # Padding on left because canvas draws in middle (5px)
            new_left = 10
        elif new_left > self.widget.plotline_width - 20:  # No padding needed on right
            new_left = self.widget.plotline_width - 20
        
        # Set our new left position within our stack
        self.plotline_control.left = new_left

        self.data['left'] = new_left

        self.plotline_control.update()

    # Called when we finish dragging our plotline_marker to save our position
    async def _drag_end(self, e=None):
        ''' Updates our alignment and side location, and applies the updadte to the canvas for our label '''

        self.plotline_control.content.mouse_cursor = ft.MouseCursor.CLICK
        self.is_dragging = False

        await self.highlight()

        x_alignment = (self.data.get('left', 0) / (self.widget.plotline_width - 10)) * 2.0 - 1.0

        self.update_data(**{'x_alignment': x_alignment, 'left': self.data.get('left', 0)})


        #if self.widget.information_display.visible:
            #self.widget.information_display.reload_mini_widget()

        
        
     

    # Called from reload_mini_widget
    def build(self):
        """ Rebuilds our plotline control that holds our plot point and slider """
        #self.margin=ft.Margin(16, 0, 16, 0)
        self.expand=True
        self.alignment=ft.Alignment.CENTER
        self.clip_behavior=ft.ClipBehavior.HARD_EDGE
        #bgcolor="red",
        #border=ft.Border.all(2, self.data.get('color', None), ft.BorderSide(style=ft.BorderStyle.SOLID)),
        self.left=self.data.get('left', 0)
        self.animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN)
        self.width=10
        self.mouse_cursor=ft.MouseCursor.CLICK
        self.on_enter=self.highlight
        self.on_exit=self.highlight
        self.on_tap_down=self.start_move
        self.on_pan_start=self.start_move
        self.on_pan_end=self._drag_end
        self.on_pan_update=self.move_marker
        #self.on_secondary_tap=lambda _: self.widget.story.open_menu(self.get_menu_options()),
        #self.on_tap=self.show_mini_widget,

        # Our container that is our plot point on the plotline, and contains our gesture detector for hovering and right clicking
        self.content = cv.Canvas(
            width=10, opacity=.7, resize_interval=20,    
            content=ft.Container(ignore_interactions=True, expand=True),
            shapes=[],    # Set shapes empty so timeline knows to set its dashed line
        )
            
        