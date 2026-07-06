''' Class for the Item widget. Displays as its own tab for easy access to pinning '''

import flet as ft
from models.views.story import Story
from models.widget import Widget
from utils.verify_data import verify_data
from styles.menu_option_style import MenuOptionStyle
from models.app import app
from utils.safe_string_checker import return_safe_name
from styles.text_fields import TextField
    

class Item(Widget):

    # Constructor
    def __init__(self, title: str, directory_path: str, story: Story, data: dict = None, is_new: bool = False):

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
                'tag': "item",             # Tag to identify what type of object this is
                'color': app.settings.data.get('default_item_color'),

                'image_base64': str(), 
                'description': str(),

                # Item data - list of segments with title and string
                'item_data': [
                    {'title': "Type", 'content': ""},
                    {'title': "Rarity", 'content': ""}, 
                    {'title': "Effects", 'content': ""},
                    {'title': "Material", 'content': ""},
                    {'title': "Size", 'content': ""},
                    {'title': "Weight", 'content': ""},
                    {'title': "Lore", 'content': ""},
                    {'title': "Cost", 'content': ""},
                    {'title': "Locations", 'content': ""},
                    {'title': "Count", 'content': ""},
                    {'title': "Notes", 'content': ""},
                ]
            },
        )

    

    # Called when clicking our upload image button
    async def _upload_item_image(self, e=None):

        files = await ft.FilePicker().pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "webp"])
        if files:

            file_path = files[0].path
            try:
                import base64

                with open(file_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    # Save to our data
                    self.update_data(**{'image_base64': f"{encoded_string}"})
                    self.reload_widget()

            except Exception as _:
                pass


    def build(self):

        # Run any constistant build from parent class, like setting up the tab
        self.create_tab()

        self.padding = ft.Padding.all(10)   # Set padding

        # Column to hold our segments textfields
        segments_column = ft.Column(
            expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            controls=[], scroll="auto", alignment=ft.MainAxisAlignment.START
        )

        
        # Adds our new segment to data and our column
        async def create_segment(e=None):
            self.data['item_data'].append({"title": self.new_segment_tf.value, "content": ""})
            self.update_data(**{'item_data': self.data['item_data']})
            segments_column.controls.append(new_segment_textfield(len(self.data['item_data']) - 1, self.new_segment_tf.value, ""))
            segments_column.update()
            self.new_segment_tf.value = ""
            self.new_segment_tf.update()
            add_segment_button.visible = True
            add_segment_button.update()

        # Deletes a segment from data and our column
        async def delete_segment(e: ft.Event):
            index = e.control.data
            if len(self.data['item_data']) > index:
                del self.data['item_data'][index]
                self.update_data(**{'item_data': self.data['item_data']})
                segments_column.controls.pop(index)
                segments_column.update()

                for i, ctrl in enumerate(segments_column.controls):
                    ctrl.data = i
                    ctrl.suffix_icon.data = i

        # Saves content when text field is unfocused
        async def save_segment(e):
            index = e.control.data
            if len(self.data['item_data']) > index:
                self.data['item_data'][index]['content'] = e.control.value
                self.update_data(**{'item_data': self.data['item_data']})

        # Gives us a new textfield for each note segment
        def new_segment_textfield(idx: int, key: str='', value: str='') -> TextField:
            return TextField(
                value, expand=True, capitalization=ft.TextCapitalization.SENTENCES, 
                multiline=True, label=key, dense=True, 
                on_blur=save_segment, 
                data=idx,
                suffix_icon=ft.IconButton(
                    ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR,
                    tooltip=f"Delete segment {key}",
                    on_click=delete_segment,
                    mouse_cursor="click", data=idx
                ),
            )

        # Go through the note data and load the segments
        for idx, segment in enumerate(self.data.get('item_data', [])):
            key = segment.get('title', '')
            value = segment.get('content', '')
            segments_column.controls.append(new_segment_textfield(idx, key, value))

        # Show the textfield to label the new segment
        async def _create_new_segment_clicked(e):
            add_segment_button.visible = False
            add_segment_button.update()
            self.new_segment_tf.value = ""
            self.new_segment_tf.visible = True
            self.new_segment_tf.label = "New Segment Label"
            self.new_segment_tf.update() 
            await self.new_segment_tf.focus()

        # Hide the textfield
        async def _hide_new_segment_tf(e):
            self.new_segment_tf.visible = False
            self.new_segment_tf.update()
            add_segment_button.visible = True
            add_segment_button.update()

        # Button to click to add a new segment
        add_segment_button = ft.Button(
            "New Segment", #ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY,
            tooltip="Add a new segment to your note.", 
            on_click=_create_new_segment_clicked, 
            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, text_style=ft.TextStyle(weight=ft.FontWeight.W_500, size=20)),
        )

        self.new_segment_tf = ft.TextField(
            label="Add New Segment", dense=True, 
            capitalization=ft.TextCapitalization.WORDS,
            on_blur=_hide_new_segment_tf, bgcolor=ft.Colors.SURFACE_CONTAINER,
            on_submit=create_segment, visible=False, autofocus=True,
            
        ) 

        description_section = ft.Column([
            ft.Row([
                ft.Text(f"Description", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=18), color=self.data.get('color', None)),
                
            ], spacing=0),
            ft.TextField(
                self.data.get('description', ""), on_blur=lambda e: self.update_data(**{"description": e.control.value}), expand=True, 
                dense=True, capitalization=ft.TextCapitalization.SENTENCES, multiline=True,
                border_color=ft.Colors.OUTLINE_VARIANT, margin=ft.Margin.only(right=10),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, border=ft.Border.all(2, ft.Colors.OUTLINE_VARIANT), border_radius=10,
                content_padding=ft.Padding.all(6), min_lines=3, cursor_color=self.data.get('color', None)
            )
            
        ], expand=True, spacing=0, alignment=ft.MainAxisAlignment.CENTER)

        body = ft.Column([
            ft.Row([
                self.select_image_button,
                description_section
            ], vertical_alignment=ft.CrossAxisAlignment.START),
            segments_column
        ], expand=True, spacing=0)

        self.content = ft.Stack([
            body,
            
            ft.Column([
                self.new_segment_tf,
                add_segment_button, 
            ], alignment=ft.MainAxisAlignment.END, horizontal_alignment=ft.CrossAxisAlignment.END, expand=True,)
        ], alignment=ft.Alignment.TOP_RIGHT, expand=True)


    def reload_widget(self):
        return
        