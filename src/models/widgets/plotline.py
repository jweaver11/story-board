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
from models.mini_widgets.plotline_plot_point import PlotlinePlotPoint
import flet.canvas as cv
from models.app import app
import asyncio 
import uuid
from constants import PLOTLINE_PADDING, PLOTLINE_WIDTH, PLOTLINE_HEIGHT
from styles.colors import colors
from styles.text_fields import TextField, SingleLineTextField


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
                'start_label': "0",                              # Start label
                'end_label': "10",                            # Start and end date of the branch, for plotline view
                'divisions': ["1", "2", "3", "4", "5", "6", "7", "8", "9"],    # List len is the num of divisions, and each value is its label
              
                'relevant_characters': dict(),  # keys and name to relevant characters. {'id': {'id': "id_val", 'name': "name_val"}...}
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
            super().__init__(
                data=data, horizontal_alignment=ft.CrossAxisAlignment.CENTER, offset=ft.Offset(-0.5, 0),
                animate_position=ft.Animation(250, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            ) # Sets our data to the passed in data

            # If we're new, give default values for our data 
            if is_new:
                self.data = {
                    'id': str(uuid.uuid4()),
                    'tag': "marker",    # Since nothing shown in sidebar, just give it a tag of marker
                    'title': "New Marker",  # Title for our marker
                    'color': "primary",
                    'position': self.widget.locked_position
                }

            self.is_dragging: bool = False

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

            def start_drag(e=None):
                self.is_dragging = True

            def highlight(e=None):
                shadow = ft.BoxShadow(
                    20, 40, 
                    ft.Colors.with_opacity(0.24, self.data.get('color', ft.Colors.PRIMARY)), 
                    #blur_style=ft.BlurStyle.OUTER
                )
                #highlight_container1.shadow = shadow
                highlight_container2.shadow = shadow
                self.update()
                

            # Called when we stop hovering over our marker
            def stop_highlight(e=None):
                if self.is_dragging == True:
                    return
                #highlight_container1.shadow = None
                highlight_container2.shadow = None
                self.update()

            def stop_drag(e=None):
                self.update_data(**{'position': (self.left, None)})
                self.is_dragging = False
                stop_highlight()
                

            def get_menu_options() -> list[ft.Control]:

                # Called when rename button is clicked
                async def handle_rename(e: ft.Event):
                    await self.widget.story.close_menu()
                    await title_tf.focus()

                # Called when color button is clicked
                def get_color_options() -> list[ft.Control]:
                    ''' Returns a list of all available colors for icon changing '''
            
                    # Changes our color in data and the UI to reflect
                    async def change_color(e: ft.Event[ft.MenuItemButton]):
                        await self.widget.story.close_menu()
                        self.update_data(**{'color': e.control.data})
                        for shape in canvas.shapes:
                            shape.paint.color = e.control.data
                        self.update()
                        
            
                    return [
                        ft.MenuItemButton(
                            content=ft.Text(color.capitalize(), weight=ft.FontWeight.BOLD, color=color),
                            on_click=change_color, close_on_click=True,
                            data=color,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click")
                        ) for color in colors
                    ]

                # Delete the marker from data and UI
                async def delete_marker(e=None):
                    await self.widget.story.close_menu()
                    self.widget.data.get('markers', {}).pop(self.data.get('id', ''), None)
                    self.widget.update_data(**{'markers': self.widget.data.get('markers', {})})
                    self.widget.marker_stack.controls.remove(self)
                    self.widget.marker_stack.update()
                    
                    
                return [
                    MenuOptionStyle(
                        on_click=handle_rename,
                        content=ft.Row([
                            ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, self.data.get('color', 'primary'),),
                            ft.Text(
                                f"Rename Marker", 
                                weight=ft.FontWeight.BOLD, 
                                overflow=ft.TextOverflow.ELLIPSIS, expand=True
                            ), 
                        ]),
                    ),
                    MenuOptionStyle(
                        ft.SubmenuButton(
                            ft.Row([
                                ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.data.get('color', "primary")), 
                                ft.Text("Marker Color", weight=ft.FontWeight.BOLD, expand=True),
                                ft.Icon(ft.Icons.ARROW_RIGHT),
                            ], expand=True),
                            get_color_options(), 
                            menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                            style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            tooltip="Change this markers color"
                        ),
                        no_padding=True, no_effects=True
                    ),
                    MenuOptionStyle(
                        ft.MenuItemButton(
                            f"Delete Marker", leading=ft.Icon(ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR),
                            on_click=delete_marker, 
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            tooltip="Delete this marker from the plotline",
                        ),
                        no_effects=True, no_padding=True
                    )
                ]
                

            # Set our size
            self.height = PLOTLINE_HEIGHT / 2
            self.left = self.data.get('position', (PLOTLINE_WIDTH // 2, 1000))[0]  # Get our left position from our data, or default to middle of plotline

            # Our container that is our plot point on the plotline, and contains our gesture detector for hovering and right clicking
            self.controls = [
                highlight_container1 := ft.Container(
                    title_tf := ft.TextField(
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
                    canvas := cv.Canvas(
                        width=10, opacity=.7,
                        expand=True,   
                        content=ft.GestureDetector(
                            on_enter=highlight,
                            on_exit=stop_highlight,
                            on_pan_start=start_drag,
                            on_pan_end=stop_drag,
                            on_pan_update=self.move_marker,
                            expand=True,
                            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
                            on_secondary_tap=lambda _: self.widget.story.open_menu(get_menu_options()),
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
        self.showing_info = False
        self.visible_mw_id = ""     # Reset our state for tracking visible mw
        await super().hide_sidebar(e)

        

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
                        padding=ft.Padding.all(8), 
                        shape=ft.RoundedRectangleBorder(radius=4),
                        border_radius=ft.BorderRadius.all(4),
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
        self.plotline_highlight_container.shadow = ft.BoxShadow(20, 40, ft.Colors.with_opacity(0.15, self.data.get('color', ft.Colors.PRIMARY)))
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
        # Stop all highlights if there were any previous
        for pp in self.plot_point_stack.controls:
            pp.stop_highlight()
        for arc in self.arc_stack.controls:
            arc.stop_highlight()

    # Called when right clicking our plotline on the canvas
    async def open_menu(self, e: ft.PointerEvent=None):
        ''' Opens our menu for the options of our related plotline '''
        if self.can_open_menu:
            self.story.open_menu(self.get_new_event_menu_options())
            self.locked_position = self.position


    async def create_plot_point(self, e: ft.Event=None):
        ''' Creates plot point in data, control and control on event stack'''
        await self.story.close_menu()
        new_plot_point = PlotlinePlotPoint(
            widget=self, 
            is_new=True, 
            data={
                'position': self.locked_position, 
                'title': "New Plot Point",
            }
        )
        self.update_data(**{'mini_widgets_data': {new_plot_point.data.get('id', ''): new_plot_point.data}})
        self.plot_point_stack.controls.append(new_plot_point)
        self.plot_point_stack.update()
        await new_plot_point.show_mini_widget()   # Show in sidebar

    # Creates a marker in data and a control on the event stack. Has no info for sidebar
    async def create_marker(self):
        await self.story.close_menu()
        new_marker = self.PlotlineMarker(widget=self, is_new=True)

        # Update our data, add it to the events stack, and show it in the sidebar
        self.update_data(**{'markers': {new_marker.data.get('id', ''): new_marker.data}})
        self.marker_stack.controls.append(new_marker)
        self.marker_stack.update()

    def create_sidebar_body_ctrls(self) -> list[ft.Control]:

        # TODO: Sidebar for plotline and pp, divisions, events. Divisions stack instead of drawing them?

        


        # Create a control for the relevant character in data, with a remove button
        def create_relevant_character_ctrl(char_data: dict) -> ft.Row:

            # Remove the character form data
            def remove_relevant_character(e: ft.Event[ft.IconButton]):
                char_id = e.control.data
                if char_id in self.data.get('relevant_characters', []):
                    self.data.get('relevant_characters', {}).pop(char_id, None)
                    self.update_data(**{'relevant_characters': self.data.get('relevant_characters', [])})
                    other_characters[char_id] = {'id': char_id, 'name': char_data.get('name')}
                relevant_characters_row.controls.remove(e.control.parent.parent)
                relevant_characters_row.update()
                return
    
            return ft.Container(
                ft.Row([
                    ft.Text(char_data.get('name'), weight=ft.FontWeight.BOLD, overflow=ft.TextOverflow.ELLIPSIS),   # Char name
                    ft.IconButton(      # Remove button
                        ft.Icons.CLOSE, ft.Colors.ERROR, tooltip=f"Remove {char_data.get('name')} from relevant characters for this plot point",
                        mouse_cursor=ft.MouseCursor.CLICK,
                        on_click=remove_relevant_character,
                        data=char_data.get('id'), 
                    )
                    ], spacing=0, margin=ft.Margin.only(left=8), tight=True
                ),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH, 
                border_radius=4,
                padding=ft.Padding.only(left=6),
            )
            

        # Pass in the characters you want
        def create_search_bar_ctrls(characters: list[dict]):
            return [
                ft.ListTile(
                    title=ft.Text(char_data.get('name')),
                    data=char_data,
                    on_click=handle_adding_relevant_characters,
                ) for char_data in characters
            ] 

        # Adds the character to data and a control to the column
        async def handle_adding_relevant_characters(e: ft.Event[ft.IconButton]):
            new_char_data = e.control.data
            new_char_id = new_char_data.get('id')
            self.data.get('relevant_characters', {})[new_char_id] = new_char_data
            self.update_data(**{'relevant_characters': self.data.get('relevant_characters', [])})
            relevant_characters_row.controls.append(create_relevant_character_ctrl(new_char_data))
            relevant_characters_row.update()
            await close_search_bar()

        # Handles when we type in search bar to filter our characters list
        async def handle_change(e: ft.Event[ft.SearchBar]):
            nonlocal character_search_bar, other_characters
            query = e.control.value.strip().lower()
            matching = [
                {
                    'id': char_data.get('id'),
                    'name': char_data.get('name') 
                } for char_data in other_characters.values() if char_data.get('name').lower().startswith(query) and char_data.get('id') not in self.data.get('relevant_characters', {})
            ] if query else [
                {
                    'id': char_data.get('id'), 
                    'name': char_data.get('name')
                } for char_data in other_characters.values()
            ]
            character_search_bar.controls = create_search_bar_ctrls(matching)
            character_search_bar.update()

        # Opens search bar and populates correct controls
        async def open_search_bar(e=None):
            character_search_bar.controls = create_search_bar_ctrls([char_data for char_data in other_characters.values() if char_data.get('id') not in self.data.get('relevant_characters', {})])
            character_search_bar.update()
            await character_search_bar.open_view()

        # Reset the value of the search bar
        def reset_search_bar(e=None):
            character_search_bar.value = ""
            character_search_bar.update()

        # When closing search bar, reset it and close the view
        async def close_search_bar(e=None):
            reset_search_bar()
            await character_search_bar.close_view()

        # All other characters in our story that are not relevant to this plot point, so we can add them
        other_characters = {
            widget.data.get('id'): {
                'id': widget.data.get('id'), 
                'name': widget.data.get('title')
            } for widget in self.story.widgets.values() if widget.data.get('tag') == 'character' and widget.data.get('id') not in self.data.get('relevant_characters', {})
        }        

        # Build UI to display all relevant characters in our data
        relevant_characters_row = ft.Row(
            [create_relevant_character_ctrl(char_data) for char_data in self.data.get('relevant_characters', {}).values()],
            wrap=True, margin=ft.Margin.only(bottom=10)
        )

        # Search bar for adding relevant characters
        character_search_bar = ft.SearchBar(
            value="", view_elevation=4,
            controls=create_search_bar_ctrls([char_data for char_data in other_characters.values() if char_data.get('id') not in self.data.get('relevant_characters', {})]), 
            bar_padding=ft.Padding.only(left=6, right=6),
            divider_color=ft.Colors.PRIMARY,
            bar_bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            bar_hint_text="Search character names here",
            bar_shape=ft.RoundedRectangleBorder(radius=4),
            view_shape=ft.RoundedRectangleBorder(radius=4),
            bar_size_constraints=ft.BoxConstraints(min_height=40, max_height=50, max_width=400),
            on_tap=open_search_bar,
            on_tap_outside_bar=close_search_bar,
            on_change=handle_change,
            on_blur=reset_search_bar,
            capitalization=ft.TextCapitalization.WORDS,
        )


        return [
                
                ft.Text(f"Relevant Characters", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), selectable=True, margin=ft.Margin.only(bottom=4)), 
                
                relevant_characters_row,
                character_search_bar,
                self.sidebar_notes_label,
                self.sidebar_notes_column,
                
            ]
        
        
        

    # Called for any size changes to our plotline canvas
    def redraw_plotline_canvas(self):
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
                paint=ft.Paint(stroke_width=4, style="stroke", color=f"{self.data.get('color', "primary")}")
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
            paint=ft.Paint(stroke_width=2, style="stroke", color=f"{self.data.get('color', "primary")}")
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
                        x, PLOTLINE_HEIGHT / 2 - PLOTLINE_PADDING / 2,
                        str(divisions[i]), 
                        ft.TextStyle(14, weight=ft.FontWeight.BOLD),
                        alignment=ft.Alignment.CENTER
                    )
                )
            
        # Add our divisions path to the canvas
        self.plotline_canvas.shapes.append(divisions_path)

                     
    def build(self):
        super().build()

        # When clicking our canvas. If we're in center vertically and not showing sidebar, show sidebar
        async def may_show_sidebar(e: ft.PointerEvent):
            if self.can_open_menu:
                await self.show_info()
            #print("Open menu")

        # Called when we change one of our labels
        def change_label(e: ft.Event[ft.TextField]):
            label = e.control.data
            new_value = e.control.value
            if label == "start_label":
                self.update_data(**{'start_label': new_value})
            elif label == "end_label":
                self.update_data(**{'end_label': new_value})
            else:
                self.update_data(**{'time_label': new_value})
            
        # Our canvas that 
        self.plotline_canvas = cv.Canvas(
            content=ft.GestureDetector(
                expand=True, 
                on_secondary_tap=self.open_menu,
                on_hover=self.hover_plotline_canvas,
                on_exit=self.stop_highlight_plotline_canvas,
                on_tap=may_show_sidebar,
                hover_interval=20,
            ),
            width=PLOTLINE_WIDTH, height=PLOTLINE_HEIGHT,
        )
        

        self.plotline_highlight_container = ft.Container(
            width=PLOTLINE_WIDTH, height=3, shadow=None, ignore_interactions=True, margin=ft.Margin.symmetric(horizontal=PLOTLINE_PADDING)
        )

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
        # Load our markers as well
        for marker in self.data.get('markers', {}).values():
            markers_data_list.append(marker)

        # Sort arcs so biggest is in the back
        arcs_data_list.sort(key=lambda item: item[1].data.get('left', 0) + item[1].data.get('right', 0))

        # Add markers next since they are next biggest
        for marker_data in markers_data_list:    
            self.marker_stack.controls.append(self.PlotlineMarker(self, marker_data))

        # Add plot points last
        for plot_point_data in plot_points_data_list:    
            self.plot_point_stack.controls.append(PlotlinePlotPoint(self, plot_point_data))

        self.sidebar_body.controls = self.create_sidebar_body_ctrls()  
        if self.data.get('show_sidebar', True) == False:
            self.showing_info = False

        start_label = ft.TextField(
            value=self.data.get('start_label', ""), dense=True,
            capitalization=ft.TextCapitalization.SENTENCES,
            bgcolor=ft.Colors.TRANSPARENT,
            on_blur=change_label,
            border_radius=4, content_padding=ft.Padding.all(0),
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.PRIMARY,
            data='start_label',
            text_align=ft.TextAlign.CENTER,
            left=PLOTLINE_PADDING,
            top=PLOTLINE_HEIGHT / 2 - PLOTLINE_PADDING,
            offset=ft.Offset(-0.5, 0),
            width=PLOTLINE_PADDING * 2, 
            text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD, overflow=ft.TextOverflow.ELLIPSIS),
        )

        end_label = ft.TextField(
            value=self.data.get('end_label', ""), dense=True,
            capitalization=ft.TextCapitalization.SENTENCES,
            bgcolor=ft.Colors.TRANSPARENT,
            on_blur=change_label,
            border_radius=4, content_padding=ft.Padding.all(0),
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.PRIMARY,
            data='end_label',
            text_align=ft.TextAlign.CENTER,
            left=PLOTLINE_WIDTH - PLOTLINE_PADDING,
            top=PLOTLINE_HEIGHT / 2 - PLOTLINE_PADDING,
            offset=ft.Offset(-0.5, 0),
            width=PLOTLINE_PADDING * 2, 
            text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD, overflow=ft.TextOverflow.ELLIPSIS),
        )

        time_label = ft.TextField(
            value=self.data.get('time_label', ""), dense=True,
            capitalization=ft.TextCapitalization.SENTENCES,
            bgcolor=ft.Colors.TRANSPARENT,
            on_blur=change_label,
            border_radius=4,
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.PRIMARY,
            data='time_label',
            text_align=ft.TextAlign.CENTER,
            left=PLOTLINE_WIDTH / 2,
            top=PLOTLINE_HEIGHT - PLOTLINE_PADDING,
            offset=ft.Offset(-0.5, 0),
            text_style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD, overflow=ft.TextOverflow.ELLIPSIS),
        )

        # Holds our drawing so we can interact with it, zoom, pan, etc.
        interactive_viewer = ft.InteractiveViewer(
            content=ft.Stack([
                ft.Container(
                    image=ft.DecorationImage("flow_chart_background.png", repeat=ft.ImageRepeat.REPEAT),
                    width=PLOTLINE_WIDTH, height=PLOTLINE_HEIGHT,
                ),
                self.plotline_canvas,
                start_label,
                time_label,
                end_label,
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

        self.redraw_plotline_canvas()







        