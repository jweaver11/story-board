''' Class for the Notes widget. Displays as its own tab for easy access to pinning '''

import flet as ft
from models.views.story import Story
from models.widget import Widget
from utils.verify_data import verify_data
from styles.menu_option_style import MenuOptionStyle
from models.app import app
from utils.safe_string_checker import return_safe_name
from styles.text_fields import TextField
import base64
from PIL import Image
from io import BytesIO
from styles.snack_bar import SnackBar
import asyncio
from flet_color_pickers import BlockPicker
from styles.colors import colors
    

class ComicPreview(Widget):

    # Constructor
    def __init__(self, title: str, directory_path: str, story: Story, data: dict = None, is_new: bool = False):

        # Initialize from our parent class 'Widget'. 
        super().__init__(
            title = title,                      # Title of the note
            directory_path = directory_path,    # Path to our notes json file
            story = story,                      # Reference to our story object
            data = data,
            is_new = is_new
        )


        # If we're new, give default values for our data 
        if self.is_new == True:
            self.data.update({
                # Widget data
                'tag': "comic_preview",             # Tag to identify what type of object this is
                'color': app.settings.data.get('default_comic_preview_color', "primary"),

                'preview_direction': "vertical",      # Default direction for comic preview, can be vertical or horizontal
                'preview_background_color': "#00000000" if app.settings.data.get('theme_mode', '') == "dark" else "#ffffffff",  # Background color behind images
                'preview_spacing': 0,               # Spacing between images
                'preview_scale': 2,                 # Scale of the images in the preview, 1 = 1:1, 2 = 2:1, etc. 

                # List to hold our featured_panels of the canvases. Also allows png uploads
                'featured_panels': [              
                    #{
                        #'id': "canvas_id or None" is None if its an uploaded image
                        #'title': "title of the panel, either canvas name or file name",
                        #'image': "base64 string of the image"
                    #}
                ],                      
            },
        )

    
    
    
        


    # Called after any changes happen to the data that need to be reflected in the UI, usually just ones that require a rebuild
    def build(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # Called to find a canvas and load a rendered image string given all its layers
        def refresh_canvas_panel(canvas_id: str) -> str:

            # Gives a blank image to start
            def _blank_png() -> str:
                blank = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
                output = BytesIO()
                blank.save(output, format="PNG")
                return base64.b64encode(output.getvalue()).decode("utf-8")

            capture_list = []
            widget = self.story.get_widget_by_id(canvas_id)
            if not widget:
                return _blank_png()
            
            for layer in widget.data.get('canvas_data', {}).get('Layers', []):
                if layer.get('capture', ""):
                    capture_list.append(layer['capture'])
                   

            if not capture_list:
                return _blank_png()

            images = []
            for capture in capture_list:
                try:
                    image_bytes = base64.b64decode(capture)
                    image = Image.open(BytesIO(image_bytes)).convert("RGBA")
                    images.append(image)
                except Exception:
                    continue

            if not images:
                return _blank_png()

            width, height = images[0].size
            merged = Image.new("RGBA", (width, height), (0, 0, 0, 0))

            for image in images:
                if image.size != (width, height):
                    image = image.resize((width, height), Image.Resampling.LANCZOS)
                merged = Image.alpha_composite(merged, image)

            output = BytesIO()
            merged.save(output, format="PNG")
            return base64.b64encode(output.getvalue()).decode("utf-8")


        
        # Adds canvases to the preview
        async def handle_add_canvas_panel(e):

            async def save_canvas(_):
            
                await asyncio.sleep(0)
                id = e.control.data
                
                widget = self.story.get_widget_by_id(id)
                
                self.data['featured_panels'].append({
                    'id': id,
                    'title': widget.data.get('title', ''),
                    'image': self._set_canvas_panel(id)
                })
                self.update_data(**{'featured_panels': self.data.get('featured_panels', [])})

        # Called to refresh any connected canvases featured_panels that might be outdated
        async def handle_refresh_panels():
            
            # Go through panels. If they are connected to a canvas, refresh the image from the canvas
            for idx, panel in enumerate(self.data.get('featured_panels', [])):
                if panel.get('id'):
                    panel['image'] = refresh_canvas_panel(panel['id'])
                    vertical_preview.controls[idx] = build_preview_panel(idx, panel.get('image'))
                    horizontal_preview.controls[idx] = build_preview_panel(idx, panel.get('image'))
                    panel_minimap.controls[idx] = build_minimap_panel(idx, panel.get('image'))

            # Update data UI
            self.update_data(**{'featured_panels': self.data.get('featured_panels', [])})
            self.update()
        
        # Handles toggling the preview direction between vertical and horizontal
        async def toggle_preview_direction(e):
            # Show the appropriate wrapper and update the button icon
            if self.data.get('preview_direction', "vertical") == "vertical":
                self.update_data(**{'preview_direction': "horizontal"})
                vertical_preview_wrapper.visible = False
                horizontal_preview_wrapper.visible = True
                toggle_preview_direction_button.icon = ft.Icons.SWAP_HORIZ
                
            else:
                self.update_data(**{'preview_direction': "vertical"})
                horizontal_preview_wrapper.visible = False
                vertical_preview_wrapper.visible = True
                toggle_preview_direction_button.icon = ft.Icons.SWAP_VERT
            self.update()
            
        # Handles uploading new panel(s) from external files
        async def handle_upload_panel(e):
            files = await ft.FilePicker().pick_files(allow_multiple=True, allowed_extensions=["jpg", "jpeg", "png", "webp"])
            self.story.blocker.visible = True
            self.story.blocker.update()
            if files:
                for file in files:
                    file_path = file.path
                    try:
                        import base64

                        with open(file_path, "rb") as image_file:
                            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                            # Save to our data
                            self.data['featured_panels'].append({
                                'id': None,
                                'title': file_path.split("\\")[-1],
                                'image': encoded_string
                            })
                            vertical_preview.controls.append(build_preview_panel(len(self.data['featured_panels']) - 1, encoded_string))
                            horizontal_preview.controls.append(build_preview_panel(len(self.data['featured_panels']) - 1, encoded_string))
                            panel_minimap.controls.append(build_minimap_panel(len(self.data['featured_panels']) - 1, encoded_string))
                            
                    except Exception as _:
                        pass
                self.update_data(**{'featured_panels': self.data.get('featured_panels', [])})
                self.update()
            self.story.blocker.visible = False
            self.story.blocker.update()
                
        


        # TODO:
        # Upload canvases
        # Refresh canvas panels

        # Returns the image control from the given string
        def build_preview_panel(idx: int, image_str: str) -> ft.Image:
            return ft.Image(image_str, fit=ft.BoxFit.CONTAIN, expand=True, data=idx)
        
        # Returns a small image in the mini map with a delete button that appears on hover
        def build_minimap_panel(idx: int, image_str: str) -> ft.GestureDetector:
            async def show_delete_icon(e: ft.Event):
                delete_button.opacity = 1
                delete_button.update()
            async def hide_delete_icon(e: ft.Event):
                delete_button.opacity = 0
                delete_button.update()
            
            return ft.GestureDetector(
                ft.Stack([
                    ft.Image(
                        image_str, fit=ft.BoxFit.CONTAIN, margin=ft.Margin.symmetric(horizontal=10), expand=True, 
                        placeholder_src=image_str, placeholder_fit=ft.BoxFit.CONTAIN,
                        fade_in_animation=ft.Animation(100, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
                        placeholder_fade_out_animation=ft.Animation(100, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
                    ),
                    delete_button := ft.IconButton(
                        ft.Icons.DELETE_OUTLINED, ft.Colors.ERROR, bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, tooltip="Remove panel from preview?",
                        opacity=0, scale=1.2, data=idx, on_click=remove_panel, mouse_cursor="click",
                        animate_opacity=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
                    ),
                ], alignment=ft.Alignment.CENTER, expand=True,),
                on_enter=show_delete_icon,
                on_exit=hide_delete_icon,
                width=100, expand=True
            )
        
        # Update index in minimap list
        async def update_minimap_indices():
            for i, ctrl in enumerate(panel_minimap.controls):
                ctrl.content.controls[1].data = i 
        
        # Removes panel from data, minimap and both previews. Updates minimap indices to match new order
        async def remove_panel(e: ft.Event):
            idx = e.control.data
            self.data['featured_panels'].pop(idx)
            self.update_data(**{'featured_panels': self.data.get('featured_panels', [])})
            vertical_preview.controls.pop(idx)
            horizontal_preview.controls.pop(idx)
            panel_minimap.controls.pop(idx)
            self.update()
            await update_minimap_indices()
        

        


        # Handles reordering of panels in the mini map and applying to the previews
        async def reorder_panels(e: ft.OnReorderEvent):
            if e.old_index == e.new_index:
                return
            self.data['featured_panels'].insert(e.new_index, self.data['featured_panels'].pop(e.old_index))
            self.update_data(**{'featured_panels': self.data.get('featured_panels', [])})

            vertical_preview.controls.insert(e.new_index, vertical_preview.controls.pop(e.old_index))
            horizontal_preview.controls.insert(e.new_index, horizontal_preview.controls.pop(e.old_index))
            panel_minimap.controls.insert(e.new_index, panel_minimap.controls.pop(e.old_index)) 
            self.update()
            await update_minimap_indices()

        # Adjusts the spacing between panels in the preview display
        async def adjust_spacing(e: ft.Event):
            new_spacing = int(e.control.data)
            self.update_data(**{'preview_spacing': new_spacing})
            e.control.parent.content = f"Preview Spacing: {str(new_spacing)}"
            vertical_preview.spacing = new_spacing
            horizontal_preview.spacing = new_spacing
            self.update()
            
        # Adjusts the scaling of the preview display
        async def adjust_scaling(e: ft.Event):
            new_scaling = int(e.control.data)
            self.update_data(**{'preview_scale': new_scaling})
            e.control.parent.content = f"Preview Scaling: {str(new_scaling)}"
            vertical_preview.parent.expand = new_scaling
            horizontal_preview.parent.expand = new_scaling
            self.update()

        # Sets the background color of the preview display
        async def set_preview_background_color(e: ft.Event):
            new_color = e.control.data
            self.update_data(**{'preview_background_color': new_color})
            e.control.parent.leading.color = new_color
            vertical_preview.parent.bgcolor = new_color
            horizontal_preview.parent.bgcolor = new_color
            self.update()
        
            
        # Column that holds our images when in vertical preview mode
        vertical_preview = ft.Column(
            [build_preview_panel(idx, panel.get('image')) for idx, panel in enumerate(self.data.get('featured_panels', []))],
            spacing=self.data.get('preview_spacing', 0),
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True, scroll=ft.ScrollMode.AUTO
        )

        # Row that holds our images when in horizontal preview mode
        horizontal_preview = ft.Row(
            [build_preview_panel(idx, panel.get('image')) for idx, panel in enumerate(self.data.get('featured_panels', []))],
            spacing=self.data.get('preview_spacing', 0),
            vertical_alignment=ft.CrossAxisAlignment.CENTER, expand=True, scroll=ft.ScrollMode.AUTO
        )

        # Wrapper for vertical preview, allows us to hide/show based on the preview_direction setting
        vertical_preview_wrapper = ft.Row([
            ft.Container(expand=1),
            ft.Container(vertical_preview, bgcolor=self.data.get('preview_background_color', ft.Colors.BLACK), expand=self.data.get('preview_scale', 2)),
            ft.Container(expand=1),
        ], expand=True, visible=self.data.get('preview_direction', "vertical") == "vertical")

        # Wrapper for the horizontal preview, allows us to hide/show based on the preview_direction setting
        horizontal_preview_wrapper = ft.Column([
            ft.Container(expand=1),
            ft.Container(horizontal_preview, bgcolor=self.data.get('preview_background_color', ft.Colors.BLACK), expand=self.data.get('preview_scale', 2)),
            ft.Container(expand=1),
        ], expand=True, visible=self.data.get('preview_direction', "vertical") == "horizontal",)

        # Minimap of the panels, allows for reordering and removing panels from the preview. Held in the sidebar
        panel_minimap = ft.ReorderableListView(
            [build_minimap_panel(idx, panel.get('image')) for idx, panel in enumerate(self.data.get('featured_panels', []))],
            scroll=ft.ScrollMode.AUTO, on_reorder=reorder_panels, align=ft.Alignment.CENTER, expand=True
        )

        # Set the main preview content as a stack
        preview_stack = ft.Stack([
            vertical_preview_wrapper,
            horizontal_preview_wrapper
        ], expand=3, alignment=ft.Alignment.CENTER)
        
        # Set the sidebar content
        self.sidebar.content = ft.Column([
            ft.Row([
                ft.Text(
                    f"\t{self.data.get('title', 'untitled')}", theme_style=ft.TextThemeStyle.TITLE_LARGE, 
                    color=self.data.get('color', None), weight=ft.FontWeight.BOLD, 
                ),
                
                ft.MenuBar(
                    [
                        ft.SubmenuButton(
                            ft.Icon(ft.Icons.PLAYLIST_ADD_OUTLINED, "primary"),
                                
                            [
                                ft.MenuItemButton(      # Folders
                                    leading=ft.Icon(ft.Icons.BRUSH_OUTLINED, self.data.get('color', "primary")), content="Add Canvases", 
                                    on_click=handle_add_canvas_panel, close_on_click=True,
                                    tooltip="Add Canvases created in Story Board to the comic preview.",
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                                ), 
                                ft.MenuItemButton(      # Documents
                                    leading=ft.Icon(ft.Icons.UPLOAD_FILE_OUTLINED, self.data.get('color', "primary")), content="Upload Image(s)", 
                                    on_click=handle_upload_panel, close_on_click=True,
                                    tooltip="Upload images to the comic preview from your device to the comic preview.",
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                                ), 
                                toggle_preview_direction_button := ft.MenuItemButton(
                                    "Swap Preview Direction", True,
                                    leading=ft.Icon(
                                        ft.Icons.SWAP_VERT if self.data.get('preview_direction', "vertical") == "vertical" else ft.Icons.SWAP_HORIZ, 
                                        self.data.get('color', ft.Colors.PRIMARY),
                                    ),
                                    tooltip="Swap the preview direction between vertical and horizontal.",
                                    on_click=toggle_preview_direction,
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor=ft.MouseCursor.CLICK),
                                ),
                                ft.MenuItemButton(
                                    "Refresh Canvas Panels",
                                    leading=ft.Icon(ft.Icons.REFRESH_OUTLINED, self.data.get('color', ft.Colors.PRIMARY)),
                                    tooltip="Refresh panels connected to Canvases that may be outdated",
                                    on_click=handle_refresh_panels,
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor=ft.MouseCursor.CLICK),
                                ),

                                ft.SubmenuButton(
                                    f"Preview Spacing: {self.data.get('preview_spacing', 0)}",
                                    [
                                        ft.MenuItemButton(
                                            str(i), data=i,
                                            on_click=adjust_spacing,
                                        ) for i in range(0, 21) if i % 2 == 0
                                    ],
                                    tooltip="Adjust the spacing between panels in the preview display.",
                                    leading=ft.Icon(ft.Icons.SPACE_BAR_OUTLINED, self.data.get('color', ft.Colors.PRIMARY)),
                                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_LEFT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                                    style=ft.ButtonStyle(alignment=ft.Alignment.CENTER, mouse_cursor="click"),
                                ),
                                ft.SubmenuButton(
                                    f"Preview Scaling: {self.data.get('preview_scale', 0)}",
                                    [
                                        ft.MenuItemButton(
                                            str(i), data=i,
                                            on_click=adjust_scaling,
                                        ) for i in range(1, 6)
                                    ],
                                    tooltip="Adjust the scale of the preview display.",
                                    leading=ft.Icon(ft.Icons.CROP_FREE_OUTLINED, self.data.get('color', ft.Colors.PRIMARY)),
                                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_LEFT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                                    style=ft.ButtonStyle(alignment=ft.Alignment.CENTER, mouse_cursor="click"),
                                ),
                                ft.SubmenuButton(
                                    f"Change Background Color",
                                    [
                                        ft.MenuItemButton(
                                            ft.Icon(ft.Icons.CIRCLE, color), data=color,
                                            on_click=set_preview_background_color,
                                        ) for color in colors
                                    ] + [ft.MenuItemButton("Transparent", data="#00000000", on_click=set_preview_background_color,)],
                                    tooltip="Adjust the scale of the preview display.",
                                    leading=ft.Icon(ft.Icons.SCALE_OUTLINED, self.data.get('preview_background_color', "#00000000")),
                                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_LEFT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                                    style=ft.ButtonStyle(alignment=ft.Alignment.CENTER, mouse_cursor="click"),
                                ),
                                
                            ],
                            menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                            style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
                        ),
                    ],
                    style=ft.MenuStyle(
                        bgcolor="transparent", shadow_color="transparent",
                        shape=ft.RoundedRectangleBorder(radius=4),
                        padding=ft.Padding.all(0)
                    ),
                ),
                ft.Container(expand=True),
                ft.IconButton(
                    ft.Icons.CLOSE, ft.Colors.ON_SURFACE_VARIANT, on_click=self.hide_sidebar,
                    mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER,
                ),
            ], spacing=0,),
            ft.Divider(),
            panel_minimap,

            
        ], expand=True, scroll="none", spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        self.content = ft.Row([
            preview_stack,
            self.show_sidebar_button,
            self.sidebar,
        ], expand=True, spacing=0)
        