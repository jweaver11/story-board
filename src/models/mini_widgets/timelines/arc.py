import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
from utils.verify_data import verify_data
import flet.canvas as cv
import math
from models.app import app

# Class for arcs (essentially sub-timelines that are connected) on a timeline. 
# Arcs split off from the main timeline and can merge back in later. Exp: Characters going on different journeys that rejoin later
class Arc(MiniWidget):

    # Constructor.
    def __init__(
        self, 
        title: str, 
        owner: Widget, 
        father, 
        page: ft.Page, 
        key: str, 
        size: str = None,
        x_alignment: float = None,          # Position of plot point on timeline if we pass one in (between -1 and 1)
        data: dict = None
    ):
        
        
        # Parent constructor
        super().__init__(
            title=title,        
            owner=owner,                    # Top most timeline this arc belongs too
            father=father,                  # Immediate parent timeline or arc that thisarc belongs too
            page=page,          
            key=key,  
            data=data,         
        ) 


        # TODO:
        # Type of arcs?? timeskips, normal, character arcs

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {   
                'tag': "arc",                               # Tag to identify what type of object this is
                'is_timeskip': bool,                        # If this arc is a time skip (skips ahead in time on the timeline)   
                'start_date': str,                          # Start and end date of the branch, for timeline view
                'end_date': str,                            # Start and end date of the branch, for timeline view
                'x_alignment_start': -.2,                   # Start position on the timeline
                'x_alignment_end': .2,                      # End position on the timeline 
                'color': "secondary",                         # Color of the arc in the timeline
                'dropdown_is_expanded': True,               # If the arc dropdown is expanded on the rail
                'plot_points_are_expanded': True,           # If the plotpoints section is expanded
                'arcs_are_expanded': True,                  # If the arcs section is expanded
                'size': size,                               # Size of the arc on the timeline. Can be Small, Medium, Large, or X-Large
                'is_focused': bool,                         # If this arc is currently focused/selected. True when mini widget visible, or mouse hovering over arc
                

                'connections': dict,                        # Connect points, arcs, branch, etc.???
                'rail_dropdown_is_expanded': True,          # If the rail dropdown is expanded  
                'content': str,
                'description': str,
                'summary': str,
                'involved_characters': list,
                'related_locations': list,
                'related_items': list,
            },
        )

        # Declare dicts of our data types  
        self.arcs: dict = {}
        self.plot_points: dict = {} 

        # Set our alignment values
        self.x_alignment_start = ft.Alignment(self.data.get('x_alignment_start'), 0)
        self.x_alignment_end = ft.Alignment(self.data.get('x_alignment_end', 0), 0)


        # UI elements
        self.timeline_control: ft.Stack = None
        self.timeline_arc: ft.Container = None
        self.gd: ft.GestureDetector = None
        self.slider: ft.RangeSlider = None

        # Keep references so we can update expands without rebuilding controls every drag tick
        self.spacing_left: ft.Container = None
        self.spacing_right: ft.Container = None
        self.timeline_row: ft.Row = None

        # Build the gesture detector for our timeline arc. It doesn't need to be rebuilt, so we just do it once in constructor
        self.gd = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            expand=True,
            on_tap=lambda e: self.toggle_visibility(value=True),    # Focus this mini widget when clicked
            on_secondary_tap=lambda e: print("Right clicked arc"), 
            on_enter=self.on_start_hover,      # Highlight container
            on_exit=self.on_stop_hover,        # Stop highlight
            content=ft.Column(alignment=ft.MainAxisAlignment.CENTER, controls=[ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[ft.Text(self.title)])]),
        )   

        # State variables
        self.is_dragging: bool = False              # If we are currently dragging our arc slider

        self.is_first_launch: bool = True        # If this is the first time launching the arc, to protect from not initialized parents
      
        # Loads our mini widget
        self.reload_mini_widget()

    def delete_dict(self, e=None):

        self.owner.arcs.pop(self.data.get('title', None), None)
        super().delete_dict()


    # Called when we hover over our arc on the timeline
    async def on_start_hover(self, e: ft.HoverEvent):
        ''' Focuses the arc control '''

        # Change its border opacity and update the page
        self.timeline_arc.border=ft.border.only(
            left=ft.BorderSide(2, self.data.get('color', "secondary")),
            right=ft.BorderSide(2, self.data.get('color', "secondary")),
            top=ft.BorderSide(2, self.data.get('color', "secondary")),
        )
        self.slider.visible = True
        self.p.update()

    # Called when we stop hovering over our arc on the timeline
    async def on_stop_hover(self, e: ft.HoverEvent):
        ''' Changes the arc control to unfocused '''

        # Makes sure we stay highlighted if our information mini widget is open
        if self.visible:
            self.slider.visible = False
            self.p.update()
            return
        
        self.timeline_arc.border=ft.border.only(
            left=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
            right=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
            top=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
        )
        self.slider.visible = False
        self.p.update()
        #print("Slider should be hidden")


    def toggle_visibility(self, e=None, value: bool = None):
        ''' Toggles the visibility of our timeline_point '''

        if value is not None:

            if value == True:
                self.timeline_arc.border=ft.border.only(
                    left=ft.BorderSide(2, self.data.get('color', "secondary")),
                    right=ft.BorderSide(2, self.data.get('color', "secondary")),
                    top=ft.BorderSide(2, self.data.get('color', "secondary")),
                )

            else:
                self.timeline_arc.border = self.timeline_arc.border=ft.border.only(
                    left=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
                    right=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
                    top=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
                )
            
            super().toggle_visibility(value=value)

        else:
            super().toggle_visibility()


    # Called at the end of dragging our point on the slider to update it
    def change_x_positions(self, e: ft.DragUpdateEvent):
        ''' Changes our x position on the slider, and saves it to our data dictionary, but not to our file yet '''

        self.is_dragging = True

        # Grab our new positions as floats of whatever number division we're on (-100 -> 100)
        new_start_position = float(e.control.start_value)
        new_end_position = float(e.control.end_value)

        # Convert that float between -1 -> 1 for our alignment to work
        nsp = new_start_position / 100
        nep = new_end_position / 100

        # Save the new position to data (don't write to disk until change_end)
        self.data['x_alignment_start'] = nsp
        self.data['x_alignment_end'] = nep

        # ---- 1) & 2) Reposition + mid expansion via expand ratios (base 1000) ----
        # Clamp defensively (RangeSlider should keep ordering, but keep it safe)
        start_a = max(-1.0, min(1.0, float(self.data.get('x_alignment_start', -0.2))))
        end_a = max(-1.0, min(1.0, float(self.data.get('x_alignment_end', 0.2))))
        if end_a < start_a:
            start_a, end_a = end_a, start_a

        left_ratio = (start_a + 1.0) / 2.0          # [-1..1] -> [0..1]
        right_ratio = (1.0 - end_a) / 2.0           # [-1..1] -> [0..1]

        left_expand = int(left_ratio * 1000)
        right_expand = int(right_ratio * 1000)
        mid_expand = max(0, 1000 - left_expand - right_expand)

        # Update expands in-place
        if self.spacing_left is not None:
            self.spacing_left.expand = left_expand
        if self.spacing_right is not None:
            self.spacing_right.expand = right_expand
        if self.timeline_arc is not None:
            self.timeline_arc.expand = mid_expand

        # ---- 3) Height follows arc width (pixel-based) ----
        # Use the actual available width (timeline width minus the fixed 24px padding on each side)
        available_w = max(int(getattr(self.owner, "timeline_width", 0)) - 48, 1)
        width_px = int(((end_a - start_a) / 2.0) * available_w)  # because mapping [-1..1] to [0..W]
        max_h = max(int((getattr(self.owner, "timeline_height", 0) / 2) - 20), 0)

        # Semicircle-ish: height ~= width/2, but capped
        new_h = min(max_h, max(0, int(width_px / 2)))
        self.timeline_arc.height = new_h

        # Update visuals
        self.timeline_row.page = self.p
        self.timeline_row.update()
        

    # Called when we finish dragging our slider thumb to save our new position
    def finished_dragging(self, e):
        ''' Saves our new x positions to the file and updates alignment. Then applies the UI changes '''

        # Update our state
        self.is_dragging = False                # No longer dragging

        # Make sure our alignment are correct
        self.x_alignment_start = ft.Alignment(self.data.get('x_alignment_start', -.2), 0)
        self.x_alignment_end = ft.Alignment(self.data.get('x_alignment_end', .2), 0)

        # Determine which side of the timeline we're on for our mini widget
        mid_value = e.control.start_value + ((e.control.end_value - e.control.start_value) / 2)
        if mid_value <= 0:
            self.data['side_location'] = "right"
        else:
            self.data['side_location'] = "left"
            
        # Save our new positions to file
        self.save_dict()

        # Apply the UI changes
        #self.reload_mini_widget()
        self._render_mini_widget()
        self.owner.reload_widget()

    # Called when toggling whether this plot point is shown on the timeline in the timeline filters
    def toggle_timeline_control(self, value: bool):
        ''' Toggles whether this plot point is shown on the timeline '''

        # Change the control visibility, data, and save it
        self.timeline_control.visible = value
        self.data['is_shown_on_widget'] = value
        self.save_dict()
        
        # If we're hiding it, also hide our mini widget if it's open
        if value == False:
            self.toggle_visibility(value=value)
        # Otherwise, just update the page
        else:
            self.p.update()

    # Called when hovering over the slider
    async def enter(self, e=None):
        ''' Called when we enter this mini widget '''
        self.slider.visible = True
        self.p.update()

    # Called when exiting hover over the slider
    async def exit(self, e=None):
        ''' Called when we exit this mini widget '''
        self.slider.visible = False
        self.p.update()

    # Called whenever we need to rebuild our slider, such as on construction or when our x position changes
    def reload_slider(self):

        # Rebuild our slider
        self.slider = ft.Stack(
            alignment=ft.Alignment(0,0),
            expand=True, #height=20,
            visible=self.visible,
            controls=[
                ft.Container(expand=True, ignore_interactions=True),        # Make sure our stack is always expanded to full size
                ft.GestureDetector(                                             # GD so we can detect right clicks on our slider
                    on_secondary_tap=lambda e: self.owner.story.open_menu(self.owner.get_menu_options()),  # Open our parent timeline menu options
                    height=50, on_enter=self.enter, on_exit=self.exit,       # Change slider visibility on hover and exit
                    content=ft.RangeSlider(
                        min=-100, max=100,                                  # Min and max values on each end of slider
                        start_value=self.data.get('x_alignment_start', 0) * 100,        # Where we start on the slider
                        end_value=self.data.get('x_alignment_end', 0) * 100,            # Where we end on the slider
                        divisions=200,                                      # Number of spots on the slider
                        active_color=self.data.get('color', "secondary"),                 # Get rid of the background colors
                        tooltip="",
                        inactive_color=ft.Colors.TRANSPARENT,               # Get rid of the background colors
                        overlay_color=ft.Colors.with_opacity(.5, self.data.get('color', "secondary")),    # Color of plot point when hovering over it or dragging    
                        on_change=self.change_x_positions,       # Update our data with new x position as we drag
                        on_change_end=self.finished_dragging,                     # Save the new position, but don't write it yet    
                    ),
                ),
                
            ]
        )
                  
        

    # Called from reload mini widget to update our timeline control
    def reload_timeline_control(self):
        ''' Reloads our arc drawing on the timeline based on current/updated data, including page size '''

        # Reload our slider
        self.reload_slider()

        # Make sure our alignment are correct
        self.x_alignment_start = ft.Alignment(self.data.get('x_alignment_start', -.2), 0)
        self.x_alignment_end = ft.Alignment(self.data.get('x_alignment_end', .2), 0)

        # Give us a ratio for integers for our left and right expand values to catch hover off of our plot pont
        left_ratio = (self.data.get('x_alignment_start', 0) + 1) / 2     # Convert -1 -> 1 to 0 -> 1
        right_ratio = (1 - self.data.get('x_alignment_end', 0)) / 2     # Convert -1 -> 1 to 0 -> 1
    
        # Set the left and right ratio
        left_ratio = int(left_ratio * 1000)
        right_ratio = int(right_ratio * 1000)

        mid_ratio = 1000 - right_ratio - left_ratio

        spacing_left = ft.Container(expand=left_ratio, ignore_interactions=True)
        spacing_right = ft.Container(expand=right_ratio, ignore_interactions=True)

        # Store for live updates during dragging
        self.spacing_left = spacing_left
        self.spacing_right = spacing_right

        self.gd.content = ft.Container(content=ft.Text(self.title, selectable=True), alignment=ft.alignment.top_center)

        self.timeline_arc = ft.Container(
            offset=ft.Offset(0, -0.5),
            expand=mid_ratio,
            height=0 if self.is_first_launch else None,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            border=ft.border.only(
                left=ft.BorderSide(2, self.data.get('color', "secondary")),
                right=ft.BorderSide(2, self.data.get('color', "secondary")),
                top=ft.BorderSide(2, self.data.get('color', "secondary")),
            ),
            border_radius=ft.border_radius.only(top_left=1000, top_right=1000, bottom_left=0, bottom_right=0),
            content=self.gd,
        )
        self.is_first_launch = False

        self.timeline_row = ft.Row(
            expand=True, spacing=0,
            controls=[
                ft.Container(width=24, ignore_interactions=True),
                self.spacing_left,
                self.timeline_arc,
                self.spacing_right,
                ft.Container(width=24, ignore_interactions=True),
            ]
        )

        self.timeline_control = ft.Stack(
            expand=True,
            controls=[
                ft.Container(expand=True, ignore_interactions=True),
                self.timeline_row,
                self.slider,
            ]
        ) 
        

    # Called to reload our mini widget content
    def reload_mini_widget(self):

        # Reload our timeline control and all associated components 
        self.reload_timeline_control()

        # Reset our height depnding if we're collapsed or not
        self.height = None

        self.title_control = ft.Row([
            ft.Text(self.data['title'], weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.CLOSE,
                tooltip=f"Close {self.title}",
                on_click=lambda e: self.toggle_visibility(value=False),
            ),
        ])


        

        
        # Rebuild our information display
        self.content_control = ft.TextField(
            hint_text="Arc",
            on_submit=lambda e: self.change_custom_field(**{'new_key': e.control.value}),
            expand=True,
        )

        # Add collapse button for dragging
        def _collapse_mode(e):
           
            # Limit our height when collapsed
            self.height = 120
                
            # Row to add our collapse button so its on the correct side
            footer_row = ft.Row([
                ft.IconButton(
                    tooltip="Expand", 
                    icon=ft.Icons.KEYBOARD_DOUBLE_ARROW_DOWN_OUTLINED,
                    on_click=lambda e: self.reload_mini_widget() # Pass in whatever branch it is (just self for now)
                )
            ])

            # Align the collapse button to the correct side
            if self.data.get('side_location', "left") == "left":
                footer_row.alignment = ft.MainAxisAlignment.END
            else:
                footer_row.alignment = ft.MainAxisAlignment.START

            self.content = ft.Column(
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                controls=[
                    self.title_control,
                    ft.Container(expand=True, ignore_interactions=True),   # Pushes content to top
                    footer_row
                ],
            )
            self.p.update()
        
        # Row to add our collapse button so its on the correct side
        footer_row = ft.Row([
            ft.IconButton(
                tooltip="Collapse", 
                icon=ft.Icons.KEYBOARD_DOUBLE_ARROW_UP_OUTLINED,
                on_click=_collapse_mode # Pass in whatever branch it is (just self for now)
            )
        ])

        # Align the collapse button to the correct side
        if self.data.get('side_location', "left") == "left":
            footer_row.alignment = ft.MainAxisAlignment.END
        else:
            footer_row.alignment = ft.MainAxisAlignment.START

        self.content = ft.Column(      
            expand=True,
            controls=[
                ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    alignment=ft.MainAxisAlignment.START,
                    expand=True,
                    controls=[
                        self.title_control,
                        self.content_control,
                        ft.Container(expand=True, ignore_interactions=True),   # Spacing
                    
                    ],
                ),
                ft.Container(expand=True, ignore_interactions=True),   # Makes sure collapse button is at the bottom
                footer_row,
            ]
        )

        

        

        self.p.update()


