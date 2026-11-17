'''
Class for showing all our widgets laid out in a family tree view.
'''

import flet as ft
from models.widget import Widget
from models.views.story import Story
from models.app import app
import flet.canvas as cv
from styles.text_fields import NoLabelTextField
from styles.icons import connection_icons
from styles.colors import colors
from constants import FIXED_STACK_WIDTH, FIXED_STACK_HEIGHT
import flet_shadcn_ui as shad

# Add label to the connection type. Allow changable symbols, colors, styles, etc
class ConnectionMap(Widget):
    # Constructor
    def __init__(self, title: str, directory_path: str, story: Story, data: dict={}, is_new: bool = False):

        # Parent class constructor
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
                # Widget data
                'tag': "connection_map",
                'color': app.settings.data.get('widget_defaults', {}).get('connection_map', {}).get('color'),

                'show_sidebar': False,  # Start hidden so our toast notification is more visible
                'show_alert': True,
                'widgets': {
                    #'id': (position) # Widget id, tied to a position
                },
                'connections': [    # List of our connections
                    #{
                        # widget1_id: str
                        # widget2_id: str
                        # icon: str -- icon of the connection
                        # color: str  -- color of the drawn line and icon for the connection
                    #}
                ],  
            },
        )

    
        # State tracking
        self.widget1: str = None
        self.widget2: str = None

        self.edges_canvas: cv.Canvas = None
        self.connections_stack: ft.Stack = None

        self.add_widget_position: tuple = (200, 200)  # Where we add widgets to the stack 
       
    # Class for the nodes for each widget added to the connection map
    class WidgetNode(ft.GestureDetector):
        def __init__(self, widget_id: str, widget: 'ConnectionMap', ref_widget: Widget, position: tuple):
            self.widget_id = widget_id
            self.widget = widget
            self.position = position
            self.ref_widget = ref_widget

        
            self.rename_tf: NoLabelTextField
            

            # Our displayed content when dragging from widget bank to stack to show as moving feedback
            self.dragging_content: ft.Container = None
            self.is_dragging: bool = False

            super().__init__(
                content=self.build_content(),
                on_enter=self._highlight,
                on_exit=self._stop_highlight,
                
                on_pan_start=self.start_new_connection,   # Show line to follow mouse
                on_pan_update=self._update_line,   # Update line to follow mouse
                on_pan_end=self._create_new_connection,  # Create the new connection when dragging ends (or remove it if it already exists)
                left=position[0],
                top=position[1],
                animate_position=ft.Animation(250, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
                offset=ft.Offset(-0.5, -0.5),
                width=150, 
                mouse_cursor=ft.MouseCursor.PRECISE,
                data={'id': self.widget_id, 'position': self.position},   
            )

        # Start creating a new connection (edge) from this node
        async def start_new_connection(self, e: ft.DragStartEvent):
            self.is_dragging = True
            self.widget.widget1 = e.control.data

            # Reflect visually using the overlay
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
        async def _update_line(self, e: ft.PointerEvent):
            line: cv.Line = self.page.overlay[-1].content.shapes[-1]  # Get the last line we added
            line.x2 = e.global_position.x
            line.y2 = e.global_position.y
            self.page.overlay[-1].update()

        # Creates our new edge (link) between nodes
        async def _create_new_connection(self, e: ft.PointerEvent):
            self.is_dragging = False
            
            # Remove our visual feedback
            self.page.overlay.pop()
            self.page.update() 

            #await self._stop_highlight()   # Stop any highlighting from the hover that happens when we end our drag on another node
            self.content.shadow = ft.BoxShadow(1, 1, blur_style=ft.BlurStyle.OUTER),
            #self.update()

            # If its an incomplete edge (we didn't end on another node), reset and exit
            if not self.widget.widget1 or not self.widget.widget2:
                self.widget.widget1 = None
                self.widget.widget2 = None
                self.update()
                return  
            
            # Don't allow connections to self
            if self.widget.widget1.get('id') == self.widget.widget2.get('id'): 
                return  
            
            # Create the new connection
            new_connection = {
                'widget1_id': self.widget.widget1.get('id'),
                'widget2_id': self.widget.widget2.get('id'),
                'color': "#FFFFFF",
                'icon': 'link'
            }

            # If the connection already exists, delete it and return
            for connection in self.widget.data['connections']:
                if (connection['widget1_id'] == new_connection['widget1_id'] and connection['widget2_id'] == new_connection['widget2_id']) or (connection['widget1_id'] == new_connection['widget2_id'] and connection['widget2_id'] == new_connection['widget1_id']):
                    self.widget.data['connections'].remove(connection)  # Remove from data
                    self.widget.update_data(**{'connections': self.widget.data['connections']})
                    self.widget.build_map_ctrls()
                    self.widget.update()
                    return
            
            

            # Save new edget to data with source, target, start, end, and default color
            self.widget.data['connections'].append(new_connection)
            self.widget.needs_file_write = True

            # Reset state trackers
            self.widget.widget1 = None
            self.widget.widget2 = None

            # Draw this new connection and give it an icon
            self.widget.edges_canvas.shapes.append(self.widget.ConnectionEdge(self.widget, new_connection))
            self.widget.connections_stack.controls.append(self.widget.ConnectionIcon(self.widget, new_connection))
            self.widget.connections_stack.update()

        def get_menu_options(self) -> list[ft.Control]:

            # Options when setting the image of a widget. Either upload, set a canvas, or clear image
            def set_widget_image_options() -> list[ft.Control]:
        
                # Called when clicking our upload image button 
                async def upload_image(e: ft.Event):
        
                    files = await ft.FilePicker().pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "webp"])
                    if files:
        
                        file_path = files[0].path
                        try:
                            import base64
        
                            with open(file_path, "rb") as image_file:
                                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                                # Save to our data
                                self.ref_widget.update_data(**{'image_base64': f"{encoded_string}"})
                                close_popovers()
        
                        except Exception:
                            pass
        
                # Sets a canvas as our image
                async def set_canvas_as_image(e=None):
        
                    # Set the canvas id when selecting a canvas from the radio group
                    def select_canvas(e: ft.Event[ft.RadioGroup]):
                        nonlocal canvas_id
                        canvas_id = e.data
                        
                    # Sets the canvas image from the returned canvas snapshot
                    def set_canvas_image(e=None):
                        if canvas_id is None:
                            self.page.pop_dialog()
                            return
                        widget = self.widget.story.get_widget_by_id(canvas_id)
                        if widget is None:
                            self.page.pop_dialog()
                            #self.page.show_dialog(SnackBar("Canvas not found. Please try again."))
                            return
        
                        snapshot_str = widget.get_snapshot_string(quality="low")
                        if not snapshot_str:
                            self.page.pop_dialog()
                            #self.page.show_dialog(SnackBar("Empty Canvas cannot be made as the image"))
                            return
        
                        self.ref_widget.update_data(**{'image_base64': snapshot_str})
                        
                        self.page.pop_dialog()

                        close_popovers()
        
                    canvas_id: str = None
        
                    dlg = shad.Dialog(
                        title="Set a Canvas as Image",
                        content=shad.RadioGroup(
                            [
                                shad.Radio(
                                    label=widget.data.get('title', 'Untitled'),
                                    value=id, 
                                ) for id, widget in self.widget.story.widgets.items() if widget.data.get('tag', '') == "canvas"
                            ],
                                
                            on_change=select_canvas
                        ),
                        actions=[
                            ft.TextButton("Cancel", on_click=lambda: self.page.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ERROR)),
                            ft.TextButton("Select", on_click=set_canvas_image, style=ft.ButtonStyle(color=ft.Colors.PRIMARY, mouse_cursor="click")),]
                    )
                    self.page.show_dialog(dlg)
        
                # Resets our image to nothing and our button to the placeholder
                async def clear_image(e: ft.Event):
                    self.ref_widget.update_data(**{'image_base64': ""})
                    close_popovers()
        
                # Build the options
                return [
                    
                    shad.MenuItem(
                        leading=ft.Icon(ft.Icons.BRUSH_OUTLINED, ft.Colors.PRIMARY, size=20),
                        content="Set Canvas",
                        on_click=set_canvas_as_image,
                    ),
                    shad.MenuItem(
                        leading=ft.Icon(ft.Icons.IMAGE_SEARCH_OUTLINED, ft.Colors.PRIMARY, size=20),
                        content="Upload Image",
                        on_click=upload_image,
                    ),
                    shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
                    shad.MenuItem(
                        leading=ft.Icon(ft.Icons.HIDE_IMAGE_OUTLINED, ft.Colors.ERROR, size=20),
                        content="Clear Image",
                        on_click=clear_image,
                    )
                ]

            async def change_color(e: ft.Event[ft.Control]):
                color = e.control.data
                
                # Update the data
                self.ref_widget.update_data(**{'color': color})
                await self.ref_widget.save_file()  # Force a file save to persist the color change
                
                if self.ref_widget.data.get('visible', False) == True:
                    await self.widget.story.workspace.update_widget_tab_color(self.ref_widget.data.get('index'), color)  # Update the color of the tab in the workspace if we're visible
                    
                self.widget.story.tree_view_rail.reload_rail()   # Reload the rail to reflect the color change
                close_popovers()
            

            def toggle_color_popover(e=None):
                color_popover.open = not color_popover.open
                color_popover.update()
            def toggle_image_popover(e=None):
                image_popover.open = not image_popover.open
                image_popover.update()
            def close_popovers(e=None):
                self.content = self.build_content()
                self.update()

            def sever_connections(widget_id: str):
                for connection in self.widget.data.get('connections', [])[:]:
                    if connection.get('widget1_id') == widget_id or connection.get('widget2_id') == widget_id:
                        self.widget.data['connections'].remove(connection)
                self.widget.build_map_ctrls()
                self.widget.update()

            def remove_widget_from_map(e=None):
                widget_id = self.ref_widget.data.get('id')
                for id in self.widget.data.get('widgets', {}).keys():   # Remove the node from data
                    if id == widget_id:
                        del self.widget.data['widgets'][id]
                        break
                # Remove all connections involving the widget
                sever_connections(widget_id)
                self.widget.build_map_ctrls()
                self.widget.update()


            # color, rename, sever connections, set image, remove from map
            return [

                color_popover := shad.Popover(
                    shad.MenuItem(
                        leading=ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.ref_widget.data.get('color', 'primary'), size=20),
                        content=ft.Row([ft.Text("Color"), ft.Icon(ft.Icons.ARROW_RIGHT, ft.Colors.OUTLINE, size=16)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        trailing=ft.Icons.ARROW_RIGHT,
                        on_click=toggle_color_popover,
                        close_on_click=False,
                    ),
                    ft.Column([
                        shad.MenuItem(
                            content=ft.Icon(ft.Icons.CIRCLE, color=color, size=20),
                            on_click=change_color, close_on_click=True, data=color,
                        ) for color in colors
                    ], tight=True, spacing=0, width=100, height=min(320, ft.context.page.height * 0.3), scroll=ft.ScrollMode.AUTO),
                    on_dismiss=close_popovers
                ), 
                shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
                image_popover := shad.Popover(
                    shad.MenuItem(
                        leading=ft.Icon(ft.Icons.IMAGE_OUTLINED, ft.Colors.PRIMARY, size=20),
                        content=ft.Row([ft.Text("Image"), ft.Icon(ft.Icons.ARROW_RIGHT, ft.Colors.OUTLINE, size=16)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        trailing=ft.Icons.ARROW_RIGHT,
                        on_click=toggle_image_popover,
                        close_on_click=False,
                    ),
                    ft.Column(set_widget_image_options(), tight=True, spacing=0, width=150, height=114, scroll=ft.ScrollMode.AUTO),
                    on_dismiss=close_popovers
                ), 
                shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
                shad.MenuItem(
                    on_click=self.rename_tf.focus,
                    content="Rename", 
                    leading=ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, ft.Colors.PRIMARY, size=20),
                ),
                shad.MenuItem(
                    on_click=lambda: sever_connections(self.ref_widget.data.get('id')),
                    content="Sever Connections", 
                    leading=ft.Icon(ft.Icons.LINK_OFF_OUTLINED, ft.Colors.PRIMARY, size=20),
                ),
                shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
                shad.MenuItem(
                    on_click=remove_widget_from_map,
                    content="Remove",
                    leading=ft.Icon(ft.Icons.CLOSE_OUTLINED, ft.Colors.ERROR, size=20),
                )
            ]

        # Used for building our content in case we need to add it temporarily when dragging from the widgetacter bank
        def build_content(self) -> ft.Container:

            def get_icon() -> ft.Icon:
                match self.ref_widget.data.get('tag'):
                    case "manuscript": return ft.Icons.DESCRIPTION_OUTLINED
                    case "canvas": return ft.Icons.BRUSH_OUTLINED
                    case "canvas_board": return ft.Icons.SPACE_DASHBOARD_OUTLINED
                    case "note": return ft.Icons.LIBRARY_BOOKS_OUTLINED
                    case "character": return ft.Icons.PERSON_OUTLINE
                    case "connection_map": return ft.Icons.LINK_OUTLINED
                    case "plotline": return ft.Icons.TIMELINE
                    case "map": return ft.Icons.MAP_OUTLINED
                    case "world": return ft.Icons.PUBLIC_OUTLINED
                    case "item": return ft.Icons.STAR_OUTLINE_ROUNDED
                    case "chart": 
                        if self.ref_widget.data.get('chart_type') == 'bar':
                            return ft.Icons.INSERT_CHART_OUTLINED 
                        else:
                            return ft.CupertinoIcons.COMPASS
                    case "comic_preview": return ft.Icons.SLIDESHOW_OUTLINED
                    case "plot_chart": return ft.Icons.ACCOUNT_TREE_OUTLINED
                    case _: return ft.Icons.ERROR_OUTLINE

            # Builds the title of the widget node that allows for renaming and dragging
            def build_title() -> ft.GestureDetector:

                async def rename_widget(e: ft.Event[ft.TextField]):
                    await self.ref_widget.submit_rename(e)

                self.rename_tf = NoLabelTextField(
                    value=self.ref_widget.data.get('title'),
                    on_blur=rename_widget,
                    text_align=ft.TextAlign.CENTER,
                    expand=True, 
                )

                # Return our icon that used to create connections
                return ft.GestureDetector(
                    ft.Container(
                        self.rename_tf,
                        expand=True, 
                        ignore_interactions=True,
                        alignment=ft.Alignment.CENTER, 
                        padding=ft.Padding.symmetric(horizontal=6, vertical=6), 
                        border_radius=4, 
                    ),
                    mouse_cursor=ft.MouseCursor.MOVE,
                    data={'id': self.widget_id, 'position': self.position},                            
                    on_pan_start=self._start_drag,
                    on_pan_end=self._drag_end,
                    on_pan_update=self.move_widget_node,
                    drag_interval=20,
                    on_double_tap=self.rename_tf.focus
                )
            
            return shad.ContextMenu(
                ft.Container(
                    ft.Column([ 
                        build_title(),  
                        ft.Divider(ft.Colors.SURFACE_CONTAINER_LOW, 2, 6, trailing_indent=6),
                        ft.Container(ft.Image(self.ref_widget.data.get('image_base64'), 100, 100, expand=True), expand=True, width=100, height=100) if self.ref_widget.data.get('image_base64') else ft.Icon(get_icon(), self.ref_widget.data.get('color'), size=100),
                                        
                    ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, ),
                    border_radius=8,
                    alignment=ft.Alignment.TOP_CENTER,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    data={'widget_id': self.widget_id},
                    shadow=ft.BoxShadow(1, 1, blur_style=ft.BlurStyle.OUTER),
                ),
                self.get_menu_options()
            )


        # Highlight our widgetacter node when we hover over it
        async def _highlight(self, e=None):
            ''' When we hover over a widgetacter node, we want to highlight it and show its connections '''
            if self.widget.widget1:
                self.widget.widget2 = e.control.data
            self.content.content.shadow = ft.BoxShadow(4, 4, ft.Colors.with_opacity(0.3, self.ref_widget.data.get('color')))
            self.update()

        # Stop highlighting our widgetacter node when we stop hovering over it. Ignore if we're dragging
        async def _stop_highlight(self, e=None):
            ''' When we stop hovering over a widgetacter node, we want to stop highlighting it '''
            if self.is_dragging:
                return
            if self.widget.widget2:
                self.widget.widget2 = None
            self.content.content.shadow = ft.BoxShadow(1, 1, blur_style=ft.BlurStyle.OUTER),
            self.update()

        async def _start_drag(self, e: ft.DragStartEvent):
            self.is_dragging = True
            
        # Moves our widgetacter node or feedback on the stack
        async def move_widget_node(self, e: ft.DragUpdateEvent):
                
            self.left += e.local_delta.x
            self.top += e.local_delta.y
            if self.left < 50:
                self.left = 50
            elif self.left > self.left > FIXED_STACK_WIDTH - 50:
                self.left = FIXED_STACK_WIDTH - 50
            if self.top < 50:
                self.top = 50
            elif self.top > self.left > FIXED_STACK_HEIGHT - 50:
                self.top = FIXED_STACK_HEIGHT - 50
            
            self.update()

            # Update the data in real time, but don't call a save until done dragging
            self.widget.data['widgets'][self.widget_id] = (self.left, self.top)

            # Update any edges connected to this widgetacter node as we move
            for connection in self.widget.edges_canvas.shapes:
                if isinstance(connection, self.widget.ConnectionEdge) and (connection.widget1_id == self.widget_id or connection.widget2_id == self.widget_id):
                    connection.draw_connection()
                    connection.update()

            # Make the icons follow us
            for icon in self.widget.connections_stack.controls:
                if isinstance(icon, self.widget.ConnectionIcon) and (icon.widget1_id == self.widget_id or icon.widget2_id == self.widget_id):
                    icon.set_position()

        # Handles when we stop dragging
        async def _drag_end(self, e: ft.DragEndEvent):
            self.is_dragging = False
            
            # Update our positional data
            self.widget.update_data(**{'widgets': self.widget.data['widgets']})
                

    # Just for drawing the connection on the canvas, and icon on the stack
    class ConnectionEdge(cv.Path):
        def __init__(self, widget: 'ConnectionMap', data: dict):

            # Set our attributes
            self.widget1_id = data.get('widget1_id')
            self.widget2_id = data.get('widget2_id')
            self.color = data.get('color', "#FFFFFF")
            self.widget = widget
            self.start_position: tuple
            self.end_position: tuple
            super().__init__(data=data)

            # Set our content
            self.draw_connection()
            
        # Draws our connection between our two widgetacter Nodes based on position
        def draw_connection(self):

            self.start_position = self.widget.data['widgets'].get(self.widget1_id, None)
            self.end_position = self.widget.data['widgets'].get(self.widget2_id, None)

            if not self.start_position or not self.end_position:
                return
            
            self.mid_position = ((self.start_position[0] + self.end_position[0]) / 2, (self.start_position[1] + self.end_position[1]) / 2)
                
            self.elements = [
                cv.Path.MoveTo(self.start_position[0], self.start_position[1]), 
                cv.Path.LineTo(self.end_position[0], self.end_position[1]), 
            ]
            self.paint = ft.Paint(self.color, stroke_width=3, style="stroke", anti_alias=True)
            return
            

    class ConnectionIcon(ft.GestureDetector):
        def __init__(self, widget: 'ConnectionMap', data: dict):
            self.widget1_id = data.get('widget1_id')
            self.widget2_id = data.get('widget2_id')
            self.color = data.get('color', "#FFFFFF")
            self.icon = data.get('icon', '')
            self.widget = widget
            super().__init__(
                data=data,
                on_enter=self._highlight_icon,
                on_exit=self._stop_highlight_icon,
                offset = ft.Offset(-0.5, -0.5),
                mouse_cursor=ft.MouseCursor.CLICK,
            )
            self.build_icon()   # Set our content

        def _get_menu_options(self):

            
            async def _new_icon_clicked(e: ft.Event):
                icon_str = e.control.data
                self.icon = icon_str
                for connection in self.widget.data['connections']:
                    if (connection['widget1_id'] == self.widget1_id and connection['widget2_id'] == self.widget2_id) or (connection['widget1_id'] == self.widget2_id and connection['widget2_id'] == self.widget1_id):
                        connection['icon'] = icon_str
                        self.widget.update_data(**{'connections': self.widget.data['connections']})
                self.build_icon()
                self.update()
                await self.widget.story.close_menu()

            async def _delete_connection(e: ft.Event):
                for connection in self.widget.data['connections']:
                    if (connection['widget1_id'] == self.widget1_id and connection['widget2_id'] == self.widget2_id) or (connection['widget1_id'] == self.widget2_id and connection['widget2_id'] == self.widget1_id):
                        self.widget.data['connections'].remove(connection)
                        self.widget.update_data(**{'connections': self.widget.data['connections']})
                        self.widget.build_map_ctrls()
                        self.widget.update()

            async def _change_icon_color(e: ft.Event):
                color_str = e.control.data
                self.color = color_str
                for connection in self.widget.data['connections']:
                    if (connection['widget1_id'] == self.widget1_id and connection['widget2_id'] == self.widget2_id) or (connection['widget1_id'] == self.widget2_id and connection['widget2_id'] == self.widget1_id):
                        connection['color'] = color_str
                        self.widget.update_data(**{'connections': self.widget.data['connections']})
                self.build_icon()
                self.update()
                await self.widget.story.close_menu()

                # Update the lines color as well
                for edge in self.widget.edges_canvas.shapes:
                    if isinstance(edge, self.widget.ConnectionEdge) and ((edge.widget1_id == self.widget1_id and edge.widget2_id == self.widget2_id) or (edge.widget1_id == self.widget2_id and edge.widget2_id == self.widget1_id)):
                        edge.color = color_str
                        edge.draw_connection()
                        edge.update()

            def toggle_new_popover(e: ft.Event):
                new_popover.open = not new_popover.open
                self.update()
            def toggle_color_popover(e: ft.Event):
                color_popover.open = not color_popover.open
                self.update()
            def close_popovers(e=None):
                new_popover.open = False
                color_popover.open = False
                new_popover.update()
                color_popover.update()

            return [
                new_popover := shad.Popover(
                    shad.MenuItem(
                        leading=ft.Icon(ft.Icons.LINK, self.data.get('color', "primary"), size=20),
                        content=ft.Row([ft.Text("Icon"), ft.Icon(ft.Icons.ARROW_RIGHT, ft.Colors.OUTLINE, size=16)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        on_click=toggle_new_popover,
                        close_on_click=False,
                    ),
                    ft.Column([
                        shad.MenuItem(
                            ft.Icon(icon, self.color, size=20), 
                            data=icon_str,
                            on_click=_new_icon_clicked, 
                        ) for icon_str, icon in connection_icons.items()
                    ], tight=True, spacing=0, width=100, height=min(320, ft.context.page.height * 0.3), scroll=ft.ScrollMode.AUTO),
                    on_dismiss=close_popovers
                ),
                shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
                color_popover := shad.Popover(
                    shad.MenuItem(
                        leading=ft.Icon(ft.Icons.COLOR_LENS, self.data.get('color', "primary"), size=20),
                        content=ft.Row([ft.Text("Color"), ft.Icon(ft.Icons.ARROW_RIGHT, ft.Colors.OUTLINE, size=16)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        on_click=toggle_color_popover,
                        close_on_click=False,
                    ),
                    ft.Column([
                        shad.MenuItem(
                            ft.Icon(ft.Icons.CIRCLE, color, size=20), 
                            data=color,
                            on_click=_change_icon_color, 
                        ) for color in colors
                    ], tight=True, spacing=0, width=100, height=min(320, ft.context.page.height * 0.3), scroll=ft.ScrollMode.AUTO),
                    on_dismiss=close_popovers
                ),

                shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
                shad.MenuItem(
                    "Delete",
                    leading=ft.Icon(ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR),
                    on_click=_delete_connection,
                ),
                
                
            ]
                
        # Highlight the node
        async def _highlight_icon(self, e: ft.PointerEvent):
            e.control.content.content.shadow = ft.BoxShadow(4, 4, ft.Colors.with_opacity(0.5, self.color))
            e.control.update()

        # Stop highlighting the node
        async def _stop_highlight_icon(self, e: ft.PointerEvent):
            e.control.content.content.shadow = None
            e.control.update()

        def set_position(self, update=True):
            start_position = self.widget.data['widgets'].get(self.widget1_id, None)
            end_position = self.widget.data['widgets'].get(self.widget2_id, None)

            if start_position and end_position:
                mid_position = ((start_position[0] + end_position[0]) / 2, (start_position[1] + end_position[1]) / 2)
                self.left = mid_position[0]
                self.top = mid_position[1]
                if update:
                    self.update()

        def build_icon(self):
            self.set_position(False)
            self.content = shad.ContextMenu(
                ft.Container(
                    ft.Icon(connection_icons.get(self.icon, ft.Icons.ERROR), self.color, size=30),
                    shape=ft.BoxShape.CIRCLE,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                    padding=ft.Padding.all(6)
                ),
                self._get_menu_options(),
                open_on_tap=True
            )

    def build_map_ctrls(self):
        # Update our mouse cursor when interacting with the drag target
        def show_accept_mc(e: ft.Event[ft.DragTarget]):
            e.control.content.mouse_cursor = ft.MouseCursor.GRABBING if self.page.platform == ft.PagePlatform.MACOS else ft.MouseCursor.CLICK
            e.control.update()

        # Reset our mouse cursor when leaving the drag target
        def hide_accept_mc(e: ft.Event[ft.DragTarget]):
            e.control.content.mouse_cursor = None
            e.control.update()

        # Adds the widget to the stack if its not there
        def accept_drag(e: ft.DragTargetEvent):
            
            draggable = e.page.get_control(e.src_id)
            widget_id = draggable.data

            # Protect against folders dragged in
            if not isinstance(widget_id, str):
                self.page.show_dialog(shad.Toast("Folders cannot be added onto the map.", duration=ft.Duration(seconds=8)))
                return

            # Protect against widgets already on the map
            if widget_id in self.data['widgets']:
                self.page.show_dialog(shad.Toast("Widget is already on the map.", duration=ft.Duration(seconds=8)))
                return

            widget = self.story.get_widget_by_id(widget_id)
            if not widget:  # Should be impossible, but protect errors
                print("Error finding widget for id: ", widget_id)
                return

            new_position = (e.local_position.x, e.local_position.y)
            self.data['widgets'][widget_id] = new_position

            self.build_map_ctrls()
            self.update()

        self.connections_stack.controls.clear()
        self.edges_canvas.shapes.clear()

        # Add our background and edges canvas to the stack
        self.connections_stack.controls.extend([
            ft.Container(
                image=ft.DecorationImage("flow_chart_background.png", repeat=ft.ImageRepeat.REPEAT),
                expand=True, border_radius=4, width=FIXED_STACK_WIDTH, height=FIXED_STACK_HEIGHT, 
            ),
            self.edges_canvas,
        ])

        # Go through our data and draw the edges and icons onto the stack
        for connection in self.data['connections'][::-1]:

            widget1 = self.story.get_widget_by_id(connection.get('widget1_id'))
            widget2 = self.story.get_widget_by_id(connection.get('widget2_id'))
            if not widget1 or not widget2:  # Remove outdated connections from data (from widgets removed from stack)
                self.data['connections'].remove(connection)
                continue

            # Add the edge (line) between widgets and icon to represent the connection
            self.edges_canvas.shapes.append(self.ConnectionEdge(self, connection))
            self.connections_stack.controls.append(self.ConnectionIcon(self, connection))

        
        
        # Go through our data and add nodes of all our widgets
        for widget_id, position in self.data.get('widgets').items():
                    
            ref_widget = self.story.get_widget_by_id(widget_id)
            if ref_widget is None:
                continue
            self.connections_stack.controls.append(
                self.WidgetNode(widget_id, self, ref_widget, position)
                
            )

        # Re-add the drag target to allow new widgets to be dropped onto the map
        self.connections_stack.controls.append(
            ft.DragTarget(
                ft.Container(expand=True, ignore_interactions=True),
                expand=True, group="widgets",
                on_accept=accept_drag,
                on_will_accept=show_accept_mc,
                on_leave=hide_accept_mc
            ),
        )
            

    # Called after any changes happen to the data that need to be reflected in the UI
    def build(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        super().build()

        # Canvas that shows the drawn lines between widgets for their connections and icons
        self.edges_canvas = cv.Canvas(expand=True)

        # Create the stack to hold our bank, widgetacter nodes, and connections canvas
        self.connections_stack = ft.Stack(
            [], 
            expand=True, alignment=ft.Alignment.CENTER_LEFT, 
            width=FIXED_STACK_WIDTH, height=FIXED_STACK_HEIGHT, 
        ) 

        self.build_map_ctrls()
        

        # Interactive viewer to hold the stack for UI manipulation
        self.iv = ft.InteractiveViewer(
            content=self.connections_stack,
            expand=True, 
            constrained=False,
            scale_factor=800, boundary_margin=1500,
            min_scale=0.02, max_scale=3.0,
            on_interaction_end=self.handle_iv_transform
        )

        self.sidebar_notes_label.margin = None

        # Info container on the right to show details of our edges and nodes
        self.sidebar_body.controls.extend([
            self.sidebar_notes_label,
            self.sidebar_notes_column
        ])


        self.content = ft.Stack([
            self.iv,
            ft.Row(
                [self.toggle_sidebar_visibility_button, self.sidebar], 
                spacing=0, expand=True, alignment=ft.MainAxisAlignment.END, 
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
        ], expand=True, alignment=ft.Alignment.CENTER_RIGHT)


        
        
    # Upon first creation, alert users how to add widgets to the stack
    def did_mount(self):
        if self.data.get('show_alert', True) == True:
            self.page.show_dialog(shad.Toast("Drag widgets from the rail to add them to the map.", duration=ft.Duration(seconds=8)))
            self.update_data(**{'show_alert': False})
        self.page.run_task(self.transform_iv)
        