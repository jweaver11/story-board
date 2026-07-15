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
from models.mini_widgets.plotline_arc import Arc
from models.mini_widgets.plotline_marker import PlotlineMarker
import flet.canvas as cv
from models.app import app
import asyncio 


class Plotline(Widget):

    # Constructor
    def __init__(self, title: str, directory_path: str, story: Story, data: dict=None, is_new: bool = False):
        
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
                
                'show_sidebar': True,   # Whether to show the info column on the side of our charts or not. 

                # Data in our info_display
                'Time Label': "Years",                          # Label for the time axis (any str they want)
                'Left Label': "0",                              # Start label
                'Right Label': "10",                            # Start and end date of the branch, for plotline view
                'Divisions': ["1", "2", "3", "4", "5", "6", "7", "8", "9"],    # List len is the num of divisions, and each value is its label
                'hide_division_labels': bool(),  
                
                # Holds our data for all markers, plot points, and arcs
                'mini_widgets_data': {     
                    #'id': {data}
                }
            },
        ) 
                
        # Declare dicts of our data types   
        self.arcs: dict = {}       
        self.plot_points: dict = {} 
        self.markers: dict = {}
        self.information_display: ft.Container = None
        
        # State elements
        self.x_alignment: float = 0.00              # Alignment to pass into new plot points and arcs
        self.left_position: int = 0                 # Absolute left position on plotline for new markers, plotpoints, and arcs
        self.plotline_width: int = int()            # Width of our plotline canvas
        self.plotline_height: int = int()           # Height of our plotline canvas
        self.show_hover_effects: bool = False   # If we should show hover effects of our plotline. Plot points and markers turn these off when hovering over them
        self.needs_redraw = False           # Used to track if we need to redraw canvas after a resize
        self.skip_first_resize = True

        # Our plotline canvas that draws our plotline line and markers
        self.plotline_canvas: cv.Canvas     # Canvas used to just draw our plotline line and markers
        self.event_stack: ft.Stack          # Stack that holds our markers, plot points, and arcs
    

    # Called when right clicking our controls for either plotline or an arc
    def get_plotline_menu_options(self) -> list[ft.Control]:

        return [
            MenuOptionStyle(
                content=ft.SubmenuButton(
                    ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, self.data.get('color', "primary")), 
                            ft.Text("New", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Icon(ft.Icons.ARROW_RIGHT),
                        ], expand=True),
                        padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(6), shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                    [
                        ft.MenuItemButton(
                            "Plot Point", leading=ft.Icon(ft.Icons.LOCATION_ON_OUTLINED, self.data.get('color', "primary")),
                            #on_click=self.new_item_clicked, 
                            tooltip="Mark important, short term events as plot points in your story",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ),
                        ft.MenuItemButton(
                            "Arc", leading=ft.Icon(ft.Icons.SHOW_CHART_OUTLINED, self.data.get('color', "primary")),
                            #on_click=self.new_item_clicked,
                            tooltip="Create extented events in your story as arcs with set start and end points",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ),
                        ft.MenuItemButton(
                            "Marker", leading=ft.Icon(ft.Icons.FLAG_OUTLINED, self.data.get('color', "primary")),
                            on_click=self.create_marker, 
                            tooltip="Create simple markers on the plotline for events or notes to help visualize the flow of your story",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        )
                    ],
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                ),
                no_padding=True, no_effects=True 
            ),   
        ]
    

    # Called when hovering over our plotline on the canvas
    async def _hover_plotline_canvas(self, e: ft.PointerEvent):
        ''' Sets our coordinated for opening the menu when right clicking and updates our alignment we want to pass in '''

        

        if self.story.workspace.is_resizing:    # If we're resizing just ignore this call
            return
        
        

        # Set coordinates for menu
        self.story.mouse_x = e.global_position.x
        self.story.mouse_y = e.global_position.y

        self.left_position = int(e.local_position.x)

        # Calculate and set our x alignment
        w = max(int(self.plotline_width or 0), 1)
        x = float(e.local_position.x)
        raw = (2.0 * x / w) - 1.0
        raw = max(-1.0, min(1.0, raw))
        self.x_alignment = round(raw, 2)    # Save new x_alignment


        # Check if we're over the plotline line itself and give visual feedback and allow us to right click 
        if abs(e.local_position.y - (self.plotline_height / 2)) <= 25:
            

            # Long horizontal timeline
            self.plotline_canvas.shapes[0].paint = ft.Paint(stroke_width=4, style="stroke", color=f"{self.data.get('color', 'primary')},1.0")

            # Divisions on the timeline
            self.plotline_canvas.shapes[len(self.information_display.data.get('Divisions', [])) + 1].paint = ft.Paint(stroke_width=2, style="stroke", color=f"{self.data.get('color', 'primary')},1.0")
            self.plotline_canvas.content.mouse_cursor = ft.MouseCursor.CLICK      # Change cursor to pointer

            try:
                self.plotline_canvas.update()
            except Exception as _:
                pass


        # If not, disable right clicking and remove visual feedback
        else:
            self.plotline_canvas.shapes[0].paint = ft.Paint(stroke_width=4, style="stroke", color=f"{self.data.get('color', 'primary')},.7")
            self.plotline_canvas.shapes[len(self.information_display.data.get('Divisions', [])) + 1].paint = ft.Paint(stroke_width=2, style="stroke", color=f"{self.data.get('color', 'primary')},.7")
            self.plotline_canvas.content.mouse_cursor = None

            try:
                self.plotline_canvas.update()
            except Exception as _:
                pass

    async def _exit_canvas(self, e=None):
        ''' Called when exiting our plotline canvas '''
        self.plotline_canvas.shapes[0].paint = ft.Paint(stroke_width=4, style="stroke", color=f"{self.data.get('color', 'primary')},.7")
        self.plotline_canvas.shapes[len(self.information_display.data.get('Divisions', [])) + 1].paint = ft.Paint(stroke_width=2, style="stroke", color=f"{self.data.get('color', 'primary')},.7")
        self.plotline_canvas.content.mouse_cursor = None

        try:
            self.plotline_canvas.update()
        except Exception as _:
            pass

    # Checks if we are within 25 pixels of the vertical center of the plotline
    def mouse_centered_vertically_on_plotline_canvas(self, e: ft.PointerEvent) -> bool:
        # TODO: Calc mouse position. If within 50 pixels of half our height, show sidebar with info display as content
        pass


    # Called when right clicking our plotline on the canvas
    async def open_menu(self, e: ft.PointerEvent):
        ''' Opens our menu for the options of our related plotline '''
        if self.mouse_centered_vertically_on_plotline_canvas(e):
            self.story.open_menu(self.get_plotline_menu_options())

        
    
        

    async def create_plot_point(self, e: ft.Event=None):
        ''' Creates plot point in data, control and control on event stack'''

    async def create_arc(self, e: ft.Event=None):
        ''' Creates an arc in data, control and control on event stack'''

    # Creates a marker in data and a control on the event stack. Has no info for sidebar
    async def create_marker(self):
        new_marker = PlotlineMarker(widget=self, data={'title': "New Marker"}, is_new=True)

        # Update our data, add it to the events stack, and show it in the sidebar
        self.update_data(**{'mini_widgets_data': {new_marker.data.get('id', ''): new_marker.data}})
        self.event_stack.controls.append(new_marker)
        await new_marker.show_mini_widget()

        
    def create_plot_point_event_stack_ctrl(self, pp_data: dict) -> ft.Control:
        ''' Creates the event stack control for a given plot point '''
        return

    # Shows either our plotline info, a plot point, or an arc in the sidebar
    def show_mini_widget(self, mw_data: dict=None):
        ''' Shows the mini widget with the given ID when clicking on it in the plotline '''
        # if no data passed in, show our sidebar ctrl
        return
    
    def load_mini_widget_sidebar_ctrl(self, mw_data: dict):
        ''' Loads the sidebar control for a given mini widget '''
        # TODO: Reload mini widget should just return the content needed for this mini widget sidebar
        # Have parent widget also have notes label, section, button all in row for info displays
        # THE CLASS SHOULD INSTEAD BE BASED ON PLOTLINE_CONTROL (RENAME EVENT_STACK_CONTROL), AND CLICKING IT SHOULD CALL RELOAD MINI WIDGET
        # Infos should not be their own mini widget, and should instead be in parent widget class
        return
    
    async def start_move_event_stack_control(self, e: ft.DragStartEvent):
        ''' Called when starting to move an event stack control '''
        return
    
    async def move_event_stack_control(self, e: ft.DragUpdateEvent):
        ''' Called when moving an event stack control '''
        return
    
    async def end_move_event_stack_control(self, e: ft.DragEndEvent):
        ''' Called when ending the move of an event stack control '''
        return
    
    # Deletes an event from data, stack, and sidebar if its active
    async def delete_event(e: ft.Event):
        # Need id
        pass


    # Called for any size changes to our plotline canvas
    async def redraw_plotline_canvas(self, e: ft.EventHandler[cv.CanvasResizeEvent]):
        ''' Redraws our plotline on the canvas when it is resized. Does it on startup as well '''
        #return
        print(e)
        
        return
               
        # Draw our plotline on the canvas with its two end markers ------------------------------------------------
        self.plotline_canvas.shapes = [
            cv.Path(
                elements=[
                    # Left vertical end marker
                    cv.Path.MoveTo(25, self.plotline_height // 2 + 25),
                    cv.Path.LineTo(25, self.plotline_height // 2 - 25),

                    # Horizontal line
                    cv.Path.MoveTo(25, self.plotline_height // 2),
                    cv.Path.LineTo(self.plotline_width, self.plotline_height // 2),

                    # Right vertical end marker
                    cv.Path.MoveTo(self.plotline_width, self.plotline_height // 2 + 25),
                    cv.Path.LineTo(self.plotline_width, self.plotline_height // 2 - 25),
                ],
                paint=ft.Paint(stroke_width=4, style="stroke", color=f"{self.data.get('color', "primary")},.7")
            ),
        ]

        # Draw our divisions on the plotline -----------------------------------------------------------------
        num_divisions = len(self.information_display.data.get('Divisions', []))  # Total number of divisions
        div_width = (self.plotline_width) / (num_divisions + 1) if num_divisions > 0 else 0   # Width between each division
        division_width = (self.plotline_width - div_width) / num_divisions  if num_divisions > 0 else 0      # Division width starting after first division plus padding

        # Create a path for our divisions
        divisions_path = cv.Path(
            elements=[],
            paint=ft.Paint(stroke_width=2, style="stroke", color=f"{self.data.get('color', "primary")},.7")
        )

        # Go through our number of divisions and add markers to the path
        for i in range(num_divisions):

            # Add the vertical marker for each label
            x = int(i * division_width) + division_width
            divisions_path.elements.append(cv.Path.MoveTo(x, self.plotline_height // 2 + 10))
            divisions_path.elements.append(cv.Path.LineTo(x, self.plotline_height // 2 - 10))  

            # Add the text label for each division
            if not self.data.get('hide_division_labels', False):
                self.plotline_canvas.shapes.append(
                    cv.Text(
                        x, self.plotline_height // 2 - 25 if app.settings.data.get('division_labels_direction', "top") == "top" else self.plotline_height // 2 + 25,
                        str(self.information_display.data.get('Divisions', ["1", "2", "3", "4", "5", "6", "7", "8", "9"])[i]), 
                        ft.TextStyle(14, weight=ft.FontWeight.BOLD),
                        alignment=ft.Alignment.CENTER
                    )
                )
            
        # Add our divisions path to the canvas
        self.plotline_canvas.shapes.append(divisions_path)


        # Add our plotline ends labels ---------------------------------------------------------------------------
        left_label = str(self.information_display.data.get('Left Label', '0'))
        left_label = left_label.split('.', 1)[0] if '.' in left_label else left_label
        right_label = str(self.information_display.data.get('Right Label', '10'))
        right_label = right_label.split('.', 1)[0] if '.' in right_label else right_label
        time_label = str(self.information_display.data.get('Time Label', 'years')).capitalize()

        # Set the text width, and align it in center, make sure it wraps
        self.plotline_canvas.shapes.append(cv.Text(
            25, self.plotline_height // 2 - 60, left_label, 
            ft.TextStyle(18, weight=ft.FontWeight.BOLD), alignment=ft.Alignment.CENTER,
            max_width=50,   # Prevent overflow left
            text_align=ft.TextAlign.CENTER, 
        ))
        self.plotline_canvas.shapes.append(cv.Text(
            self.plotline_width, self.plotline_height // 2 - 60, right_label, 
            ft.TextStyle(18, weight=ft.FontWeight.BOLD), alignment=ft.Alignment.CENTER,
            text_align=ft.TextAlign.CENTER, max_width=50,   # Prevent overflow right
        ))
        self.plotline_canvas.shapes.append(cv.Text(
            self.plotline_width // 2, self.plotline_height - 50, time_label, 
            ft.TextStyle(24, weight=ft.FontWeight.BOLD), alignment=ft.Alignment.CENTER,
            text_align=ft.TextAlign.CENTER
        ))

        
        

        self.plotline_canvas.update()

    # Re-aligns the event controls
    async def align_event_controls(self):
        # Add our plot points labels above or below their dot on the plotline ------------------------------------------------
        line_direction = "bottom"  # Line direction either going above or below the plotline that flips evert plotline
        line_height = "small"    # Line height that cycles between small, medium, and large after each plot point

        sorted_plot_points = dict(sorted(self.plot_points.items(), key=lambda item: item[1].data.get('x_alignment', 0.0)))

        for plot_point in sorted_plot_points.values():
            # If we're hiding all plot points, skip drawing them
            if self.data.get('hide_all_plot_points', False):
                break
            
            if self.data.get('show_all_plot_points', False) or plot_point.data.get('is_shown_on_widget', False):
                # Calculate x position
                x_alignment = max(-1.0, min(1.0, float(plot_point.data.get('x_alignment', 0.0))))
                
                
                new_x_pos = int(((x_alignment + 1) / 2) * (self.plotline_width - 10))  
                plot_point.plotline_control.left = new_x_pos
                plot_point.plotline_control.top = self.plotline_height // 2 - 12     # Make sure plot point is in middle of the line

                x_pos = new_x_pos + 28

                if line_direction == "top":
                    moveTo = cv.Path.MoveTo(x_pos, self.plotline_height // 2 - 20)
                    # Set our line height
                    match line_height:
                        case "small":
                            y_pos = int(self.plotline_height // 2) - 50
                        case "medium":
                            y_pos = int(self.plotline_height // 2) - 100
                        case "large":
                            y_pos = int(self.plotline_height // 2) - 150
                        case _:
                            y_pos = int(self.plotline_height // 2) - 150

                    line_direction = "bottom"
                    
                else:
                    moveTo = cv.Path.MoveTo(x_pos, self.plotline_height // 2 + 20)
                    match line_height:
                        case "small":
                            y_pos = int(self.plotline_height - (self.plotline_height // 2) + 50)
                            line_height = "medium"
                        case "medium":
                            y_pos = int(self.plotline_height - (self.plotline_height // 2) + 100)
                            line_height = "large"
                        case "large":
                            y_pos = int(self.plotline_height - (self.plotline_height // 2) + 150)
                            line_height = "small"
                        case _:
                            y_pos = int(self.plotline_height - (self.plotline_height // 2) + 150)

                    line_direction = "bottom"

                label_path = cv.Path(
                    elements=[
                        moveTo,
                        cv.Path.LineTo(x_pos, y_pos),
                    ],
                    paint=ft.Paint(stroke_width=2, style="stroke", color=plot_point.data.get('color', self.data.get('color', "primary")))
                )

                # Add the text label for the plot point
                self.plotline_canvas.shapes.append(label_path)

                self.plotline_canvas.shapes.append(
                    cv.Text(
                        x_pos, 
                        y_pos + 20 if line_direction == "bottom" else y_pos - 20,
                        plot_point.title, 
                        ft.TextStyle(14, weight=ft.FontWeight.BOLD, color=plot_point.data.get('color', "secondary"), overflow=ft.TextOverflow.ELLIPSIS),
                        alignment=ft.Alignment.CENTER,
                        max_width=100,
                        text_align=ft.TextAlign.CENTER
                    )
                )

                try:
                    plot_point.plotline_control.update()
                except Exception as _:
                    pass


        # Add our markers on the plotline ------------------------------------------------
        for marker in self.markers.values():
            # If we're hiding all markers, skip drawing them
            if self.data.get('hide_all_markers', False):
                break

            if marker.data.get('is_shown_on_widget', False):

                # Since markers are positioned absolutely, we just need to update their left position based on their x_alignment value
                x_alignment = max(-1.0, min(1.0, float(marker.data.get('x_alignment', 0.0))))
                
                # Calculate x position and set the control to have it
                new_x_pos = int(((x_alignment + 1) / 2) * (self.plotline_width - 10))
                marker.plotline_control.left = new_x_pos  

                # Set how high up we want to go (Up to 80% height)
                y_pos = int(self.plotline_height // 4)

                # Guard against the header
                if y_pos < 70: 
                    y_pos = 70

                marker_height = self.plotline_height // 2 
                marker.plotline_control.height = marker_height
                marker.plotline_control.top = y_pos         
                #marker.plotline_control.bottom = self.plotline_height - y_pos     
    
                # Re-paint its shapes (dashed line) if needed (Only first load)
                marker.plotline_control.content.content.shapes = [
                    cv.Line(
                        3, 0, 3, (marker_height), 
                        paint=ft.Paint(
                            marker.data.get('color', "secondary"),
                            stroke_dash_pattern=[10, 10],
                            stroke_width=2
                        ) 
                    )
                ]
            
                label_path = cv.Text(
                    new_x_pos + 18, y_pos - 20, 
                    marker.title,
                    ft.TextStyle(14, weight=ft.FontWeight.BOLD, color=marker.data.get('color', "secondary"), overflow=ft.TextOverflow.ELLIPSIS),
                    alignment=ft.Alignment.CENTER,
                    max_width=100,
                    text_align=ft.TextAlign.CENTER
                )
            
                
                # Add the text label for the plot point
                self.plotline_canvas.shapes.append(label_path)

                try:
                    marker.plotline_control.update()
                except Exception as _:
                    pass

        # Go through our arcs and update their size --------------------------------------------------        
        for arc in self.arcs.values():

            if self.data.get('hide_all_arcs', False):
                break

            if arc.data.get('is_shown_on_widget', False):
                # Make sure heights and widths r updated
                arc.plotline_control.bottom = self.plotline_height // 2       # Make sure plot point is in middle of the line

                width = self.plotline_width - arc.data.get('left', 0) - arc.data.get('right', 0)
                
                lr = arc.data.get('left_ratio', 0)
                rr = arc.data.get('right_ratio', 0)            

                new_left = int(lr * self.plotline_width)
                new_right = int(rr * self.plotline_width)

                new_width = self.plotline_width - new_left - new_right
                if new_width < 100:
                    new_width = 100

                height = new_width * 0.5

                if height >= self.plotline_height / 2 -70:
                    height = self.plotline_height / 2 -70
                #width_ratio = width / max(self.plotline_width, 1)

                #height = (self.plotline_height / 2) * (width_ratio) - 40
                if height < 50:
                    height = 50

                arc.data['left'] = new_left
                arc.data['right'] = new_right
                arc.data['width'] = new_width
                arc.plotline_control.height = int(height) 

                arc.plotline_control.left = new_left   
                arc.plotline_control.right = new_right
                arc.plotline_control.bottom = self.plotline_height / 2

                try:
                    arc.plotline_control.update()
                except Exception as _:
                    pass
        return

                     
    def build(self):
        super().build()

    # Called when we need to rebuild out plotline UI
    def reload_widget(self):

        # When clicking our canvas. If we're in center vertically and not showing sidebar, show sidebar
        async def may_show_sidebar(e: ft.PointerEvent):
            if self.mouse_centered_vertically_on_plotline_canvas(e):
                if not self.data.get('show_sidebar', False):
                    await self.show_sidebar()

            
            
            
        # Our canvas that 
        self.plotline_canvas = cv.Canvas(
            resize_interval=500, 
            expand=True, 
            on_resize=self.redraw_plotline_canvas,
            content=ft.GestureDetector(
                expand=True, 
                on_secondary_tap=self.open_menu,
                on_hover=self._hover_plotline_canvas,
                on_exit=self._exit_canvas,
                on_tap=may_show_sidebar,
                hover_interval=20,
            )
        )

        
        # Create a stack so we can sit our plotpoints and arcs on our plotline
        self.event_stack = ft.Stack(
            expand=True, 
            alignment=ft.Alignment(0, 0),
            clip_behavior=ft.ClipBehavior.NONE,
            on_size_change=self.align_event_controls,
            controls=[
                ft.Container(
                    self.plotline_canvas, #ft.Padding.only(left=16, right=16), 
                    expand=True, clip_behavior=ft.ClipBehavior.NONE,
                )      # Add our canvas which has our visual plotline
            ]
        ) 
 
        # Sort our arcs so the bigger ones are in back and smaller on top
        sorted_arcs = dict(sorted(self.arcs.items(), key=lambda item: item[1].data.get('left', 0) + item[1].data.get('right', 0)))

        # Handler for plotline resize events
        for arc in sorted_arcs.values():
            if self.data.get('show_all_arcs', False) or arc.data.get('is_shown_on_widget', False):
                # Add the arc control to the plotline stack
                self.event_stack.controls.append(arc.plotline_control)

        # Add our plot points to the plotline (They position themselves)
        for plot_point in self.plot_points.values():    
            if self.data.get('show_all_plot_points', False) or plot_point.data.get('is_shown_on_widget', False):
                self.event_stack.controls.append(plot_point.plotline_control)

        # Add our markers to the plotline (They position themselves)
        for marker in self.markers.values():    
            if self.data.get('show_all_markers', False) or marker.data.get('is_shown_on_widget', False):
                self.event_stack.controls.append(marker.plotline_control)

        # Holds our drawing so we can interact with it, zoom, pan, etc.
        interactive_viewer = ft.InteractiveViewer(
            content=self.event_stack,
            expand=3, 
            constrained=False,
            scale_factor=500, boundary_margin=200,
            min_scale=0.02, max_scale=3.0,
        )
        self.body_container.content = ft.Stack([
            ft.Row([interactive_viewer, self.sidebar], spacing=0, expand=True),
            self.show_sidebar_button, 
        ], expand=True, alignment=ft.Alignment.CENTER_RIGHT)

        print("Sidebar visible:", self.sidebar.visible)
        print("Sidebar button visible: ", self.show_sidebar_button.visible)

        self._render_widget()







        