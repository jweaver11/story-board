import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
from utils.verify_data import verify_data
import math
from styles.text_styles import text_style
import flet.canvas as cv
from styles.icons import icons

# Plotpoint mini widget object that appear on plotlines and arcs
class PlotPoint(MiniWidget):

    # Constructor. Requires title, widget widget, page reference, and optional data dictionary
    def __init__(
        self, 
        title: str, 
        widget: Widget, 
        page: ft.Page, 
        key: str,                           # Key is plot_points for plotlines
        x_alignment: float = None,          # Position of plot point on plotline if we pass one in (between -1 and 1)
        left: int = None,                   # Absolute left position on plotline. If not provided, will be calculated from x_alignment
        data: dict = None       
    ):
        
        # Check if we're new and need to create file
        is_new = False
        if data is None:
            is_new = True
        
        if left is not None:
            side_location = 'right' if left <= widget.plotline_width // 2 else 'left'
        else:
            side_location = data.get('side_location', 'right') if data is not None else 'right'


        # Parent constructor
        super().__init__(
            title=title,        
            widget=widget,        
            page=page,          
            key=key,  
            side_location=side_location,
            data=data,    
        ) 

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {   
                'tag': "plot_point",            # Tag to identify what type of object this is
                'x_alignment': x_alignment if x_alignment is not None else float,           # Float between -1 and 1 on x axis of plotline. 0 is center
                'icon': "circle",
                'left': left, 
                'color': "secondary",           # Color of the plot point on the plotline

                # Information for our information display
                'Description': str,
                'When': str,
                'Where': str,
                'Involved Characters': list,
                'Related Objects': list,
            },
        )

        # Set our x alignment to position on our plotline. -1 is left, 0 is center, 1 is right. Default 0
        self.x_alignment = ft.Alignment(self.data.get('x_alignment', 0), 0)

        # UI elements
        self.plotline_control: ft.Container = None    # Circle container to show our plot point on the plotline
        self.icon_button = ft.PopupMenuButton(      # Button to change the plot points icon on the plotline
            icon=self.data.get('icon', 'circle'),
            tooltip="Plot Point Icon", icon_color=self.data.get('color', 'secondary'),
            menu_padding=ft.Padding(0,0,0,0), 
            items=self._get_icon_options()
        )

        # State variables
        self.is_dragging: bool = False              # If we are currently dragging our plot point

        if is_new:
            self.p.run_task(self.save_dict)

        # Reloads the information display of the canvas
        self.reload_plotline_control()
        self.reload_mini_widget()

    
    async def move_plot_point(self, e=None):
        ''' Changes our x position on the slider, and saves it to our data dictionary, but not to our file yet '''

        if e is None:
            delta_x = 0
        else:
            delta_x = e.delta_x

        if not isinstance(delta_x, (int, float)):
            delta_x = 0
        
        
        # Calculate our new absolute positioning based on our delta x from dragging
        new_left = self.plotline_control.left + delta_x

        # Clamp sides and use timeline padding
        if new_left < 0:        # Padding on left because canvas draws in middle (5px)
            new_left = 0
        elif new_left > self.widget.plotline_width - 16:  # No padding needed on right
            new_left = self.widget.plotline_width - 16
        
        # Set our new left position within our stack
        self.plotline_control.left = new_left

        self.data['left'] = new_left

        await self.save_dict()
        self.plotline_control.update()
        
            
    # Called when toggling whether this plot point is shown on the plotline in the plotline filters
    async def toggle_plotline_control(self, value: bool):
        ''' Toggles whether this plot point is shown on the plotline '''

        # Change the control visibility, data, and save it
        self.plotline_control.visible = value
        self.data['is_shown_on_widget'] = value
        await self.save_dict()
        
        # If we're hiding it, also hide our mini widget if it's open
        if value == False:
            await self.hide_mini_widget()

        self.widget.reload_widget()
          
    # Called when we start dragging
    async def _drag_start(self, e=None):
        ''' Called when we start dragging our plot point. Sets our state to dragging and changes our mouse cursor '''

        self.plotline_control.content.mouse_cursor = ft.MouseCursor.RESIZE_LEFT_RIGHT
        self.is_dragging = True

        # Hide all other info displays while dragging
        for mw in self.widget.mini_widgets:
            mw.visible = False

        self.update()

    # Quick fixer for the mouse cursor and highlight is we just clicked the plotpoint without dragging
    async def _tap_up(self, e=None):
        self.plotline_control.content.mouse_cursor = ft.MouseCursor.CLICK
        await self._highlight()

    # Called when we finish dragging our plotline_marker to save our position
    async def _drag_end(self, e=None):
        ''' Updates our alignment and side location, and applies the updadte to the canvas for our label '''

        self.plotline_control.content.mouse_cursor = ft.MouseCursor.CLICK
        self.is_dragging = False
        if not self.visible:        # Turn of highlight if we're not visilbe
            self.plotline_control.shadow = None
        
        x_alignment = (self.data.get('left', 0) / (self.widget.plotline_width - 10)) * 2.0 - 1.0

        self.data['x_alignment'] = x_alignment

        if self.data.get('x_alignment', 0) <= 0:
            self.data['side_location'] = "right"
        else:
            self.data['side_location'] = "left"

        await self.save_dict()

        # Re-show all the info displays we hid while dragging
        for mw in self.widget.mini_widgets:
            if mw.data.get('visible', True):
                mw.visible = True

        if self.widget.information_display.visible:
            self.widget.information_display.reload_mini_widget(no_update=True)
        await self.widget.rebuild_plotline_canvas(no_update=False)

        self.widget.story.active_rail.content.reload_rail()

    # Called when hovering over our plot point to show the slider
    async def _highlight(self, e=None):
        ''' Shows our slider and hides our plotline_marker. Makes sure all other sliders are hidden '''

        # Gives us a focused shadow
        self.plotline_control.shadow = ft.BoxShadow(5, 10, ft.Colors.with_opacity(.6, self.data.get('color'))) #if self.plotline_control.shadow is None else None
        self.plotline_control.update()

    # Hides are shadow unless our info display is visible, then stay highlighted
    async def _stop_highlight(self, e=None):

        # If we're dragging, keep highlighted
        if self.is_dragging:
            return

        # If our info display is visible, keep highlighted
        if not self.visible:
            self.plotline_control.shadow = None
            self.plotline_control.update()

    def _get_icon_options(self) -> list[ft.Control]:
        ''' Returns a list of all available icons for icon changing '''

        # Called when an icon option is clicked on popup menu to change icon
        def _change_icon(icon: str, e):
            ''' Passes in our kwargs to the widget, and applies the updates '''

            # Set our data and update our button icon
            self.data['icon'] = icon
            self.p.run_task(self.save_dict)

            # Update the UI to match. Plotline control needs widget to reload as well
            self.icon_button.icon = icon
            self.reload_plotline_control()
            self.widget.reload_widget()

        # List for our icons when formatted
        icon_controls = [] 

        # Create our controls for our icon options
        for icon in icons:
            icon_controls.append(
                ft.PopupMenuItem(
                    content=ft.Icon(icon, self.data.get('color', 'secondary')),
                    on_click=lambda e, ic=icon: _change_icon(ic, e)
                )
            )

        return icon_controls
    
    # Makes sure we stop highlighting
    def hide_mini_widget(self, e=None):
        self.plotline_control.shadow = None
        self.plotline_control.update()
        return super().hide_mini_widget()


    # Called from reload_mini_widget
    def reload_plotline_control(self):
        """ Rebuilds our plotline control that holds our plot point and slider """

        # Our container that is our plot point on the plotline, and contains our gesture detector for hovering and right clicking
        self.plotline_control = ft.Container(
            margin=ft.Margin(16, 0, 16, 0), expand=False, 
            opacity=1.0, shape=ft.BoxShape.CIRCLE,
            alignment=ft.Alignment.CENTER, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            left=self.data.get('left', 0), animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            content=ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK, on_tap_up=self._tap_up,
                on_enter=self._highlight, on_exit=self._stop_highlight, on_pan_start=self._drag_start,
                on_pan_update=self.move_plot_point, drag_interval=20, on_pan_end=self._drag_end,
                on_secondary_tap=lambda e: self.widget.story.open_menu(self._get_menu_options()),
                on_tap=self.show_mini_widget, on_tap_down=self._drag_start,
                content=ft.Icon(self.data.get('icon', 'circle'), self.data.get('color', None))
            ),
        )

        try:
            self.plotline_control.update()
        except Exception as e:
            pass


    # Called when reloading changes to our plot point and in constructor
    def reload_mini_widget(self):
        ''' Rebuilds any parts of our UI and information that may have changed when we update our data '''

        title_control = ft.Row([
            self.icon_button,
            ft.GestureDetector(
                ft.Text(f"\t\t{self.data['title']}\t\t", weight=ft.FontWeight.BOLD, tooltip=f"Rename {self.title}"),
                on_double_tap=self._rename_clicked,
                on_tap=self._rename_clicked,
                on_secondary_tap=lambda e: self.widget.story.open_menu(self._get_menu_options()),
                mouse_cursor="click", hover_interval=500
            ),
            ft.IconButton(
                ft.Icons.PUSH_PIN_OUTLINED if not self.widget.data.get('information_display_is_pinned', False) else ft.Icons.PUSH_PIN_ROUNDED,
                self.data.get('color', None),
                tooltip="Pin Information Display" if not self.widget.data.get('information_display_is_pinned', False) else "Unpin Information Display",
                on_click=self._toggle_pin
            ),
            ft.Container(expand=True),
            ft.IconButton(
                ft.Icons.CLOSE, ft.Colors.OUTLINE,
                tooltip=f"Close {self.title}",
                on_click=self.hide_mini_widget,
            ),
        ], spacing=0)


        description_tf = ft.TextField(
            value=self.data.get('Description', ''), multiline=True, expand=True, 
            on_blur=lambda e: self.change_data(**{'Description': e.control.value}), 
            label="Description", capitalization=ft.TextCapitalization.SENTENCES,
            tooltip="Brief description of this plot point"
        )

        when_tf = ft.TextField(
            value=self.data.get('When', ''), multiline=True, expand=True, 
            on_blur=lambda e: self.change_data(**{'When': e.control.value}), 
            label="When", capitalization=ft.TextCapitalization.SENTENCES,
            tooltip="Time or date related to this plot point"
        )

        where_tf = ft.TextField(
            value=self.data.get('Where'), multiline=True, expand=True, 
            on_blur=lambda e: self.change_data(**{'Where': e.control.value}), 
            label="Where", capitalization=ft.TextCapitalization.SENTENCES,
            tooltip="List of location(s) related to this plot point"
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
                #print("Adding key")
                self.data.get('Involved Characters', []).append(char_key)

            self.p.run_task(self.save_dict)

            involved_characters_row.controls = _set_involved_characters_controls()
            involved_characters_selector.controls = _get_involved_characters()
            self.update()

        # Called to check our list of characters involved on this plotpoint. They are stored as keys and returned as names for display
        def _get_involved_characters() -> list[str]:
            char_list = []
            
            for widget in self.widget.story.widgets:
                if widget.data.get('tag', None) == 'character':
                    
                    char_list.append(
                        ft.Checkbox(
                            widget.title,
                            #True if char_key in self.data.get('Involved Characters', []) else False,
                            #data=char_key,
                            #label_style=ft.TextStyle(color=char_obj.data.get('color', None), weight=ft.FontWeight.BOLD),
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

            self.update()

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
                char = self.widget.story.characters.get(ic_key, None)
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

            self.update()

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
                char = self.widget.story.objects.get(obj_key, None)
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

            self.p.run_task(self.save_dict)

            related_objects_row.controls = _set_related_objects_controls()
            related_objects_selector.controls = _get_related_objects()
            self.update()

        def _get_related_objects() -> list[str]:
            char_list = []
            
            for widget in self.widget.story.widgets:
                if widget.data.get('tag', None) == 'object':
                    
                    char_list.append(
                        ft.Checkbox(
                            widget.title,
                            #True if obj_key in self.data.get('Involved Characters', []) else False,
                            #data=obj_key,
                            #label_style=ft.TextStyle(color=obj_obj.data.get('color', None), weight=ft.FontWeight.BOLD),
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

        content = ft.Column(
            expand=True, tight=True, scroll="auto", alignment=ft.MainAxisAlignment.START, 
            controls=[
                ft.Container(height=1),
                description_tf,
                ft.Row([when_tf, where_tf]),
                
                involved_characters_row,        # Holds label, buttons for each involved character, and add/remove button
                involved_characters_selector,
                
                related_objects_row,
                related_objects_selector,
                
                custom_fields_label,
                ft.Container(custom_fields_column, margin=ft.Margin.symmetric(horizontal=20)),
            ]
        )

        column = ft.Column([
            title_control,
            ft.Divider(height=2, thickness=2),
            content
        ], expand=True, scroll="none", tight=True, alignment=ft.MainAxisAlignment.START)
        
        self.content = column
        
      
            

        try:
            self.update()
        except Exception as _:
            pass
