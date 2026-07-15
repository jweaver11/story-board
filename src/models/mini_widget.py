'''
Mini widgets are high complexity components that sit in the widgets content AND can display their info inside the parent widgets sidebar.
If it cannot do both, its not a mini widget
'''


import flet as ft
from models.widget import Widget
from styles.menu_option_style import MenuOptionStyle
from styles.colors import colors
from styles.text_fields import TextField
import uuid
from constants import PLOTLINE_CANVAS_PADDING

class MiniWidget(ft.GestureDetector):

    # Constructor
    def __init__(
        self, 
        widget: Widget, 
        data: dict = {},
        is_new: bool=False  
    ):

        self.widget = widget        
        # Parent constructor
        super().__init__(
            data=data, 
            animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            on_right_pan_end=lambda: None,  # Needs an event or gets angy
        )

        # If we're new, give default values for our data 
        self.is_new: bool = is_new 

        # Give us default data if we're new. Child class will for a file save
        if self.is_new == True:
            self.data = {
                'id': str(uuid.uuid4()),
                'title': data.get('title', ''),         # Title of the mini widget, should match the object title
                'tag': str(),                           # Default mini widget tag, but should be overwritten by child classes
                'alignment': data.get('alignment', (0, 0)),     # Alignment of the mini widget on its parents stack
                'position': data.get('position', (200, 200)),       # Position of the mini widget on its parents stack
                'color': data.get('color', 'primary'),          # Color of the mini widget
                'notes': [],                            # Notes stored at bottom of info sidebar section
            }

        # State trackers
        self.is_dragging: bool = False              # If we are currently dragging our mini widget
        self.shown_in_sidebar: bool = False     # If we are currently shown on the sidebar and should stay highlighted
        
    # Called every time the mouse moves over our rail
    async def set_mouse_coords(self, e: ft.PointerEvent):
        ''' Stores our mouse positioning so we know where to open menus '''
        self.widget.story.mouse_x = e.global_position.x 
        self.widget.story.mouse_y = e.global_position.y
            
    # Called when deleting our mini widget
    def delete_mini_widget(self):
        ''' Deletes our data from all live widget/mini widget objects that we nest in, and saves the widgets file '''

    # Updates our data then makes sure the widget data for us matches
    def update_data(self, **kwargs):
        
        # Allow Updates our data
        def _merge_data(target: dict, updates: dict):
            for key, value in updates.items():
                current_value = target.get(key)
                if isinstance(current_value, dict) and isinstance(value, dict):
                    _merge_data(current_value, value)
                else:
                    target[key] = value

        # Merge our data then have the widget match
        _merge_data(self.data, kwargs)  
        self.widget.update_data(**{'mini_widgets_data': {self.data.get('id', ''): self.data}})

    # Called every time the mouse moves over our rail
    async def set_mouse_coords(self, e: ft.PointerEvent):
        ''' Stores our mouse positioning so we know where to open menus '''
        self.widget.story.mouse_x = e.global_position.x 
        self.widget.story.mouse_y = e.global_position.y

    def _set_icon(self) -> ft.Icon:
        ''' Returns the icon for this mini widget based on its tag and data '''

        match self.data.get('icon', 'location_pin'):
            case "location_city":
                icon = ft.Icons.LOCATION_CITY
            case "stairs_outlined":
                icon = ft.Icons.STAIRS_OUTLINED
            case "terrain":
                icon = ft.Icons.TERRAIN
            case "forest":
                icon = ft.Icons.FOREST
            case "water":
                icon = ft.Icons.WATER

            case _:
                icon = ft.Icons.LOCATION_PIN

        return icon


    async def _new_note_clicked(self, e=None):
        ''' Called when the new field button is clicked '''



    def _build_notes_column(self) -> ft.Column:
        ''' Builds our column of custom fields for this mini widget '''
        
    
    


    def get_menu_options(self) -> list[ft.Control]:

        # Color, rename, delete
        return [
            MenuOptionStyle(
                on_click=self.handle_rename,
                content=ft.Row([
                    ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, self.data.get('color', 'primary'),),
                    ft.Text(
                        "Rename", 
                        weight=ft.FontWeight.BOLD, 
                    ), 
                ]),
            ),
            MenuOptionStyle(
                ft.SubmenuButton(
                    ft.Row([
                        ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.data.get('color', "primary")), 
                        ft.Text("Color", weight=ft.FontWeight.BOLD, expand=True),
                        ft.Icon(ft.Icons.ARROW_RIGHT),
                    ], expand=True),
                    #self._get_color_options(), 
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    tooltip="Change this widget's color"
                ),
                no_padding=True, no_effects=True
            ),
            MenuOptionStyle(
                #on_click=self._delete_clicked,
                content=ft.Row([
                    ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, ft.Colors.ERROR),
                    ft.Text("Delete", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True),
                ]),
            )
        ]
        

    def handle_rename(self, e: ft.Event=None):
        ''' Replaces our widget title with a text field to rename it '''

        
    # Called when color button is clicked
    def _get_color_options(self) -> list[ft.Control]:
        ''' Returns a list of all available colors for icon changing '''

        # Called when a color option is clicked on popup menu to change icon color
        async def _change_icon_color(e: ft.Event):
            ''' Passes in our kwargs to the widget, and applies the updates '''

            self.update_data(**{'color': e.control.data})
            

        # List for our colors when formatted
        color_controls = [] 

        # Create our controls for our color options
        for color in colors:
            color_controls.append(
                ft.MenuItemButton(
                    content=ft.Text(color.capitalize(), weight=ft.FontWeight.BOLD, color=color),
                    on_click=_change_icon_color, close_on_click=True,
                    data=color,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click")
                )
            )

        return color_controls
    
    # Called when hovering over stacked control to give us a highlighted shadow
    async def highlight(self, e: ft.Event=None):
        ''' Shows our slider and hides our plotline_marker. Makes sure all other sliders are hidden '''
        self.shadow = ft.BoxShadow(2, 2, self.data.get('color', ft.Colors.PRIMARY), blur_style=ft.BlurStyle.OUTER)
        self.update()

    # Called when we stop hovering over our marker
    async def stop_highlight(self, e: ft.Event=None):
        if self.shown_in_sidebar:
            return
        self.shadow = None
        self.update()    

    # Shows our mini widget in the sidebar of our widgets content
    async def show_mini_widget(self, e: ft.Event=None):
        ''' Shows our mini widget '''
        self.shown_in_sidebar = True
        self.widget.sidebar_title.value = self.data.get('title', '')   # Update title to match us
        self.widget.sidebar_body.controls = self.create_sidebar_ctrls()  # Build info sidebar content here
        
        # Applies the update
        self.widget.sidebar.update()
        await self.widget.show_sidebar()

    # Child classes override this
    def create_sidebar_ctrls(self) -> list:
        ''' Creates the controls for the sidebar for this mini widget '''
        return [] 
    
    # Set the content of our mini widget
    def build(self):
        self.left = self.data.get('position', (200, 0))[0]

    
        
# TODO: Have notes label, button, input_tf all standardized