'''
Very simple mini widget that shows markers on the timeline, which are simplified plot points.
Just displayed as a dashed vertical line on the plotline with a label, and a description
'''



import flet as ft
from models.widget import Widget
from models.mini_widget import MiniWidget
import flet.canvas as cv
import uuid
from constants import PLOTLINE_CANVAS_PADDING

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
            self.data.update({
                'tag': "marker",    # Since nothing shown in sidebar, just give it a tag of marker
            }) 
        
    # Child classes override this
    def create_sidebar_ctrls(self) -> list:
        ''' Creates the controls for the sidebar for this mini widget '''
        return []

    # Update state
    async def start_move(self, e=None):
        ''' Called when we start dragging our plot point. Sets our state to dragging and changes our mouse cursor '''
        self.is_dragging = True
        

    # Called when actively dragging our slider thumb to change our x position
    async def move_marker(self, e: ft.DragUpdateEvent):
        ''' Changes our x position on the slider, and saves it to our data dictionary, but not to our file yet '''

        
        # Calculate our new absolute positioning based on our delta x from dragging
        new_left = self.left + e.local_delta.x

        # Clamp sides and use timeline padding
        if new_left < PLOTLINE_CANVAS_PADDING:        # Padding on left because canvas draws in middle (5px)
            new_left = PLOTLINE_CANVAS_PADDING
        elif new_left > self.widget.plotline_width - PLOTLINE_CANVAS_PADDING: 
            new_left = self.widget.plotline_width - PLOTLINE_CANVAS_PADDING
        
        # Set our new left position within our stack
        self.left = new_left
        self.update()

    # Called when done moving. Saves our position and new alignment to data
    async def save_position(self, e=None):
        ''' Updates our alignment and side location, and applies the updadte to the canvas for our label '''

        self.is_dragging = False
        #await self.highlight()

        alignment = (
            (self.left / (self.widget.plotline_width - PLOTLINE_CANVAS_PADDING)) * 2.0 - 1.0,
            0
        )

        self.update_data(**{'alignment': alignment, 'position': (self.left, 0)})


        #if self.widget.information_display.visible:
            #self.widget.information_display.reload_mini_widget()

        
    async def show_mini_widget(self, e = None):
        return 
     

    # Called from reload_mini_widget
    def build(self):
        """ Rebuilds our plotline control that holds our plot point and slider """

        super().build()

        async def highlight(e: ft.HoverEvent=None):
            shadow = ft.BoxShadow(
                2, 4, 
                ft.Colors.with_opacity(0.2, self.data.get('color', ft.Colors.PRIMARY)), 
                #blur_style=ft.BlurStyle.OUTER
            )
            highlight_container1.shadow = shadow
            highlight_container2.shadow = shadow
            self.update()

        # Called when we stop hovering over our marker
        async def stop_highlight(e: ft.Event=None):
            if self.shown_in_sidebar:
                return
            highlight_container1.shadow = None
            highlight_container2.shadow = None
            self.update()


        # Set our size
        self.height = self.page.height / 2
        #self.width = 10

        # Our container that is our plot point on the plotline, and contains our gesture detector for hovering and right clicking
        self.content = ft.Column([
            highlight_container1 := ft.Container(
                ft.GestureDetector(
                    ft.Text(self.data.get('title'), width=100, text_align=ft.TextAlign.CENTER),
                    on_enter=highlight,
                    on_exit=stop_highlight,
                    on_tap_down=self.start_move,
                    on_pan_start=self.start_move,
                    on_pan_end=self.save_position,
                    on_pan_update=self.move_marker,
                    mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
                    on_secondary_tap=lambda _: self.widget.story.open_menu(self.get_menu_options()),
                    on_tap=self.show_mini_widget,
                ),
                width=100,
            ),
            highlight_container2 := ft.Container(
                cv.Canvas(
                    width=10, opacity=.7,
                    expand=True,   
                    content=ft.GestureDetector(
                        on_enter=highlight,
                        on_exit=stop_highlight,
                        on_tap_down=self.start_move,
                        on_pan_start=self.start_move,
                        on_pan_end=self.save_position,
                        on_pan_update=self.move_marker,
                        expand=True,
                        mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
                        on_secondary_tap=lambda _: self.widget.story.open_menu(self.get_menu_options()),
                        on_tap=self.show_mini_widget,
                    ),
                    shapes=[
                        cv.Line(
                            4, 0, 4, self.height, 
                            paint=ft.Paint(
                                self.data.get('color', ft.Colors.PRIMARY),
                                stroke_dash_pattern=[10, 10],
                                stroke_width=3
                            ) 
                        ),
                    ]
                ),
                width=10, expand=True
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)            
        