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

        # Creates our 4 edge pin locations for our widgets inside our workspace.
        self.top_pin = IsolatedRow(height=story.data['top_pin_height'], controls=[])
        self.left_pin = IsolatedColumn(width=story.data['left_pin_width'], controls=[])
        self.right_pin = IsolatedColumn(width=story.data['right_pin_width'], controls=[])
        self.bottom_pin = IsolatedRow(height=story.data['bottom_pin_height'], controls=[])

        # Create our draggable resizers to editour pin sizes by dragging on the inside edge of them
        self.top_pin_resizer = ft.GestureDetector(
            content=ft.Container(
                height=10,
                bgcolor=ft.Colors.TRANSPARENT,
                padding=ft.Padding.only(top=8),  # Push the 2px divider to the right side
            ),
            on_pan_update=self.move_top_pin_resizer,
            on_pan_end=self.save_pin_sizes,
            mouse_cursor=ft.MouseCursor.RESIZE_UP_DOWN,
            drag_interval=20,
        )
        self.left_pin_resizer = ft.GestureDetector(
            content=ft.Container(
                width=10,
                bgcolor=ft.Colors.TRANSPARENT,
                padding=ft.Padding.only(left=8),
            ),
            on_pan_update=self.move_left_pin_resizer,
            on_pan_end=self.save_pin_sizes,
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
            drag_interval=20,
        )
        self.right_pin_resizer = ft.GestureDetector(
            content=ft.Container(
                width=10,
                bgcolor=ft.Colors.TRANSPARENT,
                padding=ft.Padding.only(left=8),  # Push the 2px resizer to the right side
            ),
            on_pan_update=self.move_right_pin_resizer,
            on_pan_end=self.save_pin_sizes,
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
            drag_interval=20,
        )
        self.bottom_pin_resizer = ft.GestureDetector(
            content=ft.Container(
                height=10,
                bgcolor=ft.Colors.TRANSPARENT,
                padding=ft.Padding.only(top=8),  # Push the 2px resizer to the right side
            ),
            on_pan_update=self.move_bottom_pin_resizer,
            on_pan_end=self.save_pin_sizes,
            mouse_cursor=ft.MouseCursor.RESIZE_UP_DOWN,
            drag_interval=20,
        )

        # Give us our formatted pins to hold the control pins and resizers. We edit and update these
        self.formatted_top_pin = IsolatedColumn(spacing=0, controls=[self.top_pin, self.top_pin_resizer])
        self.formatted_left_pin = IsolatedRow(spacing=0, controls=[self.left_pin, self.left_pin_resizer]) 
        self.formatted_right_pin = IsolatedRow(spacing=0, controls=[self.right_pin_resizer, self.right_pin])  # Right pin formatting row
        self.formatted_bottom_pin = IsolatedColumn(spacing=0, controls=[self.bottom_pin_resizer, self.bottom_pin])  # Bottom pin formatting column


        # Main pin UI components. Main pin has different formatting so we have a tab view
        self.main_pin = []                  # List to hold all the visible main pin widgets
        self.main_pin_tab_bar: ft.TabBar = ft.TabBar(tabs=[], scrollable=True)    # Holds our tabs for our widgets in main pin
        self.main_pin_tab_bar_view = ft.TabBarView(controls=[], expand=True)     # Holds our 'tab_views' for our widgets in the main pin

        # Stick our main pin in a container for styling
        self.formatted_main_pin = ft.Container(
            expand=True, border_radius=ft.BorderRadius.all(8),
            gradient=dark_gradient, 
            margin=ft.Margin.all(0),
            padding=ft.Padding.only(top=0, bottom=8, left=8, right=8),
            
        )

        # Arrange all the widgets that should be shown into their correct positions
        self.arrange_widgets()

        if len(self.main_pin) == 0:
            self.main_pin.append(ft.Container())
            self.main_pin_tab_bar.tabs.append(ft.Tab(""))     # Add empty tab so it doesn't bug out when we add the first widget
            self.main_pin_tab_bar_view.controls.append(ft.Container())   # Add empty content for the empty tab
                
        # Parent tabs control needed for rendering
        self.main_pin_tabs = ft.Tabs(
            expand=True, 
            length=len(self.main_pin),
            selected_index=-1,
            on_change=self.tab_change,
            animation_duration=100,
            content=ft.Column([
                self.main_pin_tab_bar,  
                self.main_pin_tab_bar_view
            ], expand=True),
        )    

        

        # Set selected index in our main pin based on previous active tab
        #for idx, widget in enumerate(self.main_pin):
            #if widget.data.get('is_active_tab', False):
                #self.main_pin_tabs.selected_index = idx
                #break

        self.formatted_main_pin.content = self.main_pin_tabs
        

        # Pin drag targets to catch pins when they are dragged from one pin to another
        self.top_pin_drag_target = ft.DragTarget(
            group="widgets", 
            content=ft.Container(expand=True, height=self.story.data.get('top_pin_height', int(self.p.height/5)), bgcolor=ft.Colors.ON_SURFACE, opacity=0, border_radius=8, margin=ft.Margin.only(left=8, right=8),), 
            on_accept=lambda e: self.pin_drag_accept(e, "top"), on_will_accept=self.highlight_pin_drag_target, on_leave=self.stop_highlight_pin_drag_target,
        )
        self.left_pin_drag_target = ft.DragTarget(
            group="widgets",
            content=ft.Container(expand=True, width=self.story.data.get('left_pin_width', int(self.p.width/10)), bgcolor=ft.Colors.ON_SURFACE, border_radius=8, opacity=0), 
            on_accept=lambda e: self.pin_drag_accept(e, "left"), on_will_accept=self.highlight_pin_drag_target, on_leave=self.stop_highlight_pin_drag_target,
        )
        self.right_pin_drag_target = ft.DragTarget(
            group="widgets", 
            content=ft.Container(expand=True, width=self.story.data.get('right_pin_width', int(self.p.width/10)), bgcolor=ft.Colors.ON_SURFACE, border_radius=8, opacity=0), 
            on_accept=lambda e: self.pin_drag_accept(e, "right"), on_will_accept=self.highlight_pin_drag_target, on_leave=self.stop_highlight_pin_drag_target,
        )
        self.bottom_pin_drag_target = ft.DragTarget(
            group="widgets", 
            content=ft.Container(expand=True, height=self.story.data.get('bottom_pin_height', int(self.p.height/5)), margin=ft.Margin.only(left=8, right=8), bgcolor=ft.Colors.ON_SURFACE, opacity=0, border_radius=ft.BorderRadius.all(8)),
            on_accept=lambda e: self.pin_drag_accept(e, "bottom"), on_will_accept=self.highlight_pin_drag_target, on_leave=self.stop_highlight_pin_drag_target,
        )
        self.main_pin_drag_target = ft.Container(
            expand=True,
            padding=ft.Padding.all(8),
            content=ft.DragTarget(
                group="widgets", 
                on_accept=lambda e: self.pin_drag_accept(e, "main"), on_will_accept=self.highlight_pin_drag_target, on_leave=self.stop_highlight_pin_drag_target,
                content=ft.Container(expand=True,  bgcolor=ft.Colors.ON_SURFACE, opacity=0, border_radius=ft.BorderRadius.all(8))
            )
        )

        # Format our pin drag targets in the stack 
        self.pin_drag_targets = ft.Container(
            visible=True,
            expand=True,
            content=ft.Row(
                spacing=0,
                expand=True,
                controls=[
                    self.left_pin_drag_target,
                    IsolatedColumn(
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

        # Blocks events during a rebuild
        self.blocker = ft.Container(expand=True, ignore_interactions=True)     

        # Our master row that holds all our widgets
        self.master_widgets_row = IsolatedRow(
            spacing=0, expand=True, 
            controls=[
                self.formatted_left_pin,    # formatted left pin
                IsolatedColumn(
                    expand=True, spacing=0, 
                    controls=[
                        self.formatted_top_pin,    # formatted top pin
                        self.formatted_main_pin,   # formatted main pin
                        self.formatted_bottom_pin,     # formatted bottom pin
                ]),
                self.formatted_right_pin,   
            ]
        )

        # Master stack that holds our widgets ^ row, and drag targets overtop. TransparentPointer allows the targets to be physical but not block widgets underneath
        self.master_stack = ft.Stack(expand=True, controls=[self.master_widgets_row, ft.TransparentPointer(self.pin_drag_targets), self.blocker])

        self.content = self.master_stack

        

        #self.reload_workspace()   # Load our workspace content for the first time without updating the UI, since we're still in the constructor

    async def save_pin_sizes(self, e: ft.DragEndEvent=None):
        self.story.data['top_pin_height'] = self.top_pin.height
        self.story.data['left_pin_width'] = self.left_pin.width
        self.story.data['right_pin_width'] = self.right_pin.width
        self.story.data['bottom_pin_height'] = self.bottom_pin.height
        self.story.save_dict()

        
    # Method called wn our resizer (inside a gesture detector) is dragged
    # Updates the size of our pin in the story object
    async def move_top_pin_resizer(self, e: ft.DragUpdateEvent):
        self.top_pin.height += e.local_delta.y

        if self.top_pin.height < self.minimum_pin_height:
            self.top_pin.height = self.minimum_pin_height
        elif self.top_pin.height > self.maximum_pin_height:
            self.top_pin.height = self.maximum_pin_height
        self.top_pin_drag_target.content.height = self.top_pin.height  
        self.formatted_top_pin.update()   # Update the formatted container that holds the pin and resizer, since the pin itself is not rendered directly and has no resizer on it
        
    # Left pin reisizer method and variable
    async def move_left_pin_resizer(self, e: ft.DragUpdateEvent):
        self.left_pin.width += e.local_delta.x
        if self.left_pin.width < self.minimum_pin_width:
            self.left_pin.width = self.minimum_pin_width
        elif self.left_pin.width > self.maximum_pin_width:
            self.left_pin.width = self.maximum_pin_width
        self.left_pin_drag_target.content.width = self.left_pin.width
        self.formatted_left_pin.update()    # Update the formatted container that holds the pin and resizer, since the pin itself is not rendered directly and has no resizer on it
    
    # Right pin resizer method and variable
    async def move_right_pin_resizer(self, e: ft.DragUpdateEvent):
        self.right_pin.width -= e.local_delta.x
        if self.right_pin.width < self.minimum_pin_width:
            self.right_pin.width = self.minimum_pin_width
        elif self.right_pin.width > self.maximum_pin_width:
            self.right_pin.width = self.maximum_pin_width
        self.right_pin_drag_target.content.width = self.right_pin.width
        self.formatted_right_pin.update() 

    # Bottom pin resizer method and variable
    async def move_bottom_pin_resizer(self, e: ft.DragUpdateEvent):
        self.bottom_pin.height -= e.local_delta.y
        if self.bottom_pin.height < self.minimum_pin_height:
            self.bottom_pin.height = self.minimum_pin_height
        elif self.bottom_pin.height > self.maximum_pin_height:
            self.bottom_pin.height = self.maximum_pin_height
        self.bottom_pin_drag_target.content.height = self.bottom_pin.height
        self.formatted_bottom_pin.update()

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

    async def tab_change(self, e: ft.Event):

        for idx, w in enumerate(self.main_pin):
            old_is_active_tab = w.data.get('is_active_tab', False)
            if idx == e.data:
                w.data['is_active_tab'] = True
            else:
                w.data['is_active_tab'] = False

            #if old_is_active_tab != w.data['is_active_tab']:    # Only save changes
                #self.p.run_task(w.save_dict)

    # Called when a draggable hovers over a drag target before dropping
    async def highlight_pin_drag_target(self, e):
        ''' Makes the drag target visible for so visual feedback '''
        e.control.content.opacity = .3
        e.control.content.update()
       
    # Called when a draggable leaves a drag target
    async def stop_highlight_pin_drag_target(self, e):
        ''' Makes the drag target invisible again '''
        e.control.content.opacity = 0
        e.control.content.update()
        

    # Accepting drags for our five pin locations
    def pin_drag_accept(self, e: ft.DragTargetEvent, new_pin_location: str):

        #self.blocker.ignore_interactions = False   # Block events during the rearrange and reload process to prevent weird bugs
        #self.blocker.update()


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

        # Set the old pin location
        old_pin_location = widget.data['pin_location']

        # If we were dragged from the main pin and we were the active tab, set the first tab to new active
        if old_pin_location == "main" and widget.data['is_active_tab'] == True:
            widget.data['is_active_tab'] = False   # Deselect ourselves
            if len(self.main_pin) > 0:
                self.main_pin_tabs.selected_index = 0     # Select the first tab as the new active tab

        # Remove our widget from its old pin location
        match old_pin_location:
            case "top":
                for w in self.top_pin.controls:
                    if w.data.get('key', "") == widget.data.get('key', ""):
                        self.top_pin.controls.remove(w)
                        break

                # If that pin is now empty, set its drag target height and visibility
                if len(self.top_pin.controls) == 0:
                    self.top_pin_drag_target.content.height = self.story.data.get('top_pin_height', int(self.p.height/5))   
                    self.top_pin_drag_target.update()
                    self.formatted_top_pin.visible = False   

                self.formatted_top_pin.update()     # Apply updates

            case "left":
                for w in self.left_pin.controls:
                    if w.data.get('key', "") == widget.data.get('key', ""):
                        self.left_pin.controls.remove(w)
                        break
                if len(self.left_pin.controls) == 0:
                    self.left_pin_drag_target.content.width = self.story.data.get('left_pin_width', int(self.p.width/10))   
                    self.left_pin_drag_target.update()
                    self.formatted_left_pin.visible = False
                self.formatted_left_pin.update()
            case "main":
                for w in self.main_pin:
                    if w.data.get('key', "") == widget.data.get('key', ""):

                        self.main_pin.remove(w)
                        self.main_pin_tab_bar.tabs.remove(w.tab)
                        self.main_pin_tab_bar_view.controls.remove(w.master_stack)

                if len(self.main_pin) == 0:
                    self.formatted_main_pin.visible = False

                self.formatted_main_pin.update()
            case "right":
                for w in self.right_pin.controls:
                    if w.data.get('key', "") == widget.data.get('key', ""):
                        self.right_pin.controls.remove(w)
                        break
                if len(self.right_pin.controls) == 0:
                    self.right_pin_drag_target.content.width = self.story.data.get('right_pin_width', int(self.p.width/10))   
                    self.right_pin_drag_target.update()
                    self.formatted_right_pin.visible = False
                self.formatted_right_pin.update()
            case "bottom":
                for w in self.bottom_pin.controls:
                    if w.data.get('key', "") == widget.data.get('key', ""):
                        self.bottom_pin.controls.remove(w)
                        break
                if len(self.bottom_pin.controls) == 0:
                    self.bottom_pin_drag_target.content.height = self.story.data.get('bottom_pin_height', int(self.p.height/5))   
                    self.bottom_pin_drag_target.update()
                    self.formatted_bottom_pin.visible = False
                self.formatted_bottom_pin.update()
  

        # Set our objects pin location to the correct new location
        widget.data['pin_location'] = new_pin_location 

        # Rebulid the widget before we re-add it back to the page
        print("Before rebuild")
        widget = self.story.rebuild_widget(widget)
        print("After rebuild")

        # TODO: Show widget
        #if not widget.visible:
            #widget.show_widget()     # This will save dict as well
        #else:
            #self.p.run_task(widget.save_dict)   

        # Check where its new pin location is
        match new_pin_location:

            case "top":
                widget.data['index'] = len(self.top_pin.controls)
                self.top_pin.controls.append(widget)     # Add it to the new pin location
                self.formatted_top_pin.visible = True     # Make sure the pin is visible if it was dragged from the rail
                if self.top_pin_drag_target.content.height != self.story.data.get('top_pin_height', int(self.p.height/5)):
                    self.top_pin_drag_target.content.height = self.story.data.get('top_pin_height', int(self.p.height/5))   
                    self.top_pin_drag_target.update()
                self.formatted_top_pin.update()     # Apply updates
            case "left":
                widget.data['index'] = len(self.left_pin.controls)
                self.left_pin.controls.append(widget)
                self.formatted_left_pin.visible = True
                if self.left_pin_drag_target.content.width != self.story.data.get('left_pin_width', int(self.p.width/10)):
                    self.left_pin_drag_target.content.width = self.story.data.get('left_pin_width', int(self.p.width/10))   
                    self.left_pin_drag_target.update()
                self.formatted_left_pin.update()
            case "main":
                widget.data['index'] = len(self.main_pin)   
                # Set other tabs to inactive, and new one to active              
                #for w in self.main_pin:
                    #w.data['is_active_tab'] = False        # Deselect all other main pin widgets

                widget.data['is_active_tab'] = True

                self.main_pin.append(widget)        # Add it for tracking
                self.main_pin_tab_bar.tabs.append(widget.tab)       # Add its tab
                self.main_pin_tab_bar_view.controls.append(widget.master_stack)     # Add its content
                self.formatted_main_pin.visible = True
                self.formatted_main_pin.update()

            case "right":
                widget.data['index'] = len(self.right_pin.controls)
                self.right_pin.controls.append(widget)
                self.formatted_right_pin.visible = True
                if self.right_pin_drag_target.content.width != self.story.data.get('right_pin_width', int(self.p.width/10)):
                    self.right_pin_drag_target.content.width = self.story.data.get('right_pin_width', int(self.p.width/10))   
                    self.right_pin_drag_target.update()
                self.formatted_right_pin.update()

            case "bottom":
                widget.data['index'] = len(self.bottom_pin.controls)
                self.bottom_pin.controls.append(widget)
                self.formatted_bottom_pin.visible = True
                if self.bottom_pin_drag_target.content.height != self.story.data.get('bottom_pin_height', int(self.p.height/5)):
                    self.bottom_pin_drag_target.content.height = self.story.data.get('bottom_pin_height', int(self.p.height/5))   
                    self.bottom_pin_drag_target.update()
                self.formatted_bottom_pin.update()


        

        
        

        # Apply to UI
        #self.reload_workspace()     

        #self.blocker.ignore_interactions = True   # Unblock events after the rearrange and reload process is done
        #self.blocker.update()


    # Called to arrange our widgets on story load to their correct pins
    def arrange_widgets(self):

        

        story = self.story
  
        # Set our visible widgets list
        visible_widgets = [w for w in story.widgets if w.data.get('visible', False)]
        if len(visible_widgets) == 0:   # Return early if no visible widgets to add to pins
            return
        
        # Sort them so workspaces look the same after reloads
        sorted_widgets = sorted(visible_widgets, key=lambda w: w.data.get('index', 0))    

        # Go through sorted visible widgets
        for widget in sorted_widgets:

            # Check if widget has data and pin_location
            pin_location = widget.data.get('pin_location', "")

            # TODO: As we get set, set their index to the new length - 1

            match pin_location:

                # For edge pins, just add them to controls
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

                # Main pin is special
                case "main":
                    self.main_pin.append(widget)        # Add it for tracking
                    self.main_pin_tab_bar.tabs.append(widget.tab)       # Add its tab
                    self.main_pin_tab_bar_view.controls.append(widget.master_stack)     # Add its content
                    continue

                case _:     # Should be impossible, but catch errors
                    continue     

        # Hide empty pins
        if len(self.top_pin.controls) == 0:
            self.formatted_top_pin.visible = False
        if len(self.left_pin.controls) == 0:
            self.formatted_left_pin.visible = False
        if len(self.right_pin.controls) == 0:
            self.formatted_right_pin.visible = False
        if len(self.bottom_pin.controls) == 0:
            self.formatted_bottom_pin.visible = False
        if len(self.main_pin) == 0:
            self.formatted_main_pin.visible = False     




    # Called when we need to reload our workspace content, especially after pin drags
    def reload_workspace(self):
        ''' Reloads our workspace content by clearing and re-adding our 5 pin locations to the master row '''

        return
        # Make sure our widgets are arranged correctly
        self.arrange_widgets()

        

        #if self.formatted_top_pin.visible:
            #self.top_pin_drag_target.content.height = self.story.data.get('top_pin_height', int(self.p.height/5))



        # Our master row that holds all our widgets
        
        
        # Finally update the UI
        try:
            self.master_widgets_row.update()
        except Exception as e:
            pass



        