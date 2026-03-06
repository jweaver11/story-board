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
                'pin_location': "right" if data is None else data.get('pin_location', "right"),   # Default pin location for notes

                # Note data
                'note_data': {}
            },
        )

        # Saving creates the file if we're new
        if is_new:
            self.p.run_task(self.save_dict)
            print(self.title, " Key while saveing new note: ", self.data.get('key'))

        
        if self.visible:
            self.reload_widget()         # Build our widget if it's visible on init

    async def _add_new_segment(self, e=None):

        async def create_segment(e=None):
            await self.save_segment(new_segment_tf.value, "", True)
            self.p.pop_dialog()

        new_segment_tf = ft.TextField(label="Segment Title", autofocus=True, capitalization=ft.TextCapitalization.WORDS, on_submit=create_segment)

        dlg = ft.AlertDialog(
            title=ft.Text("Add New Note Segment"),
            content=new_segment_tf,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.p.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR)),
                ft.TextButton("Create", on_click=create_segment)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.p.show_dialog(dlg)

    # Saves content when text field is unfocused
    async def save_segment(self, key: str, value: str, should_reload: bool=False):
        self.data['note_data'][key] = value
        await self.save_dict()

        if should_reload:
            self.reload_widget()

    def delete_segment(self, key: str):
        if key in self.data['note_data']:
            del self.data['note_data'][key]
            self.p.run_task(self.save_dict)
            self.reload_widget()

    # Called after any changes happen to the data that need to be reflected in the UI, usually just ones that require a rebuild
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''


        async def _save_segment(e):
            key = e.control.label
            value = e.control.value
            await self.save_segment(key, value)

        # Rebuild out tab to reflect any changes
        self.reload_tab()
        
        # Hold our segment controls when we load the note data
        segments_list = []

        # Go through the note data and load the segments
        for key, value in self.data.get('note_data', {}).items():
            segments_list.append(
                ft.Row([
                    ft.TextField(
                        value, expand=True,
                        multiline=True, label=key, dense=True, capitalization=ft.TextCapitalization.SENTENCES, 
                        on_blur=_save_segment,
                    ),
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR,
                        tooltip=f"Delete segment {key}",
                        on_click=lambda e, k=key: self.delete_segment(k)
                    )
                ])
            )

        add_segment_button = ft.IconButton(
            ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY,
            tooltip="Add New Segment to Note",
            on_click=self._add_new_segment, mouse_cursor="click"
        )
        
        body = ft.Column(
            expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=segments_list + [ft.Row([add_segment_button], alignment=ft.MainAxisAlignment.CENTER)]
        )

        # Assign the body_container content as whatever view you have built in the widget
        self.body_container.content = body
        
        # Build in widget function that will handle loading our mini widgets and rendering the whole thing
        self._render_widget()
        