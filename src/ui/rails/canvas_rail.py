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
from models.isolated_controls.column import IsolatedColumn
from utils.safe_string_checker import return_safe_name
from styles.text_field import TextField


# Class for our Canvas Board rail
class CanvasRail(Rail):

    def __init__(self, page: ft.Page, story: Story):

        # Initialize the parent Rail class first
        super().__init__(
            page=page,
            story=story,
            directory_path=story.data.get('content_directory_path', ''),
        )

        # UI elements ---------------------------------------------
        # Buttons at the top of the rail
        self.top_row_buttons = [
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
                #[     
                    #ft.MenuItemButton(
                        #leading=ft.Icon(ft.Icons.BRUSH_OUTLINED, ft.Colors.PRIMARY), content="Canvas",
                        #data="canvas", on_click=self.new_item_clicked, close_on_click=True,
                        #tooltip="Create a new Canvas for sketching drawing, or visual note taking",
                        #style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True
                    #),
                    #ft.MenuItemButton(
                        #leading=ft.Icon(ft.Icons.SPACE_DASHBOARD_OUTLINED, ft.Colors.PRIMARY), content="Canvas Board",
                        #data="canvas_board", on_click=self.new_item_clicked, close_on_click=True,
                        #tooltip="Create a new Canvas Board to organize your canvases and plan your story visually",
                        #style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    #),
                #],
                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10)),
                style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
                disabled=True
            ),
        ]

        # Color picker for changing brush color
        color_only = app.settings.data.get('paint_settings', {}).get('color', "#000000").split(",", 1)[0]     # Set color without opacity for the color picker
        self.color_picker = ColorPicker(
            color=color_only, on_color_change=self._set_color, 
            scale=.8, 
            picker_area_border_radius=ft.BorderRadius.all(6)
        )   # Set our color pickers color 

        self.color_selector = ft.SubmenuButton(
            ft.Icon(ft.Icons.COLOR_LENS_ROUNDED, app.settings.data.get('paint_settings', {}).get('color', ft.Colors.PRIMARY)), 
            width=40,
            tooltip="The color of your brush strokes.",
            on_close=self._save_color, expand=True,
            controls=[ft.Column([
                self.color_picker,  
                ft.MenuItemButton(
                    "Set Color", on_click=lambda: None,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click")
                )
            ])],
            style=ft.ButtonStyle(
                mouse_cursor=ft.MouseCursor.CLICK,  
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                shape=ft.RoundedRectangleBorder(radius=4),
                padding=ft.Padding.all(0),
            ),
            menu_style=ft.MenuStyle(
                alignment=ft.Alignment.TOP_RIGHT,
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, 
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding.all(0)
            ),
        )

        self.brush_label = ft.Text(
            app.settings.data.get('canvas_settings').get('current_brush_name').capitalize(), overflow=ft.TextOverflow.ELLIPSIS,
            theme_style=ft.TextThemeStyle.LABEL_LARGE, tooltip="Current brush style", expand=True
        )
        

        self.brush_selector = ft.SubmenuButton(
            self._build_preview_brush(app.settings.data.get('paint_settings', {})),
            self._get_brush_options(),
            #leading=self.brush_label,
            trailing=ft.Icon(ft.Icons.ARROW_DROP_DOWN, ft.Colors.ON_SURFACE_VARIANT, scale=0.8),
            style=ft.ButtonStyle(
                mouse_cursor=ft.MouseCursor.CLICK,  
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if app.settings.data.get('canvas_settings', {}).get('current_control_mode', '') == "draw" else None,
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

        self.tool_selector = ft.SubmenuButton(
            self._set_preview_tool_icon(),
            self._get_tool_options(),
            
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
           
        self.reload_rail()
    
    # Set the color pickers color
    async def _set_color(self, e):
        self.color_picker.color = e.data
    
    # Called when color picker is closed
    async def _save_color(self, e=None):
        app.settings.data['paint_settings']['color'] = self.color_picker.color
        await app.settings.save_dict()
        self.story.active_rail.reload_rail()

    def _set_preview_tool_icon(self) -> ft.Control:

        in_tool_mode = app.settings.data.get('canvas_settings', {}).get('current_control_mode', "") == "tool"
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
            
    async def _set_active_tool(self, e):
        tool_name = e.control.data
        app.settings.data['canvas_settings']['current_control_mode'] = "tool"
        app.settings.data['canvas_settings']['current_tool_name'] = tool_name
        await app.settings.save_dict()
        self.story.active_rail.reload_rail()
        for widget in self.story.widgets:
            if widget.data.get('tag') == "canvas":
                if widget.data.get('visible', True):
                    await widget.set_mouse_cursor()


    def _get_tool_options(self) -> list[ft.Control]:
        ''' Gets our tool options for the popup menu. '''

        return [
            ft.Text("\tTools", color=ft.Colors.ON_SURFACE_VARIANT, italic=True),   # Placeholder for shapes section
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
            ft.Text("\tShapes", color=ft.Colors.ON_SURFACE_VARIANT, italic=True),   # Placeholder for shapes section
            
            ft.MenuItemButton(
                ft.Row([
                    ft.Text("Dialogue Box", overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                    ft.Icon(ft.CupertinoIcons.BUBBLE_LEFT_FILL, ft.Colors.PRIMARY)
                    # ft.CupertinoIcons.CHAT_BUBBLE
                ]),
                data="dialogue_box",
                on_click=self._set_active_tool,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor=ft.MouseCursor.CLICK),
                tooltip="Add dialogue boxes to your canvas"
            ),

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

        
    # Called when selecting one of our brushes
    def _set_active_brush(self, brush_settings: dict, name: str):
        ''' Sets the current brush settings to the passed in brush settings dictionary '''

        app.settings.data['canvas_settings']['current_control_mode'] = "draw"
        app.settings.data['paint_settings'].update(brush_settings)
        app.settings.data['canvas_settings']['current_brush_name'] = name
        self.p.run_task(app.settings.save_dict)

        self.story.active_rail.reload_rail()
        for widget in self.story.widgets:
            if widget.data.get('tag') == "canvas":
                if widget.data.get('visible', True):
                    self.p.run_task(widget.set_mouse_cursor)

    # Set the blend mode label based on current mode in settings
    def _set_blend_mode_label(self) -> str:
        ''' Returns the label for the current blend mode. '''

        mode = app.settings.data.get('paint_settings', {}).get('blend_mode', 'src_over')
        if mode is None:
            return "None"
        match mode:
            case "src_over": return "None"
            case "color": return "Color"
            case "color_burn": return "Color Burn"
            case "color_dodge": return "Color Dodge"
            case "darken": return "Darken"
            case "difference": return "Difference"
            case "dst": return "Destination"
            case "dst_a_top": return "Destination Atop Source"
            case "dst_in": return "Destination In"
            case "dst_out": return "Destination Out"
            case "dst_over": return "Destination Over"
            case "exclusion": return "Exclusion"
            case "hard_light": return "Hard Light"
            case "hue": return "Hue"
            case "lighten": return "Lighten"
            case "luminosity": return "Luminosity"
            case "modulate": return "Modulate"
            case "multiply": return "Multiply"
            case "overlay": return "Overlay"
            case "plus": return "Plus"
            case "saturation": return "Saturation"
            case "screen": return "Screen"
            case "soft_light": return "Soft Light"
            case "src": return "Source"
            case "src_a_top": return "Source Atop Destination"
            case "src_in": return "Source In"
            case "src_out": return "Source Out"
            case "xor": return "XOR"
            case _: return mode.replace("_", " ").title()
        

    # Called to build a small preview canvas of our brush strokes for visual distinction
    def _build_preview_brush(self, paint_settings: dict) -> cv.Canvas:
        ''' Builds a small canvas, and uses the passed in paint settings to draw a sample stroke to show the user what their current brush settings look like. '''

        color = app.settings.data.get('paint_settings', {}).get('color', "#000000")
        
        # Default brush settings to creating non-custom brushes
        default_brush_settings = {
            'color': color,   
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
            
        
        # Set our canvas and grab our style. BUILD like width and height are 100, 30. This size is just for padding
        preview_canvas = cv.Canvas(width=105, height=35)

        # Max size just to display on this canvas
        max_size = 6

        ps = paint_settings.copy()
        ps['blend_mode'] = None

        # Set max values of paint so that it fits normally on our small preview
        if ps.get('stroke_width', 3) > max_size:
            ps['stroke_width'] = max_size
        if ps.get('blur_image', 0) > max_size:
            ps['blur_image'] = max_size

        
        preview_canvas.shapes = [
            cv.Path([
                cv.Path.MoveTo(5, 25),
                cv.Path.CubicTo(5, 25, 10, 16, 50, 15),
                cv.Path.CubicTo(50, 15, 90, 14, 100, 5)
            ], ps)
        ]

        return ft.Container(preview_canvas, opacity=.99)
    

    def _get_brush_options(self) -> list[ft.Control]:
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
            ft.Text("\tDefault Brushes", color=ft.Colors.ON_SURFACE_VARIANT, italic=True),   # Placeholder for shapes section
            ft.MenuItemButton(
                data=default_brush_settings,
                content=ft.Container(
                    ft.Row([ft.Text("Default", expand=True, overflow=ft.TextOverflow.ELLIPSIS), self._build_preview_brush(default_brush_settings)], spacing=20),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE
                ),
                on_click=lambda _: self._set_active_brush(default_brush_settings, name="Default"),
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor=ft.MouseCursor.CLICK),
            ),    
            ft.MenuItemButton(
                data=default_brush_settings,
                content=ft.Container(
                    ft.Row([ft.Text("Shadow", expand=True, overflow=ft.TextOverflow.ELLIPSIS), self._build_preview_brush(shadow_brush_settings)], spacing=20),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE
                ),
                on_click=lambda _: self._set_active_brush(shadow_brush_settings, name="Shadow"),
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor=ft.MouseCursor.CLICK),
            ),        
                   

            ft.Divider(),   # Placeholder for shapes section
            ft.Text("\tSaved Brushes", color=ft.Colors.ON_SURFACE_VARIANT, italic=True),   # Placeholder for shapes section
        ]

        # Go through our saved brushes and add options to select them
        for name, brush_settings in app.settings.data.get('canvas_settings', {}).get('saved_brushes', {}).items():
            options.append(
                ft.MenuItemButton(
                    data=brush_settings,
                    content=ft.Container(
                        ft.Row([ft.Text(name.capitalize(), expand=True, overflow=ft.TextOverflow.ELLIPSIS), self._build_preview_brush(brush_settings)], spacing=20),
                        clip_behavior=ft.ClipBehavior.HARD_EDGE
                    ),
                    on_click=lambda _, bs=brush_settings, n=name: self._set_active_brush(bs, n),
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor=ft.MouseCursor.CLICK),
                )
            )

        return options



    # Called on startup and when we have changes to the rail that have to be reloaded 
    def reload_rail(self):
        ''' Reloads the canvas rail with updated data and UI elements. '''

        # Called when changing paint width
        def _paint_width_changed(e):
            new_width = int(e.control.value)
            # Change the data directly
            app.settings.data['paint_settings']['stroke_width'] = new_width
            self.p.run_task(app.settings.save_dict)
            self.story.active_rail.reload_rail()

        # Called when changing paint anti-aliasing
        def _paint_anti_alias_changed(e):
            new_anti_alias = e.control.value
            app.settings.data['paint_settings']['anti_alias'] = new_anti_alias
            self.p.run_task(app.settings.save_dict)
            self.story.active_rail.reload_rail()

        # Add fill or not to our style based on teh switch state
        async def _paint_fill_changed(e):
            is_fill = e.control.value
            if is_fill:
                app.settings.data['paint_settings']['style'] = app.settings.data['paint_settings']['style'] + "_fill"
            else:
                app.settings.data['paint_settings']['style'] = app.settings.data['paint_settings']['style'].replace("_fill", "")
            await app.settings.save_dict()
            self.story.active_rail.reload_rail()

        def _paint_stroke_cap_changed(e):
            new_stroke_cap = e.control.content.lower()
            app.settings.data['paint_settings']['stroke_cap'] = new_stroke_cap
            self.p.run_task(app.settings.save_dict)
            self.story.active_rail.reload_rail()

        def _paint_stroke_join_changed(e):
            new_stroke_join = e.control.content.lower()
            app.settings.data['paint_settings']['stroke_join'] = new_stroke_join
            self.p.run_task(app.settings.save_dict)
            self.story.active_rail.reload_rail() 

        # Called when changing paint stroke blur
        def _paint_stroke_blur_changed(e):
            app.settings.data['paint_settings']['blur_image'] = int(e.control.value)
            self.p.run_task(app.settings.save_dict)
            self.story.active_rail.reload_rail()
            

        def _paint_blend_mode_changed(e):
            mode = e.control.data

            # Set the new mode and label
            app.settings.data['paint_settings']['blend_mode'] = mode

            self.p.run_task(app.settings.save_dict)
            self.story.active_rail.reload_rail()


        # Called to save our active brush settings as a custom brush we can load later (Excludes color and opacity)
        def _save_custom_brush_clicked(e=None):
            ''' Shows our existing brush options and allows us to override or save as a new brush '''

            # Saves the current name and closes the dialog
            async def _save_and_close(e=None): 

                nonlocal name
                safe_name = return_safe_name(name)

                # Save current brush settings as a new custom brush
                brush_settings = app.settings.data['paint_settings'].copy()
                app.settings.data['canvas_settings']['saved_brushes'][safe_name] = brush_settings
                self.p.run_task(app.settings.save_dict)

                # Just rebuild the rail so we can select our newly saved brush
                self.story.active_rail.reload_rail()
                self.p.pop_dialog()

            # Deletes a color
            async def _delete_custom_brush(e):
                nonlocal content
                name = e.control.data

                # Remove it from data
                if name in app.settings.data.get('canvas_settings', {}).get('saved_brushes', {}):
                    del app.settings.data['canvas_settings']['saved_brushes'][name]
                    await app.settings.save_dict()

                # Remove the control from the dialog
                dlg.content.controls = [ctrl for ctrl in content.controls if ctrl.data != name]   
                content.update()

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
            def _check_name_change(e):
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
            new_custom_brush_name_text_field = TextField(
                label="Brush Name", autofocus=True, on_submit=_save_and_close, dense=True,
                capitalization=ft.TextCapitalization.SENTENCES, expand=True,
                on_change=_check_name_change,
            )

            name: str = None

            # Our save button that just changes text from save to overwrite
            save_button = ft.TextButton("Save", on_click=_save_and_close, style=ft.ButtonStyle(mouse_cursor="click")) 

            content = ft.Column(
                tight=True,
                scroll="auto",
                controls=[new_custom_brush_name_text_field], 
            ) 

            dlg = ft.AlertDialog(
                title=ft.Text("Name your custom brush"), 
                content=content,
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: self.p.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                    save_button
                ]
            )

            for name, existing_brush in app.settings.data.get('canvas_settings', {}).get('saved_brushes', {}).items():
                content.controls.append(
                    ft.Container(
                        ft.Row([
                            ft.Text(name, theme_style=ft.TextThemeStyle.LABEL_LARGE, expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                            self._build_preview_brush(existing_brush),
                            ft.IconButton(
                                ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, 
                                data=name, on_click=_delete_custom_brush, tooltip="Delete this saved brush",
                                mouse_cursor=ft.MouseCursor.CLICK
                            ),
                        ], spacing=20), border_radius=ft.BorderRadius.all(4), clip_behavior=ft.ClipBehavior.HARD_EDGE, padding=ft.Padding.only(left=6),
                        on_click=_select_active_brush_override, data=name,
                    )
                )

            self.p.show_dialog(dlg)


        menubar = ft.MenuBar(
            self.top_row_buttons,
            #expand=True,
            style=ft.MenuStyle(
                bgcolor="transparent", shadow_color="transparent",
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
        )

        header = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[menubar]
        )

        # Width/Size of brush
        self.paint_width_slider = ft.Slider(
            min=1, max=100, tooltip="The size of your brush strokes.", expand=True,
            divisions=99, value=app.settings.data.get('paint_settings', {}).get('stroke_width', 5),
            label="Brush Size: {value}px",
            on_change_end=_paint_width_changed
        )


        # If we use anti aliasing or not
        paint_anti_alias_toggle = ft.Switch(
            True, "\tAnti-Aliasing", on_change=_paint_anti_alias_changed,
            label_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=12),
            value=app.settings.data.get('paint_settings', {}).get('anti_alias', True),
            tooltip="Whether to use anti-aliasing for smoother brush strokes. Disabling may result in jagged edges",
            #label_position=ft.LabelPosition.LEFT
        )

        # Stroke cap shape
        if app.settings.data.get('paint_settings', {}).get('stroke_cap', 'butt') == 'round':
            paint_stroke_cap_icon = ft.Icons.CIRCLE_OUTLINED
        elif app.settings.data.get('paint_settings', {}).get('stroke_cap', 'butt') == 'square':
            paint_stroke_cap_icon = ft.Icons.SQUARE_OUTLINED
        else:
            paint_stroke_cap_icon = ft.Icons.CROP_SQUARE_OUTLINED
        paint_stroke_cap_selector = ft.SubmenuButton(
            ft.Row([
                
                ft.Text("Stroke Cap Shape", theme_style=ft.TextThemeStyle.LABEL_LARGE), 
                ft.Icon(paint_stroke_cap_icon),
                
            ], spacing=6),     # Stroke cap shape selector
            tooltip="The shape that your brush strokes will have at the end of each line segment.",
            menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10)),
            style=ft.ButtonStyle(
                padding=ft.Padding.only(left=4, right=4), alignment=ft.Alignment.CENTER, mouse_cursor="click", #bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                shape=ft.RoundedRectangleBorder(radius=4)
            ),
            controls=[
                ft.MenuItemButton("Butt", on_click=_paint_stroke_cap_changed, leading=ft.Icon(ft.Icons.CROP_SQUARE_OUTLINED), style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),),
                ft.MenuItemButton("Round", on_click=_paint_stroke_cap_changed, leading=ft.Icon(ft.Icons.CIRCLE_OUTLINED), style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),),
                ft.MenuItemButton("Square", on_click=_paint_stroke_cap_changed, leading=ft.Icon(ft.Icons.SQUARE_OUTLINED), style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),),
            ]
        )

        if app.settings.data.get('paint_settings', {}).get('stroke_join', 'miter') == 'round':
            stroke_join_icon = ft.Icons.CIRCLE_OUTLINED
        elif app.settings.data.get('paint_settings', {}).get('stroke_join', 'miter') == 'bevel':
            stroke_join_icon = ft.Icons.SQUARE_OUTLINED
        else:
            stroke_join_icon = ft.Icons.CROP_SQUARE_OUTLINED
        paint_stroke_join_selector = ft.SubmenuButton(
            ft.Row([
                
                ft.Text("Stroke Join Shape", theme_style=ft.TextThemeStyle.LABEL_LARGE), 
                ft.Icon(stroke_join_icon),
                
            ], spacing=6),   
            tooltip="The shape that your brush strokes will have at the join of two line segments.",
            menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10)),
            style=ft.ButtonStyle(
                padding=ft.Padding.only(left=4, right=4), alignment=ft.Alignment.CENTER, mouse_cursor="click",
                #bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, 
                shape=ft.RoundedRectangleBorder(radius=4)
            ),
            controls=[
                ft.MenuItemButton("Miter", leading=ft.Icon(ft.Icons.CROP_SQUARE_OUTLINED), on_click=_paint_stroke_join_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),),
                ft.MenuItemButton("Round", leading=ft.Icon(ft.Icons.CIRCLE_OUTLINED), on_click=_paint_stroke_join_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),),
                ft.MenuItemButton("Bevel", leading=ft.Icon(ft.Icons.SQUARE_OUTLINED), on_click=_paint_stroke_join_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),),
            ]
        )


        self.paint_stroke_blur_slider = ft.Slider(
            min=0, max=50,  tooltip="The blur effect of your brush strokes.", expand=True,
            divisions=50, value=app.settings.data.get('paint_settings', {}).get('blur_image', 0),
            label="Stroke Blur: {value}",  
            on_change_end=_paint_stroke_blur_changed  
        )

        

        
        paint_blend_mode_selector = ft.SubmenuButton(
            f"Blend Mode: {self._set_blend_mode_label()}", 
            tooltip="The Current blend effects applied to your brush strokes. \nSome blend modes don't render correctly until AFTER a stroke is completed.",
            menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10)),
            style=ft.ButtonStyle(
                padding=ft.Padding.only(left=4, right=4), alignment=ft.Alignment.CENTER,
                #bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, 
                shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click", 
            ),
            controls=[
                ft.MenuItemButton("None",  on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data=None, tooltip="No blend mode"),
                ft.MenuItemButton("Color", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="color", tooltip="Take the hue and saturation of the source image, and the luminosity of the destination image"),
                ft.MenuItemButton("Color Burn", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="color_burn", tooltip="Divide the inverse of the destination by the source, and inverse the result"),
                ft.MenuItemButton("Color Dodge", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="color_dodge", tooltip="Divide the destination by the inverse of the source"),
                ft.MenuItemButton("Darken", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="darken", tooltip="Composite the source and destination image by choosing the lowest value from each color channel"),
                ft.MenuItemButton("Difference", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="difference", tooltip="Subtract the smaller value from the bigger value for each channel"),
                ft.MenuItemButton("Destination", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="dst", tooltip="Drop the source image, only paint the destination image"),
                ft.MenuItemButton("Destination Atop Source", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="dst_a_top", tooltip="Composite the destination image over the source image, but only where it overlaps the source"),
                ft.MenuItemButton("Destination In", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="dst_in", tooltip="Show the destination image, but only where the two images overlap. The source image is not rendered, it is treated merely as a mask. The color channels of the source are ignored, only the opacity has an effect"),
                ft.MenuItemButton("Destination Out", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="dst_out", tooltip="Show the destination image, but only where the two images do not overlap. The source image is not rendered, it is treated merely as a mask. The color channels of the source are ignored, only the opacity has an effect"),
                ft.MenuItemButton("Destination Over", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="dst_over", tooltip="Composite the source image under the destination image"),
                ft.MenuItemButton("Exclusion", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="exclusion", tooltip="Subtract double the product of the two images from the sum of the two images."),
                ft.MenuItemButton("Hard Light", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="hard_light", tooltip="Multiply the components of the source and destination images after adjusting them to favor the source"),
                ft.MenuItemButton("Hue", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="hue", tooltip="Take the hue of the source image, and the saturation and luminosity of the destination image"),
                ft.MenuItemButton("Lighten", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="lighten", tooltip="Composite the source and destination image by choosing the highest value from each color channel"),
                ft.MenuItemButton("Luminosity", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="luminosity", tooltip="Take the luminosity of the source image, and the hue and saturation of the destination image"),
                ft.MenuItemButton("Modulate", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="modulate", tooltip="Multiply the color components of the source and destination images"),
                ft.MenuItemButton("Multiply", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="multiply", tooltip="Multiply the components of the source and destination images, including the alpha channel"),
                ft.MenuItemButton("Overlay", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="overlay", tooltip="Multiply the components of the source and destination images after adjusting them to favor the destination"),
                ft.MenuItemButton("Plus", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="plus", tooltip="Sum the components of the source and destination images"),
                ft.MenuItemButton("Saturation", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="saturation", tooltip="Take the saturation of the source image, and the hue and luminosity of the destination image"),
                ft.MenuItemButton("Screen", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="screen", tooltip="Multiply the inverse of the components of the source and destination images, and inverse the result"),
                ft.MenuItemButton("Soft Light", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="soft_light", tooltip="Somewhere between Overlay and Color blend modes"),
                ft.MenuItemButton("Source", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="src", tooltip="Drop the destination image, only paint the source image"),
                ft.MenuItemButton("Soure Atop Destination", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="src_a_top", tooltip="Composite the source image over the destination image, but only where it overlaps the destination"),
                ft.MenuItemButton("Source In", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="src_in", tooltip="Show the source image, but only where the two images overlap. The destination image is not rendered, it is treated merely as a mask. The color channels of the destination are ignored, only the opacity has an effect"),
                ft.MenuItemButton("Source Out", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="src_out", tooltip="Show the source image, but only where the two images do not overlap. The destination image is not rendered, it is treated merely as a mask. The color channels of the destination are ignored, only the opacity has an effect"),
                ft.MenuItemButton("XOR", on_click=_paint_blend_mode_changed, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), data="xor", tooltip="Apply a bitwise xor operator to the source and destination images. This leaves transparency where they would overlap"),
            ]
        )
        

        save_custom_brush_button = ft.IconButton(      
            ft.Icons.SAVE_ROUNDED, ft.Colors.PRIMARY,
            tooltip="Save current brush settings as a custom brush", 
            on_click=_save_custom_brush_clicked, mouse_cursor=ft.MouseCursor.CLICK,
            style=ft.ButtonStyle(
                mouse_cursor=ft.MouseCursor.CLICK,  
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                shape=ft.RoundedRectangleBorder(radius=4),
                padding=ft.Padding.all(0),
            ),
        )  

        if app.settings.data.get('canvas_settings', {}).get('active_tool', 'brush') == "brush":
            pass
        else:
            pass

        # Switch between our drawing and tool mode
        async def _set_control_mode(e):
            selected_mode = e.control.data
            app.settings.data['canvas_settings']['current_control_mode'] = selected_mode
            if selected_mode == "draw":
                if app.settings.data.get('paint_settings', {}).get('blend_mode', "") == "clear":
                    app.settings.data['paint_settings']['blend_mode'] = "src_over"
            await app.settings.save_dict()
            self.story.active_rail.reload_rail()
            for widget in self.story.widgets:
                if widget.data.get('tag') == "canvas":
                    if widget.data.get('visible', True):
                        await widget.set_mouse_cursor()


        # Buttons that set either to draw or to use a tool
        set_draw_button = ft.IconButton(
            ft.Icons.BRUSH_ROUNDED if app.settings.data.get('canvas_settings', {}).get('current_control_mode', 'draw') == "draw" else ft.Icons.BRUSH_OUTLINED,
            ft.Colors.PRIMARY,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if app.settings.data.get('canvas_settings', {}).get('current_control_mode', 'draw') == "draw" else None,
            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, shape=ft.RoundedRectangleBorder(radius=4)),
            tooltip="Set the active control to the last used brush",
            data="draw", on_click=_set_control_mode
        )
        set_tool_button = ft.IconButton(
            ft.Icons.BUILD_ROUNDED if app.settings.data.get('canvas_settings', {}).get('current_control_mode', 'draw') == "tool" else ft.Icons.BUILD_OUTLINED,
            ft.Colors.PRIMARY,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if app.settings.data.get('canvas_settings', {}).get('current_control_mode', 'draw') == "tool" else None,
            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, shape=ft.RoundedRectangleBorder(radius=4)),
            tooltip="Set the active control to the last used tool",
            data="tool", on_click=_set_control_mode
        )

        # Set a tooltip for certain tools
        tool_note_visible = False
        match app.settings.data.get('canvas_settings', {}).get('current_tool_name', 'draw'):
            case "erase":
                tool_tooltip = "Eraser Tool: Erases overtop of existing content ONLY on the active layer, \n" \
                "Even though it appears to erase all layers beneath the active layer"
                if app.settings.data.get('canvas_settings', {}).get('current_control_mode', 'draw') == "tool":
                    tool_note_visible = True

            case "line":
                tool_tooltip = "Line Tool: Draws straight lines from starting point where mouse is pressed down until mouse is released"
                if app.settings.data.get('canvas_settings', {}).get('current_control_mode', 'draw') == "tool":
                    tool_note_visible = True

            case _:

                tool_tooltip = None
                tool_note_visible = False

        # Set a note for certain tools
        tool_note = ft.Icon(
            ft.Icons.INFO_OUTLINE, ft.Colors.PRIMARY,
            scale=0.8,
            visible=tool_note_visible,
            tooltip=tool_tooltip
        )

        fill_switch = ft.Switch(
            True, "\tFill Paint", on_change=_paint_fill_changed,
            label_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=12),
            value=app.settings.data.get('paint_settings', {}).get('style', 'stroke').endswith('_fill'),
            tooltip="Whether to fill strokes and shapes, or leave them hollow (Transparent)",
            #label_position=ft.LabelPosition.LEFT
        )

        # Toggles path smoothing
        async def _path_smoothing_changed(e):
            new_value = e.control.value
            app.settings.data['canvas_settings']['use_path_smoothing'] = e.control.value
            await app.settings.save_dict()

        use_path_smoothing_switch =  ft.Switch(
            True, "\tPath Smoothing", on_change=_path_smoothing_changed,
            label_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=12),
            value=app.settings.data.get('canvas_settings', {}).get('use_path_smoothing', True),
            tooltip="Whether to apply path smoothing to brush strokes. Makes the brushes paint color appear smoother, especially at lower opacity values.",
            #label_position=ft.LabelPosition.LEFT
        )

        # Updates any live text tools if we changed a setting that would affect it
        async def _update_live_text_shape():
            for widget in self.story.widgets:
                if widget.data.get('tag') == "canvas" and widget.data.get('visible', False):
                    if widget.manipulating_shape and widget.active_tool.shape_type == "text":
                        widget.active_tool.cv_shape.style = ft.TextStyle(
                            # TODO: Set properties here
                        )
                        widget.active_tool.cv_shape.update()

        async def _change_text_options(e):
            option = e.control.data
            value = e.control.value
            if option == "bold":
                app.settings.data['text_settings']['bold'] = value
            elif option == "italic":
                app.settings.data['text_settings']['italic'] = value
            elif option == "underline":
                app.settings.data['text_settings']['underline'] = value
            elif option == "strikethough":
                app.settings.data['text_settings']['strikethough'] = value
            await app.settings.save_dict()
            self.story.active_rail.reload_rail()
            await _update_live_text_shape()

        
        
        # Build the content of our rail
        content = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=4,
            expand=True,
            controls=[
                ft.Container(self.new_item_textfield, padding=ft.Padding.only(left=10, right=10)),

                # Save brush settings, label for rail, and reset brush settings to defaults buttons
                ft.Row([
                    ft.Text("Brush Settings", theme_style=ft.TextThemeStyle.TITLE_MEDIUM, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, expand=True),
                ]),
                #ft.Container(height=10),
            
   
                #ft.Text(
                    #"\tCurrent Color", color=ft.Colors.ON_SURFACE, 
                    #theme_style=ft.TextThemeStyle.LABEL_LARGE, 
                    #italic=True,
                    #tooltip="The color of your brush strokes"
                #),
                    
                #ft.Row([
                    
                #], spacing=4),
               # ft.Container(height=10),

                # Brush Selector and Save custom brush button
                #ft.Text(
                    #"\tCurrent Brush", color=ft.Colors.ON_SURFACE, 
                    #theme_style=ft.TextThemeStyle.LABEL_LARGE, 
                    #italic=True,
                    #tooltip="The current brush you have selected"
                #),
                ft.Container(
                    ft.MenuBar(
                        [self.color_selector],
                        style=ft.MenuStyle(bgcolor="transparent", shadow_color="transparent", padding=ft.Padding.all(0)),
                        #expand=True,
                    ),
                    margin=ft.Margin.only(left=4)
                ),

                ft.Row([
                    ft.Container(set_draw_button, margin=ft.Margin.only(left=4)), 
                    ft.Container(
                        ft.MenuBar(
                            [self.brush_selector], 
                            style=ft.MenuStyle(
                                bgcolor="transparent", shadow_color="transparent", padding=ft.Padding.all(0)
                            ),
                            #expand=True,
                        ),
                        margin=ft.Margin.only(left=4)
                    ),
                    
                    ft.Container(save_custom_brush_button, margin=ft.Margin.only(left=4))
                ], spacing=0, wrap=True),  
                #ft.Container(height=10),  

                #ft.Text(
                    #"\tCurrent Tool", color=ft.Colors.ON_SURFACE, 
                    #theme_style=ft.TextThemeStyle.LABEL_LARGE, 
                    #italic=True,
                    #tooltip="The current tool you have selected"
                #),

                ft.Row([
                    ft.Container(set_tool_button, margin=ft.Margin.only(left=4)),
                    ft.MenuBar(
                        [self.tool_selector], 
                        style=ft.MenuStyle(
                            bgcolor="transparent", shadow_color="transparent", padding=ft.Padding.all(0)
                        ),
                        #expand=True,
                    ),
                    tool_note
                ], spacing=4),
                    
   
                

                ft.Row([
                    ft.Text("\t\tWidth", theme_style=ft.TextThemeStyle.LABEL_LARGE,), 
                    self.paint_width_slider
                ], spacing=0, tooltip="Size of your strokes"),      # Size slider

                ft.Row([ft.Text("\t\tBlur", theme_style=ft.TextThemeStyle.LABEL_LARGE), self.paint_stroke_blur_slider], spacing=0),

                

                
                
                #ft.Container(height=10),   # Spacer
 
                # Effects section with anti-aliasing toggle, stroke blur slider, and blend mode selector
                #ft.Divider(),
                #ft.Row([ft.Text("Effects", theme_style=ft.TextThemeStyle.TITLE_MEDIUM, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER),
                #ft.Container(height=10),   # Spacer
                fill_switch,

                use_path_smoothing_switch,
                
                paint_anti_alias_toggle,
                

                ft.MenuBar(
                    [paint_stroke_cap_selector],
                    style=ft.MenuStyle(
                        bgcolor="transparent", shadow_color="transparent",
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                ),

                
                ft.MenuBar(
                    [paint_stroke_join_selector],
                    style=ft.MenuStyle(
                        bgcolor="transparent", shadow_color="transparent",
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                ),


                ft.MenuBar(
                    [paint_blend_mode_selector],
                    style=ft.MenuStyle(
                        bgcolor="transparent", shadow_color="transparent",
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                ),


                # Effects section with anti-aliasing toggle, stroke blur slider, and blend mode selector
                ft.Divider(),
                ft.Row([ft.Text("Tool Settings", theme_style=ft.TextThemeStyle.TITLE_MEDIUM, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER),
                #ft.Container(height=10),   # Spacer

                # If widget.manipulating_shape and visible, then modify its curreent shape
                ft.Text("Text size"),
                ft.Text("Text color"),
                ft.Text("Fonts"),
                ft.Text("Text Bold"),
                ft.Text("Text Italic"),
                ft.Text("Text Decoration"),
                ft.Text("Background Color"),
                ft.Text("Shadow Color"),
                ft.Text("Letter Spacing"),
                ft.Text("Word Spacing"),
                ft.Text("Rectangle border radius"),
                ft.Text("Option to use paint settings for shapes or not"),
                ft.Text("Adjust sampling option"),
            ]
        )
        
        

       
 
        self.controls = [
            IsolatedColumn(
                spacing=0,
                expand=True,
                controls=[
                    header,
                    ft.Divider(),
                    content
                ]
            )
        ]
        

        # Apply the update
        try:
            self.update()
        except Exception:
            pass


# TODO: 
# Add txt input for brush size as well
# Use path smoothing for brush strokes, will use cv.Path if true else cv.line. Won't effect shapes
# Add rest of dialogue boxes, and resizing of them
# Build in dialoge bubbles shapes for dialogue (up-left, up-right, down-left, down-right, middle-up, middle-down). See canvas example on flet docs, they have one
# -- Both round and normal for above dialogue boxes
# Option to paint shapes as just blank standard paint, not use current paint settings