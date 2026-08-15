''' UI model file to create our all_workspaces_rail on the left side of the screen.
This object is stored in app.all_workspaces_rail.
Handles new workspace selections, re-ordering, collapsing, and expanding the rail. '''

import flet as ft
from flet_color_pickers import ColorLabelType, ColorPicker, PaletteType
import math
import flet.canvas as cv
from utils.safe_string_checker import return_safe_name
from models.views.story import Story

tool_icons = {
    'brush': ft.Icons.BRUSH_ROUNDED,
    'brush_outlined': ft.Icons.BRUSH_OUTLINED,
    'text': ft.Icons.TEXT_FIELDS,
    'text_outlined': ft.Icons.TEXT_FIELDS_OUTLINED,
    'erase': ft.Icons.AUTO_FIX_NORMAL,
    'erase_outlined': ft.Icons.AUTO_FIX_NORMAL_OUTLINED,
    'fill': ft.Icons.FORMAT_COLOR_FILL,
    'fill_outlined': ft.Icons.FORMAT_COLOR_FILL_OUTLINED,
    'line': ft.Icons.REMOVE,
    'line_outlined': ft.Icons.REMOVE_OUTLINED,
    'circle': ft.Icons.CIRCLE,
    'circle_outlined': ft.Icons.CIRCLE_OUTLINED,
    'oval': ft.Icon(ft.Icons.CIRCLE, ft.Colors.PRIMARY, scale=ft.Scale(scale_x=0.8)),
    'oval_outlined': ft.Icon(ft.Icons.CIRCLE_OUTLINED, ft.Colors.PRIMARY, scale=ft.Scale(scale_x=0.8)),
    'arc': ft.Icon(ft.CupertinoIcons.CIRCLE_RIGHTHALF_FILL, ft.Colors.PRIMARY, rotate=math.pi*1.5),
    'arc_outlined': ft.Icon(ft.CupertinoIcons.CIRCLE_RIGHTHALF_FILL, ft.Colors.PRIMARY, rotate=math.pi/2),
    'rectangle': ft.Icons.RECTANGLE,
    'rectangle_outlined': ft.Icons.RECTANGLE_OUTLINED,
    'triangle': ft.CupertinoIcons.ARROWTRIANGLE_UP_FILL,
    'triangle_outlined': ft.CupertinoIcons.ARROWTRIANGLE_UP,
}

NEGATIVE_NUMBER_FILTER = ft.InputFilter(allow=True, regex_string=r"^-?[0-9]*$")

