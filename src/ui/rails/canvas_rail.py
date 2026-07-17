""" 
Canvas Rail to display all drawing options and tools 
"""

import flet as ft
from models.views.story import Story
from ui.rails.rail import Rail
from styles.menu_option_style import MenuOptionStyle
import math
from flet_color_pickers import ColorPicker
from models.app import app
import flet.canvas as cv
from utils.safe_string_checker import return_safe_name
from styles.text_fields import TextField


# Class for our Canvas Board rail
class CanvasRail(Rail):

    def __init__(self, story: Story):

        # Initialize the parent Rail class first
        super().__init__(story=story)


        

        text_color_only = app.settings.data.get('canvas_settings', {}).get('text_shape_color', "#FFFFFF").split(",", 1)[0]     # Set color without opacity for the color picker
        self.text_color_picker = ColorPicker(
            color=text_color_only, on_color_change=self._set_text_color, 
            scale=.8, 
            picker_area_border_radius=ft.BorderRadius.all(4)
        )   # Set our color pickers color 

        text_shadow_color_only = app.settings.data.get('canvas_settings', {}).get('text_shadow_color', "#00000000").split(",", 1)[0]     # Set color without opacity for the color picker
        self.text_shadow_color_picker = ColorPicker(
            color=text_shadow_color_only, on_color_change=self._set_text_shadow_color, 
            scale=.8, 
            picker_area_border_radius=ft.BorderRadius.all(4)
        )   # Set our color pickers color   
            
    

    async def _set_text_color(self, e):
        self.text_color_picker.color = e.data

    async def _set_text_shadow_color(self, e):
        self.text_shadow_color_picker.color = e.data
    
    

    async def _save_text_color(self, e: ft.Event):   
        app.settings.update_data(**{"canvas_settings": {"text_shape_color": self.text_color_picker.color}})
        #brush_selector.content = build_preview_brush(app.settings.data.get('paint_settings', {}))
        #brush_selector.update()
        print(e.control)
        #await self.update_tool_preview()

    async def _save_text_shadow_color(self, e=None):
        app.settings.data['canvas_settings']['text_shadow_color'] = self.text_shadow_color_picker.color
        app.settings.update_data(**{"canvas_settings": {"text_shadow_color": self.text_shadow_color_picker.color}})
        #brush_selector.content = build_preview_brush(app.settings.data.get('paint_settings', {}))
        #brush_selector.update()
        #await self.update_tool_preview()

    
            
    async def _set_active_tool(self, e: ft.Event):
        tool_name = e.control.data
        app.settings.update_data(**{"canvas_settings": {"current_control_mode": "tool", "current_tool_name": tool_name}})
        #brush_selector.content = build_preview_brush(app.settings.data.get('paint_settings', {}))
        #brush_selector.update()
        for widget in self.story.widgets.values():
            if widget.data.get('tag') == "canvas":
                if widget.data.get('visible', True):
                    await widget.set_mouse_cursor()


    def get_tool_options(self) -> list[ft.Control]:
        ''' Gets our tool options for the popup menu. '''

        return [
            ft.Text("Tools", color=ft.Colors.ON_SURFACE_VARIANT, italic=True),   # Placeholder for shapes section
            ft.MenuItemButton(
                ft.Row([
                    ft.Text("Erase", overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                    ft.Icon(ft.Icons.AUTO_FIX_NORMAL, ft.Colors.PRIMARY)
                ]),
                data="erase",
                on_click=self._set_active_tool,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor=ft.MouseCursor.CLICK),
                tooltip="Erase parts of your Canvas using your current brush width"
            ),
            ft.MenuItemButton(
                ft.Row([
                    ft.Text("Line", overflow=ft.TextOverflow.ELLIPSIS, expand=True), 
                    ft.Icon(ft.Icons.REMOVE, ft.Colors.PRIMARY)
                ]),
                data="line",
                on_click=self._set_active_tool,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor=ft.MouseCursor.CLICK),
                tooltip="Draw straight lines. Click and drag to draw a line between your starting point and the current position of your mouse."
            ),
            ft.MenuItemButton(
                ft.Row([
                    ft.Text("Text", overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                    ft.Icon(ft.Icons.TEXT_FIELDS, ft.Colors.PRIMARY)
                ]),
                data="text",
                on_click=self._set_active_tool,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor=ft.MouseCursor.CLICK),
                tooltip="Add text only to your canvas. Useful for labels"
            ),
            

            # Shapes we can use
            ft.Divider(), 
            ft.Text("Shapes", color=ft.Colors.ON_SURFACE_VARIANT, italic=True),   # Placeholder for shapes section
            
            #ft.MenuItemButton(
                #ft.Row([
                    #ft.Text("Dialogue Box", overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                    #ft.Icon(ft.CupertinoIcons.BUBBLE_LEFT_FILL, ft.Colors.PRIMARY)
                    # ft.CupertinoIcons.CHAT_BUBBLE
                #]),
                #data="dialogue_box",
                #on_click=self._set_active_tool,
                #style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor=ft.MouseCursor.CLICK),
                #tooltip="Add dialogue boxes to your canvas"
            #),

            ft.MenuItemButton(
                ft.Row([
                    ft.Text("Circle", overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                    ft.Icon(ft.Icons.CIRCLE, ft.Colors.PRIMARY)
                ]),
                data="circle",
                on_click=self._set_active_tool,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor=ft.MouseCursor.CLICK),
                tooltip="Add perfect circles to your canvas"
            ),
            ft.MenuItemButton(
                ft.Row([
                    ft.Text("Oval", overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                    ft.Icon(ft.Icons.CIRCLE, ft.Colors.PRIMARY, scale=ft.Scale(scale_x=0.8))
                ]),
                data="oval",
                on_click=self._set_active_tool,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor=ft.MouseCursor.CLICK),
                tooltip="Add ovals and ellipses to your canvas"
            ),
            ft.MenuItemButton(
                ft.Row([
                    ft.Text("Arc", overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                    ft.Icon(ft.CupertinoIcons.CIRCLE_RIGHTHALF_FILL, ft.Colors.PRIMARY, rotate=math.pi/2)   
                ]),
                data="arc",
                on_click=self._set_active_tool,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor=ft.MouseCursor.CLICK),
                tooltip="Add arcs and partial circles to your canvas"
            ),
            ft.MenuItemButton(
                ft.Row([
                    ft.Text("Rectangle", overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                    ft.Icon(ft.Icons.RECTANGLE, ft.Colors.PRIMARY)
                ]),
                data="rectangle",
                on_click=self._set_active_tool,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor=ft.MouseCursor.CLICK),
                tooltip="Add rectangles and squares to your canvas"
            ),
            ft.MenuItemButton(
                ft.Row([
                    ft.Text("Triangle", overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                    ft.Icon(ft.CupertinoIcons.ARROWTRIANGLE_UP_FILL, ft.Colors.PRIMARY)
                ]),
                data="triangle",
                on_click=self._set_active_tool,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor=ft.MouseCursor.CLICK),
                tooltip="Add triangles to your canvas"
            ),    
        ]

        
    

    
        

    
    
    

    # Build the canvas rail
    def build(self):

        # Our settings for easier reference
        paint_settings: dict
        canvas_settings: dict

        # UI elements used in the canvas rail
        color_picker: ColorPicker              # Color picker for changing brush color
        color_selector: ft.SubmenuButton       # Button on the rail for selected a color. Clicking shows our color picker

        set_draw_mode_button: ft.IconButton          # Button for setting draw mode on the current brush. Only does anything if in tool mode
        brush_selector: ft.SubmenuButton        # Button on the rail for selecting a brush. Clicking shows our brush options
        save_custom_brush_button: ft.IconButton        # Saves the current brush settings as a new custom brush

        set_tool_mode_button: ft.IconButton          # Button for setting tool mode on the current brush. Only does anything if in draw mode
        tool_selector: ft.SubmenuButton         # Button on the rail for selecting a tool. Clicking shows our tool options
        path_smoothing_strength_slider : ft.Slider              # Slider for changing the strength of the smooth stroke effect

        width_slider: ft.Slider                 # Slider for changing the paint width
        blur_slider: ft.Slider                  # Slider for changing the paint blur

        fill_switch: ft.Switch                    # Switch for changing the paint style to fill or not
        anti_alias_switch: ft.Switch                    # Switch for enabling anti-aliasing or not on the current paint

        stroke_smoothing_switch: ft.Switch        # If we should use path smoothing switch
        
        
        stroke_dashed_pattern_switch: ft.Switch            # Switch for enabling dashed strokes or not
        # Something stroke dashed editor here

        stroke_cap_selector: ft.SubmenuButton            # Button for selecting the stroke cap of the current paint
        stroke_join_selector: ft.SubmenuButton           # Button for selecting the stroke join of the current paint
        blend_mode_selector: ft.SubmenuButton            # Button for selecting the blend mode of the current paint


        # Updates any live text tools if we changed a setting that would affect it
        def update_tool_preview():
            nonlocal canvas_settings, paint_settings
            decoration = canvas_settings.get('text_shape_decoration', "none")
            match decoration:
                case "Underline": text_decoration = ft.TextDecoration.UNDERLINE
                case "Overline": text_decoration = ft.TextDecoration.OVERLINE
                case "Line Through": text_decoration = ft.TextDecoration.LINE_THROUGH
                case _: text_decoration = None

            # Check any visible canvases
            for widget in self.story.workspace.tab_view.controls:
                if widget.data.get('tag') == "canvas":

                    # If they're manipulating a shape, adjust the paint settings to match
                    if widget.manipulating_shape:

                        # TODO: Write update function in the canvas that re-grabs the correct paint settings from the app data and applies it to the shape
                        # Then just call that here, or before the manipulating_shape check
                    
                        # Fix any paint changes
                        widget.active_tool.paint.color = app.settings.data.get('update_paint_blend_mode', {}).get('color', ft.Colors.BLACK) if canvas_settings.get('use_paint_for_shapes', True) else ft.Colors.BLACK
                        widget.active_tool.paint.stroke_width=app.settings.data.get('update_paint_blend_mode', {}).get('stroke_width', 3) if canvas_settings.get('use_paint_for_shapes', True) else 3
                        widget.active_tool.paint.style=app.settings.data.get('update_paint_blend_mode', {}).get('style', ft.PaintingStyle.STROKE)
                        widget.active_tool.paint.stroke_cap=app.settings.data.get('update_paint_blend_mode', {}).get('stroke_cap', "round") if canvas_settings.get('use_paint_for_shapes', True) else "round"
                        widget.active_tool.paint.stroke_join=app.settings.data.get('update_paint_blend_mode', {}).get('stroke_join', "round") if canvas_settings.get('use_paint_for_shapes', True) else "round"
                        widget.active_tool.paint.blur_image=app.settings.data.get('update_paint_blend_mode', {}).get('blur_image', 0) if canvas_settings.get('use_paint_for_shapes', True) else 0
                        widget.active_tool.paint.anti_alias=app.settings.data.get('update_paint_blend_mode', {}).get('anti_alias', True) if canvas_settings.get('use_paint_for_shapes', True) else True
                    
                        if widget.active_tool.shape_type == "text":
                            widget.active_tool.cv_shape.style = ft.TextStyle(
                                size=app.settings.data.get('canvas_settings', {}).get('text_shape_size', 20),
                                weight=ft.FontWeight.BOLD if app.settings.data.get('canvas_settings', {}).get('text_shape_bold', False) else ft.FontWeight.NORMAL,
                                color=app.settings.data.get('canvas_settings', {}).get('text_shape_color', ft.Colors.ON_SURFACE),
                                italic=app.settings.data.get('canvas_settings', {}).get('text_shape_italic', False),
                                decoration=text_decoration,
                                #shadow
                                letter_spacing=app.settings.data.get('canvas_settings', {}).get('text_shape_letter_spacing', 0),
                                word_spacing=app.settings.data.get('canvas_settings', {}).get('text_shape_word_spacing', 0),
                            )
                        elif widget.active_tool.shape_type == "rectangle":
                            widget.active_tool.cv_shape.border_radius = ft.BorderRadius.all(
                                app.settings.data.get('canvas_settings', {}).get('rectangle_border_radius', 0)
                            )

                        widget.active_tool.cv_shape.update()
                        break

        # Set the color pickers color upon change
        def set_color(e: ft.Event[ColorPicker]):
            color_picker.color = e.data

        # Saves our color to data and updates the brush selector
        def save_color(e=None):
            paint_settings.update({"color": color_picker.color})
            app.settings.update_data(**{"paint_settings": paint_settings})
            update_brush_preview()
            #update_tool_icon()
            color_selector.trailing.color = color_picker.color
            #tool_selector.trailing.color = color_picker.color
            self.update()

        # Sets current control mode to drawing
        def set_draw_mode(e=None):
            nonlocal canvas_settings, paint_settings, brush_selector, set_draw_mode_button, save_custom_brush_button
            canvas_settings['current_control_mode'] = "draw"
            if app.settings.data.get('paint_settings', {}).get('blend_mode', "") == "clear":
                paint_settings['blend_mode'] = "src_over"
            app.settings.update_data(**{'paint_settings': paint_settings, 'canvas_settings': canvas_settings})
            # Update UI
            update_brush_preview()
            brush_selector.style.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
            color_selector.trailing.color = paint_settings.get('color', "#000000")
            set_draw_mode_button.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
            set_draw_mode_button.icon = ft.Icons.BRUSH_ROUNDED
            set_tool_mode_button.bgcolor = None
            set_tool_mode_button.icon = ft.Icons.BUILD_OUTLINED
            tool_selector.style.bgcolor = None
            save_custom_brush_button.style.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
            save_custom_brush_button.disabled = False
            self.update()

        # Updates the brush preview canvas with the current brush settings upon changes
        def update_brush_preview():
            brush_selector.content = build_preview_brush(paint_settings)

        # Build a small preview of current or passed in brush settings to show in the brush selector
        def build_preview_brush(brush_settings: dict=None) -> ft.Control:
            nonlocal paint_settings

            # Set current settings or passed in settings
            if brush_settings is None:
                brush_settings = paint_settings.copy()
            else:
                brush_settings = brush_settings.copy()

            # Create our preview canvas. Paint like w=100, and h=30. Extra height is justp adding
            preview_canvas = cv.Canvas(width=105, height=35)

            # Set max values of paint so that it fits normally on our small preview
            if brush_settings.get('stroke_width', 3) > 6:
                brush_settings['stroke_width'] = 6
            if brush_settings.get('blur_image', 0) > 6:
                brush_settings['blur_image'] = 6
            brush_settings['blend_mode'] = None     # Turn off blend mode

            # Paint the stroke with safe paint settings
            preview_canvas.shapes = [
                cv.Path([
                    cv.Path.MoveTo(5, 25),
                    cv.Path.CubicTo(5, 25, 10, 16, 50, 15),
                    cv.Path.CubicTo(50, 15, 90, 14, 100, 5)
                ], brush_settings)
            ]
            return preview_canvas   # Return the canvas
        
        # Sets current brush settings using passed in brush settings
        def set_active_brush(brush_settings: dict, name: str):
            nonlocal canvas_settings, paint_settings
            canvas_settings.update({"current_control_mode": {'current_control_mode': "draw", 'current_brush_name': name}})
            paint_settings.update(**brush_settings)
            app.settings.update_data(**{"canvas_settings": canvas_settings, "paint_settings": brush_settings})
            update_brush_preview()
            set_draw_mode()
            self.update()


        # builds a list of our built in and custom brush options for our brush selector when its open
        def get_brush_options() -> list[ft.Control]:
            ''' Gets our brush options for the popup menu. '''
            
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

            # Start by building our default brush options
            options = [
                ft.Text("Default Brushes", color=ft.Colors.ON_SURFACE_VARIANT, italic=True, margin=ft.Margin.only(left=4)),   # Placeholder for shapes section
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
                    

                ft.Divider(),   # Placeholder for shapes section
                ft.Text("Saved Brushes", color=ft.Colors.ON_SURFACE_VARIANT, italic=True, margin=ft.Margin.only(left=4)),   # Placeholder for shapes section
            ]

            # Go through our saved brushes and add options to select them
            for name, brush_settings in app.settings.data.get('canvas_settings', {}).get('saved_brushes', {}).items():
                options.append(
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

            return options
        
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

            content = ft.Column([new_custom_brush_name_text_field], scroll="auto", height=self.page.height / 2) 

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
            match app.settings.data.get('canvas_settings', {}).get('current_tool_name', ""):
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
            nonlocal canvas_settings, paint_settings, brush_selector, set_tool_mode_button, save_custom_brush_button
            canvas_settings['current_control_mode'] = "tool"
            app.settings.update_data(**{'canvas_settings': canvas_settings})
            # Update buttons
            brush_selector.style.bgcolor = None
            set_draw_mode_button.bgcolor = None
            set_draw_mode_button.icon = ft.Icons.BRUSH_OUTLINED
            set_tool_mode_button.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
            set_tool_mode_button.icon = ft.Icons.BUILD_ROUNDED
            tool_selector.style.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
            save_custom_brush_button.style.bgcolor = None
            save_custom_brush_button.disabled = True
            self.update() 

        # Called when changing paint width
        def update_paint_width(e: ft.Event[ft.Slider]):
            nonlocal paint_settings
            paint_settings.update({"stroke_width": int(e.control.value)})
            app.settings.update_data(**{"paint_settings": paint_settings})
            update_brush_preview()
            self.update()

        # Called when changing paint width
        def update_paint_blur(e: ft.Event[ft.Slider]):
            nonlocal paint_settings
            paint_settings.update({"blur_image": int(e.control.value)})
            app.settings.update_data(**{"paint_settings": paint_settings})
            update_brush_preview()
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
            update_brush_preview()
            self.update()

        # Called when changing paint anti-aliasing
        def update_paint_anti_alias(e: ft.Event[ft.Switch]):
            nonlocal paint_settings
            paint_settings.update({"anti_alias": e.control.value})
            app.settings.update_data(**{"paint_settings": paint_settings})
            update_brush_preview()
            self.update()

        # Updates whether we'll use path smoothing or not
        def update_paint_stoke_smoothing(e: ft.Event[ft.Switch]):
            nonlocal canvas_settings
            canvas_settings.update({"use_stroke_smoothing": e.control.value})
            app.settings.update_data(**{"canvas_settings": canvas_settings})

        # Updates the strength of the smooth stroke effect
        def update_paint_path_smoothing_strength(e: ft.Event[ft.Slider]):
            nonlocal canvas_settings
            canvas_settings.update({"path_smoothing_strength": e.control.value})
            app.settings.update_data(**{"canvas_settings": canvas_settings})

        # Returns the correct icon for the current stroke cap setting based on current paint settings
        def get_stroke_cap_icon() -> ft.Icon:
            nonlocal paint_settings
            stroke_cap = paint_settings.get('stroke_cap', 'butt')
            if stroke_cap == 'round': return ft.Icons.CIRCLE_OUTLINED
            elif stroke_cap == 'square':return ft.Icons.SQUARE_OUTLINED
            else: return ft.Icons.CROP_SQUARE_OUTLINED

        # Updates the stroke cap of the current paint
        def update_paint_stroke_cap(e: ft.Event[ft.MenuItemButton]):
            nonlocal paint_settings
            new_stroke_cap = e.control.content.lower()
            paint_settings['stroke_cap'] = new_stroke_cap
            app.settings.update_data(**{"paint_settings": {"stroke_cap": new_stroke_cap}})
            stroke_cap_selector.trailing.icon = get_stroke_cap_icon()
            update_brush_preview()
            self.update()

        # Returns the correct icon for the current stroke join setting based on current paint settings
        def get_stroke_join_icon() -> ft.Icon:
            nonlocal paint_settings
            stroke_join = paint_settings.get('stroke_join', 'miter')
            if stroke_join == 'round': return ft.Icons.CIRCLE_OUTLINED
            elif stroke_join == 'bevel': return ft.Icons.SQUARE_OUTLINED
            else: return ft.Icons.CROP_SQUARE_OUTLINED

        # Updates the stroke join of the current paint
        async def update_paint_stroke_join(e: ft.Event[ft.SubmenuButton]):
            nonlocal paint_settings
            new_stroke_join = e.control.content.lower()
            paint_settings['stroke_join'] = new_stroke_join
            app.settings.update_data(**{"paint_settings": {"stroke_join": new_stroke_join}})
            stroke_join_selector.trailing.icon = get_stroke_join_icon()
            update_brush_preview()
            self.update()

        # Set the blend mode label based on current mode in settings
        def set_blend_mode_label() -> str:
            nonlocal paint_settings
            mode = paint_settings.get('blend_mode', 'src_over')
            if mode is None:
                return f"Blend Mode: None"
            return f"Blend Mode: {mode.replace("_", " ").title()}"
            
        # Get the options for blend modes
        def get_blend_mode_options() -> list[ft.Control]:
            ''' Gets our blend mode options for the popup menu. '''

            return [
                ft.MenuItemButton("None",  on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data=None, tooltip="No blend mode"),
                ft.MenuItemButton("Color", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="color", tooltip="Take the hue and saturation of the source image, and the luminosity of the destination image"),
                ft.MenuItemButton("Color Burn", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="color_burn", tooltip="Divide the inverse of the destination by the source, and inverse the result"),
                ft.MenuItemButton("Color Dodge", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="color_dodge", tooltip="Divide the destination by the inverse of the source"),
                ft.MenuItemButton("Darken", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="darken", tooltip="Composite the source and destination image by choosing the lowest value from each color channel"),
                ft.MenuItemButton("Difference", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="difference", tooltip="Subtract the smaller value from the bigger value for each channel"),
                ft.MenuItemButton("Destination", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="dst", tooltip="Drop the source image, only paint the destination image"),
                ft.MenuItemButton("Destination Atop Source", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="dst_a_top", tooltip="Composite the destination image over the source image, but only where it overlaps the source"),
                ft.MenuItemButton("Destination In", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="dst_in", tooltip="Show the destination image, but only where the two images overlap. The source image is not rendered, it is treated merely as a mask. The color channels of the source are ignored, only the opacity has an effect"),
                ft.MenuItemButton("Destination Out", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="dst_out", tooltip="Show the destination image, but only where the two images do not overlap. The source image is not rendered, it is treated merely as a mask. The color channels of the source are ignored, only the opacity has an effect"),
                ft.MenuItemButton("Destination Over", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="dst_over", tooltip="Composite the source image under the destination image"),
                ft.MenuItemButton("Exclusion", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="exclusion", tooltip="Subtract double the product of the two images from the sum of the two images."),
                ft.MenuItemButton("Hard Light", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="hard_light", tooltip="Multiply the components of the source and destination images after adjusting them to favor the source"),
                ft.MenuItemButton("Hue", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="hue", tooltip="Take the hue of the source image, and the saturation and luminosity of the destination image"),
                ft.MenuItemButton("Lighten", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="lighten", tooltip="Composite the source and destination image by choosing the highest value from each color channel"),
                ft.MenuItemButton("Luminosity", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="luminosity", tooltip="Take the luminosity of the source image, and the hue and saturation of the destination image"),
                ft.MenuItemButton("Modulate", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="modulate", tooltip="Multiply the color components of the source and destination images"),
                ft.MenuItemButton("Multiply", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="multiply", tooltip="Multiply the components of the source and destination images, including the alpha channel"),
                ft.MenuItemButton("Overlay", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="overlay", tooltip="Multiply the components of the source and destination images after adjusting them to favor the destination"),
                ft.MenuItemButton("Plus", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="plus", tooltip="Sum the components of the source and destination images"),
                ft.MenuItemButton("Saturation", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="saturation", tooltip="Take the saturation of the source image, and the hue and luminosity of the destination image"),
                ft.MenuItemButton("Screen", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="screen", tooltip="Multiply the inverse of the components of the source and destination images, and inverse the result"),
                ft.MenuItemButton("Soft Light", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="soft_light", tooltip="Somewhere between Overlay and Color blend modes"),
                ft.MenuItemButton("Source", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="src", tooltip="Drop the destination image, only paint the source image"),
                ft.MenuItemButton("Soure Atop Destination", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="src_a_top", tooltip="Composite the source image over the destination image, but only where it overlaps the destination"),
                ft.MenuItemButton("Source In", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="src_in", tooltip="Show the source image, but only where the two images overlap. The destination image is not rendered, it is treated merely as a mask. The color channels of the destination are ignored, only the opacity has an effect"),
                ft.MenuItemButton("Source Out", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="src_out", tooltip="Show the source image, but only where the two images do not overlap. The destination image is not rendered, it is treated merely as a mask. The color channels of the destination are ignored, only the opacity has an effect"),
                ft.MenuItemButton("XOR", on_click=update_paint_blend_mode, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="xor", tooltip="Apply a bitwise xor operator to the source and destination images. This leaves transparency where they would overlap"),
            ]
        
        # Updates the blend mode of the current paint settings
        def update_paint_blend_mode(e: ft.Event[ft.MenuItemButton]):
            nonlocal paint_settings
            mode = e.control.data
            paint_settings.update({"blend_mode": mode})
            app.settings.update_data(**{"paint_settings": paint_settings})
            blend_mode_selector.content = set_blend_mode_label()
            self.update()

        # Grab our data for easier manipulation
        paint_settings = app.settings.data.get('paint_settings', {}).copy()
        canvas_settings = app.settings.data.get('canvas_settings', {}).copy()

        # Color picker for changing brush color
        color_picker = ColorPicker(
            color=paint_settings.get('color', "#000000").split(",", 1)[0], 
            on_color_change=set_color, 
            scale=.8, 
            picker_area_border_radius=ft.BorderRadius.all(4)
        )   


        # Create our color selector button
        color_selector = ft.SubmenuButton(
            "Color",
            trailing=ft.Icon(ft.Icons.COLOR_LENS_ROUNDED, app.settings.data.get('paint_settings', {}).get('color', ft.Colors.PRIMARY)), 
            tooltip="The color of your brush strokes.",
            on_close=save_color, expand=True,
            controls=[ft.Column([
                color_picker,  
                ft.MenuItemButton(
                    "Set Color", 
                    on_click=lambda: None,  # Something so its not disabled
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor=ft.MouseCursor.CLICK,
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
                    )
                )
            ])],
            style=ft.ButtonStyle(
                mouse_cursor=ft.MouseCursor.CLICK,  
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                shape=ft.RoundedRectangleBorder(radius=4),
            ),
            menu_style=ft.MenuStyle(
                alignment=ft.Alignment.TOP_RIGHT,
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
            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, shape=ft.RoundedRectangleBorder(radius=4)),
            tooltip="Set the active control to the last used brush",
            data="draw", on_click=set_draw_mode
        )

        # Selector to choose a build in brush or a custom brush
        brush_selector = ft.SubmenuButton(
            build_preview_brush(paint_settings),
            get_brush_options(),
            trailing=ft.Icon(ft.Icons.ARROW_DROP_DOWN, ft.Colors.ON_SURFACE_VARIANT, scale=0.8),
            style=ft.ButtonStyle(
                mouse_cursor=ft.MouseCursor.CLICK,  
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if app.settings.data.get('canvas_settings', {}).get('current_control_mode', '') == "draw" else None,
                shape=ft.RoundedRectangleBorder(radius=4),
                #padding=ft.Padding.only(left=4),
            ),
            menu_style=ft.MenuStyle(
                alignment=ft.Alignment.TOP_RIGHT,
                bgcolor=ft.Colors.SURFACE_CONTAINER, 
                shape=ft.RoundedRectangleBorder(radius=4),
            ),
            expand=True,
        )

        # Button to save current paint settings as a custom brush
        save_custom_brush_button = ft.IconButton(      
            ft.Icons.SAVE_ROUNDED, ft.Colors.PRIMARY,
            tooltip="Save current brush settings as a custom brush", 
            on_click=save_custom_brush_clicked, mouse_cursor=ft.MouseCursor.CLICK,
            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                shape=ft.RoundedRectangleBorder(radius=4), padding=ft.Padding.all(0)),
        )  

        # Button to set the control mode to tool mode
        set_tool_mode_button = ft.IconButton(
            ft.Icons.BUILD_ROUNDED if app.settings.data.get('canvas_settings', {}).get('current_control_mode', 'draw') == "tool" else ft.Icons.BUILD_OUTLINED,
            ft.Colors.PRIMARY,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if app.settings.data.get('canvas_settings', {}).get('current_control_mode', 'draw') == "tool" else None,
            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, shape=ft.RoundedRectangleBorder(radius=4)),
            tooltip="Set the active control to the last used tool",
            data="tool", on_click=set_tool_mode
        )

        # Selector to choose a tool to use on the canvas
        tool_selector = ft.SubmenuButton(
            update_tool_icon(),
            self.get_tool_options(),
            
            trailing=ft.Icon(ft.Icons.ARROW_DROP_DOWN, ft.Colors.ON_SURFACE_VARIANT, scale=0.8),
            style=ft.ButtonStyle(
                mouse_cursor=ft.MouseCursor.CLICK,  
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if app.settings.data.get('canvas_settings', {}).get('current_control_mode', '') == "tool" else None,
                shape=ft.RoundedRectangleBorder(radius=4),
                padding=ft.Padding.only(left=4),
            ),
            menu_style=ft.MenuStyle(
                alignment=ft.Alignment.TOP_RIGHT,
                bgcolor=ft.Colors.SURFACE_CONTAINER, 
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            expand=True,
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

        # Strength path smoothing effect
        path_smoothing_strength_slider = ft.Slider(
            min=1, max=10,  expand=True,
            divisions=10, value=canvas_settings.get('path_smoothing_strength', 1),
            label="Strength: {value}",
            on_change_end=update_paint_path_smoothing_strength,
            tooltip="The strength of the stroke smoothing effect. Higher values will make strokes appear smoother and more natural",
        )

        # Whether to fill strokes and shapes or not
        fill_switch = ft.Switch(
            True, "Fill Paint", on_change=update_paint_fill,
            label_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=12),
            value=paint_settings.get('style', 'stroke').endswith('_fill'),
            tooltip="Whether to fill strokes and shapes, or leave them hollow (Transparent)",
            #label_position=ft.LabelPosition.LEFT
        )

        # If we use anti aliasing or not
        anti_alias_switch = ft.Switch(
            True, "Anti-Aliasing", on_change=update_paint_anti_alias,
            label_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=12),
            value=paint_settings.get('anti_alias', True),
            tooltip="Whether to use anti-aliasing for smoother brush strokes. Disabling may result in jagged edges",
        )

        # Toggles path smoothing
        stroke_smoothing_switch =  ft.Switch(
            True, "Stroke Smoothing", on_change=update_paint_stoke_smoothing,
            label_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=12),
            value=canvas_settings.get('use_stroke_smoothing', True),
            tooltip="Makes the brushes paint color appear consistant for an entire stroke, especially at lower opacity values.",
        )

        

        # Selector for the shape of the ends of strokes
        stroke_cap_selector = ft.SubmenuButton(
            "Stroke Cap Shape",
            trailing=ft.Icon(get_stroke_cap_icon(), ft.Colors.PRIMARY),
            tooltip="The shape that your brush strokes will have at the end of each line segment.",
            menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
            style=ft.ButtonStyle(
                padding=ft.Padding.only(left=4, right=4), alignment=ft.Alignment.CENTER, mouse_cursor="click", #bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                shape=ft.RoundedRectangleBorder(radius=4),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            ),
            controls=[
                ft.MenuItemButton("Butt", on_click=update_paint_stroke_cap, leading=ft.Icon(ft.Icons.CROP_SQUARE_OUTLINED, ft.Colors.PRIMARY), style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),),
                ft.MenuItemButton("Round", on_click=update_paint_stroke_cap, leading=ft.Icon(ft.Icons.CIRCLE_OUTLINED, ft.Colors.PRIMARY), style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),),
                ft.MenuItemButton("Square", on_click=update_paint_stroke_cap, leading=ft.Icon(ft.Icons.SQUARE_OUTLINED, ft.Colors.PRIMARY), style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),),
            ]
        )

        # Selector for the shape of sharp turns and joins in strokes
        stroke_join_selector = ft.SubmenuButton(
            "Stroke Join Shape",
            trailing=ft.Icon(get_stroke_join_icon(), ft.Colors.PRIMARY),  
            tooltip="The shape that your brush strokes will have at the join of two line segments, or sharp corners.",
            menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
            style=ft.ButtonStyle(
                padding=ft.Padding.only(left=4, right=4), alignment=ft.Alignment.CENTER, mouse_cursor="click",
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                shape=ft.RoundedRectangleBorder(radius=4)
            ),
            controls=[
                ft.MenuItemButton("Miter", leading=ft.Icon(ft.Icons.CROP_SQUARE_OUTLINED, ft.Colors.PRIMARY), on_click=update_paint_stroke_join, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),),
                ft.MenuItemButton("Round", leading=ft.Icon(ft.Icons.CIRCLE_OUTLINED, ft.Colors.PRIMARY), on_click=update_paint_stroke_join, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),),
                ft.MenuItemButton("Bevel", leading=ft.Icon(ft.Icons.SQUARE_OUTLINED, ft.Colors.PRIMARY), on_click=update_paint_stroke_join, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),),
            ]
        )

        # Selector for the blend mode of the brush strokes
        blend_mode_selector = ft.SubmenuButton(
            set_blend_mode_label(), 
            controls=get_blend_mode_options(),
            tooltip="The Current blend effects applied to your brush strokes. \nSome blend modes don't render correctly until AFTER a stroke is completed.",
            menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
            style=ft.ButtonStyle(
                padding=ft.Padding.only(left=4, right=4), alignment=ft.Alignment.CENTER,
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click", 
            ),
        )
        

        


        

        

        async def _change_shape_options(e):
            option = e.control.data
            value = e.control.value
            
            match option:
                case "size":
                    app.settings.data['canvas_settings']['text_shape_size'] = int(value) or 0
                case "bold":
                    app.settings.data['canvas_settings']['text_shape_bold'] = value or False
                case "italic":
                    app.settings.data['canvas_settings']['text_shape_italic'] = value or False
                case "decoration":
                    app.settings.data['canvas_settings']['text_shape_decoration'] = value or "None"
                case "letter_spacing":
                    app.settings.data['canvas_settings']['text_shape_letter_spacing'] = int(value) or 0
                case "word_spacing":
                    app.settings.data['canvas_settings']['text_shape_word_spacing'] = int(value) or 0
                case "border_radius":
                    app.settings.data['canvas_settings']['rectangle_border_radius'] = int(value) or 0
                case "use_paint_for_shapes":
                    app.settings.data['canvas_settings']['use_paint_for_shapes'] = value or False
            app.settings.update_data(**{"canvas_settings": app.settings.data['canvas_settings']})
            #await self.update_tool_preview()


        text_color_selector = ft.SubmenuButton(
            "Text Color",
            trailing=ft.Icon(ft.Icons.COLOR_LENS_ROUNDED, app.settings.data.get('canvas_settings', {}).get('text_shape_color', ft.Colors.ON_SURFACE)),
            #width=40,
            tooltip="The color of text added with the text tool",
            on_close=self._save_text_color, expand=True,
            controls=[ft.Column([
                self.text_color_picker,  
                ft.MenuItemButton(
                    "Set Color", on_click=lambda: None,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click")
                )
            ])],
            style=ft.ButtonStyle(
                mouse_cursor=ft.MouseCursor.CLICK,  
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                shape=ft.RoundedRectangleBorder(radius=4),
                #padding=ft.Padding.all(0),
            ),
            menu_style=ft.MenuStyle(
                alignment=ft.Alignment.TOP_RIGHT,
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, 
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding.all(0)
            ),
        )

        text_shadow_color_selector = ft.SubmenuButton(
            "Text Shadow Color",
            trailing=ft.Icon(ft.Icons.COLOR_LENS_ROUNDED, app.settings.data.get('canvas_settings', {}).get('text_shape_color', ft.Colors.ON_SURFACE)),
            #width=40,
            tooltip="The color of text added with the text tool",
            on_close=self._save_text_shadow_color, expand=True,
            controls=[ft.Column([
                self.text_shadow_color_picker,  
                ft.MenuItemButton(
                    "Set Color", on_click=lambda: None,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click")
                )
            ])],
            style=ft.ButtonStyle(
                mouse_cursor=ft.MouseCursor.CLICK,  
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                shape=ft.RoundedRectangleBorder(radius=4),
                #padding=ft.Padding.all(0),
            ),
            menu_style=ft.MenuStyle(
                alignment=ft.Alignment.TOP_RIGHT,
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, 
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding.all(0)
            ),
        )

        async def _change_text_decoration(e):
            decoration = str(e.control.content)
            app.settings.data['canvas_settings']['text_shape_decoration'] = decoration or "None"
            match decoration:
                case "Underline":
                    new_icon = ft.Icons.FORMAT_UNDERLINE
                case "Overline":
                    new_icon = ft.Icons.FORMAT_OVERLINE
                case "Line Through":
                    new_icon = ft.Icons.FORMAT_STRIKETHROUGH
                case _:
                    new_icon = ft.Icons.FORMAT_CLEAR

            app.settings.update_data(**{"canvas_settings": {"text_shape_decoration": decoration}})
            #await self.update_tool_preview()
            text_decoration_selector.trailing.icon = new_icon
            text_decoration_selector.update()

        match app.settings.data.get('canvas_settings', {}).get('text_shape_decoration', 'none'):
            case "Underline":
                text_decoration_trailing_icon = ft.Icons.FORMAT_UNDERLINE
            case "Overline":
                text_decoration_trailing_icon = ft.Icons.FORMAT_OVERLINE    

            case "Line Through":
                text_decoration_trailing_icon = ft.Icons.FORMAT_STRIKETHROUGH
            case _:
                text_decoration_trailing_icon = ft.Icons.FORMAT_CLEAR
        text_decoration_selector = ft.SubmenuButton(
            "Text Decoration",
            [
                ft.MenuItemButton(
                    "None", 
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    on_click=_change_text_decoration,
                ),
                ft.MenuItemButton(
                    "Underline", 
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    on_click=_change_text_decoration,
                ),
                ft.MenuItemButton(
                    "Overline",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    on_click=_change_text_decoration,
                ),
                ft.MenuItemButton(
                    "Line Through", 
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    on_click=_change_text_decoration,
                ),
                
            ],
            trailing=ft.Icon(text_decoration_trailing_icon, app.settings.data.get('canvas_settings', {}).get('text_shape_color', ft.Colors.ON_SURFACE)),
            
            tooltip="The text decoration for text shapes",
            menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10)),
            style=ft.ButtonStyle(
                mouse_cursor=ft.MouseCursor.CLICK,  
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                shape=ft.RoundedRectangleBorder(radius=4),
                #padding=ft.Padding.all(0),
            ),
        )
        
        
        # Build the content of our rail
        content = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            margin=ft.Margin.only(left=8),
            spacing=4,
            expand=True,
            controls=[
                # New item tf for canvas boards
                self.new_item_textfield,

                # Label brush settings
                ft.Text("Brush Settings", theme_style=ft.TextThemeStyle.LABEL_LARGE, weight=ft.FontWeight.W_500, 
                        italic=True, color=ft.Colors.ON_SURFACE_VARIANT, expand=True),
            
                # Hold our color selector
                ft.MenuBar(
                    [color_selector],
                    style=ft.MenuStyle(bgcolor="transparent", shadow_color="transparent", padding=ft.Padding.all(0)),
                ),

                # Our set_draw_mode_button, brush selector, and save custom brush button
                ft.Row([
                    set_draw_mode_button, 
                    ft.MenuBar([brush_selector], style=ft.MenuStyle(bgcolor="transparent", shadow_color="transparent", padding=ft.Padding.all(0))),
                    save_custom_brush_button
                ], spacing=4, wrap=True),  
                
                # Row to set the tool mode , select a tool, and show a note about the current tool
                ft.Row([
                    set_tool_mode_button, 
                    ft.MenuBar([tool_selector], style=ft.MenuStyle(bgcolor="transparent", shadow_color="transparent", padding=ft.Padding.all(0))),
                ], spacing=4, wrap=True),
                    
                # Slider about the width of the current brush strokes
                ft.Row([ft.Text("Size", theme_style=ft.TextThemeStyle.LABEL_LARGE), width_slider], spacing=0, tooltip="Size of your strokes"),      # Size slider

                # Slider about the blur of the current brush strokes
                ft.Row([ft.Text("Blur", theme_style=ft.TextThemeStyle.LABEL_LARGE), blur_slider], spacing=0),

                # Slider for the strenght of smooth stroke
                ft.Row([ft.Text("Path Smoothing", theme_style=ft.TextThemeStyle.LABEL_LARGE), path_smoothing_strength_slider], spacing=0),

                # Fill and anti alias switches
                fill_switch,    
                anti_alias_switch,    
                stroke_smoothing_switch,                       
                
                # Stroke cap, join, and blend mode selectors
                ft.MenuBar(
                    [stroke_cap_selector],
                    style=ft.MenuStyle(
                        bgcolor="transparent", shadow_color="transparent",
                        shape=ft.RoundedRectangleBorder(radius=4),
                    ),
                ),
                ft.MenuBar(
                    [stroke_join_selector],
                    style=ft.MenuStyle(
                        bgcolor="transparent", shadow_color="transparent",
                        shape=ft.RoundedRectangleBorder(radius=4),
                    ),
                ),
                ft.MenuBar(
                    [blend_mode_selector],
                    style=ft.MenuStyle(
                        bgcolor="transparent", shadow_color="transparent",
                        shape=ft.RoundedRectangleBorder(radius=4),
                    ),
                ),

                # Divider between text and tool settings
                ft.Divider(),
                ft.Text("Text & Tool Settings", theme_style=ft.TextThemeStyle.LABEL_LARGE, weight=ft.FontWeight.W_500, italic=True, color=ft.Colors.ON_SURFACE_VARIANT, expand=True),
            
                # Text Size
                TextField(
                    label="Text Size", on_blur=_change_shape_options, data="size", dense=True,
                    tooltip="The size of text added with the text tool", expand=True,
                    input_filter=ft.NumbersOnlyInputFilter(), #width=100, #expand=True, 
                    value=str(app.settings.data.get('canvas_settings', {}).get('text_shape_size', 16))
                ),

                # Letter spacing
                TextField(
                    label="Letter Spacing", on_blur=_change_shape_options, data="letter_spacing", dense=True, expand=True,
                    input_filter=ft.NumbersOnlyInputFilter(), #width=100, #expand=True, 
                    value=str(app.settings.data.get('canvas_settings', {}).get('text_shape_letter_spacing', 0))
                ),
                
                # Word spacing
                TextField(
                    label="Word Spacing", on_blur=_change_shape_options, data="word_spacing", dense=True, expand=True,
                    input_filter=ft.NumbersOnlyInputFilter(), #width=100, #expand=True, 
                    value=str(app.settings.data.get('canvas_settings', {}).get('text_shape_word_spacing', 0))
                ),
                
                # Border radius on rectangles
                TextField(
                    label="Rectangle Border Radius", on_blur=_change_shape_options, data="border_radius", dense=True,
                    input_filter=ft.NumbersOnlyInputFilter(), #width=100, #expand=True, 
                    value=str(app.settings.data.get('canvas_settings', {}).get('rectangle_border_radius', 0)),
                    expand=True,
                ),

                # Color selector for text shapes
                ft.MenuBar(
                    [text_color_selector],
                    style=ft.MenuStyle(bgcolor="transparent", shadow_color="transparent", padding=ft.Padding.all(0)),
                ),
                ft.MenuBar(
                    [text_decoration_selector], 
                    style=ft.MenuStyle(
                        bgcolor="transparent", shadow_color="transparent", padding=ft.Padding.all(0)
                    ),
                    
                ),
                
                #ft.MenuBar(
                    #[text_shadow_color_selector],
                    #style=ft.MenuStyle(bgcolor="transparent", shadow_color="transparent", padding=ft.Padding.all(0)),
                    #expand=True,
                #),

                ft.Switch(
                    True, "Text Bold", on_change=_change_shape_options, data="bold",
                    label_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=12),
                    value=app.settings.data.get('canvas_settings', {}).get('text_shape_bold', False),
                    tooltip="Whether text shapes will be bold or not",
                    #label_position=ft.LabelPosition.LEFT
                ),
                ft.Switch(
                    True, "Text Italic", on_change=_change_shape_options, data="italic",
                    label_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=12),
                    value=app.settings.data.get('canvas_settings', {}).get('text_shape_italic', False),
                    tooltip="Whether text shapes will be italic or not",
                    #label_position=ft.LabelPosition.LEFT
                ),
        

                ft.Switch(
                    True, "Use Brush Paint for Shapes", on_change=_change_shape_options, data="use_paint_for_shapes",
                    label_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=12),
                    value=app.settings.data.get('canvas_settings', {}).get('use_paint_for_shapes', False),
                    tooltip="Whether shapes will use the current paint settings (color, stroke width, etc) or will just be painted with a standard fill or stroke with no effects. \nFill is always used. Text shapes are not affected by this setting",
                    #label_position=ft.LabelPosition.LEFT
                ), 
                
                
            ]
        )        
        

        # Buttons for the menu bar
        top_row_buttons = [
            ft.SubmenuButton(
                ft.Container(
                    ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, "primary"),
                    padding=ft.Padding.all(8), shape=ft.BoxShape.CIRCLE,
                    width=40, height=40, alignment=ft.Alignment.CENTER
                ),
                [
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.BRUSH_OUTLINED, ft.Colors.PRIMARY), content="Canvas",
                        data="canvas", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new Canvas for sketching drawing, or visual note taking",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), #disabled=True
                    ),
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.SPACE_DASHBOARD_OUTLINED, ft.Colors.PRIMARY), content="Canvas Board",
                        data="canvas_board", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new Canvas Board to organize your canvases and plan your story visually",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    ),
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY), content="Map",
                        data="map", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new Map to visualize the locations of your story and the layout of your world",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    ),
                ],
                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10)),
                style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
            ),
            ft.SubmenuButton(
                ft.Container(
                    ft.Icon(ft.Icons.FILE_UPLOAD_OUTLINED, ft.Colors.OUTLINE),
                    padding=ft.Padding.all(8), shape=ft.BoxShape.CIRCLE,
                    width=40, height=40, alignment=ft.Alignment.CENTER
                ),
                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
                disabled=True
            ),
        ]

        # Set rail menu bar and header controls
        menubar = ft.MenuBar(top_row_buttons, style=ft.MenuStyle(
            bgcolor=ft.Colors.TRANSPARENT, shadow_color=ft.Colors.TRANSPARENT,
            shape=ft.RoundedRectangleBorder(radius=4))
        )
 
        self.controls = [
            ft.Column(
                spacing=0,
                expand=True,
                controls=[
                    ft.Row([menubar], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Divider(thickness=2, leading_indent=8),
                    content
                ]
            )
        ]
        

# TODO: 
# Add fonts and shadow options
# Build in dialoge bubbles shapes for dialogue (up-left, up-right, down-left, down-right, middle-up, middle-down). See canvas example on flet docs, they have one
# -- Both round and normal for above dialogue boxes
