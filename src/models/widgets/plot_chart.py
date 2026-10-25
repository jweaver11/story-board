''' Class for the Plot Chart widget, works similar to a flow chart'''

import flet as ft
from models.views.story import Story
from models.widget import Widget, WidgetView, WidgetSidebar
from styles.context_menu_option import MenuOptionStyle
from styles.text_fields import SmallTextField, TextField
import flet.canvas as cv
from styles.snack_bar import SnackBar
from styles.colors import colors
import asyncio
from contexts.constants import FIXED_STACK_WIDTH, FIXED_STACK_HEIGHT
import uuid
from styles.text_fields import NoLabelTextField
from dataclasses import dataclass, field
from typing import Callable

# Plot charts
@ft.observable
@dataclass
class PlotChart(Widget):

    tag: str = "plot_chart"

    nodes: dict = field(default_factory=dict)  # Nodes in the plot chart, keyed by id
    edges: list = field(default_factory=list)  # List of all edges in the plot chart

    spider_web_view: bool = False   # How to render edge connections between nodes

    def __post_init__(self):
        
        for node_id, node_data in self.nodes.items():
            if isinstance(node_data, dict):
                self.nodes[node_id] = Node(**node_data)
        
        super().__post_init__()

        # Card edits happen on Card objects, which the list can't see. Hold the listener strongly: observables keep weak refs
        self._node_listener = lambda sender, field: self.mark_dirty()
        for node in self.nodes.values():
            node.subscribe(self._node_listener)

    def create_node(self, new_node_position: ft.Offset):
        new_id = str(uuid.uuid4())
        node_data = {
            'id': new_id, 
            'label': f"Node {len(self.nodes) + 1}", 
            'position': {'x': new_node_position[0], 'y': new_node_position[1]} if isinstance(new_node_position, (tuple, list)) else {'x': new_node_position.x, 'y': new_node_position.y},
            'color': "#FFFFFF",
            'description': ""
        }
        node = Node(**node_data)
        node.subscribe(self._node_listener)
        self.nodes[new_id] = node

    def delete_node(self, node_id: str):
        if node_id in self.nodes:
            self.nodes.pop(node_id)
            #node.unsubscribe(self._node_listener)
            for edge in self.edges[:]:
                if node_id in edge:
                    self.edges.remove(edge)

    def toggle_view_mode(self):
        self.spider_web_view = not self.spider_web_view

    def create_or_delete_edge(self, source_node_id: str, target_node_id: str):
        # (a, b) and (b, a) are the same edge
        if source_node_id == target_node_id:
            return
        for existing in self.edges:
            if set(existing) == {source_node_id, target_node_id}:
                self.edges.remove(existing)
                return
        self.edges.append((source_node_id, target_node_id))
    

# Nodes inside the Plot Charts
@ft.observable
@dataclass
class Node:
    id: str
    label: str = "New Node"
    position: dict = field(default_factory=lambda: {"x": 200, "y": 200})
    color: str = "#FFFFFF"
    description: str = ""

    def set_label(self, new_label: str):
        self.label = new_label

    def set_description(self, new_description: str):
        self.description = new_description

    def move_node(self, e: ft.DragUpdateEvent):
        self.position['x'] = self.position['x'] + e.local_delta.x
        self.position['y'] = self.position['y'] + e.local_delta.y

    def set_color(self, new_color: str):
        self.color = new_color             
        
# Class for the Edges/Links between our nodes that show up as a line on the edge_canvas
@ft.component
def EdgeView(source_node: Node, target_node: Node, spider_web_view: bool=False):

    # Unpack into local vars so we don't mutate the stored tuples
    start_x = source_node.position['x']
    start_y = source_node.position['y']
    end_x = target_node.position['x']
    end_y = target_node.position['y']

    # Straight edges between nodes
    if spider_web_view == True:
        # Adjust for in/out nodes
        if start_x < end_x:
            start_x += 140  # 150 width - 10 for mid node
            end_x += 10
        else:
            end_x += 140
            start_x += 10
                
        elements = [
            cv.Path.MoveTo(start_x, start_y),
            cv.Path.LineTo(end_x, end_y),
        ]

    # Three-node turns
    else:
        

        mid_x = (start_x + end_x) / 2
        elements = [
            cv.Path.MoveTo(start_x, start_y),
            cv.Path.LineTo(mid_x, start_y),
            cv.Path.LineTo(mid_x, end_y),
            cv.Path.LineTo(end_x, end_y),
        ]

    return cv.Path(elements, ft.Paint(ft.Colors.ON_SURFACE, stroke_width=3, style="stroke", anti_alias=True))
            