# Class so we can store our all workspaces rail as an object inside of app
class CanvasRail(ft.Container):
    
    # Constructor for our all_workspaces_rail object. Needs a page reference passed in
    def __init__(self, story: Story):

        self.story = story
       
        # Style our rail (container)
        super().__init__(
            alignment=ft.Alignment.CENTER,  # Aligns content to the 
            padding=ft.Padding.only(bottom=10, right=6, left=6, top=10),
            animate=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            border=ft.Border(right=ft.BorderSide(2, ft.Colors.OUTLINE_VARIANT)),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST
        )


    # Called mostly when re-ordering or collapsing the rail. Also called on start
    def build(self) -> ft.Control:
        from models.app import app   


        class Switch(ft.Switch):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.adaptive=True
                self.label_style=ft.TextStyle(color=ft.Colors.ON_SURFACE_VARIANT, italic=True)
                #self.margin=ft.Margin.only(top=8, left=4, right=4)

        class ExpansionTile(ft.ExpansionTile):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.border_radius=ft.BorderRadius.all(4)
                self.tile_padding=ft.Padding.only(left=0, right=0)
                self.shape = ft.RoundedRectangleBorder(side=ft.BorderSide(color=ft.Colors.OUTLINE_VARIANT), radius=4)
                self.collapsed_shape = ft.RoundedRectangleBorder(radius=4)
                self.title_style=ft.TextStyle(color=ft.Colors.ON_SURFACE_VARIANT, italic=True)
                self.dense=True
                self.margin=ft.Margin.only(left=4, right=4, bottom=4)
                #ft.ExpansionTile()

        class TextField(ft.TextField):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.dense=True
                self.label_style=ft.TextStyle(color=ft.Colors.PRIMARY, italic=True)
                self.border_radius=ft.BorderRadius.all(4)
                #self.content_padding=ft.Padding.only(left=6, right=6, top=4, bottom=4)
                #self.expand=False
                self.multiline=False
                self.text_size=12
                if self.input_filter is None:
                    self.input_filter=ft.NumbersOnlyInputFilter()
                self.margin=ft.Margin.only(top=8, left=4, right=4)
                self.border_color=ft.Colors.OUTLINE_VARIANT
                self.focused_border_color=ft.Colors.PRIMARY

        class UpDownButtons(ft.Column):
            def __init__(self, up_function=None, down_function=None):
                super().__init__(
                    spacing=2,
                    #tight=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.END,
                    margin=ft.Margin.only(right=4),
                    controls=[
                    ft.IconButton(
                        ft.Icons.ARROW_DROP_UP, ft.Colors.PRIMARY, 16, width=20, height=16, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                        style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                        on_click=up_function,
                    ),
                    ft.IconButton(
                        ft.Icons.ARROW_DROP_DOWN, ft.Colors.PRIMARY, 16, width=20, height=16, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                        style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                        on_click=down_function
                    )
                    ]
                )
                
                
        # Updates the mouse cursor or all visible canvases based on updated tool mode
        def set_canvas_mouse_cursor():
            if self.story is None:
                return
            for widget in self.story.workspace.tab_view.controls:
                if not widget.data: # Protect empty
                    return
                if widget.data.get('tag') == "canvas":
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

        # Set the color pickers color upon change, so that saving it goes to right spot
        def set_color(e: ft.Event[ColorPicker]):
            e.control.color = e.data
            

        # Saves our color to data and updates the brush selector
        def save_color(e=None):
            paint_settings.update({"color": color_picker.color})
            app.settings.update_data(**{"paint_settings": paint_settings})
            brush_preview.content = build_preview_brush()   # Update the brush selector with the new brush
            set_tool_mode_button.icon = update_tool_icon()
            color_selector.content.color = color_picker.color
            if color_picker.color not in color_picker.color_history:
                color_picker.color_history.append(color_picker.color)
                if len(color_picker.color_history) > 6:
                    color_picker.color_history.pop(0)
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
            
            brush_preview.content = build_preview_brush()
            set_canvas_mouse_cursor()
            reset_button_bgcolors()
            reset_tool_icons()

            set_draw_mode_button.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
            set_draw_mode_button.icon = tool_icons.get('brush')
            brush_selector.style.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST

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
            if brush_settings.get('blur_image', 0) > 10:
                brush_settings['blur_image'] = 10
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

        def build_preview_text(ts: dict=None) -> ft.Control:
            nonlocal text_settings
            if not ts:
                ts = text_settings.copy()

            text_style = ft.TextStyle(**ts)
            text_control = ft.Text("Preview Text", style=text_style)

            decoration = ts.get('decoration', None)
            match decoration:
                case "underline":
                    text_control.style.decoration = ft.TextDecoration.UNDERLINE
                case "overline":
                    text_control.style.decoration = ft.TextDecoration.OVERLINE
                case "line_through":
                    text_control.style.decoration = ft.TextDecoration.LINE_THROUGH
                case _:
                    text_control.style.decoration = None

            text_control.style.shadow = ft.BoxShadow(
                blur_radius=ts.get('shadow', {}).get('blur_radius', 0),
                color=ts.get('shadow', {}).get('color', None),
                offset=ft.Offset(
                    ts.get('shadow', {}).get('offset_x', 0),
                    ts.get('shadow', {}).get('offset_y', 0)
                ),
            )
            return text_control
        
        # Sets current brush settings using passed in brush settings
        def set_active_brush(brush_settings: dict, name: str):
            nonlocal canvas_settings, paint_settings
            canvas_settings.update({"current_control_mode": {'current_control_mode': "draw", 'current_brush_name': name}})
            paint_settings.update(**brush_settings)
            app.settings.update_data(**{"canvas_settings": canvas_settings, "paint_settings": brush_settings})
            
            brush_preview.content = build_preview_brush()
            brush_selector.controls = get_brush_options()   # Update the brush selector with the new brush
            set_draw_mode()
            self.update()
            set_canvas_mouse_cursor()
            update_canvas_tool_preview()
            
        
        # Sets current text settings using passed in text settings
        def set_active_text_setting(new_text_settings: dict, name: str):
            nonlocal text_settings
            text_settings.clear()
            text_settings.update(**new_text_settings)
            app.settings.update_data(**{"text_settings": text_settings})

            update_text_preview()
            text_settings_button.controls = get_text_options()   # Update the text settings selector with the new setting
            set_text_mode()
            self.update()
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
            nonlocal canvas_settings, paint_settings, brush_selector, tool_selector
            canvas_settings['current_control_mode'] = "tool"
            canvas_settings['current_tool_name'] = e.control.data
            app.settings.update_data(**{'canvas_settings': canvas_settings})
            set_canvas_mouse_cursor()
            
            reset_button_bgcolors()
            reset_tool_icons()
            
            e.control.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
            e.control.icon = tool_icons.get(e.control.data)
            self.update() 

        # Turn off all bgcolors
        def reset_button_bgcolors():
            for ctrl in self.content.controls:
                if isinstance(ctrl, ft.IconButton):
                    ctrl.bgcolor = None
            set_draw_mode_button.bgcolor = None
            brush_selector.style.bgcolor = None
            set_text_mode_button.bgcolor = None
            text_settings_button.style.bgcolor = None

        # Set icons to outlined values
        def reset_tool_icons():
            set_draw_mode_button.icon = tool_icons.get('brush_outlined')
            set_text_mode_button.icon = tool_icons.get('text_outlined')
            erase_tool_button.icon = tool_icons.get('erase_outlined')
            line_tool_button.icon = tool_icons.get('line_outlined')
            circle_tool_button.icon = tool_icons.get('circle_outlined')
            oval_tool_button.icon = tool_icons.get('oval_outlined')
            arc_tool_button.icon = tool_icons.get('arc_outlined')
            rectangle_tool_button.icon = tool_icons.get('rectangle_outlined')
            triangle_tool_button.icon = tool_icons.get('triangle_outlined')


        def set_text_mode(e=None):
            nonlocal canvas_settings, paint_settings, brush_selector, set_tool_mode_button
            canvas_settings['current_control_mode'] = "text"
            app.settings.update_data(**{'canvas_settings': canvas_settings})
            set_text_mode_button.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
            text_settings_button.style.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
            
            set_canvas_mouse_cursor()

            reset_button_bgcolors()
            reset_tool_icons()

            text_settings_button.style.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
            set_text_mode_button.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
            set_text_mode_button.icon = tool_icons.get('text')


            self.update()

        def get_tool_options() -> list[ft.Control]:
            ''' Gets our tool options for the popup menu. '''
    
            return [
                ft.Row([
                    ft.Text("Tools", color=ft.Colors.ON_SURFACE_VARIANT, italic=True),
                ], alignment=ft.MainAxisAlignment.CENTER),   
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
                #ft.MenuItemButton(
                    #ft.Row([
                        #ft.Text("Text", overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                        #ft.Icon(ft.Icons.TEXT_FIELDS, ft.Colors.PRIMARY)
                    #]),
                    #data="text",
                    #on_click=set_active_tool,
                    #style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor=ft.MouseCursor.CLICK),
                    #tooltip="Add text only to your canvas. Useful for labels"
                #),
                
    
                # Shapes we can use
                ft.Divider(), 
                ft.Row([
                    ft.Text("Shapes", color=ft.Colors.ON_SURFACE_VARIANT, italic=True),
                ], alignment=ft.MainAxisAlignment.CENTER),  
                
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
            set_tool_mode(e.control)
            self.update()

        

        # Add fill or not to our style based on teh switch state
        def update_paint_fill(e: ft.Event[ft.Switch]):
            nonlocal paint_settings
            is_fill = e.control.value
            if is_fill:
                paint_settings.update({"style": paint_settings['style'] + "_fill"})
            else:
                paint_settings.update({"style": paint_settings['style'].replace("_fill", "")})
            app.settings.update_data(**{"paint_settings": paint_settings})
            
            brush_preview.content = build_preview_brush()
            self.update()
            update_canvas_tool_preview()

        # Called when changing paint anti-aliasing
        def update_paint_anti_alias(e: ft.Event[ft.Switch]):
            nonlocal paint_settings
            paint_settings.update({"anti_alias": e.control.value})
            app.settings.update_data(**{"paint_settings": paint_settings})
            
            brush_preview.content = build_preview_brush()
            self.update()
            update_canvas_tool_preview()

        # Updates whether we'll use path smoothing or not
        def update_paint_brush_smoothing(e: ft.Event[ft.Switch]):
            nonlocal canvas_settings
            canvas_settings.update(**{"use_brush_smoothing": e.control.value})
            app.settings.update_data(**{"canvas_settings": canvas_settings})

        # Updates the strength of the smooth stroke effect
        def update_paint_stroke_smoothing_strength(e: ft.Event[ft.Slider]):
            nonlocal canvas_settings
            canvas_settings.update(**{"stroke_smoothing_strength": e.control.value})
            app.settings.update_data(**{"canvas_settings": canvas_settings})

        # Returns the correct icon for the current stroke cap setting based on current paint settings
        def get_stroke_cap_icon() -> ft.Icon:
            nonlocal paint_settings
            stroke_cap = paint_settings.get('stroke_cap', 'butt')
            if stroke_cap == 'round': return ft.Icon(ft.Icons.CIRCLE, ft.Colors.PRIMARY)
            elif stroke_cap == 'square':return ft.Icon(ft.Icons.SQUARE, ft.Colors.PRIMARY)
            else: return ft.Icon(ft.Icons.SQUARE_ROUNDED, ft.Colors.PRIMARY)

        # Updates the stroke cap of the current paint
        def update_paint_stroke_cap(e: ft.Event[ft.RadioGroup]):
            nonlocal paint_settings
            new_stroke_cap = e.control.value.lower()
            paint_settings['stroke_cap'] = new_stroke_cap
            app.settings.update_data(**{"paint_settings": {"stroke_cap": new_stroke_cap}})
            e.control.content.leading = get_stroke_cap_icon()
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
        async def update_paint_stroke_join(e: ft.Event[ft.RadioGroup]):
            nonlocal paint_settings
            new_stroke_join = e.control.value.lower()
            paint_settings['stroke_join'] = new_stroke_join
            app.settings.update_data(**{"paint_settings": {"stroke_join": new_stroke_join}})
            e.control.content.leading = get_stroke_join_icon()
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
                ft.Radio("None", value="src_over", tooltip="No blend mode"),
                ft.Radio("Color", value="color", tooltip="Take the hue and saturation of the source image, and the luminosity of the destination image"),
                ft.Radio("Color Burn", value="color_burn", tooltip="Divide the inverse of the destination by the source, and inverse the result"),
                ft.Radio("Color Dodge", value="color_dodge", tooltip="Divide the destination by the inverse of the source"),
                ft.Radio("Darken", value="darken", tooltip="Composite the source and destination image by choosing the lowest value from each color channel"),
                ft.Radio("Difference", value="difference", tooltip="Subtract the smaller value from the bigger value for each channel"),
                ft.Radio("Destination", value="dst", tooltip="Drop the source image, only paint the destination image"),
                ft.Radio("Destination Atop Source", value="dst_a_top", tooltip="Composite the destination image over the source image, but only where it overlaps the source"),
                ft.Radio("Destination In", value="dst_in", tooltip="Show the destination image, but only where the two images overlap. The source image is not rendered, it is treated merely as a mask. The color channels of the source are ignored, only the opacity has an effect"),
                ft.Radio("Destination Out", value="dst_out", tooltip="Show the destination image, but only where the two images do not overlap. The source image is not rendered, it is treated merely as a mask. The color channels of the source are ignored, only the opacity has an effect"),
                ft.Radio("Destination Over", value="dst_over", tooltip="Composite the source image under the destination image"),
                ft.Radio("Exclusion", value="exclusion", tooltip="Subtract double the product of the two images from the sum of the two images."),
                ft.Radio("Hard Light", value="hard_light", tooltip="Multiply the components of the source and destination images after adjusting them to favor the source"),
                ft.Radio("Hue", value="hue", tooltip="Take the hue of the source image, and the saturation and luminosity of the destination image"),
                ft.Radio("Lighten", value="lighten", tooltip="Composite the source and destination image by choosing the highest value from each color channel"),
                ft.Radio("Luminosity", value="luminosity", tooltip="Take the luminosity of the source image, and the hue and saturation of the destination image"),
                ft.Radio("Multiply", value="multiply", tooltip="Multiply the components of the source and destination images"),
                ft.Radio("Overlay", value="overlay", tooltip="Multiply the components of the source and destination images after adjusting them to favor the destination"),
                ft.Radio("Saturation", value="saturation", tooltip="Take the saturation of the source image, and the hue and luminosity of the destination image"),
                ft.Radio("Screen", value="screen", tooltip="Multiply the inverse of the components of the source and destination images, and then inverse the result"),
                ft.Radio("Soft Light", value="soft_light", tooltip="Multiply the components of the source and destination images after adjusting them to favor the destination"),
                ft.Radio("Source", value="src", tooltip="Drop the destination image, only paint the source image"),
                ft.Radio("Source Atop Destination", value="src_a_top", tooltip="Composite the source image over the destination image, but only where it overlaps the destination"),
                ft.Radio("Source In", value="src_in", tooltip="Show the source image, but only where the two images overlap. The destination image is not rendered, it is treated merely as a mask. The color channels of the destination are ignored, only the opacity has an effect"),
                ft.Radio("Source Out", value="src_out", tooltip="Show the source image, but only where the two images do not overlap. The destination image is not rendered, it is treated merely as a mask. The color channels of the destination are ignored, only the opacity has an effect"),
                ft.Radio("Source Over", value="src_over", tooltip="Composite the destination image under the source image"),
                ft.Radio("Xor", value="xor", tooltip="Composite the source and destination images by showing the non-overlapping parts of both images"),
            ]
                
        
        # Updates the blend mode of the current paint settings
        def update_paint_blend_mode(e: ft.Event[ft.RadioGroup]):
            nonlocal paint_settings
            mode = e.control.value
            paint_settings.update(**{"blend_mode": mode})
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
                on_click=save_custom_brush_clicked,
                #margin=ft.Margin.only(right=4),
                style=ft.ButtonStyle( #bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    shape=ft.RoundedRectangleBorder(radius=4), padding=ft.Padding.all(0)),
            )  
            

            def update_tf(e: ft.Event[ft.TextField]):
                nonlocal paint_settings
                # If less than 0, reset to the value it was
                if not e.control.value.strip():
                    e.control.value = str(text_settings.get(e.control.data, 10))
                    e.control.update()
                    return

                # Make sure value within bounds
                clamp_bounds = 50 if e.control.data == "blur_image" else 100
                if e.control.data == "stroke_smoothing_strength":
                    clamp_bounds = 10
                value = int(max(min(int(e.control.value), clamp_bounds), 0))
                e.control.value = str(value)    # Reupdate clamped value
                e.control.update()

                key = e.control.data
                paint_settings.update({key: value})
                if e.control.data != "stroke_smoothing_strength":
                    app.settings.update_data(**{"paint_settings": paint_settings})
                else:
                    canvas_settings.update(**{"stroke_smoothing_strength": value})
                    app.settings.update_data(**{"canvas_settings": canvas_settings})

                brush_preview.content = build_preview_brush()

                self.update()
                set_canvas_mouse_cursor()
                update_canvas_tool_preview()
                


            # Increase the value (clamped) and pass the event along for settings
            def increate_tf_value(e: ft.Event[TextField]):
                current_val = int(e.control.parent.parent.value)
                clamp_bounds = 50 if e.control.parent.parent.data == "blur_image" else 100
                if e.control.parent.parent.data == "stroke_smoothing_strength":
                    clamp_bounds = 10
                new_val = min(current_val + 1, clamp_bounds)
                e.control.parent.parent.value = str(new_val)
                update_tf(ft.Event(name="click", control=e.control.parent.parent, data=e.control.parent.parent.data))

            # Decrease the value (clamped) and pass the event along for settings
            def decrease_tf_value(e: ft.Event[TextField]):
                current_val = int(e.control.parent.parent.value)
                new_val = max(current_val - 1, 0)
                e.control.parent.parent.value = str(new_val)
                update_tf(ft.Event(name="click", control=e.control.parent.parent, data=e.control.parent.parent.data))

            
            width_tf = TextField(
                label="Size (0-100)", value=str(paint_settings.get('stroke_width', 5)), 
                on_blur=update_tf, data="stroke_width", input_filter=ft.NumbersOnlyInputFilter(),
                suffix_icon=UpDownButtons(increate_tf_value, decrease_tf_value),
            )

            blur_tf = TextField(
                label="Blur Strength (0-50)", value=str(paint_settings.get('blur_image', 0)),
                on_blur=update_tf, data="blur_image", input_filter=ft.NumbersOnlyInputFilter(),
                suffix_icon=UpDownButtons(increate_tf_value, decrease_tf_value),
            )

            stroke_smoothing_tf = TextField(
                label="Stroke Smoothing Strength (0-10)", value=str(canvas_settings.get('stroke_smoothing_strength', 1)),
                on_blur=update_tf, data="stroke_smoothing_strength", input_filter=ft.NumbersOnlyInputFilter(),
                suffix_icon=UpDownButtons(increate_tf_value, decrease_tf_value),
            )

            
            # Whether to fill strokes and shapes or not
            fill_switch = Switch(
                label="Fill Paint", on_change=update_paint_fill,
                value=paint_settings.get('style', 'stroke').endswith('_fill'),
                tooltip="Whether to fill strokes and shapes, or leave them hollow (Transparent). Forces brush smoothing",
            )
    
            # If we use anti aliasing or not
            anti_alias_switch = Switch(
                label="Anti-Aliasing", on_change=update_paint_anti_alias,
                value=paint_settings.get('anti_alias', True),
                tooltip="Whether to use anti-aliasing for smoother brush strokes. Disabling may result in jagged edges",
            )

            brush_smoothing_switch = Switch(
                label="Brush Smoothing", on_change=update_paint_brush_smoothing,
                value=canvas_settings.get('use_brush_smoothing', True),
                tooltip="Whether to smooth brush strokes to have a uniform color and opacity.",
                
            )

            # Selector for the shape of the ends of strokes
            stroke_cap_rg = ft.RadioGroup(
                content=ExpansionTile(
                    title="Stroke Cap Shape",
                    leading=get_stroke_cap_icon(),
                    tooltip="The shape that your brush strokes will have at the ends of lines.",
                    controls=[
                        ft.Radio(key.capitalize(), value=key) for key in ("butt", "round", "square")
                    ]
                ),
                value=paint_settings.get('stroke_cap', 'butt'),
                on_change=update_paint_stroke_cap,
            )
    
            

            
            stroke_join_rg = ft.RadioGroup(
                content=ExpansionTile(
                    title="Stroke Join Shape",
                    tooltip="The shape that your brush strokes will have at sharp turns and corners.",
                    leading=get_stroke_join_icon(),
                    controls=[
                        ft.Radio(key.capitalize(), value=key) for key in ("miter", "round", "bevel")
                    ]
                ),
                value=paint_settings.get('stroke_join', 'miter'),
                on_change=update_paint_stroke_join,
            )
    
            
            blend_mode_rg = ft.RadioGroup(
                content=ExpansionTile(
                    title="Blend Mode",
                    tooltip="The blend effects applied to your brush strokes.",
                    leading=ft.Icon(ft.Icons.LENS_BLUR, ft.Colors.PRIMARY),
                    controls=get_blend_mode_options()
                ),
                value=paint_settings.get('blend_mode', 'src_over'),
                on_change=update_paint_blend_mode,
            )

            def highlight_option(e: ft.Event[ft.GestureDetector]):
                e.control.content.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
                e.control.update()
            def stop_highlight_option(e: ft.Event[ft.GestureDetector]):
                e.control.content.bgcolor = ft.Colors.TRANSPARENT
                e.control.update()
            


            # Start by building our default brush options
            ctrls = [
                ft.Row([
                    ft.Text("Brush Settings", color=ft.Colors.ON_SURFACE_VARIANT, italic=True),   
                    save_custom_brush_button
                ], margin=ft.Margin.only(left=4), alignment=ft.MainAxisAlignment.CENTER),

                ft.Row([
                    ft.Text("Brush Preview", color=ft.Colors.ON_SURFACE_VARIANT,),
                    brush_preview,
                ], margin=ft.Margin.only(left=8)),

                # Slider about the width of the current brush strokes
                #ft.Row([ft.Text("Size", color=ft.Colors.ON_SURFACE_VARIANT, ), width_slider], spacing=0, tooltip="Size of your strokes", margin=ft.Margin.only(left=8)),      # Size slider

                # Slider about the blur of the current brush strokes
                #ft.Row([ft.Text("Blur", color=ft.Colors.ON_SURFACE_VARIANT, ), blur_slider], spacing=0, margin=ft.Margin.only(left=8)),


                width_tf,
                blur_tf,
                #stroke_smoothing_tf,

                ft.Row([
                    brush_smoothing_switch,
                    ft.Icon(ft.Icons.INFO_OUTLINED, ft.Colors.OUTLINE, scale=0.6, tooltip="Long brush strokes with no break will cause performance issues.")
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER, margin=ft.Margin.only(top=8), spacing=0),
                ft.Container(height=8),  # Spacer
                fill_switch, 
                anti_alias_switch,
                

                stroke_cap_rg,
                stroke_join_rg,
                blend_mode_rg,

                ft.Divider(),

                #ft.Text("Default Brushes", color=ft.Colors.ON_SURFACE_VARIANT, italic=True, margin=ft.Margin.only(left=8), expand=True),   
                ft.Row([
                    ft.Text("Saved Brushes", color=ft.Colors.ON_SURFACE_VARIANT, italic=True),
                ], alignment=ft.MainAxisAlignment.CENTER),  
     
                ft.GestureDetector(
                    ft.Container(
                        ft.Row([ft.Text("Default", expand=True, overflow=ft.TextOverflow.ELLIPSIS), build_preview_brush(default_brush_settings)], spacing=20),
                        clip_behavior=ft.ClipBehavior.HARD_EDGE, border_radius=4, padding=ft.Padding.only(left=10, right=10)
                    ),
                    data=default_brush_settings,
                    on_tap=lambda _: set_active_brush(default_brush_settings, name="Default"),
                    on_enter=highlight_option,
                    on_exit=stop_highlight_option
                ),    
                ft.GestureDetector(
                    ft.Container(
                        ft.Row([ft.Text("Shadow", expand=True, overflow=ft.TextOverflow.ELLIPSIS), build_preview_brush(shadow_brush_settings)], spacing=20),
                        clip_behavior=ft.ClipBehavior.HARD_EDGE, border_radius=4, padding=ft.Padding.only(left=10, right=10)
                    ),
                    data=shadow_brush_settings,
                    on_tap=lambda _: set_active_brush(shadow_brush_settings, name="Shadow"),
                    on_enter=highlight_option,
                    on_exit=stop_highlight_option
                )

                    

                #ft.Divider(),   # Placeholder for shapes section
                    # Placeholder for shapes section
            ]

            # Go through our saved brushes and add options to select them
            for name, brush_settings in app.settings.data.get('canvas_settings', {}).get('saved_brushes', {}).items():
                ctrls.append(
                    ft.GestureDetector(
                        ft.Container(
                            ft.Row([ft.Text(name, expand=True, overflow=ft.TextOverflow.ELLIPSIS), build_preview_brush(brush_settings)], spacing=20),
                            clip_behavior=ft.ClipBehavior.HARD_EDGE, border_radius=4, padding=ft.Padding.only(left=10, right=10)
                        ),
                        data=brush_settings,
                        on_tap=lambda e: set_active_brush(e.control.data, name=name),
                        on_enter=highlight_option,
                        on_exit=stop_highlight_option
                    )
                )

            return ctrls

        def get_text_options() -> list[ft.Control]:
            nonlocal text_settings

            # Updating standard text settings
            def update_text_setting(e: ft.Event[TextField | ft.RadioGroup | ft.Slider | Switch]):
                nonlocal text_settings

                if isinstance(e.control, ft.RadioGroup):
                    value = e.control.value

                elif isinstance(e.control, Switch):
                    if e.control.data == "weight":
                        value = "bold" if e.control.value else "normal"
                    elif e.control.data == "italic":
                        value = e.control.value
                elif isinstance(e.control, ft.Slider):
                    value = e.control.value

                elif isinstance(e.control, TextField):
                    # If less than 0, reset to the value it was
                    if not e.control.value.strip():
                        e.control.value = str(text_settings.get(e.control.data, 10))
                        e.control.update()
                        return

                    # Make sure value within bounds
                    value = int(max(min(int(e.control.value), 128), 0))
                    e.control.value = str(value)    # Reupdate clamped value
                    e.control.update()

                else:
                    return

                key = e.control.data
                text_settings.update(**{key: value})
                app.settings.update_data(**{"text_settings": text_settings})

                update_text_preview()
                text_preview.update()
                update_canvas_tool_preview()

            # Update text shadow settings (blur radius, blur style, offset, spread radius)
            def update_text_shadow_setting(e: ft.Event[TextField | ft.RadioGroup]):
                nonlocal text_settings
                shadow = text_settings.get('shadow') or {}

                if isinstance(e.control, ft.RadioGroup):
                    value = e.control.value

                elif isinstance(e.control, TextField):
                    # If less than 0, reset to the value it was
                    if not e.control.value.strip():
                        e.control.value = str(shadow.get(e.control.data, 0))
                        e.control.update()
                        return

                    # Keep offsets in the -100 to 100 range; other shadow values cannot be negative.
                    minimum = -100 if e.control.data in ("offset_x", "offset_y") else 0
                    value = int(max(min(int(e.control.value), 100), minimum))
                    e.control.value = str(value)    # Reupdate clamped value
                    e.control.update()

                else:
                    return

                shadow[e.control.data] = value
                text_settings['shadow'] = shadow
                app.settings.update_data(**{"text_settings": text_settings})

                update_text_preview()
                text_preview.update()
                update_canvas_tool_preview()

            # Update text foreground settings
            def update_text_foreground_setting(e: ft.Event[ft.TextField | ft.Dropdown | ft.Slider | ft.Switch]):
                nonlocal text_settings

            def save_text_color(e: ft.Event[ft.SubmenuButton]):
                nonlocal text_color_picker, text_color_selector
                color = text_color_picker.color
                text_settings.update({"color": color})
                app.settings.update_data(**{"text_settings": text_settings})
                text_color_selector.content = ft.Icon(ft.Icons.CIRCLE, color)
                if text_color_picker.color not in text_color_picker.color_history:
                    text_color_picker.color_history.append(text_color_picker.color)
                    if len(text_color_picker.color_history) > 6:
                        text_color_picker.color_history.pop(0)
                self.update()
                update_canvas_tool_preview()
                update_text_preview()
                text_preview.update()

            def save_text_bg_color(e: ft.Event[ft.SubmenuButton]):
                nonlocal text_bg_color_picker, text_bg_color_selector
                color = text_bg_color_picker.color
                text_settings.update({"bgcolor": color})
                app.settings.update_data(**{"text_settings": text_settings})
                text_bg_color_selector.content = ft.Icon(ft.Icons.CIRCLE, color)
                if text_bg_color_picker.color not in text_bg_color_picker.color_history:
                    text_bg_color_picker.color_history.append(text_bg_color_picker.color)
                    if len(text_bg_color_picker.color_history) > 6:
                        text_bg_color_picker.color_history.pop(0)
                self.update()
                update_canvas_tool_preview()
                update_text_preview()
                text_preview.update()

            def save_text_decoration_color(e: ft.Event[ft.SubmenuButton]):
                nonlocal text_decoration_color_picker, text_decoration_color_selector
                color = text_decoration_color_picker.color
                text_settings.update(**{"decoration_color": color})
                app.settings.update_data(**{"text_settings": text_settings})
                text_decoration_color_selector.content = ft.Icon(ft.Icons.CIRCLE, color)
                if text_decoration_color_picker.color not in text_decoration_color_picker.color_history:
                    text_decoration_color_picker.color_history.append(text_decoration_color_picker.color)
                    if len(text_decoration_color_picker.color_history) > 6:
                        text_decoration_color_picker.color_history.pop(0)
                self.update()
                update_canvas_tool_preview()
                update_text_preview()
                text_preview.update()

            def save_text_shadow_color(e: ft.Event[ft.SubmenuButton] = None):
                nonlocal text_shadow_color_picker, text_shadow_color_selector
                color = text_shadow_color_picker.color
                shadow = text_settings.get('shadow') or {}
                shadow['color'] = color
                text_settings['shadow'] = shadow
                app.settings.update_data(**{"text_settings": text_settings})
                text_shadow_color_selector.content = ft.Icon(ft.Icons.CIRCLE, color)
                if text_shadow_color_picker.color not in text_shadow_color_picker.color_history:
                    text_shadow_color_picker.color_history.append(text_shadow_color_picker.color)
                    if len(text_shadow_color_picker.color_history) > 6:
                        text_shadow_color_picker.color_history.pop(0)
                self.update()
                update_canvas_tool_preview()
                update_text_preview()
                text_preview.update()

            # Increase/decrease helpers for text shadow number fields
            def increase_shadow_tf_value(e: ft.Event[TextField]):
                current_val = int(e.control.parent.parent.value)
                new_val = min(current_val + 1, 100)
                e.control.parent.parent.value = str(new_val)
                update_text_shadow_setting(ft.Event(name="click", control=e.control.parent.parent, data=e.control.parent.parent.data))

            def decrease_shadow_tf_value(e: ft.Event[TextField]):
                current_val = int(e.control.parent.parent.value)
                min_val = 0 if e.control.parent.parent.data != "offset_x" and e.control.parent.parent.data != "offset_y" else -100
                new_val = max(current_val - 1, min_val)
                e.control.parent.parent.value = str(new_val)
                update_text_shadow_setting(ft.Event(name="click", control=e.control.parent.parent, data=e.control.parent.parent.data))

            # Increase the value (clamped) and pass the event along for settings
            def increate_tf_value(e: ft.Event[TextField]):
                current_val = int(e.control.parent.parent.value)
                new_val = min(current_val + 1, 128)
                e.control.parent.parent.value = str(new_val)
                update_text_setting(ft.Event(name="click", control=e.control.parent.parent, data=e.control.parent.parent.data))

            # Decrease the value (clamped) and pass the event along for settings
            def decrease_tf_value(e: ft.Event[TextField]):
                current_val = int(e.control.parent.parent.value)
                new_val = max(current_val - 1, 0)
                e.control.parent.parent.value = str(new_val)
                update_text_setting(ft.Event(name="click", control=e.control.parent.parent, data=e.control.parent.parent.data))
                


            bold_switch = Switch(   # TODO: make radio with normal, 100-1000, bold
                True, "Bold", on_change=update_text_setting,
                value=text_settings.get('weight', 'normal').lower() == "bold",
                data="weight",
            )

            italic_switch = Switch(
                True, "Italic", on_change=update_text_setting,
                value=text_settings.get('italic', False),
                data="italic",
            )

            

            size_tf = TextField(
                value=str(text_settings.get('size', 14)),
                on_blur=update_text_setting, data="size", label="Text Size (0-128)", 
                input_filter=ft.NumbersOnlyInputFilter(), 
                suffix_icon=UpDownButtons(up_function=increate_tf_value, down_function=decrease_tf_value),
            )

            letter_spacing_tf = TextField(
                value=str(text_settings.get('letter_spacing', 0)),
                on_blur=update_text_setting, data="letter_spacing", label="Letter Spacing (0-128)",
                input_filter=ft.NumbersOnlyInputFilter(),
                suffix_icon=UpDownButtons(up_function=increate_tf_value, down_function=decrease_tf_value)
            )

            word_spacing_tf = TextField(
                value=str(text_settings.get('word_spacing', 0)),
                on_blur=update_text_setting, data="word_spacing", label="Word Spacing (0-128)",
                input_filter=ft.NumbersOnlyInputFilter(),
                suffix_icon=UpDownButtons(up_function=increate_tf_value, down_function=decrease_tf_value)
            )

            text_decoration_thickness_tf = TextField(
                value=str(text_settings.get('decoration_thickness', 1)),
                on_blur=update_text_setting, data="decoration_thickness", label="Text Decoration Thickness (0-128)",
                input_filter=ft.NumbersOnlyInputFilter(),
                suffix_icon=UpDownButtons(up_function=increate_tf_value, down_function=decrease_tf_value)
            )
            text_decoration_thickness_tf.margin = ft.Margin.only(top=8, left=4, right=4, bottom=4)

            shadow_settings = text_settings.get('shadow') or {}

            shadow_blur_radius_tf = TextField(
                value=str(shadow_settings.get('blur_radius', 0)),
                on_blur=update_text_shadow_setting, data="blur_radius", label="Shadow Blur Radius (0-100)",
                input_filter=ft.NumbersOnlyInputFilter(),
                suffix_icon=UpDownButtons(up_function=increase_shadow_tf_value, down_function=decrease_shadow_tf_value)
            )

            shadow_spread_radius_tf = TextField(
                value=str(shadow_settings.get('spread_radius', 0)),
                on_blur=update_text_shadow_setting, data="spread_radius", label="Shadow Spread Radius (0-100)",
                input_filter=ft.NumbersOnlyInputFilter(),
                suffix_icon=UpDownButtons(up_function=increase_shadow_tf_value, down_function=decrease_shadow_tf_value)
            )

            shadow_offset_x_tf = TextField(
                value=str(shadow_settings.get('offset_x', 0)),
                on_blur=update_text_shadow_setting, data="offset_x", label="Shadow Offset X (-100-100)",
                input_filter=NEGATIVE_NUMBER_FILTER,
                suffix_icon=UpDownButtons(up_function=increase_shadow_tf_value, down_function=decrease_shadow_tf_value)
            )

            shadow_offset_y_tf = TextField(
                value=str(shadow_settings.get('offset_y', 0)),
                on_blur=update_text_shadow_setting, data="offset_y", label="Shadow Offset Y (-100-100)",
                input_filter=NEGATIVE_NUMBER_FILTER,
                suffix_icon=UpDownButtons(up_function=increase_shadow_tf_value, down_function=decrease_shadow_tf_value)
            )

            # Add baseline rg here if wanted (not wanted rn)
            font_family_rg = ft.RadioGroup(
                content=ExpansionTile(
                    title="Font Family",
                    controls=[
                        ft.Radio(key, value=key) for key in self.page.fonts.keys()
                    ]
                ),
                value=text_settings.get('font_family', 'Arial'),
                on_change=update_text_setting,
                data="font_family"
            )



              

            

            # Color picker for changing brush color
            text_color_picker = ColorPicker(
                color=text_settings.get('color', None),
                on_color_change=set_color, 
                picker_area_border_radius=ft.BorderRadius.all(4),
                color_history=[]
            ) 
    
            
            # Color picker for changing brush color
            text_bg_color_picker = ColorPicker(
                color=text_settings.get('bgcolor', None),
                on_color_change=set_color, 
                picker_area_border_radius=ft.BorderRadius.all(4),
                color_history=[]
            )   

            text_decoration_color_picker = ColorPicker(
                color=text_settings.get('decoration_color', None),
                on_color_change=set_color, 
                picker_area_border_radius=ft.BorderRadius.all(4),
                color_history=[]
            )

            text_shadow_color_picker = ColorPicker(
                color=shadow_settings.get('color', None),
                on_color_change=set_color, 
                picker_area_border_radius=ft.BorderRadius.all(4),
                color_history=[]
            )

            # Create our color selector button
            text_color_selector = ft.SubmenuButton(
                ft.Icon(ft.Icons.CIRCLE, text_settings.get('color', ft.Colors.PRIMARY)), 
                tooltip="The color of your text",
                on_close=save_text_color, #expand=True,
                width=40,
                height=40,
                controls=[text_color_picker],
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0)),
                menu_style=ft.MenuStyle(
                    alignment=ft.Alignment.TOP_RIGHT,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, 
                    shape=ft.RoundedRectangleBorder(radius=4),
                    padding=ft.Padding.all(0)
                ),
            )
    
            # Create our color selector button
            text_bg_color_selector = ft.SubmenuButton(
                ft.Icon(ft.Icons.CIRCLE, text_settings.get('bgcolor', ft.Colors.PRIMARY)), 
                tooltip="The color of your background behind your text.",
                on_close=save_text_bg_color, #expand=True,
                width=40,
                height=40,
                controls=[text_bg_color_picker],
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0),),
                menu_style=ft.MenuStyle(
                    alignment=ft.Alignment.CENTER_RIGHT,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, 
                    shape=ft.RoundedRectangleBorder(radius=4),
                    padding=ft.Padding.all(0)
                ),
            )

            text_decoration_color_selector = ft.SubmenuButton(
                ft.Icon(ft.Icons.CIRCLE, text_settings.get('decoration_color', ft.Colors.PRIMARY)),
                tooltip="The color of your text decoration (underline, overline, line through).",
                on_close=save_text_decoration_color, #expand=True,
                width=40,
                height=40,
                controls=[text_decoration_color_picker],
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0),),
                menu_style=ft.MenuStyle(
                    alignment=ft.Alignment.CENTER_RIGHT,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                    shape=ft.RoundedRectangleBorder(radius=4),
                    padding=ft.Padding.all(0)
                ),
            )

            text_shadow_color_selector = ft.SubmenuButton(
                ft.Icon(ft.Icons.CIRCLE, shadow_settings.get('color', ft.Colors.PRIMARY)),
                tooltip="The color of your text shadow.",
                on_close=save_text_shadow_color, #expand=True,
                width=40,
                height=40,
                controls=[text_shadow_color_picker],
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0),),
                menu_style=ft.MenuStyle(
                    alignment=ft.Alignment.CENTER_RIGHT,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                    shape=ft.RoundedRectangleBorder(radius=4),
                    padding=ft.Padding.all(0)
                ),
            )

            text_color_options_button = ft.SubmenuButton(
                controls=get_color_options(text_color_picker, save_text_color),
                content=ft.Icon(ft.Icons.ARROW_DROP_DOWN, ft.Colors.PRIMARY, scale=0.8),
                style=ft.ButtonStyle(
                    #mouse_cursor=ft.MouseCursor.CLICK,  
                    shape=ft.RoundedRectangleBorder(radius=0),
                    padding=ft.Padding.all(0),
                ),
                menu_style=ft.MenuStyle(
                    alignment=ft.Alignment.TOP_RIGHT,
                    bgcolor=ft.Colors.SURFACE_CONTAINER, 
                    shape=ft.RoundedRectangleBorder(radius=4),
                    padding=ft.Padding.all(0)
                ),
                expand=True,
                width=24,
            )  

            text_bg_color_options_button = ft.SubmenuButton(
                controls=get_color_options(text_bg_color_picker, save_text_bg_color),
                content=ft.Icon(ft.Icons.ARROW_DROP_DOWN, ft.Colors.PRIMARY, scale=0.8),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=0),
                    padding=ft.Padding.all(0),
                ),
                menu_style=ft.MenuStyle(
                    alignment=ft.Alignment.CENTER_RIGHT,
                    bgcolor=ft.Colors.SURFACE_CONTAINER, 
                    shape=ft.RoundedRectangleBorder(radius=4),
                    padding=ft.Padding.all(0)
                ),
                expand=True,
                width=24,
            )  

            text_decoration_color_options_button = ft.SubmenuButton(
                controls=get_color_options(text_decoration_color_picker, save_text_decoration_color),
                content=ft.Icon(ft.Icons.ARROW_DROP_DOWN, ft.Colors.PRIMARY, scale=0.8),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=0),
                    padding=ft.Padding.all(0),
                ),
                menu_style=ft.MenuStyle(
                    alignment=ft.Alignment.CENTER_RIGHT,
                    bgcolor=ft.Colors.SURFACE_CONTAINER, 
                    shape=ft.RoundedRectangleBorder(radius=4),
                    padding=ft.Padding.all(0)
                ),
                expand=True,
                width=24,
            )

            text_shadow_color_options_button = ft.SubmenuButton(
                controls=get_color_options(text_shadow_color_picker, save_text_shadow_color),
                content=ft.Icon(ft.Icons.ARROW_DROP_DOWN, ft.Colors.PRIMARY, scale=0.8),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=0),
                    padding=ft.Padding.all(0),
                ),
                menu_style=ft.MenuStyle(
                    alignment=ft.Alignment.CENTER_RIGHT,
                    bgcolor=ft.Colors.SURFACE_CONTAINER, 
                    shape=ft.RoundedRectangleBorder(radius=4),
                    padding=ft.Padding.all(0)
                ),
                expand=True,
                width=24,
            )

            

            text_shadow_rg = ExpansionTile(
                title="Text Shadow Settings",
                controls=[
                        #ft.RadioGroup(
                            #content=ft.Column(
                                #[
                                #ft.Text("Shadow Type", italic=True, margin=ft.Margin.only(left=4))
                                #] + [
                                #ft.Radio(key.capitalize(), value=key) for key in ("none", "normal", "solid", "outer", "inner")
                            #], spacing=0),
                           # value=shadow_settings.get('blur_style', 'normal') if shadow_settings.get('blur_style', None) is not None else 'normal',
                            #on_change=update_text_shadow_setting,
                            #data="blur_style"
                                #)
                            #] + [
                        shadow_blur_radius_tf,
                        #shadow_spread_radius_tf,
                        shadow_offset_x_tf,
                        shadow_offset_y_tf,
                    ]
            )
            

            text_decoration_rg = ExpansionTile(
                title="Text Decoration Settings",
                controls=[
                    ft.RadioGroup(
                        content=ft.Column(
                            [ft.Text("Decoration Type", italic=True, margin=ft.Margin.only(left=4))] + [
                                ft.Radio(key.capitalize().replace("_", " "), value=key) for key in ("none", "underline", "overline", "line_through")
                            ],
                            spacing=0
                        ),
                        value=text_settings.get('decoration', 'none') if text_settings.get('decoration', None) is not None else 'none',
                        on_change=update_text_setting,
                        data="decoration"
                    ),
                    text_decoration_thickness_tf,
                    ft.RadioGroup(
                        content=ft.Column(
                            [ft.Text("Decoration Style", italic=True, margin=ft.Margin.only(left=4))] + [
                                ft.Radio(key.capitalize(), value=key) for key in ("solid", "wavy", "double", "dotted", "dashed")
                            ],
                            spacing=0
                        ),
                        value=text_settings.get('decoration_style', 'solid'),
                        on_change=update_text_setting,
                        data="decoration_style"
                    )
                ]
            )
            
        
            # Called to save our active text settings as a custom named text setting we can load later
            def save_custom_text_settings_clicked(e=None):
                ''' Shows our existing text setting options and allows us to override or save as a new one '''

                # Saves the current name and closes the dialog
                async def _save_and_close(e=None):

                    nonlocal name, text_settings
                    safe_name = return_safe_name(name)

                    # Save current text settings as a new custom text setting
                    app.settings.data['canvas_settings']['saved_text_settings'][safe_name] = text_settings.copy()
                    app.settings.update_data(**{"canvas_settings": {"saved_text_settings": app.settings.data['canvas_settings']['saved_text_settings']}})

                    self.page.pop_dialog()
                    text_settings_button.controls = get_text_options()   # Update the text settings selector with the new setting
                    self.update()

                # Deletes a saved text setting
                async def _delete_custom_text_setting(e):
                    nonlocal content
                    name = e.control.data

                    # Remove it from data
                    if name in app.settings.data.get('canvas_settings', {}).get('saved_text_settings', {}):
                        del app.settings.data['canvas_settings']['saved_text_settings'][name]
                        app.settings.update_data(**{"canvas_settings": {"saved_text_settings": app.settings.data['canvas_settings']['saved_text_settings']}})

                    # Remove the control from the dialog
                    dlg.content.controls = [ctrl for ctrl in content.controls if ctrl.data != name]
                    content.update()

                    text_settings_button.controls = get_text_options()   # Update the text settings selector with the new setting
                    self.update()

                    # If we were going to override it but instead deleted it, apply that UI change
                    if name == new_custom_text_setting_name_text_field.value:
                        new_custom_text_setting_name_text_field.error = None
                        new_custom_text_setting_name_text_field.update()
                        save_button.content = "Save"
                        save_button.update()
                        await new_custom_text_setting_name_text_field.focus()

                # Sets an existing custom text setting to be overwritten by the current settings
                def _select_active_text_setting_override(e):
                    nonlocal name, content

                    # Show visual effects that the text setting will be overwritten
                    name = e.control.data
                    e.control.bgcolor = ft.Colors.OUTLINE_VARIANT
                    e.control.update()
                    save_button.content = "Overwrite"
                    save_button.update()

                    # Textfield UI changes
                    new_custom_text_setting_name_text_field.value = name
                    new_custom_text_setting_name_text_field.error = f"Saving will overwrite {name}"
                    new_custom_text_setting_name_text_field.update()

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

                # Textfield for naming custom text setting
                new_custom_text_setting_name_text_field = ft.TextField(
                    label="Text Setting Name", autofocus=True, on_submit=_save_and_close, dense=True,
                    capitalization=ft.TextCapitalization.SENTENCES, #expand=True,
                    on_change=_check_name_change,
                )

                name: str = None

                # Our save button that just changes text from save to overwrite
                save_button = ft.TextButton("Save", on_click=_save_and_close, style=ft.ButtonStyle(mouse_cursor="click"))

                content = ft.Column([new_custom_text_setting_name_text_field], scroll=ft.ScrollMode.AUTO, height=self.page.height / 2)

                dlg = ft.AlertDialog(
                    title=ft.Text("Name your custom text setting"),
                    content=content,
                    actions=[
                        ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                        save_button
                    ]
                )

                for name, existing_text_setting in app.settings.data.get('canvas_settings', {}).get('saved_text_settings', {}).items():
                    content.controls.append(
                        ft.Container(
                            ft.Row([
                                ft.Text(name, theme_style=ft.TextThemeStyle.LABEL_LARGE, expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                                build_preview_text(existing_text_setting),
                                ft.IconButton(
                                    ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR,
                                    data=name, on_click=_delete_custom_text_setting, tooltip="Delete this saved text setting",
                                    mouse_cursor=ft.MouseCursor.CLICK
                                ),
                            ], spacing=20), border_radius=ft.BorderRadius.all(4), clip_behavior=ft.ClipBehavior.HARD_EDGE, padding=ft.Padding.only(left=6),
                            on_click=_select_active_text_setting_override, 
                            data=name,
                        )
                    )

                self.page.show_dialog(dlg)


            ctrls = [
                ft.Row([
                    ft.Text("Text Settings", color=ft.Colors.ON_SURFACE_VARIANT, italic=True, tooltip="Settings for text shapes used on canvases"),
                    ft.IconButton(
                        ft.Icons.SAVE_ROUNDED, ft.Colors.PRIMARY, on_click=save_custom_text_settings_clicked, 
                        tooltip="Save the current text settings as a custom text setting you can load later.", 
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)),
                    )
                ], alignment=ft.MainAxisAlignment.CENTER),   
                ft.Container(
                    ft.Row([text_preview], alignment=ft.MainAxisAlignment.CENTER), 
                    margin=ft.Margin.all(10), border_radius=4, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    alignment=ft.Alignment.CENTER, padding=ft.Padding.all(10)
                ),
                ft.Divider(2, 2),
                #ft.Row([
                    #ft.Container(text_preview, expand=True, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH, alignment=ft.Alignment.CENTER, border_radius=4, padding=ft.Padding.all(10))
                #]),
                
                bold_switch,  
                italic_switch,

                size_tf,
                letter_spacing_tf,
                word_spacing_tf,

                ft.Row([
                    ft.Text("Text Color"),
                    ft.MenuBar(
                        [
                            ft.Container(
                                text_color_selector,
                                border_radius=ft.BorderRadius.only(top_left=4, bottom_left=4),
                            ),
                            ft.Container(
                                text_color_options_button,    
                                border_radius=ft.BorderRadius.only(top_right=4, bottom_right=4),
                                alignment=ft.Alignment.CENTER
                            ),  # Button to save current color to settings
                        ],
                        style=ft.MenuStyle(
                            alignment=ft.Alignment.CENTER_LEFT,
                            bgcolor=ft.Colors.TRANSPARENT,
                            shadow_color=ft.Colors.TRANSPARENT,
                            padding=ft.Padding.all(0)
                        ),
                    ),
                    
                ], margin=ft.Margin.only(left=4), spacing=0),
                ft.Row([
                    ft.Text("Text Background Color"),
                    ft.MenuBar(
                        [
                            ft.Container(
                                text_bg_color_selector,
                                border_radius=ft.BorderRadius.only(top_left=4, bottom_left=4),
                            ),
                            ft.Container(
                                text_bg_color_options_button,    
                                border_radius=ft.BorderRadius.only(top_right=4, bottom_right=4),
                                alignment=ft.Alignment.CENTER
                            ),  # Button to save current color to settings
                        ],
                        style=ft.MenuStyle(
                            alignment=ft.Alignment.CENTER_RIGHT,
                            bgcolor=ft.Colors.TRANSPARENT,
                            shadow_color=ft.Colors.TRANSPARENT,
                            padding=ft.Padding.all(0)
                        ),
                    ),
                ], spacing=0, margin=ft.Margin.only(left=4)),

                ft.Row([
                    ft.Text("Text Decoration Color"),
                    ft.MenuBar(
                        [
                            ft.Container(
                                text_decoration_color_selector,
                                border_radius=ft.BorderRadius.only(top_left=4, bottom_left=4),
                            ),
                            ft.Container(
                                text_decoration_color_options_button,    
                                border_radius=ft.BorderRadius.only(top_right=4, bottom_right=4),
                                alignment=ft.Alignment.CENTER
                            ),  # Button to save current color to settings
                        ],
                        style=ft.MenuStyle(
                            alignment=ft.Alignment.CENTER_LEFT,
                            bgcolor=ft.Colors.TRANSPARENT,
                            shadow_color=ft.Colors.TRANSPARENT,
                            padding=ft.Padding.all(0)
                        ),
                    ),
                ], spacing=0, margin=ft.Margin.only(left=4)),

                ft.Row([
                    ft.Text("Text Shadow Color"),
                    ft.MenuBar(
                        [
                            ft.Container(
                                text_shadow_color_selector,
                                border_radius=ft.BorderRadius.only(top_left=4, bottom_left=4),
                            ),
                            ft.Container(
                                text_shadow_color_options_button,
                                border_radius=ft.BorderRadius.only(top_right=4, bottom_right=4),
                                alignment=ft.Alignment.CENTER
                            ),  # Button to save current color to settings
                        ],
                        style=ft.MenuStyle(
                            alignment=ft.Alignment.CENTER_RIGHT,
                            bgcolor=ft.Colors.TRANSPARENT,
                            shadow_color=ft.Colors.TRANSPARENT,
                            padding=ft.Padding.all(0)
                        ),
                    ),
                ], spacing=0, margin=ft.Margin.only(left=4)),

                font_family_rg,
                text_decoration_rg,
                text_shadow_rg,

                ft.Divider(),
                ft.Row([
                    ft.Text("Saved Text Settings", color=ft.Colors.ON_SURFACE_VARIANT, italic=True),
                ], alignment=ft.MainAxisAlignment.CENTER),  
            ]

            def highlight_option(e: ft.Event[ft.GestureDetector]):
                e.control.content.bgcolor = ft.Colors.OUTLINE_VARIANT
                e.control.update()
            def stop_highlight_option(e: ft.Event[ft.GestureDetector]):
                e.control.content.bgcolor = ft.Colors.TRANSPARENT
                e.control.update()

            # Go through our saved text options and add them to the list of controls
            # NOTE: loop var must not be named `text_settings`, it would shadow the nonlocal current settings dict
            for name, saved_text_setting in app.settings.data.get('canvas_settings', {}).get('saved_text_settings', {}).items():
                ctrls.append(
                    ft.GestureDetector(
                        ft.Container(
                            ft.Row([
                                ft.Text(name.capitalize(), expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                                build_preview_text(saved_text_setting)
                            ]),
                            border_radius=ft.BorderRadius.all(4), padding=10
                        ),
                        data=saved_text_setting,
                        on_tap=lambda _, ts=saved_text_setting, n=name: set_active_text_setting(ts, n),
                        on_enter=highlight_option,
                        on_exit=stop_highlight_option
                    )
                )
                

            return ctrls

        # Grab our data for easier manipulation
        paint_settings = app.settings.data.get('paint_settings', {}).copy()
        canvas_settings = app.settings.data.get('canvas_settings', {}).copy()
        text_settings = app.settings.data.get('text_settings', {}).copy()

        # Color picker for changing brush color
        color_picker = ColorPicker(
            color=paint_settings.get('color', "#000000"),
            on_color_change=set_color, 
            picker_area_border_radius=ft.BorderRadius.all(4),
            color_history=[]
        )   

        # Create our color selector button
        color_selector = ft.SubmenuButton(
            ft.Icon(ft.Icons.CIRCLE, paint_settings.get('color', ft.Colors.PRIMARY)), 
            tooltip="The color of your brush strokes.",
            on_close=save_color, #expand=True,
            width=40,
            height=40,
            controls=[ft.Column([
                color_picker,  
                ft.MenuItemButton(
                    "Set Color", 
                    on_click=lambda: None,  # Something so its not disabled
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=4), #mouse_cursor=ft.MouseCursor.CLICK,
                        bgcolor=ft.Colors.SURFACE_CONTAINER
                    )
                )
            ])],
            style=ft.ButtonStyle(
                #mouse_cursor=ft.MouseCursor.CLICK,  
                #bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                shape=ft.RoundedRectangleBorder(radius=0),
            ),
            menu_style=ft.MenuStyle(
                alignment=ft.Alignment.TOP_RIGHT,
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, 
                shape=ft.RoundedRectangleBorder(radius=4),
                padding=ft.Padding.all(0)
            ),
        )

        def get_color_options(target_color_picker: ColorPicker, apply_color) -> list[ft.Control]:
            nonlocal canvas_settings

            def set_saved_color(e: ft.Event[ft.MenuItemButton]):
                color_data = e.control.data
                target_color_picker.color = color_data.get('value', "#000000")
                apply_color(None)

            def delete_color(e: ft.Event[ft.IconButton]):
                nonlocal canvas_settings
                idx = e.control.data
                canvas_settings['saved_colors'].pop(idx)
                app.settings.update_data(**{"canvas_settings": {"saved_colors": canvas_settings['saved_colors']}})
                color_options_button.controls = get_color_options(color_picker, save_color)
                text_settings_button.controls = get_text_options()
                self.update()

            def save_custom_color(e: ft.Event[ft.IconButton]):

                # Saves the color to data and pops the dialog
                async def save_color_name(e=None):
                    nonlocal canvas_settings
                    color_name = name_tf.value.strip()
                    # Always pull from the picker that triggered this save, not the paint picker
                    current_color = target_color_picker.color
                    canvas_settings['saved_colors'].append({'name': color_name, 'value': current_color})
                    app.settings.update_data(**{"canvas_settings": {"saved_colors": canvas_settings['saved_colors']}})
                    color_options_button.controls = get_color_options(color_picker, save_color)
                    text_settings_button.controls = get_text_options()
                    self.update()
                    self.page.pop_dialog()
            

                name_tf = ft.TextField(label="Color Name", autofocus=True, on_submit=save_color_name, capitalization=ft.TextCapitalization.WORDS)
                #color = e.control.parent.parent.parent.parent.controls[0].content.color or paint_settings.get('color', "#000000")
                
                self.page.show_dialog(
                    ft.AlertDialog(
                        title="Name Color",
                        content=name_tf,
                        actions=[
                            ft.TextButton("Cancel", on_click=lambda: self.page.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor=ft.MouseCursor.CLICK)),
                            ft.TextButton("Save", on_click=save_color_name, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.PRIMARY)),
                        ]
                    )
                )
                
            def highlight_option(e: ft.Event[ft.GestureDetector]):
                e.control.content.bgcolor = ft.Colors.OUTLINE_VARIANT
                e.control.update()
            def stop_highlight_option(e: ft.Event[ft.GestureDetector]):
                e.control.content.bgcolor = ft.Colors.TRANSPARENT
                e.control.update()


            ctrls = [
                ft.Row([    # Label
                    ft.Text("Saved Colors", color=ft.Colors.ON_SURFACE_VARIANT, italic=True, margin=ft.Margin.only(left=4)),
                    ft.IconButton(  # Save button
                        ft.Icons.SAVE_ROUNDED, ft.Colors.PRIMARY, on_click=save_custom_color, 
                        tooltip="Save the current color to your saved colors", 
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)),
                    ),
                ], margin=ft.Margin.only(left=4), alignment=ft.MainAxisAlignment.CENTER)   
            ]
            for idx, color_data in enumerate(canvas_settings.get('saved_colors', [])):
                ctrls.append(
                    ft.GestureDetector(
                        ft.Container(
                            ft.Row([
                                ft.Icon(ft.Icons.CIRCLE, color_data.get('value', "#000000")),
                                ft.Text(color_data.get('name', 'Unnamed Color')),
                                ft.IconButton(ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR, data=idx, tooltip="Delete this saved color", on_click=delete_color),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            border_radius=ft.BorderRadius.all(4), padding=ft.Padding.only(left=10, right=10)
                        ),
                        data=color_data,
                        on_tap=set_saved_color,
                        on_enter=highlight_option,
                        on_exit=stop_highlight_option,
                    )
                )
            
            return ctrls

        color_options_button = ft.SubmenuButton(
            controls=get_color_options(color_picker, save_color),
            content=ft.Icon(ft.Icons.ARROW_DROP_DOWN, ft.Colors.PRIMARY, scale=0.8),
            style=ft.ButtonStyle(
                #mouse_cursor=ft.MouseCursor.CLICK,  
                shape=ft.RoundedRectangleBorder(radius=0),
                padding=ft.Padding.all(0),
            ),
            menu_style=ft.MenuStyle(
                alignment=ft.Alignment.TOP_RIGHT,
                bgcolor=ft.Colors.SURFACE_CONTAINER, 
                shape=ft.RoundedRectangleBorder(radius=4),
                padding=ft.Padding.all(0)
            ),
            expand=True,
            width=24,
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
            content=ft.Icon(ft.Icons.ARROW_DROP_DOWN, ft.Colors.PRIMARY, scale=0.8),
            style=ft.ButtonStyle(
                #mouse_cursor=ft.MouseCursor.CLICK,  
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if app.settings.data.get('canvas_settings', {}).get('current_control_mode', '') == "draw" else None,
                shape=ft.RoundedRectangleBorder(radius=0),
                padding=ft.Padding.all(0),
            ),
            menu_style=ft.MenuStyle(
                alignment=ft.Alignment.TOP_RIGHT,
                bgcolor=ft.Colors.SURFACE_CONTAINER, 
                shape=ft.RoundedRectangleBorder(radius=4),
                padding=ft.Padding.all(0)
            ),
            expand=True,
            width=24,
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
            content=ft.Icon(ft.Icons.ARROW_DROP_DOWN, ft.Colors.PRIMARY, scale=0.8),
            style=ft.ButtonStyle(
                #mouse_cursor=ft.MouseCursor.CLICK,  
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if app.settings.data.get('canvas_settings', {}).get('current_control_mode', '') == "tool" else None,
                shape=ft.RoundedRectangleBorder(radius=0),
                padding=ft.Padding.all(0),
            ),
            menu_style=ft.MenuStyle(
                alignment=ft.Alignment.TOP_RIGHT,
                bgcolor=ft.Colors.SURFACE_CONTAINER, 
                shape=ft.RoundedRectangleBorder(radius=4),
                padding=ft.Padding.all(0)
            ),
            expand=True,
            width=24,
        )

        text_preview = ft.Text(
            "Preview Text", selectable=True, 
            #style=ft.TextStyle(**text_settings)
        )

        def update_text_preview():
            nonlocal text_preview, text_settings
            text_preview.style = ft.TextStyle(**text_settings)
            
            # Match decoration accordingly, since its str -> control doesnt work
            decoration = text_settings.get('decoration', None)
            match decoration:
                case "underline":
                    text_preview.style.decoration = ft.TextDecoration.UNDERLINE
                case "overline":
                    text_preview.style.decoration = ft.TextDecoration.OVERLINE
                case "line_through":
                    text_preview.style.decoration = ft.TextDecoration.LINE_THROUGH
                case _:
                    text_preview.style.decoration = None

            text_preview.style.shadow = ft.BoxShadow(
                blur_radius=text_settings.get('shadow', {}).get('blur_radius', 0),
                color=text_settings.get('shadow', {}).get('color', None),
                offset=ft.Offset(
                    text_settings.get('shadow', {}).get('offset_x', 0),
                    text_settings.get('shadow', {}).get('offset_y', 0)
                ),
            )

        update_text_preview()

        set_text_mode_button = ft.IconButton(
            ft.Icons.TEXT_FIELDS if app.settings.data.get('canvas_settings', {}).get('current_control_mode', 'draw') == "text" else ft.Icons.TEXT_FIELDS_OUTLINED,
            ft.Colors.PRIMARY,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if canvas_settings.get('current_control_mode', '') == "text" else None,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0)),
            tooltip="Set the active control to text mode.",
            data="text", on_click=set_text_mode
        )

        text_settings_button = ft.SubmenuButton(
            controls=get_text_options(),
            content=ft.Icon(
                ft.Icons.ARROW_DROP_DOWN, 
                ft.Colors.PRIMARY,
                scale=0.8
            ),
            style=ft.ButtonStyle(
                #mouse_cursor=ft.MouseCursor.CLICK,  f
                shape=ft.RoundedRectangleBorder(radius=0),
                padding=ft.Padding.all(0),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if canvas_settings.get('current_control_mode', '') == "text" else None
            ),
            menu_style=ft.MenuStyle(
                alignment=ft.Alignment.TOP_RIGHT,
                bgcolor=ft.Colors.SURFACE_CONTAINER, 
                shape=ft.RoundedRectangleBorder(radius=4),
                padding=ft.Padding.all(0)
            ),
            expand=True,
            width=24,
        )

        erase_tool_button = ft.IconButton(
            ft.Icons.AUTO_FIX_NORMAL if canvas_settings.get('current_tool_name', 'draw') == "erase" and canvas_settings.get('current_control_mode', "draw") == "tool" else ft.Icons.AUTO_FIX_NORMAL_OUTLINED,
            ft.Colors.PRIMARY,
            data="erase",
            on_click=set_tool_mode,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4),),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if canvas_settings.get('current_tool_name', 'draw') == "erase" and canvas_settings.get('current_control_mode', "draw") == "tool" else None,
            tooltip="Erase Tool"
        )
        fill_tool_button = ft.IconButton(
            ft.Icons.FORMAT_COLOR_FILL,
            ft.Colors.PRIMARY,
            data="fill",
            #disabled=True,
            on_click=set_tool_mode,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4),),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if canvas_settings.get('current_tool_name', 'draw') == "fill" and canvas_settings.get('current_control_mode', "draw") == "tool" else None,
            tooltip="Fill Tool"
        )
        line_tool_button = ft.IconButton(
            ft.Icons.REMOVE if canvas_settings.get('current_tool_name', 'draw') == "line" and canvas_settings.get('current_control_mode', "draw") == "tool" else ft.Icons.REMOVE_OUTLINED,
            ft.Colors.PRIMARY,
            data="line",
            on_click=set_tool_mode,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4),),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if canvas_settings.get('current_tool_name', 'draw') == "line" and canvas_settings.get('current_control_mode', "draw") == "tool" else None,
            tooltip="Line Tool"
        )
        circle_tool_button = ft.IconButton(
            ft.Icons.CIRCLE if canvas_settings.get('current_tool_name', 'draw') == "circle" and canvas_settings.get('current_control_mode', "draw") == "tool" else ft.Icons.CIRCLE_OUTLINED,
            ft.Colors.PRIMARY,
            data="circle",
            on_click=set_tool_mode,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if canvas_settings.get('current_tool_name', 'draw') == "circle" and canvas_settings.get('current_control_mode', "draw") == "tool" else None,
            tooltip="Circle Shape"
        )
                              
        oval_tool_button = ft.IconButton(
            ft.Icon(ft.Icons.CIRCLE, ft.Colors.PRIMARY, scale=ft.Scale(scale_x=0.8),) if canvas_settings.get('current_tool_name', 'draw') == "oval" and canvas_settings.get('current_control_mode', "draw") == "tool" else ft.Icon(ft.Icons.CIRCLE_OUTLINED, ft.Colors.PRIMARY, scale=ft.Scale(scale_x=0.8),),
            data="oval",
            on_click=set_tool_mode,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if canvas_settings.get('current_tool_name', 'draw') == "oval" and canvas_settings.get('current_control_mode', "draw") == "tool" else None, 
            tooltip="Oval Shape"
        )
        arc_tool_button = ft.IconButton(
            tool_icons.get('arc') if canvas_settings.get('current_tool_name', 'draw') == "arc" and canvas_settings.get('current_control_mode', "draw") == "tool" else tool_icons.get('arc_outlined'),
            
            data="arc",
            on_click=set_tool_mode,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), ),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if canvas_settings.get('current_tool_name', 'draw') == "arc" and canvas_settings.get('current_control_mode', "draw") == "tool" else None,
            tooltip="Arc Shape"
        )
        rectangle_tool_button = ft.IconButton(
            ft.Icons.RECTANGLE if canvas_settings.get('current_tool_name', 'draw') == "rectangle" and canvas_settings.get('current_control_mode', "draw") == "tool" else ft.Icons.RECTANGLE_OUTLINED,
            ft.Colors.PRIMARY,
            data="rectangle",
            on_click=set_tool_mode,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4),),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if canvas_settings.get('current_tool_name', 'draw') == "rectangle" and canvas_settings.get('current_control_mode', "draw") == "tool" else None,
            tooltip="Rectangle Shape"
        )
        triangle_tool_button = ft.IconButton(
            ft.CupertinoIcons.ARROWTRIANGLE_UP_FILL if canvas_settings.get('current_tool_name', 'draw') == "triangle" and canvas_settings.get('current_control_mode', "draw") == "tool" else ft.CupertinoIcons.ARROWTRIANGLE_UP,
            ft.Colors.PRIMARY,
            data="triangle",
            on_click=set_tool_mode,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), ),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if canvas_settings.get('current_tool_name', 'draw') == "triangle" and canvas_settings.get('current_control_mode', "draw") == "tool" else None,
            tooltip="Triangle Shape"
        )
        
        drawing_controls = [
            ft.MenuBar(
                [
                    ft.Container(
                        color_selector,
                        border_radius=ft.BorderRadius.only(top_left=4, bottom_left=4),
                    ),
                    ft.Container(
                        color_options_button,    
                        border_radius=ft.BorderRadius.only(top_right=4, bottom_right=4),
                        alignment=ft.Alignment.CENTER
                    ),  # Button to save current color to settings
                ],
                style=ft.MenuStyle(
                    alignment=ft.Alignment.CENTER_LEFT,
                    bgcolor=ft.Colors.TRANSPARENT,
                    shadow_color=ft.Colors.TRANSPARENT,
                    padding=ft.Padding.all(0)
                ),
            ),
            
            ft.MenuBar(
                [
                    ft.Container(
                        set_draw_mode_button,
                        border_radius=ft.BorderRadius.only(top_left=4, bottom_left=4),
                    ),

                    ft.Container(
                        brush_selector,    
                        border_radius=ft.BorderRadius.only(top_right=4, bottom_right=4),
                        #margin=ft.Margin.only(right=20)
                    ),
                ],
                style=ft.MenuStyle(
                    alignment=ft.Alignment.CENTER_LEFT,
                    bgcolor=ft.Colors.TRANSPARENT,
                    shadow_color=ft.Colors.TRANSPARENT,
                    padding=ft.Padding.all(0)
                ),
            ),


            ft.MenuBar(
                [
                    ft.Container(
                        set_text_mode_button,
                        border_radius=ft.BorderRadius.only(top_left=4, bottom_left=4),
                    ),
                    ft.Container(
                        text_settings_button,     
                        border_radius=ft.BorderRadius.only(top_right=4, bottom_right=4),
                        #margin=ft.Margin.only(right=20)
                    ),
                ],
                style=ft.MenuStyle(
                    alignment=ft.Alignment.CENTER_LEFT,
                    bgcolor=ft.Colors.TRANSPARENT,
                    shadow_color=ft.Colors.TRANSPARENT,
                    padding=ft.Padding.all(0)
                ),
            ),


            erase_tool_button,
            fill_tool_button,
            line_tool_button,
            circle_tool_button,
            oval_tool_button,
            arc_tool_button,
            rectangle_tool_button,
            triangle_tool_button


        ]
        
        

        # Sets our content as a column. This will fill our width and hold...
        # Either our list of workspaces, or a reorderable list of our workspaces
        self.content = ft.Column(
            #[ft.Row([self.rail_label], alignment=ft.MainAxisAlignment.CENTER)] + 
            drawing_controls,
            #[ft.Container(expand=True), ft.Row([self.collapse_icon_button], alignment=ft.MainAxisAlignment.END)],
            #horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            #spacing=20,
        )

        # If mobile, this will be shown on menubar instead
        self.visible = not self.page.platform.is_mobile()

        # If the user has set to hide the canvas rail, then hide it on startup
        if app.settings.data.get('story', {}).get('show_canvas_rail', False) == True:
            self.width = 78
        else:
            self.width = 0


    