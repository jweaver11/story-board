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
from models.mini_widgets.plotlines.arc import Arc
from utils.verify_data import verify_data
import flet.canvas as cv
from models.app import app
import asyncio


class Plotline(Widget):

    # Constructor. Requires title, owner widget, page reference, and optional data dictionary
    def __init__(self, title: str, page: ft.Page, directory_path: str, story: Story, data: dict=None):
        
        # Parent constructor
        super().__init__(
            title = title,  
            page = page,   
            directory_path = directory_path, 
            story = story,     
            data = data,  
        ) 


        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {
                'tag': "plotline",
                'color': app.settings.data.get('default_plotline_color'),

                'filters': {   
                    'show_timeskips': True,
                    'show_plot_points': True,
                    'show_arcs': True,
                },        
                'information_display_visibility': True,
                    
                'time_label': "years",                          # Label for the time axis (any str they want)
                'left_label': "0",                          # Start label
                'right_label': "10",                          # Start and end date of the branch, for plotline view
                'divisions': ["1", "2", "3", "4", "5", "6", "7", "8", "9"],    # List len is the num of divisions, and each value is its label
                'hide_division_labels': bool,              # If the division labels are hidden on the plotline
                'division_labels_direction': "top",               # If the division labels are on top of the plotline instead of below

                # Our rail dropdown states
                'dropdown_is_expanded': True,               # If the branch dropdown is expanded on the rail
                'plot_points_dropdown_expanded': True,      # If the plotpoints section is expanded
                'arcs_dropdown_expanded': True,             # If the arcs section is expanded

                # Filter dropdown states
                'arcs_filter_dropdown_expanded': bool,        # If the arcs filter dropdown is expanded
                'plot_points_filter_dropdown_expanded': bool, # If the plot points filter dropdown is
                'show_all_plot_points': True,              # If all plot points are shown regardless of individual settings
                'show_all_arcs': True,                     # If all arcs are shown regardless of individual settings
                

                'plot_points': dict,                        # Dict of plot points in this branch
                'arcs': dict,                               # Dict of arcs in this branch
                'connections': dict,                        # Connect points, arcs, branch, etc.???
                'rail_dropdown_is_expanded': True,          # If the rail dropdown is expanded  
                'description': str,
                'events': list,                             # Step by step of plot events through the arc. Call plot point??
                'involved_characters': list,
                'related_locations': list,
                'related_items': list,

                'left_edge_label': float,                   # Label for the left edge of the plotline
                'right_edge_label': float,                  # Label for the right edge of the plotline
            },
        ) 

        

        # Declare and create our information display, which is our plotlines mini widget 
        self.information_display: ft.Container = None
        self.create_information_display()
        
        # Declare dicts of our data types   
        self.arcs: dict = {}       
        self.plot_points: dict = {} 
        self.time_skips: dict = {}
        self.connections: dict = {}  # Needed????


        # Loads our three mini widgets into their dicts
        self.load_arcs()
        self.load_plot_points()
        
        # State elements
        self.x_alignment: float = 0.00      # Alignment to pass into new plot points and arcs
        self.plotline_width: int = int()    # Width of our plotline canvas. Just used in calculations, not applied
        self.plotline_height: int = int()   # Height of our plotline canvas Just used in calculations, not applied

        # Our plotline canvas that draws our plotline line and markers
        self.plotline_canvas = cv.Canvas(
            on_resize=self.rebuild_plotline_canvas, resize_interval=20, expand=True, 
            opacity=0.7,
            content=ft.GestureDetector(
                expand=True, on_secondary_tap=self.on_secondary_tap,
                on_exit=self.on_exit, 
                on_hover=self.hover_plotline_canvas,
                on_tap=lambda e: self.information_display.toggle_visibility(value=True),
                hover_interval=10,
            )
        )

        # Dropdown on the rail. We don't use it here, let the rail handle it
        self.plotline_dropdown = None      # 'Plotline_Dropdown'

        # Builds/reloads our plotline UI
        self.reload_widget()

    # Called in the constructor
    def create_information_display(self):
        ''' Creates our plotline information display mini widget '''
        from models.mini_widgets.plotlines.plotline_information_display import PlotlineInformationDisplay
        
        self.information_display = PlotlineInformationDisplay(
            title=self.title,
            owner=self,
            father=self,
            page=self.p,
            key="none",     # Not used, but its required so just whatever works
            data=None,      # It uses our data, so we don't need to give it a copy that we would have to constantly maintain
        )
        # Add to our mini widgets so it shows up in the UI
        self.mini_widgets.append(self.information_display)

    # Called in the constructor
    def load_arcs(self):
        ''' Loads branches from data into self.branches  '''

        # Looks up our branches in our data, then passes in that data to create a live object
        for key, data in self.data['arcs'].items():
            self.arcs[key] = Arc(
                title=key, 
                owner=self, 
                father=self,
                page=self.p, 
                key="arcs",
                data=data
            )
            self.mini_widgets.append(self.arcs[key])  # Branches need to be in the owners mini widgets list to show up in the UI
    
    # Called in the constructor
    def load_plot_points(self):
        ''' Loads plotpoints from data into self.plotpoints  '''
        from models.mini_widgets.plotlines.plot_point import PlotPoint

        # Looks up our plotpoints in our data, then passes in that data to create a live object
        for key, data in self.data['plot_points'].items():
            self.plot_points[key] = PlotPoint(
                title=key, 
                owner=self, 
                father=self,
                page=self.p, 
                key="plot_points", 
                data=data
            )
            self.mini_widgets.append(self.plot_points[key])  # Plot points need to be in the owners mini widgets list to show up in the UI
        
    # Called when creating a new arc
    async def create_arc(self, title: str):
        ''' Creates a new arc inside of our plotline object, and updates the data to match '''
        from models.mini_widgets.plotlines.arc import Arc

        new_arc = Arc(
            title=title, 
            owner=self, 
            father=self,
            page=self.p, 
            key="arcs", 
            x_alignment=self.x_alignment,
            data=None
        )

        # Add our new Arc mini widget object to our arcs dict, and to our owners mini widgets
        self.arcs[new_arc.title] = new_arc
        self.mini_widgets.append(new_arc)
        new_arc.toggle_visibility(value=True)

        # Apply our changes in the UI
        self.story.active_rail.content.reload_rail()
        await self.rebuild_plotline_canvas()
        self.reload_widget()
       
        
    # Called when creating a new plotpoint
    def create_plot_point(self, title: str):
        ''' Creates a new plotpoint inside of our plotline object, and updates the data to match '''
        from models.mini_widgets.plotlines.plot_point import PlotPoint

        new_plot_point = PlotPoint(
            title=title, 
            owner=self, 
            father=self,
            page=self.p, 
            key="plot_points", 
            x_alignment=self.x_alignment,
            data=None
        )
        # Add our new Plot Point mini widget object to our plot_points dict, and to our owners mini widgets
        self.plot_points[new_plot_point.title] = new_plot_point
        self.mini_widgets.append(new_plot_point)
        new_plot_point.toggle_visibility(value=True)

        # Apply our changes in the UI
        self.story.active_rail.content.reload_rail()
        self.reload_widget()


    def delete_plot_point(self, plot_point):
        ''' Deletes a plot point from our plotline '''
        
        # Remove from our dict
        if plot_point.title in self.plot_points:
            self.plot_points.pop(plot_point.title)
            self.data['plot_points'].pop(plot_point.title, None)
            self.save_dict()

        # Apply changes
        self.reload_widget()

    def delete_arc(self, arc):
        ''' Deletes an arc from our plotline '''
        
        # Remove from our dict
        if arc.title in self.arcs:
            self.arcs.pop(arc.title)
            self.data['arcs'].pop(arc.title, None)
            self.save_dict()

        # Apply changes
        self.reload_widget()

    # Called when right clicking our controls for either plotline or an arc
    def get_menu_options(self) -> list[ft.Control]:

        #TODO: Should be New, show information display, renamde, color, delete

        # Color, rename, delete
        return [
             MenuOptionStyle(
                content=ft.PopupMenuButton(
                    content=ft.Row([ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED), ft.Text("New", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD)]),
                    tooltip="New", menu_padding=0,
                    items=[
                        ft.PopupMenuItem(
                            text="Plot Point", icon=ft.Icons.ADD_LOCATION_OUTLINED,
                            on_click=self.new_item_clicked, data="plot_point"
                        ),
                        ft.PopupMenuItem(
                            text="Arc", icon=ft.Icons.CIRCLE_OUTLINED,
                            on_click=self.new_item_clicked, data="arc"
                        ),
                    ]
                ),
            ),
            # Delete button
            MenuOptionStyle(
                on_click=self.rename_clicked,
                content=ft.Row([
                    ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED),
                    ft.Text(
                        "Rename", 
                        weight=ft.FontWeight.BOLD, 
                        color=ft.Colors.ON_SURFACE
                    ), 
                ]),
            ),
            # Color changing popup menu
            MenuOptionStyle(
                content=ft.PopupMenuButton(
                    expand=True,
                    tooltip="",
                    padding=None,
                    content=ft.Row(
                        expand=True,
                        controls=[
                            ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, color=ft.Colors.PRIMARY),
                            ft.Text("Color", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True), 
                        ]
                    ),
                    items=self._get_color_options()
                )
            ),
            # Delete button
            MenuOptionStyle(
                #on_click=lambda e: self._delete_clicked(e),
                content=ft.Row([
                    ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED),
                    ft.Text("Delete", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True),
                ]),
            ),
        ]
    

    # Called when hovering over our plotline on the canvas
    async def hover_plotline_canvas(self, e: ft.HoverEvent):
        ''' Sets our coordinated for opening the menu when right clicking and updates our alignment we want to pass in '''

        # Set coordinates for menu
        self.story.mouse_x = e.global_x
        self.story.mouse_y = e.global_y

        # Calculate and set our x alignment
        w = max(int(self.plotline_width or 0), 1)
        x = float(e.local_x)
        raw = (2.0 * x / w) - 1.0
        raw = max(-1.0, min(1.0, raw))
        self.x_alignment = round(raw, 2)    # Save new x_alignment


        # Check if we're over the plotline line itself and give visual feedback
        if abs(e.local_y - (self.plotline_height / 2)) <= 25:
            self.plotline_canvas.page = self.p      # refresh page reference
            self.plotline_canvas.opacity = 1        # Full opacity to highlight
            self.plotline_canvas.content.mouse_cursor=ft.MouseCursor.CLICK      # Change cursor to pointer
            self.plotline_canvas.update()       # Apply changes
        else:
            self.plotline_canvas.page = self.p
            self.plotline_canvas.opacity = .7
            self.plotline_canvas.content.mouse_cursor=None
            self.plotline_canvas.update()
        
        

    # Called when mouse exits our plotline area
    async def on_exit(self, e: ft.HoverEvent):
        ''' Un-highlights our plotline control for visual feedback '''
        
        self.plotline_canvas.page = self.p
        self.plotline_canvas.opacity = .7
        self.plotline_canvas.update()

    # Called when right clicking our plotline on the canvas
    async def on_secondary_tap(self, e):
        ''' Opens our menu for the options of our related plotline '''

        self.story.open_menu(self.get_menu_options())

    async def new_item_clicked(self, e):
        ''' Called when new plot point or arc is clicked from plotline context menu '''
        
        tag = e.control.data

        if tag is not None:
            if tag == "arc":
                await self.create_arc(f"Arc {len(self.arcs) + 1}")
            elif tag == "plot_point":
                self.create_plot_point(f"Plot Point {len(self.plot_points) + 1}")
        else:
            print("Error: No tag found for new item creation")

        await asyncio.sleep(.3)
        await self.story.close_menu()


    # Called when rename button is clicked
    async def rename_clicked(self, e):
        ''' Makes sure our information display is visible, and focuses the title control for renaming '''

        # Close the menu
        await self.story.close_menu()

        # Make sure our information display is visible
        if not self.information_display.visible:
            self.information_display.toggle_visibility(value=True)

        # Focus the title control for renaming
        self.information_display.title_control.focus()

    # Called for any size changes to our plotline canvas
    async def rebuild_plotline_canvas(self, e: cv.CanvasResizeEvent=None):
        ''' Redraws our plotline on the canvas when it is resized. Does it on startup as well '''

        # Check if we just called this to redraw without an event. If we did, skip the size updates
        if e is None:
            update_arcs = False
    
        else:
            
            # Check if we have a new height. If not, don't update the arcs
            if self.plotline_height == int(e.height):
                update_arcs = False
            else:
                update_arcs = True

            # Update our page reference and size
            self.plotline_canvas.page = self.p
            self.plotline_width = int(e.width)
            self.plotline_height = int(e.height)
        
        # Draw our plotline on the canvas with its two end markers ------------------------------------------------
        self.plotline_canvas.shapes = [
            cv.Path(
                elements=[
                    # Left vertical end marker
                    cv.Path.MoveTo(5, self.plotline_height // 2 + 25),
                    cv.Path.LineTo(5, self.plotline_height // 2 - 25),

                    # Horizontal line
                    cv.Path.MoveTo(5, self.plotline_height // 2),
                    cv.Path.LineTo(self.plotline_width - 5, self.plotline_height // 2),

                    # Right vertical end marker
                    cv.Path.MoveTo(self.plotline_width - 5, self.plotline_height // 2 + 25),
                    cv.Path.LineTo(self.plotline_width - 5, self.plotline_height // 2 - 25),
                ],
                paint=ft.Paint(stroke_width=4, style="stroke", color=self.data.get('color', "primary"))
            ),
        ]

        # Draw our divisions on the plotline -----------------------------------------------------------------
        num_divisions = len(self.data.get('divisions', 9))  # Get number of divisions and the width between each division
        div_width = self.plotline_width / num_divisions if num_divisions > 0 else 0 
        division_width = (self.plotline_width - div_width - 10) / num_divisions if num_divisions > 0 else 0      # Division width starting after first division plus padding

        # Create a path for our divisions
        divisions_path = cv.Path(
            elements=[],
            paint=ft.Paint(stroke_width=2, style="stroke", color=self.data.get('color', "primary"))
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
                        x, self.plotline_height // 2 - 40 if self.data.get('division_labels_direction', "top") == "top" else self.plotline_height // 2 + 40,
                        str(self.data.get('divisions', ["1", "2", "3", "4", "5", "6", "7", "8", "9"])[i]), 
                        ft.TextStyle(14, weight=ft.FontWeight.BOLD),
                        alignment=ft.alignment.center
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
            5, self.plotline_height // 2 - 60, left_label, 
            ft.TextStyle(18, weight=ft.FontWeight.BOLD), alignment=ft.alignment.center,
            max_width=55,   # Prevent overflow left
        ))
        self.plotline_canvas.shapes.append(cv.Text(
            self.plotline_width - 5, self.plotline_height // 2 - 60, right_label, 
            ft.TextStyle(18, weight=ft.FontWeight.BOLD), alignment=ft.alignment.center
        ))
        self.plotline_canvas.shapes.append(cv.Text(
            self.plotline_width // 2, self.plotline_height // 2 + 80, time_label, 
            ft.TextStyle(20, weight=ft.FontWeight.BOLD), alignment=ft.alignment.center
        ))

        
        # Add our plot points labels above or below their dot on the plotline ------------------------------------------------
        line_direction = "top"  # Line direction either going above or below the plotline that flips evert plotline
        line_height = "small"    # Line height that cycles between small, medium, and large after each plot point

        sorted_plot_points = dict(sorted(self.plot_points.items(), key=lambda item: item[1].data.get('x_alignment', 0.0)))

        for plot_point in sorted_plot_points.values():
            if plot_point.data.get('is_shown_on_widget', False):
                # Calculate x position
                x_alignment = max(-1.0, min(1.0, float(plot_point.data.get('x_alignment', 0.0))))
                x_pos = int(((x_alignment + 1.0) / 2.0) * (self.plotline_width - 10)) + 5    # because mapping [-1..1] to [0..W], plus 5px padding

                # Adjust based on offset from the margin the plot points use
                offset_x = 5 * x_alignment
                x_pos = x_pos - offset_x

                if line_direction == "top":
                    moveTo = cv.Path.MoveTo(x_pos, self.plotline_height // 2 - 20)
                    # Set our line height
                    match line_height:
                        case "small":
                            y_pos = int(self.plotline_height // 3)
                        case "medium":
                            y_pos = int(self.plotline_height // 4)
                        case "large":
                            y_pos = int(self.plotline_height // 6)
                        case _:
                            y_pos = int(self.plotline_height // 6)

                    line_direction = "bottom"
                    
                else:
                    moveTo = cv.Path.MoveTo(x_pos, self.plotline_height // 2 + 20)
                    match line_height:
                        case "small":
                            y_pos = int(self.plotline_height - (self.plotline_height // 3))
                            line_height = "medium"
                        case "medium":
                            y_pos = int(self.plotline_height - (self.plotline_height // 4))
                            line_height = "large"
                        case "large":
                            y_pos = int(self.plotline_height - (self.plotline_height // 6))
                            line_height = "small"
                        case _:
                            y_pos = int(self.plotline_height - (self.plotline_height // 6))

                    line_direction = "top"


                
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
                        y_pos - 20 if line_direction == "bottom" else y_pos + 20,
                        plot_point.title, 
                        #" ",
                        ft.TextStyle(14, weight=ft.FontWeight.BOLD, color=plot_point.data.get('color', "secondary"), overflow=ft.TextOverflow.ELLIPSIS),
                        alignment=ft.alignment.center,
                        max_width=100,
                    )
                )

        # Go through our arcs and update their size --------------------------------------------------
        if update_arcs:
            for arc in self.arcs.values():
                # ---- 1) & 2) Reposition + mid expansion via expand ratios (base 1000) ----
                # Clamp defensively (RangeSlider should keep ordering, but keep it safe)
                start_a = max(-1.0, min(1.0, float(arc.data.get('x_alignment_start', -0.2))))
                end_a = max(-1.0, min(1.0, float(arc.data.get('x_alignment_end', 0.2))))
                if end_a < start_a:
                    start_a, end_a = end_a, start_a

                left_ratio = (start_a + 1.0) / 2.0          # [-1..1] -> [0..1]
                right_ratio = (1.0 - end_a) / 2.0           # [-1..1] -> [0..1]

                left_expand = int(left_ratio * 1000)
                right_expand = int(right_ratio * 1000)
                mid_expand = max(0, 1000 - left_expand - right_expand)

                # Update expands in-place
                if arc.spacing_left is not None:
                    arc.spacing_left.expand = left_expand
                if arc.spacing_right is not None:
                    arc.spacing_right.expand = right_expand
                if arc.plotline_arc is not None:
                    arc.plotline_arc.expand = mid_expand

                # ---- 3) Height follows arc width (pixel-based) ----
                # Use the actual available width (plotline width minus the fixed 24px padding on each side)
                available_w = max(int(getattr(self, "plotline_width", 0)) - 48, 1)
                width_px = int(((end_a - start_a) / 2.0) * available_w)  # because mapping [-1..1] to [0..W]
                max_h = max(int((getattr(self, "plotline_height", 0) / 2) - 20), 0)

                # Semicircle-ish: height ~= width/2, but capped
                new_h = min(max_h, max(0, int(width_px / 2)))
                arc.plotline_arc.height = new_h

            self.p.update()

        # If we didn't rebuild our arcs, just update the canvas
        else:
            self.plotline_canvas.update()

        
    

    # Called when we need to rebuild out plotline UI
    def reload_widget(self):

        # Rebuild our tab to reflect any changes
        self.reload_tab()
        
        # TODO:
        # Clicking brings up a mini-menu in the plotlines widget to show details and allow editing
        # Plotline object and all its children are gesture detectors
        # If event (pp, arc, etc.) is clicked on left side of screen bring mini widgets on right side, and vise versa
        # Time label is optional. Label vertial markers along the plotline with int and label if user provided

        
        # Create a stack so we can sit our plotpoints and arcs on our plotline
        plotline_stack = ft.Stack(
            expand=True, 
            alignment=ft.Alignment(0, 0),
            controls=[
                ft.Container(self.plotline_canvas, ft.padding.only(left=16, right=16), expand=True)      # Add our canvas which has our visual plotline
            ]
        )

        # Order arcs by from longest to shortest, so longer arcs are in back (temp)
        sorted_arcs = dict(sorted(self.arcs.items(), key=lambda item: item[1].data['x_alignment_end'] - item[1].data['x_alignment_start'], reverse=True))


        # Handler for plotline resize events
        for arc in sorted_arcs.values():
            # Add the arc control to the plotline stack
            plotline_stack.controls.append(arc.plotline_control)

        # Add our plot points to the plotline (They position themselves)
        for plot_point in self.plot_points.values():    
            # Add the plot point control to the plotline stack
            plotline_stack.controls.append(plot_point.plotline_control)


        self.body_container.content = plotline_stack


        ''' Start building our header with filter dropdowns ------------------------'''

        
        
        def _get_plot_points_filter_options() -> list[ft.Control]:
            # List for our colors when formatted
            plot_point_checkboxes = [ft.Checkbox(label="Show All", value=self.data.get('show_all_plot_points'), expand=True, adaptive=True)] 

            # Create our controls for our color options
            for plot_point in self.plot_points.values():
                plot_point_checkboxes.append(
                    ft.Checkbox(
                        label=plot_point.title, 
                        value=plot_point.data.get('is_shown_on_widget'), 
                        expand=True, adaptive=True,
                        on_change=lambda e, pp=plot_point: pp.toggle_plotline_control(e.control.value),
                    )
                )

            return plot_point_checkboxes
        

        def _get_arcs_filter_options() -> list[ft.Control]:

            # List for our colors when formatted
            arc_checkboxes = [ft.Checkbox(label="Show All", value=self.data.get('show_all_arcs', True), expand=True, adaptive=True)] 

            # Create our controls for our color options
            for arc in self.arcs.values():
                arc_checkboxes.append(
                    ft.Checkbox(
                        label=arc.title, 
                        value=arc.data.get('is_shown_on_widget'), 
                        expand=True, adaptive=True,
                        on_change=lambda e, a=arc: a.toggle_plotline_control(e.control.value),
                    )
                ) 
                
            return arc_checkboxes

        

        plot_points_filters = ft.Container(
            padding=None,
            width=170,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=ft.border_radius.all(6),
            content=ft.ExpansionTile(
                expand=True, dense=True,
                on_change=lambda e: self.change_data(**{'plot_points_filter_dropdown_expanded': not self.data.get('plot_points_filter_dropdown_expanded', True)}),
                title=ft.Text("Plot Point Filters", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE), 
                initially_expanded=self.data.get('plot_points_filter_dropdown_expanded', True),
                visual_density=ft.VisualDensity.COMPACT,
                tile_padding=ft.Padding(6, 0, 0, 0),      # If no leading icon, give us small indentation
                maintain_state=True, adaptive=True,
                expanded_cross_axis_alignment=ft.CrossAxisAlignment.START,
                shape=ft.RoundedRectangleBorder(),
                controls=_get_plot_points_filter_options()
            )
        )

        arcs_filters = ft.Container(
            padding=None,
            width=170,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=ft.border_radius.all(6),
            content=ft.ExpansionTile(
                expand=True, dense=True,
                on_change=lambda e: self.change_data(**{'arcs_filter_dropdown_expanded': not self.data.get('arcs_filter_dropdown_expanded', True)}),
                title=ft.Text("Arcs Filters", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE), 
                initially_expanded=self.data.get('arcs_filter_dropdown_expanded', True),
                visual_density=ft.VisualDensity.COMPACT,
                tile_padding=ft.Padding(6, 0, 0, 0),      # If no leading icon, give us small indentation
                maintain_state=True, adaptive=True,
                expanded_cross_axis_alignment=ft.CrossAxisAlignment.START,
                shape=ft.RoundedRectangleBorder(),
                controls=_get_arcs_filter_options()
            )
        )
        
    

        header =ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[plot_points_filters, arcs_filters],
        )
        

        self._render_widget(header=header)# 




        