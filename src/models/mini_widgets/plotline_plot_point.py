import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
from utils.verify_data import verify_data
import math
from styles.text_styles import text_style
import flet.canvas as cv
from styles.icons import icons
from styles.text_field import TextField

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
        
        # Parent constructor
        super().__init__(
            title=title,        
            widget=widget,        
            page=page,          
            key=key,  
            data=data,    
        ) 

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {   
                'tag': "plot_point",            # Tag to identify what type of object this is
                'x_alignment': x_alignment if x_alignment is not None else float,           # Float between -1 and 1 on x axis of plotline. 0 is center
                'left': left, 
                'color': "primary",           # Color of the plot point on the plotline

                # Information for our information display
                'Description': str,
                'When': str,
                'Where': str,
                'Relevant Characters': list,
            },
        )

        # Set our x alignment to position on our plotline. -1 is left, 0 is center, 1 is right. Default 0
        self.x_alignment = ft.Alignment(self.data.get('x_alignment', 0), 0)

        # UI elements
        self.plotline_control: ft.Container = None    # Circle container to show our plot point on the plotline

        # State variables
        self.is_dragging: bool = False              # If we are currently dragging our plot point
        self.is_first_launch: bool = True            # If this is the first time we're loading this plot point, used to trigger animations on first load

        if is_new:
            self.p.run_task(self.save_dict)

        # Reloads the information display of the canvas
        self.reload_plotline_control()
        self.reload_mini_widget()


    
    async def move_plot_point(self, e: ft.DragUpdateEvent):
        ''' Changes our x position on the slider, and saves it to our data dictionary, but not to our file yet '''

       
        if e is None:
            delta_x = 0
        else:
            delta_x = e.local_delta.x

        if not isinstance(delta_x, (int, float)):
            delta_x = 0
        
        
        # Calculate our new absolute positioning based on our delta x from dragging
        new_left = self.plotline_control.left + delta_x

        # Clamp sides and use timeline padding
        if new_left < 0:        # Padding on left because canvas draws in middle (5px)
            new_left = 0
        elif new_left > self.widget.plotline_width - 25:  # No padding needed on right
            new_left = self.widget.plotline_width - 25
        
        # Set our new left position within our stack
        self.plotline_control.left = new_left

        self.data['left'] = new_left

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

        for mw in self.widget.mini_widgets:
            if hasattr(mw, 'plotline_control'):
                mw.reload_plotline_control(no_update=True)
        self.widget.reload_widget()
          
    # Called when we start dragging
    async def _drag_start(self, e: ft.DragStartEvent):
        ''' Called when we start dragging our plot point. Sets our state to dragging and changes our mouse cursor '''

        self.plotline_control.content.mouse_cursor = ft.MouseCursor.RESIZE_LEFT_RIGHT
        self.plotline_control.update()
        self.is_dragging = True

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

        await self.save_dict()

        if self.widget.information_display.visible:
            self.widget.information_display.reload_mini_widget()

        await self.widget.rebuild_plotline_canvas(True)
        #self.widget.story.active_rail.reload_rail()

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
        async def _change_icon(e):
            ''' Passes in our kwargs to the widget, and applies the updates '''

            # Set our data and update our button icon
            self.data['icon'] = e.control.data
            await self.save_dict()

            # Update the UI to match. Plotline control needs widget to reload as well
            self.reload_mini_widget()
            self.widget.reload_widget()

        # List for our icons when formatted
        icon_controls = [] 

        # Create our controls for our icon options
        for icon in icons:
            icon_controls.append(
                ft.MenuItemButton(
                    content=ft.Icon(icon, self.data.get('color', 'note')),
                    on_click=_change_icon,
                    data=icon,
                    style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK)
                )
            )

        return icon_controls
    
    # Makes sure we stop highlighting
    async def hide_mini_widget(self, e=None, update=True):
        self.plotline_control.shadow = None
        self.plotline_control.update()
        return await super().hide_mini_widget(update=update)


    # Called from reload_mini_widget
    def reload_plotline_control(self, no_update=False):
        """ Rebuilds our plotline control that holds our plot point and slider """

        # Our container that is our plot point on the plotline, and contains our gesture detector for hovering and right clicking
        self.plotline_control = ft.Container(
            margin=ft.Margin(16, 0, 16, 0), 
            opacity=1.0, shape=ft.BoxShape.CIRCLE,
            #bgcolor="red", 
            width=24, height=24,
            alignment=ft.Alignment.CENTER, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            left=self.data.get('left', 0), animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            content=ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK, on_tap_up=self._tap_up,
                on_enter=self._highlight, on_exit=self._stop_highlight, on_pan_start=self._drag_start,
                on_pan_update=self.move_plot_point, drag_interval=20, on_pan_end=self._drag_end,
                on_secondary_tap=lambda _: self.widget.story.open_menu(self._get_menu_options()),
                on_tap=self.show_mini_widget, on_tap_down=self._drag_start,
                content=ft.Icon(ft.Icons.CIRCLE, self.data.get('color', None))
            ),
        )
        
        if no_update:
            return

        try:
            self.plotline_control.update()
        except Exception as _:
            pass


    # Called when reloading changes to our plot point and in constructor
    def reload_mini_widget(self):
        ''' Rebuilds any parts of our UI and information that may have changed when we update our data '''

        title_control = ft.Row([
            ft.GestureDetector(
                ft.Text(f"\t{self.data['title']}", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, 
                color=self.data.get('color', None), expand=True),
                on_double_tap=self._rename_clicked,
                on_secondary_tap=lambda _: self.widget.story.open_menu(self._get_menu_options()),
                mouse_cursor="click", hover_interval=500, expand=True
            ),
            
            ft.IconButton(
                ft.Icons.CLOSE, ft.Colors.OUTLINE,
                tooltip=f"Close {self.title}",
                on_click=self.hide_mini_widget,
                mouse_cursor="click"
            ),
        ], spacing=0)


        description_tf = TextField(
            value=self.data.get('Description', ''), multiline=True, expand=True, 
            on_blur=lambda e: self.change_data(**{'Description': e.control.value}), 
            label="Description", capitalization=ft.TextCapitalization.SENTENCES,
            dense=True
        )

        when_tf = TextField(
            value=self.data.get('When', ''), multiline=True, expand=True, 
            on_blur=lambda e: self.change_data(**{'When': e.control.value}), 
            label="When", capitalization=ft.TextCapitalization.SENTENCES,
            dense=True
        )

        where_tf = TextField(
            value=self.data.get('Where'), multiline=True, expand=True, 
            on_blur=lambda e: self.change_data(**{'Where': e.control.value}), 
            label="Where", capitalization=ft.TextCapitalization.SENTENCES,
            dense=True
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
                #add_Relevant_characters_button.icon = ft.Icons.EDIT_OFF_OUTLINED
                add_Relevant_characters_button.content.controls[1].icon = ft.Icons.EDIT_OFF_OUTLINED
            else:
                add_Relevant_characters_button.content.controls[1].icon = ft.Icons.EDIT_OUTLINED

            self.update()

        add_Relevant_characters_button = ft.TextButton(
            ft.Row([
                ft.Text("Relevant Characters", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)), 
                ft.Icon(ft.Icons.EDIT_OUTLINED, self.data.get('color', None))
            ], tight=True),
            tooltip="Add or remove relevant characters for this plot point",
            style=ft.ButtonStyle(text_style=ft.TextStyle(weight=ft.FontWeight.BOLD), mouse_cursor="click", color=self.data.get('color', ft.Colors.PRIMARY)),
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
                for widget in self.widget.story.widgets:
                    if widget.data.get('key', "") == ic_key and widget.data.get('tag', None) == 'character':
                        char = widget
                        break
                if char is not None:
                    name = char.data.get('title', ic_key)


                    # Add the control now
                    controls.append(
                        ft.Row([
                            ft.Text(f"\t\t\t{name}", color=char.data.get('color', None), weight=ft.FontWeight.BOLD),
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
            ft.Text("Notes", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None),),
            ft.IconButton(
                ft.Icons.NEW_LABEL_OUTLINED, self.data.get('color', "primary"),
                tooltip="Add Note",
                on_click=self._new_note_clicked,
                mouse_cursor="click"
            )
        ], spacing=0)

        notes_column = self._build_notes_column()

        content = ft.Column(
            expand=True, tight=True, scroll="auto", alignment=ft.MainAxisAlignment.START, 
            controls=[
                ft.Container(height=1),
                description_tf,
                ft.Row([when_tf, where_tf]),
                
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
        ], expand=True, scroll="none", spacing=0)
        
        self.content = column
        
      
        try:
            self.update()
        except Exception as _:
            pass