# How view for the sidebar (textfield) control is rendered for each node
@ft.component
def NodeSidebarView(node: Node) -> ft.TextField:
    return ft.TextField(
        value=node.description,
        on_change=lambda e: node.set_description(e.control.value),
        label=node.label,
        text_style=ft.TextStyle(italic=True, color=ft.Colors.ON_SURFACE_VARIANT, size=14),
        data=node.id,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        multiline=True, dense=True, expand=True,
        capitalization=ft.TextCapitalization.SENTENCES,
        label_style=ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=ft.Colors.PRIMARY),
        border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.TRANSPARENT), border_radius=4)
    )

# The view of each node on the main stack for the plot chart
@ft.component
def NodeView(
        node: Node, 
        start_new_edge_position: ft.Offset,
        set_start_new_edge_position: Callable,
        update_new_edge_position: ft.Offset,
        set_update_new_edge_position: Callable,
        source_node_id: str,
        set_source_node_id: Callable,
        target_node_id: str,
        set_target_node_id: Callable,
        create_or_delete_edge: Callable,
        delete_node: Callable,
    ):

    def enter_connector(set_highlight):
        set_highlight(True)
        if source_node_id:
            set_target_node_id(node.id)
        
    
    def exit_connector(set_highlight):
        set_highlight(False)
        if target_node_id == node.id:
            set_target_node_id("")
    
    # Start of new edge from drag, we set the start position and source node ID
    def start_new_edge_drag(e: ft.DragStartEvent):
        set_start_new_edge_position(update_new_edge_position)

        if source_node_id:
            set_target_node_id(node.id)
        else:
            set_source_node_id(node.id)

    def update_new_edge_drag(e: ft.DragUpdateEvent):
        old_pos = update_new_edge_position.copy()
        new_x = old_pos.x + e.local_delta.x
        new_y = old_pos.y + e.local_delta.y
        set_update_new_edge_position(ft.Offset(new_x, new_y))

    def end_new_edge_drag(e: ft.DragEndEvent):
        set_start_new_edge_position(ft.Offset(**node.position))

        if source_node_id and target_node_id:
            create_or_delete_edge(source_node_id, target_node_id)

        set_source_node_id("")
        set_target_node_id("")

    def get_node_options() -> list[ft.PopupMenuItem]:
        return [
            ft.PopupMenuItem("Rename", ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, ft.Colors.PRIMARY), on_click=lambda: set_renaming_node(True)),
            ft.PopupMenuItem(       # Color change options
                ft.SubmenuButton(
                    ft.Row([
                        ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, ft.Colors.PRIMARY), 
                        ft.Text("Color", weight=ft.FontWeight.BOLD, expand=True),
                        ft.Icon(ft.Icons.ARROW_RIGHT),
                    ], expand=True),
                    [ft.MenuItemButton(color.capitalize(), style=ft.ButtonStyle(color), on_click=lambda e, data=color: node.set_color(data)) for color in colors],
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click", overlay_color=ft.Colors.TRANSPARENT),
                    tooltip="Change this widget's color"
                ),
                padding=ft.Padding.all(0)
            ),
            ft.PopupMenuItem("Delete", ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, ft.Colors.ERROR), on_click=lambda: delete_node(node.id)),
        ]
        

    def connector(side: str, highlight: bool, set_highlight) -> ft.GestureDetector:
        return ft.GestureDetector(
            ft.Container(
                ft.Icon(ft.Icons.CIRCLE_OUTLINED, node.color, scale=1.25), shape=ft.BoxShape.CIRCLE,
                shadow=ft.BoxShadow(10, 20, ft.Colors.with_opacity(0.25, node.color)) if highlight else None
            ), 
            mouse_cursor=ft.MouseCursor.PRECISE,
            data={'id': node.id, 'side': side},
            key=f"{node.id}_{side}",
            on_enter=lambda: enter_connector(set_highlight),
            on_exit=lambda: exit_connector(set_highlight),
            on_pan_start=start_new_edge_drag,
            on_pan_update=update_new_edge_drag,
            on_pan_end=end_new_edge_drag,
            drag_interval=20,
        )

    description_ctrl = SmallTextField(
        node.description,
        expand=True, 
        on_change=lambda e: node.set_description(e.control.value),
        enable_interactive_selection=False
    )

    renaming_node, set_renaming_node = ft.use_state(False)

    title_tf = NoLabelTextField(
        value=node.label,
        on_change=lambda e: node.set_label(e.control.value),
        on_blur=lambda e: set_renaming_node(False),
        text_align=ft.TextAlign.CENTER,
        expand=True,
        autofocus=renaming_node,
        border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.TRANSPARENT), border_radius=4)
    )

    highlight_left, set_highlight_left = ft.use_state(False)
    highlight_right, set_highlight_right = ft.use_state(False)

    # Our nodes content. Column with label, divider, description text field, and connection points
    return ft.GestureDetector(
        ft.Container(
            ft.ContextMenu(
                ft.Column([
                    ft.GestureDetector(
                        ft.Container(title_tf, ignore_interactions=not renaming_node, expand=True),
                        on_pan_update=node.move_node,
                        mouse_cursor=ft.MouseCursor.MOVE,
                        drag_interval=20,
                        on_double_tap=lambda: set_renaming_node(True),
                        tooltip="Double tap to rename Node"
                    ),
                    ft.Divider(ft.Colors.SURFACE_CONTAINER_LOW, 2),
                    description_ctrl,
                    ft.Row([
                        connector("left", highlight_left, set_highlight_left),
                        connector("right", highlight_right, set_highlight_right),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                expand=True,
                secondary_items=get_node_options()
            ),
            expand=True,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border_radius=8, padding=ft.Padding.all(8),
            alignment=ft.Alignment.TOP_CENTER,
        ),
        left=node.position['x'],
        top=node.position['y'],
        width=150, data=node.id,
        offset=ft.Offset(-0.5, -0.5),   # Shift the node to center it on its position
        animate_position=ft.Animation(250, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
        on_secondary_tap=lambda: None,
        hover_interval=20,
        key=node.id
    )

# The main view component for our plot charts
@ft.component
def PlotChartView(plot_chart: PlotChart):

    def set_positions(e: ft.HoverEvent):
        set_cm_global_position(e.global_position)
        set_cm_local_position(e.local_position)
        set_new_node_position(e.local_position)
        set_update_new_edge_position(e.local_position)

    async def open_menu(_):
        await context_menu.open(cm_global_position, cm_local_position)

    def get_menu_options() -> list[ft.PopupMenuItem]:
       
        return [
            ft.PopupMenuItem(
                "Add Node", 
                ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY), 
                on_click=lambda: plot_chart.create_node(new_node_position),
            ),
            ft.PopupMenuItem(
                "Toggle Connector View", 
                ft.Icon(ft.Icons.VERTICAL_DISTRIBUTE_OUTLINED if plot_chart.spider_web_view == True else ft.Icons.SHOW_CHART, ft.Colors.PRIMARY), 
                on_click=lambda: plot_chart.toggle_view_mode(),
            )
        ]

    # State and management
    new_node_position, set_new_node_position = ft.use_state((200, 200))     # Position a new node will get when created
    cm_global_position, set_cm_global_position = ft.use_state((0, 0))   # Context menu global position
    cm_local_position, set_cm_local_position = ft.use_state((0, 0))     # Context menu local position

    start_new_edge_position, set_start_new_edge_position = ft.use_state(ft.Offset(0, 0))   # Tracks the mouse position when an edge drag starts
    update_new_edge_position, set_update_new_edge_position = ft.use_state(ft.Offset(0, 0))   # Tracks the current mouse position when hovering

    source_node_id, set_source_node_id = ft.use_state(None)        # Node ID to be set when we start an edge drag from a node connector
    target_node_id, set_target_node_id = ft.use_state(None)        # Node ID to be set when we end an edge drag on a node connector

    drag_origin = ft.use_ref(None)  # (mouse x, mouse y, node x, node y) when an edge drag began

    # e.local_position is relative to the connector being dragged, so track the mouse's movement from where the drag began instead
    def start_edge_drag(node_id: str, e):
        node = plot_chart.nodes[node_id]
        drag_origin.current = (e.global_position.x, e.global_position.y, node.position['x'], node.position['y'])
        set_update_new_edge_position(ft.Offset(node.position['x'], node.position['y']))
        set_source_node_id(node_id)

    def update_edge_drag(e):
        if drag_origin.current is None:
            return
        gx, gy, nx, ny = drag_origin.current
        set_update_new_edge_position(ft.Offset(nx + e.global_position.x - gx, ny + e.global_position.y - gy))

    def end_edge_drag(e):

        if source_node_id and target_node_id:
            plot_chart.create_or_delete_edge(source_node_id, target_node_id)
        set_source_node_id(None)
        set_target_node_id(None)
        drag_origin.current = None
        

    # Paints the active edge connection if there is a current drag between nodes
    def paint_active_edge_connection() -> list[cv.Line]:
        # Paint nothing when we have not begun dragging a connector on a node
        if not source_node_id:
            return []
        
        # Otherwise, find where our mouse is
        start_x = start_new_edge_position.x
        start_y = start_new_edge_position.y

        # Build a line
        return [cv.Line(
            start_x, start_y,
            update_new_edge_position.x, update_new_edge_position.y,
            ft.Paint("#FFFFFF", stroke_width=3, style="stroke")
        )]
            
    # Canvas to hold our edge lines between nodes
    edge_canvas = cv.Canvas(
        paint_active_edge_connection(),  
        content=ft.GestureDetector(
            ft.Container(
                width=FIXED_STACK_WIDTH, height=FIXED_STACK_HEIGHT,
                border=ft.Border.all(2, ft.Colors.OUTLINE_VARIANT),
            ),
            width=FIXED_STACK_WIDTH, height=FIXED_STACK_HEIGHT,
            on_hover=set_positions,
            on_secondary_tap=open_menu,
            on_tap=open_menu,
            hover_interval=2,
            #mouse_cursor=ft.MouseCursor.PRECISE,
        ),
        width=FIXED_STACK_WIDTH, height=FIXED_STACK_HEIGHT,
        key=f"{plot_chart.id}_edge_canvas"
    )

    # Stack that holdes our nodes
    node_stack = ft.Stack(
        [
            NodeView(
                node, 
                start_new_edge_position, 
                set_start_new_edge_position, 
                update_new_edge_position,
                set_update_new_edge_position, 
                source_node_id,
                set_source_node_id,
                target_node_id,
                set_target_node_id,
                plot_chart.create_or_delete_edge,
                plot_chart.delete_node
            ) for node in plot_chart.nodes.values()
        ],
        width=FIXED_STACK_WIDTH, height=FIXED_STACK_HEIGHT
    )

    # Info container on the right to show details of our edges and nodes
    sidebar_ctrls = [
        
        ft.Text(f"Nodes", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), margin=ft.Margin.only(bottom=10)),
           
        # Nodes here
        ft.Column(
            [NodeSidebarView(node, key=node.id) for node in plot_chart.nodes.values()],
            tight=True, #margin=ft.Margin.only(left=10, right=10)
        ),
    ]

    # Go through and draw our edges on the canvas
    for edge in plot_chart.edges:
        edge_canvas.shapes.append(EdgeView(plot_chart.nodes[edge[0]], plot_chart.nodes[edge[1]], plot_chart.spider_web_view))
    

    # Interactive viewer to hold the stack for UI manipulation
    iv = ft.InteractiveViewer(
        content=ft.Stack([      # Hold the edge canvas and node stack
            ft.Container(
                image=ft.DecorationImage("flow_chart_background.png", repeat=ft.ImageRepeat.REPEAT),
                expand=True, border_radius=4
            ),
            edge_canvas,
            node_stack, 
        ], width=FIXED_STACK_WIDTH, height=FIXED_STACK_HEIGHT),
        expand=3, 
        constrained=False,
        scale_factor=800, boundary_margin=1500,
        min_scale=0.02, max_scale=3.0,
    )   

    
    context_menu = ft.ContextMenu(iv, items=get_menu_options(), expand=True)

    return WidgetView(
        plot_chart,
        ft.Stack([
            context_menu,
            WidgetSidebar(plot_chart, body_ctrls=sidebar_ctrls)
        ], expand=True, alignment=ft.Alignment.CENTER_RIGHT)
    )