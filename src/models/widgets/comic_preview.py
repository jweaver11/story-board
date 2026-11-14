''' Class for the Notes widget. Displays as its own tab for easy access to pinning '''

import flet as ft
from models.views.story import Story
from models.widget import Widget
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
import flet_shadcn_ui as shad
from styles.highlight_button import HighlightButton
    

class ComicPreview(Widget):

    # Constructor
    def __init__(self, title: str, directory_path: str, story: Story, data: dict={}, is_new: bool = False):

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
                'color': app.settings.data.get('widget_defaults', {}).get('comic_preview', {}).get('color', "primary"),
                'show_sidebar': True,   # Start showing sidebar

                'preview_direction': app.settings.data.get('widget_defaults', {}).get('comic_preview', {}).get('preview_direction', "vertical"),            # Default direction for comic preview, can be vertical or horizontal
                'preview_background_color': app.settings.data.get('widget_defaults', {}).get('comic_preview', {}).get('preview_background_color', "#00000000"),  # Background color behind images
                'preview_spacing': app.settings.data.get('widget_defaults', {}).get('comic_preview', {}).get('preview_spacing', 0),                       # Spacing between images
                'preview_scale': app.settings.data.get('widget_defaults', {}).get('comic_preview', {}).get('preview_scale', 2),                         # Scale of the images in the preview, 1 = 1:1, 2 = 2:1, etc. 
                'filter_quality': app.settings.data.get('widget_defaults', {}).get('comic_preview', {}).get('filter_quality', "medium"),                 # Filter quality for the images in the preview, can be low, medium, or high
                'use_anti_aliasing': app.settings.data.get('widget_defaults', {}).get('comic_preview', {}).get('anti_aliasing', True),                  # Whether to use anti-aliasing when rendering the images in the preview

                # List to hold our featured_panels of the canvases. Also allows png uploads
                'featured_panels': [              
                    #{
                        #'id': "canvas_id or None" is None if its an uploaded image
                        #'image': "base64 string of the image"
                    #}
                ],                      
            },
        )

    # Called after any changes happen to the data that need to be reflected in the UI, usually just ones that require a rebuild
    def build(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        super().build()
        
        # Adds canvases to the preview
        async def handle_add_canvas_panel(e):

            async def save_selections(_):

                self.story.block_page()
            
                # Go through each included canvas and add it to the featured panels
                for control in canvas_options:
                    id = control.data
                    checkbox = control.controls[0]  # Check if the checkbox is ticked
                    if not checkbox.value:
                        continue
                
                    widget = self.story.get_widget_by_id(id)

                    if not widget:
                        self.page.pop_dialog()
                        self.page.show_dialog(SnackBar("Widget not found"))
                        self.story.unblock_page()
                        return

                    encoded_string = widget.get_snapshot_string()

                    self.data['featured_panels'].append({
                        'id': id,
                        #'title': file_path.split("\\")[-1],
                        'image': encoded_string
                    })
                    preview_panel_controls.append(build_preview_panel(len(self.data['featured_panels']) - 1, encoded_string))
                    panel_minimap.controls.append(build_minimap_panel(len(self.data['featured_panels']) - 1, encoded_string))

                self.update_data(**{'featured_panels': self.data.get('featured_panels', [])})
                self.update()

                self.story.unblock_page()
                self.page.pop_dialog()
                
                

            canvas_options = [
                ft.Row([
                    shad.Checkbox(label=widget.data.get('title')),
                    ft.Image(src=widget.get_snapshot_bytes("low"), width=192, height=108)
                ], data=widget_id)
                for widget_id, widget in self.story.widgets.items() if widget.data.get('tag') == 'canvas'
            ]

            dlg = shad.Dialog(
                title="Select Included Canvases",
                content=ft.Column(
                    canvas_options,
                    tight=True,
                    scroll=ft.ScrollMode.AUTO
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda: self.page.pop_dialog(), style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.ERROR)),
                    ft.TextButton("Add Canvases", on_click=save_selections, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.PRIMARY)),
                ]
            )
            self.story.page.show_dialog(dlg)

        
            
        # Handles uploading new panel(s) from external files
        async def handle_upload_panel(e: ft.Event):
            files = await ft.FilePicker().pick_files(allow_multiple=True, allowed_extensions=["jpg", "jpeg", "png", "webp"])
            self.story.block_page()
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
                                #'title': file_path.split("\\")[-1],
                                'image': encoded_string
                            })
                            
                            preview_panel_controls.append(build_preview_panel(len(self.data['featured_panels']) - 1, encoded_string))
                            panel_minimap.controls.append(build_minimap_panel(len(self.data['featured_panels']) - 1, encoded_string))
                            
                    except Exception as _:
                        pass
                self.update_data(**{'featured_panels': self.data.get('featured_panels', [])})
                self.update()
            self.story.unblock_page()
            

        # Returns the image control from the given string
        def build_preview_panel(idx: int, image_str: str) -> ft.Image:
            filter_quality = {
                "low": ft.FilterQuality.LOW,
                "medium": ft.FilterQuality.MEDIUM,
                "high": ft.FilterQuality.HIGH
            }.get(self.data.get('filter_quality', "medium"), ft.FilterQuality.MEDIUM)

            # Better performance
            try:
                image_bytes = base64.b64decode(image_str)
                img = Image.open(BytesIO(image_bytes))
                if img.mode in ("P", "PA"):  # palette images with transparency must go via RGBA
                    img = img.convert("RGBA")
                has_alpha = img.mode in ("RGBA", "LA")
                if not has_alpha:
                    img = img.convert("RGB")
                max_dim = 2160  # cap at 4K height; anything larger is not visible anyway
                if img.width > max_dim or img.height > max_dim:
                    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                output = BytesIO()
                if has_alpha:
                    img.save(output, format="PNG", optimize=True)
                else:
                    img.save(output, format="JPEG", quality=92, optimize=True)
                image_str = base64.b64encode(output.getvalue()).decode("utf-8")
            except Exception:
                pass  # fall back to original if conversion fails

            return ft.Image(image_str, fit=ft.BoxFit.CONTAIN, expand=True, data=idx, filter_quality=filter_quality)
        
        # Returns a small image in the mini map with a delete button that appears on hover
        def build_minimap_panel(idx: int, image_str: str) -> ft.GestureDetector:
            def create_thumbnail(image_str: str) -> str:
                try:
                    image_bytes = base64.b64decode(image_str)
                    img = Image.open(BytesIO(image_bytes)).convert("RGBA")
                    img.thumbnail((100 * 2, 100), Image.Resampling.BILINEAR)
                    output = BytesIO()
                    img.save(output, format="PNG", optimize=True)
                    return base64.b64encode(output.getvalue()).decode("utf-8")
                except Exception:
                    return image_str
            async def show_delete_icon(e: ft.Event):
                delete_button.opacity = 1
                delete_button.update()
            async def hide_delete_icon(e: ft.Event):
                delete_button.opacity = 0
                delete_button.update()

            # Create a much more lightweight thumbnail for the smaller minimap panels
            thumb = create_thumbnail(image_str)
            
            return ft.ReorderableDragHandle(
                ft.GestureDetector(
                    ft.Stack([
                        ft.Row([]), # Fill up so we can drag from anywhere
                        ft.Image(
                            thumb, fit=ft.BoxFit.CONTAIN, margin=ft.Margin.symmetric(horizontal=10), expand=True, 
                            filter_quality=ft.FilterQuality.LOW, 
                            placeholder_src=thumb,
                            fade_in_animation=ft.Animation(50),
                            placeholder_fade_out_animation=ft.Animation(50)
                        ),
                        delete_button := ft.IconButton(
                            ft.Icons.DELETE_OUTLINED, ft.Colors.ERROR, bgcolor=ft.Colors.SURFACE, tooltip="Remove panel from preview?",
                            opacity=0, scale=1.2, data=idx, on_click=remove_panel, mouse_cursor="click",
                            animate_opacity=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
                        ),
                    ], alignment=ft.Alignment.CENTER, expand=True,),
                    on_enter=show_delete_icon,
                    on_exit=hide_delete_icon,
                    height=100, expand=True
                )
            )
        
        # Update index in minimap list
        async def update_minimap_indices():
            for i, ctrl in enumerate(panel_minimap.controls):
                ctrl.content.content.controls[2].data = i 
        
        # Removes panel from data, minimap and both previews. Updates minimap indices to match new order
        async def remove_panel(e: ft.Event):
            idx = e.control.data
            self.data['featured_panels'].pop(idx)
            self.update_data(**{'featured_panels': self.data.get('featured_panels', [])})
            preview_panel_controls.pop(idx)
            panel_minimap.controls.pop(idx)
            self.update()
            await update_minimap_indices()
        
        # Handles reordering of panels in the mini map and applying to the previews
        async def reorder_panels(e: ft.OnReorderEvent):
            if e.old_index == e.new_index:
                return
            self.data['featured_panels'].insert(e.new_index, self.data['featured_panels'].pop(e.old_index))
            self.update_data(**{'featured_panels': self.data.get('featured_panels', [])})

            preview_panel_controls.insert(e.new_index, preview_panel_controls.pop(e.old_index))
            panel_minimap.controls.insert(e.new_index, panel_minimap.controls.pop(e.old_index)) 
            self.update()
            await update_minimap_indices()

        

        def build_header_cm_button() -> shad.ContextMenu:
            # Called to refresh any connected canvases featured_panels that might be outdated
            async def handle_refresh_panels():
                close_popovers()
                # Go through panels. If they are connected to a canvas, refresh the image from the canvas
                for idx, panel in enumerate(self.data.get('featured_panels', [])):
                    if panel.get('id'):
                        widget = self.story.get_widget_by_id(panel['id'])
                        if not widget:
                            continue
                        image_str = widget.get_snapshot_string("max")
                        panel['image'] = image_str
                        preview_panel_controls[idx] = build_preview_panel(idx, panel.get('image'))
                        panel_minimap.controls[idx] = build_minimap_panel(idx, panel.get('image'))
    
                # Update data UI
                self.update_data(**{'featured_panels': self.data.get('featured_panels', [])})
                self.update()
            
            # Handles toggling the preview direction between vertical and horizontal
            async def toggle_preview_direction(e: ft.Event):
                close_popovers()
                # Show the appropriate wrapper and update the button icon
                if self.data.get('preview_direction', "vertical") == "vertical":
                    self.update_data(**{'preview_direction': "horizontal"})
                    vertical_preview_wrapper.visible = False
                    horizontal_preview_wrapper.visible = True
                    self.sidebar_header.controls[-1] = build_header_cm_button()
                    
                else:
                    self.update_data(**{'preview_direction': "vertical"})
                    horizontal_preview_wrapper.visible = False
                    vertical_preview_wrapper.visible = True
                    self.sidebar_header.controls[-1] = build_header_cm_button()
                self.update()
            # Adjusts the spacing between panels in the preview display
            async def adjust_spacing(e: ft.Event):
                close_popovers()
                new_spacing = int(e.control.data)
                self.update_data(**{'preview_spacing': new_spacing})
                self.sidebar_header.controls[-1] = build_header_cm_button()
                vertical_preview.spacing = new_spacing
                horizontal_preview.spacing = new_spacing
                self.update()
                
            # Adjusts the scaling of the preview display
            async def adjust_scaling(e: ft.Event):
                close_popovers()
                new_scaling = int(e.control.data)
                self.update_data(**{'preview_scale': new_scaling})
                self.sidebar_header.controls[-1] = build_header_cm_button()
                vertical_preview.parent.expand = new_scaling
                horizontal_preview.parent.expand = new_scaling
                self.update()
    
            # Sets the background color of the preview display
            async def set_preview_background_color(e: ft.Event):
                close_popovers()
                new_color = e.control.data
                self.update_data(**{'preview_background_color': new_color})
                self.sidebar_header.controls[-1] = build_header_cm_button()
                vertical_preview.parent.bgcolor = new_color
                horizontal_preview.parent.bgcolor = new_color
                self.update()
    
            # Sets the filter quality of the preview display
            async def set_filter_quality(e: ft.Event):
                close_popovers()
                new_quality = str(e.control.data)
                self.update_data(**{'filter_quality': new_quality})
                e.control.parent.content = f"Filter Quality: {new_quality.capitalize()}"
                fq = {
                    "low": ft.FilterQuality.LOW,
                    "medium": ft.FilterQuality.MEDIUM,
                    "high": ft.FilterQuality.HIGH
                }.get(new_quality, ft.FilterQuality.MEDIUM)
                for idx, panel in enumerate(self.data.get('featured_panels', [])):
                    preview_panel_controls[idx].filter_quality = fq
                    panel_minimap.controls[idx].content.content.controls[1].filter_quality = fq
                self.update()
    
            async def toggle_anti_aliasing(e: ft.Event):
                close_popovers()
                new_value = not self.data.get('use_anti_aliasing', True)
                self.update_data(**{'use_anti_aliasing': new_value})
                e.control.content = f"Anti-Aliasing: {str(new_value)}"
                for idx, panel in enumerate(self.data.get('featured_panels', [])):
                    preview_panel_controls[idx].anti_alias = new_value
                    panel_minimap.controls[idx].content.content.controls[1].anti_alias = new_value
                self.update()
            def toggle_bgcolor_popover(e):
                bgcolor_popover.open = not bgcolor_popover.open
                self.update()
            def toggle_preview_spacing_popover(e):
                preview_spacing_popover.open = not preview_spacing_popover.open
                self.update()
            def toggle_preview_scaling_popover(e):
                preview_scaling_popover.open = not preview_scaling_popover.open
                self.update()
            def toggle_image_filter_popover(e):
                image_filter_popover.open = not image_filter_popover.open
                self.update()
            def close_popovers():
                bgcolor_popover.open = False
                preview_spacing_popover.open = False
                preview_scaling_popover.open = False
                image_filter_popover.open = False
                self.update()
            return shad.ContextMenu(
                HighlightButton(ft.Icon(ft.Icons.SETTINGS_OUTLINED, ft.Colors.PRIMARY), is_round=True, use_padding=True),
                [
                    shad.MenuItem(
                        "Refresh Canvas Panels",
                        leading=ft.Icon(ft.Icons.REFRESH_OUTLINED, ft.Colors.PRIMARY, size=20),
                        tooltip="Refresh panels connected to Canvases that may be outdated",
                        on_click=handle_refresh_panels,
                    ),
                    toggle_preview_direction_button := shad.MenuItem(
                        "Swap Preview Direction",
                        leading=ft.Icon(
                            ft.Icons.SWAP_VERT if self.data.get('preview_direction', "vertical") == "vertical" else ft.Icons.SWAP_HORIZ, 
                            ft.Colors.PRIMARY, size=20
                        ),
                        tooltip="Swap the preview direction between vertical and horizontal.",
                        on_click=toggle_preview_direction,
                    ),
                    shad.MenuItem(
                        f"Anti-Aliasing: {self.data.get('use_anti_aliasing', True)}",
                        leading=ft.Icon(ft.Icons.ANIMATION_OUTLINED, ft.Colors.PRIMARY, size=20),
                        tooltip="If anti aliasing should be used when rendering images in the preview. Will affect performance and image quality.",
                        on_click=toggle_anti_aliasing,
                    ),
                    shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
                    bgcolor_popover := shad.Popover(
                        shad.MenuItem(
                            leading=ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.data.get('preview_background_color', ft.Colors.PRIMARY), size=20),
                            content=ft.Row([ft.Text("Background Color"), ft.Icon(ft.Icons.ARROW_RIGHT, ft.Colors.OUTLINE, size=16)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            on_click=toggle_bgcolor_popover,
                            close_on_click=False,
                        ),
                        ft.Column([
                            shad.MenuItem(
                                content=ft.Icon(ft.Icons.CIRCLE, color=color, size=20),
                                on_click=set_preview_background_color, close_on_click=True, data=color,
                                expand=True
                            ) for color in colors
                        ] + [shad.MenuItem(
                            content=ft.Icon(ft.Icons.CIRCLE_OUTLINED, color="#00000000", size=20),
                            on_click=set_preview_background_color, close_on_click=True, data="#00000000",
                            expand=True
                        )], tight=True, spacing=0, width=100),
                        on_dismiss=close_popovers
                    ), 
                    shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
                    preview_spacing_popover := shad.Popover(
                        shad.MenuItem(
                            leading=ft.Icon(ft.Icons.SPACE_BAR_OUTLINED, ft.Colors.PRIMARY, size=20),
                            content=ft.Row([ft.Text(f"Preview Spacing: {self.data.get('preview_spacing', 0)}"), ft.Icon(ft.Icons.ARROW_RIGHT, ft.Colors.OUTLINE, size=16)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            on_click=toggle_preview_spacing_popover,
                            close_on_click=False,
                        ),
                        ft.Column([
                            shad.MenuItem(
                                content=ft.Text(str(i)),
                                on_click=adjust_spacing, close_on_click=True, data=i,
                                expand=True
                            ) for i in range(0, 21) if i % 2 == 0
                        ], tight=True, spacing=0, width=100),
                        on_dismiss=close_popovers
                    ),
                    shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
                    preview_scaling_popover := shad.Popover(
                        shad.MenuItem(
                            leading=ft.Icon(ft.Icons.CROP_FREE_OUTLINED, ft.Colors.PRIMARY, size=20),
                            content=ft.Row([ft.Text(f"Preview Scaling: {self.data.get('preview_scale', 0)}"), ft.Icon(ft.Icons.ARROW_RIGHT, ft.Colors.OUTLINE, size=16)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            on_click=toggle_preview_scaling_popover,
                            close_on_click=False,
                        ),
                        ft.Column([
                            shad.MenuItem(
                                content=ft.Text(str(i)),
                                on_click=adjust_scaling, close_on_click=True, data=i,
                                expand=True
                            ) for i in range(1, 6)
                        ], tight=True, spacing=0, width=100),
                        on_dismiss=close_popovers
                    ),
                    shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
                    image_filter_popover := shad.Popover(
                        shad.MenuItem(
                            leading=ft.Icon(ft.Icons.FILTER_OUTLINED, ft.Colors.PRIMARY, size=20),
                            content=ft.Row([ft.Text(f"Image Filter Quality: {self.data.get('filter_quality', 'Medium').capitalize()}"), ft.Icon(ft.Icons.ARROW_RIGHT, ft.Colors.OUTLINE, size=16)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            on_click=toggle_image_filter_popover,
                            close_on_click=False,
                        ),
                        ft.Column([
                            shad.MenuItem(
                                content=ft.Text(str(quality).capitalize()),
                                data=quality,
                                on_click=set_filter_quality, 
                            ) for quality in ("low", "medium", "high")
                        ], tight=True, spacing=0, width=100),
                        on_dismiss=close_popovers
                    ),
                ],
                open_on_tap=True
            )
        
        
        preview_panel_controls = [build_preview_panel(idx, panel.get('image')) for idx, panel in enumerate(self.data.get('featured_panels', []))]
            
        # Column that holds our images when in vertical preview mode
        vertical_preview = ft.ListView(
            preview_panel_controls,
            #preview_panel_controls.copy() if self.data.get('preview_direction', "vertical") == "vertical" else [],
            spacing=self.data.get('preview_spacing', 0),
            #horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            expand=True, scroll=ft.ScrollMode.AUTO
        )

        # Row that holds our images when in horizontal preview mode
        horizontal_preview = ft.ListView(
            preview_panel_controls,
            #preview_panel_controls.copy() if self.data.get('preview_direction', "vertical") == "horizontal" else [],
            spacing=self.data.get('preview_spacing', 0), horizontal=True,
            #vertical_alignment=ft.CrossAxisAlignment.CENTER, 
            expand=True, scroll=ft.ScrollMode.AUTO
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

        

        # Adds settings for this widget into the header on the sidebar
        self.sidebar_header.controls.append(
            build_header_cm_button()
        )
        
        # Set the sidebar content
        self.sidebar_body.controls.extend([
            ft.Row([
                ft.Text(f"Panels", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)),
                shad.ContextMenu(
                    HighlightButton(ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY), is_round=True, use_padding=True),
                    [
                        shad.MenuItem(
                            leading=ft.Icon(ft.Icons.BRUSH_OUTLINED, ft.Colors.PRIMARY), content="Add Canvases",
                            on_click=handle_add_canvas_panel,
                        ),
                        shad.MenuItem(
                            leading=ft.Icon(ft.Icons.UPLOAD_FILE_OUTLINED, ft.Colors.PRIMARY), content="Upload Image(s)",
                            on_click=handle_upload_panel,
                        ),
                    ],
                    open_on_tap=True
                ),
                
            ], spacing=0),
            panel_minimap,
        ])

        self.content = ft.Stack([
            ft.Row([
                preview_stack,
                self.toggle_sidebar_visibility_button, 
                self.sidebar,
            ], expand=True, spacing=0),
            
        ], expand=True, alignment=ft.Alignment.CENTER_RIGHT)
