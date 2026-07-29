import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
import math
from styles.text_styles import text_style
import flet.canvas as cv
from styles.icons import icons
from styles.text_fields import TextField
from constants import PLOTLINE_PADDING, PLOTLINE_WIDTH, PLOTLINE_HEIGHT
from styles.icons import icons
from styles.menu_option_style import MenuOptionStyle

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
                'relevant_characters': list(),
                'icon': "circle",

                # Information for our information display
                'info': [
                    {'label': 'When', 'value': ""},
                    {'label': 'Where', 'value': ""},
                ]
            })

        self.icon: ft.Icon
        self.plotline_description_tf: TextField

    
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

    # Handles deleting our location from the map and data
    async def handle_delete(self, e=None):
       
        await super().handle_delete()   # Delete from data
        # Remove from stack and sidebar if we're showing
        self.widget.plot_point_stack.controls.remove(self)
        self.widget.plot_point_stack.update()
        if self.widget.visible_mw_id == self.data.get('id', ''):
            await self.widget.show_info()
    

    def get_icon_options(self) -> list[ft.Control]:
        ''' Returns a list of all available icons for icon changing '''
        async def change_icon(e: ft.Event[ft.MenuItemButton]):
            await self.widget.story.close_menu()
            self.update_data(**{'icon': e.control.data})
            self.icon.icon = icons.get(e.control.data, ft.Icons.LOCATION_PIN)
            self.update()
            if self.widget.visible_mw_id == self.data.get('id', ''):
                self.widget.sidebar_header.controls = self.create_sidebar_header_ctrls()    # Rebuild our header if we're shown in sidebar
                self.widget.sidebar_header.update()
        return [
            ft.MenuItemButton(
                ft.Icon(icon, self.data.get('color', "primary")),
                on_click=change_icon, close_on_click=True,
                data=icon_str,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click")
            ) for icon_str, icon in icons.items()
        ]


    def get_menu_options(self) -> list[ft.Control]:
        return [
            MenuOptionStyle(
                ft.SubmenuButton(
                    ft.Row([
                        ft.Icon(icons.get(self.data.get('icon'), ft.Icons.CIRCLE), self.data.get('color', "primary")), 
                        ft.Text("Icon", weight=ft.FontWeight.BOLD, expand=True),
                        ft.Icon(ft.Icons.ARROW_RIGHT),
                    ], expand=True),
                    self.get_icon_options(), 
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    tooltip="Change this locations icon on the map"
                ),
                no_padding=True, no_effects=True
            ),
            MenuOptionStyle(
                ft.SubmenuButton(
                    ft.Row([
                        ft.Icon(ft.Icons.PHOTO_SIZE_SELECT_SMALL_OUTLINED, self.data.get('color', "primary")),
                        ft.Text("Icon Size", weight=ft.FontWeight.BOLD, expand=True),
                        ft.Icon(ft.Icons.ARROW_RIGHT),
                    ], expand=True),
                    [
                        ft.MenuItemButton(
                            size, data=size, close_on_click=True,
                            on_click=self.set_icon_size, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click")
                        ) for size in ("Small", "Medium", "Large", "Beefy")
                    ],
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                ),
                no_padding=True, no_effects=True
            ),
            
            MenuOptionStyle(
                on_click=self.handle_delete,
                content=ft.Row([
                    ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, ft.Colors.ERROR),
                    ft.Text(f"Delete {self.data.get('title')}", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True),
                ]),
            )
        ]

    # Make sure to unhighlight any highlighted plot points when we close our mini widget
    async def show_mini_widget(self, e=None):
        
        await super().show_mini_widget(e)
        for pp in self.widget.plot_point_stack.controls:
            if pp.data.get('id', '') != self.data.get('id', ''):
                pp.stop_highlight()
        for arc in self.widget.arc_stack.controls:
            arc.stop_highlight()

    

    def create_sidebar_header_ctrls(self) -> list[ft.Control]:
        ctrls = super().create_sidebar_header_ctrls()
        # TODO: ADjust icon size here too

        return ctrls

    
    def create_sidebar_body_ctrls(self) -> list[ft.Control]:
        ''' Rebuilds any parts of our UI and information that may have changed when we update our data '''

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
                break
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

        self.description_tf.value = self.data.get('description', '')

        content = ft.Column(
            expand=True, tight=True, scroll="auto", alignment=ft.MainAxisAlignment.START, 
            controls=[
                
                
                Relevant_characters_row,        # Holds label, buttons for each Relevant character, and add/remove button
                Relevant_characters_selector,
                ft.Divider(2, 2),
                self.sidebar_info_label,
                self.sidebar_info_column,
     
            ]
        )

        return content

    # Called when hovering over our plot point to show the slider
    def highlight(self, e=None):
        if self.content.controls[0].shadow is None:
            self.content.controls[0].shadow = ft.BoxShadow(20, 40, ft.Colors.with_opacity(.5, self.data.get('color'))) #if self.plotline_control.shadow is None else None
            self.update()

    # Hides are shadow unless our info display is visible, then stay highlighted
    def stop_highlight(self, e=None):

        # If we're dragging, keep highlighted
        if self.is_dragging:
            return

        # Stay highlighted if we're showing our info display
        if self.widget.visible_mw_id == self.data.get('id', ''):
            return
        if self.content.controls[0].shadow is not None:
            self.content.controls[0].shadow = None
            self.update()

    async def set_icon_size(self, e: ft.Event[ft.MenuItemButton]):
        await super().set_icon_size(e)
        self.top = PLOTLINE_HEIGHT / 2 - self.icon.size / 2
        self.update()

    def build(self):
        """ Rebuilds our plotline control that holds our plot point and slider """

        # Update our new description in real time without saving to data
        def update_description(e: ft.Event[ft.TextField]):
            new_description = e.control.value
            if self.widget.visible_mw_id == self.data.get('id', ''):
                self.description_tf.value = new_description
                self.description_tf.update()
            self.plotline_description_tf.value = new_description
            self.plotline_description_tf.update()

        def rename(e: ft.Event[ft.TextField]):
            new_title = e.control.value
            if self.widget.visible_mw_id == self.data.get('id', ''):
                self.sidebar_title.value = new_title
                self.sidebar_title.update()
            self.plotline_title_tf.value = new_title
            self.plotline_title_tf.update()

            
        super().build()

        
        self.left = self.data.get('position', (200, 0))[0]
        
        self.offset = ft.Offset(-0.5, 0)

        # Create our icon with the right color and size
        icon_size_map = {"Small": 30, "Medium": 65, "Large": 100, "Beefy": 150}
        self.icon = ft.Icon(
            icons.get(self.data.get('icon'), ft.Icons.LOCATION_PIN), self.data.get('color', None), expand=False, 
            size=icon_size_map.get(self.data.get('icon_size', 30), 30),
            animate_size=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
        )

        self.top = PLOTLINE_HEIGHT / 2 - self.icon.size / 2

        self.plotline_title_tf = ft.TextField(
            value=self.data.get('title', ''), 
            bgcolor=ft.Colors.TRANSPARENT, 
            text_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD),
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.PRIMARY,
            multiline=False, dense=True, width=150,
            on_blur=lambda e: self.update_data(**{'title': e.control.value}),
            on_change=rename,
            capitalization=ft.TextCapitalization.SENTENCES,
            label_style=ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=ft.Colors.PRIMARY),
            content_padding=ft.Padding.all(0),
            text_align=ft.TextAlign.CENTER
        )

        self.plotline_description_tf = ft.TextField(
            value=self.data.get('description', ''), 
            bgcolor=ft.Colors.TRANSPARENT, 
            text_style=ft.TextStyle(size=10, italic=True),
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.PRIMARY,
            multiline=True, dense=True, width=150,
            on_blur=lambda e: self.update_data(**{'description': e.control.value}),
            capitalization=ft.TextCapitalization.SENTENCES,
            label_style=ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=ft.Colors.PRIMARY),
            on_change = update_description, content_padding=ft.Padding.all(0),
            text_align=ft.TextAlign.CENTER
        )   

        

        self.description_tf.on_change = update_description
        
    
        # Our container that is our plot point on the plotline, and contains our gesture detector for hovering and right clicking
        self.content = ft.Column([
            ft.Container(
                ft.GestureDetector(
                    self.icon, 
                    on_enter=self.highlight, on_exit=self.stop_highlight, 
                    on_pan_update=self.move_plot_point, on_pan_end=self.save_position,
                    on_secondary_tap=lambda: self.widget.story.open_menu(self.get_menu_options()),
                    on_tap=self.show_mini_widget,
                    mouse_cursor=ft.MouseCursor.CLICK
                ),
                shape=ft.BoxShape.CIRCLE, 
            ),
            ft.Container(expand=True, width=1, bgcolor=ft.Colors.ON_SURFACE_VARIANT, height=PLOTLINE_HEIGHT / 8, margin=ft.Margin.only(top=10)),
            self.plotline_title_tf,
            self.plotline_description_tf
        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.START)



        
        
