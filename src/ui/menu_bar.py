''' 
UI element for our Menu bar at the top of the page (file, edit, etc)
Holds our settings icon, feedback, and account name as well
'''

import flet as ft
from models.app import app
from models.views.story import Story
from utils.check_story_unique import story_is_unique
from styles.snack_bar import SnackBar



# Called in main to create menu bar if no story exists, or by a story to create menu bar for that story
def create_menu_bar(page: ft.Page, story: Story = None) -> ft.Container:


    def _rename_clicked(e):
        # Should pop open dialog to rename current story
        pass


    # Called when file -> new is clicked
    def _create_new_story_clicked(e):
        ''' Opens a dialog to create a new story. Checks story is unique or not '''


        

        async def submit_new_story(e):
            ''' Creates a new story with the given title '''

            # Import our variable if it is unique or nah
            is_unique = not create_button.disabled
            if not is_unique:
                await story_title_field.focus()   # refocus the text field since the title was not unique
                story_title_field.update()
                return

            title = story_title_field.value.strip()

            # Check if the title is unique
            if is_unique:
                #print("title is unique, story being created: ", title)
                app.create_new_story(title, page) # Needs the story object
                page.pop_dialog()
            else:
                story_title_field.error = "Story Title must be unique"
                await story_title_field.focus()   # refocus the text field since the title was not unique
                story_title_field.update()


        # Called everytime the user enters a new letter in the text box
        async def textbox_value_changed(e):
            ''' Called when the text in the text box changes '''

            is_unique = story_is_unique(story_title_field.value)

            if story_title_field.value.strip() == "":   # Disable the button if the text box is empty
                is_unique = False

            create_button.disabled = not is_unique
            story_title_field.error = None if is_unique else "Story Title must be unique"
            
                
            create_button.update()
            await story_title_field.focus()   # refocus the text field so user can keep typing without clicking back in
            story_title_field.update()


        # Create a reference to the text field so we can access its value
        story_title_field = ft.TextField(
            label="Story Title",
            autofocus=True, capitalization=ft.TextCapitalization.WORDS,
            on_submit=submit_new_story,
            on_change=textbox_value_changed,
        )

        create_button = ft.TextButton(
            "Create", on_click=submit_new_story, disabled=True, style=ft.ButtonStyle(mouse_cursor="click")
        )

        # The dialog that will pop up whenever the new story button is clicked
        dlg = ft.AlertDialog(

            # Title of our dialog
            title=ft.Text(
                "Create New Story", 
                color=ft.Colors.ON_SURFACE,
                weight=ft.FontWeight.BOLD,
            ),

            # Main content is text box for user to input story title
            content=story_title_field,

            # Our two action buttons at the bottom of the dialog
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                create_button,
            ],
        )

        # Open our dialog in the overlay
        page.show_dialog(dlg)


    # Called when file -> open is clicked
    async def _open_clicked(e=None):
        ''' Opens a dialog to open an existing story '''

        #print("Open Story Clicked")

        selected_story = None

        # Called when a new story text button is clicked
        def change_selected_story(e):
            ''' Changes our selected story variable '''

            nonlocal selected_story
            selected_story = e.control.value
            open_button.disabled = False
            open_button.style=ft.ButtonStyle(color=ft.Colors.PRIMARY, mouse_cursor="click")
            open_button.update()

        # Returns a list of all story titles available to open
        def get_stories_list() -> ft.Control:
            ''' Returns a list of all story titles available to open '''

            # List of our story choices
            stories = []

            # Set style for our options
            style = ft.TextStyle(
                size=14,
                color=ft.Colors.ON_SURFACE,
                weight=ft.FontWeight.BOLD,
            )

            # Use something better than radio in future, but for now this works
            for story in app.stories.values():
                stories.append(
                    ft.Radio(expand=False, value=story.data.get('title'), label=story.data.get('title'), label_style=style, mouse_cursor=ft.MouseCursor.CLICK)
                )

            # Return our list of stories
            return stories


        # Called when the 'open' button is clicked in the bottom right of the dialog
        async def open_selected_story(e=None):
            ''' Changes the route to the selected story '''

            #print("Open button clicked, selected story is: ", selected_story)

            if selected_story is not None:
                await page.push_route(app.stories[selected_story].route)
                app.settings.story = app.stories[selected_story]  # Gives our settings widget the story reference it needs
                page.pop_dialog()
                page.update()
            else:
                print("No story selected")

            page.pop_dialog()
            page.update()

        open_button = ft.TextButton("Open", on_click=open_selected_story, disabled=True, style=ft.ButtonStyle(mouse_cursor="click"))

        # Our alert dialog that pops up when file -> open is clicked
        dlg = ft.AlertDialog(
            title=ft.Text(
                "What story would you like to open?",
                color=ft.Colors.ON_SURFACE,
                weight=ft.FontWeight.BOLD,
            ),
            alignment=ft.Alignment.CENTER,
            title_padding=ft.Padding.all(25),
            content=ft.RadioGroup(
                content=ft.Column(scroll=ft.ScrollMode.AUTO, expand=False, controls=get_stories_list()),
                on_change=change_selected_story
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                open_button,
            ]
        )

        # Opens our dialog
        page.show_dialog(dlg)

    async def _settings_clicked(e=None):
        ''' Goes to the settings page '''
        if page.route != "/settings":
            await page.push_route("/settings")
        else:
            # Get the active story title and find its route
            if story is not None:
                await page.push_route(story.route)
            else:
                await page.push_route("/")

    # Create our menu bar with submenu items
    file_options = ft.MenuBar(
        #expand=True,
        style=ft.MenuStyle(     # Styling our menubar
            alignment=ft.Alignment.CENTER,
            bgcolor=ft.Colors.TRANSPARENT,
            shadow_color=ft.Colors.TRANSPARENT,
            
        ),
        controls=[  # The controls shown in our menu bar from left to right
            ft.SubmenuButton(   # Button that opens a subment
                content=ft.Container(
                    content=ft.Text("File", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),     # Content of subment button
                    alignment=ft.Alignment.CENTER
                ), 
                style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                menu_style=ft.MenuStyle(padding=ft.Padding.all(0)),
                
                controls=[      # The options shown inside of our button
                    ft.MenuItemButton(
                        content=ft.Text("New Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        leading=ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED, ft.Colors.PRIMARY),
                        close_on_click=True,
                        style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                        on_click=_create_new_story_clicked,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Open Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        leading=ft.Icon(ft.CupertinoIcons.BOOK, ft.Colors.PRIMARY),
                        close_on_click=True,
                        style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                        on_click=_open_clicked,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Rename Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        leading=ft.Icon(ft.Icons.EDIT_OUTLINED, ft.Colors.PRIMARY),
                        close_on_click=True,
                        style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                        on_click=_rename_clicked,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Import Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        tooltip="Import a folder containing an exported story from Story Board on another device.",
                        leading=ft.Icon(ft.Icons.FILE_UPLOAD_OUTLINED, ft.Colors.PRIMARY),
                        close_on_click=True,
                        style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                        #on_click=_open_clicked,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Export Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        leading=ft.Icon(ft.Icons.FILE_DOWNLOAD_OUTLINED, ft.Colors.PRIMARY),
                        close_on_click=True,
                        tooltip="Export's your story to a folder on your device. Allows for easy import to Story Board on another device.",
                        style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                        #on_click=_open_clicked,
                    ),
                    
                    ft.MenuItemButton(
                        content=ft.Text("Settings", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        leading=ft.Icon(ft.Icons.SETTINGS_OUTLINED, ft.Colors.PRIMARY),
                        close_on_click=True,
                        style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                        on_click=_settings_clicked,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Delete Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        leading=ft.Icon(ft.Icons.DELETE_FOREVER_ROUNDED, ft.Colors.ERROR),
                        close_on_click=True,
                        style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                        #on_click=_delete_clicked,
                    ),
                ],
            ),
        ], 
    )

    class TextController(ft.Row):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.alignment = ft.MainAxisAlignment.CENTER
            self.data = app.settings.data.get('text_controller_settings', {})
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
                    e.control.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGH
                    e.control.icon_color = ft.Colors.PRIMARY
                else:
                    e.control.bgcolor = ft.Colors.TRANSPARENT
                    e.control.icon_color = ft.Colors.ON_SURFACE_VARIANT
                e.control.update()
                app.settings.update_data(**{'text_controller_settings': self.data})


            self.controls = [   

                #ft.Text("Text Controller", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE_VARIANT, size=14, italic=True, opacity=.5),

                ft.IconButton(
                    ft.Icons.FORMAT_BOLD,
                    ft.Colors.PRIMARY if self.data.get('bold', False) else ft.Colors.ON_SURFACE_VARIANT,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH if self.data.get('bold', False) else ft.Colors.TRANSPARENT,
                    data="bold", on_click=set_buttons,
                    visible=False,  # TEMP
                ),
                ft.IconButton(
                    ft.Icons.FORMAT_ITALIC,
                    ft.Colors.PRIMARY if self.data.get('italic', False) else ft.Colors.ON_SURFACE_VARIANT,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH if self.data.get('italic', False) else ft.Colors.TRANSPARENT,
                    data="italic", on_click=set_buttons,
                    visible=False,  # TEMP
                ),

                # TODO: Text Controller
                # size, format_align, font family, letter_spacing, word_spacing, color
                # decoration, decoration color, decoration thickness, decoration style
            ]

    text_controller = TextController()
    
        
    # Return our formatted menubar
    return ft.Container(
        border=ft.Border.only(bottom=ft.BorderSide(width=1, color=ft.Colors.OUTLINE_VARIANT)),
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
        content=ft.Row(
            spacing=0,
            controls=[
                file_options,    # Menubar on left
                text_controller,

                ft.Text(
                    "Alpha", color=ft.Colors.PRIMARY, weight=ft.FontWeight.BOLD, 
                    tooltip="Storyboard is currently in alpha. Bugs are expected. More features coming soon! \nCheck out Settings -> Resources for a list of planned features and known issues. \nJoin the Discord to suggest your features and report bugs."
                ),  # Feedback button
                ft.Icon(
                    ft.Icons.INFO_OUTLINED, color=ft.Colors.PRIMARY, scale=.5, 
                    tooltip="Storyboard is currently in alpha. Bugs are expected. More features coming soon! \nCheck out Settings -> Resources for a list of planned features and known issues. \nJoin the Discord to suggest your features and report bugs."
                ),
                ft.IconButton(ft.Icons.SETTINGS_OUTLINED, "primary", on_click=_settings_clicked, mouse_cursor=ft.MouseCursor.CLICK),   # Settings button
            ]
        )
    )