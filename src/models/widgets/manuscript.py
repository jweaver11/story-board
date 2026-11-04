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

                # The text as json list data that is loaded and saved
                'manuscript_data': list(),       

            })  
            ft.TextStyle()
        self.dirty = False  # Marks if the manuscript has unsaved changes

    
            
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


        # Set our mouse coords whenever we hover over word count button
        #self.sidebar_header.controls.append(ft.GestureDetector(word_count_button, on_hover=self.set_mouse_coords, hover_interval=50))
        

        # Build the sidebar
        self.sidebar_notes_label.margin = None
        self.sidebar_body.controls.extend([
            self.sidebar_notes_label,
            self.sidebar_notes_column
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