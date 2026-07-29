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
                
                'when': str(),
                'where': str(),
                'relevant_characters': list(),
            })

        self.icon: ft.Icon

    
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
                on_click=self.handle_delete,
                content=ft.Row([
                    ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, ft.Colors.ERROR),
                    ft.Text(f"Delete {self.data.get('title')}", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True),
                ]),
            )
        ]


    def create_sidebar_header_ctrls(self) -> list[ft.Control]:
        ctrls = super().create_sidebar_header_ctrls()

        return ctrls

    
    def create_sidebar_body_ctrls(self) -> list[ft.Control]:
        ''' Rebuilds any parts of our UI and information that may have changed when we update our data '''



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

        return content

    def build(self):
        """ Rebuilds our plotline control that holds our plot point and slider """

        super().build()

        self.mouse_cursor=ft.MouseCursor.CLICK
        self.on_enter = self.highlight
        self.on_exit = self.stop_highlight
        self.on_pan_update=self.move_plot_point 
        self.on_pan_end=self.save_position
        self.on_secondary_tap=lambda: self.widget.story.open_menu(self.get_menu_options())
        self.on_tap=self.show_mini_widget
        self.left = self.data.get('position', (200, 0))[0]
        self.tooltip = self.data.get('title', "Plot Point")
        self.offset = ft.Offset(-0.5, 0)

        self.icon = ft.Icon(icons.get(self.data.get('icon', None), ft.Icons.CIRCLE), self.data.get('color', None))
        
    
        # Our container that is our plot point on the plotline, and contains our gesture detector for hovering and right clicking
        self.content = ft.Container(self.icon, shape=ft.BoxShape.CIRCLE)
        
