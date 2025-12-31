import flet as ft
from models.views.story import Story
from models.widget import Widget
from handlers.verify_data import verify_data
from styles.menu_option_style import Menu_Option_Style
from flet_quill import FletQuill


# Class that holds our text chapter objects
class Chapter(Widget):
    # Constructor
    def __init__(self, title: str, page: ft.Page, directory_path: str, story: Story, data: dict=None):

        # Initialize from our parent class 'Widget'. 
        super().__init__(
            title = title,  
            page = page,  
            directory_path = directory_path,  
            story = story,       
            data = data,    
        )

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            object=self,   # Pass in our own data so the function can see the actual data we loaded
            required_data={
                'tag': "chapter",
                'summary': str,     # Summary of what will happen in the chapter
                'content': str,
                'temp': str,
                'test': str,
                'comments': dict,
            }
        )

        self.mini_notes = {}
        self.load_mini_notes()

        # Load our widget UI on start after we have loaded our data
        self.reload_widget()


    def load_mini_notes(self):
        ''' Loads our mini notes from our data into live objects '''
        from models.mini_widgets.comment import Comment

        # Loop through our data mini notes and create live objects for each
        for note_title, note_data in self.data['comments'].items():
            self.mini_widgets.append(Comment(
                title=note_title,
                owner=self,
                father=self,
                page=self.p,
                key="comments",
                data=note_data,
            ))
    
    def submit_comment(self, e):
        title = e.control.value
        self.create_comment(title)
        e.control.value = ""
        self.reload_widget()

    # Called when right clicking our controls for either timeline or an arc
    def get_menu_options(self) -> list[ft.Control]:

        # Color, rename
        return [
            Menu_Option_Style(
                #on_click=self.rename_clicked,
                content=ft.Row([
                    ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED),
                    ft.Text(
                        "Rename", 
                        weight=ft.FontWeight.BOLD, 
                        color=ft.Colors.ON_SURFACE
                    ), 
                ]),
            ),
            # Color changing popup menu
            Menu_Option_Style(
                content=ft.PopupMenuButton(
                    expand=True,
                    tooltip="",
                    padding=None,
                    content=ft.Row(
                        expand=True,
                        controls=[
                            ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, color=ft.Colors.PRIMARY),
                            ft.Text("Color", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True), 
                            ft.Icon(ft.Icons.ARROW_DROP_DOWN_OUTLINED, color=ft.Colors.ON_SURFACE, size=16),
                        ]
                    ),
                    items=self.get_color_options()
                )
            ),
        ]




    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # Rebuild out tab to reflect any changes
        self.reload_tab()
        
        # BUILDING BODY - the inside the body container of our widget
        
        self.body_container.content = ft.Column(
            expand=True,
            controls=[
                FletQuill(
                    file_path=f"{self.directory_path}/{self.title}_text.json",

                    #border_visible=True,
                    #border_width=1.0,       # Defaults to 1.0

                    # Set paddings around the editor. Defaults to 10.0
                    #padding_left=72.0,
                    #padding_top=72.0,
                    #padding_right=72.0,
                    #padding_bottom=72.0,

                    #aspect_ratio=8.5/11.0,  # paper-like ratio

                    #show_toolbar_divider=False,  # Show divider below toolbar
                )
            ]
        )
        

        self._render_widget()

        