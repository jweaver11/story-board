''' 
Class for our menubar, which will hold our file options, drawing controls, and setting shortcut
'''

import flet as ft
from models.app import app
from models.views.story import Story
from utils.check_story_unique import story_is_unique
from styles.snack_bar import SnackBar
from styles.text_fields import TextField
from flet_color_pickers import ColorPicker
import math
import flet.canvas as cv
from utils.safe_string_checker import return_safe_name



class MenuBar(ft.Container):
    def __init__(self, story: Story = None):

        self.story = story

        super().__init__(
            border=ft.Border.only(bottom=ft.BorderSide(width=1, color=ft.Colors.OUTLINE_VARIANT)),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
        )

    def is_isolated(self):
        return True


    def build(self):

        class Dropdown(ft.Dropdown):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.border_color=ft.Colors.OUTLINE_VARIANT
                self.menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4))
                self.label_style=ft.TextStyle(color=ft.Colors.ON_SURFACE_VARIANT, italic=True)
                self.margin=ft.Margin.only(top=8, left=4, right=4)
                self.dense=True

        class Switch(ft.Switch):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.adaptive=True
                self.label_style=ft.TextStyle(color=ft.Colors.ON_SURFACE_VARIANT, italic=True)
                #self.margin=ft.Margin.only(top=8, left=4, right=4)
                


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
                    app.create_new_story(title, self.page) # Needs the story object
                    self.page.pop_dialog()
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
                    ft.TextButton("Cancel", on_click=lambda e: self.page.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                    create_button,
                ],
            )
    
            # Open our dialog in the overlay
            self.page.show_dialog(dlg)
    
    
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
                    await self.page.push_route(app.stories[selected_story].route)
                    app.settings.story = app.stories[selected_story]  # Gives our settings widget the story reference it needs
                    self.page.pop_dialog()
                    self.page.update()
                else:
                    print("No story selected")
    
                self.page.pop_dialog()
                self.page.update()
    
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
                    ft.TextButton("Cancel", on_click=lambda e: self.page.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                    open_button,
                ]
            )
    
            # Opens our dialog
            self.page.show_dialog(dlg)
    
        async def _settings_clicked(e=None):
            ''' Goes to the settings page '''
            if self.page.route != "/settings":
                await self.page.push_route("/settings")
            else:
                # Get the active story title and find its route
                if self.story is not None:
                    await self.page.push_route(self.story.route)
                else:
                    await self.page.push_route("/")

        def toggle_show_canvas_rail(e: ft.Event[ft.MenuItemButton]):
            ''' Toggles the visibility of the canvas rail on the left side of the page '''
            new_value = not app.settings.data.get('story', {}).get('show_canvas_rail', False)
            app.settings.update_data(**{'story': {'show_canvas_rail': new_value}})
            if new_value:
                e.control.leading.icon = ft.Icons.VISIBILITY_OUTLINED
            else:
                e.control.leading.icon = ft.Icons.VISIBILITY_OFF_OUTLINED
            if self.story is not None:
                if new_value:
                    self.story.canvas_rail.width = 78
                else:
                    self.story.canvas_rail.width = 0
                self.story.canvas_rail.update()
            e.control.update()
    
        # Create our menu bar with submenu items
        file_options = ft.MenuBar(
            #expand=True,
            style=ft.MenuStyle(     # Styling our menubar
                alignment=ft.Alignment.CENTER,
                bgcolor=ft.Colors.TRANSPARENT,
                shadow_color=ft.Colors.TRANSPARENT,
                padding=ft.Padding.all(0)
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
                            content=ft.Text("Toggle Canvas Rail", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                            leading=ft.Icon(
                                ft.Icons.VISIBILITY_OUTLINED if app.settings.data.get('story', {}).get('show_canvas_rail', False) else ft.Icons.VISIBILITY_OFF_OUTLINED,
                                ft.Colors.PRIMARY
                            ),
                            close_on_click=True, 
                            disabled=self.story is None,
                            style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                            on_click=toggle_show_canvas_rail,
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







        # DRAW MODE STUFFF -----------------------------------------------------



        # Our settings for easier reference
        paint_settings: dict        # Paint for our brush
        canvas_settings: dict       # Other drawing and shape related settings
        text_settings: dict         # Text settings

        # UI elements used in the canvas rail
        color_picker: ColorPicker              # Color picker for changing brush color
        color_selector: ft.SubmenuButton       # Button on the rail for selected a color. Clicking shows our color picker

        set_draw_mode_button: ft.IconButton          # Button for setting draw mode on the current brush. Only does anything if in tool mode
        brush_selector: ft.SubmenuButton        # Button on the rail for selecting a brush. Clicking shows our brush options

        set_tool_mode_button: ft.IconButton          # Button for setting tool mode on the current brush. Only does anything if in draw mode
        tool_selector: ft.SubmenuButton         # Button on the rail for selecting a tool. Clicking shows our tool options
        #stroke_smoothing_strength_slider : ft.Slider              # Slider for changing the strength of the smooth stroke effect

        #brush_smoothing_switch: ft.Switch        # If we should use path smoothing switch
        
        
        stroke_dashed_pattern_switch: ft.Switch            # Switch for enabling dashed strokes or not
        # Something stroke dashed editor here

        


        # Text controller settings -----------------------------------------------------



        # Updates the mouse cursor or all visible canvases based on updated tool mode
        def set_canvas_mouse_cursor():
            if self.story is None:
                return
            for widget in self.story.workspace.tab_view.controls:
                if not widget.data: # Protect empty
                    return
                if widget.data.get('tag') == "canvas":
                    if widget.data.get('visible', True):
                        if widget.state.manipulating_shape == True:
                            widget.set_mouse_cursor()
                            break

        # Checks all our widgets. If any of them are manipulating a tool, we paint it on the canvas if switching from tool to draw mode
        def update_canvas_tool_preview():
            if self.story is None:
                return
            for widget in self.story.workspace.tab_view.controls:
                if not widget.data: # Protect empty
                    return
                if widget.data.get('tag') == "canvas":
                    if widget.data.get('visible', True):
                        if widget.state.manipulating_shape == True:
                            widget.update_tool_preview()
                            break

        # Set the color pickers color upon change
        def set_color(e: ft.Event[ColorPicker]):
            color_picker.color = e.data

        # Saves our color to data and updates the brush selector
        def save_color(e=None):
            paint_settings.update({"color": color_picker.color})
            app.settings.update_data(**{"paint_settings": paint_settings})
            #update_brush_preview()
            #brush_selector.controls = get_brush_options()   # Update the brush selector with the new brush
            brush_preview.content = build_preview_brush()   # Update the brush selector with the new brush
            #set_tool_mode_button.icon = update_tool_icon()
            color_selector.content.color = color_picker.color
            self.update()
            set_canvas_mouse_cursor()
            update_canvas_tool_preview()

        # Sets current control mode to drawing
        def set_draw_mode(e=None):
            nonlocal canvas_settings, paint_settings, brush_selector, set_draw_mode_button
            canvas_settings['current_control_mode'] = "draw"
            if app.settings.data.get('paint_settings', {}).get('blend_mode', "") == "clear":
                paint_settings['blend_mode'] = "src_over"
            app.settings.update_data(**{'paint_settings': paint_settings, 'canvas_settings': canvas_settings})
            # Update UI
            #update_brush_preview()
            #brush_selector.controls = get_brush_options()   # Update the brush selector with the new brush
            brush_preview.content = build_preview_brush()
            set_canvas_mouse_cursor()
            brush_selector.style.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
            color_selector.content.color = paint_settings.get('color', "#000000")
            set_draw_mode_button.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
            set_draw_mode_button.icon = ft.Icons.BRUSH_ROUNDED
            #set_tool_mode_button.bgcolor = None
            #set_tool_mode_button.icon = ft.Icons.BUILD_OUTLINED
            #set_tool_mode_button.icon = update_tool_icon()
            tool_selector.style.bgcolor = None
            self.update()

        

        # Build a small preview of current or passed in brush settings to show in the brush selector
        def build_preview_brush(brush_settings: dict=None) -> ft.Control:
            nonlocal paint_settings

            # Set current settings or passed in settings
            if brush_settings is None:
                brush_settings = paint_settings.copy()
            else:
                brush_settings = brush_settings.copy()

            # Create our preview canvas. Paint like w=100, and h=30. Extra height is justp adding
            preview_canvas = cv.Canvas(width=120, height=50)

            # Set max values of paint so that it fits normally on our small preview
            if brush_settings.get('stroke_width', 3) > 6:
                brush_settings['stroke_width'] = 6
            if brush_settings.get('blur_image', 0) > 6:
                brush_settings['blur_image'] = 6
            brush_settings['blend_mode'] = None     # Turn off blend mode

            # Paint the stroke with safe paint settings, leaving 10px padding on all sides
            preview_canvas.shapes = [
                cv.Path([
                    cv.Path.MoveTo(10, 40),     # Bottom Left
                    cv.Path.CubicTo(10, 40, 35, 20, 60, 25),    # Bottom left -> Middle
                    cv.Path.CubicTo(60, 25, 80, 30, 110, 10)    # Middle -> Top Right
                ], brush_settings)
            ]
            return preview_canvas   # Return the canvas
        
        # Sets current brush settings using passed in brush settings
        def set_active_brush(brush_settings: dict, name: str):
            nonlocal canvas_settings, paint_settings
            canvas_settings.update({"current_control_mode": {'current_control_mode': "draw", 'current_brush_name': name}})
            paint_settings.update(**brush_settings)
            app.settings.update_data(**{"canvas_settings": canvas_settings, "paint_settings": brush_settings})
            #update_brush_preview()
            #brush_selector.controls = get_brush_options()   # Update the brush selector with the new brush
            brush_preview.content = build_preview_brush()
            set_draw_mode()
            self.update()
            set_canvas_mouse_cursor()
            update_canvas_tool_preview()
            
        
        # Called to save our active brush settings as a custom brush we can load later (Excludes color and opacity)
        def save_custom_brush_clicked(e=None):
            ''' Shows our existing brush options and allows us to override or save as a new brush '''

            # Saves the current name and closes the dialog
            async def _save_and_close(e=None): 

                nonlocal name, paint_settings
                safe_name = return_safe_name(name)

                # Save current brush settings as a new custom brush
                app.settings.data['canvas_settings']['saved_brushes'][safe_name] = paint_settings.copy()
                app.settings.update_data(**{"canvas_settings": {"saved_brushes": app.settings.data['canvas_settings']['saved_brushes']}})

                self.page.pop_dialog()
                brush_selector.controls = get_brush_options()   # Update the brush selector with the new brush
                brush_preview.content = build_preview_brush()
                self.update()

            # Deletes a color
            async def _delete_custom_brush(e):
                nonlocal content
                name = e.control.data

                # Remove it from data
                if name in app.settings.data.get('canvas_settings', {}).get('saved_brushes', {}):
                    del app.settings.data['canvas_settings']['saved_brushes'][name]
                    app.settings.update_data(**{"canvas_settings": {"saved_brushes": app.settings.data['canvas_settings']['saved_brushes']}})

                # Remove the control from the dialog
                dlg.content.controls = [ctrl for ctrl in content.controls if ctrl.data != name]   
                content.update()

                brush_selector.controls = get_brush_options()   # Update the brush selector with the new brush
                brush_preview.content = build_preview_brush()
                self.update()

                # If we were going to override it but instead deleted it, apply that UI change
                if name == new_custom_brush_name_text_field.value:
                    new_custom_brush_name_text_field.error = None
                    new_custom_brush_name_text_field.update()
                    save_button.content = "Save"
                    save_button.update()
                    await new_custom_brush_name_text_field.focus()
                    
            # Sets an existing custom color to be overwritten by the current color
            def _select_active_brush_override(e):
                nonlocal name, content
                
                # Show visual effects that the brush will be overwritten
                name = e.control.data
                e.control.bgcolor = ft.Colors.OUTLINE_VARIANT
                e.control.update()
                save_button.content = "Overwrite"
                save_button.update()

                # Textfield UI changes
                new_custom_brush_name_text_field.value = name
                new_custom_brush_name_text_field.error = f"Saving will overwrite {name}"
                new_custom_brush_name_text_field.update()

                # Deselect any other options that are selected
                for ctrl in dlg.content.controls:
                    if isinstance(ctrl, ft.Container) and ctrl != e.control:
                        if ctrl.bgcolor == ft.Colors.OUTLINE_VARIANT:
                            ctrl.bgcolor = ft.Colors.TRANSPARENT
                            ctrl.update()

            # If newly changed name already exists, show that it will be overwritten
            def _check_name_change(e: ft.Event[ft.TextField]):
                nonlocal content, name
                name = e.control.value
                new_name = e.control.value  

                for ctrl in content.controls:
                    if isinstance(ctrl, ft.Container) and ctrl.data == new_name:
                        ctrl.bgcolor = ft.Colors.OUTLINE_VARIANT
                        ctrl.update()
                        save_button.content = "Overwrite"
                        save_button.update()
                        e.control.error = f"Saving will overwrite {e.control.value}"
                        e.control.update()
                        return
                    
                for ctrl in content.controls:
                    if isinstance(ctrl, ft.Container):
                        ctrl.bgcolor = ft.Colors.TRANSPARENT
                        ctrl.update()
                save_button.content = "Save"
                save_button.update()
                e.control.error = None
                e.control.update()

            # Textfield for naming custom color
            new_custom_brush_name_text_field = ft.TextField(
                label="Brush Name", autofocus=True, on_submit=_save_and_close, dense=True,
                capitalization=ft.TextCapitalization.SENTENCES, #expand=True,
                on_change=_check_name_change, 
            )

            name: str = None

            # Our save button that just changes text from save to overwrite
            save_button = ft.TextButton("Save", on_click=_save_and_close, style=ft.ButtonStyle(mouse_cursor="click")) 

            content = ft.Column([new_custom_brush_name_text_field], scroll=ft.ScrollMode.AUTO, height=self.page.height / 2) 

            dlg = ft.AlertDialog(
                title=ft.Text("Name your custom brush"), 
                content=content,
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                    save_button
                ]
            )

            for name, existing_brush in app.settings.data.get('canvas_settings', {}).get('saved_brushes', {}).items():
                content.controls.append(
                    ft.Container(
                        ft.Row([
                            ft.Text(name, theme_style=ft.TextThemeStyle.LABEL_LARGE, expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                            build_preview_brush(existing_brush),
                            ft.IconButton(
                                ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, 
                                data=name, on_click=_delete_custom_brush, tooltip="Delete this saved brush",
                                mouse_cursor=ft.MouseCursor.CLICK
                            ),
                        ], spacing=20), border_radius=ft.BorderRadius.all(4), clip_behavior=ft.ClipBehavior.HARD_EDGE, padding=ft.Padding.only(left=6),
                        on_click=_select_active_brush_override, data=name,
                    )
                )

            self.page.show_dialog(dlg)

        def update_tool_icon():
            nonlocal canvas_settings
            in_tool_mode = canvas_settings.get('current_control_mode', "") == "tool"
            match canvas_settings.get('current_tool_name', ""):
                case "erase": 
                    return ft.Icon(ft.Icons.AUTO_FIX_NORMAL if in_tool_mode else ft.Icons.AUTO_FIX_NORMAL_OUTLINED, ft.Colors.PRIMARY)
                case "line":
                    return ft.Icon(ft.Icons.REMOVE if in_tool_mode else ft.Icons.REMOVE_OUTLINED, ft.Colors.PRIMARY)
                case "text":
                    return ft.Icon(ft.Icons.TEXT_FIELDS if in_tool_mode else ft.Icons.TEXT_FIELDS_OUTLINED, ft.Colors.PRIMARY)
                case "circle":
                    return ft.Icon(ft.Icons.CIRCLE if in_tool_mode else ft.Icons.CIRCLE_OUTLINED, ft.Colors.PRIMARY)
                case "arc":
                    return ft.Icon(ft.CupertinoIcons.CIRCLE_RIGHTHALF_FILL, ft.Colors.PRIMARY, rotate=math.pi/2)
                case "rectangle":
                    return ft.Icon(ft.Icons.RECTANGLE if in_tool_mode else ft.Icons.RECTANGLE_OUTLINED, ft.Colors.PRIMARY)
                case "triangle":
                    return ft.Icon(ft.CupertinoIcons.ARROWTRIANGLE_UP_FILL if in_tool_mode else ft.CupertinoIcons.ARROWTRIANGLE_UP, ft.Colors.PRIMARY)
                case "oval":
                    return ft.Icon(ft.Icons.CIRCLE if in_tool_mode else ft.Icons.CIRCLE_OUTLINED, ft.Colors.PRIMARY, scale=ft.Scale(scale_x=0.8))
                case "dialogue_box":
                    return ft.Icon(ft.CupertinoIcons.BUBBLE_LEFT_FILL if in_tool_mode else ft.CupertinoIcons.BUBBLE_LEFT, ft.Colors.PRIMARY)
                case _:
                    return ft.Icon(ft.Icons.BUILD if in_tool_mode else ft.Icons.BUILD_OUTLINED, ft.Colors.PRIMARY, scale=0.8)

        # Sets current control mode to tool
        def set_tool_mode(e: ft.Event[ft.IconButton]):
            nonlocal canvas_settings, paint_settings, brush_selector, set_tool_mode_button
            canvas_settings['current_control_mode'] = "tool"
            app.settings.update_data(**{'canvas_settings': canvas_settings})
            set_canvas_mouse_cursor()
            # Update buttons
            brush_selector.style.bgcolor = None
            set_draw_mode_button.bgcolor = None
            set_draw_mode_button.icon = ft.Icons.BRUSH_OUTLINED
            set_tool_mode_button.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
            set_tool_mode_button.icon = ft.Icons.BUILD_ROUNDED
            tool_selector.style.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
            set_tool_mode_button.icon = update_tool_icon()
            self.update() 

        def get_tool_options() -> list[ft.Control]:
            ''' Gets our tool options for the popup menu. '''
    
            return [
                ft.Text("Tools", color=ft.Colors.ON_SURFACE_VARIANT, italic=True, margin=ft.Margin.only(left=4, top=4, right=4)),   # Placeholder for shapes section
                ft.MenuItemButton(
                    ft.Row([
                        ft.Text("Erase", overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                        ft.Icon(ft.Icons.AUTO_FIX_NORMAL, ft.Colors.PRIMARY)
                    ]),
                    data="erase",
                    on_click=set_active_tool,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor=ft.MouseCursor.CLICK),
                    tooltip="Erase parts of your Canvas using your current brush width"
                ),
                ft.MenuItemButton(
                    ft.Row([
                        ft.Text("Line", overflow=ft.TextOverflow.ELLIPSIS, expand=True), 
                        ft.Icon(ft.Icons.REMOVE, ft.Colors.PRIMARY)
                    ]),
                    data="line",
                    on_click=set_active_tool,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor=ft.MouseCursor.CLICK),
                    tooltip="Draw straight lines. Click and drag to draw a line between your starting point and the current position of your mouse."
                ),
                ft.MenuItemButton(
                    ft.Row([
                        ft.Text("Text", overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                        ft.Icon(ft.Icons.TEXT_FIELDS, ft.Colors.PRIMARY)
                    ]),
                    data="text",
                    on_click=set_active_tool,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor=ft.MouseCursor.CLICK),
                    tooltip="Add text only to your canvas. Useful for labels"
                ),
                
    
                # Shapes we can use
                ft.Divider(), 
                ft.Text("Shapes", color=ft.Colors.ON_SURFACE_VARIANT, italic=True, margin=ft.Margin.only(left=4, right=4)),   # Placeholder for shapes section
                
                #ft.MenuItemButton(
                    #ft.Row([
                        #ft.Text("Dialogue Box", overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                        #ft.Icon(ft.CupertinoIcons.BUBBLE_LEFT_FILL, ft.Colors.PRIMARY)
                        # ft.CupertinoIcons.CHAT_BUBBLE
                    #]),
                    #data="dialogue_box",
                    #on_click=set_active_tool,
                    #style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor=ft.MouseCursor.CLICK),
                    #tooltip="Add dialogue boxes to your canvas"
                #),
    
                ft.MenuItemButton(
                    ft.Row([
                        ft.Text("Circle", overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                        ft.Icon(ft.Icons.CIRCLE, ft.Colors.PRIMARY)
                    ]),
                    data="circle",
                    on_click=set_active_tool,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor=ft.MouseCursor.CLICK),
                    tooltip="Add perfect circles to your canvas"
                ),
                ft.MenuItemButton(
                    ft.Row([
                        ft.Text("Oval", overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                        ft.Icon(ft.Icons.CIRCLE, ft.Colors.PRIMARY, scale=ft.Scale(scale_x=0.8))
                    ]),
                    data="oval",
                    on_click=set_active_tool,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor=ft.MouseCursor.CLICK),
                    tooltip="Add ovals and ellipses to your canvas"
                ),
                ft.MenuItemButton(
                    ft.Row([
                        ft.Text("Arc", overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                        ft.Icon(ft.CupertinoIcons.CIRCLE_RIGHTHALF_FILL, ft.Colors.PRIMARY, rotate=math.pi/2)   
                    ]),
                    data="arc",
                    on_click=set_active_tool,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor=ft.MouseCursor.CLICK),
                    tooltip="Add arcs and partial circles to your canvas"
                ),
                ft.MenuItemButton(
                    ft.Row([
                        ft.Text("Rectangle", overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                        ft.Icon(ft.Icons.RECTANGLE, ft.Colors.PRIMARY)
                    ]),
                    data="rectangle",
                    on_click=set_active_tool,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor=ft.MouseCursor.CLICK),
                    tooltip="Add rectangles and squares to your canvas"
                ),
                ft.MenuItemButton(
                    ft.Row([
                        ft.Text("Triangle", overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                        ft.Icon(ft.CupertinoIcons.ARROWTRIANGLE_UP_FILL, ft.Colors.PRIMARY)
                    ]),
                    data="triangle",
                    on_click=set_active_tool,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor=ft.MouseCursor.CLICK),
                    tooltip="Add triangles to your canvas"
                ),    
            ]

        # Sets the active tool and updates the tool selector icon and brush preview
        async def set_active_tool(e: ft.Event[ft.MenuItemButton]):
            nonlocal canvas_settings, paint_settings
            tool_name = e.control.data
            canvas_settings.update({"current_tool_name": tool_name})
            app.settings.update_data(**{"canvas_settings": canvas_settings})
            set_tool_mode()
            self.update()
            set_canvas_mouse_cursor()

        # Called when changing paint width
        def update_paint_width(e: ft.Event[ft.Slider]):
            nonlocal paint_settings
            paint_settings.update({"stroke_width": int(e.control.value)})
            app.settings.update_data(**{"paint_settings": paint_settings})
            #update_brush_preview()
            #brush_selector.controls = get_brush_options()   # Update the brush selector with the new brush
            brush_preview.content = build_preview_brush()
            self.update()
            set_canvas_mouse_cursor()
            update_canvas_tool_preview()

        # Called when changing paint width
        def update_paint_blur(e: ft.Event[ft.Slider]):
            nonlocal paint_settings
            paint_settings.update({"blur_image": int(e.control.value)})
            app.settings.update_data(**{"paint_settings": paint_settings})
            #update_brush_preview()
            #brush_selector.controls = get_brush_options()   # Update the brush selector with the new brush
            brush_preview.content = build_preview_brush()
            self.update()
            update_canvas_tool_preview()

        # Add fill or not to our style based on teh switch state
        def update_paint_fill(e: ft.Event[ft.Switch]):
            nonlocal paint_settings
            is_fill = e.control.value
            if is_fill:
                paint_settings.update({"style": paint_settings['style'] + "_fill"})
            else:
                paint_settings.update({"style": paint_settings['style'].replace("_fill", "")})
            app.settings.update_data(**{"paint_settings": paint_settings})
            #update_brush_preview()
            #brush_selector.controls = get_brush_options()   # Update the brush selector with the new brush
            brush_preview.content = build_preview_brush()
            self.update()
            update_canvas_tool_preview()

        # Called when changing paint anti-aliasing
        def update_paint_anti_alias(e: ft.Event[ft.Switch]):
            nonlocal paint_settings
            paint_settings.update({"anti_alias": e.control.value})
            app.settings.update_data(**{"paint_settings": paint_settings})
            #update_brush_preview()
            #brush_selector.controls = get_brush_options()   # Update the brush selector with the new brush
            brush_preview.content = build_preview_brush()
            self.update()
            update_canvas_tool_preview()

        # Updates whether we'll use path smoothing or not
        def update_paint_brush_smoothing(e: ft.Event[ft.Switch]):
            nonlocal canvas_settings
            canvas_settings.update({"use_brush_smoothing": e.control.value})
            app.settings.update_data(**{"canvas_settings": canvas_settings})

        # Updates the strength of the smooth stroke effect
        def update_paint_stroke_smoothing_strength(e: ft.Event[ft.Slider]):
            nonlocal canvas_settings
            canvas_settings.update({"stroke_smoothing_strength": e.control.value})
            app.settings.update_data(**{"canvas_settings": canvas_settings})

        # Returns the correct icon for the current stroke cap setting based on current paint settings
        def get_stroke_cap_icon() -> ft.Icon:
            nonlocal paint_settings
            stroke_cap = paint_settings.get('stroke_cap', 'butt')
            if stroke_cap == 'round': return ft.Icon(ft.Icons.CIRCLE, ft.Colors.PRIMARY)
            elif stroke_cap == 'square':return ft.Icon(ft.Icons.SQUARE, ft.Colors.PRIMARY)
            else: return ft.Icon(ft.Icons.SQUARE_ROUNDED, ft.Colors.PRIMARY)

        # Updates the stroke cap of the current paint
        def update_paint_stroke_cap(e: ft.Event[ft.Dropdown]):
            nonlocal paint_settings
            new_stroke_cap = e.control.value.lower()
            paint_settings['stroke_cap'] = new_stroke_cap
            app.settings.update_data(**{"paint_settings": {"stroke_cap": new_stroke_cap}})
            e.control.leading_icon = get_stroke_cap_icon()
            #update_brush_preview()
            #brush_selector.controls = get_brush_options()   # Update the brush selector with the new brush
            brush_preview.content = build_preview_brush()
            self.update()
            set_canvas_mouse_cursor()
            update_canvas_tool_preview()

        # Returns the correct icon for the current stroke join setting based on current paint settings
        def get_stroke_join_icon() -> ft.Icon:
            nonlocal paint_settings
            stroke_join = paint_settings.get('stroke_join', 'miter')
            if stroke_join == 'round': return ft.Icon(ft.Icons.CIRCLE, ft.Colors.PRIMARY)
            elif stroke_join == 'bevel': return ft.Icon(ft.Icons.SQUARE, ft.Colors.PRIMARY)
            else: return ft.Icon(ft.Icons.SQUARE_ROUNDED, ft.Colors.PRIMARY)


        # Updates the stroke join of the current paint
        async def update_paint_stroke_join(e: ft.Event[ft.Dropdown]):
            nonlocal paint_settings
            new_stroke_join = e.control.value.lower()
            paint_settings['stroke_join'] = new_stroke_join
            app.settings.update_data(**{"paint_settings": {"stroke_join": new_stroke_join}})
            e.control.leading_icon = get_stroke_join_icon()
            #update_brush_preview()
            #brush_selector.controls = get_brush_options()   # Update the brush selector with the new brush
            brush_preview.content = build_preview_brush()
            self.update()
            update_canvas_tool_preview()

        # Set the blend mode label based on current mode in settings
        def set_blend_mode_value() -> str:
            nonlocal paint_settings
            mode = paint_settings.get('blend_mode', 'src_over')
            if mode is None:
                return f"Blend Mode: None"
            return f"Blend Mode: {mode.replace("_", " ").title()}"
            
        # Get the options for blend modes
        def get_blend_mode_options() -> list[ft.Control]:
            ''' Gets our blend mode options for the popup menu. '''

            return [
                ft.DropdownOption("None", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data=None, leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="No blend mode")),
                ft.DropdownOption("Color", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="color", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Take the hue and saturation of the source image, and the luminosity of the destination image")),
                ft.DropdownOption("Color Burn", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="color_burn", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Divide the inverse of the destination by the source, and inverse the result")),
                ft.DropdownOption("Color Dodge", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="color_dodge", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Divide the destination by the inverse of the source")),
                ft.DropdownOption("Darken", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="darken", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Composite the source and destination image by choosing the lowest value from each color channel")),
                ft.DropdownOption("Difference", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="difference", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Subtract the smaller value from the bigger value for each channel")),
                ft.DropdownOption("Destination", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="dst", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Drop the source image, only paint the destination image")),
                ft.DropdownOption("Destination Atop Source", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="dst_a_top", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Composite the destination image over the source image, but only where it overlaps the source")),
                ft.DropdownOption("Destination In", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="dst_in", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Show the destination image, but only where the two images overlap. The source image is not rendered, it is treated merely as a mask. The color channels of the source are ignored, only the opacity has an effect")),
                ft.DropdownOption("Destination Out", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="dst_out", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Show the destination image, but only where the two images do not overlap. The source image is not rendered, it is treated merely as a mask. The color channels of the source are ignored, only the opacity has an effect")),
                ft.DropdownOption("Destination Over", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="dst_over", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Composite the source image under the destination image")),
                ft.DropdownOption("Exclusion", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="exclusion", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Subtract double the product of the two images from the sum of the two images.")),
                ft.DropdownOption("Hard Light", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="hard_light", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Multiply the components of the source and destination images after adjusting them to favor the source")),
                ft.DropdownOption("Hue", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="hue", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Take the hue of the source image, and the saturation and luminosity of the destination image")),
                ft.DropdownOption("Lighten", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="lighten", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Composite the source and destination image by choosing the highest value from each color channel")),
                ft.DropdownOption("Luminosity", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="luminosity", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Take the luminosity of the source image, and the hue and saturation of the destination image")),
                ft.DropdownOption("Modulate", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="modulate", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Multiply the color components of the source and destination images")),
                ft.DropdownOption("Multiply", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="multiply", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Multiply the components of the source and destination images, including the alpha channel")),
                ft.DropdownOption("Overlay", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="overlay", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Multiply the components of the source and destination images after adjusting them to favor the destination")),
                ft.DropdownOption("Plus", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="plus", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Sum the components of the source and destination images")),
                ft.DropdownOption("Saturation", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="saturation", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Take the saturation of the source image, and the hue and luminosity of the destination image")),
                ft.DropdownOption("Screen", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="screen", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Multiply the inverse of the components of the source and destination images, and inverse the result")),
                ft.DropdownOption("Soft Light", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="soft_light", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Somewhere between Overlay and Color blend modes")),
                ft.DropdownOption("Source", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="src", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Drop the destination image, only paint the source image")),
                ft.DropdownOption("Soure Atop Destination", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="src_a_top", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Composite the source image over the destination image, but only where it overlaps the destination")),
                ft.DropdownOption("Source In", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="src_in", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Show the source image, but only where the two images overlap. The destination image is not rendered, it is treated merely as a mask. The color channels of the destination are ignored, only the opacity has an effect")),
                ft.DropdownOption("Source Out", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="src_out", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Show the source image, but only where the two images do not overlap. The destination image is not rendered, it is treated merely as a mask. The color channels of the destination are ignored, only the opacity has an effect")),
                ft.DropdownOption("XOR", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="xor", leading_icon=ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.PRIMARY, scale=0.8, tooltip="Apply a bitwise xor operator to the source and destination images. This leaves transparency where they would overlap")),
            ]
        
        # Updates the blend mode of the current paint settings
        def update_paint_blend_mode(e: ft.Event[ft.Dropdown]):
            nonlocal paint_settings
            mode = e.control.data
            paint_settings.update({"blend_mode": mode})
            app.settings.update_data(**{"paint_settings": paint_settings})
            self.update()
            update_canvas_tool_preview()

        
        # Returns a list of our controls for for the brush selector for settings, save, and custom brushes
        def get_brush_options() -> list[ft.Control]:
            # Default brush settings to creating non-custom brushes
            default_brush_settings = {
                'color': "#FFFFFF",   
                'stroke_width': 3,
                'style': "stroke",
                'stroke_cap': "round",
                'stroke_join': "round",
                'stroke_miter_limit': 10, 
                'stroke_dash_pattern': None,
                'anti_alias': True,
                'blur_image': 0,
                'blend_mode': "src_over",
            }
            # Settings for default shadow brush
            shadow_brush_settings = {
                'color': "#40000000",   
                'stroke_width': 20,
                'style': "stroke",
                'stroke_cap': "round",
                'stroke_join': "round",
                'stroke_miter_limit': 10, 
                'stroke_dash_pattern': None,
                'anti_alias': True,
                'blur_image': 10,
            }
            # Button to save current paint settings as a custom brush
            save_custom_brush_button = ft.IconButton(      
                ft.Icons.SAVE_ROUNDED, ft.Colors.PRIMARY,
                tooltip="Save current brush settings as a custom brush", 
                on_click=save_custom_brush_clicked, mouse_cursor=ft.MouseCursor.CLICK,
                #margin=ft.Margin.only(right=4),
                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, #bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    shape=ft.RoundedRectangleBorder(radius=4), padding=ft.Padding.all(0)),
            )  
            # Width/Size of brush
            width_slider = ft.Slider(
                min=1, max=100, tooltip="The size of your brush strokes.", expand=True,
                divisions=99, value=paint_settings.get('stroke_width', 5),
                label="Brush Size: {value}px",
                on_change_end=update_paint_width
            )

            # Blur strength of the brush strokes
            blur_slider = ft.Slider(
                min=0, max=50,  tooltip="The blur effect of your brush strokes.", expand=True,
                divisions=50, value=paint_settings.get('blur_image', 0),
                label="Stroke Blur: {value}",  
                on_change_end=update_paint_blur
            )

            # Whether to fill strokes and shapes or not
            fill_switch = ft.Switch(
                True, "Fill Paint", on_change=update_paint_fill,
                label_text_style=ft.TextStyle(color=ft.Colors.ON_SURFACE_VARIANT, ),
                value=paint_settings.get('style', 'stroke').endswith('_fill'),
                tooltip="Whether to fill strokes and shapes, or leave them hollow (Transparent). Forces brush smoothing",
                #label_position=ft.LabelPosition.LEFT
            )
    
            # If we use anti aliasing or not
            anti_alias_switch = Switch(
                True, "Anti-Aliasing", on_change=update_paint_anti_alias,
                value=paint_settings.get('anti_alias', True),
                tooltip="Whether to use anti-aliasing for smoother brush strokes. Disabling may result in jagged edges",
            )

            # Selector for the shape of the ends of strokes
            stroke_cap_dropdown = Dropdown(
                label="Stroke Cap Shape",
                value=paint_settings.get('stroke_cap', 'butt').capitalize(),
                leading_icon=get_stroke_cap_icon(), 
                tooltip="The shape that your brush strokes will have at the end of each line segment.",
                on_select=update_paint_stroke_cap,
                options=[
                    ft.DropdownOption("Butt", "Butt",  leading_icon=ft.Icons.SQUARE_ROUNDED, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, icon_color=ft.Colors.PRIMARY),),
                    ft.DropdownOption("Round", "Round", leading_icon=ft.Icons.CIRCLE, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, icon_color=ft.Colors.PRIMARY),),
                    ft.DropdownOption("Square", "Square", leading_icon=ft.Icons.SQUARE, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, icon_color=ft.Colors.PRIMARY),),
                ]
            )
    
           

            stroke_join_dropdown = Dropdown(
                label="Stroke Join Shape",
                value=paint_settings.get('stroke_join', 'butt').capitalize(),
                leading_icon=get_stroke_join_icon(), 
                tooltip="The shape that your brush strokes will have at sharp turns and corners.",
                on_select=update_paint_stroke_join,
                options=[
                    ft.DropdownOption("Miter", "Miter",  leading_icon=ft.Icons.SQUARE_ROUNDED, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, icon_color=ft.Colors.PRIMARY),),
                    ft.DropdownOption("Round", "Round", leading_icon=ft.Icons.CIRCLE, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, icon_color=ft.Colors.PRIMARY),),
                    ft.DropdownOption("Bevel", "Bevel", leading_icon=ft.Icons.SQUARE, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, icon_color=ft.Colors.PRIMARY),),
                ]
            )
    
            # Selector for the blend mode of the brush strokes
            blend_mode_dropdown = Dropdown(
                label="Blend Mode",
                value=set_blend_mode_value(),
                leading_icon=ft.Icon(ft.Icons.LENS_BLUR, ft.Colors.PRIMARY),
                tooltip="The Current blend effects applied to your brush strokes.",
                on_select=update_paint_blend_mode,
                options=get_blend_mode_options()
            )


            # Start by building our default brush options
            ctrls = [
                ft.Row([
                    ft.Text("Brush Settings", color=ft.Colors.ON_SURFACE_VARIANT, italic=True, expand=True),   
                    save_custom_brush_button
                ], margin=ft.Margin.only(left=4)),

                ft.Row([
                    ft.Text("Brush Preview", color=ft.Colors.ON_SURFACE_VARIANT,),
                    brush_preview,
                ], margin=ft.Margin.only(left=8)),

                # Slider about the width of the current brush strokes
                ft.Row([ft.Text("Size", color=ft.Colors.ON_SURFACE_VARIANT, ), width_slider], spacing=0, tooltip="Size of your strokes", margin=ft.Margin.only(left=8)),      # Size slider

                # Slider about the blur of the current brush strokes
                ft.Row([ft.Text("Blur", color=ft.Colors.ON_SURFACE_VARIANT, ), blur_slider], spacing=0, margin=ft.Margin.only(left=8)),

                fill_switch, 
                anti_alias_switch,

                stroke_cap_dropdown,
                stroke_join_dropdown,
                blend_mode_dropdown,

                ft.Divider(),

                #ft.Text("Default Brushes", color=ft.Colors.ON_SURFACE_VARIANT, italic=True, margin=ft.Margin.only(left=8), expand=True),   
                ft.Text("Saved Brushes", color=ft.Colors.ON_SURFACE_VARIANT, italic=True, margin=ft.Margin.only(left=8)),
                ft.MenuItemButton(
                    data=default_brush_settings,
                    content=ft.Container(
                        ft.Row([ft.Text("Default", expand=True, overflow=ft.TextOverflow.ELLIPSIS), build_preview_brush(default_brush_settings)], spacing=20),
                        clip_behavior=ft.ClipBehavior.HARD_EDGE
                    ),
                    on_click=lambda _: set_active_brush(default_brush_settings, name="Default"),
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor=ft.MouseCursor.CLICK),
                ),    
                ft.MenuItemButton(
                    data=default_brush_settings,
                    content=ft.Container(
                        ft.Row([ft.Text("Shadow", expand=True, overflow=ft.TextOverflow.ELLIPSIS), build_preview_brush(shadow_brush_settings)], spacing=20),
                        clip_behavior=ft.ClipBehavior.HARD_EDGE
                    ),
                    on_click=lambda _: set_active_brush(shadow_brush_settings, name="Shadow"),
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor=ft.MouseCursor.CLICK),
                ),        
                    

                #ft.Divider(),   # Placeholder for shapes section
                   # Placeholder for shapes section
            ]

            # Go through our saved brushes and add options to select them
            for name, brush_settings in app.settings.data.get('canvas_settings', {}).get('saved_brushes', {}).items():
                ctrls.append(
                    ft.MenuItemButton(
                        data=brush_settings,
                        content=ft.Container(
                            ft.Row([ft.Text(name.capitalize(), expand=True, overflow=ft.TextOverflow.ELLIPSIS), build_preview_brush(brush_settings)], spacing=20),
                            clip_behavior=ft.ClipBehavior.HARD_EDGE
                        ),
                        on_click=lambda _, bs=brush_settings, n=name: set_active_brush(bs, n),
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor=ft.MouseCursor.CLICK),
                    )
                )

            ctrls.append(ft.MenuItemButton(
                "Close Brush Settings", close_on_click=True, on_click=lambda: None,
                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.ERROR, shape=ft.RoundedRectangleBorder(radius=4))))
            return ctrls

        def get_text_options() -> list[ft.Control]:

            # Updating standard text settings
            def update_text_setting(e: ft.Event[ft.TextField | Dropdown | ft.Slider | Switch]):
                nonlocal text_settings

                if isinstance(e.control, Dropdown):
                    value = e.control.value.lower()

                elif isinstance(e.control, Switch):
                    if e.control.data == "weight":
                        value = "bold" if e.control.value else "normal"
                    elif e.control.data == "italic":
                        value = e.control.value

                key = e.control.data
                text_settings.update({key: value})
                app.settings.update_data(**{"text_settings": text_settings})

                text_preview.style = ft.TextStyle(**text_settings)
                text_preview.update()
                update_canvas_tool_preview()

            # Update text shadow settings
            def update_text_shadow_setting(e: ft.Event[ft.TextField | ft.Dropdown | ft.Slider | ft.Switch]):
                nonlocal text_settings

            # Update text foreground settings
            def update_text_foreground_setting(e: ft.Event[ft.TextField | ft.Dropdown | ft.Slider | ft.Switch]):
                nonlocal text_settings
                

            # TODO: Have update any option re-set the controls inside

            ft.TextStyle()

            # color - color picker
            # bgcolor - color picker

            # size - slider
            # letter_spacing - slider
            # word_spacing - slider

            # decoration options - exptile with
                # decoration - dropdown
                # decoration_style - dropdown
                # decoration_color - color picker
                # decoration_thickness - slider
                
            # shadow - ExpansionTile w/ lot of other options
                # blur radius - slider
                # blur style - dropdown
                # color - color picker
                # offset - x/y sliders ??
                # spread radius - slider

            # foregound - ExpansionTile w/ lot of other options (call outline??)
                #'color': "white",     # Hex color folowed by opacity
                #'stroke_width': 3,          # Size of the strokees
                #'style': "stroke",          # style of the strokes. Either stroke or fill
                #'stroke_cap': "round",      # Each end of the strokes shape
                #'stroke_join': "round",     # How corners between strokes are drawn
                #'stroke_miter_limit': 10, 
                #'stroke_dash_pattern': None,         # If we should use dashed lines, and the pattern for them
                #'anti_alias': True,     # Use anti aliasing for smoother strokes or not
                #'blur_image': 0,        # How much blur to apply to the stroke
                #'blend_mode': None,     # Any blend mode to apply to the stroke, or None for normal

            baseline_dd = Dropdown(
                label="Baseline",
                value=text_settings.get('baseline', 'alphabetic').capitalize(),
                tooltip="The shape that your brush strokes will have at the end of each line segment.",
                on_select=update_text_setting,
                data="baseline",
                options=[
                    ft.DropdownOption("Alphabetic", "Alphabetic", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),),
                    ft.DropdownOption("Ideographic", "Ideographic", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),),
                ]
            )

            font_family_dd = Dropdown(
                label="Font Family",
                value=text_settings.get('font_family', 'Arial'),
                tooltip="The font family to use for text shapes.",
                on_select=update_text_setting,
                data="font_family",
                options=[
                    ft.DropdownOption("Arial", "Arial", style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),),
                ]
            )


            bold_switch = Switch(
                True, "Bold", on_change=update_text_setting,
                value=text_settings.get('weight', 'normal').lower() == "bold",
                data="weight",
            )

            italic_switch = Switch(
                True, "Italic", on_change=update_text_setting,
                value=text_settings.get('italic', False),
                data="italic",
            )

            # 'text_settings': {
            #'size': 14,
            #'weight': "normal",  # Options: None, w100, w200, w300, w400, w500, w600, w700, w800, w900, bold
            #'italic': False,
            #'decoration': None,  # Options: none, underline, overline, line_through
            #'decoration_color': "#000000",
            #'decoration_thickness': 1.0,
            #'decoration_style': "solid",    # options: solid, wavy, double, dotted, dashed
            #'font_family': "Arial",
            #'color': "#FFFFFF",
            #'bgcolor': "#00000000",  # Background color for text shapes
            #'shadow': {
                #'blur_radius': 0,
                #'blur_style': 'normal', # Options: normal, solid, outer, inner
                #'color': "black",
                #'offset': (0, 0),
                #'spread_radius': 0,
            #},   # Boxshad values
            #'foreground': {
                #'color': "white",     # Hex color folowed by opacity
                #'stroke_width': 3,          # Size of the strokees
                #'style': "stroke",          # style of the strokes. Either stroke or fill
                #'stroke_cap': "round",      # Each end of the strokes shape
                #'stroke_join': "round",     # How corners between strokes are drawn
                #'stroke_miter_limit': 10, 
                #'stroke_dash_pattern': None,         # If we should use dashed lines, and the pattern for them
                #'anti_alias': True,     # Use anti aliasing for smoother strokes or not
                #'blur_image': 0,        # How much blur to apply to the stroke
                #'blend_mode': None,     # Any blend mode to apply to the stroke, or None for normal
            #},      
            #'letter_spacing': 0,
            #'word_spacing': 0,
            #'baseline': "alphabetic",  # How text is rendered - Options: alphabetic or ideographic
        #},






            return [
                ft.Text("Text & Shape Settings", color=ft.Colors.ON_SURFACE_VARIANT, italic=True, expand=True),  
                ft.Row([
                    ft.Container(text_preview, expand=True, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH, alignment=ft.Alignment.CENTER, border_radius=4, padding=ft.Padding.all(10))
                ]),

                #baseline_dd, Not needed
                font_family_dd, # TODO: Add fonts still
                
                bold_switch,  
                italic_switch,


            ]
            


        # Grab our data for easier manipulation
        paint_settings = app.settings.data.get('paint_settings', {}).copy()
        canvas_settings = app.settings.data.get('canvas_settings', {}).copy()
        text_settings = app.settings.data.get('text_settings', {}).copy()

        # Color picker for changing brush color
        color_picker = ColorPicker(
            color=paint_settings.get('color', "#000000").split(",", 1)[0], 
            on_color_change=set_color, 
            scale=.8, 
            picker_area_border_radius=ft.BorderRadius.all(4)
        )   

        # Create our color selector button
        color_selector = ft.SubmenuButton(
            ft.Icon(ft.Icons.CIRCLE, app.settings.data.get('paint_settings', {}).get('color', ft.Colors.PRIMARY)), 
            tooltip="The color of your brush strokes.",
            on_close=save_color, expand=True,
            margin=ft.Margin.only(right=20),
            width=40,
            controls=[ft.Column([
                color_picker,  
                ft.MenuItemButton(
                    "Set Color", 
                    on_click=lambda: None,  # Something so its not disabled
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=4), #mouse_cursor=ft.MouseCursor.CLICK,
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
                    )
                )
            ])],
            style=ft.ButtonStyle(
                #mouse_cursor=ft.MouseCursor.CLICK,  
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                shape=ft.RoundedRectangleBorder(radius=4),
            ),
            menu_style=ft.MenuStyle(
                alignment=ft.Alignment.BOTTOM_LEFT,
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, 
                shape=ft.RoundedRectangleBorder(radius=4),
                padding=ft.Padding.all(0)
            ),
        )

        # Button to set the control mode to draw mode
        set_draw_mode_button = ft.IconButton(
            ft.Icons.BRUSH_ROUNDED if app.settings.data.get('canvas_settings', {}).get('current_control_mode', 'draw') == "draw" else ft.Icons.BRUSH_OUTLINED,
            ft.Colors.PRIMARY,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if app.settings.data.get('canvas_settings', {}).get('current_control_mode', 'draw') == "draw" else None,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0)),
            tooltip="Set the active control to the last used brush",
            data="draw", on_click=set_draw_mode
        )

        brush_preview = ft.Container(build_preview_brush(), expand=True, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH, alignment=ft.Alignment.CENTER, border_radius=4)
            
        # Selector to choose a build in brush or a custom brush
        brush_selector = ft.SubmenuButton(
            #build_preview_brush(paint_settings),
            controls=get_brush_options(),
            content=ft.Icon(ft.Icons.ARROW_DROP_DOWN, ft.Colors.ON_SURFACE_VARIANT, scale=0.8),
            style=ft.ButtonStyle(
                #mouse_cursor=ft.MouseCursor.CLICK,  
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if app.settings.data.get('canvas_settings', {}).get('current_control_mode', '') == "draw" else None,
                shape=ft.RoundedRectangleBorder(radius=0),
                padding=ft.Padding.all(0),
            ),
            menu_style=ft.MenuStyle(
                alignment=ft.Alignment.BOTTOM_LEFT,
                bgcolor=ft.Colors.SURFACE_CONTAINER, 
                shape=ft.RoundedRectangleBorder(radius=4),
                padding=ft.Padding.all(0)
            ),
            expand=True,
            width=30,
        )

        

        # Button to set the control mode to tool mode
        set_tool_mode_button = ft.IconButton(
            update_tool_icon(),
            ft.Colors.PRIMARY,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if app.settings.data.get('canvas_settings', {}).get('current_control_mode', 'draw') == "tool" else None,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0)),
            tooltip="Set the active control to the last used tool",
            data="tool", on_click=set_tool_mode
        )

        # Selector to choose a tool to use on the canvas
        tool_selector = ft.SubmenuButton(
            controls=get_tool_options(),
            content=ft.Icon(ft.Icons.ARROW_DROP_DOWN, ft.Colors.ON_SURFACE_VARIANT, scale=0.8),
            style=ft.ButtonStyle(
                #mouse_cursor=ft.MouseCursor.CLICK,  
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if app.settings.data.get('canvas_settings', {}).get('current_control_mode', '') == "tool" else None,
                shape=ft.RoundedRectangleBorder(radius=0),
                padding=ft.Padding.all(0),
            ),
            menu_style=ft.MenuStyle(
                alignment=ft.Alignment.BOTTOM_LEFT,
                bgcolor=ft.Colors.SURFACE_CONTAINER, 
                shape=ft.RoundedRectangleBorder(radius=4),
                padding=ft.Padding.all(0)
            ),
            expand=True,
            width=30,
        )

        text_preview = ft.Text("Preview text", selectable=True, style=ft.TextStyle(**text_settings))

        text_settings_button = ft.SubmenuButton(
            controls=get_text_options(),
            content=ft.Icon(ft.Icons.TEXT_FIELDS, ft.Colors.PRIMARY),
            style=ft.ButtonStyle(
                #mouse_cursor=ft.MouseCursor.CLICK,  
                shape=ft.RoundedRectangleBorder(radius=4),
                padding=ft.Padding.all(0),
                #bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
            ),
            menu_style=ft.MenuStyle(
                alignment=ft.Alignment.BOTTOM_LEFT,
                bgcolor=ft.Colors.SURFACE_CONTAINER, 
                shape=ft.RoundedRectangleBorder(radius=4),
                padding=ft.Padding.all(0)
            ),
            expand=True,
            width=40,
        )

        
        # Strength path smoothing effect
        stroke_smoothing_strength_slider = ft.Slider(
            min=1, max=10,  expand=True,
            divisions=10, value=canvas_settings.get('stroke_smoothing_strength', 1),
            label="Strength: {value}",
            on_change_end=update_paint_stroke_smoothing_strength,
            tooltip="The strength of the stroke smoothing effect. Higher values will make strokes appear smoother and more natural",
        )

        # Toggles path smoothing
        brush_smoothing_switch =  ft.Switch(
            True, "Brush Smoothing", on_change=update_paint_brush_smoothing,
            label_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=12),
            value=canvas_settings.get('use_brush_smoothing', True),
            tooltip="Makes the brushes paint color appear consistant for an entire stroke, especially at lower opacity values.",
        )

       

        
          

# TODO: 
# Add fonts and shadow options
# Font outline colors
# Build in dialoge bubbles shapes for dialogue (up-left, up-right, down-left, down-right, middle-up, middle-down). See canvas example on flet docs, they have one
# -- Both round and normal for above dialogue boxes
        

        # Create our menu bar with submenu items
        drawing_controls = ft.MenuBar(
            #expand=True,
            visible=self.page.platform.is_mobile(),
            style=ft.MenuStyle(     # Styling our menubar
                alignment=ft.Alignment.CENTER,
                bgcolor=ft.Colors.TRANSPARENT,
                shadow_color=ft.Colors.TRANSPARENT,
            ),
            controls=[  # Segment button of draw mode, brush options, and dropdown of saved brushes with option to save current
                
                color_selector,   # Color selector with color picker and option to save color to settings


                ft.Container(
                    set_draw_mode_button,
                    border_radius=ft.BorderRadius.only(top_left=4, bottom_left=4),
                ),

                ft.Container(
                    brush_selector,    
                    border_radius=ft.BorderRadius.only(top_right=4, bottom_right=4),
                    margin=ft.Margin.only(right=20)
                ),
                
                ft.Container(
                    set_tool_mode_button,
                    border_radius=ft.BorderRadius.only(top_left=4, bottom_left=4),
                ),
                ft.Container(
                    tool_selector,     
                    border_radius=ft.BorderRadius.only(top_right=4, bottom_right=4),
                    margin=ft.Margin.only(right=20)
                ),

                ft.MenuBar([text_settings_button], style=ft.MenuStyle(bgcolor="transparent", shadow_color="transparent", padding=ft.Padding.all(0))),

                

                # Text editor
            ], 
        )

        self.content = ft.Row(
            spacing=0,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                file_options,    # File options button

                drawing_controls,   # Main drawing controls

                ft.Row([        # Row that has alpha text, info button, and settings button
                    ft.Text(
                        "Alpha", color=ft.Colors.PRIMARY, weight=ft.FontWeight.BOLD, 
                        tooltip="Storyboard is currently in alpha. Bugs are expected. More features coming soon! \nCheck out Settings -> Resources for a list of planned features and known issues. \nJoin the Discord to suggest your features and report bugs."
                    ),  # Feedback button
                    ft.Icon(
                        ft.Icons.INFO_OUTLINED, color=ft.Colors.PRIMARY, scale=.5, 
                        tooltip="Storyboard is currently in alpha. Bugs are expected. More features coming soon! \nCheck out Settings -> Resources for a list of planned features and known issues. \nJoin the Discord to suggest your features and report bugs."
                    ),
                    ft.IconButton(ft.Icons.SETTINGS_OUTLINED, "primary", on_click=_settings_clicked, mouse_cursor=ft.MouseCursor.CLICK),   # Settings button
                ], tight=True, spacing=0)
            ]
        )