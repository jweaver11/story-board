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
from models.isolated_controls.row import IsolatedRow
from models.isolated_controls.column import IsolatedColumn
from models.isolated_controls.tab_bar_view import IsolatedTabBarView
import asyncio

# Our workspace object that is stored in our story object
class Workspace(ft.Container):
    # Constructor
    def __init__(self, page: ft.Page, story: Story):

        # Set our container properties for the workspace
        super().__init__(
            expand=True,
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.only(top=10, bottom=10, left=2, right=10),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
        )

        self.p = page
        self.story = story

        self.minimum_pin_height = int(self.p.height / 5)
        self.minimum_pin_width = int(self.p.width / 8)
        self.maximum_pin_height = int(self.p.height / 2)   
        self.maximum_pin_width = int(self.p.width / 2)   

        # Creates our 4 side pin locations for our widgets inside our workspace. These are placed directly on the page
        self.top_pin = IsolatedRow(height=story.data['top_pin_height'], controls=[])
        self.left_pin = IsolatedColumn(width=story.data['left_pin_width'], controls=[])
        self.right_pin = IsolatedColumn(width=story.data['right_pin_width'], controls=[])
        self.bottom_pin = IsolatedRow(height=story.data['bottom_pin_height'], controls=[])

        # Main pin is not rendered directly since it changes based on active tab when more than one widget is present
        self.main_pin = []      # List to hold all our widgets in the main pin that we manipulate easier
        self.main_pin_tabs: ft.Tabs = None
        self.main_pin_column = ft.Column(expand=True)

        # Pin drag targets
        self.top_pin_drag_target = ft.DragTarget(
            group="widgets", 
            content=ft.Container(expand=True, height=self.story.data.get('top_pin_height', int(self.p.height/5)), bgcolor=ft.Colors.ON_SURFACE, opacity=0, border_radius=8, margin=ft.Margin.only(left=8, right=8),), 
            on_accept=self.pin_drag_accept, on_will_accept=self.on_hover_pin_drag_target, on_leave=self.on_stop_hover_drag_target,
            data="top"
        )
        self.left_pin_drag_target = ft.DragTarget(
            group="widgets",
            content=ft.Container(expand=True, width=self.story.data.get('left_pin_width', int(self.p.width/10)), bgcolor=ft.Colors.ON_SURFACE, border_radius=8, opacity=0), 
            on_accept=self.pin_drag_accept, on_will_accept=self.on_hover_pin_drag_target, on_leave=self.on_stop_hover_drag_target,
            data="left"
        )

        self.right_pin_drag_target = ft.DragTarget(
            group="widgets", 
            content=ft.Container(expand=True, width=self.story.data.get('right_pin_width', int(self.p.width/10)), bgcolor=ft.Colors.ON_SURFACE, border_radius=8, opacity=0), 
            on_accept=self.pin_drag_accept, on_will_accept=self.on_hover_pin_drag_target, on_leave=self.on_stop_hover_drag_target,
            data="right"
        )
        self.bottom_pin_drag_target = ft.DragTarget(
            group="widgets", 
            content=ft.Container(expand=True, height=self.story.data.get('bottom_pin_height', int(self.p.height/5)), margin=ft.Margin.only(left=8, right=8), bgcolor=ft.Colors.ON_SURFACE, opacity=0, border_radius=ft.BorderRadius.all(8)),
            on_accept=self.pin_drag_accept, on_will_accept=self.on_hover_pin_drag_target, on_leave=self.on_stop_hover_drag_target,
            data="bottom"
        )

        # Weird flet rendering logic, this one needs a container around the drag target to work properly
        self.main_pin_drag_target = ft.Container(
            expand=True,
            padding=ft.Padding.all(8),
            content=ft.DragTarget(
                group="widgets", 
                on_accept=self.pin_drag_accept, on_will_accept=self.on_hover_pin_drag_target, on_leave=self.on_stop_hover_drag_target,
                content=ft.Container(expand=True,  bgcolor=ft.Colors.ON_SURFACE, opacity=0, border_radius=ft.BorderRadius.all(8)),
                data="main"
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
        self.master_widgets_row = IsolatedRow(spacing=0, expand=True, controls=[])

        self.blocker = ft.Container(ft.ProgressRing(scale=.5, stroke_width=15), expand=True, visible=False, blur=1, left=0, right=0, top=0, bottom=0)     # Blocks events during a rebuild

        # Master stack that holds our widgets ^ row, and drag targets overtop. TransparentPointer allows the targets to be physical but not block widgets underneath
        self.master_stack = ft.Stack(expand=True, controls=[self.master_widgets_row, ft.TransparentPointer(self.pin_drag_targets), self.blocker])

        self.content = self.master_stack

        self.reload_workspace()   # Load our workspace content for the first time without updating the UI, since we're still in the constructor


    # When a draggable starts dragging, we add our drag targets to the master stack
    def show_pin_drag_targets(self, e=None):
        ''' Adds our drag targets to the master stack so we can drop our widgets into pin locations '''

        # If no visible in the top pin
        if len(self.top_pin.controls) == 0:
            #self.top_pin_drag_target.content.height = self.story.data.get('top_pin_height', int(self.p.height/5))
            self.top_pin_drag_target.content.height = self.minimum_pin_height   # Set to minimum height so we can actually see it and drop into it
            self.top_pin_drag_target.update()
       
        # If no visible in the left pin
        if len(self.left_pin.controls) == 0:
            #self.left_pin_drag_target.content.width = self.story.data.get('left_pin_width', int(self.pwidth/10))
            self.left_pin_drag_target.content.width = self.minimum_pin_width   # Set to minimum width so we can actually see it and drop into it
            self.left_pin_drag_target.update()
        
        # If no visible in the right pind
        if len(self.right_pin.controls) == 0:
            #self.right_pin_drag_target.content.width = self.story.data.get('right_pin_width', int(self.p.width/10))
            self.right_pin_drag_target.content.width = self.minimum_pin_width   # Set to minimum width so we can actually see it and drop into it
            self.right_pin_drag_target.update()
        
        # If no visible in the bottom pin
        if len(self.bottom_pin.controls) == 0:
            #self.bottom_pin_drag_target.content.height = self.story.data.get('bottom_pin_height', int(self.p.height/5))
            self.bottom_pin_drag_target.content.height = self.minimum_pin_height   # Set to minimum height so we can actually see it and drop into it
            self.bottom_pin_drag_target.update()

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
    async def pin_drag_accept(self, e: ft.DragTargetEvent):

        # TODO: Update index of stolen widget, and any effected widgets from old pin location, and save them

        # Put our blocker on the page to block events during longer reloads
        self.blocker.visible = True
        self.blocker.update()
        await asyncio.sleep(0)

        pin_location = e.control.data

        # Reset our container to be invisible again
        e.control.content.opacity = 0
        e.control.content.update()

        
        draggable = e.page.get_control(e.src_id)
            
        # Grab our key and set the widget
        widget_key = draggable.data

        widget = None

        for w in self.story.widgets:
            if w.data.get('key', "") == widget_key:
                widget = w
                break

        if widget is None:
            print("Error: Widget not found for drag accept")
            self.p.show_dialog(SnackBar("Error: Widget not found for drag accept"))
            return

        old_pin_location = widget.data['pin_location']

        # If we were dragged from the main pin and we were the active tab, set the first tab to new active
        if old_pin_location == "main" and widget.data['is_active_tab'] == True:
            widget.data['is_active_tab'] = False   # Deselect ourselves
  

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



        
        # Make sure our widget is visible if it was dragged from the rail
        if not widget.visible:
            await widget.show_widget()      # This will save dict as well
            self.blocker.visible = False
            self.blocker.update()
            return
        else:
            self.p.run_task(widget.save_dict)  

            # Apply to UI
            self.reload_workspace()     

            self.blocker.visible = False   # Unblock events
            self.blocker.update()


    # Called when we drag a widget from one pin location to another
    def arrange_widgets(self):
        ''' Arranges our widgets to their correct pin locations after a change is made to their pin location.
        Also adds widgets to their correct pin locations if they are missing from any pin location '''

        story = self.story

        self.right_pin.controls.clear()
        self.left_pin.controls.clear()
        self.top_pin.controls.clear()
        self.bottom_pin.controls.clear()
        self.main_pin.clear()       # Main pin is not rendered as its just a list, so we can just clear it
        
        if len(story.widgets) == 0: # Return early if no widgets exist yet
            return
        
        sorted_widgets = sorted(story.widgets, key=lambda w: w.data.get('index', 0))    # Sort our widgets by their index in their pin location so they are in the correct order when we add them back to the UI

        # Go through all our widgets in the story
        for w in sorted_widgets:

            # Check if they are visible
            if w.data.get('visible', False):

                # CRUCIAL. Fixes outdated page references by creating a new object
                widget = self.story.rebuild_widget(w)
    
                # Check if widget has data and pin_location
                pin_location = widget.data.get('pin_location', "")

                match pin_location:

                    case "top":
                        self.top_pin.controls.append(widget)
                        continue

                    case "left":
                        self.left_pin.controls.append(widget)
                        continue

                    case "right":
                        self.right_pin.controls.append(widget)
                        continue

                    case "bottom":
                        self.bottom_pin.controls.append(widget)
                        continue

                    case "main":
                        self.main_pin.append(widget)
                        continue

                    case _:     # Should be impossible, but catch errors
                        widget.data['pin_location'] = "main"
                        self.p.run_task(widget.save_dict)
                        self.main_pin.append(widget)
                        continue                

        # If main pin is empty, steal one from other pins so we are always fullscreen
        if len(self.main_pin) == 0:
            
            # Steal last widget from left controls first
            if len(self.left_pin.controls) > 0:
                stolen_widget = self.left_pin.controls.pop()
                self.main_pin.append(stolen_widget)
            # Then right if left is emtpy
            elif len(self.right_pin.controls) > 0:
                stolen_widget = self.right_pin.controls.pop()
                self.main_pin.append(stolen_widget)
            # Then top if right is empty
            elif len(self.top_pin.controls) > 0:
                stolen_widget = self.top_pin.controls.pop()
                self.main_pin.append(stolen_widget)
            # Then bottom if top is empty
            elif len(self.bottom_pin.controls) > 0:
                stolen_widget = self.bottom_pin.controls.pop()
                self.main_pin.append(stolen_widget)

            else:
                stolen_widget = None
            
            # If we stole a widget, make its data match its new location
            if stolen_widget is not None:
                stolen_widget.data['pin_location'] = "main"
                self.p.run_task(stolen_widget.save_dict)


    # Called when we need to reload our workspace content, especially after pin drags
    def reload_workspace(self):
        ''' Reloads our workspace content by clearing and re-adding our 5 pin locations to the master row '''

        # Make sure our widgets are arranged correctly
        self.arrange_widgets()

        async def save_pin_sizes(e: ft.DragEndEvent=None):
            self.story.data['top_pin_height'] = self.top_pin.height
            self.story.data['left_pin_width'] = self.left_pin.width
            self.story.data['right_pin_width'] = self.right_pin.width
            self.story.data['bottom_pin_height'] = self.bottom_pin.height
            await self.story.save_dict()

        
        # Method called wn our divider (inside a gesture detector) is dragged
        # Updates the size of our pin in the story object
        async def move_top_pin_divider(e: ft.DragUpdateEvent):
            self.top_pin.height += e.local_delta.y

            if self.top_pin.height < self.minimum_pin_height:
                self.top_pin.height = self.minimum_pin_height
            elif self.top_pin.height > self.maximum_pin_height:
                self.top_pin.height = self.maximum_pin_height
            self.top_pin_drag_target.content.height = self.top_pin.height  
            formatted_top_pin.update()   # Update the formatted container that holds the pin and divider, since the pin itself is not rendered directly and has no resizer on it
        
        # The control that holds our divider, which we drag to resize the top pin
        top_pin_resizer = ft.GestureDetector(
            content=ft.Container(
                height=10,
                bgcolor=ft.Colors.TRANSPARENT,
                padding=ft.Padding.only(top=8),  # Push the 2px divider to the right side
            ),
            on_pan_update=move_top_pin_divider,
            on_pan_end=save_pin_sizes,
            mouse_cursor=ft.MouseCursor.RESIZE_UP_DOWN,
            drag_interval=20,
        )

        # Left pin reisizer method and variable
        async def move_left_pin_divider(e: ft.DragUpdateEvent):
            self.left_pin.width += e.local_delta.x
            if self.left_pin.width < self.minimum_pin_width:
                self.left_pin.width = self.minimum_pin_width
            elif self.left_pin.width > self.maximum_pin_width:
                self.left_pin.width = self.maximum_pin_width
            self.left_pin_drag_target.content.width = self.left_pin.width
            formatted_left_pin.update()    # Update the formatted container that holds the pin and divider, since the pin itself is not rendered directly and has no resizer on it
        
        left_pin_resizer = ft.GestureDetector(
            content=ft.Container(
                width=10,
                bgcolor=ft.Colors.TRANSPARENT,
                padding=ft.Padding.only(left=8),
            ),
            on_pan_update=move_left_pin_divider,
            on_pan_end=save_pin_sizes,
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
            drag_interval=20,
        )
        

        # Right pin resizer method and variable
        async def move_right_pin_divider(e: ft.DragUpdateEvent):
            self.right_pin.width -= e.local_delta.x
            if self.right_pin.width < self.minimum_pin_width:
                self.right_pin.width = self.minimum_pin_width
            elif self.right_pin.width > self.maximum_pin_width:
                self.right_pin.width = self.maximum_pin_width
            self.right_pin_drag_target.content.width = self.right_pin.width
            formatted_right_pin.update() 

        right_pin_resizer = ft.GestureDetector(
            content=ft.Container(
                width=10,
                bgcolor=ft.Colors.TRANSPARENT,
                padding=ft.Padding.only(left=8),  # Push the 2px divider to the right side
            ),
            on_pan_update=move_right_pin_divider,
            on_pan_end=save_pin_sizes,
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
            drag_interval=20,
        )

        # Bottom pin resizer method and variable
        async def move_bottom_pin_divider(e: ft.DragUpdateEvent):
            self.bottom_pin.height -= e.local_delta.y
            if self.bottom_pin.height < self.minimum_pin_height:
                self.bottom_pin.height = self.minimum_pin_height
            elif self.bottom_pin.height > self.maximum_pin_height:
                self.bottom_pin.height = self.maximum_pin_height
            self.bottom_pin_drag_target.content.height = self.bottom_pin.height
            formatted_bottom_pin.update()
        
        bottom_pin_resizer = ft.GestureDetector(
            content=ft.Container(
                height=10,
                bgcolor=ft.Colors.TRANSPARENT,
                padding=ft.Padding.only(top=8),  # Push the 2px divider to the right side
            ),
            on_pan_update=move_bottom_pin_divider,
            on_pan_end=save_pin_sizes,
            mouse_cursor=ft.MouseCursor.RESIZE_UP_DOWN,
            drag_interval=20,
        )

        async def tab_change(e: ft.Event):

            for idx, w in enumerate(self.main_pin):
                old_is_active_tab = w.data.get('is_active_tab', False)
                if idx == e.data:
                    w.data['is_active_tab'] = True
                else:
                    w.data['is_active_tab'] = False

                if old_is_active_tab != w.data['is_active_tab']:    # Only save changes
                    self.p.run_task(w.save_dict)


        
        # Main pin is rendered as a tab control, so we won't use dividers and will use different logic
        if len(self.main_pin) > 1:
                
            # Hold all our main pin tabs
            main_pin_tabs = ft.Tabs(
                expand=True, length=len(self.main_pin),
                selected_index=-1,
                on_change=tab_change,
                animation_duration=100,
                content=ft.Column([
                    ft.TabBar(
                        tabs=[widget.tab for widget in self.main_pin], scrollable=True
                    ), 
                    ft.TabBarView(
                        controls=[widget.master_stack for widget in self.main_pin],
                        expand=True
                    )
                ], expand=True),
            )   
            
            main_pin_tabs.selected_index = -1   #TODO: Set to active tab
            
            # Stick it in a container for styling
            formatted_main_pin = ft.Container(
                expand=True, border_radius=ft.BorderRadius.all(8),
                gradient=dark_gradient, 
                margin=ft.Margin.all(0),
                padding=ft.Padding.only(top=0, bottom=8, left=8, right=8),
                content=main_pin_tabs
            )

            for idx, widget in enumerate(self.main_pin):
                if widget.data.get('is_active_tab', False):
                    main_pin_tabs.selected_index = idx
                    break

        elif len(self.main_pin) == 1:
            formatted_main_pin = self.main_pin[0]
            
        else:
            formatted_main_pin = ft.Container(expand=True)
        
        
        # Formatted pin locations that hold our pins, and our resizer gesture detectors.
        # Main pin is always expanded and has no resizer, so it doesnt need to be formatted
        formatted_top_pin = ft.Column(spacing=0, controls=[self.top_pin, top_pin_resizer])
        formatted_left_pin = ft.Row(spacing=0, controls=[self.left_pin, left_pin_resizer]) 
        formatted_right_pin = ft.Row(spacing=0, controls=[right_pin_resizer, self.right_pin])  # Right pin formatting row
        formatted_bottom_pin = ft.Column(spacing=0, controls=[bottom_pin_resizer, self.bottom_pin])  # Bottom pin formatting column
        
        # Check if our pins have any widgets in them. If not, hide them
        if len(self.top_pin.controls) == 0:
            formatted_top_pin.visible = False

        # Left pin
        if len(self.left_pin.controls) == 0:
            formatted_left_pin.visible = False

        # Right pin
        if len(self.right_pin.controls) == 0:
            formatted_right_pin.visible = False

        # Bottom pin
        if len(self.bottom_pin.controls) == 0:
            formatted_bottom_pin.visible = False


        #print("Num Widgets -- Visibility")
        #print("Top Pin: ", len(self.top_pin.controls), formatted_top_pin.visible)
        #print("Left Pin: ", len(self.left_pin.controls), formatted_left_pin.visible)
        #print("Main Pin: ", len(self.main_pin), formatted_main_pin.visible)
        #print("Right Pin: ", len(self.right_pin.controls), formatted_right_pin.visible)
        #print("Bottom Pin: ", len(self.bottom_pin.controls), formatted_bottom_pin.visible)


        # Our master row that holds all our widgets
        self.master_widgets_row.controls.clear()
        self.master_widgets_row.controls = [
            formatted_left_pin,    # formatted left pin
            IsolatedColumn(
                expand=True, spacing=0, 
                controls=[
                    formatted_top_pin,    # formatted top pin
                    formatted_main_pin,   # formatted main pin
                    formatted_bottom_pin,     # formatted bottom pin
            ]),
            formatted_right_pin,   
        ]
        
        
        # Finally update the UI
        try:
            self.master_widgets_row.update()
        except Exception as e:
            pass


        