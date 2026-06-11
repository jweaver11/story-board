'''
Class for showing all our characters laid out in a family tree view.
'''

import flet as ft
from models.widget import Widget
from models.views.story import Story
from utils.verify_data import verify_data
from models.app import app
import flet.canvas as cv
from models.mini_widgets.character_connection import CharacterConnection
from styles.snack_bar import SnackBar
from styles.menu_option_style import MenuOptionStyle
from styles.icons import connection_icons
from styles.colors import colors

# Add label to the connection type. Allow changable symbols, colors, styles, etc
class CharacterConnectionMap(Widget):
    # Constructor
    def __init__(self, name: str, page: ft.Page, directory_path: str, story: Story, data: dict=None, is_rebuilt: bool = False):

        # Check if we're new and need to create file
        is_new = False
        if data is None:
            is_new = True

        # Parent class constructor
        super().__init__(
            title = name,  
            page = page,   
            directory_path = directory_path, 
            story = story,   
            data = data,    
            is_rebuilt = is_rebuilt
        )

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            object=self,   # Pass in our own data so the function can see the actual data we loaded
            required_data={
                # Widget data
                'tag': "character_connection_map",
                'color': app.settings.data.get('default_character_connection_map_color'),
                'description': '',
                'spider_web_view': False, # Whether lines/edges between characters are straight or have 3 segments
                'characters': {
                    #'id': (position) # position of the character on the map
                },
                'connections': [    # List of our connections
                    #{
                        # char 1 key: str
                        # char 1 key: str
                        # icon: str -- icon of the connection
                        # color: str  -- color of the drawn line and icon for the connection
                    #}
                ],  
            },
        )


        # Saving creates the file if we're new
        if is_new:
            self.p.run_task(self.save_dict)
    
        # State tracking
        self.char1: str = None
        self.char2: str = None
        self.is_dragging = False

        self.character_bank: ft.Column = None
        self.connections_stack: ft.Stack = None
        self.cs_width: int = 0
        self.cs_height: int = 0
        
        # Requires all widgets to be loaded first, so story calls reload_widget first
        if self.visible:
            self.reload_widget()

    class CharacterNode(ft.GestureDetector):
        def __init__(self, char_id: str, widget: 'CharacterConnectionMap', color, char_name: str, image: str, position: tuple=None):
            self.char_id = char_id
            self.widget = widget
            self.image = image
            self.color = color
            self.name = char_name
            self.position = position
            self.in_character_bank: bool = not position 

            # Our displayed content when dragging from char bank to stack to show as moving feedback
            self.dragging_content: ft.Container = None
            self.is_dragging: bool = False

            super().__init__(
                content=self.build_content(),
                on_enter=self._highlight,
                on_exit=self._stop_highlight,
                
                on_pan_start=self.start_new_connection if not self.in_character_bank else self._start_drag,   # Show line to follow mouse
                on_pan_update=self._update_line if not self.in_character_bank else self.move_char_node,   # Update line to follow mouse
                on_pan_end=self._create_new_connection if not self.in_character_bank else self._drag_end,  
                left=position[0] if position else None,
                top=position[1] if position else None,
                animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN) if not self.in_character_bank else None,
                offset=ft.Offset(-0.5, -0.5) if self.position else None,
                #width=90,
                #height=90,
                mouse_cursor=ft.MouseCursor.PRECISE if not self.in_character_bank else ft.MouseCursor.MOVE,
                data={'id': self.char_id, 'position': self.position},   
            )

        async def start_new_connection(self, e: ft.DragStartEvent):
            self.is_dragging = True
            self.widget.char1 = e.control.data
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
            if not self.widget.char1 or not self.widget.char2:
                self.widget.char1 = None
                self.widget.char2 = None
                self.update()
                return  
            
            # Don't allow connections to self
            if self.widget.char1.get('id') == self.widget.char2.get('id'):    # Don't allow connections to self
                return  
            
            # Create the new connection
            new_connection = {
                'char1_id': self.widget.char1.get('id'),
                'char2_id': self.widget.char2.get('id'),
                'color': "#FFFFFF",
                'icon': 'link'
            }

            # If the connection already exists, delete it and return
            for i, connection in enumerate(self.widget.data['connections']):
                if (connection['char1_id'] == new_connection['char1_id'] and connection['char2_id'] == new_connection['char2_id']) or (connection['char1_id'] == new_connection['char2_id'] and connection['char2_id'] == new_connection['char1_id']):
                    self.widget.data['connections'].remove(connection)  # Remove from data
                    await self.widget.save_dict()   # Save
                    self.widget.connections_canvas.shapes.pop(i)    # Remove the edge drawing
                    
                    for j, icon in enumerate(self.widget.connections_stack.controls[:]):
                        if isinstance(icon, self.widget.ConnectionIcon) and ((icon.char1_id == new_connection['char1_id'] and icon.char2_id == new_connection['char2_id']) or (icon.char1_id == new_connection['char2_id'] and icon.char2_id == new_connection['char1_id'])):
                            self.widget.connections_stack.controls.pop(j)
                    self.widget.connections_stack.update()
                    return
            
            

            # Save new edget to data with source, target, start, end, and default color
            self.widget.data['connections'].append(new_connection)
            await self.widget.save_dict()

            # Reset state trackers
            self.widget.char1 = None
            self.widget.char2 = None

            # Draw this new connection and give it an icon
            self.widget.connections_canvas.shapes.append(self.widget.ConnectionEdge(self.widget, new_connection))
            self.widget.connections_stack.controls.append(self.widget.ConnectionIcon(self.widget, new_connection))
            self.widget.connections_stack.update()

        # Used for building our content in case we need to add it temporarily when dragging from the character bank
        def build_content(self) -> ft.Container:

            # Called to build a connector if this character node is outside the character bank
            def build_connector() -> ft.GestureDetector:

                # Return our icon that used to create connections
                return ft.GestureDetector(
                    ft.Container(
                        ft.Text(self.name, weight=ft.FontWeight.W_500), 
                        expand=True, 
                        #border=ft.Border.all(2, ft.Colors.ON_SURFACE_VARIANT),
                        alignment=ft.Alignment.CENTER, 
                        padding=ft.Padding.symmetric(horizontal=6, vertical=4), 
                        border_radius=4, 
                        width=90,
                    ),
                    mouse_cursor=ft.MouseCursor.MOVE,
                    data={'id': self.char_id, 'position': self.position},                            
                    #on_enter=_highlight_node,   # Highlight and set target source trackers if we enter a node while dragging from another
                    on_pan_start=self._start_drag,
                    on_pan_end=self._drag_end,
                    on_pan_update=self.move_char_node,
                    #on_exit=_stop_highlight_node,  
                )
            
            return ft.Container(
                ft.Column([
                    ft.Container(
                        ft.Text(self.name, weight=ft.FontWeight.W_500), 
                        expand=True, 
                        #border=ft.Border.all(2, ft.Colors.ON_SURFACE_VARIANT),
                        alignment=ft.Alignment.CENTER, 
                        padding=ft.Padding.symmetric(horizontal=6, vertical=2), 
                        border_radius=4, 
                        width=100,
                        margin=ft.Margin.only(bottom=2)
                    ) if self.in_character_bank else build_connector(),  
                    ft.Divider(ft.Colors.SURFACE_CONTAINER_LOW, 2, 6, trailing_indent=6),
                    ft.Image(self.image, 100, 100, expand=True) if self.image else ft.Icon(ft.Icons.PERSON_OUTLINE_OUTLINED, self.color, size=100),
                                      
                ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, ),
                border_radius=8,
                #padding=ft.Padding.all(8),
                alignment=ft.Alignment.TOP_CENTER,
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                data={'char_id': self.char_id},
                shadow=ft.BoxShadow(1, 1, blur_style=ft.BlurStyle.OUTER),
                width=100,
            )


        # Highlight our character node when we hover over it
        async def _highlight(self, e=None):
            ''' When we hover over a character node, we want to highlight it and show its connections '''
            if self.widget.char1:
                self.widget.char2 = e.control.data
            self.content.shadow = ft.BoxShadow(4, 4, ft.Colors.with_opacity(0.3, self.color))
            self.update()

        # Stop highlighting our character node when we stop hovering over it. Ignore if we're dragging
        async def _stop_highlight(self, e=None):
            ''' When we stop hovering over a character node, we want to stop highlighting it '''
            if self.is_dragging:
                
                return
            if self.widget.char2:
                self.widget.char2 = None
            self.content.shadow = ft.BoxShadow(1, 1, blur_style=ft.BlurStyle.OUTER),
            self.update()

        async def _start_drag(self, e: ft.DragStartEvent):
            
            self.is_dragging = True
            
            # If we're still in the character bank, don't try and move us, just reflect us moving on the stack
            if self.in_character_bank:

                # Create our content feedback when dragging. Give feedback a shadow, and matching offset
                self.dragging_content = self.build_content()
                self.dragging_content.shadow = ft.BoxShadow(8, 8, ft.Colors.with_opacity(0.2, self.color))
                self.dragging_content.offset = ft.Offset(-0.5, -0.5)
                self.dragging_content.animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN)
                
                # Position us on the local stack based on where the drag starts globally for the top position
                self.dragging_content.left = 50     # Just use half the character bank width for left position
                top_ratio = e.global_position.y / self.page.height
                self.dragging_content.top = top_ratio * self.widget.cs_height 
                
                # Add positioned feedback to the stack
                self.widget.connections_stack.controls.append(self.dragging_content)
                self.widget.connections_stack.update()   
            
        # Moves our character node or feedback on the stack
        async def move_char_node(self, e: ft.DragUpdateEvent):
            
            # If we're in the char bank, reflect our movement on the appended container on the stack
            if self.in_character_bank:

                self.dragging_content.left += e.local_delta.x
                self.dragging_content.top += e.local_delta.y
                self.dragging_content.update()

            # Otherwise, we're already on the map, so move our actual node
            else:
                
                self.left += e.local_delta.x
                self.top += e.local_delta.y
                self.update()

                # Call highlight if we're over the character bank and not already highlited
                if self.left <= 140:
                    if not self.widget.character_bank_container.shadow:
                        await self.widget.highlight_character_bank()
                # Otherwise remove the highlight if its active
                else:
                    if self.widget.character_bank_container.shadow:
                        await self.widget.stop_highlight_character_bank()

                # Update the data in real time, but don't call a save until done dragging
                self.widget.data['characters'][self.char_id] = (self.left, self.top)

                # Update any edges connected to this character node as we move
                for connection in self.widget.connections_canvas.shapes:
                    if isinstance(connection, self.widget.ConnectionEdge) and (connection.char1_id == self.char_id or connection.char2_id == self.char_id):
                        connection.draw_connection()
                        connection.update()

                for icon in self.widget.connections_stack.controls:
                    if isinstance(icon, self.widget.ConnectionIcon) and (icon.char1_id == self.char_id or icon.char2_id == self.char_id):
                        icon.build_icon()
                        icon.update()

        # Handles when we stop dragging
        async def _drag_end(self, e: ft.DragEndEvent):
            self.is_dragging = False
            
            # If we're dragging from the bank
            if self.in_character_bank:

                # If we did not leave the character bank, or are dragged past the stack limits, remove the feedback and return early
                if self.dragging_content.left < 140 or self.dragging_content.top < 0 or self.dragging_content.top > self.widget.cs_height or self.dragging_content.left > self.widget.cs_width:  
                    self.widget.connections_stack.controls.remove(self.dragging_content)
                    self.widget.connections_stack.update()
                    self.widget.char1 = None
                    return
                
                self.in_character_bank = False

                # Add to our widgets data
                self.widget.data['characters'][self.char_id] = (self.dragging_content.left, self.dragging_content.top)
                await self.widget.save_dict()   
                
                

                # Remove our feedback from the overly, and ourself from the character bank, and add ourselves to the stack with the correct position
                self.widget.connections_stack.controls.remove(self.dragging_content)
                self.widget.character_bank.controls.remove(self)
                self.widget.connections_stack.controls.append(self)

                self.left = self.dragging_content.left
                self.top = self.dragging_content.top
                self.offset = ft.Offset(-0.5, -0.5)
                self.animate_position = ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN)
                self.on_pan_start = self.start_new_connection
                self.on_pan_update = self._update_line
                self.on_pan_end = self._create_new_connection
                self.mouse_cursor = ft.MouseCursor.PRECISE

                self.widget.connections_stack.update()
                self.content = self.build_content() # Rebuild our content AFTER we are re-mounted to the page, or get sync issues
                self.update()


            # Otherwise we're dragging from the stack already
            else:
                if self.left < 140 or self.top < 0:  # If we never left the character bank, snap back to originl position.
                    self.widget.connections_stack.controls.remove(self)
                    self.widget.character_bank.controls.append(self)

                    self.in_character_bank = True
                    self.left = None
                    self.top = None
                    self.offset = None
                    self.animate_position = None
                    self.on_pan_start = self._start_drag
                    self.on_pan_update = self.move_char_node
                    self.on_pan_end = self._drag_end
                    self.mouse_cursor = ft.MouseCursor.MOVE

                    # Remove the edge from the canvas
                    for connection in self.widget.connections_canvas.shapes[:]:
                        if isinstance(connection, self.widget.ConnectionEdge) and (connection.char1_id == self.char_id or connection.char2_id == self.char_id):
                            self.widget.connections_canvas.shapes.remove(connection)

                    # Remove the icon from the stack
                    for icon in self.widget.connections_stack.controls[:]:
                        if isinstance(icon, self.widget.ConnectionIcon) and (icon.char1_id == self.char_id or icon.char2_id == self.char_id):
                            self.widget.connections_stack.controls.remove(icon)

                    # Remove the connection from the data
                    for connection in self.widget.data['connections'][:]:
                        if connection['char1_id'] == self.char_id or connection['char2_id'] == self.char_id:
                            self.widget.data['connections'].remove(connection)
                    

                    self.widget.connections_stack.update()
                    await self._stop_highlight()
                    self.content = self.build_content()
                    self.update()
                    
                    self.in_character_bank = True
                    self.widget.char1 = None
                    self.widget.char2 = None    

                    # Remove from our widgets data
                    self.widget.data['characters'].pop(self.char_id, None)
                    await self.widget.save_dict()
                    return
                
                # Update our positional data
                await self.widget.save_dict()
                

    # Just for drawing the connection on the canvas, and icon on the stack
    class ConnectionEdge(cv.Path):
        def __init__(self, widget: 'CharacterConnectionMap', data: dict):

            # Set our attributes
            self.char1_id = data.get('char1_id')
            self.char2_id = data.get('char2_id')
            self.color = data.get('color', "#FFFFFF")
            self.widget = widget
            super().__init__(data=data)

            # Set our content
            self.draw_connection()
            
        # Draws our connection between our two character Nodes based on position
        def draw_connection(self):

            self.start_position = self.widget.data['characters'].get(self.char1_id, None)
            self.end_position = self.widget.data['characters'].get(self.char2_id, None)

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
        def __init__(self, widget: 'CharacterConnectionMap', data: dict):
            self.char1_id = data.get('char1_id')
            self.char2_id = data.get('char2_id')
            self.color = data.get('color', "#FFFFFF")
            self.icon = data.get('icon', '')
            self.widget = widget
            super().__init__(
                data=data,
                on_enter=self._highlight_icon,
                on_exit=self._stop_highlight_icon,
                on_secondary_tap=lambda _: self.widget.story.open_menu(self._get_menu_options()),
                on_tap=lambda _: self.widget.story.open_menu(self._get_menu_options()),
                offset = ft.Offset(-0.5, -0.5),
                mouse_cursor=ft.MouseCursor.CLICK,
            )
            self.build_icon()   # Set our content

        def _get_menu_options(self):

            # TODO: Better styling, add color and icon change options, and delete connection
            async def _new_icon_clicked(e: ft.Event):
                icon_str = e.control.data
                self.icon = icon_str
                for connection in self.widget.data['connections']:
                    if (connection['char1_id'] == self.char1_id and connection['char2_id'] == self.char2_id) or (connection['char1_id'] == self.char2_id and connection['char2_id'] == self.char1_id):
                        connection['icon'] = icon_str
                        await self.widget.save_dict()
                self.build_icon()
                self.update()
                await self.widget.story.close_menu()

            async def _delete_connection(e: ft.Event):
                for i, connection in enumerate(self.widget.data['connections']):
                    if (connection['char1_id'] == self.char1_id and connection['char2_id'] == self.char2_id) or (connection['char1_id'] == self.char2_id and connection['char2_id'] == self.char1_id):
                        self.widget.data['connections'].remove(connection)
                        await self.widget.save_dict()
                        self.widget.connections_canvas.shapes.pop(i)
                        
                        for j, icon in enumerate(self.widget.connections_stack.controls[:]):
                            if isinstance(icon, self.widget.ConnectionIcon) and ((icon.char1_id == self.char1_id and icon.char2_id == self.char2_id) or (icon.char1_id == self.char2_id and icon.char2_id == self.char1_id)):
                                self.widget.connections_stack.controls.pop(j)
                        self.widget.connections_stack.update()
                        await self.widget.story.close_menu()
                        return

            async def _change_icon_color(e: ft.Event):
                color_str = e.control.data
                self.color = color_str
                for connection in self.widget.data['connections']:
                    if (connection['char1_id'] == self.char1_id and connection['char2_id'] == self.char2_id) or (connection['char1_id'] == self.char2_id and connection['char2_id'] == self.char1_id):
                        connection['color'] = color_str
                        await self.widget.save_dict()
                self.build_icon()
                self.update()
                await self.widget.story.close_menu()
            

            return [
                 MenuOptionStyle(
                    ft.SubmenuButton(
                        ft.Row([
                            ft.Icon(ft.Icons.LINK, self.data.get('color', "primary")), 
                            ft.Text("Icon", weight=ft.FontWeight.BOLD, expand=True),
                            ft.Icon(ft.Icons.ARROW_RIGHT),
                        ], expand=True),
                        [MenuOptionStyle(
                            ft.Row([ft.Icon(icon, self.color)]),
                            data=icon_str,
                            on_click=_new_icon_clicked   
                        ) for icon_str, icon in connection_icons.items()],
                        menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                        style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        tooltip="Change this connections icon"
                    ),
                    no_padding=True, no_effects=True
                ),
                MenuOptionStyle(
                    ft.SubmenuButton(
                        ft.Row([
                            ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.data.get('color', "primary")), 
                            ft.Text("Color", weight=ft.FontWeight.BOLD, expand=True),
                            ft.Icon(ft.Icons.ARROW_RIGHT),
                        ], expand=True),
                        [ft.MenuItemButton(
                            content=ft.Text(color.capitalize(), weight=ft.FontWeight.BOLD, color=color),
                            on_click=_change_icon_color, close_on_click=True, data=color,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click")
                        ) for color in colors],
                        menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                        style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        tooltip="Change this connections color"
                    ),
                    no_padding=True, no_effects=True
                ),
                
                MenuOptionStyle(
                    on_click=_delete_connection,
                    content=ft.Row([
                        ft.Icon(ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR,),
                        ft.Text(
                            "Delete", 
                            weight=ft.FontWeight.BOLD, 
                            
                        ), 
                    ]),
                ),
            ]
                
        # Highlight the node
        async def _highlight_icon(self, e: ft.PointerEvent):
            e.control.content.shadow = ft.BoxShadow(4, 4, ft.Colors.with_opacity(0.5, self.color))
            e.control.update()

        # Stop highlighting the node
        async def _stop_highlight_icon(self, e: ft.PointerEvent):
            e.control.content.shadow = None
            e.control.update()

        def build_icon(self):
            start_position = self.widget.data['characters'].get(self.char1_id, None)
            end_position = self.widget.data['characters'].get(self.char2_id, None)

            mid_position = ((start_position[0] + end_position[0]) / 2, (start_position[1] + end_position[1]) / 2)

            self.left = mid_position[0]
            self.top = mid_position[1]
            self.content = ft.Container(
                ft.Icon(connection_icons.get(self.icon, ft.Icons.ERROR), self.color, size=30),
                shape=ft.BoxShape.CIRCLE,
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                padding=ft.Padding.all(6)
            )

            

    # Highlight the character bank
    async def highlight_character_bank(self, e=None):
        self.character_bank_container.shadow = ft.BoxShadow(4, 4, ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE))
        self.character_bank_container.update()

    # Stop highlighting the character bank
    async def stop_highlight_character_bank(self, e=None):
        self.character_bank_container.shadow = None
        self.character_bank_container.update()
    

    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''
        
        # Set size of stack needed for ratios
        async def _set_connection_stack_size(e: ft.LayoutSizeChangeEvent):
            self.cs_width = e.width
            self.cs_height = e.height
               
        self.reload_tab()

        self.character_bank = ft.Column(
            [
                ft.Text("Character Bank", theme_style=ft.TextThemeStyle.LABEL_LARGE, weight=ft.FontWeight.W_500, italic=True, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Divider(2, 2)
            ], 
            scroll=ft.ScrollMode.AUTO, 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        self.character_bank_container = ft.Container(
            ft.GestureDetector(
                self.character_bank,
                on_enter=self.highlight_character_bank, on_exit=self.stop_highlight_character_bank
            ),
            border=ft.Border.only(right=ft.BorderSide(2, ft.Colors.OUTLINE_VARIANT)),
            width=140,
            expand=True,
            padding=ft.Padding.all(10),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        )

        # Go through our stor
        for widget in self.story.widgets.values():
            if widget.data.get('tag') == 'character':
                if widget.data.get('id') in self.data['characters']:
                    continue
                char_id = widget.data.get('id')
                color = widget.data.get('color')
                char_name = widget.title
                image = widget.data.get('image_base64')

                self.character_bank.controls.append(self.CharacterNode(char_id, self, color, char_name, image))

        self.character_bank.controls.append(ft.Container(expand=True))

        # Canvas that shows the drawn lines between characters for their connections and icons
        self.connections_canvas = cv.Canvas(
            content=ft.GestureDetector(
                expand=True,
                on_hover=self._get_coords,
                hover_interval=20,
            ),
            expand=True, 
            resize_interval=100,
        )

        # Create the stack to hold our bank, character nodes, and connections canvas
        self.connections_stack = ft.Stack([
        
            self.connections_canvas,
            ft.Column([self.character_bank_container])
            
        ], expand=True, alignment=ft.Alignment.TOP_LEFT, on_size_change=_set_connection_stack_size) 

        # Have a new 'edge' drawn for each connection
        for connection in self.data['connections']:

            # Add the edge (line) between characters and icon to represent the connection
            self.connections_canvas.shapes.append(self.ConnectionEdge(self, connection))
            self.connections_stack.controls.append(self.ConnectionIcon(self, connection))
        
        

        # Add all our characters that are already on the map to the stack at the right positions
        for char_id, position in self.data['characters'].items():
            
            char = self.story.get_widget_by_id(char_id)
            if char is None:
                continue
            self.connections_stack.controls.append(
                self.CharacterNode(
                    char_id, 
                    self, 
                    char.data.get('color'), 
                    char.title, 
                    char.data.get('image_base64', ''), 
                    position
                )
                
            )

        # Set our content to the body_container (from Widget class) as the body we just built
        self.body_container.content = self.connections_stack

        self._render_widget()
            


