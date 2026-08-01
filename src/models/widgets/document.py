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
from styles.menu_option_style import MenuOptionStyle


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
                'text_controller_settings': {
                    'font_family': "Arial",
                    'font_size': 12,
                    'bold': False,
                    'italic': False,
                    'decoration': None,
                    # TODO:
                    # size, format_align, font family, letter_spacing, word_spacing, color
                    # decoration, decoration color, decoration thickness, decoration style
                },

                # Holds our comments and reference images in data
                'comments': dict(),
                'reference_images': dict(),

                # The text as json list data that is loaded and saved
                'document_data': list(),       

                'new_doc_data': list(), 
                #[
                # {
                # 'style': {
                    # 'bold': False, 
                    # 'italic', False...
                    # }, 
                # 'text': "Hello World!\n"
                # }, ...
                # ],  # Default data for new documents
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
            self.widget.update_data(reference_images={self.data["id"]: self.data})
            
        # Deletes this comment from parents data and controls
        def delete_image(self, e=None):
            self.widget.data['reference_images'].pop(self.data["id"], None)
            self.widget.update_data(**{'reference_images': self.widget.data.get('reference_images', {})})
            self.widget.ref_img_column.controls.remove(self)
            self.widget.ref_img_column.update()
            

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


    class TextController(ft.Row):
        def __init__(self, widget, *args, **kwargs):
            super().__init__(*args, **kwargs)
            #self.alignment = ft.MainAxisAlignment.CENTER
            #self.data = app.settings.data.get('text_controller_settings', {})
            self.widget = widget
            self.expand = True
            self.spacing = 0

        def build(self):

            # Sets dropdowns on UI changes and updates the correct data
            def set_dropdowns(e: ft.Event[ft.Dropdown]):
                pass

            # Sets buttons on UI changes and updates the correct data
            def set_buttons(e: ft.Event[ft.IconButton]):
                setting = e.control.data
                new_value = not self.data.get(setting, False)
                self.data[setting] = new_value
                if new_value == True:
                    e.control.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
                    e.control.icon_color = ft.Colors.PRIMARY
                else:
                    e.control.bgcolor = ft.Colors.TRANSPARENT
                    e.control.icon_color = ft.Colors.ON_SURFACE_VARIANT
                e.control.update()
                self.widget.update_data(**{'text_controller_settings': self.data})


            self.controls = [   

                #ft.Text("Text Controller", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE_VARIANT, size=14, italic=True, opacity=.5),

                ft.IconButton(
                    ft.Icons.FORMAT_BOLD,
                    ft.Colors.PRIMARY if self.data.get('bold', False) else ft.Colors.ON_SURFACE_VARIANT,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH if self.data.get('bold', False) else ft.Colors.TRANSPARENT,
                    data="bold", on_click=set_buttons,
                    #visible=False,  # TEMP
                ),
                ft.IconButton(
                    ft.Icons.FORMAT_ITALIC,
                    ft.Colors.PRIMARY if self.data.get('italic', False) else ft.Colors.ON_SURFACE_VARIANT,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH if self.data.get('italic', False) else ft.Colors.TRANSPARENT,
                    data="italic", on_click=set_buttons,
                    #visible=False,  # TEMP
                ),

                # TODO: Text Controller
                # size, format_align, font family, letter_spacing, word_spacing, color
                # decoration, decoration color, decoration thickness, decoration style
            ]
    
            
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

        async def new_comment_clicked(e=None):
            
            # Otherwise its a comment, so hide our button and show our textfield
            new_comment_button.visible = False
            new_comment_button.update()
            new_comment_tf.visible = True
            new_comment_tf.value = ""
            new_comment_tf.update()
            await new_comment_tf.focus()  

        # Shows our new mini widget button and hides our textfield after creating/blurring comment tf
        def show_new_comment_button(e=None):
            new_comment_button.visible = True
            new_comment_button.update()
            new_comment_tf.value = ""
            new_comment_tf.visible = False
            new_comment_tf.update()

        # Creates our new comment in data then adds it to the column
        def create_comment(e: ft.Event[ft.TextField]):
            comment_title = e.control.value.strip()
            new_comment = self.Comment(title=comment_title, widget=self)
            self.update_data(**{'comments': {new_comment.data["id"]: new_comment.data}})
            self.comments_column.controls.append(new_comment)
            self.comments_column.update()

            
        # Opens our file picker to imoprt our image
        async def new_ref_image_clicked(e: ft.Event[ft.IconButton]):
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
                    self.update_data(**{'reference_images': {reference_image.data["id"]: reference_image.data}})
                    self.ref_img_column.controls.append(reference_image)
                    self.ref_img_column.update()
                        
                except Exception as e:
                    e.control.page.show_dialog(SnackBar(f"Error loading image: {str(e)}"))

        # Gets our word count 
        async def get_word_count() -> list[MenuOptionStyle]:
            word_count = 0
            doc_data = await self.quill_editor.save()
            for block in doc_data:
                if "insert" in block:
                    word_count += len(block["insert"].split())
            self.story.open_menu([MenuOptionStyle(ft.Text(f"Word Count: {word_count}"))])
        
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
            ft.Column([ft.KeyboardListener(self.quill_editor, on_key_down=mark_dirty, expand=True)], expand=True, scroll=ft.ScrollMode.AUTO),
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), 
            border_radius=4,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=ft.Padding.all(80), 
            expand=True, 
            alignment=ft.Alignment.TOP_LEFT, 
            margin=ft.Margin.symmetric(horizontal=70, vertical=50),
            aspect_ratio=8.5/11.0,  # paper-like ratio
        )
        

            
        
        # Otherwise, build our info column
        self.comments_column = ft.Column(
            [self.Comment(title=comment_data.get('title'), widget=self, data=comment_data) for comment_data in self.data.get('comments', {}).values()], 
            tight=True
        )
        self.ref_img_column = ft.Column(
            [self.ReferenceImage(widget=self, data=mw_data) for mw_data in self.data.get('reference_images', {}).values()], 
            tight=True
        )


        # Word count button
        word_count_button = ft.IconButton(
            icon=ft.CupertinoIcons.TEXTFORMAT_SIZE, icon_color=ft.Colors.PRIMARY,
            tooltip="Word Count", 
            on_click=get_word_count,
        )
        self.sidebar_header.controls.append(ft.GestureDetector(word_count_button, on_hover=self.set_mouse_coords, hover_interval=50))
        
        
        self.sidebar_body.controls.extend([
            ft.Row([
                
                ft.Text("Comments", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)),
                new_comment_button := ft.IconButton(     
                    ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY,
                    on_click=new_comment_clicked, 
                    mouse_cursor="click",
                ), 
                new_comment_tf := ft.TextField(
                    label="Comment Title", dense=True, margin=ft.Margin.symmetric(horizontal=6),
                    capitalization=ft.TextCapitalization.WORDS,
                    on_blur=show_new_comment_button, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                    on_submit=create_comment, animate_opacity=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
                    visible=False, autofocus=True, expand=True,
                ),
                    
            ], spacing=0),
            
            self.comments_column, 

            ft.Row([
                ft.Text("Reference Images", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)),
                ft.IconButton(     
                    ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY,
                    on_click=new_ref_image_clicked, 
                    mouse_cursor="click",
                ), 
            ], spacing=0),

            self.ref_img_column
        ])

        self.content = ft.Column([
            ft.Container(quill_toolbar, bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, alignment=ft.Alignment.CENTER_LEFT),
            ft.Divider(2, 2),
            ft.Row([
                editor_container,
                self.toggle_sidebar_visibility_button, 
                self.sidebar
            ], spacing=0, expand=True),
        ], spacing=0, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)


        '''

        # New testing stuff -------------------------------------------------------------------------
        def remove_cursor_span():
            if cursor_span in self.document_text.spans:
                self.cursor_blink_task.cancel()
                self.document_text.spans.remove(cursor_span)
                self.document_text.update()

        def add_cursor_span(span_idx: int):
            # The index to insert the span and restart our task
            return
            self.cursor_blink_task = asyncio.create_task(blink_cursor())

        # Temp for manipulating
        def handle_select_text(e: ft.TextSelectionChangeEvent):

            # Also check if selecting cursor and ignore that

            # Start and end idx of each letter in the text
            start_idx = e.selection.start
            end_idx = e.selection.end
            selected_length = end_idx - start_idx
            print(e.selected_text, "\n", e)

            # When there was just a tap, we insert the cursor span at the 
            if start_idx == end_idx:

                remove_cursor_span()

                

                span_lengths = [len(span.text) for span in self.document_text.spans if span is not cursor_span]

                # add_cursor_span(span_idx)
                # Calculate new idx for spans adding here and do it
                # Add it here

                return
            # Highlighted something, so remove the cursor
            remove_cursor_span()

            print(start_idx, end_idx)

            # Find included spans here based in index and length of highlighted text



        async def blink_cursor():
            while True:
                await asyncio.sleep(0.75)
                if cursor_span is not None:
                    if cursor_span.style.color == ft.Colors.TRANSPARENT:
                        cursor_span.style.color = ft.Colors.PRIMARY
                    else:
                        cursor_span.style.color = ft.Colors.TRANSPARENT
                    cursor_span.update()


        def handle_keystroke(e: ft.KeyboardEvent):
            # Mark us dirty
            if self.dirty == False:
                self.dirty = True
            # Standard keys, arrow keys, delete, paste, etc.
        

        self.cursor_blink_task: asyncio.Task = None
        self.cursor_blink_task = asyncio.create_task(blink_cursor())
        self.selected_text: set = set()  # Selected letter start and end idxs for manipulating text

        self.active_span: ft.TextSpan = ft.TextSpan()   # Active span to manipulate text
        cursor_span = ft.TextSpan(
            "|",
            style=ft.TextStyle(color=ft.Colors.PRIMARY, weight=ft.FontWeight.BOLD)
        )

        text_controller = self.TextController(self, data=self.data.get('text_controller_settings', {}))

        self.document_text = ft.Text(   # Text control to hold our spans
            spans=[ft.TextSpan("Temp for testing\n"), ft.TextSpan("Even more text"), cursor_span,],
            on_selection_change=handle_select_text, selectable=True, expand=True, expand_loose=True,
        )      
        
        
        editor_container =ft.Container(
            ft.Column([ft.KeyboardListener(self.document_text, on_key_down=handle_keystroke, expand=True)], expand=True, scroll=ft.ScrollMode.AUTO),
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), 
            border_radius=4,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=ft.Padding.all(80), 
            expand=True, alignment=ft.Alignment.TOP_LEFT, 
            margin=ft.Margin.symmetric(horizontal=70, vertical=50),
            #aspect_ratio=8.5/11.0,  # paper-like ratio
        )
        

        self.content = ft.Column([
            ft.Container(text_controller, bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, alignment=ft.Alignment.CENTER_LEFT),
            ft.Divider(2, 2),
            ft.Row([
                editor_container,
                self.toggle_sidebar_visibility_button, 
                self.sidebar
            ], spacing=0, expand=True),
        ], spacing=0, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        # TODO New cursor solution, since the one currently sux

        
        '''

