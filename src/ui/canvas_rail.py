''' UI model file to create our all_workspaces_rail on the left side of the screen.
This object is stored in app.all_workspaces_rail.
Handles new workspace selections, re-ordering, collapsing, and expanding the rail. '''

import flet as ft
from flet_color_pickers import ColorPicker
import math
import flet.canvas as cv
from utils.safe_string_checker import return_safe_name
from models.views.story import Story

# Class so we can store our all workspaces rail as an object inside of app
class CanvasRail(ft.Container):
    
    # Constructor for our all_workspaces_rail object. Needs a page reference passed in
    def __init__(self, story: Story):

        self.story = story
       
        # Style our rail (container)
        super().__init__(
            alignment=ft.Alignment.CENTER,  # Aligns content to the 
            padding=ft.Padding.only(bottom=10, right=10, left=10),
            animate=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            border=ft.Border(right=ft.BorderSide(2, ft.Colors.OUTLINE_VARIANT)),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST
        )

    # Called by clicking button on bottom right of rail
    def toggle_collapse_rail(self, e: ft.Event[ft.IconButton]):
        ''' Collapses or expands the rail, and saves the state in settings '''
        from models.app import app    # Always grabs updated reference when collapsing/expanding

        # Toggle our collapsed state
        app.settings.update_data(**{'story': {'workspaces_rail_is_collapsed': not app.settings.data.get('story', {}).get('workspaces_rail_is_collapsed', False)}})

        if app.settings.data.get('story', {}).get('workspaces_rail_is_collapsed', False):  # If we are collapsed, make the rail less wide
            self.width = 100
            e.control.icon = ft.Icons.KEYBOARD_DOUBLE_ARROW_RIGHT_ROUNDED
            self.rail_label.opacity = 0
        else:   # If not collapsed, make rail normal size
            self.width = 120
            e.control.icon = ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT_ROUNDED
            self.rail_label.opacity = 1
        self.update()  # Reload the rail to apply changes


    # Called mostly when re-ordering or collapsing the rail. Also called on start
    def build(self) -> ft.Control:
        from models.app import app   

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
            set_tool_mode_button.icon = update_tool_icon()
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
            set_tool_mode_button.bgcolor = None
            set_tool_mode_button.icon = ft.Icons.BUILD_OUTLINED
            set_tool_mode_button.icon = update_tool_icon()
            tool_selector.style.bgcolor = None
            text_settings_button.style.bgcolor = None
            set_text_mode_button.bgcolor = None
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
        def set_tool_mode(e=None):
            nonlocal canvas_settings, paint_settings, brush_selector, set_tool_mode_button, set_text_mode_button, text_settings_button, tool_selector
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
            text_settings_button.style.bgcolor = None
            set_text_mode_button.bgcolor = None
            self.update() 

        def set_text_mode(e=None):
            nonlocal canvas_settings, paint_settings, brush_selector, set_tool_mode_button
            canvas_settings['current_control_mode'] = "text"
            app.settings.update_data(**{'canvas_settings': canvas_settings})
            set_text_mode_button.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
            text_settings_button.style.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
            set_tool_mode_button.bgcolor = None
            set_draw_mode_button.bgcolor = None
            brush_selector.style.bgcolor = None
            tool_selector.style.bgcolor = None
            set_canvas_mouse_cursor()
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

            #ctrls.append(ft.MenuItemButton(
                #"Close Brush Settings", close_on_click=True, on_click=lambda: None,
                #style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.ERROR, shape=ft.RoundedRectangleBorder(radius=4))))
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
                    ft.DropdownOption(
                        key, key, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                    ) for key, value in self.page.fonts.items()
                    
                ] 
            )

            # TODO: Have value of DD (switching to dif control) reflect the selected font


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
                ft.Row([text_preview], alignment=ft.MainAxisAlignment.CENTER, margin=ft.Margin.all(10)),
                #ft.Row([
                    #ft.Container(text_preview, expand=True, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH, alignment=ft.Alignment.CENTER, border_radius=4, padding=ft.Padding.all(10))
                #]),

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
            #scale=.8, 
            picker_area_border_radius=ft.BorderRadius.all(4)
        )   

        # Create our color selector button
        color_selector = ft.SubmenuButton(
            ft.Icon(ft.Icons.CIRCLE, app.settings.data.get('paint_settings', {}).get('color', ft.Colors.PRIMARY)), 
            tooltip="The color of your brush strokes.",
            on_close=save_color, #expand=True,
            #margin=ft.Margin.only(right=20),
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
        #ft.Icon(ft.Icons.SAVE_ROUNDED, ft.Colors.PRIMARY, scale=0.8),

        def get_color_options() -> list[ft.Control]:
            nonlocal paint_settings, canvas_settings

            def set_saved_color(e: ft.Event[ft.MenuItemButton]):
                nonlocal paint_settings
                color_data = e.control.data
                paint_settings['color'] = color_data.get('value', "#000000")
                app.settings.update_data(**{"paint_settings": {"color": color_data.get('value', "#000000")}})
                color_selector.content = ft.Icon(ft.Icons.CIRCLE, color_data.get('value'))
                brush_preview.content = build_preview_brush()
                self.update()
                update_canvas_tool_preview()

            def delete_color(e: ft.Event[ft.IconButton]):
                nonlocal canvas_settings
                idx = e.control.data
                canvas_settings['saved_colors'].pop(idx)
                app.settings.update_data(**{"canvas_settings": {"saved_colors": canvas_settings['saved_colors']}})
                e.control.parent.parent.parent.controls.remove(e.control.parent.parent)
                e.control.parent.parent.parent.update()

            def save_custom_color(e=None):

                # Saves the color to data and pops the dialog
                def save_color_name(e=None):
                    nonlocal paint_settings, canvas_settings
                    color_name = name_tf.value.strip()
                    current_color = paint_settings.get('color', "#000000")
                    canvas_settings['saved_colors'].append({'name': color_name, 'value': current_color})
                    app.settings.update_data(**{"canvas_settings": {"saved_colors": canvas_settings['saved_colors']}})
                    color_options_button.controls = get_color_options()
                    self.update()
                    self.page.pop_dialog()

            

                name_tf = ft.TextField(label="Color Name", autofocus=True, on_submit=save_color_name, capitalization=ft.TextCapitalization.WORDS)
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
                
                pass

            ctrls = [ft.Text("Saved Colors", color=ft.Colors.ON_SURFACE_VARIANT, italic=True, expand=True, margin=ft.Margin.only(left=4))]
            for idx, color_data in enumerate(canvas_settings.get('saved_colors', [])):
                ctrls.append(
                    ft.MenuItemButton(
                        content=ft.Row([
                            ft.Text(color_data.get('name', 'Unnamed Color')),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR, data=idx, tooltip="Delete this saved color", on_click=delete_color),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), 
                        close_on_click=True,
                        leading=ft.Icon(ft.Icons.CIRCLE, color_data.get('value', "#000000")),
                        on_click=set_saved_color,
                        data=color_data
                    )
                )
            ctrls.append(ft.MenuItemButton(
                "Save current color", True,
                leading=ft.Icon(ft.Icons.SAVE_ROUNDED, ft.Colors.PRIMARY),
                on_click=save_custom_color,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=4), #mouse_cursor=ft.MouseCursor.CLICK,
                    bgcolor=ft.Colors.SURFACE_CONTAINER
                )
            ))
            return ctrls

        color_options_button = ft.SubmenuButton(
            #build_preview_brush(paint_settings),
            controls=get_color_options(),
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
            width=30,
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
            width=30,
        )

        text_preview = ft.Text("Preview text", selectable=True, style=ft.TextStyle(**text_settings))


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
                #mouse_cursor=ft.MouseCursor.CLICK,  
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
            width=30,
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
                        #margin=ft.Margin.only(right=20)
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
                    set_tool_mode_button,
                    border_radius=ft.BorderRadius.only(top_left=4, bottom_left=4),
                ),
                ft.Container(
                    tool_selector,     
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
        ]
        
        # If we're collapsed...
        if app.settings.data.get('story', {}).get('workspaces_rail_is_collapsed', False):

            self.width = 100     # Make the rail less wide
            
            # Set our collapsed icon buttons icon depending on collapsed state
            collapse_icon = ft.Icons.KEYBOARD_DOUBLE_ARROW_RIGHT_ROUNDED

        # If not collapsed, make rail normal size and set the correct icon
        else:
            self.width = 120
            collapse_icon = ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT_ROUNDED

        self.width = 92


        # Set our collapsed icon button using our defined icon above
        self.collapse_icon_button = ft.IconButton(
            collapse_icon, ft.Colors.PRIMARY,
            on_click=self.toggle_collapse_rail,
        )

        self.rail_label = ft.Text(
            "Canvas\nSettings", color=ft.Colors.ON_SURFACE_VARIANT, italic=True, 
            text_align=ft.TextAlign.CENTER,
            #opacity=1 if app.settings.data.get('story', {}).get('workspaces_rail_is_collapsed', False) == False else 0
        )

        

        # Sets our content as a column. This will fill our width and hold...
        # Either our list of workspaces, or a reorderable list of our workspaces
        self.content = ft.Column(
            [ft.Row([self.rail_label], alignment=ft.MainAxisAlignment.CENTER)] + 
            drawing_controls,
            #[ft.Container(expand=True), ft.Row([self.collapse_icon_button], alignment=ft.MainAxisAlignment.END)],
            #horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )

        # If mobile, this will be shown on menubar instead
        self.visible = not self.page.platform.is_mobile()

        # If the user has set to hide the canvas rail, then hide it on startup
        self.visible = app.settings.data.get('story', {}).get('hide_canvas_rail', False) == False  


    