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
from constants import FIXED_STACK_WIDTH, FIXED_STACK_HEIGHT, FIXED_STACK_PADDING
import uuid
from styles.text_fields import NoLabelTextField
import flet_shadcn_ui as shad
import math


NODE_STACK_PADDING = 200
NODE_WIDTH = 200
NODE_HEIGHT = 200

CONNECTOR_WIDTH = 16
CONNECTOR_HEIGHT = 30

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

                'view_mode': app.settings.data.get('widget_defaults', {}).get('plot_chart', {}).get('view_mode', False),   # If the plot chart is in spider web view or not

                'nodes': [],
                  # List of all our Nodes/events
                    #{'label': "", 'description': "", 'position': (100, 100), 'color': '#FFFFFF'}
                 
                'edges': [    # List of all our Links/Connections between nodes
                    #{'source': "", 'target': ""}
                ] 
            },
        )

        # State and management
        self.new_node_position = (NODE_STACK_PADDING, NODE_STACK_PADDING)     # Position we place new nodes
        self.edge_canvas: cv.Canvas           # Canvas that holds our edges (cv.shapes)
        self.node_stack: ft.Stack           # Stack that holds our nodes (gesture detectors)

        # State trackers
        self.source_node: str = None        # Tracks which node we are dragging from when creating a new edge
        self.target_node: str = None        # Tracks which node we are dragging to when creating a new edge


    # Class for handling all node logic
    class Node(ft.GestureDetector):

        def __init__(self, widget: 'PlotChart',  data: dict={}):

            # Initialize node properties
            self.widget = widget
            position = data.get('position', (NODE_STACK_PADDING, NODE_STACK_PADDING))

            self.highlight_ctrl: ft.Container = ft.Container()

            super().__init__(
                left=position[0],
                top=position[1],
                width=NODE_WIDTH, height=NODE_HEIGHT,
                data=data,
                on_enter=self.handle_enter_node, 
                on_exit=self.handle_exit_node,
                offset=ft.Offset(-0.5, -0.5),   # So we sit in the middle of our actual position
                animate_position=ft.Animation(250, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            )

        def handle_enter_node(self, e=None):
            ''' Highlight the node when mouse enters it and set it correctly '''
            if self.widget.source_node:
                self.highlight_ctrl.shadow = ft.BoxShadow(5, 10, ft.Colors.with_opacity(0.25, ft.Colors.ON_SURFACE))
                self.highlight_ctrl.update()
                self.widget.target_node = self.data.get('id', '')
            

        def handle_exit_node(self, e=None):
            ''' Remove the highlight from the node when mouse exits it, and unmark us as a target '''
            if self.widget.target_node == self.data.get('id', ''):
                self.widget.target_node = None
            self.highlight_ctrl.shadow = None
            self.highlight_ctrl.update()
            

        # Moves the node on the stack and updates the drawing that connects the edges
        async def move_node(self, e: ft.DragUpdateEvent):
            
            # Update us visually
            self.left += e.local_delta.x
            self.top += e.local_delta.y

            # Clamp
            if self.left < FIXED_STACK_PADDING:
                self.left = FIXED_STACK_PADDING
            elif self.left > FIXED_STACK_WIDTH - FIXED_STACK_PADDING - NODE_WIDTH:
                self.left = FIXED_STACK_WIDTH - FIXED_STACK_PADDING - NODE_WIDTH
            if self.top < NODE_STACK_PADDING:
                self.top = NODE_STACK_PADDING
            elif self.top > FIXED_STACK_HEIGHT - 50:
                self.top = FIXED_STACK_HEIGHT - 50
            self.update()
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
            await self.title_tf.focus()

        # Opens a menu with our options when right clicking a node
        def node_menu_options(self) -> list[shad.MenuItem]:
            
            return [
                shad.MenuItem(
                    on_click=self.delete_clicked,
                    content="Delete Node",
                    leading=ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, ft.Colors.ERROR, size=20),
                )
            ] 


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

            self.widget.update()

        # Builds our node
        def build(self):
            
            def handle_enter_connector(e: ft.PointerEvent[ft.GestureDetector]):
                ''' Highlight the connector when we enter it, and set it as the target node if we're dragging from another node.'''
                if self.widget.source_node:   
                    self.widget.target_node = e.control.data

                # Visual highlight
                e.control.content.shadow = ft.BoxShadow(10, 20, ft.Colors.with_opacity(0.25, ft.Colors.ON_SURFACE))
                e.control.update()
            def handle_exit_connector(e: ft.PointerEvent[ft.GestureDetector]):
                ''' Set us as not the target node and stop highlighting'''
                self.widget.target_node = None
                e.control.content.shadow = None
                e.control.update()
                self.handle_enter_node()    # Call enter to re-set the state tracking if we are dragging

            # Creates our new edge (link) between nodes
            def _create_new_edge(e: ft.PointerEvent[ft.GestureDetector]):
                
                # Remove our visual feedback
                self.page.overlay.pop()
                self.page.update()

                # If its an incomplete edge (we didn't end on another node), reset and exit
                if not self.widget.source_node or not self.widget.target_node:
                    self.widget.source_node = None
                    self.widget.target_node = None
                    handle_exit_connector(e)   # Stops the highlight
                    return  
                
                # Don't allow connections to self
                if self.widget.source_node == self.widget.target_node:    # Don't allow connections to self
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

                # Re-render page to show new edge
                handle_exit_connector(e)   # Stops the highlight

                # Add edge to the canvas
                self.widget.edge_canvas.shapes.append(
                    self.widget.Edge(
                        self.widget,
                        self.widget.data.get('edges')[-1]
                    )
                )
                self.widget.edge_canvas.update()

                

            # Update our state trackers for new edges and show visual feedback
            async def start_new_edge(e: ft.PointerEvent[ft.Control]):
                self.widget.source_node = e.control.data
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

            def _save_title(e: ft.Event[ft.TextField]):
                for node_data in self.widget.data.get('nodes', []):
                    if node_data.get('id', '') == self.data.get('id', ''):
                        node_data['label'] = e.control.value
                        break
                self.widget.update_data(**{'nodes': self.widget.data.get('nodes', [])})

  
            # Saves the description for this node when the text field loses focus
            async def _save_description(e: ft.Event[ft.TextField]):
                for node_data in self.widget.data.get('nodes', []):
                    if node_data.get('id', '') == self.data.get('id', ''):
                        node_data['description'] = e.control.value
                        break
                self.widget.update_data(**{'nodes': self.widget.data.get('nodes', [])})

            # Returns a connectino point for each side of the node
            def build_connector(side: str = "left"):
                return ft.GestureDetector(
                    ft.Container(
                        ft.Icon(
                            ft.Icons.KEYBOARD_ARROW_LEFT_OUTLINED if side == "right" else ft.Icons.KEYBOARD_ARROW_RIGHT_OUTLINED, 
                            ft.Colors.PRIMARY, size=CONNECTOR_WIDTH - 2,
                        ), 
                        height=CONNECTOR_HEIGHT, width=CONNECTOR_WIDTH, border=ft.Border.all(1, color=ft.Colors.OUTLINE),
                        border_radius=40, bgcolor=ft.Colors.GREY_700,
                    ), 
                    mouse_cursor=ft.MouseCursor.PRECISE,
                    data=self.data.get('id'),                        
                    on_enter=handle_enter_connector,  
                    on_pan_start=start_new_edge,   
                    on_pan_update=_update_line,   
                    on_pan_end=_create_new_edge,  
                    on_exit=handle_exit_connector,  
                    drag_interval=20,
                    left=0 if side == "left" else None,
                    right=0 if side == "right" else None,
                )


            # Text field for editing the node's description
            self.description_ctrl = SmallTextField(
                self.data.get('description', ''),
                expand=True, 
                on_blur=_save_description,
                enable_interactive_selection=False
            )

            self.title_tf = NoLabelTextField(
                value=self.data.get('label', ''),
                on_blur=_save_title,
                text_align=ft.TextAlign.CENTER,
                margin=ft.Margin.only(top=12),
            )

            self.highlight_ctrl = ft.Container(
                expand=True, #shadow=ft.BoxShadow(0, 1, blur_style=ft.BlurStyle.OUTER),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                border_radius=8, 
                padding=ft.Padding.only(top=0, bottom=8, left=8, right=8),
                alignment=ft.Alignment.TOP_CENTER,
                left=CONNECTOR_WIDTH / 2, right=CONNECTOR_WIDTH / 2, top=0, bottom=0,
                content=ft.Column([
                    self.title_tf,      # Title text field
                    ft.Divider(ft.Colors.SURFACE_CONTAINER_LOW, 2),     # Divider between title and description
                    self.description_ctrl,  # Description text field
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
            )

            drag_handle = ft.GestureDetector(     # GD for moving the node via pan events
                ft.Icon(ft.Icons.REMOVE, ft.Colors.OUTLINE),
                on_pan_update=self.move_node,
                on_pan_end=self.save_position,
                mouse_cursor=ft.MouseCursor.MOVE,
                drag_interval=20,
                top=0, 
                offset=ft.Offset(0, -0.25)
            )

            # Our nodes content. Column with label, divider, description text field, and connection points
            self.content = shad.ContextMenu(
                items=self.node_menu_options(),
                content=ft.Stack(   # Stack to hold our connectors and node
                    alignment=ft.Alignment.CENTER, clip_behavior=ft.ClipBehavior.NONE,
                    controls=[
                        self.highlight_ctrl,
                        drag_handle,
                        build_connector("left"),
                        build_connector("right"),
                    ]
                ),
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

            # Go find our start and end position based on the node data
            for node_data in self.widget.data.get('nodes', []):
                if node_data.get('id') == self.source_node:
                    self.start_position = node_data.get('position', (0, 0))
                elif node_data.get('id') == self.target_node:
                    self.end_position = node_data.get('position', (0, 0))

            # Catch errors
            if not self.start_position or not self.end_position:
                return

            # Unpack into local vars so we don't mutate the stored tuples
            start_x, start_y = self.start_position
            end_x, end_y = self.end_position

            # Straight edges between nodes
            if self.widget.data.get('view_mode', '') == "straight":
                # Adjust for in/out nodes
                if start_x < end_x:
                    start_x += NODE_WIDTH / 2
                    end_x -= NODE_WIDTH / 2
                else:
                    end_x += NODE_WIDTH / 2
                    start_x -= NODE_WIDTH / 2
                     
                self.elements = [
                    cv.Path.MoveTo(start_x, start_y),
                    cv.Path.LineTo(end_x, end_y),
                ]

            # ZigZags between nodes
            elif self.widget.data.get('view_mode', '') == "zigzag":
                mid_x = (start_x + end_x) / 2
                self.elements = [
                    cv.Path.MoveTo(start_x, start_y),
                    cv.Path.LineTo(mid_x, start_y),
                    cv.Path.LineTo(mid_x, end_y),
                    cv.Path.LineTo(end_x, end_y),
                ]

            # Curved edges between nodes
            else:
                direction = 1 if start_x < end_x else -1
                start_x += direction * NODE_WIDTH / 2
                end_x -= direction * NODE_WIDTH / 2
                handle_length = max(abs(end_x - start_x) / 2, CONNECTOR_WIDTH)
                self.elements = [
                    cv.Path.MoveTo(start_x, start_y),
                    cv.Path.CubicTo(
                        start_x + direction * handle_length, start_y,
                        end_x - direction * handle_length, end_y,
                        x=end_x, y=end_y
                    ),
                ]


    # Creates our node with given title if unique
    async def create_node(self, e: ft.Event[ft.Control]):

        # Default label
        node_label = f"Node {len(self.data.get('nodes', [])) + 1}"

        # Clamp
        if self.new_node_position[0] < FIXED_STACK_PADDING:
            self.new_node_position = (FIXED_STACK_PADDING, self.new_node_position[1])
        elif self.new_node_position[0] > FIXED_STACK_WIDTH - FIXED_STACK_PADDING - NODE_WIDTH:
            self.new_node_position = (FIXED_STACK_WIDTH - FIXED_STACK_PADDING - NODE_WIDTH, self.new_node_position[1])
        if self.new_node_position[1] < NODE_STACK_PADDING:
            self.new_node_position = (self.new_node_position[0], NODE_STACK_PADDING)
        elif self.new_node_position[1] > FIXED_STACK_HEIGHT - 50:
            self.new_node_position = (self.new_node_position[0], FIXED_STACK_HEIGHT - 50)
        

        self.data['nodes'].append({
            'id': str(uuid.uuid4()),
            'label': node_label, 
            'position': self.new_node_position, 
            'description': ""
        })
        self.update_data(**{'nodes': self.data['nodes']})

        # Add the node to the stack
        self.node_stack.controls.append(self.Node(widget=self, data=self.data.get('nodes')[-1]))

        self.update()


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
            multiline=True, dense=True, expand=True, 
            border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.TRANSPARENT), border_radius=4),
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

            async def set_highlight_connector(e: ft.Event[shad.MenuItem]):
                highlight_connector = e.control.data
                self.update_data(**{'view_mode': highlight_connector})
                for edge in self.edge_canvas.shapes:
                    if isinstance(edge, self.Edge):
                        edge.draw_edge()
                        edge.update()
                self.update()

            return [
                shad.MenuItem(
                    "New Node",
                    leading=ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY, size=20),
                    on_click=_create_node,
                    #data="right_click"
                ),
                shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
                ft.Row([ft.Text(f"Views", italic=True)], alignment=ft.MainAxisAlignment.CENTER, margin=ft.Margin.only(bottom=4)),

                shad.MenuItem(
                    "Curved", data="curved",
                    leading=ft.Icon(ft.Icons.GESTURE, ft.Colors.PRIMARY, size=20),
                    on_click=set_highlight_connector,
                ),
                shad.MenuItem(
                    "ZigZag", data="zigzag",
                    leading=ft.Icon(ft.Icons.SHOW_CHART, ft.Colors.PRIMARY, size=20),
                    on_click=set_highlight_connector,
                ),
                shad.MenuItem(
                    "Straight", data="straight",
                    leading=ft.Icon(ft.Icons.VERTICAL_DISTRIBUTE_OUTLINED, ft.Colors.PRIMARY, size=20),
                    on_click=set_highlight_connector,
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
                hover_interval=40,
                data="right_click"
            ),
            width=FIXED_STACK_WIDTH, height=FIXED_STACK_HEIGHT
        )

        # Stack that holdes our nodes
        self.node_stack = ft.Stack([], width=FIXED_STACK_WIDTH, height=FIXED_STACK_HEIGHT)

        self.sidebar_notes_label.margin = None

        # Info container on the right to show details of our edges and nodes
        self.sidebar_body.controls.extend([
            self.sidebar_notes_label,
            self.sidebar_notes_column
        ])
            
            
        # Add our nodes and edges to the stack/canvas
        for node_data in self.data.get('nodes', []):
            self.node_stack.controls.append(self.Node(self, node_data))


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
            on_interaction_end=self.handle_iv_transform
        )

        # Set up our main conent
        self.content = ft.Stack([
            shad.ContextMenu(
                ft.Container(width=FIXED_STACK_WIDTH, height=FIXED_STACK_HEIGHT),
                get_new_node_menu_options(),
                open_on_long_press=True,
                expand=True
            ),
            ft.TransparentPointer(self.iv),
            ft.Row(
                [self.toggle_sidebar_visibility_button, self.sidebar], 
                spacing=0, expand=True, alignment=ft.MainAxisAlignment.END, 
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )
        ], expand=True, alignment=ft.Alignment.CENTER_RIGHT)

    def did_mount(self):
        return
        self.page.run_task(self.transform_iv)