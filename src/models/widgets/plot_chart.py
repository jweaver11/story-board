''' Class for the Plot Chart widget, works similar to a flow chart'''

import flet as ft
from models.views.story import Story
from models.widget import Widget
from utils.verify_data import verify_data
from styles.menu_option_style import MenuOptionStyle
from models.app import app
from utils.safe_string_checker import return_safe_name
from styles.text_field import TextField
import flet.canvas as cv
from styles.snack_bar import SnackBar
from styles.colors import colors
import asyncio

class PlotChart(Widget):

    # Constructor
    def __init__(self, title: str, page: ft.Page, directory_path: str, story: Story, data: dict = None, is_rebuilt: bool = False):

        # Check if we're new and need to create file
        is_new = False
        if data is None:
            is_new = True

        # Initialize from our parent class 'Widget'. 
        super().__init__(
            title = title,                      # Title of the note
            page = page,                        # Grabs our original page for convenience and consistency
            directory_path = directory_path,    # Path to our notes json file
            story = story,                      # Reference to our story object
            data = data,
            is_rebuilt = is_rebuilt
        )

        # Verifies this object has the required data fields, and creates them if not.
        # If the fields exist already, they will be skipped. Example, loaded notes have the "note" tag, so that would be skipped
        # If you provide default types, it gives it default values, otherwise you can specify values
        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {
                # Widget data
                'key': f"{self.directory_path}\\{return_safe_name(self.title)}_plot_chart", 
                'tag': "plot_chart",             # Tag to identify what type of object this is
                'color': app.settings.data.get('default_note_color'),
                'pin_location': app.settings.data.get('default_note_pin_location', "right") if data is None else data.get('pin_location', "right"),   # Default pin location for notes

                'description': str,
                'show_info': True, 
                'spider_web_view': False,

                'nodes': [],
                  # List of all our Nodes/events
                    #{'label': "", 'description': "", 'position': (100, 100), 'color': '#FFFFFF'}
                 
                'edges': [    # List of all our Links/Connections between nodes
                    #{'source': "", 'target': "", 'color': '#FFFFFF', }
                ] 
            },
        )
        #self.body_container.padding = ft.Padding.only(left=16, bottom=16)

        self.new_node_position = (100, 100)

        # State trackers
        self.source_node: str = None        # Tracks which node we are dragging from when creating a new edge
        self.target_node: str = None        # Tracks which node we are dragging to when creating a new edge
        self.source_side: str = None      # Determines which sides of the nodes we start dragging from
        self.target_side: str = None       # Determines which sides of the nodes we end dragging on
        

        # Saving creates the file if we're new
        if is_new:
            self.p.run_task(self.save_dict)
        
        if self.visible:
            self.reload_widget()         # Build our widget if it's visible on init

    class Node(ft.GestureDetector):

        def __init__(self, widget: 'PlotChart', label: str, description: str="", position: tuple=tuple(), color: str="white"):

            
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
                on_hover=self.widget._set_coords,
            )

        # Moves the node on the stack and updates the drawing that connects the edges
        async def move_node(self, e: ft.DragUpdateEvent):
            self.left += e.local_delta.x
            self.top += e.local_delta.y
            self.update()

            for node in self.widget.data.get('nodes', []):
                if node['label'] == self.label:
                    node['position'] = (self.left, self.top)
                    break

            for edge in self.widget.edge_canvas.shapes:
                if isinstance(edge, self.widget.Edge) and (edge.source_node == self.label or edge.target_node == self.label):
                    edge.draw_edge()   
                    edge.update()

        # Saves our new position when we are done dragging
        async def save_position(self):
            for node in self.widget.data.get('nodes', []):
                if node['label'] == self.label:
                    node['position'] = (self.left, self.top)
                    break

            #for edge in self.widget.data.get('edges', []):
                #if edge['source'] == self.label:
                    #edge['start_position'] = (self.left, self.top)
                #elif edge['target'] == self.label:
                    #edge['end_position'] = (self.left, self.top)

            await self.widget.save_dict()
            self.widget.reload_widget()   # Reload to update the new edge positions

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
                    on_click=self.widget.edit_node_description_clicked,
                    content=ft.Row([
                        ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, self.color,),
                        ft.Text(
                            "Edit Description", 
                            weight=ft.FontWeight.BOLD, 
                            
                        ), 
                    ]),
                    data={'label': self.label, 'description': self.description}
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

        async def delete_clicked(self, e: ft.Event):

            # Remove the node
            for idx, node in enumerate(self.widget.data.get('nodes', [])):
                if node['label'] == self.label:
                    self.widget.data['nodes'].pop(idx)
                    break
            
            # Remove any edges connected to the node
            for edge in self.widget.data.get('edges', []):
                if edge['source'] == self.label or edge['target'] == self.label:
                    self.widget.data['edges'].remove(edge)

            await self.widget.save_dict()
            self.widget.reload_widget()
            await self.widget.story.close_menu()

        def get_color_options(self) -> list[ft.Control]:
            ''' Returns a list of all available colors for icon changing '''

            # Called when a color option is clicked on popup menu to change icon color
            async def _change_icon_color(e=None):
                ''' Passes in our kwargs to the widget, and applies the updates '''
                color = e.control.data

                for node in self.widget.data.get('nodes', []):
                    if node['label'] == self.label:
                        node['color'] = color
                        break
                await self.widget.save_dict()

                self.widget.reload_widget()
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
                        self.widget.data['edges'].remove(edge)
                        await self.widget.save_dict()
                        # Reset state trackers
                        self.widget.source_node = None
                        self.widget.target_node = None
                        self.widget.source_side = None
                        self.widget.target_side = None
                        # Reload
                        self.widget.reload_widget()  
                        return  
                
                # Otherwise we're creating it, so grab the positions for the new edge
                for node in self.widget.data.get('nodes', []):
                    if node['label'] == self.widget.source_node:
                        start_position = node['position']
                    elif node['label'] == self.widget.target_node:
                        end_position = node['position']

                # Save new edget to data with source, target, start, end, and default color
                self.widget.data['edges'].append({
                    'source': self.widget.source_node,
                    'target': self.widget.target_node,
                    'color': "#FFFFFF",
                    'start_position': start_position,  
                    'end_position': end_position
                })
                await self.widget.save_dict()

                # Reset state trackers
                self.widget.source_node = None
                self.widget.target_node = None
                self.widget.source_side = None
                self.widget.target_side = None

                # Re-render page to show new edge
                await _stop_highlight_node(e)   # Stops the highlight
                self.widget.reload_widget()   # Reload to show the new edge
                

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

            self.description_ctrl = ft.Text(f"{self.description}\n", italic=True, color=ft.Colors.ON_SURFACE_VARIANT, max_lines=5, overflow=ft.TextOverflow.ELLIPSIS)


            self.content = ft.Container(
                ft.Column([
                    ft.GestureDetector(
                        ft.Row([ft.Text(self.label, expand=True, overflow=ft.TextOverflow.ELLIPSIS, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER)], alignment=ft.MainAxisAlignment.CENTER),
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
            self.color = data.get('color', "#FFFFFF")
            self.widget = widget

            super().__init__([], paint=ft.Paint(self.color, stroke_width=3, style="stroke", anti_alias=True))
            self.draw_edge()

        # Changes the edges color
        def change_color(self, color: str):
            self.color = color
            self.paint = ft.Paint(self.color, stroke_width=3, style="stroke", anti_alias=True)
            self.update()

        def draw_edge(self):
            self.start_position = None
            self.end_position = None
            for node in self.widget.data.get('nodes', []):
                if node['label'] == self.source_node:
                    self.start_position = node.get('position', (0, 0))
                elif node['label'] == self.target_node:
                    self.end_position = node.get('position', (0, 0))


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

            # Three-segment turns
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
                self.p.pop_dialog()
                return

            if await _check_node_title(node_title.value):
                for node in self.data.get('nodes', []):
                    if node['label'] == old_label:
                        node['label'] = node_title.value
                        break
                for edge in self.data.get('edges', []):
                    if edge['source'] == old_label:
                        edge['source'] = node_title.value
                    elif edge['target'] == old_label:
                        edge['target'] = node_title.value
                await self.save_dict()
                self.reload_widget()
                self.p.pop_dialog()

        await self.story.close_menu()

        old_label = e.control.data

        node_title = TextField(
            old_label, hint_text="Node Label", capitalization=ft.TextCapitalization.SENTENCES, 
            autofocus=True, on_submit=_rename_node,
        )

        self.p.show_dialog(
            ft.AlertDialog(
                title="Rename Node",
                content=node_title,
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: self.p.pop_dialog(), style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.ERROR)),
                    ft.TextButton("Rename", on_click=_rename_node, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK))
                ]
            )
        )

    async def edit_node_description_clicked(self, e: ft.Event):

        async def _set_node_description(_):
            for node in self.data.get('nodes', []):
                if node['label'] == node_label:
                    node['description'] = description.value
                    break
            await self.save_dict()
            self.reload_widget()
            self.p.pop_dialog()

        await self.story.close_menu()

        node_label = e.control.data.get('label', "")
        old_description = e.control.data.get('description', "")

        description = TextField(
            old_description, hint_text="Node Description", capitalization=ft.TextCapitalization.SENTENCES, 
            autofocus=True, on_submit=_set_node_description, multiline=True
        )

        self.p.show_dialog(
            ft.AlertDialog(
                title=f"Edit Description for {node_label}",
                content=description,
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: self.p.pop_dialog(), style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.ERROR)),
                    ft.TextButton("Save", on_click=_set_node_description, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK))
                ]
            )
        )
        

    # Adds our options to create new nodes when right clicking on the canvas
    async def _open_menu(self, e: ft.PointerEvent):
        
        menu_options = [
            MenuOptionStyle(
                ft.MenuItemButton(
                    "Node", leading=ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, self.data.get('color', "primary")),
                    on_click=self._add_node_clicked, 
                    tooltip="Create a new node for the plot chart",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                ),
                no_padding=True, no_effects=True 
            ),
            
            #MenuOptionStyle(
                #on_click=self._toggle_show_info,
                #content=ft.Row([
                    #ft.Icon(ft.Icons.INFO_OUTLINE, self.data.get('color', 'primary')),
                    #ft.Text(
                        #"Show Info", 
                        #weight=ft.FontWeight.BOLD, 
                        #color=ft.Colors.ON_SURFACE
                    #), 
                #]),
            #),
        ] + self._get_menu_options()

        self.story.open_menu(menu_options)

    # Called when click a button to create a new node
    async def _add_node_clicked(self, e: None):
        ''' Opens a dialog to name the node or cancel '''

        # Checks that node title is unique
        async def _check_node_title(title: str) -> bool:
            for node in self.data.get('nodes', []):
                if node['label'] == title:
                    node_title.error = "Node label taken"
                    node_title.update()
                    return False
            return True

        # Creates our node with given title if unique
        async def _create_node(_):

            if not node_title.value:
                node_title.error = "Node must have a label"
                node_title.update()
                await node_title.focus()
                return

            if await _check_node_title(node_title.value):

                # Check if we're creating from the info column, and just put the new node in the center
                if e.control.data is not None:
                    self.new_node_position = (self.w / 2 * .75, self.h / 2) # Center of widget when showing info

                title = node_title.value if node_title.value else "Node"
                self.data['nodes'].append({'label': title, 'position': self.new_node_position, 'color': '#FFFFFF', 'description': ""})
                await self.save_dict()
                self.reload_widget()
                self.p.pop_dialog()
                self.new_node_position = (self.w / 2 * .75, self.h / 2) # Reset new node position to default for next time

        await self.story.close_menu()
        
        node_title = TextField(
            capitalization=ft.TextCapitalization.SENTENCES, 
            autofocus=True, on_submit=_create_node,
        )

        self.p.show_dialog(
            ft.AlertDialog(
                title="Node Title",
                content=node_title,
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: self.p.pop_dialog(), style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.ERROR)),
                    ft.TextButton("Create", on_click=_create_node, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK))
                ]
            )
        )
   

    # Called after any changes happen to the data that need to be reflected in the UI, usually just ones that require a rebuild
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # TODO: Add spider web view. Don't rebuild at all
        
        # Rebuild out tab to reflect any changes
        self.reload_tab()

        # Sets our canvas coords for when we're creating a new node by right clicking
        async def _set_canvas_coords(e: ft.HoverEvent):
            self.new_node_position = (e.local_position.x, e.local_position.y)
            self.story.mouse_x = e.global_position.x
            self.story.mouse_y = e.global_position.y    

        # Show the info whenever we click the background
        async def _show_info_display(e: ft.PointerEvent=None):
            self.data['show_info'] = True
            await self.save_dict()
            self.reload_widget()    
        
        # Canvas to hold our edge lines betwee nodes
        self.edge_canvas = cv.Canvas(
            [],  
            content=ft.GestureDetector(
                expand=True,
                on_secondary_tap=self._open_menu,
                on_hover=_set_canvas_coords,
                on_tap=_show_info_display,
                hover_interval=30,
            ),
            expand=True
        )

        # Stack that holdes our edges and nodes
        self.node_stack = ft.Stack([self.edge_canvas], expand=True)


        async def _change_description(e: ft.Event):
            await self.change_data(**{'description': e.control.value})

        description_tf = TextField(
            label="Description", value=self.data.get('description', ""), dense=True, multiline=True,
            capitalization=ft.TextCapitalization.SENTENCES, expand=True,
            on_blur=_change_description,   # When we click out of the text field, we save our changes
            label_style=ft.TextStyle(color=self.data.get('color', None)),
        )           

        # Load all our nodes into controls
        def _load_nodes() -> ft.Column:

            # Changes the link color of an edge
            async def _change_node_color(e: ft.Event):
                color = str(e.control.content)
                idx = e.control.data
                self.data['nodes'][idx]['color'] = color
                await self.save_dict()
                self.reload_widget()

            # Deletes a node and all connected edges
            async def _delete_node(e: ft.Event):
                idx = e.control.data
                node_label = self.data['nodes'][idx]['label']
                self.data['nodes'].pop(idx)
                for edge in self.data.get('edges', []):
                    if edge['source'] == node_label or edge['target'] == node_label:
                        self.data['edges'].remove(edge)
                await self.save_dict()
                self.reload_widget()

            controls = []
            for idx, node in enumerate(self.data.get('nodes', [])):
                
                controls.append(
                    ft.Row([
                        ft.PopupMenuButton(
                            icon=ft.Icons.COLOR_LENS_OUTLINED, 
                            icon_color=node.get('color', ft.Colors.ON_SURFACE), menu_padding=ft.Padding.all(0),
                            tooltip="Change Node Color",
                            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                            items=[
                                ft.PopupMenuItem(
                                    color.capitalize(), label_text_style=ft.TextStyle(color=color, weight=ft.FontWeight.BOLD),
                                    data=idx, 
                                    on_click=_change_node_color, 
                                    mouse_cursor=ft.MouseCursor.CLICK
                                ) for color in colors
                            ]
                        ),
                        ft.Text(
                            spans=[
                                ft.TextSpan(f"{node.get('label', f"Node {idx+1}")}:\t\t", style=ft.TextStyle(color=node.get('color', ft.Colors.ON_SURFACE), weight=ft.FontWeight.W_500, )),
                                ft.TextSpan(f"{node.get('description', '')}", style=ft.TextStyle(color=ft.Colors.ON_SURFACE_VARIANT, italic=True, overflow=ft.TextOverflow.ELLIPSIS))
                                
                            ],
                            expand=True, max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS
                        ),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR, on_click=_delete_node, data=idx, mouse_cursor=ft.MouseCursor.CLICK),
                        
                        
                    ], spacing=0)
                )

            return ft.Column(controls, spacing=0, tight=True)
        
        # Load all our edges into controls
        def _load_edges() -> ft.Column:

            # Changes the link color of an edge
            async def _change_edge_color(e: ft.Event):
                color = str(e.control.content)
                idx = e.control.data
                self.data['edges'][idx]['color'] = color
                await self.save_dict()
                self.reload_widget()

            # Deletes an edge
            async def _delete_edge(e: ft.Event):
                idx = e.control.data
                self.data['edges'].pop(idx)
                await self.save_dict()
                self.reload_widget()

            controls = []
            for idx, edge in enumerate(self.data.get('edges', [])):

                # Grab nodes colors. order them by x
                for node in self.data.get('nodes', []):
                    if node['label'] == edge['source']:
                        source_node = node
                    elif node['label'] == edge['target']:
                        target_node = node
                    
                if source_node.get('position', (0, 0))[0] <= target_node.get('position', (0, 0))[0]:  # If x_source is left of x_target
                    source_node_label = source_node.get('label', edge['source'])
                    target_node_label = target_node.get('label', edge['target'])
                    source_color = source_node.get('color', ft.Colors.ON_SURFACE)
                    target_color = target_node.get('color', ft.Colors.ON_SURFACE)
                else:
                    source_node_label = target_node.get('label', edge['target'])
                    target_node_label = source_node.get('label', edge['source'])
                    source_color = target_node.get('color', ft.Colors.ON_SURFACE)
                    target_color = source_node.get('color', ft.Colors.ON_SURFACE)

                # Color selector, Source -> Target, delete
                controls.append(
                    ft.Row([
                        ft.PopupMenuButton(
                            icon=ft.Icons.COLOR_LENS_OUTLINED, 
                            icon_color=edge.get('color', ft.Colors.ON_SURFACE), menu_padding=ft.Padding.all(0),
                            tooltip="Change Connection Color",
                            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                            items=[
                                ft.PopupMenuItem(
                                    color.capitalize(), label_text_style=ft.TextStyle(color=color, weight=ft.FontWeight.BOLD),
                                    data=idx, 
                                    on_click=_change_edge_color, 
                                    mouse_cursor=ft.MouseCursor.CLICK
                                ) for color in colors
                            ]
                        ),
                        ft.Text(
                            spans=[
                                ft.TextSpan(source_node_label, style=ft.TextStyle(color=source_color, weight=ft.FontWeight.W_500,)),
                                ft.TextSpan(" ➜ ", style=ft.TextStyle(color=edge.get('color', ft.Colors.ON_SURFACE), weight=ft.FontWeight.W_500,)),
                                ft.TextSpan(target_node_label, style=ft.TextStyle(color=target_color, weight=ft.FontWeight.W_500,))
                            ],
                            expand=True
                        ),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR, on_click=_delete_edge, data=idx, mouse_cursor=ft.MouseCursor.CLICK),
                    ], spacing=0)
                )
            return ft.Column(controls, spacing=0)

        # Info container on the right to show details of our edges and nodes
        info_column = ft.Column(
            [
                
                ft.Row([
                    ft.Text(f"\tNodes", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),
                    ft.IconButton(
                        ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                        self.data.get('color', ft.Colors.PRIMARY),
                        mouse_cursor=ft.MouseCursor.CLICK,
                        on_click=self._add_node_clicked,
                        data="ignore_position"
                    ),
                ]),

                # Nodes here
                _load_nodes(),

                ft.Divider(),
                ft.Text(f"\tConnections", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),

                _load_edges(),

                
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

        # Button in the bottom right to add new nodes
        self.node_stack.controls.append(
            ft.Button(
                "Node", 
                ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                on_click=self._add_node_clicked, 
                data="ignore_position",
                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                right=20, bottom=20, scale=1.3
            )
        )

        # Go through and draw our edges on the canvas
        for edge in self.data.get('edges', []):

            self.edge_canvas.shapes.append(self.Edge(self, edge))

        plot_chart_info = ft.Container(
            expand=1,
            border=ft.Border.only(left=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            padding=ft.Padding.only(left=11, top=8, bottom=8,),
            shadow=ft.BoxShadow(0, 1),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            content=ft.Column(
                [
                    ft.Row([
                        ft.Text(
                            f"\tPlot Chart Info", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, 
                            #color=self.data.get('color', None), 
                            expand=True
                        ),
                        ft.IconButton(
                            ft.Icons.CLOSE, ft.Colors.ON_SURFACE_VARIANT, on_click=self._toggle_show_info, 
                            mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER,
                        ),
                    ]),
                    ft.Divider(),
                    info_column,
                    ft.Row([ft.Container(description_tf, expand=True, padding=ft.Padding.only(right=11))]),
                ], expand=True, scroll="none", spacing=0),
        )

        # Interactive viewer to hold the stack for UI manipulation
        iv = ft.InteractiveViewer(
            content=self.node_stack, 
            expand=3,
            scale_factor=500,
            min_scale=0.5, max_scale=3.0,
        )

         # If we're not showing info, just give us a button to show info and return early
        if not self.data.get('show_info', True):

            plot_chart_info = ft.IconButton(
                ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT_ROUNDED, self.data.get('color', ft.Colors.PRIMARY),
                on_click=self._toggle_show_info, 
                mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER,
            )
                    
        
        #self.body_container.content = ft.Row([iv, plot_chart_info], expand=True, spacing=0)
        self.body_container.content = iv

        self._render_widget()
