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
                'characters': {
                    #'id': {position} # position of the character on the map
                },
                'connections': [    # List of our connections
                    #{
                        # char 1 key: str
                        # char 1 key: str
                        # description: str
                        # icon: str -- icon of the connection
                        # color: str  -- color of the drawn line and icon for the connection
                        # char1 position: tuple(x,y) -- position of the char1 icon on the map, relative to the center (0,0)
                        # char2 position: tuple(x,y) -- position of the char2 icon on the
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
                on_pan_start=self._start_drag,
                on_pan_end=self._drag_end,
                on_pan_update=self.move_char_node,
                left=position[0] if position else None,
                top=position[1] if position else None,
                animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN) if not self.in_character_bank else None,
                offset=ft.Offset(-0.5, -0.5) if self.position else None,
                width=80,
                mouse_cursor=ft.MouseCursor.MOVE,
                data={'id': self.char_id, 'position': self.position},   
            )

        # Used for building our content in case we need to add it temporarily when dragging from the character bank
        def build_content(self) -> ft.Container:

            # Called to build a connector if this character node is outside the character bank
            def build_connector() -> ft.GestureDetector:

                # Highlight the node
                async def _highlight_node(e: ft.PointerEvent):
                    if self.widget.char1:
                        self.widget.char2 = e.control.data
                        print("Set target character to:", self.widget.char2)
                    e.control.content.shadow = ft.BoxShadow(8, 8, ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE))
                    e.control.update()

                # Stop highlighting the node
                async def _stop_highlight_node(e: ft.PointerEvent):
                    e.control.content.shadow = None
                    e.control.update()

                async def start_new_connection(e: ft.DragStartEvent):
                    self.widget.char1 = e.control.data
                    print("Set source character to:", self.widget.char1)
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

                # Creates our new edge (link) between nodes
                async def _create_new_connection(e: ft.PointerEvent):
                    
                    # Remove our visual feedback
                    self.page.overlay.pop()
                    self.page.update()

                    # If its an incomplete edge (we didn't end on another node), reset and exit
                    if not self.widget.char1 or not self.widget.char2:
                        self.widget.char1 = None
                        self.widget.char2 = None
                        print("Incomplete connection, missing source or target character. Resetting.")
                        return  
                    
                    # Don't allow connections to self
                    if self.widget.char1.get('id') == self.widget.char2.get('id'):    # Don't allow connections to self
                        self.page.show_dialog(SnackBar("Cannot connct a character to themself."))
                        return  
                    
                    start_position = self.widget.char1.get('position')
                    end_position = self.widget.char2.get('position')

                    new_connection = {
                        'char1_id': self.widget.char1.get('id'),
                        'char2_id': self.widget.char2.get('id'),
                        'color': "#FFFFFF",
                        'char1_position': start_position,  
                        'char2_position': end_position
                    }

                    # If the connection already exists, delete it and return
                    for i, connection in enumerate(self.widget.data['connections']):
                        if (connection['source'] == new_connection['source'] and connection['target'] == new_connection['target']) or (connection['source'] == new_connection['target'] and connection['target'] == new_connection['source']):
                            self.widget.data['connections'].remove(connection)
                            await self.widget.save_dict()
                            self.widget.connections_canvas.shapes.pop(i)
                            self.widget.connections_canvas.update()
                            print("Connection exists, deleting it instead")
                            return
                    
                    

                    # Save new edget to data with source, target, start, end, and default color
                    self.widget.data['connections'].append(new_connection)
                    await self.widget.save_dict()
                    print("Created new connection:", new_connection)

                    # Reset state trackers
                    self.widget.char1 = None
                    self.widget.char2 = None

                    self.widget.connections_canvas.shapes.append(
                        self.widget.ConnectionEdge(
                            self.widget,
                            new_connection
                        )
                    )
                    self.widget.connections_canvas.update()

                    
                    
                return ft.GestureDetector(
                    ft.Container(ft.Icon(ft.Icons.CIRCLE_OUTLINED, scale=1.25), shape=ft.BoxShape.CIRCLE), 
                    mouse_cursor=ft.MouseCursor.PRECISE,
                    data={'id': self.char_id, 'position': self.position},                            
                    on_enter=_highlight_node,   # Highlight and set target source trackers if we enter a node while dragging from another
                    on_pan_start=start_new_connection,   # Show line to follow mouse
                    on_pan_update=_update_line,   # Update line to follow mouse
                    on_pan_end=_create_new_connection,  
                    on_exit=_stop_highlight_node,  
                )
            return ft.Container(
                ft.Column([
                    ft.Image(self.image, 50, 50) if self.image else ft.Icon(ft.Icons.PERSON_OUTLINE_OUTLINED, self.color, size=40),
                    ft.Text(self.name),
                    ft.Container() if self.in_character_bank else build_connector()
                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                shape=ft.BoxShape.CIRCLE,
                data={'char_id': self.char_id}
            )


        # Highlight our character node when we hover over it
        async def _highlight(self, e=None):
            ''' When we hover over a character node, we want to highlight it and show its connections '''
            if self.widget.char1:
                self.widget.char2 = e.control.data
            self.content.shadow = ft.BoxShadow(8, 8, ft.Colors.with_opacity(0.2, self.color))
            self.update()

        # Stop highlighting our character node when we stop hovering over it. Ignore if we're dragging
        async def _stop_highlight(self, e=None):
            ''' When we stop hovering over a character node, we want to stop highlighting it '''
            if self.is_dragging:
                return
            self.content.shadow = None
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
                

            else:
                pass
            
        # Moves our character node or feedback on teh stack
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
                if self.left <= 100:
                    if not self.widget.character_bank_container.shadow:
                        await self.widget.highlight_character_bank()

                # Otherwise remove the highlight if its active
                else:
                    if self.widget.character_bank_container.shadow:
                        await self.widget.stop_highlight_character_bank()

        # Handles when we stop dragging
        async def _drag_end(self, e: ft.DragEndEvent):
            self.is_dragging = False
            
            # If we're dragging from the bank
            if self.in_character_bank:

                # If we did not leave the character bank, or are dragged past the stack limits, remove the feedback and return early
                if self.dragging_content.left < 100 or self.dragging_content.top < 0 or self.dragging_content.top > self.widget.cs_height or self.dragging_content.left > self.widget.cs_width:  
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

                # Match our actual node to the feedback content
                self.left = self.dragging_content.left
                self.top = self.dragging_content.top
                self.offset = ft.Offset(-0.5, -0.5)
                self.animate_position = ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN)
                self.content = self.build_content()

                self.widget.connections_stack.update()

                #self.widget.reload_edges()

            # Otherwise we're dragging from the stack already
            else:
                if self.left < 100 or self.top < 0:  # If we never left the character bank, snap back to originl position.
                    self.widget.connections_stack.controls.remove(self)
                    self.widget.character_bank.controls.append(self)

                    self.left = None
                    self.top = None
                    self.offset = None
                    self.animate_position = None
                    self.content = self.build_content()

                    self.widget.connections_stack.update()
                    await self._stop_highlight()
                    
                    self.in_character_bank = True
                    self.widget.char1 = None

                    # Remove from our widgets data
                    self.widget.data['characters'].pop(self.char_id, None)
                    await self.widget.save_dict()
                    
                    return
                
                # Update our positional data
                self.widget.data['characters'][self.char_id] = (self.left, self.top)
                await self.widget.save_dict()

                # Re-Draw edges
                

    # Just for drawing the connection on the canvas, and icon on the stack
    class ConnectionEdge(cv.Path):
        def __init__(self, widget: 'CharacterConnectionMap', data: dict):
            start_position = data.get('char1_position', ())
            end_position = data.get('char2_position', ())
            color = data.get('color', "#FFFFFF")
            #description = data.get('description', '')
            super().__init__(
                [
                    cv.Path.MoveTo(start_position[0], start_position[1]), 
                    cv.Path.LineTo(end_position[0], end_position[1]), 
                ],
                paint=ft.Paint(color, stroke_width=3, style="stroke", anti_alias=True),
                data=data
            )
            
            self.widget = widget
            self.color = color

        

    # Highlight the character bank
    async def highlight_character_bank(self, e=None):
        self.character_bank_container.shadow = ft.BoxShadow(1, 1, ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE))
        self.character_bank_container.update()

    # Stop highlighting the character bank
    async def stop_highlight_character_bank(self, e=None):
        self.character_bank_container.shadow = None
        self.character_bank_container.update()
    

    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # TODO: 
        # Update connections cv.Paths after/during a character node drag movement
        # Fix bug where recently added char nodes don't allow for new connections until reload_widget is called

        
        
        # Set size of stack needed for ratios
        async def _set_connection_stack_size(e: ft.LayoutSizeChangeEvent):
            self.cs_width = e.width
            self.cs_height = e.height



               
        self.reload_tab()

        self.character_bank = ft.Column(
            [], scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
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
                on_secondary_tap=lambda _: self.story.open_menu(self._get_menu_options()),
                on_hover=self._get_coords,
                #drag_interval=50, 
                hover_interval=20,
                #on_pan_start=lambda: print("Pan Started")
            ),
            expand=True, resize_interval=100,
            #on_resize=self._rebuild_canvas, 
        )

        for connection in self.data['connections']:
            print("Loading connection: ", connection)
            self.connections_canvas.shapes.append(
                self.ConnectionEdge(
                    self,
                    connection
                )
            )
        
        
        self.connections_stack = ft.Stack([
        
            self.connections_canvas
            
        ], expand=True, alignment=ft.Alignment.TOP_LEFT, on_size_change=_set_connection_stack_size) 

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

        # TODO: Go through connected characters and add their icons to the map
        # Go through the added character icons and draw the connections between them, with room for icons
        # Spider web (straight lines) vs tree lines (2 point, 3 line segment) options??

        self.character_bank_container = ft.Container(
            ft.GestureDetector(
                self.character_bank,
                on_enter=self.highlight_character_bank, on_exit=self.stop_highlight_character_bank
            ),
            border=ft.Border.only(right=ft.BorderSide(2, ft.Colors.OUTLINE_VARIANT)),
            width=100,
            expand=True,
            padding=ft.Padding.symmetric(vertical=10),
        )

        self.connections_stack.controls.append(ft.Column([self.character_bank_container]))



        iv = ft.InteractiveViewer(
            content=self.connections_stack, expand=True,
            scale_factor=750, #boundary_margin=50,
            min_scale=0.5, max_scale=2.0, scale=1.0,
        )
        
        
        # Set our content to the body_container (from Widget class) as the body we just built
        #self.body_container.content = iv


        self.body_container.content = self.connections_stack

        self._render_widget()
            


