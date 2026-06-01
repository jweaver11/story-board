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
                'nodes': [  # List of all our Nodes/events
                    {'label': "", 'description': "", 'position': (100, 100), 'color': '#FFFFFF'}
                ], 
                'edges': [    # List of all our Connections between nodes
                    {'source': "", 'target': "", 'color': '#FFFFFF'}
                ] 
            },
        )
        #self.body_container.padding = ft.Padding.only(left=16, bottom=16)

        self.new_node_position = (100, 100)
        

        # Saving creates the file if we're new
        if is_new:
            self.p.run_task(self.save_dict)
        
        if self.visible:
            self.reload_widget()         # Build our widget if it's visible on init

    class Node(ft.GestureDetector):

        def __init__(self, widget: Widget, label: str, description: str="", position: tuple=tuple(), color: str="white"):

            
            self.label = label
            self.color = color
            self.widget = widget
            self.description = description

            #self.w, self.h = 150, 100

            super().__init__(
                left=position[0],
                top=position[1],
                width=150, 
                #height=100,
                mouse_cursor=ft.MouseCursor.MOVE,
                drag_interval=50,
                animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
                on_pan_update=self.move_node,
                on_pan_end=self.save_position,
                on_secondary_tap=self.open_menu,
                on_hover=self.widget._set_coords,
                
            )
            #ft.GestureDetector()

        # Moves the node on the stack and updates the drawing that connects the edges
        async def move_node(self, e: ft.DragUpdateEvent):
            delta_x = e.local_delta.x
            delta_y = e.local_delta.y

            self.left += delta_x
            self.top += delta_y
            self.update()

            #TODO: Update link drawing to match new coords

        # Saves our new position when we are done dragging
        async def save_position(self):
            for node in self.widget.data.get('nodes', []):
                if node['label'] == self.label:
                    node['position'] = (self.left, self.top)
                    break

            await self.widget.save_dict()

        # Opens a menu with our options when right clicking a node
        async def open_menu(self, e: ft.PointerEvent):
            menu_options = [
                MenuOptionStyle(
                    #on_click=self.rename_clicked,
                    content=ft.Row([
                        ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, self.color,),
                        ft.Text(
                            "Rename", 
                            weight=ft.FontWeight.BOLD, 
                            
                        ), 
                    ]),
                ),
                MenuOptionStyle(
                    #on_click=self.rename_clicked,
                    content=ft.Row([
                        ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, self.color,),
                        ft.Text(
                            "Edit Description", 
                            weight=ft.FontWeight.BOLD, 
                            
                        ), 
                    ]),
                ),
                MenuOptionStyle(
                    ft.SubmenuButton(
                        ft.Row([
                            ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.color), 
                            ft.Text("Color", weight=ft.FontWeight.BOLD, expand=True),
                            ft.Icon(ft.Icons.ARROW_RIGHT),
                        ], expand=True),
                        #self.get_color_options(), 
                        menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                        style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        tooltip="Change this widget's color"
                    ),
                    no_padding=True, no_effects=True
                ),
                MenuOptionStyle(
                    #on_click=self.delete_clicked,
                    content=ft.Row([
                        ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, ft.Colors.ERROR),
                        ft.Text("Delete", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True),
                    ]),
                )
            ] 

            self.widget.story.open_menu(menu_options)

        def build(self):
            async def _size_change(e):
                pass
                #self.w = e.width
                #self.h = e.height

            self.content = ft.Container(
                ft.Column([
                    ft.Text(self.label),
                    ft.Divider(2, 2),
                    ft.Text(self.description, italic=True, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Row([
                        ft.Icon(
                        ft.Icons.CIRCLE_OUTLINED, scale=0.8), ft.Icon(ft.Icons.CIRCLE_OUTLINED, scale=0.8)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                expand=True, shadow=ft.BoxShadow(0, 2),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                border_radius=8, padding=ft.Padding.all(8),
                alignment=ft.Alignment.TOP_CENTER,
                on_size_change=_size_change,
            )
                
        

    class Edge:
        # End points (connectors on each node), color
        pass

        
    async def _open_menu(self, e: ft.PointerEvent):
        self.new_node_position = (e.local_position.x, e.local_position.y)
        menu_options = [] + self._get_menu_options()

        self.story.open_menu(menu_options)
   

    # Called after any changes happen to the data that need to be reflected in the UI, usually just ones that require a rebuild
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

    
        #TODO: Show nodes and edges in info
        # Right click to add edges as well
        # Add minimap

        async def _add_node(e: None):
            async def _create_node(e=None):

                title = node_title.value if node_title.value else "Node"
                self.data['nodes'].append({'label': title, 'position': self.new_node_position, 'color': '#FFFFFF'})
                await self.save_dict()
                self.reload_widget()
                self.p.pop_dialog()
                self.new_node_position = (100, 100)

            node_title = TextField(hint_text="Node Label", capitalization=ft.TextCapitalization.SENTENCES, autofocus=True)

            self.p.show_dialog(
                ft.AlertDialog(
                    title="Node Name",
                    content=node_title,
                    actions=[
                        ft.TextButton("Cancel", on_click=lambda _: self.p.pop_dialog(), style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.ERROR)),
                        ft.TextButton("Create", on_click=_create_node, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK))
                    ]
                )
            )

        # Rebuild out tab to reflect any changes
        self.reload_tab()
        
        # Draws the link between edges, and allows us to create more options
        link_canvas = cv.Canvas(
            content=ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.PRECISE if self.data.get('map_data', {}).get('drawing_mode') else None, 
                expand=True,

                on_secondary_tap=self._open_menu,
                on_hover=self._get_coords,
                #on_tap=self._show_info_display,
                #on_tap=lambda e: self.story.open_menu(self._get_menu_options()),
                drag_interval=20, hover_interval=20,
            ),
            expand=True
        )

        

        stack = ft.Stack([
            link_canvas,
        ], expand=3)

        for node in self.data.get('nodes', []):
            stack.controls.append(self.Node(self, label=node['label'], position=node['position'], color=node['color']))

        for edge in self.data.get('edges', []):
            pass
            # TODO: Draw edges using curves on canvas from and too

        

        info = ft.Container(
            ft.Column([
                ft.Row([
                    ft.Text(f"\tNodes", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),
                    ft.IconButton(
                        ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                        self.data.get('color', ft.Colors.PRIMARY),
                        mouse_cursor=ft.MouseCursor.CLICK,
                        on_click=_add_node,
                    ),
                ]),

                ft.Divider(2, 2),
                ft.Text(f"\tConnections", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),
            ], expand=True),
            border=ft.Border.only(left=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            padding=ft.Padding.only(left=11, top=8, bottom=8,),
            shadow=ft.BoxShadow(0, 1),
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            expand=1
        )

        # Assign the body_container content as whatever view you have built in the widget
        self.body_container.content = ft.Row([stack, info], expand=True, spacing=0)
        
        # Build in widget function that will handle loading our mini widgets and rendering the whole thing
        self._render_widget()
        