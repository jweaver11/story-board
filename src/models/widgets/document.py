import flet as ft
from models.views.story import Story
from models.widget import Widget
from utils.verify_data import verify_data
from styles.menu_option_style import MenuOptionStyle
from flet_quill import FletQuill, FletQuillEditor, FletQuillToolbar
from models.app import app
from models.isolated_controls.row import IsolatedRow
from models.isolated_controls.column import IsolatedColumn
import math
from models.mini_widgets.reference_image import ReferenceImage
from utils.safe_string_checker import return_safe_name
import asyncio


# Class that holds our text document objects
class Document(Widget):
    # Constructor
    def __init__(self, title: str, directory_path: str, story: Story, data: dict=None, is_new: bool = False):


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
                'tag': "document",
                'color': app.settings.data.get('default_canvas_color'),
                'mini_widgets_displayed_overtop': False,  

                'show_info': True,   # Whether to show the info column on the side of our charts or not.

                # Holds our comments and reference images in data
                'mini_widgets': [],

                # The text as json list data that is loaded and saved
                'document_data': list,       
            }
        )
      

    def load_comments(self):
        ''' Loads our mini notes from our data into live objects '''
        from models.mini_widgets.comment import Comment

        for title, comment_data in self.data['comments'].items():
            self.comments[title] = Comment(
                title=title, 
                widget=self, 
                key="comments",
                data=comment_data
            )
            self.mini_widgets.append(
                self.comments[title]
            )

    def load_reference_images(self):
        for title, image_data in self.data['reference_images'].items():
            self.reference_images[title] = ReferenceImage(
                title=title, 
                widget=self, 
                key="reference_images",
                data=image_data
            )
            self.mini_widgets.append(
                self.reference_images[title]
            )

    def _create_reference_image(self, title: str, side_location: str, image_str: str):
        reference_image = ReferenceImage(
            title=title,
            widget=self,
            key="reference_images",
            data={
                'image': image_str,
                'side_location': side_location
            }
        )
        self.reference_images[title] = reference_image
        self.mini_widgets.append(reference_image)

    async def _create_reference_image_clicked(self, e):

        side_location = e.control.data  

        files = await ft.FilePicker().pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "webp"])
        if files:

            file_path = files[0].path
            file_name = files[0].name.split(".")[0]
            try:
                import base64

                with open(file_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

                self._create_reference_image(title=file_name, side_location=side_location, image_str=encoded_string)
                
                #await asyncio.sleep(0.2)  # Small delay to ensure data is saved before reloading
                self.reload_widget() # Reload workspace to update the UI with our new image
                    

            except Exception as _:
                pass
                #print(f"Error loading image: {e}")

    class Comment(ft.Container):

        # TODO: Started re-doing documents to use build only!!!!




        ############

        # Constructor
        def __init__(self, title: str, widget: Widget, key: str, data: dict=None):

            # Parent constructor
            super().__init__(data=data) 

            self.key = key
            self.widget = widget
            self.title = title

            # If we're new, give default values for our data 
            if data is None:
                self.data = {
                    'tag': "comment",
                    'content': "",
                    'collapsed': False,
                }

            self.padding = ft.Padding.all(10)

        def build(self):
            async def _show_options_button(e=None):
                options_button.visible = True
                options_button.update()

            async def _hide_options_button(e=None):
                options_button.visible = False
                options_button.update()

            title_control = ft.GestureDetector(
                content=ft.Row([
                    ft.Text(
                        f"{self.data['title']}", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), 
                        color=self.data.get('color', None), weight=ft.FontWeight.BOLD, expand=True,
                    ),
                    options_button := ft.IconButton(
                        icon=ft.Icons.MORE_VERT_ROUNDED,
                        visible=False,
                        on_click=lambda _: self.widget.story.open_menu(self._get_menu_options()),
                        mouse_cursor=ft.MouseCursor.CLICK,
                    ),
                ], height=35),
                #on_double_tap=self._rename_clicked,
                on_secondary_tap=lambda _: self.widget.story.open_menu(self._get_menu_options()),
                on_hover=self._set_menu_coords,
                on_enter=_show_options_button,
                on_exit=_hide_options_button,
                #mouse_cursor="click", 
                hover_interval=100,
            )
                
            


            content_tf = ft.TextField(
                self.data['content'], expand=True, 
                multiline=True, on_blur=lambda e: self.widget.update_data(**{'content': e.control.value}),
                dense=True, capitalization=ft.TextCapitalization.SENTENCES
            )

            self.content = ft.Column(
                tight=True, 
                alignment=ft.MainAxisAlignment.START, #spacing=6,
                controls=[
                    title_control,
                    content_tf,
                ]
            )

    # Called after any changes happen to the data that need to be reflected in the UI
    def build(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        def load_sidebar() -> ft.Column:
            pass

        async def _save_quill():
            ''' Saves our quill data, but marks that it needs to be saved '''
        
            self.data['document_data'] = await quill_editor.save()
            

        # Rebuild out tab to reflect any changes
        self.create_tab()

        quill = FletQuill(
            show_toolbar_divider=False,
            center_toolbar=False,
            text_data=[{"insert": "Hello from the combined control!\n"}],
        )
        
        quill_toolbar = FletQuillToolbar(
            show_toolbar_divider=False,
                center_toolbar=True,
        )
        quill_editor = FletQuillEditor(
            text_data=self.data.get('document_data', [{"insert": "Hello World!\n"}]),
            placeholder_text="Start your masterpiece here...",
        )

        # Holds our flet quill
        document_container = ft.Container(
            expand=3, 
            alignment=ft.Alignment.TOP_CENTER, 
            padding=ft.Padding.all(10),
            content=ft.Column([
                quill_toolbar, 
                ft.Container(
                    ft.KeyboardListener(quill_editor, on_key_down=_save_quill, expand=True),
                    expand=True, 
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), 
                    border_radius=ft.BorderRadius.all(4),
                    padding=ft.Padding.all(20),  
                ),
            ], expand=True, spacing=0),
            #height=1200,
            #aspect_ratio=8.5/11.0,  # paper-like ratio
        )

        # If we're not showing info, just give us a button to show info and return early
        if not self.data.get('show_info', True):

            self.body_container.content = ft.Row(
                [
                    document_container, 
                    ft.IconButton(
                        ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT_ROUNDED, self.data.get('color', ft.Colors.PRIMARY),
                        on_click=self._toggle_show_info, 
                        mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER,
                    )
                ], expand=True, spacing=0
            )
            self._render_widget()
            return      
        
        # Otherwise, build our info column
        info_column = ft.Column([
            
        ], expand=1, spacing=0, scroll="auto")

        # Add our mini widgets to our info column, with dividers in between
        for idx, mw in enumerate(self.mini_widgets):
            info_column.controls.append(mw)
            if idx != len(self.mini_widgets) - 1:   # Don't add divider after last mini widget
                info_column.controls.append(ft.Divider())
            else:
                info_column.controls.append(ft.Container(expand=True))  # Little padding at the end of the list

        

        info_container = ft.Container(
            ft.Column([
                ft.Row([
                    ft.Text(
                        f"\t{self.title}", theme_style=ft.TextThemeStyle.TITLE_LARGE, 
                        color=self.data.get('color', None), weight=ft.FontWeight.BOLD, 
                    ),
                    ft.PopupMenuButton(
                        icon=ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, icon_color=self.data.get('color', "primary"),
                        tooltip="Create new comment or reference image",
                        style=ft.ButtonStyle(mouse_cursor="click"),
                        menu_padding=ft.Padding.all(0),
                        items=[
                            ft.PopupMenuItem(
                                "Comment",
                                ft.Icon(ft.CupertinoIcons.BUBBLE_RIGHT, self.data.get('color', "primary")), 
                                on_click=self.create_comment_clicked,
                                mouse_cursor="click",
                            ),
                            ft.PopupMenuItem(
                                "Reference Image", 
                                ft.Icon(ft.Icons.IMAGE_OUTLINED, self.data.get('color', "primary")), 
                                on_click=self._create_reference_image_clicked,
                                data="left",
                                mouse_cursor="click",
                            ),
                        ],
                    ),
                        
                    ft.Container(expand=True),
                    ft.IconButton(
                        ft.Icons.CLOSE, ft.Colors.ON_SURFACE_VARIANT, on_click=self._toggle_show_info,
                        mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER,
                    ),
                ], spacing=0),
                ft.Divider(),
                info_column, 
            ], expand=True, scroll="none", spacing=0),
            border=ft.Border.only(left=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            padding=ft.Padding.only(left=11, top=8, bottom=8),
            shadow=ft.BoxShadow(0, 1),
            expand=1,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
        )

        self.content = ft.Row([
            document_container,
            ft.Column([     # Extra column to force vertical expansion
                
                info_container
            ], scroll="none", expand=True, spacing=0)
        ], expand=True)


    def reload_widget(self):    # TEMP TO PREVENT ERRORS FROM CALLS
        return

# DONE BUILD
        

        