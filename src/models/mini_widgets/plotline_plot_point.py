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
from models.app import app

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
                'relevant_characters': dict(),  # ids and name to relevant characters. {'id': {'id': "id_val", 'name': "name_val"}...}
                'icon': "circle",
                'color': app.settings.data.get('widget_defaults', {}).get('plotline', {}).get('plot_point_color', "white"),

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

    def save_position(self, e: ft.DragEndEvent):
        super().save_position(e)
        # Refresh event data in the sidebar to match updated drag
        if self.widget.showing_info:
            self.widget.sidebar_body.controls = self.widget.create_sidebar_body_ctrls()
            self.widget.sidebar_body.update()
        

    
    # Create our sidebar body controls
    def create_sidebar_body_ctrls(self) -> list[ft.Control]:
        ''' Rebuilds any parts of our UI and information that may have changed when we update our data '''

        # Create a control for the relevant character in data, with a remove button
        def create_relevant_character_ctrl(char_data: dict) -> ft.Row:

            # Remove the character form data
            def remove_relevant_character(e: ft.Event[ft.IconButton]):
                char_id = e.control.data
                if char_id in self.data.get('relevant_characters', []):
                    self.data.get('relevant_characters', {}).pop(char_id, None)
                    self.update_data(**{'relevant_characters': self.data.get('relevant_characters', [])})
                    other_characters[char_id] = {'id': char_id, 'name': char_data.get('name')}
                relevant_characters_row.controls.remove(e.control.parent.parent)
                relevant_characters_row.update()
                return
    
            return ft.Container(
                ft.Row([
                    ft.Text(char_data.get('name'), weight=ft.FontWeight.BOLD, overflow=ft.TextOverflow.ELLIPSIS),   # Char name
                    ft.IconButton(      # Remove button
                        ft.Icons.CLOSE, ft.Colors.ERROR, tooltip=f"Remove {char_data.get('name')} from relevant characters for this plot point",
                        mouse_cursor=ft.MouseCursor.CLICK,
                        on_click=remove_relevant_character,
                        data=char_data.get('id'), 
                    )
                    ], spacing=0, margin=ft.Margin.only(left=8), tight=True
                ),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH, 
                border_radius=4,
                padding=ft.Padding.only(left=6),
            )
            

        # Pass in the characters you want
        def create_search_bar_ctrls(characters: list[dict]):
            return [
                ft.ListTile(
                    title=ft.Text(char_data.get('name')),
                    data=char_data,
                    on_click=handle_adding_relevant_characters,
                ) for char_data in characters
            ] 

        # Adds the character to data and a control to the column
        async def handle_adding_relevant_characters(e: ft.Event[ft.IconButton]):
            new_char_data = e.control.data
            new_char_id = new_char_data.get('id')
            self.data.get('relevant_characters', {})[new_char_id] = new_char_data
            self.update_data(**{'relevant_characters': self.data.get('relevant_characters', [])})
            relevant_characters_row.controls.append(create_relevant_character_ctrl(new_char_data))
            relevant_characters_row.update()
            await close_search_bar()

        # Handles when we type in search bar to filter our characters list
        async def handle_change(e: ft.Event[ft.SearchBar]):
            nonlocal character_search_bar, other_characters
            query = e.control.value.strip().lower()
            matching = [
                {
                    'id': char_data.get('id'),
                    'name': char_data.get('name') 
                } for char_data in other_characters.values() if char_data.get('name').lower().startswith(query) and char_data.get('id') not in self.data.get('relevant_characters', {})
            ] if query else [
                {
                    'id': char_data.get('id'), 
                    'name': char_data.get('name')
                } for char_data in other_characters.values()
            ]
            character_search_bar.controls = create_search_bar_ctrls(matching)
            character_search_bar.update()

        # Opens search bar and populates correct controls
        async def open_search_bar(e=None):
            character_search_bar.controls = create_search_bar_ctrls([char_data for char_data in other_characters.values() if char_data.get('id') not in self.data.get('relevant_characters', {})])
            character_search_bar.update()
            await character_search_bar.open_view()

        # Reset the value of the search bar
        def reset_search_bar(e=None):
            character_search_bar.value = ""
            character_search_bar.update()

        # When closing search bar, reset it and close the view
        async def close_search_bar(e=None):
            reset_search_bar()
            await character_search_bar.close_view()

        # All other characters in our story that are not relevant to this plot point, so we can add them
        other_characters = {
            widget.data.get('id'): {
                'id': widget.data.get('id'), 
                'name': widget.data.get('title')
            } for widget in self.widget.story.widgets.values() if widget.data.get('tag') == 'character' and widget.data.get('id') not in self.data.get('relevant_characters', {})
        }        

        # Build UI to display all relevant characters in our data
        relevant_characters_row = ft.Row(
            [create_relevant_character_ctrl(char_data) for char_data in self.data.get('relevant_characters', {}).values()],
            wrap=True, margin=ft.Margin.only(bottom=10)
        )

        # Search bar for adding relevant characters
        character_search_bar = ft.SearchBar(
            value="", view_elevation=4,
            controls=create_search_bar_ctrls([char_data for char_data in other_characters.values() if char_data.get('id') not in self.data.get('relevant_characters', {})]), 
            bar_padding=ft.Padding.only(left=6, right=6),
            divider_color=ft.Colors.PRIMARY,
            bar_bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            bar_hint_text="Search character names here",
            bar_shape=ft.RoundedRectangleBorder(radius=4),
            view_shape=ft.RoundedRectangleBorder(radius=4),
            bar_size_constraints=ft.BoxConstraints(min_height=40, max_height=50, max_width=400),
            on_tap=open_search_bar,
            on_tap_outside_bar=close_search_bar,
            on_change=handle_change,
            on_blur=reset_search_bar,
            capitalization=ft.TextCapitalization.WORDS,
        )

        return [
                
            ft.Text(f"Relevant Characters", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), selectable=True, margin=ft.Margin.only(bottom=4)), 

            relevant_characters_row,
            character_search_bar,

            self.sidebar_info_label,
            self.sidebar_info_column,
    
            ]
        

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

    def update_rename(self, e: ft.Event[ft.TextField]):
        new_title = e.control.value
        # Update title in sidebar if we're showing our info
        if self.widget.visible_mw_id == self.data.get('id', ''):
            self.sidebar_title.value = new_title
            self.sidebar_title.update()
        # Update our event title in the sidebar if plotline is showing info
        elif self.widget.showing_info:
            for ctrl in self.widget.events_column.controls:
                if ctrl.data == self.data.get('id', ''):
                    ctrl.controls[0].value = new_title
                    ctrl.controls[0].update()
                    break
        self.plotline_title_tf.value = new_title
        self.plotline_title_tf.update()

    def build(self):
        """ Rebuilds our plotline control that holds our plot point and slider """

        # Update our new description in real time without saving to data
        def update_description(e: ft.Event[ft.TextField]):
            new_description = e.control.value
            # Update description in sidebar if we're showing our info
            if self.widget.visible_mw_id == self.data.get('id', ''):
                self.description_tf.value = new_description
                self.description_tf.update()
            # Update our event title in the sidebar if plotline is showing info
            elif self.widget.showing_info:
                for ctrl in self.widget.events_column.controls:
                    if ctrl.data == self.data.get('id', ''):
                        ctrl.controls[1].value = new_description
                        ctrl.controls[1].update()
                        break
            # Make sure our description on the stack matches if our sidebar description was updated
            self.plotline_description_tf.value = new_description
            self.plotline_description_tf.update()

        
            

            
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
            on_blur=self.save_rename,
            on_change=self.update_rename,
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
            on_blur=self.save_description,
            capitalization=ft.TextCapitalization.SENTENCES,
            label_style=ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=ft.Colors.PRIMARY),
            on_change=update_description, content_padding=ft.Padding.all(0),
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



        
        
