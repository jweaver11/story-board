import flet as ft
from models.views.story import Story
from models.widget import Widget
from flet_quill import FletQuill, FletQuillEditor, FletQuillToolbar
from models.app import app
import math
from utils.safe_string_checker import return_safe_name
import asyncio
import uuid
from styles.text_fields import TextField
from styles.snack_bar import SnackBar


# Class that holds our text document objects
class Document(Widget):
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
                'tag': "document",
                'color': app.settings.data.get('widget_defaults', {}).get('document', {}).get('color'),
                'show_sidebar': True,

                # Settings for the toolbar
                'toolbar_settings': {
                    'font_family': "Arial",
                    'font_size': 12,
                    'bold': False,
                    'italic': False,
                    'decoration': None,
                },

                # Holds our comments and reference images in data
                'comments': dict(),

                # The text as json list data that is loaded and saved
                'document_data': list(),       
            }
        )  
        self.dirty: bool = False  # Marks if our document has unsaved changes that need to be written to file
        self.quill_editor: FletQuillEditor  # Will hold our flet quill editor object
        self.comments_column: ft.Column  # Will hold our comments and reference images on the right side of the document

    class Comment(TextField):

        # Constructor
        def __init__(self, title: str, widget: 'Document', data: dict=None):

            self.widget = widget

            # If we're new, give default values for our data 
            if data is None:
                data = {
                    'id': str(uuid.uuid4()),
                    'title': title,
                    'tag': "comment",
                    'content': "",
                }

            # Parent constructor
            super().__init__(
                data=data, 
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                multiline=True, dense=True, expand=True, border_radius=4,
                on_blur=lambda e: self.update_data(**{'content': e.control.value}),
                capitalization=ft.TextCapitalization.SENTENCES,
                suffix_icon=ft.IconButton(ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR, mouse_cursor="click", on_click=self.delete_comment),
                label_style=ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=ft.Colors.PRIMARY)
            ) 

        # Updates our data then the associated dict inside parents 'comments' dict
        def update_data(self, **kwargs):
            self.data.update(kwargs)
            self.widget.update_data(comments={self.data["id"]: self.data})

        # Deletes this comment from parents data and controls
        def delete_comment(self, e=None):
            self.widget.data['comments'].pop(self.data["id"], None)
            self.widget.update_data(**{'comments': self.widget.data.get('comments', {})})
            self.widget.comments_column.controls.remove(self)
            self.widget.comments_column.update()
            

        # Build the comment
        def build(self):
            self.value = self.data.get('content', "")
            self.label = self.data.get('title', "")
            self.label_style = ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=ft.Colors.PRIMARY)
    
    class ReferenceImage(ft.Container):
        def __init__(self, widget: 'Document', data: dict=None):

            self.widget = widget

            # If we're new, give default values for our data 
            if data is None:
                data = {
                    'id': str(uuid.uuid4()),
                    'tag': "reference_image",
                    'image': "",
                }
            
            # Parent constructor
            super().__init__(
                data=data,
                border_radius=10,
                expand=True,
                padding=10,
            ) 

        # Updates our data then the associated dict inside parents 'comments' dict
        def update_data(self, **kwargs):
            self.data.update(kwargs)
            self.widget.update_data(comments={self.data["id"]: self.data})
            
        # Deletes this comment from parents data and controls
        def delete_image(self, e=None):
            self.widget.data['comments'].pop(self.data["id"], None)
            self.widget.update_data(**{'comments': self.widget.data.get('comments', {})})
            self.widget.comments_column.controls.remove(self)
            self.widget.comments_column.update()
            

        # Build the image
        def build(self):

            async def show_delete_icon(e: ft.Event):
                self.content.content.controls[1].opacity = 1
                self.content.update()
            async def hide_delete_icon(e: ft.Event):
                self.content.content.controls[1].opacity = 0
                self.content.update()
            
           # self.image = ft.DecorationImage()
            self.content = ft.GestureDetector(
                ft.Stack([
                    ft.Image(src=self.data['image'], fit=ft.BoxFit.CONTAIN),
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINED, ft.Colors.ERROR, bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, tooltip="Delete reference image?",
                        opacity=0, scale=1.5, on_click=self.delete_image, mouse_cursor="click",
                        animate_opacity=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
                    ),
                ], alignment=ft.Alignment.CENTER),
                on_enter=show_delete_icon,
                on_exit=hide_delete_icon,
            )
            
    # Checks if our document is dirty, and saves it if it is
    async def save_file(self):
        if self.dirty == True:
            self.dirty = False
            self.update_data(**{'document_data': await self.quill_editor.save()})
        await super().save_file()
        

    # Called after any changes happen to the data that need to be reflected in the UI
    def build(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        super().build()

        async def new_mini_widget_clicked(e: ft.Event):
            
            # Get the type of mini widget (comment or reference image)
            mw_type = e.control.data   

            # If reference image, handle that seperately and return
            if mw_type == "reference_image":
                await new_ref_image_clicked(e)
                return
            
            # Otherwise its a comment, so hide our button and show our textfield
            new_mini_widget_button.parent.visible = False
            new_mini_widget_button.parent.update()
            #new_comment_tf_placeholder.visible = False
            #new_comment_tf_placeholder.update()
            new_comment_tf.visible = True
            new_comment_tf.value = ""
            new_comment_tf.data = mw_type
            new_comment_tf.update()
            await new_comment_tf.focus()  

        # Shows our new mini widget button and hides our textfield after creating/blurring comment tf
        async def show_new_mini_widget_button(e: ft.Event):
            new_mini_widget_button.parent.visible = True
            new_mini_widget_button.parent.update()
            new_comment_tf.value = ""
            new_comment_tf.visible = False
            new_comment_tf.update()

        # Creates our new comment in data then adds it to the column
        async def create_comment(e: ft.Event):
            comment_title = e.control.value.strip()
            new_comment = self.Comment(title=comment_title, widget=self)
            self.update_data(**{'comments': {new_comment.data["id"]: new_comment.data}})
            self.comments_column.controls.append(new_comment)
            self.comments_column.update()

            
        # Opens our file picker to imoprt our image
        async def new_ref_image_clicked(e: ft.Event):
            files = await ft.FilePicker().pick_files(allowed_extensions=["jpg", "jpeg", "png", "webp"])
            if files:

                file_path = files[0].path
                try:
                    import base64

                    with open(file_path, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

                    reference_image = self.ReferenceImage(
                        widget=self, 
                        data={
                            'id': str(uuid.uuid4()),
                            'tag': "reference_image",
                            'image': encoded_string,
                        }
                    )
                    self.update_data(**{'comments': {reference_image.data["id"]: reference_image.data}})
                    self.comments_column.controls.append(reference_image)
                    self.comments_column.update()
                        
                except Exception as e:
                    e.page.show_dialog(SnackBar(f"Error loading image: {str(e)}"))



        # Loads our comments and ref images from data into controls to display on right side of document
        def load_comments() -> list:
            mini_widget_controls = []
            for mw_data in self.data.get('comments', {}).values():
                if mw_data['tag'] == "comment":
                    mini_widget_controls.append(self.Comment(title=mw_data.get('title'), widget=self, data=mw_data))
                elif mw_data['tag'] == "reference_image":
                    mini_widget_controls.append(self.ReferenceImage(widget=self, data=mw_data))
            return mini_widget_controls
        
        # Marks ourselves as dirty after any changes to the document
        def mark_dirty(e=None):
            if self.dirty == False:
                self.dirty = True
            
        
        # Toolbar only
        quill_toolbar = FletQuillToolbar(
            #show_toolbar_divider=True,
            #center_toolbar=True,
        )
        # Editor only 
        self.quill_editor = FletQuillEditor(
            text_data=self.data.get('document_data', [{"insert": "Hello World!\n"}]),
            placeholder_text="Start your masterpiece here...",
            expand=True
        )
        # Both
        #self.quill = FletQuill(
            #show_toolbar_divider=True,
            #center_toolbar=False,
            #text_data=self.data.get('document_data', [{"insert": "Hello World!\n"}]),
            #expand=True
        #)

        # Holds our flet quill
        editor_container = ft.Container(
            expand=True, 
            alignment=ft.Alignment.TOP_CENTER, 
            margin=ft.Margin.symmetric(horizontal=40, vertical=20),
            padding=ft.Padding.all(30),
            border_radius=4,
            
            content=ft.Container(
                ft.Column([ft.KeyboardListener(self.quill_editor, on_key_down=mark_dirty, expand=True)], expand=True, scroll=ft.ScrollMode.AUTO),
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), 
                border_radius=4,
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                padding=ft.Padding.all(80), expand=True, 
            ),
            aspect_ratio=8.5/11.0,  # paper-like ratio
        )

            
        
        # Otherwise, build our info column
        self.comments_column = ft.Column(load_comments(), expand=True, scroll=ft.ScrollMode.AUTO)
        
        self.sidebar_body.controls.extend([
            ft.Row([
                
                ft.Text("Comments", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)),
                ft.MenuBar(
                    [
                        new_mini_widget_button := ft.SubmenuButton(
                            ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY),
                            [
                                ft.MenuItemButton(      # Folders
                                    leading=ft.Icon(ft.CupertinoIcons.BUBBLE_RIGHT, ft.Colors.PRIMARY), content="Text", 
                                    data="comment", on_click=new_mini_widget_clicked, close_on_click=True,
                                    tooltip="Create a new folder to organize your story",
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                                ), 
                                ft.MenuItemButton(      # Documents
                                    leading=ft.Icon(ft.Icons.IMAGE_OUTLINED, ft.Colors.PRIMARY), content="Image", 
                                    data="reference_image", on_click=new_mini_widget_clicked, close_on_click=True,
                                    tooltip="Create a new document for text chapters or scenes in your story",
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                                ), 
                            ],
                            menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                            style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
                        ),
                    ],
                    style=ft.MenuStyle(
                        bgcolor="transparent", shadow_color="transparent",
                        shape=ft.RoundedRectangleBorder(radius=4),
                        padding=ft.Padding.all(0)
                    ),
                ),
                new_comment_tf := ft.TextField(
                    label="Comment Title", dense=True, margin=ft.Margin.symmetric(horizontal=6),
                    capitalization=ft.TextCapitalization.WORDS,
                    on_blur=show_new_mini_widget_button, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                    on_submit=create_comment, animate_opacity=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
                    visible=False, autofocus=True, expand=True,
                ),
                    
            ], spacing=0),
            
            self.comments_column, 

            # Testing purposes
            #ft.Text(
                #spans=[
                    #ft.TextSpan("Span 1"),
                    #ft.TextSpan("Span 2")
                #],
                #on_selection_change=lambda e: print(e),
                #selectable=True
            #)
        ])
        

        self.content = ft.Column([
            ft.Container(quill_toolbar, bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, alignment=ft.Alignment.CENTER_LEFT),
            ft.Divider(2, 2),
            ft.Row([
                editor_container,
                self.toggle_sidebar_visibility_button, 
                self.sidebar
            ], spacing=0, expand=True)
        ], spacing=0, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)