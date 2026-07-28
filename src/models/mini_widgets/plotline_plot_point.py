import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
import math
from styles.text_styles import text_style
import flet.canvas as cv
from styles.icons import icons
from styles.text_fields import TextField
from constants import PLOTLINE_PADDING, PLOTLINE_WIDTH, PLOTLINE_HEIGHT

# Plotpoint mini widget object that appear on plotlines and arcs
class PlotlinePlotPoint(MiniWidget):

    def __init__(
        self, 
        widget: Widget, 
        data: dict = {},
        is_new: bool=False
    ):

        # Parent constructor
        super().__init__(widget=widget, data=data, is_new=is_new) 

        # If we're new, give default values for our data 
        if self.is_new:
            self.data.update({ 
                'tag': "plot_point",            # Tag to identify what type of object this is
                
                'when': str(),
                'where': str(),
                'relevant_characters': list(),
            })

    
    async def move_plot_point(self, e: ft.DragUpdateEvent):
        ''' Changes our x position on the slider, and saves it to our data dictionary, but not to our file yet '''

        # Calculate new left and clamp. Apply updates
        new_left = self.left + e.local_delta.x
        if new_left < PLOTLINE_PADDING:       
            new_left = PLOTLINE_PADDING
        elif new_left > PLOTLINE_WIDTH - PLOTLINE_PADDING: 
            new_left = PLOTLINE_WIDTH - PLOTLINE_PADDING
        self.left = new_left
        self.update()

    # Called when hovering over our plot point to show the slider
    async def highlight(self, e=None):
        ''' Shows our slider and hides our plotline_marker. Makes sure all other sliders are hidden '''

        # Gives us a focused shadow
        self.shadow = ft.BoxShadow(5, 10, ft.Colors.with_opacity(.6, self.data.get('color'))) #if self.plotline_control.shadow is None else None
        self.update()

    # Hides are shadow unless our info display is visible, then stay highlighted
    async def stop_highlight(self, e=None):

        # If we're dragging, keep highlighted
        if self.is_dragging:
            return

        # If our info display is visible, keep highlighted
        if not self.visible:
            self.shadow = None
            self.update()

    def _get_icon_options(self) -> list[ft.Control]:
        ''' Returns a list of all available icons for icon changing '''

        # Called when an icon option is clicked on popup menu to change icon
        async def _change_icon(e: ft.Event[ft.MenuItemButton]):
            ''' Passes in our kwargs to the widget, and applies the updates '''

            # Set our data and update our button icon
            self.update_data(**{'icon': e.control.data})

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

 
    def build(self):
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
                on_enter=self.highlight, on_exit=self.stop_highlight, on_pan_start=self.drag_start,
                on_pan_update=self.move_plot_point, drag_interval=20, on_pan_end=self.drag_end,
                on_secondary_tap=lambda _: self.widget.story.open_menu(self._get_menu_options()),
                on_tap=self.show_mini_widget, on_tap_down=self.drag_start,
                content=ft.Icon(ft.Icons.CIRCLE, self.data.get('color', None))
            ),
        )


    
    def create_sidebar_body_ctrls(self):
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
                on_click=self.widget.hide_sidebar,
                mouse_cursor="click"
            ),
        ], spacing=0)



        when_tf = TextField(
            value=self.data.get('When', ''), multiline=True, expand=True, 
            on_blur=lambda e: self.update_data(**{'When': e.control.value}), 
            label="When", capitalization=ft.TextCapitalization.SENTENCES,
            dense=True
        )

        where_tf = TextField(
            value=self.data.get('Where'), multiline=True, expand=True, 
            on_blur=lambda e: self.update_data(**{'Where': e.control.value}), 
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

            self.update_data(**{'Relevant Characters': self.data.get('Relevant Characters', [])})

            Relevant_characters_row.controls = _set_Relevant_characters_controls()
            Relevant_characters_selector.controls = _get_Relevant_characters()
            self.update()

        # Called to check our list of characters Relevant on this plotpoint. They are stored as keys and returned as names for display
        def _get_Relevant_characters() -> list[str]:
            char_list = []
            
            for widget in self.widget.story.widgets.values():
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
            char = None
            for idx, ic_key in enumerate(self.data.get('Relevant Characters', [])):
                for widget in self.widget.story.widgets.values():
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

        content = ft.Column(
            expand=True, tight=True, scroll="auto", alignment=ft.MainAxisAlignment.START, 
            controls=[
                ft.Container(height=1),
                
                ft.Row([when_tf, where_tf]),
                
                Relevant_characters_row,        # Holds label, buttons for each Relevant character, and add/remove button
                Relevant_characters_selector,
                ft.Divider(2, 2),
     
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
