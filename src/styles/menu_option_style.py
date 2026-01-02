import flet as ft


# Styling for our menu option buttons
class MenuOptionStyle(ft.GestureDetector):

    # Constructor
    def __init__(
        self, 
        content: ft.Control,                # Control displayed as the button
        page: ft.Page = None,              # Page reference
        on_click: callable = None,          # Function called on click
        data = None                         # Any data needed for this option to help with logic
    ):

        self.p = page

        # Parent constructor
        super().__init__(
            expand=True,
            data=data,
            mouse_cursor=ft.MouseCursor.CLICK,
            on_tap=on_click if on_click is not None else lambda e: None,        # Set our on click function
            on_enter=self.on_hover,                                             # Set our hover functions                             
            on_exit=self.on_hover_exit,                                         # Set our stop hovering function
            content=ft.Container(
                #border_radius=ft.border_radius.all(6), 
                padding=ft.padding.symmetric(vertical=2, horizontal=2),
                content=content                                                 # Set our content passed in                                
            ),
        )

    # Called when mouse is hovering over this option
    async def on_hover(self, e: ft.HoverEvent):
        ''' Changes background color to highlight hover '''
        
        self.content.bgcolor = ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE_VARIANT)
        if self.p is not None:
            self.p.update()
            return
        self.content.update()

    # Called when mouse is no longer hovering over this option
    async def on_hover_exit(self, e: ft.HoverEvent):
        ''' Resets background color on hover exit '''
        
        self.content.bgcolor = None
        if self.p is not None:
            self.p.update()
            return
        self.content.update()

   