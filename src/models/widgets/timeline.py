'''
Our timeline object that stores plot points, arcs, and time skips.
These objects is displayed in the timelines widget, and store our mini widgets plot points, arcs, and time skips.
'''

import json
import os
import flet as ft
from styles.menu_option_style import MenuOptionStyle
from models.views.story import Story
from models.widget import Widget
from models.mini_widgets.timelines.arc import Arc
from utils.verify_data import verify_data
import flet.canvas as cv
from models.app import app
import math


class Timeline(Widget):

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
                'tag': "timeline",
                'color': app.settings.data.get('default_timeline_color'),

                'filters': {   
                    'show_timeskips': True,
                    'show_plot_points': True,
                    'show_arcs': True,
                },        
                'information_display_visibility': True,
                    
                'time_label': str,                          # Label for the time axis (any str they want)
                'start_date': str,                          # Start and end date of the branch, for timeline view
                'end_date': str,                            # Start and end date of the branch, for timeline view

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

                'divisions': 10,                            # Number of divisions on the timeline

                'left_edge_label': float,                   # Label for the left edge of the timeline
                'right_edge_label': float,                  # Label for the right edge of the timeline
            },
        ) 

        

        # Declare and create our information display, which is our timelines mini widget 
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
        self.timeline_width: int = int()    # Width of our timeline canvas. Just used in calculations, not applied
        self.timeline_height: int = int()   # Height of our timeline canvas Just used in calculations, not applied

        # Our timeline canvas that draws our timeline line and markers
        self.timeline_canvas = cv.Canvas(
            on_resize=self.timeline_resized, resize_interval=20, expand=True, 
            opacity=0.7,
            content=ft.GestureDetector(
                expand=True, on_secondary_tap=self.on_secondary_tap,
                on_exit=self.on_exit, 
                on_hover=self.hover_timeline_canvas,
                on_tap=lambda e: self.information_display.toggle_visibility(value=True),
                hover_interval=20,
            )
        )

        # Dropdown on the rail. We don't use it here, let the rail handle it
        self.timeline_dropdown = None      # 'Timeline_Dropdown'

        # Builds/reloads our timeline UI
        self.reload_widget()

    # Called in the constructor
    def create_information_display(self):
        ''' Creates our timeline information display mini widget '''
        from models.mini_widgets.timelines.timeline_information_display import TimelineInformationDisplay
        
        self.information_display = TimelineInformationDisplay(
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
        from models.mini_widgets.timelines.plot_point import PlotPoint

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
    def create_arc(self, title: str):
        ''' Creates a new arc inside of our timeline object, and updates the data to match '''
        from models.mini_widgets.timelines.arc import Arc

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
        self.reload_widget()
        
    # Called when creating a new plotpoint
    def create_plot_point(self, title: str):
        ''' Creates a new plotpoint inside of our timeline object, and updates the data to match '''
        from models.mini_widgets.timelines.plot_point import PlotPoint

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
        ''' Deletes a plot point from our timeline '''
        
        # Remove from our dict
        if plot_point.title in self.plot_points:
            self.plot_points.pop(plot_point.title)
            self.data['plot_points'].pop(plot_point.title, None)
            self.save_dict()

        # Apply changes
        self.reload_widget()

    def delete_arc(self, arc):
        ''' Deletes an arc from our timeline '''
        
        # Remove from our dict
        if arc.title in self.arcs:
            self.arcs.pop(arc.title)
            self.data['arcs'].pop(arc.title, None)
            self.save_dict()

        # Apply changes
        self.reload_widget()

    # Called when right clicking our controls for either timeline or an arc
    def get_menu_options(self) -> list[ft.Control]:

        # Color, rename, delete
        return [
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
                            ft.Icon(ft.Icons.ARROW_DROP_DOWN_OUTLINED, color=ft.Colors.ON_SURFACE, size=16),
                        ]
                    ),
                    items=self._get_color_options()
                )
            ),
            MenuOptionStyle(
                on_click=self.new_item_clicked,
                data="arc",
                content=ft.Row([
                    ft.Icon(ft.Icons.CIRCLE_OUTLINED),
                    ft.Text("Arc", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
                ])
            ),
            MenuOptionStyle(
                on_click=self.new_item_clicked,
                data="plot_point",
                content=ft.Row([
                    ft.Icon(ft.Icons.ADD_LOCATION_OUTLINED),
                    ft.Text("Plot Point", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
                ])
            ),
        ]
    

    # Called when hovering over our timeline on the canvas
    async def hover_timeline_canvas(self, e: ft.HoverEvent):
        ''' Sets our coordinated for opening the menu when right clicking and updates our alignment we want to pass in '''

        # Set coordinates for menu
        self.story.mouse_x = e.global_x
        self.story.mouse_y = e.global_y

        # Calculate and set our x alignment
        w = max(int(self.timeline_width or 0), 1)
        x = float(e.local_x)
        raw = (2.0 * x / w) - 1.0
        raw = max(-1.0, min(1.0, raw))
        self.x_alignment = round(raw, 2)    # Save new x_alignment


        # Check if we're over the timeline line itself and give visual feedback
        if abs(e.local_y - (self.timeline_height / 2)) <= 50:
            self.timeline_canvas.page = self.p      # refresh page reference
            self.timeline_canvas.opacity = 1        # Full opacity to highlight
            self.timeline_canvas.content.mouse_cursor=ft.MouseCursor.CLICK      # Change cursor to pointer
            self.timeline_canvas.update()       # Apply changes
        else:
            self.timeline_canvas.page = self.p
            self.timeline_canvas.opacity = .7
            self.timeline_canvas.content.mouse_cursor=None
            self.timeline_canvas.update()
        
        

    # Called when mouse exits our timeline area
    async def on_exit(self, e: ft.HoverEvent):
        ''' Un-highlights our timeline control for visual feedback '''
        
        self.timeline_canvas.page = self.p
        self.timeline_canvas.opacity = .7
        self.timeline_canvas.update()

    # Called when right clicking our timeline on the canvas
    async def on_secondary_tap(self, e):
        ''' Opens our menu for the options of our related timeline '''

        self.story.open_menu(self.get_menu_options())

    async def new_item_clicked(self, e):
        ''' Called when new arc is clicked from timeline context menu '''
        #self.create_arc("New Arc")
        #self.new_item_container.visible = True
        await self.story.close_menu()

        tag = e.control.data

        #self.story.open_new_item_input(self.new_item_container)
        #self.p.update()

        # Show our textfield to enter the name of the new item, giving it default based name on length of those num items
        # On submit runs its rename function to create the new item

        if tag is not None:
            if tag == "arc":
                self.create_arc(f"Arc {len(self.arcs) + 1}")
            elif tag == "plot_point":
                self.create_plot_point(f"Plot Point {len(self.plot_points) + 1}")
        else:
            print("Error: No tag found for new item creation")


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


    async def timeline_resized(self, e: cv.CanvasResizeEvent):
        ''' Redraws our timeline on the canvas when it is resized. Does it on startup as well '''

        # Check if we have a new height. If not, don't update the arcs
        if self.timeline_height == int(e.height):
            update_arcs = False
        else:
            update_arcs = True

        # Update our page reference and size
        self.timeline_canvas.page = self.p
        self.timeline_width = int(e.width)
        self.timeline_height = int(e.height)
        
        # Re-draw our timeline and end markers
        self.timeline_canvas.shapes = [
            cv.Path(
                elements=[
                    # Left vertical end marker
                    cv.Path.MoveTo(0, self.timeline_height // 2 + 25),
                    cv.Path.LineTo(0, self.timeline_height // 2 - 25),

                    # Horizontal line
                    cv.Path.MoveTo(0, self.timeline_height // 2),
                    cv.Path.LineTo(self.timeline_width, self.timeline_height // 2),

                    # Right vertical end marker
                    cv.Path.MoveTo(self.timeline_width, self.timeline_height // 2 + 25),
                    cv.Path.LineTo(self.timeline_width, self.timeline_height // 2 - 25),
                ],
                paint=ft.Paint(stroke_width=4, style="stroke", color=self.data.get('color', "primary"))
            ),
        ]

        # Get number of divisions and the width between each division
        num_divisions = self.data.get('divisions', 10)
        division_width = self.timeline_width / num_divisions if num_divisions > 0 else 0

        # Create a path for our divisions
        divisions_path = cv.Path(
            elements=[],
            paint=ft.Paint(stroke_width=2, style="stroke", color=self.data.get('color', "primary"))
        )

        # Go through our number of divisions and add markers to the path
        for i in range(num_divisions + 1):
            x = int(i * division_width)
            divisions_path.elements.append(cv.Path.MoveTo(x, self.timeline_height // 2 + 10))
            divisions_path.elements.append(cv.Path.LineTo(x, self.timeline_height // 2 - 10))  
            
        # Add our divisions path to the canvas
        self.timeline_canvas.shapes.append(divisions_path)


        # Go through our arcs and update their size
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
                if arc.timeline_arc is not None:
                    arc.timeline_arc.expand = mid_expand

                # ---- 3) Height follows arc width (pixel-based) ----
                # Use the actual available width (timeline width minus the fixed 24px padding on each side)
                available_w = max(int(getattr(self, "timeline_width", 0)) - 48, 1)
                width_px = int(((end_a - start_a) / 2.0) * available_w)  # because mapping [-1..1] to [0..W]
                max_h = max(int((getattr(self, "timeline_height", 0) / 2) - 20), 0)

                # Semicircle-ish: height ~= width/2, but capped
                new_h = min(max_h, max(0, int(width_px / 2)))
                arc.timeline_arc.height = new_h

            self.p.update()

        # If we didn't rebuild our arcs, just update the canvas
        else:
            self.timeline_canvas.update()

        
    

    # Called when we need to rebuild out timeline UI
    def reload_widget(self):

        # Rebuild our tab to reflect any changes
        self.reload_tab()
        
        # TODO:
        # Clicking brings up a mini-menu in the timelines widget to show details and allow editing
        # Timeline object and all its children are gesture detectors
        # If event (pp, arc, etc.) is clicked on left side of screen bring mini widgets on right side, and vise versa
        # Time label is optional. Label vertial markers along the timeline with int and label if user provided

        
        # Create a stack so we can sit our plotpoints and arcs on our timeline
        timeline_stack = ft.Stack(
            expand=True, 
            alignment=ft.Alignment(0, 0),
            controls=[
                ft.Container(self.timeline_canvas, ft.padding.only(left=16, right=16), expand=True)      # Add our canvas which has our visual timeline
            ]
        )

        # Order arcs by from longest to shortest, so longer arcs are in back (temp)
        sorted_arcs = dict(sorted(self.arcs.items(), key=lambda item: item[1].data['x_alignment_end'] - item[1].data['x_alignment_start'], reverse=True))

        # Handler for timeline resize events
        for arc in sorted_arcs.values():
            # Add the arc control to the timeline stack
            timeline_stack.controls.append(arc.timeline_control)

        # Add our plot points to the timeline (They position themselves)
        for plot_point in self.plot_points.values():    
            # Add the plot point control to the timeline stack
            timeline_stack.controls.append(plot_point.timeline_control)


        self.body_container.content = timeline_stack


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
                        on_change=lambda e, pp=plot_point: pp.toggle_timeline_control(e.control.value),
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
                        on_change=lambda e, a=arc: a.toggle_timeline_control(e.control.value),
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




        