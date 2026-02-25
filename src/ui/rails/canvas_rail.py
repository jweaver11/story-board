""" 
Canvas Rail to display all drawing options and tools 
NOTE: Cannot use self.reload_rail() in this class, because ColorPicker is built in and loses its page reference

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
            ft.PopupMenuButton(
                icon=ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                tooltip="New", menu_padding=0,
                items=[
                    ft.PopupMenuItem(
                        "Canvas", icon=ft.Icons.BRUSH_OUTLINED,
                        on_click=self.new_canvas_clicked, data="canvas"
                    ),
                    ft.PopupMenuItem(
                        "Canvas Board", icon=ft.Icons.SPACE_DASHBOARD_OUTLINED,
                        on_click=self.new_item_clicked, data="canvas_board"
                    ),
                ]
            ),
            ft.PopupMenuButton(
                icon=ft.Icons.FILE_UPLOAD_OUTLINED,
                tooltip="Upload",
                menu_padding=0,
                items=[
                    ft.PopupMenuItem(
                        "Image", icon=ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED,
                    ),
                    ft.PopupMenuItem(
                        "Canvas", icon=ft.Icons.BRUSH_OUTLINED,
                    ),
                ]
            )
        ]

        # Color picker for changing brush color
        color_only = app.settings.data.get('paint_settings', {}).get('color', "#000000").split(",", 1)[0]     # Set color without opacity for the color picker
        self.color_picker = ColorPicker(color=color_only)   # Set our color pickers color 

        self.color_selector = ft.PopupMenuButton(
            icon=ft.Icons.COLOR_LENS_OUTLINED, tooltip="The color of your brush strokes.",
            icon_color=app.settings.data.get('paint_settings', {}).get('color', ft.Colors.PRIMARY),
            menu_padding=ft.Padding.all(0), size_constraints=ft.BoxConstraints(min_width=310),
            on_cancel=self._set_color,
            items=self._get_color_options()
        )

        self.brush_label = ft.Text(
            app.settings.data.get('canvas_settings').get('current_brush_name').capitalize(), overflow=ft.TextOverflow.ELLIPSIS,
            theme_style=ft.TextThemeStyle.LABEL_LARGE, tooltip="Current brush style", expand=True
        )
        self.brush_selector = ft.PopupMenuButton(
            tooltip="Change brush style",
            menu_padding=ft.Padding.all(0),
            items=self._get_brush_options()
        )
        self.brush_selector.content = ft.Container(
            ft.Row([self.brush_label, self._build_preview_canvas(app.settings.data.get('paint_settings', {}))], spacing=20),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

        self.paint_blend_mode_selector: ft.PopupMenuButton = None   
        self.paint_blend_mode_label = ft.Text(
            f"Blend Mode: {self._set_blend_mode_label()}", theme_style=ft.TextThemeStyle.LABEL_LARGE, expand=True,
            tooltip="Current blend effects applied to your brush strokes. Select to change."
        )

    # Get our color picker and saved custom color options
    def _get_color_options(self) -> list[ft.PopupMenuItem]:

        # Add our color picker and custom colors label
        colors = [
            ft.PopupMenuItem(
                disabled=True,
                content=ft.Container(
                    padding=ft.Padding(left=10, right=10, top=10, bottom=20),
                    content=self.color_picker,
                ), 
            ),
        ]


        return colors


    # Called when color picker is closed
    def _set_color(self, e):

        selected_color = self.color_picker.color    # Our new selected color
           
        # Our story data needs the opacity, but color picker can't have it
        opacity = app.settings.data.get('paint_settings', {}).get('color', "1.0").split(",", 1)[1].strip()
        color_with_opacity = f"{selected_color},{opacity}"
        app.settings.data['paint_settings']['color'] = color_with_opacity
        app.settings.save_dict()

        self.color_selector.icon_color = selected_color
        self.brush_selector.items = self._get_brush_options()   # Update our brush options to show the new color in the previews
        self.brush_selector.content = ft.Container(
            ft.Row([self.brush_label, self._build_preview_canvas(app.settings.data.get('paint_settings', {}))], spacing=20),
            clip_behavior=ft.ClipBehavior.HARD_EDGE, border_radius=ft.border_radius.all(4)
        )   # Update our brush selector preview to show the new color
        self.update()


        
    # Called when selecting one of our brushes
    def _set_brush(self, brush_settings: dict, name: str):
        ''' Sets the current brush settings to the passed in brush settings dictionary '''

        app.settings.data['paint_settings'].update(brush_settings)
        app.settings.data['canvas_settings']['current_brush_name'] = name
        app.settings.save_dict()

        self.brush_label.value = name.capitalize()
        self.brush_selector.content = ft.Container(
            ft.Row([self.brush_label, self._build_preview_canvas(brush_settings)], spacing=20),
            clip_behavior=ft.ClipBehavior.HARD_EDGE, border_radius=ft.border_radius.all(4), expand=True,
        )
        self.color_picker.color = brush_settings.get('color', "#000000").split(",", 1)[0].strip()   # Update color picker to match new brush color (without opacity)
        self.color_selector.icon_color = brush_settings.get('color', ft.Colors.PRIMARY).split(",", 1)[0].strip()   # Update selector icon color to match new brush color (without opacity)

        self.paint_opacity_slider.value = float(brush_settings.get('color', "1.0").split(",", 1)[1].strip()) * 100
        stroke_cap = brush_settings.get('stroke_cap', 'butt')
        if stroke_cap == "round":
            self.paint_stroke_cap_selector.icon = ft.Icons.CIRCLE_OUTLINED
        elif stroke_cap == "square":
            self.paint_stroke_cap_selector.icon = ft.Icons.SQUARE_OUTLINED
        else:
            self.paint_stroke_cap_selector.icon = ft.Icons.CROP_SQUARE_OUTLINED

        stroke_join = brush_settings.get('stroke_join', 'miter') 
        if stroke_join == "round":
            self.paint_stroke_join_selector.icon = ft.Icons.CIRCLE_OUTLINED
        elif stroke_join == "bevel":
            self.paint_stroke_join_selector.icon = ft.Icons.SQUARE_OUTLINED
        else:
            self.paint_stroke_join_selector.icon = ft.Icons.CROP_SQUARE_OUTLINED

        

        self.paint_anti_alias_toggle.value = brush_settings.get('anti_alias', True)
        self.paint_stroke_blur_slider.value = brush_settings.get('blur_image', 0)
        self.paint_blend_mode_selector.icon = ft.Icons.BLUR_OFF_OUTLINED if brush_settings.get('blend_mode', None) is None else ft.Icons.BLUR_ON_OUTLINED
        self.paint_blend_mode_label.value = f"Blend Mode: {self._set_blend_mode_label()}"
        self.update()

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

    # Reset our paint settings to their defaults. Unload any selected brushes.
    def _reset_to_defaults(self, e):
        ''' Resets all paint settings to their default values (except color and opacity) '''

        current_color = app.settings.data.get('paint_settings', {}).get('color', "#000000") 
        app.settings.data['paint_settings'] = {
            "color": current_color,         # Keep current color
            "stroke_width": 3,              # Default brush size
            "style": "stroke",              # Default paint style
            "anti_alias": True,             # Default anti-aliasing on
            "stroke_cap": "round",          # Default stroke cap
            "stroke_join": "round",         # Default stroke join
            "stroke_miter_limit": 10,       # Default miter limit
            "blur_image": 0,                # Default no blur
            "blend_mode": None,             # Default no blend mode
            "stroke_dash_pattern": None,    # Default no dash pattern
        }
        app.settings.save_dict()

        # Since we can't call reload_rail, manually update all controls :(
        self.paint_anti_alias_toggle.value = True
        self.paint_stroke_cap_selector.icon = ft.Icons.CIRCLE_OUTLINED
        self.paint_stroke_join_selector.icon = ft.Icons.CIRCLE_OUTLINED
        self.paint_stroke_blur_slider.value = 0
        self.paint_blend_mode_selector.icon = ft.Icons.BLUR_OFF_OUTLINED
        self.paint_blend_mode_label.value = f"Blend Mode: {self._set_blend_mode_label()}"

        self.update()   # Apply update

        


    # Called to build a small preview canvas of our brush strokes for visual distinction
    def _build_preview_canvas(self, paint_settings: dict) -> cv.Canvas:
        ''' Builds a small canvas, and uses the passed in paint settings to draw a sample stroke to show the user what their current brush settings look like. '''
        # Set our canvas and grab our style. BUILD like width and height are 100, 30. This size is just for padding
        preview_canvas = cv.Canvas(width=105, height=35)

        # Max size just to display on this canvas
        max_size = 6

        ps = paint_settings.copy()
        style = ps.get('style', 'stroke')
        if ps.get('stroke_width', 3) > max_size:
            ps['stroke_width'] = max_size

        match style:
            # These cases are for building custom shapes
            case "lineto":
                ps.update({'style': 'stroke'})  # Give it a usable style so it actually draws something
                preview_canvas.shapes = [
                    cv.Path([
                        cv.Path.MoveTo(0, 15),
                        cv.Path.LineTo(100, 15)
                    ], ps)
                ]

            case "arc":
                ps.update({'style': 'stroke'})
                preview_canvas.shapes = [
                    cv.Path([
                        cv.Path.Arc(0, 3, 30, 40, math.pi, math.pi)
                    ], ps)
                ]

            case "arcto":
                ps.update({'style': 'stroke'})
                preview_canvas.shapes = [
                    cv.Path([
                        cv.Path.MoveTo(0, 30),
                        cv.Path.ArcTo(30, 30, 15, 90)
                    ], ps)
                ]


            # All other saved brushes use stroke or fill, so this is the main fallback where we can just use the settings as they are
            case _:
                preview_canvas.shapes = [
                    cv.Path([
                        cv.Path.MoveTo(0, 25),
                        cv.Path.CubicTo(0, 25, 10, 16, 50, 15),
                        cv.Path.CubicTo(50, 15, 90, 14, 100, 5)
                    ], ps)
                ]

        return preview_canvas
    
    def _get_brush_options(self) -> list[ft.PopupMenuItem]:
        ''' Gets our brush options for the popup menu. '''

        color = app.settings.data.get('paint_settings', {}).get('color', "#000000")
        
        # Default brush settings to creating non-custom brushes
        default_brush_settings = {
            'color': color,   # Default to white in dark mode and black in light mode
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

        # Edited brush settings depending on the style
        fill_brush_settings = default_brush_settings.copy()
        fill_brush_settings['style'] = 'fill'

        line_brush_settings = default_brush_settings.copy() 
        line_brush_settings['style'] = 'lineto'

        arc_brush_settings = default_brush_settings.copy()
        arc_brush_settings['style'] = 'arc'
        #arc_fill_brush_settings = fill_brush_settings.copy()
        #arc_fill_brush_settings['style'] = 'arcfill'

        half_circle_brush_settings = default_brush_settings.copy()
        half_circle_brush_settings['style'] = 'arcto'
        #half_circle_fill_brush_settings = fill_brush_settings.copy()
        #half_circle_fill_brush_settings['style'] = 'arctofill'

        # Start by building our default brush options
        options = [
            ft.PopupMenuItem("Default Brushes", disabled=True, height=20),   # Placeholder for shapes section
            ft.PopupMenuItem(
                data=default_brush_settings,
                content=ft.Container(
                    ft.Row([ft.Text("Stroke", expand=True, overflow=ft.TextOverflow.ELLIPSIS), self._build_preview_canvas(default_brush_settings)], spacing=20),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE
                ),
                on_click=lambda e: self._set_brush(default_brush_settings, name="Stroke")
            ),
            ft.PopupMenuItem(
                data=fill_brush_settings,
                content=ft.Container(
                    ft.Row([ft.Text("Lasso Fill", expand=True, overflow=ft.TextOverflow.ELLIPSIS), self._build_preview_canvas(fill_brush_settings)], spacing=20),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE
                ),
                on_click=lambda e: self._set_brush(fill_brush_settings, name="Lasso Fill")
            ), 
            ft.PopupMenuItem(content=ft.Divider(), disabled=True, height=16),   # Placeholder for shapes section
            ft.PopupMenuItem("Tools & Shapes", disabled=True, height=20),   # Placeholder for shapes section
            ft.PopupMenuItem(
                data=fill_brush_settings,
                content=ft.Container(
                    ft.Row([ft.Text("Erase", expand=True, overflow=ft.TextOverflow.ELLIPSIS), self._build_preview_canvas(fill_brush_settings)], spacing=20),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE
                ),
                #on_click=lambda e: self._set_brush(fill_brush_settings, name="Lasso Fill")
            ),
            ft.PopupMenuItem(
                data=default_brush_settings,
                content=ft.Container(
                    ft.Row([ft.Text("Line", expand=True, overflow=ft.TextOverflow.ELLIPSIS), self._build_preview_canvas(line_brush_settings)], spacing=20),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE
                ),
                on_click=lambda e: self._set_brush(line_brush_settings, "Line")
            ),
            ft.PopupMenuItem(
                data=default_brush_settings,
                content=ft.Container(
                    ft.Row([ft.Text("Arc", expand=True, overflow=ft.TextOverflow.ELLIPSIS), self._build_preview_canvas(arc_brush_settings)], spacing=20),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE
                ),
                on_click=lambda e: self._set_brush(arc_brush_settings, "Arc")
            ),
            ft.PopupMenuItem(
                data=default_brush_settings,
                content=ft.Container(
                    ft.Row([ft.Text("Half Circle", expand=True, overflow=ft.TextOverflow.ELLIPSIS), self._build_preview_canvas(half_circle_brush_settings)], spacing=20),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE
                ),
                on_click=lambda e: self._set_brush(half_circle_brush_settings, "Half Circle")
            ),
            #TODO: Add more shapes here
            
            # TODO: Add more built in options here

            ft.PopupMenuItem(content=ft.Divider(), disabled=True, height=16),   # Placeholder for shapes section
            ft.PopupMenuItem("Saved Brushes", disabled=True, height=20),   # Placeholder for shapes section
        ]

        for name, brush_settings in app.settings.data.get('canvas_settings', {}).get('saved_brushes', {}).items():
            options.append(
                ft.PopupMenuItem(
                    text=name, data=brush_settings,
                    content=ft.Container(
                        ft.Row([ft.Text(name, expand=True, overflow=ft.TextOverflow.ELLIPSIS), self._build_preview_canvas(brush_settings)], spacing=20),
                        clip_behavior=ft.ClipBehavior.HARD_EDGE
                    ),
                    on_click=lambda e, bs=brush_settings, n=name: self._set_brush(bs, name=n)
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
            app.settings.save_dict()

        # Called when changing paint opacity
        def _paint_opacity_changed(e):
            new_opacity = float(e.control.value)/100

            # Get our current color without opacity
            current_color = app.settings.data.get('paint_settings', {}).get('color', "#000000").split(",", 1)[0].strip()
            color_with_opacity = f"{current_color},{new_opacity}"

            # Change the data directly
            app.settings.data['paint_settings']['color'] = color_with_opacity
            app.settings.save_dict()

        
            

        # Called when changing paint anti-aliasing
        def _paint_anti_alias_changed(e):
            new_anti_alias = e.control.value
            app.settings.data['paint_settings']['anti_alias'] = new_anti_alias
            app.settings.save_dict()

        def _paint_stroke_cap_changed(e):
            new_stroke_cap = e.control.text.lower()
            if new_stroke_cap == "butt":
                e.control.parent.icon = ft.Icons.CROP_SQUARE_OUTLINED
            elif new_stroke_cap == "round":
                e.control.parent.icon = ft.Icons.CIRCLE_OUTLINED
            else:
                e.control.parent.icon = ft.Icons.SQUARE_OUTLINED
            app.settings.data['paint_settings']['stroke_cap'] = new_stroke_cap
            app.settings.save_dict()
            self.update()

        def _paint_stroke_join_changed(e):
            new_stroke_join = e.control.text.lower()
            # Update icon based on stroke join type if desired
            if new_stroke_join == "miter":
                e.control.parent.icon = ft.Icons.CROP_SQUARE_OUTLINED
            elif new_stroke_join == "round":
                e.control.parent.icon = ft.Icons.CIRCLE_OUTLINED
            else:
                e.control.parent.icon = ft.Icons.SQUARE_OUTLINED
            app.settings.data['paint_settings']['stroke_join'] = new_stroke_join
            app.settings.save_dict()
            self.update()

        # Called when changing paint stroke blur
        def _paint_stroke_blur_changed(e):
            app.settings.data['paint_settings']['blur_image'] = int(e.control.value)
            app.settings.save_dict()
            

        def _paint_blend_mode_changed(e):
            mode = e.control.data

            # Set the icon
            if mode is None:
                self.paint_blend_mode_selector.icon = ft.Icons.BLUR_OFF_OUTLINED
                print("Mode is none")
                
            else:
                self.paint_blend_mode_selector.icon = ft.Icons.BLUR_ON_OUTLINED

            # Set the new mode and label
            app.settings.data['paint_settings']['blend_mode'] = mode
            self.paint_blend_mode_label.value = f"Blend Mode: {self._set_blend_mode_label()}"

            app.settings.save_dict()
            self.update()


        # Called to save our active brush settings as a custom brush we can load later (Excludes color and opacity)
        def _save_custom_brush(e=None):
            ''' Shows our existing brush options and allows us to override or save as a new brush '''

            # Saves the current name and closes the dialog
            def _save_and_close(e=None): 
                nonlocal name
                # Save current brush settings as a new custom brush
                brush_settings = app.settings.data['paint_settings'].copy()
                app.settings.data['canvas_settings']['saved_brushes'][name] = brush_settings
                app.settings.save_dict()

                # Update our selector to include the new option
                self.brush_selector.items = self._get_brush_options() 
                self.brush_selector.update()        # Requires direct update to work
                self.p.close(dlg)

            # Sets the name value when typing in the textfield. Checks if it exists and de-selects any existing ones
            def _set_name(e):
                nonlocal name
                name = e.control.value.strip()  

                for ctrl in dlg.content.controls:
                    if isinstance(ctrl, ft.GestureDetector):
                        ctrl.content.bgcolor = ft.Colors.TRANSPARENT

                for key in app.settings.data.get('canvas_settings', {}).get('saved_brushes', {}).keys():
                    if key == name:
                        e.control.error_text = "A brush with this name already exists. It will be overwritten if you save."
                        save_button.text = "Overwrite"
                        self.update()
                        #self.p.update()
                        return
                    
                save_button.text = "Save"
                e.control.error_text = None
                self.update()
                #self.p.update()

            # Deletes a color
            def _delete_brush(e):
                name = e.control.data

                if name in app.settings.data.get('canvas_settings', {}).get('saved_brushes', {}):
                    del app.settings.data['canvas_settings']['saved_brushes'][name]
                    app.settings.save_dict()

                dlg.content.controls = [ctrl for ctrl in dlg.content.controls if not (isinstance(ctrl, ft.GestureDetector) and ctrl.data == name)]
                self.update()
                #self.p.update()
                    
            # Sets an existing custom color to be overwritten by the current color
            def _set_brush_override(e):
                nonlocal name
                
                if e.control.content.bgcolor == ft.Colors.with_opacity(.1, ft.Colors.ON_SURFACE):
                    e.control.content.bgcolor = ft.Colors.TRANSPARENT
                    name = None
                    save_button.text = "Save"
                    self.update()
                    #self.p.update()
                    return

                name = e.control.data
                e.control.content.bgcolor = ft.Colors.with_opacity(.1, ft.Colors.ON_SURFACE)
                e.control.update()
                save_button.text = "Overwrite"

                for ctrl in dlg.content.controls:
                    if isinstance(ctrl, ft.GestureDetector) and ctrl != e.control:
                        ctrl.content.bgcolor = ft.Colors.TRANSPARENT
                
                self.update()
                #self.p.update()

            # Textfield for naming custom color
            text_field = ft.TextField(
                label="Brush Name", autofocus=True, on_submit=lambda e: _save_and_close(), dense=True,
                capitalization=ft.TextCapitalization.SENTENCES, on_change=_set_name, expand=True
            )

            name: str = None

            # Our save button that just changes text from save to overwrite
            save_button = ft.TextButton("Save", on_click=_save_and_close, scale=1.2)  

            dlg = ft.AlertDialog(
                title=ft.Text("Name your custom brush"), 
                content=ft.Column(
                    width=self.p.width * 0.25, expand=False,
                    height=self.p.height * 0.6,
                    controls=[
                        ft.Divider(),
                        ft.Row([
                            text_field,
                            ft.Icon(ft.Icons.INFO_OUTLINED, color=ft.Colors.PRIMARY, scale=.5, tooltip="Select a brush below to overwrite instead of saving as a new brush."),
                        ], spacing=0),
                    ], scroll="auto"
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: self.p.close(dlg), style=ft.ButtonStyle(color=ft.Colors.ERROR), scale=1.2),
                    ft.Container(width=12),   # Spacer
                    save_button
                ]
            )

            for name, existing_brush in app.settings.data.get('canvas_settings', {}).get('saved_brushes', {}).items():
                dlg.content.controls.append(
                    ft.GestureDetector(
                        ft.Container(
                            ft.Row([
                                ft.Text(name, theme_style=ft.TextThemeStyle.LABEL_LARGE, expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                                self._build_preview_canvas(existing_brush),
                                ft.IconButton(ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, data=name, on_click=_delete_brush, tooltip="Delete this saved brush"),
                            ], spacing=20), border_radius=ft.border_radius.all(4), clip_behavior=ft.ClipBehavior.HARD_EDGE, padding=ft.padding.only(left=6)
                        ),
                        on_tap=_set_brush_override, data=name, mouse_cursor=ft.MouseCursor.CLICK
                    )
                )

            self.p.open(dlg)


        # Our header at the top of the rail
        header = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=self.top_row_buttons,
        )

        # Opacity slider
        opacity_value = float(app.settings.data.get('paint_settings', {}).get('color', "1.0").split(",", 1)[1].strip()) * 100
        self.paint_opacity_slider = ft.Slider(
            min=0, max=100,  tooltip="The opacity of your brush strokes. (How see through they are)",
            divisions=100, value=opacity_value, expand=True,
            label="Opacity: {value}%",
            on_change_end=_paint_opacity_changed
        )

        # Width/Size of brush
        self.paint_width_slider = ft.Slider(
            min=1, max=50,  tooltip="The size of your brush strokes.", expand=True,
            divisions=49, value=app.settings.data.get('paint_settings', {}).get('stroke_width', 5),
            label="Brush Size: {value}px",
            on_change_end=_paint_width_changed
        )


        # If we use anti aliasing or not
        self.paint_anti_alias_toggle = ft.Checkbox(
            label="Anti-Aliasing  ", on_change=_paint_anti_alias_changed,
            label_position=ft.LabelPosition.LEFT,
            value=app.settings.data.get('paint_settings', {}).get('anti_alias', True),
            tooltip="Whether to use anti-aliasing for smoother brush strokes. Disabling may result in jagged edges"
        )

        # Stroke cap shape
        if app.settings.data.get('paint_settings', {}).get('stroke_cap', 'butt') == 'round':
            paint_stroke_icon = ft.Icons.CIRCLE_OUTLINED
        elif app.settings.data.get('paint_settings', {}).get('stroke_cap', 'butt') == 'square':
            paint_stroke_icon = ft.Icons.SQUARE_OUTLINED
        else:
            paint_stroke_icon = ft.Icons.CROP_SQUARE_OUTLINED
        self.paint_stroke_cap_selector = ft.PopupMenuButton(
            icon=paint_stroke_icon, menu_padding=ft.Padding.all(0),
            tooltip="The shape that your brush strokes will have at the end of each line segment.",
            items=[
                ft.PopupMenuItem("Butt", on_click=_paint_stroke_cap_changed, icon=ft.Icons.CROP_SQUARE_OUTLINED, tooltip="Flat cut ends"),
                ft.PopupMenuItem("Round", on_click=_paint_stroke_cap_changed, icon=ft.Icons.CIRCLE_OUTLINED, tooltip="Rounded ends"),
                ft.PopupMenuItem("Square", on_click=_paint_stroke_cap_changed, icon=ft.Icons.SQUARE_OUTLINED, tooltip="Sharp cut ends"),
            ]
        )

        if app.settings.data.get('paint_settings', {}).get('stroke_join', 'miter') == 'round':
            stroke_cap_icon = ft.Icons.CIRCLE_OUTLINED
        elif app.settings.data.get('paint_settings', {}).get('stroke_join', 'miter') == 'bevel':
            stroke_cap_icon = ft.Icons.SQUARE_OUTLINED
        else:
            stroke_cap_icon = ft.Icons.CROP_SQUARE_OUTLINED
        self.paint_stroke_join_selector = ft.PopupMenuButton(
            icon=stroke_cap_icon, menu_padding=ft.Padding.all(0),
            tooltip="The shape that your brush strokes will have at the join of two line segments.",
            items=[
                ft.PopupMenuItem("Miter", icon=ft.Icons.CROP_SQUARE_OUTLINED, on_click=_paint_stroke_join_changed, tooltip="Sharp corners"),
                ft.PopupMenuItem("Round", icon=ft.Icons.CIRCLE_OUTLINED, on_click=_paint_stroke_join_changed, tooltip="Rounded corners"),
                ft.PopupMenuItem("Bevel", icon=ft.Icons.SQUARE_OUTLINED, on_click=_paint_stroke_join_changed, tooltip="Flat cut corners"),
            ]
        )


        self.paint_stroke_blur_slider = ft.Slider(
            min=0, max=50,  tooltip="The blur effect of your brush strokes.", expand=True,
            divisions=50, value=app.settings.data.get('paint_settings', {}).get('blur_image', 0),
            label="Stroke Blur: {value}",  
            on_change_end=_paint_stroke_blur_changed  
        )

        if app.settings.data.get('paint_settings', {}).get('blend_mode', None) is None:
            paint_blend_mode_icon = ft.Icons.BLUR_ON_OUTLINED
        else:
            paint_blend_mode_icon = ft.Icons.BLUR_OFF_OUTLINED

        self.paint_blend_mode_selector = ft.PopupMenuButton(
            icon=paint_blend_mode_icon, menu_padding=ft.Padding.all(0),
            tooltip="Current blend effects applied to your brush strokes. Select to change.",
            items=[
                ft.PopupMenuItem("None", icon=ft.Icons.BLUR_OFF_OUTLINED, on_click=_paint_blend_mode_changed, data=None, tooltip="No blend mode"),
                ft.PopupMenuItem("Color", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="color", tooltip="Take the hue and saturation of the source image, and the luminosity of the destination image"),
                ft.PopupMenuItem("Color Burn", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="color_burn", tooltip="Divide the inverse of the destination by the source, and inverse the result"),
                ft.PopupMenuItem("Color Dodge", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="color_dodge", tooltip="Divide the destination by the inverse of the source"),
                ft.PopupMenuItem("Darken", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="darken", tooltip="Composite the source and destination image by choosing the lowest value from each color channel"),
                ft.PopupMenuItem("Difference", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="difference", tooltip="Subtract the smaller value from the bigger value for each channel"),
                ft.PopupMenuItem("Destination", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="dst", tooltip="Drop the source image, only paint the destination image"),
                ft.PopupMenuItem("Destination Atop Source", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="dst_a_top", tooltip="Composite the destination image over the source image, but only where it overlaps the source"),
                ft.PopupMenuItem("Destination In", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="dst_in", tooltip="Show the destination image, but only where the two images overlap. The source image is not rendered, it is treated merely as a mask. The color channels of the source are ignored, only the opacity has an effect"),
                ft.PopupMenuItem("Destination Out", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="dst_out", tooltip="Show the destination image, but only where the two images do not overlap. The source image is not rendered, it is treated merely as a mask. The color channels of the source are ignored, only the opacity has an effect"),
                ft.PopupMenuItem("Destination Over", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="dst_over", tooltip="Composite the source image under the destination image"),
                ft.PopupMenuItem("Exclusion", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="exclusion", tooltip="Subtract double the product of the two images from the sum of the two images."),
                ft.PopupMenuItem("Hard Light", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="hard_light", tooltip="Multiply the components of the source and destination images after adjusting them to favor the source"),
                ft.PopupMenuItem("Hue", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="hue", tooltip="Take the hue of the source image, and the saturation and luminosity of the destination image"),
                ft.PopupMenuItem("Lighten", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="lighten", tooltip="Composite the source and destination image by choosing the highest value from each color channel"),
                ft.PopupMenuItem("Luminosity", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="luminosity", tooltip="Take the luminosity of the source image, and the hue and saturation of the destination image"),
                ft.PopupMenuItem("Modulate", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="modulate", tooltip="Multiply the color components of the source and destination images"),
                ft.PopupMenuItem("Multiply", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="multiply", tooltip="Multiply the components of the source and destination images, including the alpha channel"),
                ft.PopupMenuItem("Overlay", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="overlay", tooltip="Multiply the components of the source and destination images after adjusting them to favor the destination"),
                ft.PopupMenuItem("Plus", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="plus", tooltip="Sum the components of the source and destination images"),
                ft.PopupMenuItem("Saturation", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="saturation", tooltip="Take the saturation of the source image, and the hue and luminosity of the destination image"),
                ft.PopupMenuItem("Screen", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="screen", tooltip="Multiply the inverse of the components of the source and destination images, and inverse the result"),
                ft.PopupMenuItem("Soft Light", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="soft_light", tooltip="Somewhere between Overlay and Color blend modes"),
                ft.PopupMenuItem("Source", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="src", tooltip="Drop the destination image, only paint the source image"),
                ft.PopupMenuItem("Soure Atop Destination", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="src_a_top", tooltip="Composite the source image over the destination image, but only where it overlaps the destination"),
                ft.PopupMenuItem("Source In", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="src_in", tooltip="Show the source image, but only where the two images overlap. The destination image is not rendered, it is treated merely as a mask. The color channels of the destination are ignored, only the opacity has an effect"),
                ft.PopupMenuItem("Source Out", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="src_out", tooltip="Show the source image, but only where the two images do not overlap. The destination image is not rendered, it is treated merely as a mask. The color channels of the destination are ignored, only the opacity has an effect"),
                ft.PopupMenuItem("XOR", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="xor", tooltip="Apply a bitwise xor operator to the source and destination images. This leaves transparency where they would overlap"),
            ]
        )
        
        # Build the content of our rail
        content = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            controls=[

                # Label for Paint settings and reset to default button
                ft.Row([
                    ft.IconButton(ft.Icons.SAVE_ROUNDED, tooltip="Save current brush settings as a custom brush", on_click=_save_custom_brush),     # Save custom brush button
                    ft.Text("Brush Settings", theme_style=ft.TextThemeStyle.TITLE_MEDIUM, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, expand=True),
                    ft.IconButton(
                        ft.Icons.RESTART_ALT_OUTLINED, on_click=self._reset_to_defaults,
                        tooltip="Resets current brush settings to defaults (Except color and opacity). Will NOT effect any saved brush",
                    )
                ],),

                # Brush Selector and Save custom brush button
                ft.Text("Current Brush", opacity=0.6, theme_style=ft.TextThemeStyle.LABEL_SMALL, tooltip="The current brush you have selected. Click to change or select a saved custom brush."),
                ft.Row([
                    self.brush_selector, 
                    ft.Text("Current Color", opacity=0.6, theme_style=ft.TextThemeStyle.LABEL_SMALL, tooltip="The color of your brush strokes"),
                    self.color_selector,
                ], wrap=True),

                # TODO: 
                # Add shapes and shapefill drawing modes. Path will use paint.style.paintingstyle fill or stroke.
                # Add shadow effect option for paths
                # Custom saved colors and custom brushes

                ft.Row([ft.Text("Size", theme_style=ft.TextThemeStyle.LABEL_LARGE, tooltip="Size of your strokes"), self.paint_width_slider]),      # Size slider
                ft.Row([ft.Text("Opacity", theme_style=ft.TextThemeStyle.LABEL_LARGE, tooltip="Opacity of your strokes (How see through they are)"), self.paint_opacity_slider]),     # Opacity slider

                ft.Row([ft.Text("Stroke Cap Shape", theme_style=ft.TextThemeStyle.LABEL_LARGE, tooltip="End shape of your strokes"), self.paint_stroke_cap_selector]),     # Stroke cap shape selector
                ft.Container(height=10),   # Spacer
                ft.Row([ft.Text("Stroke Join Shape", theme_style=ft.TextThemeStyle.LABEL_LARGE, tooltip="Shape taken at point of two strokes connecting"), self.paint_stroke_join_selector]),   # Stroke join shape selector
                ft.Container(height=10),   # Spacer
 
                # Effects section with anti-aliasing toggle, stroke blur slider, and blend mode selector
                ft.Divider(),
                ft.Row([ft.Text("Effects", theme_style=ft.TextThemeStyle.TITLE_MEDIUM, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=10),   # Spacer
                self.paint_anti_alias_toggle,
                ft.Container(height=10),   # Spacer
                ft.Row([ft.Text("Blur", theme_style=ft.TextThemeStyle.LABEL_LARGE), self.paint_stroke_blur_slider]),
                ft.Container(height=10),   # Spacer
                ft.Row([self.paint_blend_mode_label, self.paint_blend_mode_selector])

            ]
        )
        

        # Build the content of our rail
        self.content = IsolatedColumn(
            spacing=0,
            expand=True,
            controls=[
                header,
                ft.Divider(),
                content
            ]
        )

        # Apply the update
        try:
            self.update()
        except Exception as e:
            pass