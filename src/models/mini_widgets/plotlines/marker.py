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
        else:
            side_location = None

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
                'description': str,
                'events': list,                 # Numbered list of events that occur at this plot point
                'x_alignment': x_alignment if x_alignment is not None else int,  # Integer between 0 and owner.plotline_width for absolute positioning
                'ratio_position': float,      # Float between -1 and 1 for relative positioning on plotline. Just used for calculations, not rendering
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

        # UI elements
        self.plotline_marker: ft.Container = None    # Circle container to show our plot point on the plotline
        self.slider: ft.Column = None               # Slider to drag our plot point along the plotline
        self.plotline_control: ft.Stack = None      # Stack that holds our plotline point and slider

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
        if new_left < 5:
            new_left = 5
        elif new_left > self.owner.plotline_width - 5:
            new_left = self.owner.plotline_width - 5
        
        # Set our new left position within our stack
        self.plotline_marker.left = new_left

        #new_alignment = min(1.0, ((new_left) / (self.owner.plotline_width - 5)) * 2 - 1, 2)   # Convert left position to -1 -> 1 alignment

        
        self.data['x_alignment'] = new_left

        self.save_dict()
        self.p.update()
        return

    def _drag_end(self, e=None):
        #self.reload_mini_widget(no_update=True)
        #self.owner.reload_widget()
        print("New alignment: ", self.data.get('x_alignment', 0))

        ratio = self.data.get('x_alignment', 0) / (self.owner.plotline_width - 10)
        


        self.data['ratio'] = ratio
        self.save_dict()
        
        
    # Called when hovering over our plot point to show the slider
    async def highlight(self, e=None):
        ''' Shows our slider and hides our plotline_marker. Makes sure all other sliders are hidden '''

        self.plotline_marker.content.content.opacity = .7 if self.plotline_marker.content.content.opacity != .7 else 1

        # Apply it to the UI
        self.p.update()

    # Called when we start dragging our slider thumb
    async def start_dragging(self, e=None):
        ''' Hides the labels of all the other plot points when we are dragging ours '''


        self.p.update()


    # Called when we stop dragging our slider thumb, or when we drag too high or low from slider
    async def hide_slider(self, e=None):
        ''' Hides our slider and puts our dot back on the plotline. Saves our new position to the file '''

        # If we clicked the slider thumb but didnt move, make our mini widget visible
        if not self.is_dragging:
            self.show_mini_widget()
            return
    
        # Hide slider
        self.slider.visible = False
        self.plotline_marker.visible = True      # Set our point to visible again
        self.is_dragging = False                # No longer dragging

        # Update our alignment based on our correct data. This is updated when dragging, so no need to set it here
        #self.x_alignment = ft.Alignment(self.data.get('x_alignment', 0), 0)

        if self.data.get('x_alignment', 0) <= 0:
            self.data['side_location'] = 'right'
        else:
            self.data['side_location'] = 'left'

        # Save new x_alignment to file
        self.save_dict()
        
        # Must reload our plot point to apply the change to ourself, then reload the parent widget to apply the change to the page
        self.reload_mini_widget()
        self.owner.reload_widget()

    # Called to determine if we want to hide our slider
    def may_hide_slider(self, e=None):
        ''' Checks our dragging state. If we are dragging, don't hide the slider '''

        # Check if we're dragging
        if self.is_dragging:
            return
        
        # If we're not dragging, hide the slider
        else:
    
            # Hide slider
            self.slider.visible = False
            self.plotline_marker.visible = True      # Set our point to visible again
            self.is_dragging = False

            # Since no data changed, just update the page to apply changes
            self.p.update()
            
    # Called when toggling whether this plot point is shown on the plotline in the plotline filters
    def toggle_plotline_control(self, value: bool):
        ''' Toggles whether this plot point is shown on the plotline '''

        # Change the control visibility, data, and save it
        self.plotline_control.visible = value
        self.data['is_shown_on_widget'] = value
        self.save_dict()
        
        # If we're hiding it, also hide our mini widget if it's open
        if value == False:
            self.hide_mini_widget(update=True)
        # Otherwise, just update the page
        else:
            self.p.update()
          

    # Called whenever we need to rebuild our slider, such as on construction or when our x position changes
    def reload_slider(self):

        # Give us a ratio for integers for our left and right expand values to catch hover off of our plot pont
        ratio = (self.data.get('x_alignment', 0) + 1) / 2     # Convert -1 -> 1 to 0 -> 1
    
        # Set the left and right ratio
        left_ratio = int(ratio * 1000)
        right_ratio = 1000 - left_ratio

        # state used during dragging
        self.slider = ft.Column(
            spacing=0,
            #visible=False,                                      # Start hidden until we hover over plot point
            controls=[
                #ft.GestureDetector(on_enter=self.hide_slider,  expand=True),    # Invisible container to hide slider when going too far up
                ft.Container(ignore_interactions=True, expand=True),    # Invisible container to hide slider when going too far up
                ft.Stack(
                    alignment=ft.Alignment(0,0),
                    controls=[
                    ft.GestureDetector(                                             # GD so we can detect right clicks on our slider
                        on_secondary_tap=lambda e: print("Right clicked plotpoint"),
                        content=ft.Slider(
                            min=-100, max=100, adaptive=True, divisions=200,  # Min and max values on each end of slider
                            value=self.data.get('x_alignment', 0) * 100,        # Where we start on the slider
                            interaction=ft.SliderInteraction.SLIDE_THUMB,       # Make sure you can only drag the plot point, and not click the slider to move it
                            active_color=ft.Colors.TRANSPARENT,                 # Get rid of the background colors
                            inactive_color=ft.Colors.TRANSPARENT,               # Get rid of the background colors
                            thumb_color=self.data.get('color', "secondary"),    # Color of our actual dot on the slider
                            overlay_color=ft.Colors.with_opacity(.5, self.data.get('color', "secondary")),    # Color of plot point when hovering over it or dragging      
                            on_change=self.change_x_position,      # Update our data with new x position as we drag
                            #on_change_end=self.hide_slider,                     # Save the new position, but don't write it yet
                            on_change_start=self.start_dragging,      # Hide other plot point labels when we start dragging                      
                            #on_blur=self.hide_slider                            # Hide the slider if we click away from it
                        ),
                    ),
                    # Sitting overtop the slider, is a row with expand based on our proportions
                    ft.Row(
                        spacing=0,
                        expand=True,
                        height=100,
                        controls=[
                            ft.GestureDetector(         # Catch our hovers to the left of the thumb
                                #on_hover=self.may_hide_slider,
                                on_pan_end=lambda e: None,
                                hover_interval=100,
                                expand=left_ratio,
                                content=ft.Container(expand=True)
                            ),
                            ft.Column(
                                width=50,
                                spacing=0,
                                controls=[
                                    
                                    # Catch above and below the thumb
                                    ft.GestureDetector(expand=True, on_pan_update=lambda e: None, data="line213", hover_interval=100),

                                    # Reserve safe space for the thumb
                                    ft.Container(       # Safe area
                                        ignore_interactions=True,
                                        shape=ft.BoxShape.CIRCLE,
                                        width=50, height=50, 
                                    ),
                                    ft.GestureDetector(expand=True, on_pan_update=lambda e: None, data="line221", hover_interval=100),
                                ]
                            ),
                            ft.GestureDetector(         # Catch our hovers to the right of the thumb
                                #on_hover=self.may_hide_slider,
                                on_pan_end=lambda e: None,
                                hover_interval=100,
                                data="called from line 226 gd",
                                expand=right_ratio,
                                content=ft.Container(expand=True)
                            ),
                        ]
                    )
                ]),
                ft.Container(ignore_interactions=True, expand=True),    # Invisible container to hide slider when going too far down
        ])

    # Called from reload_mini_widget
    def reload_plotline_control(self):
        """ Rebuilds our plotline control that holds our plot point and slider """

        

        # Reload our slider
        self.reload_slider()

        
        #print("Setting marker height to owner height:", h)
        #print("Marker height set to:", height)

        # Our container that is our plot point on the plotline, and contains our gesture detector for hovering and right clicking
        self.plotline_marker = ft.Container(
            margin=ft.Margin(16, 0, 16, 0), expand=False, #padding=ft.padding.only(left=5),
            width=10, alignment=ft.alignment.center, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            left=self.data.get('x_alignment', 0),
            #border=ft.border.all(2, "yellow"),
            content=ft.GestureDetector(
                expand=True, width=10, mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
                on_enter=self.highlight, on_exit=self.highlight,
                on_pan_update=self.change_x_position, drag_interval=20, on_pan_end=self._drag_end,
                on_secondary_tap=lambda e: print("Right click on Marker"),
                on_tap=self.show_mini_widget,
                content=cv.Canvas(
                    width=10, height=10000, opacity=.7, expand=True, resize_interval=20,
                    content=ft.Container(ignore_interactions=True, expand=True), #on_resize=_resize_plotline_canvas, 
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
            #self.update()