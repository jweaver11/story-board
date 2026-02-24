'''
UI styling for the main workspace area of appliction that holds our widgets (tabs)
Returns our container with our formatting areas inside the workspace area.
The stories 'mast_stack' holds our 'master_row', which contains our five pins: top, left, main, right, and bottom.
Overtop that, we append our drag targets when we start dragging a widget (tab). Thats why its a stack
'''

import flet as ft
from models.app import app
from models.views.story import Story
import json
from styles.colors import dark_gradient
from styles.snack_bar import SnackBar

# Our workspace object that is stored in our story object
class Workspace(ft.Container):
    # Constructor
    def __init__(self, page: ft.Page, story: Story):

        # Set our container properties for the workspace
        super().__init__(
            expand=True,
            alignment=ft.alignment.center,
            padding=ft.padding.only(top=10, bottom=10, left=2, right=10),
        )

        self.p = page
        self.story = story

        self.minimum_pin_height = int(self.p.height / 5)
        self.minimum_pin_width = int(self.p.width / 10)

        # Creates our 4 side pin locations for our widgets inside our workspace. These are placed directly on the page
        self.top_pin = ft.Row(spacing=10, height=story.data['top_pin_height'], controls=[])
        self.left_pin = ft.Column(spacing=10, width=story.data['left_pin_width'], controls=[])
        self.right_pin = ft.Column(spacing=10, width=story.data['right_pin_width'], controls=[])
        self.bottom_pin = ft.Row(spacing=10, height=story.data['bottom_pin_height'], controls=[])

        # Main pin is not rendered directly since it changes based on active tab when more than one widget is present
        self.main_pin = []

        # Pin drag targets
        self.top_pin_drag_target = ft.DragTarget(
            group="widgets", 
            content=ft.Container(expand=True, height=self.story.data.get('top_pin_height', int(self.p.height/5)), bgcolor=ft.Colors.ON_SURFACE, opacity=0, border_radius=8, margin=ft.margin.only(left=8, right=8),), 
            on_accept=lambda e: self.pin_drag_accept(e, "top"), on_will_accept=self.on_hover_pin_drag_target, on_leave=self.on_stop_hover_drag_target,
        )
        self.left_pin_drag_target = ft.DragTarget(
            group="widgets",
            content=ft.Container(expand=True, width=self.story.data.get('left_pin_width', int(self.p.width/10)), bgcolor=ft.Colors.ON_SURFACE, border_radius=8, opacity=0), 
            on_accept=lambda e: self.pin_drag_accept(e, "left"), on_will_accept=self.on_hover_pin_drag_target, on_leave=self.on_stop_hover_drag_target,
        )

        self.right_pin_drag_target = ft.DragTarget(
            group="widgets", 
            content=ft.Container(expand=True, width=self.story.data.get('right_pin_width', int(self.p.width/10)), bgcolor=ft.Colors.ON_SURFACE, border_radius=8, opacity=0), 
            on_accept=lambda e: self.pin_drag_accept(e, "right"), on_will_accept=self.on_hover_pin_drag_target, on_leave=self.on_stop_hover_drag_target,
        )
        self.bottom_pin_drag_target = ft.DragTarget(
            group="widgets", 
            content=ft.Container(expand=True, height=self.story.data.get('bottom_pin_height', int(self.p.height/5)), margin=ft.margin.only(left=8, right=8), bgcolor=ft.Colors.ON_SURFACE, opacity=0, border_radius=8),
            on_accept=lambda e: self.pin_drag_accept(e, "bottom"), on_will_accept=self.on_hover_pin_drag_target, on_leave=self.on_stop_hover_drag_target,
        )

        # Weird flet rendering logic, this one needs a container around the drag target to work properly
        self.main_pin_drag_target = ft.Container(
            expand=True,
            padding=ft.padding.all(8),
            content=ft.DragTarget(
                group="widgets", 
                on_accept=lambda e: self.pin_drag_accept(e, "main"), on_will_accept=self.on_hover_pin_drag_target, on_leave=self.on_stop_hover_drag_target,
                content=ft.Container(expand=True,  bgcolor=ft.Colors.ON_SURFACE, opacity=0, border_radius=8)
            )
        )

        self.pin_drag_targets = ft.Container(
            visible=True,
            expand=True,
            content=ft.Row(
                spacing=0,
                expand=True,
                controls=[
                    self.left_pin_drag_target,
                    ft.Column(
                        expand=True,
                        spacing=0,
                        controls=[
                            self.top_pin_drag_target,
                            self.main_pin_drag_target,  
                            self.bottom_pin_drag_target,
                        ]
                    ),
                    self.right_pin_drag_target,
                ]
            )
        )

        # Our master row that holds all our widgets
        self.master_widgets_row = ft.Row(spacing=0, expand=True, controls=[])

        # Master stack that holds our widgets ^ row, and drag targets overtop. TransparentPointer allows the targets to be physical but not block widgets underneath
        self.master_stack = ft.Stack(expand=True, controls=[self.master_widgets_row, ft.TransparentPointer(self.pin_drag_targets)])

        self.reload_workspace()   # Load our workspace content for the first time without updating the UI, since we're still in the constructor


    # When a draggable starts dragging, we add our drag targets to the master stack
    def show_pin_drag_targets(self, e=None):
        ''' Adds our drag targets to the master stack so we can drop our widgets into pin locations '''

        visible_top_pin_controls = [control for control in self.top_pin.controls if getattr(control, 'visible', True)]
        # If no visible in the top pin
        if len(visible_top_pin_controls) == 0:
            self.top_pin_drag_target.content.height = self.story.data.get('top_pin_height', int(self.p.height/5))

        visible_left_pin_controls = [control for control in self.left_pin.controls if getattr(control, 'visible', True)]
        # If no visible in the left pin
        if len(visible_left_pin_controls) == 0:
            self.left_pin_drag_target.content.width = self.story.data.get('left_pin_width', int(self.p.width/10))

        visible_right_pin_controls = [control for control in self.right_pin.controls if getattr(control, 'visible', True)]
        # If no visible in the right pin
        if len(visible_right_pin_controls) == 0:
            self.right_pin_drag_target.content.width = self.story.data.get('right_pin_width', int(self.p.width/10))

        visible_bottom_pin_controls = [control for control in self.bottom_pin.controls if getattr(control, 'visible', True)]
        # If no visible in the bottom pin
        if len(visible_bottom_pin_controls) == 0:
            self.bottom_pin_drag_target.content.height = self.story.data.get('bottom_pin_height', int(self.p.height/5))
        


    
    # Called when a draggable hovers over a drag target before dropping
    async def on_hover_pin_drag_target(self, e):
        ''' Makes the drag target visible for so visual feedback '''
        e.control.content.opacity = .3
        e.control.content.update()
       
    # Called when a draggable leaves a drag target
    async def on_stop_hover_drag_target(self, e):
        ''' Makes the drag target invisible again '''
        e.control.content.opacity = 0
        e.control.content.update()
        
    # Accepting drags for our five pin locations
    def pin_drag_accept(self, e, pin_location: str):

        # Reset our container to be invisible again
        e.control.content.opacity = 0
        e.control.content.update()

        # Load our event data
        event_data = json.loads(e.data)
        
        # Grab our draggable from the event
        draggable = e.page.get_control(event_data.get("src_id"))
            
        # Grab our key and set the widget
        widget_key = draggable.data

        widget = None

        for w in self.story.widgets:
            if w.data.get('key', "") == widget_key:
                widget = w
                break

        if widget is None:
            print("Error: Widget not found for drag accept")
            self.p.open(SnackBar("Error: Widget not found for drag accept"))
            return

        old_pin_location = widget.data['pin_location']

        # If we were dragged from the main pin and we were the active tab, set the first tab to new active
        if old_pin_location == "main" and widget.data['is_active_tab'] == True:

            widget.data['is_active_tab'] = False   # Deselect ourselves

            # If there are other widgets in the main pin, set the first one to active tab
            #self.self.main_pin[0].data['is_active_tab'] = True
            #self.self.main_pin[0].save_dict()
                
                

        # Set our objects pin location to the correct new location
        widget.data['pin_location'] = pin_location  

        # Even though we're not in the new pin location until we reload, we can just use the length to find our index
        if pin_location == "top":
            widget.data['index'] = len(self.top_pin.controls)
        
        elif pin_location == "left":
            widget.data['index'] = len(self.left_pin.controls)
        
        elif pin_location == "main":
            widget.data['index'] = len(self.main_pin)   

            # Set other tabs to inactive, and new one to active              
            for w in self.main_pin:
                w.data['is_active_tab'] = False        # Deselect all other main pin widgets

            widget.data['is_active_tab'] = True

        elif pin_location == "right":
            widget.data['index'] = len(self.right_pin.controls)

        elif pin_location == "bottom":
            widget.data['index'] = len(self.bottom_pin.controls)


        widget.force_size_render = True     # Force a reload in our new pin because our size changes

        # Make sure our widget is visible if it was dragged from the rail
        if not widget.visible:
            widget.toggle_visibility(value=True)      # This will save dict as well
        else:
            widget.save_dict()  

        # Apply to UI
        self.reload_workspace()

        # Reload our widget to apply size changes that some of them need
        #widget.reload_widget()        


    # Called when we drag a widget from one pin location to another
    def arrange_widgets(self):
        ''' Arranges our widgets to their correct pin locations after a change is made to their pin location.
        Also adds widgets to their correct pin locations if they are missing from any pin location '''

        story = self.story

        # Clear all pin locations first
        self.top_pin.controls.clear()
        self.left_pin.controls.clear()
        self.main_pin.clear()
        self.right_pin.controls.clear()
        self.bottom_pin.controls.clear()

        if len(story.widgets) == 0:
            return

        # Lets widgets keep their order between sessions
        ordered_widgets = sorted(story.widgets, key=lambda w: w.data.get('index', 0))


        # Go through all our widgets in the story
        for widget in ordered_widgets:

            # Check if they are visible
            if widget.visible:
    
                # Check if widget has data and pin_location
                pin_location = widget.data.get('pin_location', None)

                if pin_location is None:
                    print("Widget has no pin_location data, defaulting to main pin")
                    widget.data['pin_location'] = "main"
                    widget.save_dict()
                    self.main_pin.append(widget)
                    continue
                    
                
                # Add widget to the correct pin based on its pin_location
                if pin_location == "top":
                    self.top_pin.controls.append(widget)
                    widget.data['index'] = self.top_pin.controls.index(widget)
                elif pin_location == "left":
                    self.left_pin.controls.append(widget)
                    widget.data['index'] = self.left_pin.controls.index(widget)
                elif pin_location == "main":
                    self.main_pin.append(widget)
                    widget.data['index'] = self.main_pin.index(widget)
                elif pin_location == "right":
                    self.right_pin.controls.append(widget)
                    widget.data['index'] = self.right_pin.controls.index(widget)
                elif pin_location == "bottom":
                    self.bottom_pin.controls.append(widget)
                    widget.data['index'] = self.bottom_pin.controls.index(widget)

        # If main pin is empty, steal one from other pins so we are always fullscreen
        if len(self.main_pin) == 0:
            pass

            # Steal from left first
            if len(self.left_pin.controls) > 0:
                # Copy and delete last widget in left pin
                widget = self.left_pin.controls.pop()
                self.main_pin.append(widget)
            # Right pin
            elif len(self.right_pin.controls) > 0:
                widget = self.right_pin.controls.pop()
                self.main_pin.append(widget)
            # Top pin
            elif len(self.top_pin.controls) > 0:
                widget = self.top_pin.controls.pop()
                self.main_pin.append(widget)
            # Bottom pin
            elif len(self.bottom_pin.controls) > 0:
                widget = self.bottom_pin.controls.pop()
                self.main_pin.append(widget)
            else:
                pass

            # If we stole a widget, make its data match its new location
            if widget is not None:
                widget.data['pin_location'] = "main"
                widget.save_dict()

        
        # TODO: ?? Go through each pin and set their index depending on position??



    # Called when we need to reload our workspace content, especially after pin drags
    def reload_workspace(self):
        ''' Reloads our workspace content by clearing and re-adding our 5 pin locations to the master row '''

        # Make sure our widgets are arranged correctly
        self.arrange_widgets()

        # Change our cursor when we hover over a resizer (divider). Either vertical or horizontal
        def show_vertical_cursor(e: ft.HoverEvent):
            e.control.mouse_cursor = ft.MouseCursor.RESIZE_UP_DOWN
            e.control.update()
        def show_horizontal_cursor(e: ft.HoverEvent):
            e.control.mouse_cursor = ft.MouseCursor.RESIZE_LEFT_RIGHT
            e.control.update()

        # When pins are done dragging, save their new sizes
        async def save_pin_sizes(e):
            self.story.data['top_pin_height'] = self.top_pin.height
            self.story.data['left_pin_width'] = self.left_pin.width
            self.story.data['right_pin_width'] = self.right_pin.width
            self.story.data['bottom_pin_height'] = self.bottom_pin.height
            self.story.save_dict()


        # Method called when our divider (inside a gesture detector) is dragged
        # Updates the size of our pin in the story object
        async def move_top_pin_divider(e: ft.DragUpdateEvent):
            # Set limits so we dont resize too small or too large
            if (e.delta_y > 0 and self.top_pin.height < self.p.height/2) or (e.delta_y < 0 and self.top_pin.height >= self.minimum_pin_height):
                self.top_pin.height += e.delta_y
            # Update the page
            self.top_pin.page = self.p
            self.top_pin.update()
        
            
        # The control that holds our divider, which we drag to resize the top pin
        top_pin_resizer = ft.GestureDetector(
            content=ft.Container(
                height=10,
                bgcolor=ft.Colors.TRANSPARENT,
                padding=ft.padding.only(top=8),  # Push the 2px divider to the right side
            ),
            on_pan_update=move_top_pin_divider,
            on_pan_end=save_pin_sizes,
            on_hover=show_vertical_cursor,
            drag_interval=20,
        )

        # Left pin reisizer method and variable
        async def move_left_pin_divider(e: ft.DragUpdateEvent):
            if (e.delta_x > 0 and self.left_pin.width < self.p.width/2) or (e.delta_x < 0 and self.left_pin.width >= self.minimum_pin_width):
                self.left_pin.width += e.delta_x
            self.left_pin.page = self.p
            self.left_pin.update()
        
        left_pin_resizer = ft.GestureDetector(
            content=ft.Container(
                width=10,
                bgcolor=ft.Colors.TRANSPARENT,
                padding=ft.padding.only(left=8),
            ),
            on_pan_update=move_left_pin_divider,
            on_pan_end=save_pin_sizes,
            on_hover=show_horizontal_cursor,
            drag_interval=20,
        )
        

        # Right pin resizer method and variable
        async def move_right_pin_divider(e: ft.DragUpdateEvent):
            if (e.delta_x < 0 and self.right_pin.width < self.p.width/2) or (e.delta_x > 0 and self.right_pin.width >= self.minimum_pin_width):
                self.right_pin.width -= e.delta_x
            self.right_pin.page = self.p
            self.right_pin.update()
        
        right_pin_resizer = ft.GestureDetector(
            content=ft.Container(
                width=10,
                bgcolor=ft.Colors.TRANSPARENT,
                padding=ft.padding.only(left=8),  # Push the 2px divider to the right side
            ),
            on_pan_update=move_right_pin_divider,
            on_pan_end=save_pin_sizes,
            on_hover=show_horizontal_cursor,
            drag_interval=20,
        )

        # Bottom pin resizer method and variable
        async def move_bottom_pin_divider(e: ft.DragUpdateEvent):
            if (e.delta_y < 0 and self.bottom_pin.height < self.p.height/2) or (e.delta_y > 0 and self.bottom_pin.height >= self.minimum_pin_height):
                self.bottom_pin.height -= e.delta_y
            self.bottom_pin.page = self.p
            self.bottom_pin.update()
        
        bottom_pin_resizer = ft.GestureDetector(
            content=ft.Container(
                height=10,
                bgcolor=ft.Colors.TRANSPARENT,
                padding=ft.padding.only(top=8),  # Push the 2px divider to the right side
            ),
            on_pan_update=move_bottom_pin_divider,
            on_pan_end=save_pin_sizes,
            on_hover=show_vertical_cursor,
            drag_interval=20,
        )

        # Called when selected new tab in the main pin
        async def main_pin_tab_change(e: ft.ControlEvent):
            ''' Updates the widgets data to reflect the new active tab '''

            # Run through our visible main pin widgets
            for widget in visible_main_controls:

                # If the widgets tab is selected, make the widget data match, otherwise deselect the rest
                if widget.tab == e.control.tabs[e.control.selected_index]:
                    widget.data['is_active_tab'] = True
                    self.main_pin_tabs.indicator_color = widget.data.get('color', ft.Colors.PRIMARY)
                else:
                    widget.data['is_active_tab'] = False

                # Save the data. This allows for selected main pin tabs to save between sessions
                widget.save_dict()

            self.main_pin_tabs.update()

        # Main pin is rendered as a tab control, so we won't use dividers and will use different logic
        visible_main_controls = [control for control in self.main_pin if getattr(control, 'visible', True)]
        if len(visible_main_controls) > 1:
                
            # Hold all our main pin tabs
            self.main_pin_tabs = ft.Tabs(
                animation_duration=0,
                on_change=main_pin_tab_change,
                expand=True,  
                padding=ft.padding.all(0),
                label_padding=ft.padding.only(left=6, right=6, top=0, bottom=0),
                mouse_cursor=ft.MouseCursor.BASIC,
                tabs=[]    # Gives our tab control here   
            )
            for widget in visible_main_controls:
                self.main_pin_tabs.tabs.append(widget.tab)
                
                if widget.data['is_active_tab']:
                    self.main_pin_tabs.selected_index = self.main_pin_tabs.tabs.index(widget.tab)
                    self.main_pin_tabs.indicator_color =  ft.Colors.with_opacity(0.8, widget.data.get('color', ft.Colors.PRIMARY))
                    

            # Stick it in a container for styling
            formatted_main_pin = ft.Container(
                expand=True, border_radius=ft.border_radius.all(8),
                gradient=dark_gradient, 
                margin=ft.margin.all(0),
                padding=ft.padding.only(top=0, bottom=8, left=8, right=8),
                content=self.main_pin_tabs
            )

        elif len(visible_main_controls) == 1:
            formatted_main_pin = visible_main_controls[0]
        else:
            formatted_main_pin = ft.Container(expand=True)

        
        # Formatted pin locations that hold our pins, and our resizer gesture detectors.
        # Main pin is always expanded and has no resizer, so it doesnt need to be formatted
        formatted_top_pin = ft.Column(spacing=0, controls=[self.top_pin, top_pin_resizer])
        formatted_left_pin = ft.Row(spacing=0, controls=[self.left_pin, left_pin_resizer]) 
        formatted_right_pin = ft.Row(spacing=0, controls=[right_pin_resizer, self.right_pin])  # Right pin formatting row
        formatted_bottom_pin = ft.Column(spacing=0, controls=[bottom_pin_resizer, self.bottom_pin])  # Bottom pin formatting column

        # Check if our pins have any visible widgets or not, so if they should show up on screen
        # Check if top pin is empty. If yes, hide the formatted pin
        if len(self.top_pin.controls) == 0:
            formatted_top_pin.visible = False
        # If top pin not empty, make sure there is at least one visible widget
        elif all(obj.visible == False for obj in self.top_pin.controls[:]):
            formatted_top_pin.visible = False
        else:   # If not empty, check if any of the widgets are visible
            for obj in self.top_pin.controls:
                if obj.visible == True:     # If any widgets are visible, show our formatted pin
                    formatted_top_pin.visible = True
                    break   # No need to keep checking if at least one is visible
            # Makes sure our height is set correctly
            if self.top_pin.height < self.minimum_pin_height:
                self.top_pin.height = self.minimum_pin_height

        # Left pin
        if len(self.left_pin.controls) == 0:
            formatted_left_pin.visible = False
        elif all(obj.visible == False for obj in self.left_pin.controls[:]):
            formatted_left_pin.visible = False
        else:
            for obj in self.left_pin.controls:
                if obj.visible == True:
                    formatted_left_pin.visible = True
                    break
            if self.left_pin.width < self.minimum_pin_width:
                self.left_pin.width = self.minimum_pin_width

        # Right pin
        if len(self.right_pin.controls) == 0:
            formatted_right_pin.visible = False
        elif all(obj.visible == False for obj in self.right_pin.controls[:]):
            formatted_right_pin.visible = False
        else:
            for obj in self.right_pin.controls:
                if obj.visible == True:
                    formatted_right_pin.visible = True
                    break
            if self.right_pin.width < self.minimum_pin_width:
                self.right_pin.width = self.minimum_pin_width

        # Bottom pin
        if len(self.bottom_pin.controls) == 0:
            formatted_bottom_pin.visible = False
        elif all(obj.visible == False for obj in self.bottom_pin.controls[:]):
            formatted_bottom_pin.visible = False
        else:
            for obj in self.bottom_pin.controls:
                if obj.visible == True:
                    formatted_bottom_pin.visible = True
                    break
            if self.bottom_pin.height < self.minimum_pin_height:
                self.bottom_pin.height = self.minimum_pin_height


        

        # Format our pins on the page
        self.master_widgets_row.controls.clear()
        self.master_widgets_row.controls = [
            formatted_left_pin,    # formatted left pin
            ft.Column(
                expand=True, spacing=0, 
                controls=[
                    formatted_top_pin,    # formatted top pin
                    #self.main_pin,     # main work area with widgets
                    formatted_main_pin,   # formatted main pin
                    formatted_bottom_pin,     # formatted bottom pin

            ]),
            formatted_right_pin,    # formatted right pin
        ]

        # Set the master_stack as the content of this container
        self.content = self.master_stack

        # Finally update the UI
        try:        # Handle first launch
            self.update()
        except Exception as e:
            pass



        
