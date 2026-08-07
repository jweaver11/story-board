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

DOCUMENT_WIDTH = 820
DOCUMENT_HEIGHT = 1060
DOCUMENT_PADDING = 80
DOCUMENT_VERTICAL_MARGIN = 50
DOCUMENT_HORIZONTAL_MARGIN = 70


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
                    'font_family': app.settings.data.get('widget_defaults', {}).get('document', {}).get('text_controller_settings', {}).get('font_family', "Arial"),
                    #'font_size': 12,
                    'weight': "normal",
                    'italic': False,
                    #'decoration': None,
                    # TODO:
                    # size, format_align, font family, letter_spacing, word_spacing, color
                    # decoration, decoration color, decoration thickness, decoration style
                },

                # Holds our comments and reference images in data
                'comments': dict(),
                'reference_images': dict(),

                # The text as json list data that is loaded and saved
                'document_data': list(),       

                # Temp data name when testing new doc data
                'new_doc_data': list(), 
                #[
                # {
                # 'text_style': {
                    # 'bold': False, 
                    # 'italic', False...
                    # }, 
                # 'text': "Hello World!\n"
                # }, ...
                # ],  # Default data for new documents
            })  
            ft.TextStyle()
        self.dirty = False  # Marks if the document has unsaved changes

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
            
    # Checks if our document is dirty, and saves it if it is
    async def save_file(self):
        if self.dirty == True:
            self.dirty = False
            self.update_data(**{'document_data': await self.quill_editor.save()})
        await super().save_file()

    def build(self):


        # Gets our word count and opens a menu to show it
        async def get_word_count():
            word_count = 0
            doc_data = await self.quill_editor.save()
            for block in doc_data:
                if "insert" in block:
                    word_count += len(block["insert"].split())
            self.story.open_menu([MenuOptionStyle(ft.Text(f"Word Count: {word_count}"))])

        # TODO: build editor stuff here
        # Marks ourselves as dirty after any changes to the document
        def mark_dirty(e=None):
            if self.dirty == False:
                self.dirty = True

        # Creates a document with a text control inside that holds our spans and allows for selection and manipulation of text
        def check_size(e: ft.LayoutSizeChangeEvent[ft.Text]):
            
            print("New size:", e.width, e.height)
            if e.height > DOCUMENT_HEIGHT - DOCUMENT_PADDING*2:
                # TODO: See if new page exists below, if so add to it or smth
                pass

        # Handles adding a new comment, hiding the button and showing the textfield for input
        async def new_comment_clicked(e=None):
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
            comments_column.controls.append(new_comment)
            comments_column.update()

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
                    ref_img_column.controls.append(reference_image)
                    ref_img_column.update()
                        
                except Exception as e:
                    e.control.page.show_dialog(SnackBar(f"Error loading image: {str(e)}"))

        super().build() # Parent constructor
            
        
        # Grab our flet quill elements
        quill_toolbar = FletQuillToolbar()  # Toolbar
        self.quill_editor = FletQuillEditor(    # Editor
            text_data=self.data.get('document_data', [{"insert": "Hello World!\n"}]),   # Pass in data
            placeholder_text="Start your masterpiece here...",
            expand=True
        )

        # Holds our flet quill
        editor_container = ft.Container(
            ft.KeyboardListener(self.quill_editor, on_key_down=mark_dirty),
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), 
            border_radius=4,
            width=DOCUMENT_WIDTH, 
            height=DOCUMENT_HEIGHT,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=ft.Padding.all(DOCUMENT_PADDING), 
            align=ft.Alignment.TOP_CENTER,
            alignment=ft.Alignment.TOP_LEFT, 
            margin=ft.Margin.symmetric(horizontal=DOCUMENT_HORIZONTAL_MARGIN, vertical=DOCUMENT_VERTICAL_MARGIN),
        )

        # Build our comments and reference images columns from data
        comments_column = ft.Column(
            [self.Comment(title=comment_data.get('title'), widget=self, data=comment_data) for comment_data in self.data.get('comments', {}).values()], 
            tight=True
        )
        ref_img_column = ft.Column(
            [self.ReferenceImage(widget=self, data=mw_data) for mw_data in self.data.get('reference_images', {}).values()], 
            tight=True
        )

        # Word count button
        word_count_button = ft.IconButton(
            icon=ft.CupertinoIcons.TEXTFORMAT_SIZE, icon_color=ft.Colors.PRIMARY,
            tooltip="Word Count", 
            on_click=get_word_count,
        )

        # Set our mouse coords whenever we hover over word count button
        self.sidebar_header.controls.append(ft.GestureDetector(word_count_button, on_hover=self.set_mouse_coords, hover_interval=50))
        

        # Build the sidebar
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
            
            comments_column, 

            ft.Row([
                ft.Text("Reference Images", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)),
                ft.IconButton(     
                    ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY,
                    on_click=new_ref_image_clicked, 
                    mouse_cursor="click",
                ), 
            ], spacing=0),

            ref_img_column
        ])
        
        
        # TODO:
        # Make sure editor and containers fit correctly like how they did in build_old
        # Re-add build_old functionality that is needed here, mostly for sidebar
        # Use a stack to hold 'pages' (containers with bgcolor and padding) sit...
        # under the quill editor. When quill editor becomes too tall, we 
        # await editor.page_break() to insert its break
        

        self.content = ft.Column([
            ft.Container(quill_toolbar, bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, alignment=ft.Alignment.CENTER_LEFT, padding=ft.Padding.only(left=4)),
            ft.Divider(2, 2),
            ft.Row([
                ft.Container(ft.Column([editor_container], scroll=ft.ScrollMode.HIDDEN), expand=True),
                self.toggle_sidebar_visibility_button, 
                self.sidebar,
            ], spacing=0, expand=True),
        ], spacing=0, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # Called after any changes happen to the data that need to be reflected in the UI
    def build_old(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        
        
        # Marks ourselves as dirty after any changes to the document
        def mark_dirty(e=None):
            if self.dirty == False:
                self.dirty = True
            
        
        # Grab our flet quill elements
        quill_toolbar = FletQuillToolbar()  # Toolbar
        self.quill_editor = FletQuillEditor(    # Editor
            text_data=self.data.get('document_data', [{"insert": "Hello World!\n"}]),   # Pass in data
            placeholder_text="Start your masterpiece here...",
            expand=True
        )

        # Both
        #self.quill = FletQuill(
            #text_data=self.data.get('document_data', [{"insert": "Hello World!\n"}]),
            #expand=True
        #)

        # Holds our flet quill
        editor_container = ft.Container(
            ft.KeyboardListener(self.quill_editor, on_key_down=mark_dirty, expand=True),
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), 
            border_radius=4,
            width=DOCUMENT_WIDTH, height=DOCUMENT_HEIGHT,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=ft.Padding.all(80), 
            align=ft.Alignment.TOP_CENTER,
            alignment=ft.Alignment.TOP_LEFT, 
            margin=ft.Margin.symmetric(horizontal=70, vertical=50),
            #aspect_ratio=8.5/11.0,  # paper-like ratio
        )
        
        

        

        self.content = ft.Column([
            ft.Container(quill_toolbar, bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, alignment=ft.Alignment.CENTER_LEFT, padding=ft.Padding.only(left=4)),
            ft.Divider(2, 2),
            ft.Row([
                ft.Container(ft.Column([editor_container], scroll=ft.ScrollMode.HIDDEN), expand=True),
                self.toggle_sidebar_visibility_button, 
                self.sidebar,
            ], spacing=0, expand=True),
        ], spacing=0, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        

        class TextController(ft.Row):
            def __init__(self, widget: 'Document', data: dict):
                super().__init__(
                    data=data,
                    spacing=0,
                    expand=True,
                    wrap=True,
                )
                self.widget = widget
                
            
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


        super().build() # Parent constructor

        # State managments
        insert_index: int = None    # Where we will insert the new text when typing
        selected_text_indexes: set = None  # Selected letter start and end idxs for manipulating text when we highlight text
        cursor_blink_task: asyncio.Task  # Task to blink our cursor span

        # UI elements
        pages_column: ft.Column = None  # Column that holds our document pages (containers)
        keyboard_listener: ft.KeyboardListener = None  # Keyboard listener for our document pages

        def create_text_cursor() -> ft.TextSpan:
            return ft.TextSpan("|", style=ft.TextStyle(color=ft.Colors.TRANSPARENT, weight=ft.FontWeight.BOLD))

        # Cursor text span we insert into our text control to show where the user is typing.
        text_cursor: ft.TextSpan = create_text_cursor()
        text_cursor_idx: int = None  # Span index of our text cursor

        # Toolbar for controlling text style and other settings. This is a custom widget that we build below.
        text_controller_toolbar: TextController = TextController(widget=self, data=self.data.get('text_controller_settings', {}))

        pages_column = ft.Column([initial_page_ctrl], spacing=0, scroll=ft.ScrollMode.HIDDEN, horizontal_alignment=ft.CrossAxisAlignment.CENTER)


        # Handles adding a new comment, hiding the button and showing the textfield for input
        async def new_comment_clicked(e=None):
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
            comments_column.controls.append(new_comment)
            comments_column.update()

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
                    ref_img_column.controls.append(reference_image)
                    ref_img_column.update()
                        
                except Exception as e:
                    e.control.page.show_dialog(SnackBar(f"Error loading image: {str(e)}"))

        # Gets our word count and opens a menu to show it
        async def get_word_count():
            word_count = 0

            # OLD
            #doc_data = await self.quill_editor.save()
            #for block in doc_data:
                #if "insert" in block:
                    #word_count += len(block["insert"].split())

            doc_data = ""
            # Go through each page and get the text from each span and count the words
            for container in pages_column.controls:
                text_span = container.content
                for span in text_span.spans:
                    doc_data += span.text
            word_count = len(doc_data.split())
            self.story.open_menu([MenuOptionStyle(ft.Text(f"Word Count: {word_count}"))])


        # Creates a document with a text control inside that holds our spans and allows for selection and manipulation of text
        def check_size(e: ft.LayoutSizeChangeEvent[ft.Text]):
            
            print("New size:", e.width, e.height)
            if e.height > DOCUMENT_HEIGHT - DOCUMENT_PADDING*2:
                # TODO: See if new page exists below, if so add to it or smth
                pass

        # Create our text span with passed in text and style
        def create_text_span_ctrl(text: str, text_style: ft.TextStyle=None) -> ft.TextSpan:
            return ft.TextSpan(text=text, style=text_style)

        # Create our text ctrl (1 per page) that holds our spans and allows for selection and manipulation of text
        def create_doc_txt_ctrl(txt_data: list[dict]) -> ft.Text:
            nonlocal text_controller_toolbar, text_cursor

            # Load our spans
            spans = [
                create_text_span_ctrl(
                    text=block.get('text', ""), 
                    text_style=ft.TextStyle(**block.get('text_style', {}))
                ) for block in txt_data
            ]

            # Create empty span if there is not text
            if not spans:
                spans.append(create_text_span_ctrl(text="ABCDEFG", text_style=ft.TextStyle(**text_controller_toolbar.data)))

            spans.append(text_cursor)  # Add our text cursor span to the end of the spans

            # Return the text control
            return ft.Text(
                spans=spans,
                selectable=True, 
                on_selection_change=handle_select_text,
                on_size_change=check_size,
            )
            
        def create_doc_page_ctrl(text_ctrl: ft.Text) -> ft.GestureDetector:

            # Updates mouse cursor for visual feedback when hovering
            def change_mouse_cursor(e: ft.HoverEvent[ft.GestureDetector]):
                if e.local_position.x < DOCUMENT_PADDING or e.local_position.y < DOCUMENT_PADDING or e.local_position.x > DOCUMENT_WIDTH - DOCUMENT_PADDING or e.local_position.y > DOCUMENT_HEIGHT - DOCUMENT_PADDING:
                    e.control.mouse_cursor = None
                else:
                    e.control.mouse_cursor = ft.MouseCursor.CLICK
                e.control.update()

            def handle_taps(e: ft.TapEvent[ft.GestureDetector]):
                # Check we tapped within bounds
                if e.control.mouse_cursor is not None:

                    print("Tapped page")

            return ft.GestureDetector(
                ft.Container(
                    text_ctrl,
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), 
                    border_radius=4,
                    width=DOCUMENT_WIDTH, 
                    height=DOCUMENT_HEIGHT,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    padding=ft.Padding.all(DOCUMENT_PADDING), 
                    align=ft.Alignment.TOP_CENTER,
                    alignment=ft.Alignment.TOP_LEFT, 
                    #margin=ft.Margin.symmetric(horizontal=DOCUMENT_HORIZONTAL_MARGIN, vertical=DOCUMENT_VERTICAL_MARGIN),
                ),
                on_tap=handle_taps,
                on_hover=change_mouse_cursor,
                hover_interval=50,
                width=DOCUMENT_WIDTH, 
                height=DOCUMENT_HEIGHT,
                margin=ft.Margin.symmetric(horizontal=DOCUMENT_HORIZONTAL_MARGIN, vertical=DOCUMENT_VERTICAL_MARGIN),
            )
               
        
        # TODO: Check if doc blank and auto-visible cursor

        
                
        # Re-creates the text cursor and blink task
        def build_text_cursor():
            nonlocal cursor_blink_task, text_cursor
            text_cursor = create_text_cursor()  # Reset the cursor span
            cursor_blink_task = asyncio.create_task(blink_cursor())

        # Removes our text cursor from thep age if its on it and sets it to None
        def remove_text_cursor() -> int | None:
            nonlocal cursor_blink_task, text_cursor
            span_idx = 0
            for page_ctrl in pages_column.controls:
                text_ctrl = page_ctrl.content.content  # Grab the text control we tapped on
                for idx, span in enumerate(text_ctrl.spans):
                    if span == text_cursor:
                        text_ctrl.spans.remove(span)
                        span_idx = idx
                        break   
            if cursor_blink_task:  
                cursor_blink_task.cancel()
            text_cursor = None
            return span_idx  # Return the index of the span we removed so we can insert it back in the same place if needed

        # Temp for manipulating
        def handle_select_text(e: ft.TextSelectionChangeEvent):
            nonlocal insert_index, selected_text_indexes, text_cursor

            # Grab the page index and page ctrl we clicked on
            page_idx = pages_column.controls.index(e.control.parent.parent)    # Grag the page we're on
            page_ctrl = pages_column.controls[page_idx]

            # Start and end idx of each letter in the text
            start_character_idx = e.selection.start
            end_character_idx = e.selection.end


            if start_character_idx != end_character_idx:
                remove_text_cursor()  # Remove the text cursor if its already on the page
                selected_text_indexes = (start_character_idx, end_character_idx)

            # When there was just a tap (start == ends), we unsert our cursor span there
            else:

                # Find our insert index based on where we tapped
                insert_index = start_character_idx  # Set our insert index to where we tapped

                text_ctrl = page_ctrl.content.content  # Grab the text control we tapped on

                # Find the span length of the text control on the page and totla character length of the text control
                span_length = len(text_ctrl.spans) - 1 if text_cursor in text_ctrl.spans else len(text_ctrl.spans)
                character_length = sum(len(span.text) for span in text_ctrl.spans if span != text_cursor)  # Get the total number of characters in the text control
                
                # If at the start, just insert our text_cursor there and skip all logic
                if insert_index == 0:
                    remove_text_cursor()  # Remove the text cursor if its already on the page
                    build_text_cursor()  # Recreates the text cursor, but doesnt add it back to the page yet
                    text_ctrl.spans.insert(0, text_cursor)

                # If inserting at end, just append our text_cursor to the end and skip all logics
                elif insert_index >= character_length:
                    remove_text_cursor()  # Remove the text cursor if its already on the page
                    build_text_cursor()  # Recreates the text cursor, but doesnt add it back to
                    text_ctrl.spans.append(text_cursor)

                # Otherwise we're in the middle, so we have to split a text span
                else:

                    text_cursor_idx = None
                    for page_ctrl in pages_column.controls:
                        text_ctrl = page_ctrl.content.content  # Grab the text control we tapped on
                        for idx, span in enumerate(text_ctrl.spans):
                            if span == text_cursor:
                                text_cursor_idx = idx
                                break
                    text_cursor_char_idx = sum(len(span.text) for span in text_ctrl.spans[:text_cursor_idx]) if text_cursor_idx is not None else 0  # Get the character index of the text cursor if it was on the page

                    # Catch clicking just in front or behind text cursor, and ignore movement
                    if text_cursor_char_idx is not None and insert_index == text_cursor_char_idx or insert_index == text_cursor_char_idx + 1:
                        remove_text_cursor()  # Remove the text cursor if its already on the page
                        build_text_cursor()  # Recreates the text cursor, but doesnt add it back to the page yet
                        text_ctrl.spans.insert(text_cursor_idx, text_cursor)  # Insert the cursor span
                        page_ctrl.update()
                        return
                    
                    
                    # Set a character index to keep track of where in the text control we have checked
                    char_idx = 0 

                    # Go through each span
                    for span_idx, span in enumerate(text_ctrl.spans):

                        span_length = len(span.text)    # Grab this spans length

                        # If our current char_index + this spans length is less than our insert index, skip the span and just add its length
                        if char_idx + span_length < insert_index:
                            char_idx += span_length
                            continue

                        split_idx = insert_index - char_idx  # Find the index to split this span at

                        before_text = span.text[:split_idx]  # Text before the split
                        after_text = span.text[split_idx:]   # Text after the split

                        # Create new spans for before and after
                        before_span = create_text_span_ctrl(text=before_text, text_style=span.style) if before_text else None
                        after_span = create_text_span_ctrl(text=after_text, text_style=span.style) if after_text else None

                        text_ctrl.spans.remove(span)  # Remove the original span
                        # Remove the text cursor
                        remove_text_cursor()
                        build_text_cursor()  # Recreates text cursor, but doesnt add it back to the page yet

                        # Add our before span, cursor span, and after span back to the text control in the correct order
                        if before_span:
                            text_ctrl.spans.insert(span_idx, before_span)  # Insert the before span
                            text_ctrl.spans.insert(span_idx + 1, text_cursor)  # Insert the
                            if after_span:
                                text_ctrl.spans.insert(span_idx + 2, after_span)  # Insert the after span
                            break

                        text_ctrl.spans.insert(span_idx, text_cursor)  # Insert the cursor span if no before span
                        if after_span:
                            text_ctrl.spans.insert(span_idx + 1, after_span)  # Insert the after span
                        break
                page_ctrl.update()
                print("New page spans:", [span.text for span in text_ctrl.spans])
                return

            # No tap, we hide the cursor and let the text highlight. update indexes we need
            
            page_ctrl.update()
            # TODO: Bug where inserting right after text cursor span issue
            # TODO: Update toolbar as well based on selected text

                
            
            
        # Blinks the cursor between invisible and our primary color
        async def blink_cursor():
            while True:
                if text_cursor:
                    if text_cursor.style.color == ft.Colors.TRANSPARENT:
                        text_cursor.style.color = ft.Colors.PRIMARY
                    else:
                        text_cursor.style.color = ft.Colors.TRANSPARENT
                    text_cursor.update()
                await asyncio.sleep(0.7)


        def handle_keystroke(e: ft.KeyboardEvent):
            nonlocal insert_index, selected_text_indexes, text_cursor

            # If we're not focused on the text control, ignore
            if not text_cursor.visible:
                return
            
            # TODO: # Standard keys, arrow keys, delete, copy, cut, paste, etc.
            
            self.needs_file_write = True
            #print(e.key)
            print(e)
            #document_text.spans[-1].text = document_text.spans[-1].text + str(e.key)
            #document_text.update()
            #print("New text:", document_text.spans[-1].text)

        cursor_blink_task = asyncio.create_task(blink_cursor()) 
            
        # Create initial text controls (1), but upon building, they will size and scale out to new pages if needed
        initial_text_ctrl = create_doc_txt_ctrl(self.data.get('new_doc_data', []))
        initial_page_ctrl = create_doc_page_ctrl(initial_text_ctrl)

        # Build our comments and reference images columns from data
        comments_column = ft.Column(
            [self.Comment(title=comment_data.get('title'), widget=self, data=comment_data) for comment_data in self.data.get('comments', {}).values()], 
            tight=True
        )
        ref_img_column = ft.Column(
            [self.ReferenceImage(widget=self, data=mw_data) for mw_data in self.data.get('reference_images', {}).values()], 
            tight=True
        )

        # Word count button
        word_count_button = ft.IconButton(
            icon=ft.CupertinoIcons.TEXTFORMAT_SIZE, icon_color=ft.Colors.PRIMARY,
            tooltip="Word Count", 
            on_click=get_word_count,
        )

        # Set our mouse coords whenever we hover over word count button
        self.sidebar_header.controls.append(ft.GestureDetector(word_count_button, on_hover=self.set_mouse_coords, hover_interval=50))
        
        # Build the sidebar
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
            
            comments_column, 

            ft.Row([
                ft.Text("Reference Images", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)),
                ft.IconButton(     
                    ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY,
                    on_click=new_ref_image_clicked, 
                    mouse_cursor="click",
                ), 
            ], spacing=0),

            ref_img_column
        ])

        # Create the pages column that holds our document pages (containers) and add the keyboard listener to it

        # Create the keyboard listener for handling events inside the pages column
        keyboard_listener = ft.KeyboardListener(
            pages_column, 
            on_key_down=handle_keystroke, # Normal presses
            on_key_repeat=handle_keystroke  # Holding keys
        )

        # Format our content
        self.content = ft.Column([
            ft.Container(text_controller_toolbar, bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, alignment=ft.Alignment.CENTER_LEFT, padding=ft.Padding.only(left=4)),
            ft.Divider(2, 2),
             ft.Row([
                ft.Container(keyboard_listener, expand=True),
                self.toggle_sidebar_visibility_button, 
                self.sidebar,
            ], spacing=0, expand=True),
        ], spacing=0, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        

        
        

