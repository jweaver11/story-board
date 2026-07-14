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

class PlotChart(Widget):

    # Constructor
    def __init__(self, title: str, directory_path: str, story: Story, data: dict = None, is_new: bool = False):

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

                'spider_web_view': False,

                'nodes': [],
                  # List of all our Nodes/events
                    #{'label': "", 'description': "", 'position': (100, 100), 'color': '#FFFFFF'}
                 
                'edges': [    # List of all our Links/Connections between nodes
                    #{'source': "", 'target': ""}
                ] 
            },
        )

        # State and management
        self.new_node_position = (100, 100)     # Position we place new nodes
        self.edge_canvas: cv.Canvas           # Canvas that holds our edges (cv.shapes)
        self.node_stack: ft.Stack           # Stack that holds our nodes (gesture detectors)
        self.node_sidebar_column: ft.Column
        self.edge_sidebar_column: ft.Column

        # State trackers
        self.source_node: str = None        # Tracks which node we are dragging from when creating a new edge
        self.target_node: str = None        # Tracks which node we are dragging to when creating a new edge
        self.source_side: str = None      # Determines which sides of the nodes we start dragging from
        self.target_side: str = None       # Determines which sides of the nodes we end dragging on

    # Class for handling all node logic
    class Node(ft.GestureDetector):

        def __init__(self, widget: 'PlotChart', label: str, description: str="", position: tuple=tuple(), color: str="white"):

            # Initialize node properties
            self.label = label
            self.color = color
            self.widget = widget
            self.description = description

            super().__init__(
                left=position[0],
                top=position[1],
                width=150, 
                offset=ft.Offset(0, -1),
                animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
                on_secondary_tap=self.open_menu,
                on_hover=self.widget.set_mouse_coords,
            )

        # Moves the node on the stack and updates the drawing that connects the edges
        async def move_node(self, e: ft.DragUpdateEvent):
            # Update data
            for node in self.widget.data.get('nodes', []):
                if node['label'] == self.label:
                    node['position'] = (self.left, self.top)
                    break
            # Update us visually
            self.left += e.local_delta.x
            self.top += e.local_delta.y
            self.update()
            # Redraw any relevant edges
            for edge in self.widget.edge_canvas.shapes:
                if isinstance(edge, self.widget.Edge) and (edge.source_node == self.label or edge.target_node == self.label):
                    edge.draw_edge()   
                    edge.update()

        # Saves our new position when we are done dragging
        async def save_position(self):
            # Make sure data is accurate
            for node in self.widget.data.get('nodes', []):
                if node['label'] == self.label:
                    node['position'] = (self.left, self.top)
                    break
            self.widget.update_data(**{'nodes': self.widget.data.get('nodes', [])})

        # Opens a menu with our options when right clicking a node
        async def open_menu(self, e: ft.PointerEvent):
            menu_options = [
                MenuOptionStyle(
                    on_click=self.widget.rename_node_clicked,
                    content=ft.Row([
                        ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, self.color,),
                        ft.Text(
                            "Rename", 
                            weight=ft.FontWeight.BOLD, 
                            
                        ), 
                    ]),
                    data=self.label
                ),
                MenuOptionStyle(
                    ft.SubmenuButton(
                        ft.Row([
                            ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.color), 
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
                if node['label'] == self.label:
                    self.widget.data['nodes'].pop(idx)
                    self.widget.node_stack.controls.pop(idx)
                    break
            # Remove any edges connected to the node from data and canvas
            self.widget.data['edges'] = [
                edge for edge in self.widget.data.get('edges', [])
                if edge['source'] != self.label and edge['target'] != self.label
            ]
            self.widget.edge_canvas.shapes = [
                shape for shape in self.widget.edge_canvas.shapes
                if not (isinstance(shape, self.widget.Edge) and (shape.source_node == self.label or shape.target_node == self.label))
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
                self.color = color

                for node in self.widget.data.get('nodes', []):
                    if node['label'] == self.label:
                        node['color'] = color
                        break
                self.widget.update_data(**{'nodes': self.widget.data.get('nodes', [])})

                self.content.content.controls[3].controls[0].content.content.color = color
                self.content.content.controls[3].controls[1].content.content.color = color
                self.update()
                
                for ctrl in self.widget.edge_sidebar_column.controls:
                    if ctrl.spans[0].text == self.label:
                        ctrl.spans[0].style.color = color
                        ctrl.update()
                        break
                    elif ctrl.spans[2].text == self.label:
                        ctrl.spans[2].style.color = color
                        ctrl.update()
                        break
                    
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
                    self.widget.target_node = e.control.data.get('label')
                    self.widget.target_side = e.control.data.get('side')

                # Visual highlight
                e.control.content.shadow = ft.BoxShadow(8, 8, ft.Colors.with_opacity(0.6, self.color))
                e.control.update()
            async def _stop_highlight_node(e: ft.PointerEvent):
                # Reset state trackers
                self.widget.target_node = None
                self.widget.target_side = None
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
                    self.widget.source_side = None
                    self.widget.target_side = None
                    await _stop_highlight_node(e)   # Stops the highlight
                    return  
                
                # Don't allow connections from the same side of the node, as that wouldnt make sense
                elif self.widget.source_side == self.widget.target_side:   
                    self.widget.source_node = None
                    self.widget.target_node = None
                    self.widget.source_side = None
                    self.widget.target_side = None
                    await _stop_highlight_node(e)   # Stops the highlight
                    self.page.show_dialog(SnackBar("Cannot connect from the same side of the node."))
                    return
                
                # Don't allow connections to self
                if self.widget.source_node == self.widget.target_node:    # Don't allow connections to self
                    self.page.show_dialog(SnackBar("Cannot connct a node to itself."))
                    return  
                
                # If the edge already exists, delete it
                for edge in self.widget.data.get('edges', []):
                    if (edge['source'] == self.widget.source_node and edge['target'] == self.widget.target_node) or (edge['source'] == self.widget.target_node and edge['target'] == self.widget.source_node):
                        edge_data = self.widget.data.get('edges', [])[-1]
                        self.widget.data['edges'].remove(edge)
                        self.widget.needs_file_write = True
                        # Reset state trackers
                        self.widget.source_node = None
                        self.widget.target_node = None
                        self.widget.source_side = None
                        self.widget.target_side = None
                        # Reload
                        source_node = edge_data['source']
                        target_node = edge_data['target']

                        # Remove from edge canvas
                        for edge in self.widget.edge_canvas.shapes:
                            if edge.source_node == source_node and edge.target_node == target_node:
                                self.widget.edge_canvas.shapes.remove(edge)
                                print("Removing edge from canvas")
                                break
                            if edge.source_node == target_node and edge.target_node == source_node:
                                self.widget.edge_canvas.shapes.remove(edge)
                                print("Removing edge from canvas")
                                break

                        for ctrl in self.widget.edge_sidebar_column.controls:
                            if ctrl.spans[0].text == source_node or ctrl.spans[0].text == target_node and ctrl.spans[2].text == source_node or ctrl.spans[2].text == target_node:
                                self.widget.edge_sidebar_column.controls.remove(ctrl)
                                print("Removing sidebar edge")
                                break
                            

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
                self.widget.source_side = None
                self.widget.target_side = None

                # Re-render page to show new edge
                await _stop_highlight_node(e)   # Stops the highlight

                # Add edge to the canvas
                self.widget.edge_canvas.shapes.append(
                    self.widget.Edge(
                        self.widget,
                        self.widget.data.get('edges')[-1]
                    )
                )

                self.widget.edge_sidebar_column.controls.append(
                    self.widget.create_edge_sidebar_ctrl(
                        self.widget.data.get('edges')[-1]
                    )
                )
                self.widget.update()

                

            # Update our state trackers for new edges and show visual feedback
            async def start_new_edge(e: ft.PointerEvent):
                
                self.widget.source_node = e.control.data.get('label')
                self.widget.source_side = e.control.data.get('side')
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

            # Saves the description for this node when the text field loses focus
            async def _save_description(e: ft.Event):
                for node in self.widget.data.get('nodes', []):
                    if node['label'] == self.label:
                        node['description'] = e.control.value
                        break
                self.widget.update_data(**{'nodes': self.widget.data.get('nodes', [])})

                for ctrl in self.widget.node_sidebar_column.controls:
                    if ctrl.data == node['label']:
                        ctrl.value = e.control.value
                        ctrl.update()
                        break

            # Text field for editing the node's description
            self.description_ctrl = SmallTextField(
                self.description, 
                expand=True,  on_change=_save_description,
            )

            # Our nodes content. Column with label, divider, description text field, and connection points
            self.content = ft.Container(
                ft.Column([
                    ft.GestureDetector(
                        ft.Row([ft.Text(self.label, expand=True,  weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER)], alignment=ft.MainAxisAlignment.CENTER),
                        on_pan_update=self.move_node,
                        on_pan_end=self.save_position,
                        mouse_cursor=ft.MouseCursor.MOVE,
                        #drag_interval=50,
                    ),
                    ft.Divider(ft.Colors.SURFACE_CONTAINER_LOW, 2),
                    self.description_ctrl,
                    ft.Row([
                        ft.GestureDetector(
                            ft.Container(ft.Icon(ft.Icons.CIRCLE_OUTLINED, self.color, scale=1.25), shape=ft.BoxShape.CIRCLE), 
                            mouse_cursor=ft.MouseCursor.PRECISE,
                            data={'label': self.label, 'side': "left"},                            
                            on_enter=_highlight_node,   # Highlight and set target source trackers if we enter a node while dragging from another
                            on_pan_start=start_new_edge,   # Show line to follow mouse
                            on_pan_update=_update_line,   # Update line to follow mouse
                            on_pan_end=_create_new_edge,  
                            on_exit=_stop_highlight_node,  
                        ),
                        ft.GestureDetector(
                            ft.Container(ft.Icon(ft.Icons.CIRCLE_OUTLINED, self.color, scale=1.25), shape=ft.BoxShape.CIRCLE), 
                            mouse_cursor=ft.MouseCursor.PRECISE,
                            data={'label': self.label, 'side': "right"},                        
                            on_enter=_highlight_node,  
                            on_pan_start=start_new_edge,   
                            on_pan_update=_update_line,   
                            on_pan_end=_create_new_edge,  
                            on_exit=_stop_highlight_node,  
                        ),
                        
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                expand=True, shadow=ft.BoxShadow(1, 1, blur_style=ft.BlurStyle.OUTER),
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
                if node['label'] == self.source_node:
                    self.start_position = node.get('position', (0, 0))
                elif node['label'] == self.target_node:
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

            # Adjust for in/out nodes
            if start_x > end_x:
                end_x += 150
            else:
                start_x += 150

            mid_x = (start_x + end_x) / 2

            # Straight edges between nodes
            if self.widget.data.get('spider_web_view', False):
                self.elements = [
                    cv.Path.MoveTo(start_x, start_y),
                    cv.Path.LineTo(end_x, end_y),
                ]

            # Three-node turns
            else:
                self.elements = [
                    cv.Path.MoveTo(start_x, start_y),
                    cv.Path.LineTo(mid_x, start_y),
                    cv.Path.LineTo(mid_x, end_y),
                    cv.Path.LineTo(end_x, end_y),
                ]
                
    async def rename_node_clicked(self, e: ft.Event):
        ''' Opens a dialog to rename the node or cancel '''

        # Checks that node title is unique
        async def _check_node_title(title: str) -> bool:
            for node in self.data.get('nodes', []):
                if node['label'] == title and title != old_label:   # Allow the same title if it's the same node
                    node_title.error = "Node label taken"
                    node_title.update()
                    return False
            return True
        
        async def _rename_node(_):
            if not node_title.value:
                node_title.error = "Node must have a label"
                node_title.update()
                await node_title.focus()
                return
            
            if old_label == node_title.value:
                self.page.pop_dialog()
                return

            # If the title is unique, we start renaming
            if await _check_node_title(node_title.value):
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

                # Update edge labels in the sidebar
                for ctrl in self.edge_sidebar_column.controls:
                    for span in ctrl.spans:
                        if span.text == old_label:
                            span.text = node_title.value
                    ctrl.update()


                self.page.pop_dialog()

        await self.story.close_menu()

        old_label = e.control.data

        node_title = ft.TextField(
            old_label, hint_text="Node Label", capitalization=ft.TextCapitalization.SENTENCES, 
            autofocus=True, on_submit=_rename_node, multiline=False
        )

        self.page.show_dialog(
            ft.AlertDialog(
                title="Rename Node",
                content=node_title,
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog(), style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.ERROR)),
                    ft.TextButton("Rename", on_click=_rename_node, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK))
                ]
            )
        )
        
    
    # Shows our textfield for creating a new node
    async def create_node_clicked(self, e: ft.Event=None):
        self.add_node_button.visible = False
        self.add_node_button.update()
        self.new_node_tf.value = ""
        self.new_node_tf.visible = True
        self.new_node_tf.label = "New node Label"
        self.new_node_tf.update() 
        await self.new_node_tf.focus()

    # Creates our node with given title if unique
    async def create_node(self, e: ft.Event=None):
        # Checks that node title is unique
        async def _check_node_title(title: str) -> bool:
            for node in self.data.get('nodes', []):
                if node['label'] == title:
                    self.new_node_tf.error = "Node label taken"
                    self.new_node_tf.update()
                    return False
            return True

        if not self.new_node_tf.value:
            self.new_node_tf.error = "Node must have a label"
            self.new_node_tf.update()
            await self.new_node_tf.focus()
            return

        if await _check_node_title(self.new_node_tf.value):

            # Check if we're creating from the info column, and just put the new node in the center
            if e.control.data is not None:
                self.new_node_position = (self.w / 2 * .75, self.h / 2) # Center of widget when showing info

            title = self.new_node_tf.value if self.new_node_tf.value else "Node"
            self.data['nodes'].append({'label': title, 'position': self.new_node_position, 'color': '#FFFFFF', 'description': ""})
            self.update_data(**{'nodes': self.data['nodes']})

            # Add the node to the stack
            self.node_stack.controls.append(
                self.Node(
                    widget=self,
                    label=title,
                    position=self.new_node_position,
                    color='#FFFFFF',
                )
            )

            # Add the node to the sidebar
            self.node_sidebar_column.controls.append(
                self.create_node_sidebar_ctrl(len(self.node_sidebar_column.controls), self.data.get('nodes')[-1])
            )

            self.update()

            self.page.pop_dialog()
            self.new_node_position = (self.w / 2 * .75, self.h / 2) # Reset new node position to default for next time

    # Returns a sidebar control for a node
    def create_node_sidebar_ctrl(self, idx: int, node_data: dict) -> ft.TextField:
        async def update_node_description(e: ft.Event):
            node_label = e.control.data
            for node in self.data.get('nodes', []):
                if node['label'] == node_label:
                    node['description'] = str(e.control.value)
                    break
            self.update_data(**{'nodes': self.data['nodes']})
            for node in self.node_stack.controls:
                if node.label == node_label:
                    node.description_ctrl.value = str(e.control.value)
                    node.description_ctrl.update()
        return ft.TextField(
            value=node_data.get('description', ''),
            on_change=update_node_description,
            label=f"{node_data.get('label', f"Node {idx+1}")}",
            text_style=ft.TextStyle(italic=True, color=ft.Colors.ON_SURFACE_VARIANT, size=14),
            data=node_data.get('label', f"Node {idx+1}"),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            multiline=True, dense=True, expand=True, border_radius=4,
            capitalization=ft.TextCapitalization.SENTENCES,
            label_style=ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=ft.Colors.PRIMARY)
        )
    
    def create_edge_sidebar_ctrl(self, edge_data: dict) -> ft.Text:
        # Grab nodes colors. order them by x
        source_node = None
        target_node = None
        for node in self.data.get('nodes', []):
            if node['label'] == edge_data['source']:
                source_node = node
            elif node['label'] == edge_data['target']:
                target_node = node

        if source_node is None or target_node is None:
            print("Invalid Nodes: ", edge_data['source'], edge_data['target'])
            return ft.Text("Invalid edge")
            
        # Grab source and target label and colors
        if source_node.get('position', (0, 0))[0] <= target_node.get('position', (0, 0))[0]:  # If x_source is left of x_target
            source_node_label = source_node.get('label', edge_data['source'])
            target_node_label = target_node.get('label', edge_data['target'])
            source_color = source_node.get('color', ft.Colors.ON_SURFACE)
            target_color = target_node.get('color', ft.Colors.ON_SURFACE)
        else:       # If x_source is right of x_target, swap them
            source_node_label = target_node.get('label', edge_data['target'])
            target_node_label = source_node.get('label', edge_data['source'])
            source_color = target_node.get('color', ft.Colors.ON_SURFACE)
            target_color = source_node.get('color', ft.Colors.ON_SURFACE)

        return ft.Text(
            spans=[
                ft.TextSpan(source_node_label, style=ft.TextStyle(color=source_color, weight=ft.FontWeight.W_500,)),
                ft.TextSpan(" ➜ ", style=ft.TextStyle(color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.W_500,)),
                ft.TextSpan(target_node_label, style=ft.TextStyle(color=target_color, weight=ft.FontWeight.W_500,))
            ],
        )

    # Show sidebar hides the button since it also exists in sidebar
    async def show_sidebar(self, e: ft.Event=None):
        self.add_node_button.visible = False
        self.add_node_button.update()
        await super().show_sidebar(e)

    # Hiding shows the add node button
    async def hide_sidebar(self, e: ft.Event=None):
        self.add_node_button.visible = True
        self.add_node_button.update()
        await super().hide_sidebar(e)

    # Redraws all edges on the canvas, useful after nodes have moved or been updated
    #def reload_edges(self):
        #for edge in self.edge_canvas.shapes:
            #edge.draw_edge()
        #self.edge_canvas.update()

    def build(self):
        super().build()
        
        # Sets our canvas coords for when we're creating a new node by right clicking
        async def set_canvas_coords(e: ft.HoverEvent):
            self.new_node_position = (e.local_position.x, e.local_position.y)
            self.story.mouse_x = e.global_position.x
            self.story.mouse_y = e.global_position.y    

        # Hides the new node tf after we submit or cancel adding a new node
        async def hide_new_node_tf(e: ft.Event=None):
            self.new_node_tf.visible = False
            self.new_node_tf.update()
            if not self.sidebar.visible:
                self.add_node_button.visible = True
                self.add_node_button.update()
        
        # Canvas to hold our edge lines between nodes
        self.edge_canvas = cv.Canvas(
            [],  
            content=ft.GestureDetector(
                content=ft.Container(
                    #image=ft.DecorationImage("dark_mode_transparent_background.jpg", fit=ft.BoxFit.FILL),
                    width=5000, height=3000,
                    border=ft.Border.all(2, ft.Colors.OUTLINE),
                ),
                width=5000, height=3000,
                on_hover=set_canvas_coords,
                hover_interval=30,
            ),
            width=5000, height=3000
        )

        # Stack that holdes our nodes
        self.node_stack = ft.Stack([], width=5000, height=3000)

        
        
        # Load all our edges into controls
        def _load_edges() -> ft.Column:

            controls = []
            for edge_data in self.data.get('edges', []):

                

                # Source -> Target
                controls.append(
                    self.create_edge_sidebar_ctrl(edge_data)
                )
            return ft.Column(controls, tight=True, margin=ft.Margin.only(left=10, right=10))
        
        self.node_sidebar_column = ft.Column(
            [self.create_node_sidebar_ctrl(idx, node_data) for idx, node_data in enumerate(self.data.get('nodes', []))],
            tight=True, margin=ft.Margin.only(left=10, right=10)
        )
        self.edge_sidebar_column = _load_edges()

        # Info container on the right to show details of our edges and nodes
        info_column = ft.Column(
            [
                self.description_tf,
                ft.Row([
                    ft.Text(f"\tNodes", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),
                    ft.IconButton(
                        ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                        self.data.get('color', ft.Colors.PRIMARY),
                        mouse_cursor=ft.MouseCursor.CLICK,
                        on_click=self.create_node_clicked,
                        data="ignore_position"
                    ),
                ], spacing=0),

                # Nodes here
                self.node_sidebar_column,
                ft.Divider(),
                ft.Text(f"\tConnections", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),

                self.edge_sidebar_column,

                
            ], 
            expand=True, scroll="auto", spacing=0,
        )
            
        
            
        # Add our nodes and edges to the stack/canvas
        for node in self.data.get('nodes', []):
            self.node_stack.controls.append(
                self.Node(
                    self, 
                    label=node['label'], 
                    description=node['description'], 
                    position=node['position'], 
                    color=node['color']
                )
            )

        

        # Go through and draw our edges on the canvas
        for edge in self.data.get('edges', []):

            self.edge_canvas.shapes.append(self.Edge(self, edge))

        self.sidebar_body.controls.append(info_column)

        # Interactive viewer to hold the stack for UI manipulation
        iv = ft.InteractiveViewer(
            content=ft.Stack([      # Hold the edge canvas and node stack
                self.edge_canvas,
                self.node_stack, 
            ], width=5000, height=3000),
            expand=3, 
            constrained=False,
            scale_factor=800, boundary_margin=200,
            min_scale=0.02, max_scale=3.0,
        )

        self.add_node_button = ft.Button(
            "Add Node", 
            on_click=self.create_node_clicked, 
            data="ignore_position",
            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, text_style=ft.TextStyle(weight=ft.FontWeight.W_500, size=20)),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            visible=not self.sidebar.visible
        )

        self.new_node_tf = ft.TextField(
            label="Add New node", dense=True, 
            capitalization=ft.TextCapitalization.WORDS,
            on_blur=hide_new_node_tf,
            on_submit=self.create_node, 
            visible=False, autofocus=True,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST
        ) 

        viewer_stack = ft.Stack([
            iv,
            ft.Column([
                self.add_node_button,
                self.new_node_tf
            ], tight=True, bottom=10, right=0,)
        ], expand=3)

        
        self.content = ft.Row([viewer_stack, self.show_sidebar_button, self.sidebar], spacing=0, expand=True)

        # TODO: Add spider web view
        # Save pan events so we can load back to how we looked on launch