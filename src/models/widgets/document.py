import flet as ft
from models.views.story import Story
from models.widget import Widget
from utils.verify_data import verify_data
from styles.menu_option_style import MenuOptionStyle
#from flet_quill import FletQuill
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
    def __init__(self, title: str, page: ft.Page, directory_path: str, story: Story, data: dict=None, is_rebuilt: bool = False):

        # Check if we're new and need to create file
        is_new = False
        if data is None:
            is_new = True

        # Initialize from our parent class 'Widget'. 
        super().__init__(
            title = title,  
            page = page,  
            directory_path = directory_path,  
            story = story,       
            data = data,  
            is_rebuilt = is_rebuilt  
        )

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            object=self,   # Pass in our own data so the function can see the actual data we loaded
            required_data={
                # Widget data
                'tag': "document",
                'color': app.settings.data.get('default_canvas_color'),
                'mini_widgets_displayed_overtop': False,  

                'show_info': True,   # Whether to show the info column on the side of our charts or not.

                # Comments displayed on the side of the document
                'comments': {           
                    'Summary': dict,      # Default comment for summaries.
                },       
                'reference_images': {},   # Reference images 

                # The text as json list data that is loaded and saved
                'document_data': list,       
            }
        )

        # Saving creates the file if we're new
        if is_new:
            self.p.run_task(self.save_dict)

        # We render our own mini widgets (comments), so we don't need parent class to render them as well
        self.no_render_mini_widgets = True  

        self.comments = {}
        self.reference_images = {}
        self.load_comments()
        self.load_reference_images()

        

        if self.visible:
            self.reload_widget()         # Build our widget if it's visible on init

    # Called when our canvas resizes
    async def _get_size(self, e: ft.LayoutSizeChangeEvent[ft.Container]):
        ''' Updates our w and h variables when sizing canvas resizes '''
        if e.width <= 0 or e.height <= 0:
            print("No size, skipping")
            return 
        self.w = int(e.width)
        self.h = int(e.height)

        if self.skip_update:
            self.skip_update = False
            return
        
        self.skip_update = True
        return

        min_document_height = 1000        # Minimum doument height to maintain readability and usability
        actual_document_height = self.h - 32    # Actual Document height

        # Check we're tall enough
        if actual_document_height < min_document_height:

            # If not, set our height unset aspect ratio, since its used over height
            self.document_container.height = min_document_height
            self.document_container.aspect_ratio = None

            # Only update every other time this is called, or updating re-calls this function
            self.document_container.update()
            self.skip_update = True
                
        else:

            # If we're already tall enough ignore an update
            self.document_container.aspect_ratio = 8.5/11.0
            self.document_container.height = None
            self.document_container.update()
            self.skip_update = True

    def load_comments(self):
        ''' Loads our mini notes from our data into live objects '''
        from models.mini_widgets.comment import Comment

        for title, comment_data in self.data['comments'].items():
            self.comments[title] = Comment(
                title=title, 
                widget=self, 
                page=self.p, 
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
                page=self.p, 
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
            page=self.p,
            key="reference_images",
            data={
                'image': image_str,
                'side_location': side_location
            }
        )
        self.reference_images[title] = reference_image
        self.mini_widgets.append(reference_image)
        self.p.run_task(reference_image.save_dict)
    
    # Will be called when we have a flet quill
    def _save_document(self, text_data: list):
        ''' Saves our document text data to our data dictionary '''
        self.data['document_data'] = text_data
        self.p.run_task(self.save_dict)

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
                await self.save_dict()  # Save to our data
                #await asyncio.sleep(0.2)  # Small delay to ensure data is saved before reloading
                self.reload_widget() # Reload workspace to update the UI with our new image
                    

            except Exception as _:
                pass
                #print(f"Error loading image: {e}")

    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # Rebuild out tab to reflect any changes
        self.reload_tab()


        #quill = FletQuill() # Put inside document container

        # Holds our flet quill
        document_container = ft.Container(
            ft.TextField(hint_text="Temp doc textfield instead of quill for now", expand=True),
            expand=3, margin=ft.Margin.symmetric(vertical=40, horizontal=40),
            border=ft.Border.all(1, ft.Colors.ON_SURFACE_VARIANT),
            border_radius=ft.BorderRadius.all(10),
            alignment=ft.Alignment.TOP_CENTER, padding=ft.Padding.all(72),
            #height=1200,
            #aspect_ratio=8.5/11.0,  # paper-like ratio
        )

        # If we're not showing info, just give us a button to show info and return early
        if not self.data.get('show_info', True):
            print("Not showing info, showing button to show info")

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
            ft.Row([
                ft.Text(
                    f"\tComments", theme_style=ft.TextThemeStyle.TITLE_LARGE, 
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
            ft.Divider()
        ], expand=1, spacing=0, scroll="auto")

        # Add our mini widgets to our info column, with dividers in between
        for idx, mw in enumerate(self.mini_widgets):
            info_column.controls.append(mw)
            if idx != len(self.mini_widgets) - 1:   # Don't add divider after last mini widget
                info_column.controls.append(ft.Divider())
            else:
                info_column.controls.append(ft.Container(expand=True))  # Little padding at the end of the list

        info_container = ft.Container(
            info_column, 
            border=ft.Border.only(left=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            padding=ft.Padding.only(left=11, top=8, bottom=8),
            shadow=ft.BoxShadow(0, 1),
            expand=1,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
        )

        self.body_container.content = IsolatedRow([
            document_container,
            ft.Column([     # Extra column to force vertical expansion
                info_container
            ], scroll="none", expand=True)
        ], expand=True, spacing=0)


        self._render_widget()

        

        

        