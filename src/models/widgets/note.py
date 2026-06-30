''' Class for the Notes widget. Displays as its own tab for easy access to pinning '''

import flet as ft
from models.views.story import Story
from models.widget import Widget
from utils.verify_data import verify_data
from styles.menu_option_style import MenuOptionStyle
from models.app import app
from utils.safe_string_checker import return_safe_name
    

class Note(Widget):

    # Constructor
    def __init__(self, title: str, page: ft.Page, directory_path: str, story: Story, data: dict = None, is_rebuilt: bool = False):

        # Check if we're new and need to create file
        is_new = False
        if data is None:
            is_new = True

        # Initialize from our parent class 'Widget'. 
        super().__init__(
            title = title,                      # Title of the note
            page = page,                        # Grabs our original page for convenience and consistency
            directory_path = directory_path,    # Path to our notes json file
            story = story,                      # Reference to our story object
            data = data,
            is_rebuilt = is_rebuilt
        )

        # Verifies this object has the required data fields, and creates them if not.
        # If the fields exist already, they will be skipped. Example, loaded notes have the "note" tag, so that would be skipped
        # If you provide default types, it gives it default values, otherwise you can specify values
        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {
                # Widget data
                'key': f"{self.directory_path}\\{return_safe_name(self.title)}_note", 
                'tag': "note",             # Tag to identify what type of object this is
                'color': app.settings.data.get('default_note_color'),
                'pin_location': app.settings.data.get('default_note_pin_location', "right") if data is None else data.get('pin_location', "right"),   # Default pin location for notes

                # Note data - list of segments with title and string
                'note_data': [
                    {"title": "", "content": ""} #{}, ...
                ]
            },
        )
        self.body_container.padding = ft.Padding.only(top=10)

        # Saving creates the file if we're new
        if is_new:
            self.needs_file_write = True
            self.p.run_task(self.save_file)

        if self.visible:
            self.reload_widget()
    

    # Called after any changes happen to the data that need to be reflected in the UI, usually just ones that require a rebuild
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # Column to hold our segments textfields
        segments_column = ft.Column(
            expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            controls=[], scroll="auto",
        )

        
        # Adds our new segment to data and our column
        async def create_segment(e=None):
            self.data['note_data'].append({"title": self.new_segment_tf.value, "content": ""})
            self.update_data(**{'note_data': self.data['note_data']})
            segments_column.controls.append(new_segment_textfield(len(self.data['note_data']) - 1, self.new_segment_tf.value, ""))
            segments_column.update()

        # Deletes a segment from data and our column
        async def delete_segment(e: ft.Event):
            index = e.control.data
            if len(self.data['note_data']) > index:
                del self.data['note_data'][index]
                self.update_data(**{'note_data': self.data['note_data']})
                segments_column.controls.pop(index)
                segments_column.update()

                for i, ctrl in enumerate(segments_column.controls):
                    ctrl.data = i
                    ctrl.suffix_icon.data = i

        # Saves content when text field is unfocused
        async def save_segment(e):
            index = e.control.data
            if len(self.data['note_data']) > index:
                self.data['note_data'][index]['content'] = e.control.value
                self.update_data(**{'note_data': self.data['note_data']})

        # Gives us a new textfield for each note segment
        def new_segment_textfield(idx: int, key: str='', value: str='') -> ft.TextField:
            return ft.TextField(
                value, expand=True, capitalization=ft.TextCapitalization.SENTENCES, 
                multiline=True, label=key, dense=True, 
                on_blur=save_segment, border_color=ft.Colors.OUTLINE_VARIANT,
                data=idx, margin=ft.Margin.symmetric(horizontal=10),
                suffix_icon=ft.IconButton(
                    ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR,
                    tooltip=f"Delete segment {key}",
                    on_click=delete_segment,
                    mouse_cursor="click", data=idx
                )
            )

        # Run any constistant build from parent class, like setting up the tab
        self.reload_tab()

        # Set our padding
        self.padding = ft.Padding.only(left=16, top=16, bottom=16)
        
        

        # Go through the note data and load the segments
        for idx, segment in enumerate(self.data.get('note_data', [])):
            key = segment.get('title', '')
            value = segment.get('content', '')
            segments_column.controls.append(new_segment_textfield(idx, key, value))

        async def _create_new_segment_clicked(e):
            if self.new_segment_tf.visible:
                await create_segment()
                return
            self.new_segment_tf.value = ""
            self.new_segment_tf.visible = True
            self.new_segment_tf.label = "New Segment Label"
            self.new_segment_tf.update() 
            await self.new_segment_tf.focus()

        async def _hide_new_segment_tf(e):
            self.new_segment_tf.visible = False
            self.new_segment_tf.update()

        add_segment_button = ft.Button(
            "Add Segment", ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY,
            tooltip="Add New Segment to Note",
            on_click=_create_new_segment_clicked, 
            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)),
        )

        self.new_segment_tf = ft.TextField(
            label="Add New Segment", dense=True, 
            capitalization=ft.TextCapitalization.WORDS,
            on_blur=_hide_new_segment_tf,
            on_submit=create_segment, visible=False, autofocus=True,
        ) 

        self.body_container.content = ft.Column([
            segments_column, 
            ft.Divider(2, 2),
            ft.Container(ft.Row([add_segment_button, self.new_segment_tf],), bgcolor=ft.Colors.SURFACE_CONTAINER_LOW)
        ], scroll=None, expand=True, spacing=0)

        self._render_widget()

# READY FOR BUILD