""" WIP """

import flet as ft
from models.views.story import Story
from ui.rails.rail import Rail
from styles.menu_option_style import MenuOptionStyle
import math
from flet_contrib.color_picker import ColorPicker
from models.app import app
from handlers.new_canvas_alert_dlg import new_canvas_alert_dlg


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
            ft.IconButton(
                tooltip="New Canvas",
                icon=ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                on_click=self.new_canvas_clicked
            ),
            ft.IconButton(
                icon=ft.Icons.FILE_UPLOAD_OUTLINED,
                tooltip="Upload Canvas",
                on_click=lambda e: print("Upload Canvas clicked")
            )
        ]

        # Color picker for changing brush color
        color_only = self.story.data.get('paint_settings', {}).get('color', "#000000").split(",", 1)[0]     # Set color without opacity for the color picker
        self.color_picker = ColorPicker(color=color_only)   # Set our color pickers color 

        self.color_picker_button = ft.PopupMenuButton(
            icon=ft.Icons.COLOR_LENS_OUTLINED, tooltip="The color of your brush strokes.",
            icon_color=self.story.data.get('paint_settings', {}).get('color', ft.Colors.PRIMARY),
            menu_padding=ft.padding.all(0), size_constraints=ft.BoxConstraints(min_width=310),
            on_cancel=self._set_color,
            items=[
                ft.PopupMenuItem(
                    disabled=True,
                    content=ft.Container(
                        padding=ft.Padding(left=10, right=10, top=10, bottom=20),
                        content=self.color_picker,     
                    ),
                    
                )
            ]
        )

        self.paint_blend_mode: ft.PopupMenuButton = None    # Will be initialized in reload_rail
        self.paint_blend_mode_label: ft.Text = ft.Text(f"Blend Mode: {self._set_blend_mode_label()}", theme_style=ft.TextThemeStyle.LABEL_LARGE, expand=True)

        self.paint_adjust_dashed_lines_button = ft.IconButton(
            icon=ft.Icons.TUNE_OUTLINED,
            tooltip="Adjust the dash pattern for dashed lines.",
            visible=self.story.data.get('paint_settings', {}).get('stroke_dash_pattern', None) is not None,
            #on_click= Open pattern adjustment dialog/button to adjust length and gap, and add more segments. Make reorderable and deletable
        )

        # Reload the rail on start
        self.reload_rail()

    # Called when new character button or menu option is clicked
    def new_canvas_clicked(self, e):
        ''' Handles setting our textfield for new character creation '''

        # Close the menu (if ones is open), which will update the page as well
        self.story.close_menu()   

        self.p.open(new_canvas_alert_dlg(self.p, self.story))
        self.p.update()

    # Called when color picker is closed
    def _set_color(self, e):

        selected_color = self.color_picker.color    # Our new selected color
           
        # Our story data needs the opacity, but color picker can't have it
        opacity = self.story.data.get('paint_settings', {}).get('color', "1.0").split(",", 1)[1].strip()
        
        
        color_with_opacity = f"{selected_color},{opacity}"
        
        self.story.data['paint_settings']['color'] = color_with_opacity
        
        self.story.save_dict()

        self.color_picker_button.icon_color = selected_color
        self.color_picker_button.icon_color = selected_color
        self.p.update()

   
    def _set_blend_mode_label(self) -> str:
        ''' Returns the label for the current blend mode. '''

        mode = self.story.data.get('paint_settings', {}).get('blend_mode', 'src_over')
        # 
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



    # Called on startup and when we have changes to the rail that have to be reloaded 
    def reload_rail(self):
        ''' Reloads the canvas rail with updated data and UI elements. '''

        # Called when changing paint width
        def _paint_width_changed(e):
            new_width = int(e.control.value)
            # Change the data directly
            self.story.data['paint_settings']['stroke_width'] = new_width
            self.story.save_dict()

        # Called when changing paint opacity
        def _paint_opacity_changed(e):
            new_opacity = float(e.control.value)/100

            # Get our current color without opacity
            current_color = self.story.data.get('paint_settings', {}).get('color', "#000000").split(",", 1)[0].strip()
            color_with_opacity = f"{current_color},{new_opacity}"

            # Change the data directly
            self.story.data['paint_settings']['color'] = color_with_opacity
            self.story.save_dict()

        # Called when changing paint style
        def _paint_style_changed(e):
            new_style = e.control.data     # New style
            
            if new_style == "stroke":       # Change the icon
                e.control.parent.icon = ft.Icons.BRUSH_OUTLINED
            elif new_style == "lineto":
                e.control.parent.icon = ft.Icons.HORIZONTAL_RULE
            elif new_style == "fill":
                e.control.parent.icon = ft.Icons.GESTURE_OUTLINED
            elif new_style == "arc":
                e.control.parent.icon = ft.Icons.AUTORENEW_OUTLINED
            elif new_style == "arcto":
                e.control.parent.icon = ft.Icons.AUTORENEW_OUTLINED
            
            self.story.data['paint_settings']['style'] = new_style      # Update the data
            self.story.save_dict()
            self.p.update()     # Update the page

        # Called when changing paint erase mode
        def _paint_erase_mode_changed(e):
            self.story.data['canvas_settings']['erase_mode'] = e.control.value    # Update if we're in erase mode or not
            self.story.save_dict()

        # Called when changing paint dash pattern usage
        def _paint_dash_pattern_changed(e):
            if e.control.value:   # If checked, set a default dash pattern
                self.story.data['paint_settings']['stroke_dash_pattern'] = self.story.data['canvas_settings']['stroke_dash_pattern']  
                self.paint_adjust_dashed_lines_button.visible = True
            else:
                self.story.data['paint_settings']['stroke_dash_pattern'] = None
                self.paint_adjust_dashed_lines_button.visible = False
            self.story.save_dict()
            self.p.update()
            

        # Called when changing paint anti-aliasing
        def _paint_anti_alias_changed(e):
            new_anti_alias = e.control.value
            self.story.data['paint_settings']['anti_alias'] = new_anti_alias
            self.story.save_dict()

        def _paint_stroke_cap_changed(e):
            new_stroke_cap = e.control.text.lower()
            if new_stroke_cap == "butt":
                e.control.parent.content = ft.Icon(ft.Icons.CROP_SQUARE_OUTLINED)
            elif new_stroke_cap == "round":
                e.control.parent.content = ft.Icon(ft.Icons.CIRCLE_OUTLINED)
            else:
                e.control.parent.content = ft.Icon(ft.Icons.SQUARE_OUTLINED)
            self.story.data['paint_settings']['stroke_cap'] = new_stroke_cap
            self.story.save_dict()
            self.p.update()

        def _paint_stroke_join_changed(e):
            new_stroke_join = e.control.text.lower()
            # Update icon based on stroke join type if desired
            if new_stroke_join == "miter":
                e.control.parent.content = ft.Icon(ft.Icons.CROP_SQUARE_OUTLINED)
            elif new_stroke_join == "round":
                e.control.parent.content = ft.Icon(ft.Icons.CIRCLE_OUTLINED)
            else:
                e.control.parent.content = ft.Icon(ft.Icons.SQUARE_OUTLINED)
            self.story.data['paint_settings']['stroke_join'] = new_stroke_join
            self.story.save_dict()
            self.p.update()

        # Called when changing paint stroke blur
        def _paint_stroke_blur_changed(e):
            self.story.data['paint_settings']['blur_image'] = int(e.control.value)
            self.story.save_dict()
            

        def _paint_blend_mode_changed(e):
            mode = e.control.data
            print(mode)

            # Set the icon
            if mode is None:
                self.paint_blend_mode.icon = ft.Icons.BLUR_OFF_OUTLINED
                print("Mode is none")
                
            else:
                self.paint_blend_mode.icon = ft.Icons.BLUR_ON_OUTLINED

            # Set the new mode and label
            self.story.data['paint_settings']['blend_mode'] = mode
            self.paint_blend_mode_label.value = f"Blend Mode: {self._set_blend_mode_label()}"

            self.story.save_dict()
            self.p.update()

        # Our header at the top of the rail
        header = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=self.top_row_buttons
        )

        # Opacity slider
        opacity_value = float(self.story.data.get('paint_settings', {}).get('color', "1.0").split(",", 1)[1].strip()) * 100
        paint_opacity = ft.Slider(
            min=0, max=100,  tooltip="The opacity of your brush strokes.",
            divisions=100, value=opacity_value, expand=True,
            label="Opacity: {value}%",
            on_change_end=_paint_opacity_changed
        )

        # Width/Size of brush
        paint_width = ft.Slider(
            min=1, max=50,  tooltip="The size of your brush strokes.", expand=True,
            divisions=49, value=self.story.data.get('paint_settings', {}).get('stroke_width', 5),
            label="Brush Size: {value}px",
            on_change_end=_paint_width_changed
        )

        paint_erase_mode = ft.Checkbox(
            on_change=_paint_erase_mode_changed, value=self.story.data.get('canvas_settings', {}).get('erase_mode', False)
        )

        # Paint style (Stroke, dash, fill, etc.)
        if self.story.data.get('paint_settings', {}).get('style', 'stroke') == 'stroke':
            paint_style_icon = ft.Icons.BRUSH_OUTLINED
        elif self.story.data.get('paint_settings', {}).get('style', 'stroke') == 'lineto':
            paint_style_icon = ft.Icons.HORIZONTAL_RULE
        elif self.story.data.get('paint_settings', {}).get('style', 'stroke') == 'fill':
            paint_style_icon = ft.Icons.GESTURE_OUTLINED
        elif self.story.data.get('paint_settings', {}).get('style', 'stroke') == 'arcto':
            paint_style_icon = ft.Icons.AUTORENEW_OUTLINED
        
        else:
            paint_style_icon = ft.Icons.BRUSH_OUTLINED

        # If stroke dash pattern is set, we're using dashed stroke
        if self.story.data.get('paint_settings', {}).get('stroke_dash_pattern', None):
            paint_style_icon = ft.Icons.LINE_STYLE_OUTLINED
        paint_style = ft.PopupMenuButton(
            icon=paint_style_icon,
            tooltip="The style of paint for your brush strokes.",
            menu_padding=ft.padding.all(0),
            items=[
                ft.PopupMenuItem(text="Stroke", data="stroke", icon=ft.Icons.BRUSH_OUTLINED, on_click=_paint_style_changed),
                ft.PopupMenuItem(text="Line", data="lineto", icon=ft.Icons.HORIZONTAL_RULE, on_click=_paint_style_changed),
                ft.PopupMenuItem(text="Lasso Fill", data="fill", icon=ft.Icons.GESTURE_OUTLINED, on_click=_paint_style_changed),
                ft.PopupMenuItem(text="Arc", data="arc", icon=ft.Icons.AUTORENEW_OUTLINED, on_click=_paint_style_changed),
                ft.PopupMenuItem(text="Half Circle", data="arcto", icon=ft.Icons.AUTORENEW_OUTLINED, on_click=_paint_style_changed),
            ]
        )

        # If we use anti aliasing or not
        paint_anti_alias = ft.Checkbox(
            label="Anti-Aliasing", on_change=_paint_anti_alias_changed,
            label_position=ft.LabelPosition.LEFT,
            value=self.story.data.get('paint_settings', {}).get('anti_alias', True)
        )

        # Stroke cap shape
        if self.story.data.get('paint_settings', {}).get('stroke_cap', 'butt') == 'round':
            paint_stroke_icon = ft.Icon(ft.Icons.CIRCLE_OUTLINED)
        elif self.story.data.get('paint_settings', {}).get('stroke_cap', 'butt') == 'square':
            paint_stroke_icon = ft.Icon(ft.Icons.SQUARE_OUTLINED)
        else:
            paint_stroke_icon = ft.Icon(ft.Icons.CROP_SQUARE_OUTLINED)
        paint_stroke_cap = ft.PopupMenuButton(
            content=paint_stroke_icon,
            tooltip="The shape that your brush strokes will have at the end of each line segment.",
            menu_padding=ft.padding.all(0),
            items=[
                ft.PopupMenuItem(text="Butt", on_click=_paint_stroke_cap_changed, icon=ft.Icons.CROP_SQUARE_OUTLINED, tooltip="Flat cut ends"),
                ft.PopupMenuItem(text="Round", on_click=_paint_stroke_cap_changed, icon=ft.Icons.CIRCLE_OUTLINED, tooltip="Rounded ends"),
                ft.PopupMenuItem(text="Square", on_click=_paint_stroke_cap_changed, icon=ft.Icons.SQUARE_OUTLINED, tooltip="Sharp cut ends"),
            ]
        )

        if self.story.data.get('paint_settings', {}).get('stroke_join', 'miter') == 'round':
            stroke_cap_icon = ft.Icon(ft.Icons.CIRCLE_OUTLINED)
        elif self.story.data.get('paint_settings', {}).get('stroke_join', 'miter') == 'bevel':
            stroke_cap_icon = ft.Icon(ft.Icons.SQUARE_OUTLINED)
        else:
            stroke_cap_icon = ft.Icon(ft.Icons.CROP_SQUARE_OUTLINED)
        paint_stroke_join = ft.PopupMenuButton(
            content=stroke_cap_icon, menu_padding=ft.padding.all(0),
            tooltip="The shape that your brush strokes will have at the join of two line segments.",
            items=[
                ft.PopupMenuItem(text="Miter", icon=ft.Icons.CROP_SQUARE_OUTLINED, on_click=_paint_stroke_join_changed, tooltip="Sharp corners"),
                ft.PopupMenuItem(text="Round", icon=ft.Icons.CIRCLE_OUTLINED, on_click=_paint_stroke_join_changed, tooltip="Rounded corners"),
                ft.PopupMenuItem(text="Bevel", icon=ft.Icons.SQUARE_OUTLINED, on_click=_paint_stroke_join_changed, tooltip="Flat cut corners"),
            ]
        )


        paint_stroke_blur = ft.Slider(
            min=0, max=50,  tooltip="The blur effect of your brush strokes.", expand=True,
            divisions=50, value=self.story.data.get('paint_settings', {}).get('blur_image', 0),
            label="Stroke Blur: {value}",  
            on_change_end=_paint_stroke_blur_changed  
        )

        if self.story.data.get('paint_settings', {}).get('blend_mode', None) is None:
            paint_blend_mode_icon = ft.Icons.BLUR_ON_OUTLINED
        else:
            paint_blend_mode_icon = ft.Icons.BLUR_OFF_OUTLINED

        self.paint_blend_mode = ft.PopupMenuButton(
            icon=paint_blend_mode_icon,
            tooltip="The blend mode of your brush strokes.", menu_padding=ft.padding.all(0),
            items=[
                ft.PopupMenuItem(text="None", icon=ft.Icons.BLUR_OFF_OUTLINED, on_click=_paint_blend_mode_changed, data=None, tooltip="No blend mode"),
                ft.PopupMenuItem(text="Color", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="color", tooltip="Take the hue and saturation of the source image, and the luminosity of the destination image"),
                ft.PopupMenuItem(text="Color Burn", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="color_burn", tooltip="Divide the inverse of the destination by the source, and inverse the result"),
                ft.PopupMenuItem(text="Color Dodge", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="color_dodge", tooltip="Divide the destination by the inverse of the source"),
                ft.PopupMenuItem(text="Darken", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="darken", tooltip="Composite the source and destination image by choosing the lowest value from each color channel"),
                ft.PopupMenuItem(text="Difference", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="difference", tooltip="Subtract the smaller value from the bigger value for each channel"),
                ft.PopupMenuItem(text="Destination", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="dst", tooltip="Drop the source image, only paint the destination image"),
                ft.PopupMenuItem(text="Destination Atop Source", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="dst_a_top", tooltip="Composite the destination image over the source image, but only where it overlaps the source"),
                ft.PopupMenuItem(text="Destination In", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="dst_in", tooltip="Show the destination image, but only where the two images overlap. The source image is not rendered, it is treated merely as a mask. The color channels of the source are ignored, only the opacity has an effect"),
                ft.PopupMenuItem(text="Destination Out", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="dst_out", tooltip="Show the destination image, but only where the two images do not overlap. The source image is not rendered, it is treated merely as a mask. The color channels of the source are ignored, only the opacity has an effect"),
                ft.PopupMenuItem(text="Destination Over", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="dst_over", tooltip="Composite the source image under the destination image"),
                ft.PopupMenuItem(text="Exclusion", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="exclusion", tooltip="Subtract double the product of the two images from the sum of the two images."),
                ft.PopupMenuItem(text="Hard Light", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="hard_light", tooltip="Multiply the components of the source and destination images after adjusting them to favor the source"),
                ft.PopupMenuItem(text="Hue", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="hue", tooltip="Take the hue of the source image, and the saturation and luminosity of the destination image"),
                ft.PopupMenuItem(text="Lighten", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="lighten", tooltip="Composite the source and destination image by choosing the highest value from each color channel"),
                ft.PopupMenuItem(text="Luminosity", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="luminosity", tooltip="Take the luminosity of the source image, and the hue and saturation of the destination image"),
                ft.PopupMenuItem(text="Modulate", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="modulate", tooltip="Multiply the color components of the source and destination images"),
                ft.PopupMenuItem(text="Multiply", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="multiply", tooltip="Multiply the components of the source and destination images, including the alpha channel"),
                ft.PopupMenuItem(text="Overlay", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="overlay", tooltip="Multiply the components of the source and destination images after adjusting them to favor the destination"),
                ft.PopupMenuItem(text="Plus", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="plus", tooltip="Sum the components of the source and destination images"),
                ft.PopupMenuItem(text="Saturation", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="saturation", tooltip="Take the saturation of the source image, and the hue and luminosity of the destination image"),
                ft.PopupMenuItem(text="Screen", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="screen", tooltip="Multiply the inverse of the components of the source and destination images, and inverse the result"),
                ft.PopupMenuItem(text="Soft Light", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="soft_light", tooltip="Somewhere between Overlay and Color blend modes"),
                ft.PopupMenuItem(text="Source", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="src", tooltip="Drop the destination image, only paint the source image"),
                ft.PopupMenuItem(text="Soure Atop Destination", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="src_a_top", tooltip="Composite the source image over the destination image, but only where it overlaps the destination"),
                ft.PopupMenuItem(text="Source In", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="src_in", tooltip="Show the source image, but only where the two images overlap. The destination image is not rendered, it is treated merely as a mask. The color channels of the destination are ignored, only the opacity has an effect"),
                ft.PopupMenuItem(text="Source Out", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="src_out", tooltip="Show the source image, but only where the two images do not overlap. The destination image is not rendered, it is treated merely as a mask. The color channels of the destination are ignored, only the opacity has an effect"),
                ft.PopupMenuItem(text="XOR", icon=ft.Icons.BLUR_ON_OUTLINED, on_click=_paint_blend_mode_changed, data="xor", tooltip="Apply a bitwise xor operator to the source and destination images. This leaves transparency where they would overlap"),
            ]
        )

        paint_use_dashed_lines = ft.Checkbox(
            label="Dashed Pattern", on_change=_paint_dash_pattern_changed,
            label_position=ft.LabelPosition.LEFT,
            value=self.story.data.get('paint_settings', {}).get('stroke_dash_pattern', None) is not None,
        )

        


        # Build the content of our rail
        content = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            controls=[
                ft.Row([ft.Text("Brush Settings: ", theme_style=ft.TextThemeStyle.TITLE_MEDIUM, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([self.color_picker_button, paint_style], alignment=ft.MainAxisAlignment.SPACE_EVENLY),

                # Add shapes and shapefill drawing modes. Path will use paint.style.paintingstyle fill or stroke.
                # Add shadow effect option for paths
                # Custom saved colors and custom brushes

                ft.Row([ft.Text("Size", theme_style=ft.TextThemeStyle.LABEL_LARGE), paint_width]),
                ft.Row([ft.Text("Opacity", theme_style=ft.TextThemeStyle.LABEL_LARGE), paint_opacity]),
                ft.Row([ft.Text("Erase Mode", theme_style=ft.TextThemeStyle.LABEL_LARGE), paint_erase_mode]),
                ft.Row([ft.Text("Stroke Cap Shape", theme_style=ft.TextThemeStyle.LABEL_LARGE), paint_stroke_cap]),
                ft.Container(height=10),   # Spacer
                ft.Row([ft.Text("Stroke Join Shape", theme_style=ft.TextThemeStyle.LABEL_LARGE), paint_stroke_join]),
                ft.Container(height=10),   # Spacer
                ft.Row([paint_use_dashed_lines, self.paint_adjust_dashed_lines_button], spacing=0),
                ft.Container(height=10),   # Spacer
                ft.Row([]),
                ft.Container(height=10),   # Spacer
               
                
                ft.Divider(),
                ft.Container(height=10),   # Spacer
                ft.Row([ft.Text("Effects: ", theme_style=ft.TextThemeStyle.TITLE_MEDIUM, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=10),   # Spacer
                ft.Row([paint_anti_alias]),
                ft.Container(height=10),   # Spacer
                ft.Row([ft.Text("Blur", theme_style=ft.TextThemeStyle.LABEL_LARGE), paint_stroke_blur]),
                ft.Container(height=10),   # Spacer
                ft.Row([self.paint_blend_mode_label, self.paint_blend_mode])

            ]
        )
        

        # Build the content of our rail
        self.content = ft.Column(
            spacing=0,
            expand=True,
            controls=[
                header,
                ft.Divider(),
                content,
                # Add more controls here as needed
            ]
        )

        # Apply the update
        self.p.update()