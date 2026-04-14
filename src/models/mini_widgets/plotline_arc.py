import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
from utils.verify_data import verify_data
import flet.canvas as cv
import math
from models.app import app
from styles.text_field import TextField


class Arc(MiniWidget):

    # Constructor.
    def __init__(
        self, 
        title: str, 
        widget: Widget, 
        page: ft.Page, 
        key: str, 
        x_alignment: float = None,          # Position of center of arc on plotline if we pass one in (between -1 and 1)
        data: dict = None
    ):
        
        
        # Parent constructor
        super().__init__(
            title=title,        
            widget=widget,                    # Top most plotline this arc belongs too
            page=page,          
            key=key,  
            data=data,         
        ) 

        # Newly created arcs
        if x_alignment is not None:

            # Calculate pixel values we need
            x_align_pixel = int((x_alignment + 1) / 2 * widget.plotline_width)
            
            # Left and right pixel values
            left = x_align_pixel - 50
            
            if left <= 0:
                left = 0
                x_align_pixel = 50

            rp = widget.plotline_width - x_align_pixel
            right = rp - 50
            
            if right >= widget.plotline_width:
                right = 0

            left_ratio = left / max(widget.plotline_width, 1)
            right_ratio = right / max(widget.plotline_width, 1)

            

        # Needs values but they shouldn't be used, since the arc is not new
        else:
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
                'color': "primary",                       # Color of the arc in the plotline
                
                # For rendering on plotline
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
                'Relevant Characters': list,
            },
        )


        # UI elements
        self.plotline_control: ft.Container = None      # Arc shaped contorl on the plotline

        # State variables
        self.is_dragging: bool = False              # If we are currently dragging our arc slider
        self.dragging_direction: str = "left"       # Direction we're dragging, left or right
        self.hidden = False                         # Track if we're in hidden mode for easier dragging

        # Loads our arc
        self.reload_plotline_control()
        self.reload_mini_widget()


    async def create_event(self, title: str):
        ''' Creates a new event in our events list with the given title '''

        # Add this new event to our data and save it
        events = self.data.get('Events', [])
        events.append({'title': title, 'description': ""})
        self.data['Events'] = events
        await self.save_dict()

        # Reload our mini widget to show this new event
        self.reload_mini_widget()


    # Called when we hover over our arc on the plotline
    async def _highlight(self, e=None):
        ''' Focuses the arc control '''

        # Change its border opacity and update the page
        self.plotline_control.shadow = ft.BoxShadow(0, 10, self.data.get('color'), blur_style=ft.BlurStyle.OUTER)

        self.plotline_control.content.content.content.controls[0].visible = True
        self.plotline_control.content.content.content.controls[2].visible = True

        self.plotline_control.update()

    # Called when we stop hovering over our arc on the plotline
    async def _stop_highlight(self, e=None):
        ''' Changes the arc control to unfocused '''

        if self.is_dragging:
            return
        
        # If we are not visible, lower our border and text
        if not self.visible:
            self.plotline_control.shadow = None
            
            self.plotline_control.content.content.content.controls[0].visible = False
            self.plotline_control.content.content.content.controls[2].visible = False
        
            self.plotline_control.update()
    
    async def hide_mini_widget(self, e=None, update=True):
        ''' Hides this arc '''
        #print(f"Hiding mini widget {self.title}")

        self.plotline_control.shadow = None

        self.plotline_control.content.content.content.controls[0].visible = False
        self.plotline_control.content.content.content.controls[2].visible = False
        self.plotline_control.update()
        
        return await super().hide_mini_widget(update=update)
    

    # Called at the start of dragging our point on the slider
    async def start_dragging(self, e: ft.PointerEvent):
        ''' Called when we start dragging our slider thumb '''

        self.is_dragging = True
        width = self.widget.plotline_width - self.data.get('left', 0) - self.data.get('right', 0)

        if e.local_position.x < width / 2:
            self.dragging_direction = "left"
        else:
            self.dragging_direction = "right"

        self.plotline_control.content.mouse_cursor = ft.MouseCursor.RESIZE_LEFT_RIGHT
        self.plotline_control.update()

        # Hide all other info displays while dragging
        for mw in self.widget.mini_widgets:
            if isinstance(mw, Arc) and mw != self:
                mw.plotline_control.ignore_interactions = True
                mw.plotline_control.update()



    # Called at the end of dragging our point on the slider to update it
    async def change_x_positions(self, e: ft.DragUpdateEvent):
        ''' Changes our x position on the slider, and saves it to our data dictionary, but not to our file yet '''

        # Check to make sure we are wide enough (100px)
        width = self.widget.plotline_width - self.data.get('left', 0) - self.data.get('right', 0)
        
        ratio = width / max(self.widget.plotline_width, 1)
        
        # If we're dragging the left handle, update left position
        if self.dragging_direction == "left":   # If we're dragging left handle (dragging right would make it bigger, dragging left would make it smaller)
            new_left = self.data.get('left', 0) + e.local_delta.x

            # Clamp edges
            if new_left < 10:
                new_left = 10
            if new_left > self.widget.plotline_width - 10:     # Make sure we don't drag past the plotline
                new_left = self.widget.plotline_width - 10

            # Width check that we're not too small
            if width >= 130:
                self.data['left'] = new_left
                self.plotline_control.left = new_left

            elif width < 130 and e.local_delta.x < 0:   # If we're trying to make it smaller, allow it, but not if we're trying to make it bigger
                self.data['left'] = new_left
                self.plotline_control.left = new_left

        # If we're dragging the right handle, update the right position
        else:
            new_right = self.data.get('right', 0) - e.local_delta.x

            # Clamp edges
            if new_right < 10:     # Make sure we don't drag past the plotline
                new_right = 10
            if new_right > self.widget.plotline_width:
                new_right = self.widget.plotline_width

            # Width check that we're not too small
            if width >= 130:
                self.data['right'] = new_right
                self.plotline_control.right = new_right

            elif width < 130 and e.local_delta.x > 0:   # If we're trying to make it smaller, allow it, but not if we're trying to make it bigger
                self.data['right'] = new_right
                self.plotline_control.right = new_right

        #new_height = (self.widget.plotline_height / 2) * (ratio) - 40
        new_height = width * 0.5

        if new_height >= self.widget.plotline_height / 2 - 70:
            new_height = self.widget.plotline_height / 2 - 70
        if new_height < 50:
            new_height = 50

            #print("New height of arc: ", new_height, " for width: ", width)

        self.plotline_control.height = int(new_height)

        # Apply the updates
        self.plotline_control.update()


    # Called when we finish dragging our slider thumb to save our new position
    async def finished_dragging(self, e=None):
        ''' Saves our new x positions to the file and updates alignment. Then applies the UI changes '''

        # Update our state
        self.is_dragging = False                # No longer dragging

        # Update our x alignment based on our new left and right positions, and save it to our data
        x_align_pixel = self.data.get('left', 0) + ((self.widget.plotline_width - self.data.get('left', 0) - self.data.get('right', 0)) / 2)
        self.data['x_alignment'] = ((x_align_pixel) / max(self.widget.plotline_width, 1)) * 2 - 1
  
        width = self.widget.plotline_width - self.data.get('left', 0) - self.data.get('right', 0)
        self.data['width'] = width

        self.data['left_ratio'] = self.data.get('left', 0) / max(self.widget.plotline_width, 1)
        self.data['right_ratio'] = self.data.get('right', 0) / max(self.widget.plotline_width, 1)

        # Hide all other info displays while dragging
        for mw in self.widget.mini_widgets:
            if isinstance(mw, Arc) and mw != self:
                mw.plotline_control.ignore_interactions = False
                mw.plotline_control.update()

        self.plotline_control.content.mouse_cursor = ft.MouseCursor.CLICK
        self.plotline_control.update()
            
        # Save our new positions to file
        await self.save_dict()

        if self.widget.information_display.visible:
            self.widget.information_display.reload_mini_widget()

        # Makes sure any resized arcs are sorted correctly
        self.widget.reload_widget()

        


    # Called when toggling whether this plot point is shown on the plotline in the plotline filters
    async def toggle_plotline_control(self, value: bool):
        ''' Toggles whether this plot point is shown on the plotline '''

        # Change the control visibility, data, and save it
        self.plotline_control.visible = value
        self.data['is_shown_on_widget'] = value
        await self.save_dict()
        
        # If we're hiding it, also hide our mini widget if it's open
        if value == False:
            self.hide_mini_widget()

        for mw in self.widget.mini_widgets:
            if hasattr(mw, 'plotline_control'):
                mw.reload_plotline_control(no_update=True)
        self.widget.reload_widget()  
        

    # Called from reload mini widget to update our plotline control
    def reload_plotline_control(self, no_update=False):
        ''' Reloads our arc drawing on the plotline based on current/updated data, including page size '''

        width = self.widget.plotline_width - self.data.get('left', 0) - self.data.get('right', 0)

        h = width * 0.5
        if h < 50:
            h = 50

        self.plotline_control = ft.Container(
            left=self.data.get('left', 0), right=self.data.get('right', None),
            alignment=ft.Alignment.TOP_CENTER, #height=h,
            margin=ft.Margin(16, 0, 16, 0), 
            animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            animate=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            border=ft.Border.only(          # Give use borderes on top left and right
                left=ft.BorderSide(2, self.data.get('color', "note")),
                right=ft.BorderSide(2, self.data.get('color', "note")),
                top=ft.BorderSide(2, self.data.get('color', "note")),
            ), 
            padding=ft.Padding.only(top=10),
            border_radius=ft.BorderRadius.only(top_left=10000, top_right=10000, bottom_left=0, bottom_right=0),      # Make it uber curved to look like an arc
            content=ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK,
                hover_interval=200, expand=True,
                on_tap=self.show_mini_widget,    # Focus this mini widget when clicked
                on_secondary_tap=lambda _: self.widget.story.open_menu(self._get_menu_options()),
                on_enter=self._highlight,      # Highlight container
                on_exit=self._stop_highlight,        # Stop highlight
                on_pan_update=self.change_x_positions, 
                on_pan_start=self.start_dragging, 
                on_pan_end=self.finished_dragging,
                drag_interval=10,
                content=ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.ARROW_LEFT_OUTLINED, ft.Colors.ON_SURFACE_VARIANT, scale=0.8, visible=False),
                            ft.Text(
                                self.title, #expand=True, 
                                overflow=ft.TextOverflow.VISIBLE, 
                                theme_style=ft.TextThemeStyle.LABEL_LARGE, text_align=ft.TextAlign.CENTER,
                            ), 
                            ft.Icon(ft.Icons.ARROW_RIGHT_OUTLINED, ft.Colors.ON_SURFACE_VARIANT, scale=0.8, visible=False)
                        ], expand=True, spacing=0, alignment=ft.MainAxisAlignment.CENTER),
                        margin=ft.Margin.symmetric(horizontal=25), expand=True, alignment=ft.Alignment.TOP_CENTER,
                        padding=ft.Padding.only(top=10)
                    ),
        
            )
        )

        if no_update:
            return

        try:
            self.plotline_control.update()
        except Exception as _:
            pass
        
        

    # Called to reload our mini widget content
    def reload_mini_widget(self):


        arc_title_text = ft.GestureDetector(
            ft.Text(f"\t\t{self.data['title']}\t\t", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, 
                tooltip=f"Rename {self.title}", color=self.data.get('color', None), expand=True),
            on_double_tap=self._rename_clicked,
            on_tap=self._rename_clicked,
            on_secondary_tap=lambda _: self.widget.story.open_menu(self._get_menu_options()),
            mouse_cursor="click", hover_interval=500, expand=True
        )

        close_button = ft.IconButton(
            ft.Icons.CLOSE, ft.Colors.OUTLINE,
            tooltip=f"Close {self.title}",
            on_click=self.hide_mini_widget,
            mouse_cursor="click"
        )
        

        title_control = ft.Row([
            arc_title_text,
            close_button
        ], spacing=0)

        summary_tf = TextField(
            value=self.data.get('Summary', ''), multiline=True, expand=True, 
            on_blur=lambda e: self.change_data(**{'Summary': e.control.value}), 
            label="Summary", capitalization=ft.TextCapitalization.SENTENCES,
            tooltip="Summary of what happened during this arc", dense=True
        )

        start_tf = TextField(
            value=self.data.get('Start', ''), multiline=True, expand=True, 
            on_blur=lambda e: self.change_data(**{'Start': e.control.value}), 
            label="Start", capitalization=ft.TextCapitalization.SENTENCES,
            tooltip="When this arc began", dense=True
        )

        end_tf = TextField(
            value=self.data.get('End', ''), multiline=True, expand=True, 
            on_blur=lambda e: self.change_data(**{'End': e.control.value}), 
            label="End", capitalization=ft.TextCapitalization.SENTENCES,
            tooltip="When this arc ends", dense=True
        )

        where_tf = TextField(
            value=self.data.get('Where'), multiline=True, expand=True, 
            on_blur=lambda e: self.change_data(**{'Where': e.control.value}), 
            label="Where", capitalization=ft.TextCapitalization.SENTENCES,
            tooltip="List of location(s) related to this plot point", dense=True
        )

        def _get_events_controls() -> list[ft.Control]:

            async def _change_event_description(e):
                
                new_description = e.control.value
                event_idx = e.control.data
                print("Index: ", event_idx)

                events = self.data.get('Events', [])
                if event_idx < len(events):
                    event = events[event_idx]
                    if isinstance(event, dict):
                        event['description'] = new_description
                        self.data['Events'][event_idx] = event
                        await self.save_dict()

            async def _delete_event(e):
                event_idx = e.control.data
                events = self.data.get('Events', [])
                if event_idx < len(events):
                    events.pop(event_idx)
                    self.data['Events'] = events
                    await self.save_dict()
                    self.reload_mini_widget()


            controls = []
            for idx, event in enumerate(self.data.get('Events', [])):
                event_title = event.get('title', "") if isinstance(event, dict) else event
                event_description = event.get('description', "") if isinstance(event, dict) else ""
                event_tf = ft.ReorderableDragHandle(
                    ft.Container(
                        TextField(
                            value=event_description, dense=True, data=idx, label=event_title, expand=True,
                            on_blur=_change_event_description, capitalization=ft.TextCapitalization.SENTENCES, multiline=True,
                            suffix_icon=ft.IconButton(ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, data=idx, on_click=_delete_event, mouse_cursor="click")
                        ),
                        padding=ft.Padding.only(left=10, right=35, top=5, bottom=5), expand=True
                    )
                )
                controls.append(event_tf)
            return controls
        
        async def _reorder_events(e):
            ''' Reorders our events list based on the new order after a drag and drop reorder '''
            events = self.data.get('Events', [])
            event = events.pop(e.old_index)
            events.insert(e.new_index, event)

            events_list.controls = _get_events_controls()
            self.data['Events'] = events
            await self.save_dict()
            self.update()
        
        events_label = ft.Row([
            ft.Text(
                "\tEvents", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None),
                tooltip="List of events (plot points) that happened during this arc. Drag to reorder them"
            ),
            ft.IconButton(
                ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, 
                self.data.get('color', "primary"),
                tooltip="Add Event", 
                on_click=lambda e: self.p.run_task(self.widget.new_item_clicked, e, self), data="event",
                mouse_cursor="click"
            ),
        ], spacing=0)


        events_list = ft.ReorderableListView(
            padding=ft.Padding.all(4), #show_default_drag_handles=False,
            controls=_get_events_controls(), on_reorder=_reorder_events, 
            spacing=16,
        )


        # Adds or removes characters from our Relevant characters list
        def _toggle_Relevant_characters(e):
            
            should_add_key = True   # Flag to check if we need to remove or not
            char_key = e.control.data   # Key of the character

            for key in self.data.get('Relevant Characters', []):
                if char_key == key:     # If the character is in there, remove them and break
                    self.data['Relevant Characters'].remove(key)
                    should_add_key = False      # Make sure we don't re-add them after
                    break

            # If we went through the list and didn't find them, add them to the list
            if should_add_key:
                #print("Adding key")
                self.data.get('Relevant Characters', []).append(char_key)

            self.p.run_task(self.save_dict)

            Relevant_characters_row.controls = _set_Relevant_characters_controls()
            Relevant_characters_selector.controls = _get_Relevant_characters()
            self.update()

        # Called to check our list of characters Relevant on this plotpoint. They are stored as keys and returned as names for display
        def _get_Relevant_characters() -> list[str]:
            char_list = []
            
            for widget in self.widget.story.widgets:
                if widget.data.get('tag', None) == 'character':
                    char_key = widget.data.get('key', "")
                    
                    char_list.append(
                        ft.Checkbox(
                            widget.title,
                            True if char_key in self.data.get('Relevant Characters', []) else False,
                            data=char_key,
                            label_style=ft.TextStyle(color=widget.data.get('color', None), weight=ft.FontWeight.BOLD),
                            on_change=_toggle_Relevant_characters,
                            mouse_cursor="click"
                        )
                    )

            if len(char_list) == 0:
                char_list.append(ft.Text("No characters in story yet", color=ft.Colors.OUTLINE, italic=True))
            return char_list

        def _toggle_Relevant_characters_selector(e=None):
            Relevant_characters_selector.visible = not Relevant_characters_selector.visible
            Relevant_characters_selector.controls = _get_Relevant_characters()

            if Relevant_characters_selector.visible:
                add_Relevant_characters_button.icon = ft.Icons.EDIT_OFF_OUTLINED
            else:
                add_Relevant_characters_button.icon = ft.Icons.EDIT_OUTLINED

            self.update()

        add_Relevant_characters_button = ft.TextButton(
            "Relevant Characters",
            ft.Icons.EDIT_OUTLINED,
            style=ft.ButtonStyle(text_style=ft.TextStyle(weight=ft.FontWeight.BOLD), mouse_cursor="click", color=ft.Colors.ON_SURFACE),
            on_click=_toggle_Relevant_characters_selector,
            
        )

        Relevant_characters_selector = ft.Column(
            _get_Relevant_characters(),
            visible=False,
        )

        def _set_Relevant_characters_controls(e=None) -> list[ft.Control]:

            controls = [
                add_Relevant_characters_button,
            ]

            for idx, ic_key in enumerate(self.data.get('Relevant Characters', [])):
                char = None
                for widget in self.widget.story.widgets:
                    if widget.data.get('key', "") == ic_key and widget.data.get('tag', None) == 'character':
                        char = widget
                        break
                if char is not None:
                    name = char.data.get('title', ic_key)


                    # Add the control now
                    controls.append(
                        ft.Row([
                            ft.Text(name, color=char.data.get('color', None), weight=ft.FontWeight.BOLD),
                            ft.IconButton(
                                ft.Icons.CLOSE, char.data.get('color', None), scale=0.8,
                                data=ic_key, mouse_cursor="click",
                                on_click=_toggle_Relevant_characters,
                            )
                        ], spacing=0, tight=True)
                    )
                    
                    if idx < len(self.data.get('Relevant Characters', [])) - 1: # Skip adding container to last character
                        controls.append(ft.Container(width=10))
                           

            return controls

        Relevant_characters_row = ft.Column(
            _set_Relevant_characters_controls(),
            spacing=0,
        )

       

        notes_label = ft.Row([
            ft.Container(width=6),
            ft.Text("Notes", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),
            ft.IconButton(
                ft.Icons.NEW_LABEL_OUTLINED, self.data.get('color', "primary"), tooltip="Add Note",
                on_click=self._new_note_clicked,
                mouse_cursor="click"
            )
        ], spacing=0)

        notes_column = self._build_notes_column()

        # Build the main body content of our info display
        content = ft.Column(
            expand=True, tight=True, scroll="auto", alignment=ft.MainAxisAlignment.START, spacing=0,
            controls=[
                ft.Container(height=10), # Spacer
                summary_tf,             # Summary

                ft.Container(height=10), # Spacer
                ft.Row([start_tf, end_tf]),             # When

                ft.Container(height=10), # Spacer
                where_tf,           # Where
                ft.Container(height=10), # Spacer
                ft.Divider(2, 2),

                events_label,
                events_list,

                Relevant_characters_row,        # Holds label, buttons for each Relevant character, and add/remove button
                Relevant_characters_selector,
                
                ft.Divider(2, 2),
                notes_label,
                ft.Container(notes_column, margin=ft.Margin.symmetric(horizontal=20)),
            ]
        )
        
        column = ft.Column([
            title_control,
            ft.Divider(),
            content
        ], expand=True, spacing=0)

        
        self.content = column
    

        try:
            self.update()
        except Exception as _:
            pass


