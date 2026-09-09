import flet as ft
from models.views.story import Story
from models.widget import Widget
from flet_quill import FletQuill, FletQuillEditor, FletQuillToolbar
from models.app import app
import math
import os
from utils.safe_string_checker import return_safe_name
import asyncio
import uuid
from styles.text_fields import TextField
from styles.snack_bar import SnackBar
from styles.menu_option_style import MenuOptionStyle

MANUSCRIPT_WIDTH = 820
MANUSCRIPT_HEIGHT = 1060
MANUSCRIPT_PADDING = 80
MANUSCRIPT_VERTICAL_MARGIN = 50
MANUSCRIPT_HORIZONTAL_MARGIN = 70


# Class that holds our text manuscript objects
class Manuscript(Widget):
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
                'tag': "manuscript",
                'color': app.settings.data.get('widget_defaults', {}).get('manuscript', {}).get('color'),
                'show_sidebar': True,


                # Holds our comments and reference images in data
                'comments': dict(),
                'reference_images': dict(),

                # The text as json list data that is loaded and saved
                'manuscript_data': list(),       

            })  
            ft.TextStyle()
        self.dirty = False  # Marks if the manuscript has unsaved changes

    class Comment(TextField):

        # Constructor
        def __init__(self, title: str, widget: 'Manuscript', data: dict=None):

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
        def __init__(self, widget: 'Manuscript', data: dict=None):

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
            
    # Checks if our manuscript is dirty, and saves it if it is
    async def save_file(self):
        if self.dirty == True:
            self.dirty = False
            self.update_data(**{'manuscript_data': await self.quill_editor.save()})
        await super().save_file()

    async def export(self, file_type: str="docx"):
        manuscript_data = self.data.get('manuscript_data', [])
        paragraphs = self._parse_manuscript_ops(manuscript_data)

        if file_type == "docx":
            return self._export_docx(paragraphs)
        elif file_type == "pdf":
            return self._export_pdf(paragraphs)
        elif file_type == "txt":
            return self._export_txt(paragraphs)

        return None

    # Splits our quill delta ops (list of {'insert': str, 'attributes': dict}) into paragraphs of styled runs
    def _parse_manuscript_ops(self, ops: list) -> list:
        paragraphs = [[]]
        for op in ops:
            text = op.get('insert', "")
            attributes = op.get('attributes', {}) or {}
            if not isinstance(text, str):
                continue
            segments = text.split('\n')
            for idx, segment in enumerate(segments):
                if segment:
                    paragraphs[-1].append({'text': segment, **attributes})
                if idx < len(segments) - 1:
                    paragraphs.append([])
        if paragraphs and not paragraphs[-1]:
            paragraphs.pop()
        return paragraphs

    # Converts a '#RRGGBB'/'#AARRGGBB' hex color string into an (r, g, b) tuple
    def _hex_to_rgb(self, color: str):
        if not isinstance(color, str) or not color.startswith("#"):
            return None
        hex_value = color.lstrip("#")
        if len(hex_value) == 8:
            hex_value = hex_value[-6:]
        if len(hex_value) != 6:
            return None
        try:
            return tuple(int(hex_value[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            return None

    # Builds a .docx file from our paragraphs, returning the raw file bytes
    def _export_docx(self, paragraphs: list) -> bytes:
        from docx import Document
        from docx.shared import Pt, RGBColor
        from io import BytesIO

        document = Document()
        for runs in paragraphs:
            paragraph = document.add_paragraph()
            for run_data in runs:
                run = paragraph.add_run(run_data.get('text', ""))
                run.bold = bool(run_data.get('bold', False))
                run.italic = bool(run_data.get('italic', False))
                run.underline = bool(run_data.get('underline', False))

                font_size = run_data.get('size')
                if font_size:
                    try:
                        run.font.size = Pt(float(font_size))
                    except (TypeError, ValueError):
                        pass

                font_family = run_data.get('font')
                if font_family:
                    run.font.name = font_family

                rgb = self._hex_to_rgb(run_data.get('color'))
                if rgb:
                    run.font.color.rgb = RGBColor(*rgb)

        buffer = BytesIO()
        document.save(buffer)
        return buffer.getvalue()

    # Joins our paragraphs into plain text, ready to be written to a .txt file
    def _export_txt(self, paragraphs: list) -> str:
        return "\n".join("".join(run.get('text', "") for run in runs) for runs in paragraphs)

    # Rasterizes our paragraphs onto paginated images and packs them into a multi-page .pdf file
    def _export_pdf(self, paragraphs: list) -> bytes:
        from PIL import Image, ImageDraw, ImageFont
        from io import BytesIO

        font_size = 14
        line_height = int(font_size * 1.5)
        usable_width = MANUSCRIPT_WIDTH - MANUSCRIPT_PADDING * 2
        bottom_limit = MANUSCRIPT_HEIGHT - MANUSCRIPT_PADDING

        font_path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "fonts", "OpenSans-VariableFont_wdth,wght.ttf")
        try:
            font = ImageFont.truetype(os.path.normpath(font_path), font_size)
        except OSError:
            font = ImageFont.load_default()

        def new_page():
            page = Image.new("RGB", (MANUSCRIPT_WIDTH, MANUSCRIPT_HEIGHT), "white")
            return page, ImageDraw.Draw(page)

        pages = []
        page, draw = new_page()
        cursor_y = MANUSCRIPT_PADDING

        for runs in paragraphs:
            paragraph_text = "".join(run.get('text', "") for run in runs)
            words = paragraph_text.split(" ") if paragraph_text else [""]
            line = ""
            for word in words:
                candidate = f"{line} {word}".strip()
                if line and draw.textlength(candidate, font=font) > usable_width:
                    if cursor_y + line_height > bottom_limit:
                        pages.append(page)
                        page, draw = new_page()
                        cursor_y = MANUSCRIPT_PADDING
                    draw.text((MANUSCRIPT_PADDING, cursor_y), line, font=font, fill="black")
                    cursor_y += line_height
                    line = word
                else:
                    line = candidate

            if cursor_y + line_height > bottom_limit:
                pages.append(page)
                page, draw = new_page()
                cursor_y = MANUSCRIPT_PADDING
            draw.text((MANUSCRIPT_PADDING, cursor_y), line, font=font, fill="black")
            cursor_y += line_height

        pages.append(page)

        buffer = BytesIO()
        pages[0].save(buffer, format="PDF", save_all=True, append_images=pages[1:])
        return buffer.getvalue()
        
        

    def build(self):

        # Gets our word count and opens a menu to show it
        async def get_word_count():
            word_count = 0
            doc_data = await self.quill_editor.save()
            for block in doc_data:
                if "insert" in block:
                    if isinstance(block["insert"], str):    # Protect against page breaks
                        word_count += len(block["insert"].split())
            self.story.open_menu([ft.Text(f"Word Count: {word_count}", margin=ft.Margin.only(left=6, right=6, top=10, bottom=10))])

        # Mark us dirty after keystroke changes so we can track unsaved changes
        def mark_dirty(e=None):
            if self.dirty == False:
                self.dirty = True


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

        # Word count button
        word_count_button = ft.IconButton(
            icon=ft.CupertinoIcons.TEXTFORMAT_SIZE, #icon_color=ft.Colors.PRIMARY,
            tooltip="Word Count", 
            on_click=get_word_count,
            bgcolor=ft.Colors.TRANSPARENT,
            highlight_color=ft.Colors.TRANSPARENT,
            hover_color=ft.Colors.TRANSPARENT
        )
            
        
        # Grab our flet quill elements
        quill_toolbar = FletQuillToolbar(
            controller_id=self.data.get('id', None),
            expand=True,
            toolbar_buttons=[ft.GestureDetector(word_count_button, on_hover=self.set_mouse_coords, hover_interval=50)]
        )  # Toolbar
        self.quill_editor = FletQuillEditor(    # Editor
            controller_id=self.data.get('id', None),
            text_data=self.data.get('manuscript_data', [{"insert": "Hello World!\n"}]),   # Pass in data
            placeholder_text="Start your masterpiece here...",
            expand=True,
        )

        
        editor_container = ft.Container(
            ft.KeyboardListener(self.quill_editor, on_key_down=mark_dirty),
            expand=True,
            margin=ft.Margin.symmetric(horizontal=MANUSCRIPT_HORIZONTAL_MARGIN, vertical=MANUSCRIPT_VERTICAL_MARGIN),
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

        

        # Set our mouse coords whenever we hover over word count button
        #self.sidebar_header.controls.append(ft.GestureDetector(word_count_button, on_hover=self.set_mouse_coords, hover_interval=50))
        

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
        

        self.content = ft.Column([
            ft.Container(
                quill_toolbar, 
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, 
                alignment=ft.Alignment.CENTER_LEFT, 
                padding=ft.Padding.only(left=4)
            ),
            ft.Divider(2, 2),
            ft.Row([
                ft.Column([editor_container], scroll=ft.ScrollMode.HIDDEN, expand=True),
                self.toggle_sidebar_visibility_button, 
                self.sidebar,
            ], spacing=0, expand=True),
        ], spacing=0, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)