import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
from utils.verify_data import verify_data
import flet.canvas as cv
import math
from models.app import app


class Arc(MiniWidget):

    # Constructor.
    def __init__(
        self, 
        title: str, 
        owner: Widget, 
        page: ft.Page, 
        key: str, 
        x_alignment: float = None,          # Position of center of arc on plotline if we pass one in (between -1 and 1)
        data: dict = None
    ):
        
        
        # Parent constructor
        super().__init__(
            title=title,        
            owner=owner,                    # Top most plotline this arc belongs too
            page=page,          
            key=key,  
            data=data,         
        ) 

        # Newly created arcs
        if x_alignment is not None:

            # Calculate pixel values we need
            x_align_pixel = int((x_alignment + 1) / 2 * owner.plotline_width)
            
            # Left and right pixel values
            left = x_align_pixel - 50
            
            if left <= 0:
                left = 0
                x_align_pixel = 50

            rp = owner.plotline_width - x_align_pixel
            right = rp - 50
            
            if right >= owner.plotline_width:
                right = 0

            left_ratio = left / max(owner.plotline_width, 1)
            right_ratio = right / max(owner.plotline_width, 1)

            if x_alignment <= 0:
                side_location = "right"
                
            else:
                side_location = "left"

        # Needs values but they shouldn't be used, since the arc is not new
        else:
            side_location = "right"     
            left = 0
            right = 0
            left_ratio = 0
            right_ratio = 0
    

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {   
                # Mini widget data
                'tag': "arc",                               # Tag to identify what type of object this is
                'color': "secondary",                       # Color of the arc in the plotline
                
                # For rendering on plotline
                'side_location': side_location,      
                'is_shown_on_widget': True,                 # If this arcs plotline control is shown on the plotline widget

                # Absolute Left and Right positions of the arc on the plotline
                'left': left,
                'right': right,       # Default width
                'left_ratio': left_ratio,
                'right_ratio': right_ratio,
                'width': 100,           # Default width of the arc in pixels, used for new arcs that don't have left and right values yet, but need for calcs  
                
                # Arc Data
                'Summary': str,
                'Events': list,             # Simple list of events during this arc["event 1", "event 2", ...]
                'Start': str,                          
                'End': str, 
                'Where': str, 
                'Involved Characters': list,
                'Related Objects': list,
            },
        )


        # UI elements
        self.plotline_control: ft.Container = None      # Arc shaped contorl on the plotline

        # Set drag handles on left and right of arc connections to the plotline
        self.left_drag_handle = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT, content=ft.Icon(ft.Icons.DRAG_INDICATOR, self.data.get('color', 'secondary'), 20), 
            on_tap=self.show_mini_widget,    # Focus this mini widget when clicked
            on_secondary_tap=lambda e: print("Right clicked arc"), 
            on_enter=self._highlight,      # Highlight container
            visible=False, on_pan_update=self.change_x_positions, on_pan_start=self.start_dragging, on_pan_end=self.finished_dragging
        ) 
        self.right_drag_handle = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT, content=ft.Icon(ft.Icons.DRAG_INDICATOR, self.data.get('color', 'secondary'), 20), 
            on_tap=self.show_mini_widget,    # Focus this mini widget when clicked
            on_secondary_tap=lambda e: print("Right clicked arc"), 
            on_enter=self._highlight,      # Highlight container
            visible=False, on_pan_update=self.change_x_positions, on_pan_start=self.start_dragging, on_pan_end=self.finished_dragging
        )    
        
        
        # State variables
        self.is_dragging: bool = False              # If we are currently dragging our arc slider
        self.hidden = False                         # Track if we're in hidden mode for easier dragging

        # Loads our arc
        self.reload_plotline_control()
        self.reload_mini_widget()


    async def create_event(self, title: str):
        ''' Creates a new event in our events list with the given title '''

        # Add this new event to our data and save it
        events = self.data.get('Events', [])
        events.append(title)
        self.data['Events'] = events
        self.save_dict()

        # Reload our mini widget to show this new event
        self.reload_mini_widget()


    # Called when we hover over our arc on the plotline
    async def _highlight(self, e: ft.HoverEvent):
        ''' Focuses the arc control '''

        # Change its border opacity and update the page
        self.plotline_control.shadow = ft.BoxShadow(0, 10, self.data.get('color'), blur_style=ft.ShadowBlurStyle.OUTER)
        self.left_drag_handle.visible = True
        self.right_drag_handle.visible = True

        self.plotline_control.page = self.p
        self.plotline_control.update()

    # Called when we stop hovering over our arc on the plotline
    async def _stop_highlight(self, e: ft.HoverEvent):
        ''' Changes the arc control to unfocused '''

        if self.is_dragging:
            return
        
        # If we are not visible, lower our border and text
        if not self.visible:
            self.plotline_control.shadow = None
            self.left_drag_handle.visible = False
            self.right_drag_handle.visible = False
        
            self.plotline_control.page = self.p
            self.plotline_control.update()
    
    def hide_mini_widget(self, e=None, update: bool=False):
        ''' Hides this arc '''
        print(f"Hiding mini widget {self.title}")

        self.plotline_control.shadow = None

        self.left_drag_handle.visible = False
        self.right_drag_handle.visible = False
        
        return super().hide_mini_widget(update=update)
    

    # Called at the start of dragging our point on the slider
    async def start_dragging(self, e):
        ''' Called when we start dragging our slider thumb '''

        self.is_dragging = True

        # Hide all other info displays while dragging
        for mw in self.owner.mini_widgets:
            mw.visible = False
            if isinstance(mw, Arc) and mw != self:
                mw.plotline_control.ignore_interactions = True

        self.p.update()


    # Called at the end of dragging our point on the slider to update it
    async def change_x_positions(self, e: ft.DragUpdateEvent):
        ''' Changes our x position on the slider, and saves it to our data dictionary, but not to our file yet '''

        # Check to make sure we are wide enough (100px)
        width = self.owner.plotline_width - self.data.get('left', 0) - self.data.get('right', 0)
        
        ratio = width / max(self.owner.plotline_width, 1)
        
        # If we're dragging the left handle, update left position
        if e.control == self.left_drag_handle:
            new_left = self.data.get('left', 0) + e.delta_x

            # Clamp edges
            if new_left < 10:
                new_left = 10
            if new_left > self.owner.plotline_width - 10:     # Make sure we don't drag past the plotline
                new_left = self.owner.plotline_width - 10

            # Width check that we're not too small
            if width >= 100:
                self.data['left'] = new_left
                self.plotline_control.left = new_left

            elif width < 100 and e.delta_x < 0:   # If we're trying to make it smaller, allow it, but not if we're trying to make it bigger
                self.data['left'] = new_left
                self.plotline_control.left = new_left

        # If we're dragging the right handle, update the right position
        else:
            new_right = self.data.get('right', 0) - e.delta_x

            # Clamp edges
            if new_right < 10:     # Make sure we don't drag past the plotline
                new_right = 10
            if new_right > self.owner.plotline_width:
                new_right = self.owner.plotline_width

            # Width check that we're not too small
            if width >= 100:
                self.data['right'] = new_right
                self.plotline_control.right = new_right

            elif width < 100 and e.delta_x > 0:   # If we're trying to make it smaller, allow it, but not if we're trying to make it bigger
                self.data['right'] = new_right
                self.plotline_control.right = new_right

        #new_height = (self.owner.plotline_height / 2) * (ratio) - 40
        new_height = width * 0.5

        if new_height >= self.owner.plotline_height / 2 -70:
            new_height = self.owner.plotline_height / 2 -70
        if new_height < 50:
            new_height = 50

            print("New height of arc: ", new_height, " for width: ", width)

        self.plotline_control.height = int(new_height)

        # Apply the updates
        self.plotline_control.page = self.p 
        self.plotline_control.update()


    # Called when we finish dragging our slider thumb to save our new position
    def finished_dragging(self, e):
        ''' Saves our new x positions to the file and updates alignment. Then applies the UI changes '''

        # Update our state
        self.is_dragging = False                # No longer dragging

        # Update our x alignment based on our new left and right positions, and save it to our data
        x_align_pixel = self.data.get('left', 0) + ((self.owner.plotline_width - self.data.get('left', 0) - self.data.get('right', 0)) / 2)
        self.data['x_alignment'] = ((x_align_pixel) / max(self.owner.plotline_width, 1)) * 2 - 1

        if self.data.get('x_alignment', 0) <= 0:
            self.data['side_location'] = "right"
        else:
            self.data['side_location'] = "left"
            
        width = self.owner.plotline_width - self.data.get('left', 0) - self.data.get('right', 0)
        self.data['width'] = width

        self.data['left_ratio'] = self.data.get('left', 0) / max(self.owner.plotline_width, 1)
        self.data['right_ratio'] = self.data.get('right', 0) / max(self.owner.plotline_width, 1)

        # Make all other plot points visible again
        for pp in self.owner.plot_points.values():
            if pp.data.get('is_shown_on_widget', True):
                pp.plotline_control.visible = True
            
        # Save our new positions to file
        self.save_dict()

        # Make other arcs work again
        for mw in self.owner.mini_widgets:
            if mw.data.get('visible', True):
                mw.visible = True
            if isinstance(mw, Arc):
                mw.plotline_control.ignore_interactions = False

        # Apply changes and make sure update plotline info
        if self.owner.information_display.visible:
            self.owner.information_display.reload_mini_widget(no_update=True)
        self.owner.reload_widget()
        self.owner.story.active_rail.content.reload_rail()

    # Called when toggling whether this plot point is shown on the plotline in the plotline filters
    def toggle_plotline_control(self, value: bool):
        ''' Toggles whether this plot point is shown on the plotline '''

        # Change the control visibility, data, and save it
        self.plotline_control.visible = value
        self.data['is_shown_on_widget'] = value
        self.save_dict()
        
        # If we're hiding it, also hide our mini widget if it's open
        if value == False:
            self.hide_mini_widget(update=True)
        # Otherwise, just update the page
        else:
            self.p.update()      
        

    # Called from reload mini widget to update our plotline control
    def reload_plotline_control(self):
        ''' Reloads our arc drawing on the plotline based on current/updated data, including page size '''

        width = self.owner.plotline_width - self.data.get('left', 0) - self.data.get('right', 0)

        h = width * 0.5
        if h < 50:
            h = 50

        print("Height of arc: ", h, " for width: ", width)

        self.plotline_control = ft.Container(
            left=self.data.get('left', 0), right=self.data.get('right', None),
            alignment=ft.alignment.top_center, #height=h,
            margin=ft.Margin(16, 0, 16, 0), animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            border=ft.border.only(          # Give use borderes on top left and right
                left=ft.BorderSide(2, self.data.get('color', "secondary")),
                right=ft.BorderSide(2, self.data.get('color', "secondary")),
                top=ft.BorderSide(2, self.data.get('color', "secondary")),
            ), 
            padding=ft.padding.only(top=10),
            border_radius=ft.border_radius.only(top_left=10000, top_right=10000, bottom_left=0, bottom_right=0),      # Make it uber curved to look like an arc
            content=ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK,
                hover_interval=200, expand=True,
                on_tap=self.show_mini_widget,    # Focus this mini widget when clicked
                on_secondary_tap=lambda e: self.owner.story.open_menu(self._get_menu_options()),
                on_enter=self._highlight,      # Highlight container
                on_exit=self._stop_highlight,        # Stop highlight
                content=ft.Column([
                    ft.Container(
                        ft.Text(
                            self.title, expand=True, overflow=ft.TextOverflow.VISIBLE, 
                            theme_style=ft.TextThemeStyle.LABEL_LARGE, text_align=ft.TextAlign.CENTER,
                        ), margin=ft.margin.symmetric(horizontal=25), expand=True, alignment=ft.alignment.bottom_center
                    ),
                    ft.Row([
                        self.left_drag_handle,
                        self.right_drag_handle
                    ], vertical_alignment=ft.CrossAxisAlignment.START, alignment=ft.MainAxisAlignment.CENTER, spacing=30, expand=True)
                ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
            )
        )

        #print(f"Plotline control left and right for {self.title}: ", self.data.get('left', 0), self.data.get('right', 100))
        
        

    # Called to reload our mini widget content
    def reload_mini_widget(self, no_update: bool=False):

        arc_icon = ft.Icon(ft.Icons.CIRCLE_OUTLINED, self.data.get('color', None))

        arc_title_text = ft.GestureDetector(
            ft.Container(ft.Text(f"\t\t{self.data['title']}\t\t", weight=ft.FontWeight.BOLD, tooltip=f"Rename {self.title}"), padding=ft.padding.only(left=8)),
            on_double_tap=self._rename_clicked,
            on_tap=self._rename_clicked,
            on_secondary_tap=lambda e: self.owner.story.open_menu(self._get_menu_options()),
            mouse_cursor="click", on_hover=self.owner._hover_tab, hover_interval=500
        )

        pin_button = ft.IconButton(
            ft.Icons.PUSH_PIN_OUTLINED if not self.data.get('is_pinned', False) else ft.Icons.PUSH_PIN_ROUNDED,
            self.data.get('color', None),
            tooltip="Pin Information Display" if not self.data.get('is_pinned', False) else "Unpin Information Display",
            on_click=self._toggle_pin
        )

        close_button = ft.IconButton(
            ft.Icons.CLOSE, ft.Colors.OUTLINE,
            tooltip=f"Close {self.title}",
            on_click=lambda e: self.hide_mini_widget(update=True),
        )
        

        title_control = ft.Row([
            arc_icon,
            arc_title_text,
            pin_button,
            ft.Container(expand=True),      # Spacer
            close_button
        ], spacing=0)

        summary_tf = ft.TextField(
            value=self.data.get('Summary', ''), multiline=True, expand=True, 
            on_blur=lambda e: self.change_data(**{'Summary': e.control.value}), 
            label="Summary", capitalization=ft.TextCapitalization.SENTENCES,
            tooltip="Summary of what happened during this arc"
        )

        start_tf = ft.TextField(
            value=self.data.get('Start', ''), multiline=True, expand=True, 
            on_blur=lambda e: self.change_data(**{'Start': e.control.value}), 
            label="Start", capitalization=ft.TextCapitalization.SENTENCES,
            tooltip="When this arc began"
        )

        end_tf = ft.TextField(
            value=self.data.get('End', ''), multiline=True, expand=True, 
            on_blur=lambda e: self.change_data(**{'End': e.control.value}), 
            label="End", capitalization=ft.TextCapitalization.SENTENCES,
            tooltip="When this arc ends"
        )

        where_tf = ft.TextField(
            value=self.data.get('Where'), multiline=True, expand=True, 
            on_blur=lambda e: self.change_data(**{'Where': e.control.value}), 
            label="Where", capitalization=ft.TextCapitalization.SENTENCES,
            tooltip="List of location(s) related to this plot point"
        )

        def _get_events_controls() -> list[ft.Control]:

            def _change_cursor(e, tag: str):
                if tag == "down":
                    e.control.mouse_cursor = ft.MouseCursor.GRABBING
                elif tag == "up":
                    e.control.mouse_cursor = ft.MouseCursor.GRAB
                self.p.update()

            controls = []
            for idx, event in enumerate(self.data.get('Events', [])):
                event_tf = ft.ReorderableDraggable(
                    idx, 
                    ft.GestureDetector(
                        ft.Container(ft.Text(event), margin=ft.margin.only(bottom=6, top=6, left=20, right=10)),
                        mouse_cursor=ft.MouseCursor.GRAB, 
                        on_tap_down=lambda e: _change_cursor(e, "down"),
                        on_tap_up=lambda e: _change_cursor(e, "up"),
                    )
                )
                controls.append(event_tf)
            return controls
        
        def _reorder_events(e):
            ''' Reorders our events list based on the new order after a drag and drop reorder '''
            events = self.data.get('Events', [])
            event = events.pop(e.old_index)
            events.insert(e.new_index, event)

            events_list.controls = _get_events_controls()
            self.data['Events'] = events
            self.save_dict()
            self.p.update()
        
        events_label = ft.Row([
            ft.Container(width=6),
            ft.Text("Events", color=self.data.get('color', 'secondary'), weight=ft.FontWeight.BOLD, tooltip="List of events that happened during this arc"),
            ft.Container(width=6),
            ft.IconButton(
                ft.Icons.ADD, tooltip="Add Event", 
                on_click=lambda e: self.p.run_task(self.owner.new_item_clicked, e, self), data="event"
            ),
        ], spacing=0)


        events_list = ft.ReorderableListView(
            padding=ft.padding.all(4), show_default_drag_handles=False,
            controls=_get_events_controls(), on_reorder=_reorder_events, 
        )


        # Adds or removes characters from our involved characters list
        def _toggle_involved_characters(e):
            
            should_add_key = True   # Flag to check if we need to remove or not
            char_key = e.control.data   # Key of the character

            for key in self.data.get('Involved Characters', []):
                if char_key == key:     # If the character is in there, remove them and break
                    self.data['Involved Characters'].remove(key)
                    should_add_key = False      # Make sure we don't re-add them after
                    break

            # If we went through the list and didn't find them, add them to the list
            if should_add_key:
                print("Adding key")
                self.data.get('Involved Characters', []).append(char_key)

            self.save_dict()

            involved_characters_row.controls = _set_involved_characters_controls()
            involved_characters_selector.controls = _get_involved_characters()
            self.p.update()

        # Called to check our list of characters involved on this plotpoint. They are stored as keys and returned as names for display
        def _get_involved_characters() -> list[str]:
            char_list = []
            
            for char_key, char_obj in self.owner.story.characters.items():
                char_list.append(
                    ft.Checkbox(
                        char_obj.data.get('title', char_key),
                        True if char_key in self.data.get('Involved Characters', []) else False,
                        data=char_key,
                        label_style=ft.TextStyle(color=char_obj.data.get('color', None), weight=ft.FontWeight.BOLD),
                        on_change=_toggle_involved_characters
                    )
                )

            if len(char_list) == 0:
                char_list.append(ft.Text("No characters in story yet", color=ft.Colors.OUTLINE))
            return char_list

        def _toggle_involved_characters_selector(e=None):
            involved_characters_selector.visible = not involved_characters_selector.visible
            involved_characters_selector.controls = _get_involved_characters()

            if involved_characters_selector.visible:
                add_involved_characters_button.icon = ft.Icons.EDIT_OFF_OUTLINED
            else:
                add_involved_characters_button.icon = ft.Icons.EDIT_OUTLINED

            self.p.update()

        add_involved_characters_button = ft.IconButton(
            ft.Icons.EDIT_OUTLINED,
            tooltip="Connect Involved Characters",
            on_click=_toggle_involved_characters_selector
        )

        involved_characters_selector = ft.Column(
            _get_involved_characters(),
            visible=False,
        )

        def _set_involved_characters_controls(e=None) -> list[ft.Control]:

            controls = [
                ft.Text("Involved Characters:\t\t\t", theme_style=ft.TextThemeStyle.LABEL_LARGE, color=self.data.get('color', None)),
            ]

            for idx, ic_key in enumerate(self.data.get('Involved Characters', [])):
                char = self.owner.story.characters.get(ic_key, None)
                if char is not None:
                    name = char.data.get('title', ic_key)

                    # Add the control now
                    controls.append(ft.Text(name, color=char.data.get('color', None), weight=ft.FontWeight.BOLD))
                    controls.append(
                        ft.IconButton(
                            ft.Icons.CLOSE, char.data.get('color', None), scale=0.8,
                            data=ic_key,
                            on_click=_toggle_involved_characters
                        )
                    )
                    if idx < len(self.data.get('Involved Characters', [])) - 1: # Skip adding container to last character
                        controls.append(ft.Container(width=10))
                           
                    

            controls.append(add_involved_characters_button)
            return controls

        
        involved_characters_row = ft.Row(
            _set_involved_characters_controls(),
            wrap=True, spacing=0,
        )

        def _toggle_related_objects_selector(e=None):
            # For simplicity, we'll just use a text field to add related objects by key. In the future, we could make a dropdown selector similar to involved characters if needed
            related_objects_selector.visible = not related_objects_selector.visible

            if related_objects_selector.visible:
                add_related_objects_button.icon = ft.Icons.EDIT_OFF_OUTLINED
            else:
                add_related_objects_button.icon = ft.Icons.EDIT_OUTLINED

            self.p.update()

        add_related_objects_button = ft.IconButton(
            ft.Icons.EDIT_OUTLINED,
            tooltip="Add Related Object by Key",
            on_click=_toggle_related_objects_selector
        )

        def _set_related_objects_controls(e=None) -> list[ft.Control]:

            controls = [
                ft.Text("Related Objects:\t\t\t", theme_style=ft.TextThemeStyle.LABEL_LARGE, color=self.data.get('color', None)),
            ]

            for idx, obj_key in enumerate(self.data.get('Related Objects', [])):
                char = self.owner.story.objects.get(obj_key, None)
                if char is not None:
                    name = char.data.get('title', obj_key)

                    # Add the control now
                    controls.append(ft.Text(name, color=char.data.get('color', None), weight=ft.FontWeight.BOLD))
                    controls.append(
                        ft.IconButton(
                            ft.Icons.CLOSE, char.data.get('color', None), scale=0.8,
                            data=obj_key,
                            #on_click=_toggle_related_objects
                        )
                    )
                    if idx < len(self.data.get('Related Objects', [])) - 1: # Skip adding container to last character
                        controls.append(ft.Container(width=10))
                           
                    

            controls.append(add_related_objects_button)
            return controls
        
        def _toggle_related_objects(e):
            should_add_key = True   # Flag to check if we need to remove or not
            obj_key = e.control.data   # Key of the character

            for key in self.data.get('Related Objects', []):
                if obj_key == key:     # If the character is in there, remove them and break
                    self.data['Related Objects'].remove(key)
                    should_add_key = False      # Make sure we don't re-add them after
                    break

            # If we went through the list and didn't find them, add them to the list
            if should_add_key:
                self.data.get('Related Objects', []).append(obj_key)

            self.save_dict()

            related_objects_row.controls = _set_related_objects_controls()
            related_objects_selector.controls = _get_related_objects()
            self.p.update()

        def _get_related_objects() -> list[str]:
            char_list = []
            
            for obj_key, obj_obj in self.owner.story.objects.items():
                char_list.append(
                    ft.Checkbox(
                        obj_obj.data.get('title', obj_key),
                        True if obj_key in self.data.get('Involved Characters', []) else False,
                        data=obj_key,
                        label_style=ft.TextStyle(color=obj_obj.data.get('color', None), weight=ft.FontWeight.BOLD),
                        on_change=_toggle_related_objects
                    )
                )

            if len(char_list) == 0:
                char_list.append(ft.Text("No objects in story yet", color=ft.Colors.OUTLINE))
            return char_list

        related_objects_row = ft.Row(
            _set_related_objects_controls(),
            wrap=True, spacing=0,
        )
        
        related_objects_selector = ft.Column(
            _get_related_objects(),
            visible=False,
        )

        custom_fields_label = ft.Row([
            ft.Container(width=6),
            ft.Text("Custom Fields", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
            ft.IconButton(
                ft.Icons.NEW_LABEL_OUTLINED, tooltip="Add Custom Field",
                on_click=lambda e: self._new_custom_field_clicked())
        ], spacing=0)

        custom_fields_column = self._build_custom_fields_column()

        # Build the main body content of our info display
        content = ft.Column(
            expand=True, tight=True, scroll="auto", alignment=ft.MainAxisAlignment.START, 
            controls=[
                ft.Container(height=1), # Spacer
                summary_tf,             # Summary

                ft.Row([start_tf, end_tf]),             # When

                where_tf,           # Where

                events_label,
                events_list,

                involved_characters_row,        # Holds label, buttons for each involved character, and add/remove button
                involved_characters_selector,
                
                related_objects_row,
                related_objects_selector,

                custom_fields_label,
                ft.Container(custom_fields_column, margin=ft.margin.symmetric(horizontal=20)),
            ]
        )



        
        column = ft.Column([
            title_control,
            ft.Divider(height=2, thickness=2),
            content
        ], expand=True, tight=True, spacing=0)

        
        self.content = column
    

        if no_update:
            return
        else:
            self.p.update()


