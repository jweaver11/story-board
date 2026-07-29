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
import asyncio
from styles.text_fields import SidebarTitleTextField

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
            animate_position=ft.Animation(250, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            on_right_pan_end=lambda: None,  # Needs an event or gets angy
            drag_interval=20,
        )

        # If we're new, give default values for our data 
        self.is_new: bool = is_new 

        # Give us default data if we're new. Child class will for a file save
        if self.is_new == True:
            self.data = {
                'id': str(uuid.uuid4()),
                'title': data.get('title', ''),         # Title of the mini widget, should match the object title
                'tag': str(),                           # Default mini widget tag, but should be overwritten by child classes
                'position': data.get('position', (200, 200)),       # Position of the mini widget on its parents stack
                'color': data.get('color', '#FFFFFF'),          # Color of the mini widget
                'info': list(),                          # Info stored about this MW. Child classes expand this 
            }

        self.sidebar_title: SidebarTitleTextField    # Title of our miniwidget in the sidebar
        self.icon: ft.Icon      # Some mw's have icons, so we store it here to change its size and color

        # State trackers
        self.is_dragging: bool = False              # If we are currently dragging our mini widget
        #self.shown_in_sidebar: bool = False         # If we are currently shown on the sidebar and should stay highlighted
        
    # Called every time the mouse moves over our rail
    async def set_mouse_coords(self, e: ft.PointerEvent):
        ''' Stores our mouse positioning so we know where to open menus '''
        self.widget.story.mouse_x = e.global_position.x 
        self.widget.story.mouse_y = e.global_position.y

    async def set_icon_size(self, e: ft.Event[ft.MenuItemButton]):
        ''' Sets the size of our icon on the map '''
        await self.widget.story.close_menu()
        self.update_data(**{'icon_size': e.control.data})
        if e.control.data == "Small":
            self.icon.size = 30
        elif e.control.data == "Medium":
            self.icon.size = 65
        elif e.control.data == "Large":
            self.icon.size = 100
        else:
            self.icon.size = 150
        self.update()
        return
            
    # Called by delete buttons to delete ourselves from data. Children deal with the UI
    async def handle_delete(self, e=None):
        await self.widget.story.close_menu()
        self.widget.data['mini_widgets_data'].pop(self.data.get('id', ''))
        self.widget.update_data(**{'mini_widgets_data': self.widget.data.get('mini_widgets_data', {})})

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

    # Saves updated position to our data
    def save_position(self, e: ft.DragEndEvent):
        # Update our data to match our new position
        self.is_dragging = False
        self.position = (self.left, self.top)
        self.update_data(**{'position': self.position})
        self.widget.set_mouse_coords(e)     # Reset the menu position
        self.stop_highlight()

    def get_menu_options(self) -> list[ft.Control]:

        # Color, rename, delete
        return []
        
    
    
    # Called when hovering over our plot point to show the slider
    def highlight(self, e=None):
        if self.content.shadow is None:
            self.content.shadow = ft.BoxShadow(20, 40, ft.Colors.with_opacity(.5, self.data.get('color'))) #if self.plotline_control.shadow is None else None
            self.update()

    # Hides are shadow unless our info display is visible, then stay highlighted
    def stop_highlight(self, e=None):

        # If we're dragging, keep highlighted
        if self.is_dragging:
            return

        # Stay highlighted if we're showing our info display
        if self.widget.visible_mw_id == self.data.get('id', ''):
            return
        if self.content.shadow is not None:
            self.content.shadow = None
            self.update()

    

    # Shows our mini widget in the sidebar of our widgets content
    async def show_mini_widget(self, e=None):
        ''' Shows our mini widget '''

        if self.widget.visible_mw_id == self.data.get('id', ''):
            return      # Already showing, don't need to do anything

        # Build our sidebar header, body, and footer
        self.widget.sidebar_header.controls = self.create_sidebar_header_ctrls()
        self.widget.sidebar_body.controls = self.create_sidebar_body_ctrls() 
        self.widget.sidebar_footer.controls = [self.description_tf]
        self.widget.visible_mw_id = self.data.get('id', '')     # Update ID

        # Update the state of the widget
        if hasattr(self.widget, 'showing_info'):
            self.widget.showing_info = False
         
        # Applies the update
        if not await self.widget.show_sidebar():
            self.widget.sidebar.update()

        self.highlight()    # Highlight our mini widget since we're showing it in the sidebar


    def create_sidebar_header_ctrls(self) -> list:
        ''' Creates the controls for the header of the sidebar for this mini widget '''

        # Re-sets the title value if it was changed in sidebar and not submitted
        def set_title_value():
            self.sidebar_title.value = self.data.get('title', '')
            self.sidebar_title.update()

        # Title that sits in the header
        self.sidebar_title = SidebarTitleTextField(
            value=self.data.get('title', ''),
            on_blur=set_title_value,
            on_submit=self.save_rename
        )

        # Header that is shared by all widgets using the sidebar. Gives them a title, open settings button, and close button
        return [self.sidebar_title]


    # Child classes override this
    def create_sidebar_body_ctrls(self) -> list:
        ''' Creates the controls for the sidebar for this mini widget '''
        

    # Updates our title in sidebar if we're shown in sidebar after a rname
    async def save_rename(self, e: ft.Event[ft.TextField]):
        await self.widget.story.close_menu()
        new_title = e.control.value
        self.update_data(**{'title': new_title})
        if self.widget.visible_mw_id == self.data.get('id'):
            self.sidebar_title.value = new_title
            self.sidebar_title.update()
        
    
    # Set the content of our mini widget
    def build(self):

        # Handles hiding our new info button and focusing our new info textfield
        async def handle_new_info_clicked(e=None):
            new_info_button.visible = False
            new_info_tf.visible = True
            new_info_tf.value = ""
            new_info_button.update()
            new_info_tf.update()
            await new_info_tf.focus()

        # Create a new info in data, then add it to the column
        async def save_new_info(e: ft.Event[ft.TextField]):
            self.data.get('info', []).append({'label': e.control.value, 'value': ''})
            self.update_data(**{'info': self.data.get('info', [])})
            self.sidebar_info_column.controls.append(
                create_new_info_ctrl(
                    info_idx = len(self.data.get('info', [])) - 1,
                    info_data = self.data.get('info', [])[-1]
                )
            )
            self.sidebar_info_column.update()
            await asyncio.sleep(0.05)
            await self.widget.sidebar_body.scroll_to(offset=-1, duration=200)

        # Saves the value of the info
        def save_info_content(e: ft.Event[ft.TextField]):
            info_idx = e.control.data
            if len(self.data.get('info', [])) > info_idx:
                self.data.get('info', [])[info_idx]['value'] = e.control.value
                self.update_data(**{'info': self.data.get('info', [])})
            
        # Returns a textfield of the info control
        def create_new_info_ctrl(info_idx: int, info_data: dict) -> TextField:
            return TextField(
                info_data.get('value', ''), label=info_data.get('label', ''), data=info_idx, expand=True, on_blur=save_info_content, 
                capitalization=ft.TextCapitalization.SENTENCES, multiline=True, dense=True,
                suffix_icon=ft.IconButton(ft.Icons.DELETE_OUTLINED, ft.Colors.ERROR, on_click=delete_info, mouse_cursor=ft.MouseCursor.CLICK)
            )

        # Deletes the info from data and then the column and updates the indices
        def delete_info(e: ft.Event):
            info_idx = e.control.parent.data
            self.data.get('info', []).pop(info_idx)
            self.update_data(**{'info': self.data.get('info', [])})
            self.sidebar_info_column.controls.pop(info_idx)
            self.sidebar_info_column.update()
            update_info_indices()

        def handle_new_info_blur(e=None):
            new_info_button.visible = True
            new_info_tf.visible = False
            new_info_button.update()
            new_info_tf.update()

        # Updates all our info ctrls (textfields) data to be accurate after an index was deleted
        def update_info_indices():
            for idx, ctrl in enumerate(self.sidebar_info_column.controls):
                ctrl.data = idx

        # The label for info with a new info button and textfield
        self.sidebar_info_label = ft.Row([
            ft.Text("Info", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), selectable=True),
            new_info_button := ft.IconButton(
                ft.Icons.NEW_LABEL_OUTLINED, ft.Colors.PRIMARY, 
                tooltip="Add Info",
                on_click=handle_new_info_clicked,
                mouse_cursor="click"
            ),
            new_info_tf := ft.TextField(
                on_submit=save_new_info, visible=False, expand=True,
                on_blur=handle_new_info_blur, margin=ft.Margin.only(left=4),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                border_radius=4, dense=True, capitalization=ft.TextCapitalization.SENTENCES,
                border_color=ft.Colors.TRANSPARENT,
                focused_border_color=ft.Colors.PRIMARY,
                label="New Item Label", label_style=ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=ft.Colors.PRIMARY)
            )
            
        ], spacing=0)

        self.sidebar_info_column = ft.Column(
            [create_new_info_ctrl(idx, value) for idx, value in enumerate(self.data.get('info', []))]
        )

        self.description_tf = ft.TextField(
            value=self.data.get('description', ''), label="Description",
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border_color=ft.Colors.TRANSPARENT,
            margin=ft.Margin.only(top=4),
            focused_border_color=ft.Colors.PRIMARY,
            multiline=True, dense=True, expand=True, 
            on_blur=lambda e: self.update_data(**{'description': e.control.value}),
            capitalization=ft.TextCapitalization.SENTENCES,
            label_style=ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=ft.Colors.PRIMARY) 
        )   