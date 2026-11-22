''' Class for the WebView, allowing user to connect to external web content '''

import flet as ft
from models.views.story import Story
from models.widget import Widget
from styles.menu_option_style import MenuOptionStyle
from models.app import app
from styles.text_fields import TextField
import asyncio
from models.dataclasses.item_template import default_item_template_data
import flet_webview as fwv
from flet_webview_all import FletWebviewAll


class WebView(Widget):

    # Constructor
    def __init__(self, title: str, directory_path: str, story: Story, data: dict={}, is_new: bool = False):

        # Initialize from our parent class 'Widget'. 
        super().__init__(
            title = title,                      
            directory_path = directory_path,    
            story = story,                     
            data = data,
            is_new = is_new
        )

         # If we're new, give default values for our data 
        if self.is_new == True:
            self.data.update({
                # Widget data
                'tag': "web_view",             # Tag to identify what type of object this is
                'color': app.settings.data.get('widget_defaults', {}).get('web_view', {}).get('color'),

                'url': 'https://www.google.com'
            },
        )

    def build(self):

        @ft.control
        class ControlButton(ft.IconButton):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.style = ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=6),
                )
                

        super().build()
        self.padding = 10
        self.bgcolor = ft.Colors.SURFACE

        async def go_back():
            if wv.can_go_back():
                await wv.go_back()

        async def go_forward():
            if wv.can_go_forward():
                await wv.go_forward()

        def show_loading(e=None):
            progress_bar.visible = True
            progress_bar.update()
        def hide_loading(e=None):
            progress_bar.visible = False
            progress_bar.update()

        async def refresh():
            return

        def bookmark_url():
            # TODO: Store bookmarks for the app, not per wv
            # Give landing page in settings.
            return
            if bookmark in bookmarks:
                return
            self.page.show_dialog()

        # Set the states of the control buttons after an action
        def set_control_buttons():
            return

        async def go_to_url(e: ft.Event[ft.TextField]):
            url = e.control.value
            self.data['url'] = url
            wv.url = url
            wv.update()

        back_button = ControlButton(ft.Icons.ARROW_BACK_OUTLINED, ft.Colors.PRIMARY, on_click=go_back)
        forward_button = ControlButton(ft.Icons.ARROW_FORWARD_OUTLINED, ft.Colors.PRIMARY, on_click=go_forward,)
        refresh_button = ControlButton(ft.Icons.REFRESH_OUTLINED, ft.Colors.PRIMARY, on_click=refresh,)
        bookmark_button = ControlButton(ft.Icons.BOOKMARK_ADD_OUTLINED, ft.Colors.PRIMARY, on_click=bookmark_url, )
        home_button = ControlButton(ft.Icons.HOME_OUTLINED, ft.Colors.PRIMARY, on_click=lambda e: go_to_url(ft.Event(control=search_bar, value="https://www.google.com")))
        set_home_button = ControlButton(ft.Icons.HOME_OUTLINED, ft.Colors.PRIMARY, on_click=lambda e: go_to_url(ft.Event(control=search_bar, value="https://www.google.com")))

        progress_bar = ft.ProgressBar(visible=False)

        
        search_bar = ft.TextField(
            value=self.data.get('url') or "https://www.google.com", 
            expand=True,
            suffix_icon=ft.Row([bookmark_button, set_home_button], spacing=0, tight=True),
            on_submit=go_to_url,
            prefix_icon=home_button,
        )
        
        bookmarks = ft.Row([])

        control_bar = ft.Row(
            spacing=0,
            controls=[
                back_button,
                forward_button,
                refresh_button,
                search_bar
            ],
            
        )

        wv = FletWebviewAll(
            url=self.data.get('url') or "https://www.google.com",
            expand=True,
            javascript_channels=["FletBridge"],
            on_permission_request=lambda e: print(e),
            ad_block_allowed_domains=["example.com"],   # never block here (subdomains too)
            ad_block_blocked_domains=["adserver.somedomain.com",],    # always block
            on_ad_blocked=lambda e: print("blocked", e.url, e.is_main_frame),
            on_page_started=show_loading,
            on_page_finished=hide_loading,
            #on_progress=lambda e: print(f"{e.progress}%"),  # Any updates as its loading (usually 1)
            on_web_resource_error=lambda e: print(e.error_code, e.description),
            on_javascript_message=lambda e: print(e.channel_name, e.message_body),
            debugging_enabled=True, allow_webview_permissions=True,
            ad_block_enabled=False,
        )

        self.content = ft.Column(
            expand=True, spacing=0,
            controls=[
                control_bar,
                bookmarks,
                wv,
                progress_bar
            ],
            
        )

