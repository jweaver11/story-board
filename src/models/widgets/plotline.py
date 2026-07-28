'''
Our plotline object that stores plot points, arcs, and time skips.
These objects is displayed in the plotlines widget, and store our mini widgets plot points, arcs, and time skips.
'''

import json
import os
import flet as ft
from styles.menu_option_style import MenuOptionStyle
from models.views.story import Story
from models.widget import Widget
from models.mini_widgets.plotline_arc import PlotlineArc
from models.mini_widgets.plotline_plot_point import PlotlinePlotPoint
import flet.canvas as cv
from models.app import app
import asyncio 
import uuid
from constants import PLOTLINE_PADDING, PLOTLINE_WIDTH, PLOTLINE_HEIGHT


class Plotline(Widget):

    # Constructor
    def __init__(self, title: str, directory_path: str, story: Story, data: dict={}, is_new: bool = False):
        
        # Parent constructor
        super().__init__(
            title = title,  
            directory_path = directory_path, 
            story = story,     
            data = data,  
            is_new = is_new
        ) 


        # If we're new, give default values for our data 
        if self.is_new == True:
            self.data.update({
                # Widget Data
                'tag': "plotline",
                'color': app.settings.data.get('widget_defaults', {}).get('plotline', {}).get('color'),
                
                'show_sidebar': True,   # Whether to show the info column on the side of our plotline 

                # Data in our info_display
                'time_label': "Years",                          # Label for the time axis (any str they want)
                'left_label': "0",                              # Start label
                'right_label': "10",                            # Start and end date of the branch, for plotline view
                'divisions': ["1", "2", "3", "4", "5", "6", "7", "8", "9"],    # List len is the num of divisions, and each value is its label
              

                'markers': dict(),  # 'id': {data}
                
                # Holds our data for all markers, plot points, and arcs
                'mini_widgets_data': {     
                    #'id': {data}
                }
            },
        ) 
                
        # State elements
        #self.show_hover_effects: bool = False   # If we should show hover effects of our plotline. Plot points and markers turn these off when hovering over them
        self.showing_info: bool = True
        self.can_open_menu: bool = False
        self.position = (0, None)  # Position for opening the menu when right clicking. We only care about x position, y is always middle of plotline
        self.locked_position = (0, None)  # Locked position for our plotline. We don't want it to move, so we lock it in place

        # Our plotline canvas that draws our plotline line and markers
        self.plotline_canvas: cv.Canvas     # Canvas used to just draw our plotline line and markers
        self.plotline_highlight_container: ft.Container   # Container that shows a highlight when hovering over the plotline
        self.arc_stack: ft.Stack
        self.marker_stack: ft.Stack
        self.plot_point_stack: ft.Stack   

    class PlotlineMarker(ft.Column):

        # Constructor. Requires title, widget widget, page reference, and optional data dictionary
        def __init__(
            self, 
            widget: 'Plotline',  
            data: dict = None,
            is_new: bool=False       
        ):
            self.widget = widget
            # Set our variables
            super().__init__(data=data, horizontal_alignment=ft.CrossAxisAlignment.CENTER, offset=ft.Offset(-0.5, 0)) # Sets our data to the passed in data

            # If we're new, give default values for our data 
            if is_new:
                self.data = {
                    'id': str(uuid.uuid4()),
                    'tag': "marker",    # Since nothing shown in sidebar, just give it a tag of marker
                    'title': "New Marker",  # Title for our marker
                    'color': "primary",
                    'position': self.widget.locked_position
                }

        def update_data(self, **kwargs):
            # Allow Updates our data
            def _merge_data(target: dict, updates: dict):
                for key, value in updates.items():
                    current_value = target.get(key)
                    if isinstance(current_value, dict) and isinstance(value, dict):
                        _merge_data(current_value, value)
                    else:
                        target[key] = value
    
            # Merge our data then have the widget match
            _merge_data(self.data, kwargs)  
            self.widget.update_data(**{'markers': {self.data.get('id', ''): self.data}})  # Update our widget's data with our new data
            

        # Move our marker when dragging it
        async def move_marker(self, e: ft.DragUpdateEvent):
            # Calculate new left and clamp. Apply updates
            new_left = self.left + e.local_delta.x
            if new_left < PLOTLINE_PADDING:       
                new_left = PLOTLINE_PADDING
            elif new_left > PLOTLINE_WIDTH - PLOTLINE_PADDING: 
                new_left = PLOTLINE_WIDTH - PLOTLINE_PADDING
            self.left = new_left
            self.update()
        

        # Called from reload_mini_widget
        def build(self):
            """ Rebuilds our plotline control that holds our plot point and slider """

            def highlight(e=None):
                shadow = ft.BoxShadow(
                    2, 4, 
                    ft.Colors.with_opacity(0.24, self.data.get('color', ft.Colors.PRIMARY)), 
                    #blur_style=ft.BlurStyle.OUTER
                )
                highlight_container1.shadow = shadow
                highlight_container2.shadow = shadow
                self.update()

            # Called when we stop hovering over our marker
            async def stop_highlight(e=None):
                highlight_container1.shadow = None
                highlight_container2.shadow = None
                self.update()
                

            # Set our size
            self.height = PLOTLINE_HEIGHT / 2
            self.left = self.data.get('position', (PLOTLINE_WIDTH // 2, 1000))[0]  # Get our left position from our data, or default to middle of plotline

            # Our container that is our plot point on the plotline, and contains our gesture detector for hovering and right clicking
            self.controls = [
                highlight_container1 := ft.Container(
                    ft.TextField(
                        self.data.get('title'), color=self.data.get('label_color', None), 
                        text_style=ft.TextStyle(
                            weight=ft.FontWeight.BOLD, 
                            overflow=ft.TextOverflow.ELLIPSIS, 
                        ),
                        expand=True, text_align=ft.TextAlign.CENTER,
                        content_padding=ft.Padding.all(0),
                        on_blur=lambda e: self.update_data(**{'title': e.control.value}), 
                        dense=True, border_radius=4,
                        border_color=ft.Colors.TRANSPARENT,
                        focused_border_color=ft.Colors.PRIMARY,
                        multiline=True,
                    ), width=PLOTLINE_PADDING * 2
                ),
                highlight_container2 := ft.Container(
                    cv.Canvas(
                        width=10, opacity=.7,
                        expand=True,   
                        content=ft.GestureDetector(
                            on_enter=highlight,
                            on_exit=stop_highlight,
                            on_pan_end=lambda: self.update_data(**{'position': (self.left, None)}),
                            on_pan_update=self.move_marker,
                            expand=True,
                            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
                            #on_secondary_tap=lambda _: self.widget.story.open_menu(self.get_menu_options()),
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
            ]        

    async def hide_sidebar(self, e=None): 
        await super().hide_sidebar(e)
        self.showing_info = False

    # Called when right clicking our controls for either plotline or an arc
    def get_new_event_menu_options(self) -> list[ft.Control]:

        return [
            MenuOptionStyle(
                content=ft.SubmenuButton(
                    ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY), 
                            ft.Text("New", weight=ft.FontWeight.BOLD, expand=True),
                            ft.Icon(ft.Icons.ARROW_RIGHT),
                        ], expand=True),
                        padding=ft.Padding.all(0), 
                        shape=ft.RoundedRectangleBorder(radius=4),
                        
                    ),
                    [
                        ft.MenuItemButton(      # Documents
                            "Plot Point", leading=ft.Icon(ft.Icons.LOCATION_ON_OUTLINED, ft.Colors.PRIMARY), 
                            on_click=self.create_plot_point, 
                            close_on_click=True,
                            tooltip="Mark important, short term events as plot points in your story",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        ), 
                        
                        ft.MenuItemButton(
                            "Arc", leading=ft.Icon(ft.Icons.SHOW_CHART_OUTLINED, ft.Colors.PRIMARY),
                            on_click=self.create_arc,
                            close_on_click=True,
                            tooltip="Create extented events in your story as arcs with set start and end points",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        ),
                        ft.MenuItemButton(
                            "Marker", leading=ft.Icon(ft.Icons.FLAG_OUTLINED, ft.Colors.PRIMARY),
                            on_click=self.create_marker, 
                            close_on_click=True,
                            tooltip="Create simple markers on the plotline for events or notes to help visualize the flow of your story",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        )
                    ],
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                ),
                no_padding=True, no_effects=True 
            ),   
            MenuOptionStyle(
                ft.MenuItemButton(
                    "Show Info", leading=ft.Icon(ft.Icons.INFO_OUTLINE, ft.Colors.PRIMARY),
                    on_click=self.show_info, 
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    tooltip="Show this map's info in the sidebar",
                ),
                no_effects=True, no_padding=True
            )
        ]

    # Simple highlight and stop highlight functions
    def highlight_plotline_canvas(self):
        self.plotline_highlight_container.shadow = ft.BoxShadow(1, 1, ft.Colors.with_opacity(0.25, self.data.get('color', ft.Colors.PRIMARY)))
        self.plotline_canvas.content.mouse_cursor = ft.MouseCursor.CLICK
        self.plotline_highlight_container.update()
        self.plotline_canvas.update()
    def stop_highlight_plotline_canvas(self):
        self.plotline_highlight_container.shadow = None
        self.plotline_canvas.content.mouse_cursor = None
        self.plotline_highlight_container.update()
        self.plotline_canvas.update()

    # Called when hovering over our plotline on the canvas
    async def hover_plotline_canvas(self, e: ft.PointerEvent):
        ''' Sets our coordinated for opening the menu when right clicking and updates our alignment we want to pass in '''

        # Determine if centered over plotline to highlight and open menus
        def mouse_centered_vertically(e: ft.PointerEvent) -> bool:
            if abs(e.local_position.y - (PLOTLINE_HEIGHT / 2)) <= 25:
                return True
            return False
        def mouse_centered_horizontally(e: ft.PointerEvent) -> bool:
            if PLOTLINE_WIDTH - e.local_position.x >= PLOTLINE_PADDING and e.local_position.x >= PLOTLINE_PADDING:
                return True
            return False
            
        super().set_mouse_coords(e) # Set coords for menus

        self.position = (e.local_position.x, None)  # Save our position for opening the menu when right clicking

        # Check if we're over the plotline line itself and give visual feedback and allow us to right click 
        if mouse_centered_vertically(e) and mouse_centered_horizontally(e):
            self.highlight_plotline_canvas()
            self.can_open_menu = True
        # If not, disable right clicking and remove visual feedback
        else:
            self.stop_highlight_plotline_canvas()
            self.can_open_menu = False

    # Called when clicking to show our info in the sidebar
    async def show_info(self, e=None):

        # Close menu
        await self.story.close_menu()
        if self.showing_info:   # Already showing info, so no need to re-call it
            return
        
        # Re-build header, body, and footer
        self.sidebar_header.controls = self.create_sidebar_header_ctrls()
        self.sidebar_body.controls = self.create_sidebar_body_ctrls()  
        self.sidebar_footer.controls = [self.description_tf]
        self.visible_mw_id = ""     # Reset our state for tracking visible mw

        # Applies the update
        if not await self.show_sidebar():   # If already showing, just update the sidebar
            self.sidebar.update()
        self.showing_info = True

    # Called when right clicking our plotline on the canvas
    async def open_menu(self, e: ft.PointerEvent=None):
        ''' Opens our menu for the options of our related plotline '''
        if self.can_open_menu:
            self.story.open_menu(self.get_new_event_menu_options())
            self.locked_position = self.position


    async def create_plot_point(self, e: ft.Event=None):
        ''' Creates plot point in data, control and control on event stack'''
        await self.story.close_menu()

    async def create_arc(self, e: ft.Event=None):
        ''' Creates an arc in data, control and control on event stack'''
        await self.story.close_menu()

    # Creates a marker in data and a control on the event stack. Has no info for sidebar
    async def create_marker(self):
        await self.story.close_menu()
        new_marker = self.PlotlineMarker(widget=self, is_new=True)

        # Update our data, add it to the events stack, and show it in the sidebar
        self.update_data(**{'markers': {new_marker.data.get('id', ''): new_marker.data}})
        self.marker_stack.controls.append(new_marker)
        self.marker_stack.update()

    def create_sidebar_body_ctrls(self) -> list[ft.Control]:
        
        
        return [
                
                ft.Divider(),
                self.sidebar_notes_label,
                self.sidebar_notes_column,
            
        ]  


    # Called for any size changes to our plotline canvas
    def draw_plotline_canvas(self):
        ''' Redraws our plotline on the canvas when it is resized. Does it on startup as well '''
               
        # Draw our plotline on the canvas with its two end markers ------------------------------------------------
        self.plotline_canvas.shapes = [
            cv.Path(
                elements=[
                    # Left vertical end marker
                    cv.Path.MoveTo(PLOTLINE_PADDING, PLOTLINE_HEIGHT // 2 + (PLOTLINE_PADDING / 2)),
                    cv.Path.LineTo(PLOTLINE_PADDING, PLOTLINE_HEIGHT // 2 - (PLOTLINE_PADDING / 2)),

                    # Horizontal line
                    cv.Path.MoveTo(PLOTLINE_PADDING, PLOTLINE_HEIGHT // 2),
                    cv.Path.LineTo(PLOTLINE_WIDTH - PLOTLINE_PADDING, PLOTLINE_HEIGHT // 2),

                    # Right vertical end marker
                    cv.Path.MoveTo(PLOTLINE_WIDTH - PLOTLINE_PADDING, PLOTLINE_HEIGHT // 2 + (PLOTLINE_PADDING / 2)),
                    cv.Path.LineTo(PLOTLINE_WIDTH - PLOTLINE_PADDING, PLOTLINE_HEIGHT // 2 - (PLOTLINE_PADDING / 2)),
                ],
                paint=ft.Paint(stroke_width=4, style="stroke", color=f"{self.data.get('color', "primary")},.7")
            ),
        ]

        # Draw our divisions on the plotline -----------------------------------------------------------------
        divisions = self.data.get('divisions', [])
        num_divisions = len(divisions)  # Total number of divisions

        # Calculate spacing between divisions within the padded bounds
        division_spacing = (PLOTLINE_WIDTH - (PLOTLINE_PADDING * 2)) / (num_divisions + 1) if num_divisions > 0 else 0


        # Create a path for our divisions
        divisions_path = cv.Path(
            elements=[],
            paint=ft.Paint(stroke_width=2, style="stroke", color=f"{self.data.get('color', "primary")},.7")
        )

        # Go through our number of divisions and add markers to the path
        for i in range(num_divisions):

            # Add the vertical marker for each label, offset from the left padding
            x = PLOTLINE_PADDING + (i + 1) * division_spacing
            divisions_path.elements.append(cv.Path.MoveTo(x, PLOTLINE_HEIGHT // 2 + 10))
            divisions_path.elements.append(cv.Path.LineTo(x, PLOTLINE_HEIGHT // 2 - 10))  

            # Add the text label for each division
            if not self.data.get('hide_division_labels', False):
                self.plotline_canvas.shapes.append(
                    cv.Text(
                        x, PLOTLINE_HEIGHT // 2 - PLOTLINE_PADDING,
                        str(divisions[i]), 
                        ft.TextStyle(14, weight=ft.FontWeight.BOLD),
                        alignment=ft.Alignment.CENTER
                    )
                )
            
        # Add our divisions path to the canvas
        self.plotline_canvas.shapes.append(divisions_path)

        # Add our plotline ends labels ---------------------------------------------------------------------------
        left_label = str(self.data.get('left_label', '0'))
        left_label = left_label.split('.', 1)[0] if '.' in left_label else left_label
        right_label = str(self.data.get('right_label', '10'))
        right_label = right_label.split('.', 1)[0] if '.' in right_label else right_label
        time_label = str(self.data.get('time_label', 'years')).capitalize()

        # Set the text width, and align it in center, make sure it wraps
        self.plotline_canvas.shapes.append(cv.Text(
            PLOTLINE_PADDING, PLOTLINE_HEIGHT // 2 - 60, left_label, 
            ft.TextStyle(18, weight=ft.FontWeight.BOLD), alignment=ft.Alignment.CENTER,
            max_width=50,   # Prevent overflow left
            text_align=ft.TextAlign.CENTER, 
        ))
        self.plotline_canvas.shapes.append(cv.Text(
            PLOTLINE_WIDTH - PLOTLINE_PADDING, PLOTLINE_HEIGHT // 2 - 60, right_label, 
            ft.TextStyle(18, weight=ft.FontWeight.BOLD), alignment=ft.Alignment.CENTER,
            text_align=ft.TextAlign.CENTER, max_width=50,   # Prevent overflow right
        ))
        self.plotline_canvas.shapes.append(cv.Text(
            PLOTLINE_WIDTH // 2, PLOTLINE_HEIGHT - 50, time_label, 
            ft.TextStyle(24, weight=ft.FontWeight.BOLD), alignment=ft.Alignment.CENTER,
            text_align=ft.TextAlign.CENTER
        ))

                     
    def build(self):
        super().build()

        # When clicking our canvas. If we're in center vertically and not showing sidebar, show sidebar
        async def may_show_sidebar(e: ft.PointerEvent):
            if self.can_open_menu:
                await self.show_sidebar()
            #print("Open menu")
            
        # Our canvas that 
        self.plotline_canvas = cv.Canvas(
            content=ft.GestureDetector(
                expand=True, 
                on_secondary_tap=self.open_menu,
                on_hover=self.hover_plotline_canvas,
                #on_exit=self._exit_canvas,
                on_tap=may_show_sidebar,
                hover_interval=20,
            ),
            width=PLOTLINE_WIDTH, height=PLOTLINE_HEIGHT,
        )
        self.draw_plotline_canvas()

        self.plotline_highlight_container = ft.Container(width=PLOTLINE_WIDTH, height=50, shadow=None, ignore_interactions=True, margin=ft.Margin.symmetric(horizontal=PLOTLINE_PADDING))

        self.arc_stack = ft.Stack([], expand=True, alignment=ft.Alignment(0, 0), width=PLOTLINE_WIDTH, height=PLOTLINE_HEIGHT,)
        self.marker_stack = ft.Stack([], expand=True, alignment=ft.Alignment(0, 0), width=PLOTLINE_WIDTH, height=PLOTLINE_HEIGHT,)
        self.plot_point_stack = ft.Stack([], expand=True, alignment=ft.Alignment(0, 0), width=PLOTLINE_WIDTH, height=PLOTLINE_HEIGHT,)
 
        # Sort our arcs so the bigger ones are in back and smaller on top
        arcs_data_list = []
        markers_data_list = []
        plot_points_data_list = []

        # Go through our data and organize it
        for mw in self.data.get('mini_widgets_data', {}).values():
            if mw.get('tag', '') == "arc":
                arcs_data_list.append(mw)
            
            else:
                plot_points_data_list.append(mw)
        for marker in self.data.get('markers', {}).values():
            markers_data_list.append(marker)

        # Sort arcs so biggest is in the back
        arcs_data_list.sort(key=lambda item: item[1].data.get('left', 0) + item[1].data.get('right', 0))

        # Add all our controls to the right stack
        for arc_data in arcs_data_list:
            self.arc_stack.controls.append(PlotlineArc())

        # Add markers next since they are next biggest
        for marker_data in markers_data_list:    
            self.marker_stack.controls.append(self.PlotlineMarker(self, marker_data))

        # Add plot points last
        for plot_point_data in plot_points_data_list:    
            self.plot_point_stack.controls.append(PlotlinePlotPoint())

        self.sidebar_body.controls = self.create_sidebar_body_ctrls()  
        if self.data.get('show_sidebar', True) == False:
            self.showing_info = False

        

        # Holds our drawing so we can interact with it, zoom, pan, etc.
        interactive_viewer = ft.InteractiveViewer(
            content=ft.Stack([
                ft.Container(
                    image=ft.DecorationImage("flow_chart_background.png", repeat=ft.ImageRepeat.REPEAT),
                    width=PLOTLINE_WIDTH, height=PLOTLINE_HEIGHT,
                ),
                self.plotline_canvas,
                self.plotline_highlight_container,
                self.arc_stack,
                self.marker_stack,
                self.plot_point_stack
            ], width=PLOTLINE_WIDTH, height=PLOTLINE_HEIGHT, alignment=ft.Alignment.CENTER),
            constrained=False, expand=True,
            scale_factor=800, boundary_margin=1500,
            min_scale=0.02, max_scale=3.0,
        )

        self.content = ft.Stack([
            interactive_viewer,
            ft.Row(
                [self.toggle_sidebar_visibility_button, self.sidebar], 
                spacing=0, expand=True, alignment=ft.MainAxisAlignment.END, 
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )
        ], expand=True, alignment=ft.Alignment.CENTER_RIGHT)







        