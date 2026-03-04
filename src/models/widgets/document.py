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

# Class that holds our text document objects
class Document(Widget):
    # Constructor
    def __init__(self, title: str, page: ft.Page, directory_path: str, story: Story, data: dict=None, is_rebuilt: bool = False):

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

                # Comments displayed on the side of the document
                'comments': {           
                    'Summary': dict,      # Default comment for summaries.
                },       

                # The text as json list data that is loaded and saved
                'document_data': list,       
            }
        )

        self.comments: dict = {}
        self.load_comments()

        # Hold our comments on left and right side of the document
        self.left_comments = IsolatedColumn([], expand=1, scroll="none", horizontal_alignment=ft.CrossAxisAlignment.END)
        self.right_comments = IsolatedColumn([], expand=1, scroll="none")
        self.document_container = ft.Container(
            ft.TextField(hint_text="Temp doc textfield instead of quill for now", expand=True),
            expand=3, margin=ft.Margin.symmetric(vertical=20),
            border=ft.Border.all(1, ft.Colors.ON_SURFACE_VARIANT),
            border_radius=ft.BorderRadius.all(10),
            alignment=ft.Alignment.TOP_CENTER, padding=ft.Padding.all(72),
            height=1200,
            #aspect_ratio=8.5/11.0,  # paper-like ratio
        )

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
            print("Skipping update")
            self.skip_update = False
            return
        return

        min_document_height = 1000        # Minimum doument height to maintain readability and usability
        actual_document_height = self.h - 32    # Actual Document height

        # Check we're tall enough
        if actual_document_height < min_document_height:

            # If not, set our height unset aspect ratio, since its used over height
            self.document_container.height = min_document_height
            self.document_container.aspect_ratio = None

            # Only update every other time this is called, or updating re-calls this function
            #if not self.skip_update:
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
    

    def submit_comment(self, e):
        title = e.control.value
        self.create_comment(title)
        e.control.value = ""
        self.reload_widget()

    def _save_document(self, text_data: list):
        ''' Saves our document text data to our data dictionary '''
        self.data['document_data'] = text_data
        self.save_dict()


    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # Rebuild out tab to reflect any changes
        self.reload_tab()

        self.left_comments.controls.clear()
        self.right_comments.controls.clear()

        self.left_comments.controls.append(ft.Container(height=10))
        self.right_comments.controls.append(ft.Container(height=10))

        # Add comment buttons go here
        self.left_comments.controls.append(
            ft.IconButton(
                ft.Icons.ADD_COMMENT_OUTLINED,
                self.data.get('color', "primary"),
                tooltip="Create a new comment",
                on_click=self.create_comment_clicked,
                data="left"
            )
        )
        self.right_comments.controls.append(
            ft.IconButton(
                ft.Icons.ADD_COMMENT_OUTLINED,
                self.data.get('color', "primary"),
                tooltip="Create a new comment",
                on_click=lambda e: self.create_comment_clicked(e, "right"),
                flip=ft.Flip(flip_x=True)
            )
        )


        for mw in self.mini_widgets:
            if mw.data.get('side_location', 'left') == 'left':
                self.left_comments.controls.append(mw)
            else:
                self.right_comments.controls.append(mw)







        self.document_container.content = ft.TextField("Quill goes here", expand=True, multiline=True)


        

        # Will hold our comments on left and right side
        doc_row = IsolatedRow([
            self.left_comments,
            self.document_container,
            self.right_comments
        ], expand=True, vertical_alignment=ft.CrossAxisAlignment.START)

        # Column that holds our row with the comments and document for scrolling
        master_column = IsolatedColumn(
            [
                ft.Text("Toolbar goes here"), ft.Divider(height=1, thickness=1), doc_row
            ], 
            scroll="auto", expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0
        )

        self.body_container.content = master_column


        self._render_widget()


        
        # BUILDING BODY - the inside the body container of our widget
        '''
        self.body_container.content = ft.Column(
            expand=True,
            controls=[
                FletQuill(
                    text_data=self.data['document_text'],
                    save_method=self._save_document,
                    #file_path=f"{self.directory_path}/{self.title}_text.json",

                    

                    # OLD
                    #border_visible=True,
                    #border_width=1.0,       # Defaults to 1.0
                    #padding_left=72.0,
                    #padding_top=72.0,
                    #padding_right=72.0,
                    #padding_bottom=72.0,
                    #aspect_ratio=8.5/11.0,  # paper-like ratio

                    show_toolbar_divider=False,  # Show divider below toolbar
                    placeholder_text=f"{self.title} begins here"
                )
            ]
        )
        '''
        

        

        