import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
from utils.verify_data import verify_data
import flet.canvas as cv
import math
from models.app import app


class Arc(MiniWidget):

    # Constructor.
    def __init__(
        self, 
        title: str, 
        owner: Widget, 
        page: ft.Page, 
        key: str, 
        x_alignment: float = None,          # Position of plot point on plotline if we pass one in (between -1 and 1)
        data: dict = None
    ):
        
        
        # Parent constructor
        super().__init__(
            title=title,        
            owner=owner,                    # Top most plotline this arc belongs too
            page=page,          
            key=key,  
            data=data,         
        ) 

        # Set either left or right on start
        if x_alignment is not None:
            x_alignment_start = x_alignment -.2 if x_alignment > -0.8 else -1
            x_alignment_end = x_alignment + .2 if x_alignment < 0.8 else 1
            side_location = "left" if x_alignment > 0 else "right"
        else:
            x_alignment_start = -0.2
            x_alignment_end = 0.2
            side_location = "right"

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {   
                # Mini widget data
                'tag': "arc",                               # Tag to identify what type of object this is
                'color': "secondary",                       # Color of the arc in the plotline
                
                # Rail display data
                'dropdown_is_expanded': True,               # If the arc dropdown is expanded on the rail
                
                # For rendering on plotline
                'side_location': side_location, 
                'on_top': True,                             # If the mini widget should appear on top of the plotline. If false, appears below      
                'rail_dropdown_is_expanded': True,          # If the rail dropdown is expanded  
                'is_shown_on_widget': True,                 # If this arcs plotline control is shown on the plotline widget
                'x_alignment_start': x_alignment_start,     # Start position on the plotline
                'x_alignment_end': x_alignment_end,         # End position on the plotline 
                
                # Arc Data

                'summary': str,
                'start_date': str,                          # Start and end date of the branch, for plotline view
                'end_date': str, 
                'involved_characters': list,
                'related_locations': list,
                'related_items': list,
                'events': list,                             # List of events that occur during this arc

            },
        )

        # Declare dicts of our data types  
        self.arcs: dict = {}
        self.plot_points: dict = {} 

        # Set our alignment values
        self.x_alignment_start = ft.Alignment(self.data.get('x_alignment_start'), 0)
        self.x_alignment_end = ft.Alignment(self.data.get('x_alignment_end', 0), 0)


        # UI elements
        self.plotline_control: ft.Stack = None      # Physical slider control that goes on the plotline
        self.plotline_arc: ft.Container = None      # The actual arc container that draws the arc on the plotline
        self.gd: ft.GestureDetector = None
        self.slider: ft.RangeSlider = None

        # Keep references so we can update expands without rebuilding controls every drag tick
        self.spacing_left: ft.Container = None
        self.spacing_right: ft.Container = None
        self.plotline_row: ft.Row = None

        # Build the gesture detector for our plotline arc. It doesn't need to be rebuilt, so we just do it once in constructor
        self.gd = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            expand=True, on_hover=self.on_hovers, hover_interval=20,
            on_tap=self.show_mini_widget,    # Focus this mini widget when clicked
            on_secondary_tap=lambda e: print("Right clicked arc"), 
            on_enter=self.on_start_hover,      # Highlight container
            on_exit=self.on_stop_hover,        # Stop highlight
            content=ft.Column(alignment=ft.MainAxisAlignment.CENTER, controls=[ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[ft.Text(self.title)])]),
        )   

        # State variables
        self.is_dragging: bool = False              # If we are currently dragging our arc slider
        self.can_open: bool = False                 # If we can open our mini widget. Used for handling when mouse over plotline and arc control, give PL priority
        self.hidden = False                         # Track if we're in hidden mode for easier dragging

        # Loads our arc
        self.reload_mini_widget()

    def delete_dict(self, e=None):

        self.owner.arcs.pop(self.data.get('title', None), None)
        super().delete_dict()


    # Called when we hover over our arc on the plotline
    async def on_start_hover(self, e: ft.HoverEvent):
        ''' Focuses the arc control '''
        self.can_open = True

        # Change its border opacity and update the page
        self.plotline_arc.border=ft.border.only( 
            left=ft.BorderSide(2, self.data.get('color', "secondary")),
            right=ft.BorderSide(2, self.data.get('color', "secondary")),
            top=ft.BorderSide(2, self.data.get('color', "secondary")),
        )
        self.gd.content.opacity = 1.0
        self.p.update()

    async def on_hovers(self, e: ft.HoverEvent):
        if self.plotline_arc.height is not None:
            if self.plotline_arc.height - e.local_y <= 25:
                self.can_open = False
            else:
                self.can_open = True

    # Called when we stop hovering over our arc on the plotline
    async def on_stop_hover(self, e: ft.HoverEvent):
        ''' Changes the arc control to unfocused '''
        self.can_open = True
        
        # If our info display is not opened (we are not visible), lower the border opacity and update the page
        if not self.visible:
            self.plotline_arc.border=ft.border.only(
                left=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
                right=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
                top=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
            )
            self.gd.content.opacity = .7
            self.p.update()

    def show_mini_widget(self, e=None):

        # If we're too close to the timeline, just open that instead
        if not self.can_open:
            self.owner.information_display.show_mini_widget()
            return
        
        self.opacity = 1
        self.ignore_interactions = False
        self.plotline_arc.border = ft.border.only(
            left=ft.BorderSide(2, self.data.get('color', "secondary")),
            right=ft.BorderSide(2, self.data.get('color', "secondary")),
            top=ft.BorderSide(2, self.data.get('color', "secondary")),
        )

        for arc in self.owner.arcs.values():
            if arc != self and arc.data.get('is_pinned', False) == False:
                arc.hide_mini_widget()

        if not self.hidden:
            super().show_mini_widget()
        else:
            self.data['visible'] = True
            self.visible = True
            self.save_dict()

            for mw in self.owner.mini_widgets:
                if mw != self and mw.data.get('is_pinned', False) == False:
                    mw.hide_mini_widget()   

            self.reload_mini_widget(no_update=True)
            self.owner.reload_widget()
    

    def hide_mini_widget(self, e=None, update: bool=False):
        ''' Hides this arc '''

        # Set the parts we need to hide in addition to the mini widget info display
        self.opacity = 0
        self.ignore_interactions = True
        self.slider.visible = False

        self.plotline_arc.border = ft.border.only(
            left=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
            right=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
            top=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
        )
        

        return super().hide_mini_widget(update=update)


    # Called at the start of dragging our point on the slider
    async def start_dragging(self, e):
        ''' Called when we start dragging our slider thumb '''

        self.is_dragging = True

        # Hide all other plot points while dragging for behavior and visual reasons
        for pp in self.owner.plot_points.values():
            pp.plotline_control.visible = False

        # Hide all other info displays while dragging
        for mw in self.owner.mini_widgets:
            mw.visible = False

        self.p.update()


    # Called at the end of dragging our point on the slider to update it
    def change_x_positions(self, e: ft.DragUpdateEvent):
        ''' Changes our x position on the slider, and saves it to our data dictionary, but not to our file yet '''

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
        if self.plotline_arc is not None:
            self.plotline_arc.expand = mid_expand

        # ---- 3) Height follows arc width (pixel-based) ----
        # Use the actual available width (plotline width minus the fixed 24px padding on each side)
        available_w = max(int(getattr(self.owner, "plotline_width", 0)) - 48, 1)
        width_px = int(((end_a - start_a) / 2.0) * available_w)  # because mapping [-1..1] to [0..W]
        max_h = max(int((getattr(self.owner, "plotline_height", 0) / 2) - 50), 0)

        # Semicircle-ish: height ~= width/2, but capped
        new_h = min(max_h, max(0, int(width_px / 2)))
        self.plotline_arc.height = new_h

        self.p.update()
        

    # Called when we finish dragging our slider thumb to save our new position
    def finished_dragging(self, e):
        ''' Saves our new x positions to the file and updates alignment. Then applies the UI changes '''

        # Update our state
        self.is_dragging = False                # No longer dragging

        # Make sure our alignment are correct
        self.x_alignment_start = ft.Alignment(self.data.get('x_alignment_start', -.2), 0)
        self.x_alignment_end = ft.Alignment(self.data.get('x_alignment_end', .2), 0)
        self.data['x_alignment'] = (self.data.get('x_alignment_end', 0) + self.data.get('x_alignment_start', 0)) / 2

        # Determine which side of the plotline we're on for our mini widget
        mid_value = e.control.start_value + ((e.control.end_value - e.control.start_value) / 2)
        if mid_value <= 0:
            self.data['side_location'] = "right"
        else:
            self.data['side_location'] = "left"

        # Make all other plot points visible again
        for pp in self.owner.plot_points.values():
            if pp.data.get('is_shown_on_widget', True):
                pp.plotline_control.visible = True
            
        # Save our new positions to file
        self.save_dict()

        for mw in self.owner.mini_widgets:
            if mw.data.get('visible', True):
                mw.visible = True

        # Apply the UI changes
        #self.reload_mini_widget()
        self.owner.reload_widget()

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

        # Rebuild our slider
        self.slider = ft.Stack(
            alignment=ft.Alignment(0,0),
            expand=True, #height=20,
            visible=self.visible,
            controls=[
                ft.Container(expand=True, ignore_interactions=True),        # Make sure our stack is always expanded to full size
                ft.GestureDetector(                                             # GD so we can detect right clicks on our slider
                    on_secondary_tap=lambda e: self.owner.story.open_menu(self.owner.get_menu_options()),  # Open our parent plotline menu options
                    height=50,       # Change slider visibility on hover and exit
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
                        on_change_start=self.start_dragging,
                    ),
                ),
                
            ]
        )
                  
        

    # Called from reload mini widget to update our plotline control
    def reload_plotline_control(self):
        ''' Reloads our arc drawing on the plotline based on current/updated data, including page size '''

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

        self.gd.content = ft.Container(
            ft.Text(self.title, style=ft.TextStyle(14, weight=ft.FontWeight.BOLD, color=self.data.get('color', "secondary"), overflow=ft.TextOverflow.ELLIPSIS)), 
            alignment=ft.alignment.top_center, opacity=.7, padding=ft.padding.only(top=10)
        )


        # ---- 1) & 2) Reposition + mid expansion via expand ratios (base 1000) ----
        # Clamp defensively (RangeSlider should keep ordering, but keep it safe)
        start_a = max(-1.0, min(1.0, float(self.data.get('x_alignment_start', -0.2))))
        end_a = max(-1.0, min(1.0, float(self.data.get('x_alignment_end', 0.2))))
        if end_a < start_a:
            start_a, end_a = end_a, start_a


        available_w = max(int(getattr(self.owner, "plotline_width", 0)) - 48, 1)
        width_px = int(((end_a - start_a) / 2.0) * available_w)  # because mapping [-1..1] to [0..W]
        max_h = max(int((getattr(self.owner, "plotline_height", 0) / 2) - 50), 0)

        # Semicircle-ish: height ~= width/2, but capped
        new_h = min(max_h, max(0, int(width_px / 2)))

        self.plotline_arc = ft.Container(
            offset=ft.Offset(0, -0.5),
            expand=mid_ratio,
            height=new_h,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            border=ft.border.only(
                left=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
                right=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
                top=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
            ),
            border_radius=ft.border_radius.only(top_left=1000, top_right=1000, bottom_left=0, bottom_right=0),
            content=self.gd,
        )

        self.plotline_row = ft.Row(
            expand=True, spacing=0,
            controls=[
                ft.Container(width=24, ignore_interactions=True),
                self.spacing_left,
                self.plotline_arc,
                self.spacing_right,
                ft.Container(width=24, ignore_interactions=True),
            ]
        )

        self.plotline_control = ft.Stack(
            expand=True,
            controls=[
                ft.Container(expand=True, ignore_interactions=True),
                self.plotline_row,
                self.slider,
            ]
        ) 
        

    # Called to reload our mini widget content
    def reload_mini_widget(self, no_update: bool=False):

        async def _toggle_pin(e):
            ''' Pins or unpins our information display '''
            is_pinned = self.data.get('is_pinned', False)
            self.data['is_pinned'] = not is_pinned
            self.save_dict()
            self.reload_mini_widget()
            self.owner.reload_widget()
            print("Toggling pin to:", not is_pinned)

        # Reload our plotline control and all associated components 
        self.reload_plotline_control()

        # Add hide mode so we can drag without Info Display taking up the screen
        def _hide_mode(e):
            self.opacity = 0 if self.opacity == 1 else 1
            self.ignore_interactions = True if self.ignore_interactions == False else False
            self.hidden = True
            self.p.update()


        self.title_control = ft.Row([
            ft.Icon(ft.Icons.CIRCLE_OUTLINED, self.owner.data.get('color', None)),
            ft.Text(self.data['title'], weight=ft.FontWeight.BOLD),
            ft.IconButton(
                ft.Icons.PUSH_PIN_OUTLINED if not self.data.get('is_pinned', False) else ft.Icons.PUSH_PIN_ROUNDED,
                self.owner.data.get('color', None),
                tooltip="Pin Information Display" if not self.data.get('is_pinned', False) else "Unpin Information Display",
                on_click=_toggle_pin
            ),
            ft.Container(expand=True),
            ft.IconButton(
                ft.Icons.MINIMIZE_OUTLINED, ft.Colors.ON_SURFACE_VARIANT,
                tooltip="Hide", on_click=_hide_mode
            ),
            ft.IconButton(
                ft.Icons.CLOSE, ft.Colors.ON_SURFACE_VARIANT,
                tooltip=f"Close {self.title}", on_click=lambda e: self.hide_mini_widget(update=True),
            ),
        ], spacing=0)

        
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


