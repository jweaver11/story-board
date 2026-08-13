''' Class for the Plot Chart widget, works similar to a flow chart'''

import flet as ft
from models.views.story import Story
from models.widget import Widget
from styles.menu_option_style import MenuOptionStyle
from models.app import app
from styles.text_fields import SmallTextField, TextField
import flet.canvas as cv
from styles.snack_bar import SnackBar
from styles.colors import colors
import asyncio
from constants import FIXED_STACK_WIDTH, FIXED_STACK_HEIGHT
import uuid
from styles.text_fields import NoLabelTextField

class PlotChart(Widget):

    # Constructor
    def __init__(self, title: str, directory_path: str, story: Story, data: dict={}, is_new: bool = False):

        # Initialize from our parent class 'Widget'. 
        super().__init__(
            title = title,                      # Title of the note
            directory_path = directory_path,    # Path to our notes json file
            story = story,                      # Reference to our story object
            data = data,
            is_new = is_new 
        )

        # If we're new, give default values for our data 
        if self.is_new == True:
            self.data.update({
                # Widget data
                'tag': "plot_chart",             # Tag to identify what type of object this is
                'color': app.settings.data.get('widget_defaults', {}).get('plot_chart', {}).get('color'),

                'spider_web_view': app.settings.data.get('widget_defaults', {}).get('plot_chart', {}).get('spider_web_view', False),   # If the plot chart is in spider web view or not

                'nodes': [],
                  # List of all our Nodes/events
                    #{'label': "", 'description': "", 'position': (100, 100), 'color': '#FFFFFF'}
                 
                'edges': [    # List of all our Links/Connections between nodes
                    #{'source': "", 'target': ""}
                ] 
            },
        )

        # State and management
        self.new_node_position = (200, 200)     # Position we place new nodes
        self.locked_new_node_position = (200, 200)  # Position we place new nodes when right clicking to create a new node
        self.edge_canvas: cv.Canvas           # Canvas that holds our edges (cv.shapes)
        self.node_stack: ft.Stack           # Stack that holds our nodes (gesture detectors)
        self.node_sidebar_column: ft.Column

        # State trackers
        self.source_node: str = None        # Tracks which node we are dragging from when creating a new edge
        self.target_node: str = None        # Tracks which node we are dragging to when creating a new edge
        #self.source_side: str = None      # Determines which sides of the nodes we start dragging from
        #self.target_side: str = None       # Determines which sides of the nodes we end dragging on

        self.add_node_button: ft.Button     # Button to add new nodes that is displayed OUTSIDE the sidebar

        
        

    # Class for handling all node logic
    class Node(ft.GestureDetector):

        def __init__(self, widget: 'PlotChart',  data: dict={}):

            # Initialize node properties
            self.widget = widget
            position = data.get('position', (200, 200))

            super().__init__(
                left=position[0],
                top=position[1],
                width=150, data=data,
                offset=ft.Offset(0, -1),
                animate_position=ft.Animation(250, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
                on_secondary_tap=self.open_menu,
                on_hover=self.widget.set_mouse_coords,
            )

        # Moves the node on the stack and updates the drawing that connects the edges
        async def move_node(self, e: ft.DragUpdateEvent):
            
            # Update us visually
            self.left += e.local_delta.x
            self.top += e.local_delta.y
            self.update()
            if self.left < 0:
                self.left = 0
            if self.top < 0:
                self.top = 0
            # Update data - Edge needs this to redraw as we drag, so we can't wait until drag is over
            for node in self.widget.data.get('nodes', []):
                if node.get('id', '') == self.data.get('id', ''):
                    node['position'] = (self.left, self.top)
                    break
            # Redraw any relevant edges
            for edge in self.widget.edge_canvas.shapes:
                if isinstance(edge, self.widget.Edge) and (edge.source_node == self.data.get('id', '') or edge.target_node == self.data.get('id', '')):
                    edge.draw_edge()   
                    edge.update()

        # Saves our new position when we are done dragging
        async def save_position(self, e: ft.DragEndEvent):
            # Make sure data is accurate
            for node_data in self.widget.data.get('nodes', []):
                if node_data.get('id', '') == self.data.get('id', ''):
                    node_data['position'] = (self.left, self.top)
                    break
            self.widget.update_data(**{'nodes': self.widget.data.get('nodes', [])})
            self.widget.set_mouse_coords(e) # Reset the menu position 

        async def rename_clicked(self, e=None):
            await self.widget.story.close_menu()
            await self.title_tf.focus()

        # Opens a menu with our options when right clicking a node
        async def open_menu(self, e=None):
            menu_options = [
                MenuOptionStyle(
                    on_click=self.rename_clicked,
                    content=ft.Row([
                        ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, self.data.get('color', '#FFFFFF')),
                        ft.Text(
                            "Edit Label", 
                            weight=ft.FontWeight.BOLD, 
                            
                        ), 
                    ]),
                    data=self.data.get('id', ''),
                ),
                MenuOptionStyle(
                    ft.SubmenuButton(
                        ft.Row([
                            ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.data.get('color', '#FFFFFF')), 
                            ft.Text("Color", weight=ft.FontWeight.BOLD, expand=True),
                            ft.Icon(ft.Icons.ARROW_RIGHT),
                        ], expand=True),
                        self.get_color_options(), 
                        menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                        style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        tooltip="Change this widget's color"
                    ),
                    no_padding=True, no_effects=True
                ),
                MenuOptionStyle(
                    on_click=self.delete_clicked,
                    content=ft.Row([
                        ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, ft.Colors.ERROR),
                        ft.Text("Delete", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True),
                    ]),
                )
            ] 

            self.widget.story.open_menu(menu_options)

        # Handles deleting the node
        async def delete_clicked(self, e: ft.Event):

            # Remove the node from data
            for idx, node in enumerate(self.widget.data.get('nodes', [])):
                if node.get('id', '') == self.data.get('id', ''):
                    self.widget.data['nodes'].pop(idx)
                    self.widget.node_stack.controls.pop(idx)
                    break
            # Remove any edges connected to the node from data and canvas
            self.widget.data['edges'] = [
                edge for edge in self.widget.data.get('edges', [])
                if edge.get('source', '') != self.data.get('id', '') and edge.get('target', '') != self.data.get('id', '')
            ]
            self.widget.edge_canvas.shapes = [
                shape for shape in self.widget.edge_canvas.shapes
                if not (isinstance(shape, self.widget.Edge) and (shape.source_node == self.data.get('id', '') or shape.target_node == self.data.get('id', '')))
            ]

            self.widget.update_data(**{'nodes': self.widget.data.get('nodes', []), 'edges': self.widget.data.get('edges', [])})

            await self.widget.story.close_menu()
            self.widget.update()

        def get_color_options(self) -> list[ft.Control]:
            ''' Returns a list of all available colors for icon changing '''

            # Called when a color option is clicked on popup menu to change icon color
            async def _change_icon_color(e: ft.Event):
                ''' Passes in our kwargs to the widget, and applies the updates '''
                color = e.control.data

                for node in self.widget.data.get('nodes', []):
                    if node.get('id') == self.data.get('id'):
                        node['color'] = color
                        break
                self.widget.update_data(**{'nodes': self.widget.data.get('nodes', [])})

                self.content.content.controls[3].controls[0].content.content.color = color
                self.content.content.controls[3].controls[1].content.content.color = color
                self.update()
                    
                await self.widget.story.close_menu()

            # List for our colors when formatted
            color_controls = [] 

            # Create our controls for our color options
            for color in colors:
                color_controls.append(
                    ft.MenuItemButton(
                        content=ft.Text(color.capitalize(), weight=ft.FontWeight.BOLD, color=color),
                        on_click=_change_icon_color, close_on_click=True, data=color,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click")
                    )
                )

            return color_controls

        # Builds our node
        def build(self):
            
            async def _highlight_node(e: ft.PointerEvent):
                # If we are dragging, update our target as this node side
                if self.widget.source_node:   # Only highlight if we're dragging from another node
                    self.widget.target_node = e.control.data.get('id')
                    #self.widget.target_side = e.control.data.get('side')

                # Visual highlight
                e.control.content.shadow = ft.BoxShadow(10, 20, ft.Colors.with_opacity(0.25, self.data.get('color', '#FFFFFF')))
                e.control.update()
            async def _stop_highlight_node(e: ft.PointerEvent):
                # Reset state trackers
                self.widget.target_node = None
                #self.widget.target_side = None
                # Highlight reset
                e.control.content.shadow = None
                e.control.update()

            # Creates our new edge (link) between nodes
            async def _create_new_edge(e: ft.PointerEvent):
                
                # Remove our visual feedback
                self.page.overlay.pop()
                self.page.update()

                # If its an incomplete edge (we didn't end on another node), reset and exit
                if not self.widget.source_node or not self.widget.target_node:
                    self.widget.source_node = None
                    self.widget.target_node = None
                    #self.widget.source_side = None
                    #self.widget.target_side = None
                    await _stop_highlight_node(e)   # Stops the highlight
                    return  
                
                # Don't allow connections to self
                if self.widget.source_node == self.widget.target_node:    # Don't allow connections to self
                    #self.page.show_dialog(SnackBar("Cannot connct a node to itself."))
                    return  
                
                # If the edge already exists, delete it
                for edge_data in self.widget.data.get('edges', []):
                    if (edge_data.get('source', '') == self.widget.source_node and edge_data.get('target', '') == self.widget.target_node) or (edge_data.get('source', '') == self.widget.target_node and edge_data.get('target', '') == self.widget.source_node):
                        self.widget.data['edges'].remove(edge_data)
                        self.widget.needs_file_write = True
                        # Reset state trackers
                        self.widget.source_node = None
                        self.widget.target_node = None
                        #self.widget.source_side = None
                        #self.widget.target_side = None
                        # Reload
                        source_node = edge_data['source']
                        target_node = edge_data['target']

                        # Remove from edge canvas
                        for edge in self.widget.edge_canvas.shapes:
                            if not isinstance(edge, self.widget.Edge):
                                continue
                            if edge.source_node == source_node and edge.target_node == target_node:
                                self.widget.edge_canvas.shapes.remove(edge)
                                #print("Removing edge from canvas")
                                break
                            if edge.source_node == target_node and edge.target_node == source_node:
                                self.widget.edge_canvas.shapes.remove(edge)
                                #print("Removing edge from canvas")
                                break
                            
                        self.widget.update_data(**{'edges': self.widget.data.get('edges', [])})
                        self.widget.update()
                        return  

                # Save new edget to data with source, target, start, end, and default color
                self.widget.data['edges'].append({
                    'source': self.widget.source_node,
                    'target': self.widget.target_node,
                })
                self.widget.update_data(**{'edges': self.widget.data.get('edges', [])})   # Update our data with the new edge

                # Reset state trackers
                self.widget.source_node = None
                self.widget.target_node = None
                #self.widget.source_side = None
                #self.widget.target_side = None

                # Re-render page to show new edge
                await _stop_highlight_node(e)   # Stops the highlight

                # Add edge to the canvas
                self.widget.edge_canvas.shapes.append(
                    self.widget.Edge(
                        self.widget,
                        self.widget.data.get('edges')[-1]
                    )
                )
                self.widget.edge_canvas.update()

                

            # Update our state trackers for new edges and show visual feedback
            async def start_new_edge(e: ft.PointerEvent):
                await self.widget.story.close_menu()
                self.widget.source_node = e.control.data.get('id', '')
                #self.widget.source_side = e.control.data.get('side')
                self.page.overlay.append(
                    ft.Container(
                        cv.Canvas([
                            cv.Line(
                                e.global_position.x, e.global_position.y, 
                                e.global_position.x, e.global_position.y, 
                                ft.Paint("#FFFFFF", stroke_width=3, style="stroke")
                            )
                        ], expand=True), 
                    expand=True, ignore_interactions=True
                    )
                )
                # Change cursor for visual feedback
                self.page.update()

            # Update the visual feedback to follow our mouse as we drag to create a new edge
            async def _update_line(e: ft.PointerEvent):
                line: cv.Line = self.page.overlay[-1].content.shapes[-1]  # Get the last line we added
                line.x2 = e.global_position.x
                line.y2 = e.global_position.y
                self.page.overlay[-1].update()

            def _update_title(e: ft.Event[ft.TextField]):
                new_title = e.control.value
                for ctrl in self.widget.node_sidebar_column.controls:
                    if ctrl.data == self.data.get('id', ''):
                        ctrl.label = new_title
                        ctrl.update()
                        break

            def _save_title(e: ft.Event[ft.TextField]):
                for node_data in self.widget.data.get('nodes', []):
                    if node_data.get('id', '') == self.data.get('id', ''):
                        node_data['label'] = e.control.value
                        break
                self.widget.update_data(**{'nodes': self.widget.data.get('nodes', [])})

            def _update_description(e: ft.Event[ft.TextField]):
                new_desc = e.control.value
                for ctrl in self.widget.node_sidebar_column.controls:
                    if ctrl.data == self.data.get('id', ''):
                        ctrl.value = new_desc
                        ctrl.update()
                        break

            # Saves the description for this node when the text field loses focus
            async def _save_description(e: ft.Event[ft.TextField]):
                for node_data in self.widget.data.get('nodes', []):
                    if node_data.get('id', '') == self.data.get('id', ''):
                        node_data['description'] = e.control.value
                        break
                self.widget.update_data(**{'nodes': self.widget.data.get('nodes', [])})

            # Text field for editing the node's description
            self.description_ctrl = SmallTextField(
                self.data.get('description', ''),
                expand=True, 
                on_change=_update_description,
                on_blur=_save_description,
            )

            self.title_tf = NoLabelTextField(
                value=self.data.get('label', ''),
                on_change=_update_title,
                on_blur=_save_title,
                #text_style=ft.TextStyle()
                text_align=ft.TextAlign.CENTER,
                expand=True, border_radius=4
            )

            # Our nodes content. Column with label, divider, description text field, and connection points
            self.content = ft.Container(
                ft.Column([
                    ft.GestureDetector(
                        ft.Container(self.title_tf, ignore_interactions=True, expand=True),
                        on_pan_start=self.widget.story.close_menu,
                        on_pan_update=self.move_node,
                        on_pan_end=self.save_position,
                        mouse_cursor=ft.MouseCursor.MOVE,
                        drag_interval=20,
                        on_double_tap=self.rename_clicked,
                    ),
                    ft.Divider(ft.Colors.SURFACE_CONTAINER_LOW, 2),
                    self.description_ctrl,
                    ft.Row([
                        ft.GestureDetector(
                            ft.Container(ft.Icon(ft.Icons.CIRCLE_OUTLINED, self.data.get('color'), scale=1.25), shape=ft.BoxShape.CIRCLE), 
                            mouse_cursor=ft.MouseCursor.PRECISE,
                            data={'id': self.data.get('id'), 'side': "left"},                            
                            on_enter=_highlight_node,   # Highlight and set target source trackers if we enter a node while dragging from another
                            on_pan_start=start_new_edge,   # Show line to follow mouse
                            on_pan_update=_update_line,   # Update line to follow mouse
                            on_pan_end=_create_new_edge,  
                            on_exit=_stop_highlight_node, 
                            drag_interval=20, 
                        ),
                        ft.GestureDetector(
                            ft.Container(ft.Icon(ft.Icons.CIRCLE_OUTLINED, self.data.get('color'), scale=1.25), shape=ft.BoxShape.CIRCLE), 
                            mouse_cursor=ft.MouseCursor.PRECISE,
                            data={'id': self.data.get('id'), 'side': "right"},                        
                            on_enter=_highlight_node,  
                            on_pan_start=start_new_edge,   
                            on_pan_update=_update_line,   
                            on_pan_end=_create_new_edge,  
                            on_exit=_stop_highlight_node,  
                            drag_interval=20,
                        ),
                        
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                expand=True, #shadow=ft.BoxShadow(1, 1, blur_style=ft.BlurStyle.OUTER),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                #bgcolor=ft.Colors.with_opacity(0.12, self.color),
                border_radius=8, padding=ft.Padding.all(8),
                alignment=ft.Alignment.TOP_CENTER,
            )
                
        
    # Class for the Edges/Links between our nodes that show up as a line on the edge_canvas
    class Edge(cv.Path):
        def __init__(self, widget: 'PlotChart', data: dict):
            self.source_node = data.get('source')
            self.target_node = data.get('target')
            self.widget = widget

            super().__init__([], paint=ft.Paint(ft.Colors.ON_SURFACE, stroke_width=3, style="stroke", anti_alias=True))

        def build(self):
            self.draw_edge()

        def draw_edge(self):
            self.start_position = None
            self.end_position = None
            for node in self.widget.data.get('nodes', []):
                if node['id'] == self.source_node:
                    self.start_position = node.get('position', (0, 0))
                elif node['id'] == self.target_node:
                    self.end_position = node.get('position', (0, 0))

            # Catch errors
            if not self.start_position or not self.end_position:
                return

            # Unpack into local vars so we don't mutate the stored tuples
            start_x, start_y = self.start_position
            end_x, end_y = self.end_position

            # Offset half way up node connector icons
            start_y -= 20
            end_y -= 20

            # Straight edges between nodes
            if self.widget.data.get('spider_web_view', False):
                # Adjust for in/out nodes
                if start_x < end_x:
                    start_x += 140  # 150 width - 10 for mid node
                    end_x += 10
                else:
                    end_x += 140
                    start_x += 10
                     
                self.elements = [
                    cv.Path.MoveTo(start_x, start_y),
                    cv.Path.LineTo(end_x, end_y),
                ]

            # Three-node turns
            else:
                # Adjust for in/out nodes
                if start_x > end_x:
                    end_x += 150
                else:
                    start_x += 150
    
                mid_x = (start_x + end_x) / 2
                self.elements = [
                    cv.Path.MoveTo(start_x, start_y),
                    cv.Path.LineTo(mid_x, start_y),
                    cv.Path.LineTo(mid_x, end_y),
                    cv.Path.LineTo(end_x, end_y),
                ]
                
    async def rename_node_clicked(self, e: ft.Event):
        ''' Opens a dialog to rename the node or cancel '''
        return
        
        async def _rename_node(_):
                
            # Update the data
            for node in self.data.get('nodes', []):
                if node['label'] == old_label:
                    node['label'] = node_title.value
                    break
            for edge in self.data.get('edges', []):
                if edge['source'] == old_label:
                    edge['source'] = node_title.value
                elif edge['target'] == old_label:
                    edge['target'] = node_title.value
            self.update_data(**{'nodes': self.data.get('nodes', []), 'edges': self.data.get('edges', [])})

            # Update node on the stack
            for ctrl in self.node_stack.controls:
                if ctrl.label == old_label:
                    ctrl.label = node_title.value
                    ctrl.content.content.controls[0].content.controls[0].value = node_title.value
                    
                    ctrl.update()
                    break

                # Update node in the sidebar
                for ctrl in self.node_sidebar_column.controls:
                    if ctrl.data == old_label:
                        ctrl.data = node_title.value
                        ctrl.label = node_title.value
                        ctrl.update()
                        break


                self.page.pop_dialog()

        await self.story.close_menu()


    # Creates our node with given title if unique
    async def create_node(self, e: ft.Event[ft.Control]):

        # Default label
        node_label = f"Node {len(self.data.get('nodes', [])) + 1}"

        required_offset = str(e.control.data)
        locked_position = str(e.control.data) == "right_click"
        if required_offset.lower() == "sidebar":
            offset_amount = ((self.w - self.sidebar.width) / 2, 0)
        elif required_offset.lower() == "button":
            offset_amount = ((self.w / 2), (self.h / 2))
        else:       # If we right clicked, our locked pos should be accurate
            offset_amount = ((self.w / 2), (self.h / 2))


        # If from sidebar or button, 
        old_new_node_position = self.new_node_position  # Keep ref to old position to reset after
        self.new_node_position = (
            self.new_node_position[0] - offset_amount[0],
            self.new_node_position[1] - offset_amount[1]
        )
        # Use the locked position if we right clicked
        if locked_position:
            self.new_node_position = self.locked_new_node_position
        if self.new_node_position[0] < 100 or self.new_node_position[1] < 100:
            self.new_node_position = (
                max(100, self.new_node_position[0]), max(100, self.new_node_position[1])
            )
        elif self.new_node_position[0] > FIXED_STACK_WIDTH or self.new_node_position[1] > FIXED_STACK_HEIGHT:
            self.new_node_position = (min(FIXED_STACK_WIDTH, self.new_node_position[0]), min(FIXED_STACK_HEIGHT, self.new_node_position[1]))

        self.data['nodes'].append({
            'id': str(uuid.uuid4()),
            'label': node_label, 
            'position': self.new_node_position, 
            'color': app.settings.data.get('widget_defaults', {}).get('plot_chart', {}).get('node_color'), 
            'description': ""
        })
        self.update_data(**{'nodes': self.data['nodes']})

        # Add the node to the stack
        self.node_stack.controls.append(self.Node(widget=self, data=self.data.get('nodes')[-1]))

        # Add the node to the sidebar
        self.node_sidebar_column.controls.append(
            self.create_node_sidebar_ctrl(len(self.node_sidebar_column.controls), self.data.get('nodes')[-1])
        )

        self.update()
        self.new_node_position = old_new_node_position  # Reset node pos so we dont drift when adding multiple nodes from sidebar


    # Returns a sidebar control for a node
    def create_node_sidebar_ctrl(self, idx: int, node_data: dict) -> ft.TextField:
        async def update_node_description(e: ft.Event):
            node_id = e.control.data
            for node in self.data.get('nodes', []):
                if node.get('id') == node_id:
                    node['description'] = str(e.control.value)
                    break
            self.update_data(**{'nodes': self.data['nodes']})
            for node in self.node_stack.controls:
                if node.data.get('id') == node_id:
                    node.description_ctrl.value = str(e.control.value)
                    node.description_ctrl.update()
        return ft.TextField(
            value=node_data.get('description', ''),
            on_change=update_node_description,
            label=f"{node_data.get('label', f"Node {idx+1}")}",
            text_style=ft.TextStyle(italic=True, color=ft.Colors.ON_SURFACE_VARIANT, size=14),
            data=node_data.get('id'),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            multiline=True, dense=True, expand=True, border_radius=4,
            capitalization=ft.TextCapitalization.SENTENCES,
            label_style=ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=ft.Colors.PRIMARY)
        )


    def set_mouse_coords(self, e: ft.PointerEvent):
        self.new_node_position = (e.local_position.x, e.local_position.y)
        super().set_mouse_coords(e)

    def build(self):
        super().build()

        def get_new_node_menu_options() -> list[ft.Control]:
            async def _create_node(e: ft.Event):
                await self.create_node(e)
                await self.story.close_menu()
            self.locked_new_node_position = self.new_node_position

            async def _toggle_view_mode(e: ft.Event):
                await self.story.close_menu()
                self.data['spider_web_view'] = not self.data.get('spider_web_view', False)
                self.update_data(**{'spider_web_view': self.data.get('spider_web_view', False)})
                for edge in self.edge_canvas.shapes:
                    if isinstance(edge, self.Edge):
                        edge.draw_edge()
                        edge.update()
                self.update()

            return [
                MenuOptionStyle(
                    on_click=_create_node,
                    content=ft.Row([
                        ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY),
                        ft.Text("Node", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, expand=True), 
                    ]),
                    data="right_click"
                ),
                MenuOptionStyle(
                    on_click=_toggle_view_mode,
                    content=ft.Row([
                        ft.Icon(
                            ft.Icons.VERTICAL_DISTRIBUTE_OUTLINED if self.data.get('spider_web_view', False) == True else ft.Icons.SHOW_CHART,
                            ft.Colors.PRIMARY
                        ),
                        ft.Text("Toggle Connector View", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, expand=True), 
                    ], tooltip="Toggle between spider web connections and 3 line connections"),
                ),
            ]
            
        # Canvas to hold our edge lines between nodes
        self.edge_canvas = cv.Canvas(
            [],  
            content=ft.GestureDetector(
                ft.Container(
                    width=FIXED_STACK_WIDTH, height=FIXED_STACK_HEIGHT,
                    border=ft.Border.all(2, ft.Colors.OUTLINE_VARIANT),
                ),
                width=FIXED_STACK_WIDTH, height=FIXED_STACK_HEIGHT,
                on_hover=self.set_mouse_coords,
                on_secondary_tap=lambda: self.story.open_menu(get_new_node_menu_options()),
                hover_interval=40,
                data="right_click"
            ),
            width=FIXED_STACK_WIDTH, height=FIXED_STACK_HEIGHT
        )

        # Stack that holdes our nodes
        self.node_stack = ft.Stack([], width=FIXED_STACK_WIDTH, height=FIXED_STACK_HEIGHT)
        
        self.node_sidebar_column = ft.Column(
            [self.create_node_sidebar_ctrl(idx, node_data) for idx, node_data in enumerate(self.data.get('nodes', []))],
            tight=True, margin=ft.Margin.only(left=10, right=10)
        )

        # Info container on the right to show details of our edges and nodes
        self.sidebar_body.controls.extend([
            ft.Row([
                ft.Text(f"Nodes", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)),
                ft.IconButton(
                    ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                    ft.Colors.PRIMARY,
                    mouse_cursor=ft.MouseCursor.CLICK,
                    on_click=self.create_node,
                    data="sidebar",
                ),
            ], spacing=0),

            # Nodes here
            self.node_sidebar_column,
            
            self.sidebar_notes_label,
            self.sidebar_notes_column

        ])
            
        
            
        # Add our nodes and edges to the stack/canvas
        for node_data in self.data.get('nodes', []):
            self.node_stack.controls.append(
                self.Node(
                    self, 
                    node_data
                )
            )

        

        # Go through and draw our edges on the canvas
        for edge in self.data.get('edges', []):
            self.edge_canvas.shapes.append(self.Edge(self, edge))
        

        # Interactive viewer to hold the stack for UI manipulation
        self.iv = ft.InteractiveViewer(
            content=ft.Stack([      # Hold the edge canvas and node stack
                ft.Container(
                    image=ft.DecorationImage("flow_chart_background.png", repeat=ft.ImageRepeat.REPEAT),
                    expand=True, border_radius=4
                ),
                self.edge_canvas,
                self.node_stack, 
            ], width=FIXED_STACK_WIDTH, height=FIXED_STACK_HEIGHT),
            expand=3, 
            constrained=False,
            scale_factor=800, boundary_margin=1500,
            min_scale=0.02, max_scale=3.0,
        )

        self.add_node_button = ft.Button(
            "Add Node", 
            on_click=self.create_node, 
            data="button",
            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, text_style=ft.TextStyle(weight=ft.FontWeight.W_500, size=20)),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            visible=not self.data.get('show_sidebar', False),
            bottom=10, right=0,
        )
        

        viewer_stack = ft.Stack([
            
            self.iv,
            #self.add_node_button
        ], expand=3)

        

        # Set up our main conent
        self.content = ft.Stack([
            self.iv,
            ft.Row(
                [self.toggle_sidebar_visibility_button, self.sidebar], 
                spacing=0, expand=True, alignment=ft.MainAxisAlignment.END, 
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )
        ], expand=True, alignment=ft.Alignment.CENTER_RIGHT)

        #self.page.run_task(self.iv.pan, -FIXED_STACK_WIDTH / 4, -FIXED_STACK_HEIGHT / 4, 0)  # Center the view on the stack

        # TODO: Add spider web view
        # In sidebar, show sequence of events like plotline