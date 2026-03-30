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

        # Saving creates the file if we're new
        if is_new:
            self.p.run_task(self.save_dict)
        
        if self.visible:
            self.reload_widget()         # Build our widget if it's visible on init

    # Opens a dialog to create a new segment in the note and then saves and reloads
    async def _create_new_segment(self, e=None):

        # Adds our new segment to the bottom of the list
        async def create_segment(e=None):
            self.data['note_data'].append({"title": new_segment_tf.value, "content": ""})
            await self.save_dict()
            self.reload_widget()
            self.p.pop_dialog()

        new_segment_tf = ft.TextField(label="Segment Title", autofocus=True, capitalization=ft.TextCapitalization.WORDS, on_submit=create_segment)

        dlg = ft.AlertDialog(
            title=ft.Text("Add New Note Segment"),
            content=new_segment_tf,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.p.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                ft.TextButton("Create", on_click=create_segment, style=ft.ButtonStyle(mouse_cursor="click"))
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.p.show_dialog(dlg)

    # Saves content when text field is unfocused
    async def _save_segment(self, e):
        index = e.control.data
        if len(self.data['note_data']) > index:
            self.data['note_data'][index]['content'] = e.control.value
            await self.save_dict()

    # Deletes a segment from the note
    async def _delete_segment(self, e):
        index = e.control.data
        if len(self.data['note_data']) > index:
            del self.data['note_data'][index]
            await self.save_dict()
            self.reload_widget()

    # Called after any changes happen to the data that need to be reflected in the UI, usually just ones that require a rebuild
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # Rebuild out tab to reflect any changes
        self.reload_tab()
        
        # Hold our segment controls when we load the note data
        segments_list = []

        # Go through the note data and load the segments
        for idx, segment in enumerate(self.data.get('note_data', [])):
            key = segment.get('title', '')
            value = segment.get('content', '')
            segments_list.append(
                ft.Row([
                    ft.TextField(
                        value, expand=True,
                        multiline=True, label=key, dense=True, capitalization=ft.TextCapitalization.SENTENCES, 
                        on_blur=self._save_segment,
                        data=idx,
                    ),
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR,
                        tooltip=f"Delete segment {key}",
                        on_click=self._delete_segment,
                        mouse_cursor="click", data=idx
                    )
                ])
            )

        add_segment_button = ft.IconButton(
            ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY,
            tooltip="Add New Segment to Note",
            on_click=self._create_new_segment, mouse_cursor="click",
        )
        
        body = ft.Column(
            expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=segments_list + [ft.Row([add_segment_button], alignment=ft.MainAxisAlignment.CENTER)]
        )

        # Assign the body_container content as whatever view you have built in the widget
        self.body_container.content = body
        
        # Build in widget function that will handle loading our mini widgets and rendering the whole thing
        self._render_widget()
        