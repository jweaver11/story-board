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
                'show_info': True,                    # Whether or not to show the info column on the left side of the page

                # List to hold our featured_images of the canvases. Also allows png uploads
                'featured_images': [              
                    #{
                        #'id': "canvas_id or None" is None if its an uploaded image
                        #'title': "title of the snapshot, either canvas name or file name",
                        #'image': "base64 string of the image"
                    #}
                ],                      
            },
        )
            
        



    # Called to find a canvas and load a snapshot from all its layers
    def _set_canvas_snapshot(self, canvas_id: str) -> str:

        def _blank_png() -> str:
            blank = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
            output = BytesIO()
            blank.save(output, format="PNG")
            return base64.b64encode(output.getvalue()).decode("utf-8")

        capture_list = []
        for widget in self.story.widgets.values():
            if widget.data['id'] == canvas_id:
                for layer in widget.data.get('canvas_data', {}).get('Layers', []):
                    if layer.get('capture', ""):
                        capture_list.append(layer['capture'])
                break

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
    
    # Called to refresh any connected canvases featured_images that might be outdated
    async def _refresh_canvas_snapshots(self):
        self.story.blocker.visible = True
        self.story.blocker.update()
        await asyncio.sleep(0)
        for snapshot in self.data.get('featured_images', []):
            if snapshot.get('id'):
                snapshot['image'] = self._set_canvas_snapshot(snapshot['id'])

        self.update_data(**{'featured_images': self.data.get('featured_images', [])})
        self.reload_widget()
        if self.story.blocker.visible:
            self.story.blocker.visible = False
            self.story.blocker.update()


    # Called after any changes happen to the data that need to be reflected in the UI, usually just ones that require a rebuild
    def build(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # Shows our info column
        async def show_mini_widgets_container(e: ft.Event):
            self.update_data(**{'show_info': True})

            show_info_button.opacity = 0
            show_info_button.disabled = True
            show_info_button.mouse_cursor = None
            show_info_button.update()

            await self.show_mini_widgets_container()

        # Hides our info column
        async def hide_mini_widgets_container(e: ft.Event):
            self.update_data(**{'show_info': False})
            
            await self.hide_mini_widgets_container()
            
            show_info_button.opacity = 1
            show_info_button.mouse_cursor = ft.MouseCursor.CLICK
            show_info_button.disabled = False
            show_info_button.update()

        async def _remove_snapshot(e):
            self.story.blocker.visible = True
            self.story.blocker.update()
            await asyncio.sleep(0)
            idx = e.control.data
            self.data['featured_images'].pop(idx)
            self.update_data(**{'featured_images': self.data.get('featured_images', [])})

            self.reload_widget()
            if self.story.blocker.visible:
                self.story.blocker.visible = False
                self.story.blocker.update()

        async def _add_canvas_snapshot(e):
            self.story.blocker.visible = True
            self.story.blocker.update()
            await asyncio.sleep(0)
            id = e.control.data
            title = None
            for widget in self.story.widgets.values():
                if widget.data.get('id') == id:
                    title = widget.title    
            self.data['featured_images'].append({
                'id': id,
                'title': title,
                'image': self._set_canvas_snapshot(id)
            })
            self.update_data(**{'featured_images': self.data.get('featured_images', [])})
            self.reload_widget()
            if self.story.blocker.visible:
                self.story.blocker.visible = False
                self.story.blocker.update()

        

        # Handles toggling the preview direction between vertical and horizontal
        async def _toggle_preview_direction(e):
            if self.data.get('preview_direction', "vertical") == "vertical":
                self.data['preview_direction'] = "horizontal"
            else:
                self.data['preview_direction'] = "vertical"
            self.update_data(**{'preview_direction': self.data.get('preview_direction', "vertical")})
            self.story.blocker.visible = True
            self.story.blocker.update()
            await asyncio.sleep(0)
            self.reload_widget()
            self.story.blocker.visible = False
            self.story.blocker.update()

        # Handles uploading new snapshot(s) from external files
        async def _upload_snapshot_clicked(e):
            files = await ft.FilePicker().pick_files(allow_multiple=True, allowed_extensions=["jpg", "jpeg", "png", "webp"])
            if files:
                for file in files:
                    file_path = file.path
                    try:
                        import base64

                        with open(file_path, "rb") as image_file:
                            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                            # Save to our data
                            self.data['featured_images'].append({
                                'id': None,
                                'title': file_path.split("\\")[-1],
                                'image': encoded_string
                            })
                            

                    except Exception as _:
                        pass
                self.update_data(**{'featured_images': self.data.get('featured_images', [])})
                self.story.blocker.visible = True
                self.story.blocker.update()
                await asyncio.sleep(0)
                self.reload_widget()
                self.story.blocker.visible = False
                self.story.blocker.update()

        # Handles reordering our featured_images on the left side of the page
        async def _reorder_snapshots(e: ft.OnReorderEvent):
            if e.old_index == e.new_index:
                return
            self.story.blocker.visible = True
            self.story.blocker.update()
            await asyncio.sleep(0)
            self.data['featured_images'].insert(e.new_index, self.data['featured_images'].pop(e.old_index))
            self.update_data(**{'featured_images': self.data.get('featured_images', [])})
            self.reload_widget()
            if self.story.blocker.visible:
                self.story.blocker.visible = False
                self.story.blocker.update()

        # Handles showing/hiding all the canvases that are featured or could be featured in the preview
        async def _toggle_featured_images(e):
            self.data['can_add_canvases'] = not self.data.get('can_add_canvases', True)
            self.update_data(**{'can_add_canvases': self.data.get('can_add_canvases', True)})
            if self.data.get('can_add_canvases', True):
                e.control.icon = ft.Icons.EDIT_OUTLINED
                selectable_snapshots.visible = True
            else:
                e.control.icon = ft.Icons.EDIT_OFF_OUTLINED
                selectable_snapshots.visible = False
            e.control.update()
            selectable_snapshots.update()

        # Rebuild out tab to reflect any changes
        self.create_tab()


        preview_display = ft.Column() if self.data.get('preview_direction', "vertical") == "vertical" else ft.Row()
        preview_display.spacing = 0
        preview_display.scroll = ft.ScrollMode.AUTO
        preview_display.expand = 2

        preview_display.controls = []

        for snapshot in self.data.get('featured_images', []):
            preview_display.controls.append(ft.Image(snapshot.get('image', ""), ft.Text("Error loading image"), fit=ft.BoxFit.CONTAIN, data=snapshot.get('id')))

        self.preview_display_container = ft.Container(
            preview_display,
            expand=2,
            bgcolor=self.data.get('preview_background_color', ft.Colors.BLACK),
        )

        preview_display_wrapper = ft.Container(
            ft.Row([
                ft.Container(expand=1), 
                self.preview_display_container, 
                ft.Container(expand=1)
            ], 
            expand=True, spacing=0, scroll="none", vertical_alignment=ft.CrossAxisAlignment.START
            ) if self.data.get('preview_direction', "vertical") == "vertical" else ft.Column([
                ft.Container(expand=1), 
                self.preview_display_container, 
                ft.Container(expand=1)
            ], expand=True, spacing=0, scroll="none", horizontal_alignment=ft.CrossAxisAlignment.START
            ),
            expand=3,
            alignment=ft.Alignment.CENTER,
        )

        preview_display_wrapper.content = ft.GestureDetector(
            preview_display_wrapper.content,
            on_secondary_tap=lambda _: self.story.open_menu(self._get_menu_options()),
            on_hover=self._get_coords,
            hover_interval=50
        )

    
        
        # Mini map with preview of all featured_images (very small) on the left side of the page
        snapshot_mini_map = ft.Column(
            [
                
                ft.Row([
                    ft.Text("Featured Canvases", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)), 
                    ft.IconButton(
                        ft.Icons.EDIT_OUTLINED if self.data.get('can_add_canvases', True) else ft.Icons.EDIT_OFF_OUTLINED, self.data.get('color', ft.Colors.PRIMARY),
                        tooltip="Add or remove canvases to be featured in the preview",
                        on_click=_toggle_featured_images,
                        mouse_cursor=ft.MouseCursor.CLICK,
                    )
                ], spacing=0)
                
                
            ],
            expand=1, scroll="auto", spacing=0
        )

        # Add featured canvases to the mini map that are reorderable
        featured_images = ft.ReorderableListView(scroll="auto", on_reorder=_reorder_snapshots)
        for idx, snapshot in enumerate(self.data.get('featured_images', [])):
            featured_images.controls.append(
                ft.ReorderableDragHandle(
                    ft.Row([
                        ft.Image(snapshot.get('image', ""), ft.Text("Error loading image"), fit=ft.BoxFit.CONTAIN, width=50, height=50),
                        ft.Text(snapshot.get('title', "Untitled"), weight=ft.FontWeight.BOLD, expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        
                        #ft.Container(width=1, height=50),
                        ft.IconButton(
                            ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR, on_click=_remove_snapshot, 
                            mouse_cursor=ft.MouseCursor.CLICK, data=idx,
                            tooltip="Remove from preview",
                        ),  # Only show delete button its an uploaded image
                        ft.Container(width=40)
                    ]),
                    data=snapshot.get('id')
                )
            )
        snapshot_mini_map.controls.append(featured_images)

        selectable_snapshots = ft.Column(
            [
                ft.Divider(),
                ft.Row([
                    ft.Text("Available Canvases", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),
                    ft.IconButton(
                        ft.Icons.FILE_UPLOAD_OUTLINED, self.data.get('color', ft.Colors.PRIMARY),
                        tooltip="Upload image(s) to be featured in the preview without connecting a canvas",
                        on_click=_upload_snapshot_clicked,
                        mouse_cursor=ft.MouseCursor.CLICK,
                    )
                ], spacing=0)
            ], 
            scroll="none", #expand=True,
            visible=True if self.data.get('can_add_canvases', True) else False
        )

        # For loop to add all canvases in story as options to be featured in the preview
        for widget in self.story.widgets.values():
            if widget.data.get('tag', "") == "canvas":
                selectable_snapshots.controls.append(
                    
                    ft.Row([
                        ft.IconButton(
                            ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, widget.data.get('color', ft.Colors.PRIMARY), on_click=_add_canvas_snapshot, 
                            mouse_cursor=ft.MouseCursor.CLICK, data=widget.data.get('id')
                        ),
                        ft.Image(self._set_canvas_snapshot(widget.data.get('id')), ft.Text("Error loading image"), fit=ft.BoxFit.CONTAIN, width=50, height=50),
                        ft.Text(f"\t\t{widget.title}", style=ft.TextStyle(weight=ft.FontWeight.BOLD), color=widget.data.get('color', None)),
                        
                    ], spacing=0, tight=True)
                )

       

        snapshot_mini_map.controls.append(selectable_snapshots)

        self.mini_widgets_container.content = ft.Container(
            ft.Column([
                ft.Row([
                    ft.Text(
                        f"{self.title}\t", theme_style=ft.TextThemeStyle.TITLE_LARGE, 
                        color=self.data.get('color', None), weight=ft.FontWeight.BOLD, 
                    ),
                    ft.IconButton(
                        ft.Icons.SWAP_VERT if self.data.get('preview_direction', "vertical") == "vertical" else ft.Icons.SWAP_HORIZ,
                        self.data.get('color', ft.Colors.PRIMARY),
                        tooltip="Toggle preview direction",
                        on_click=_toggle_preview_direction,
                        mouse_cursor=ft.MouseCursor.CLICK,
                    ),
                    ft.IconButton(
                        ft.Icons.REFRESH_OUTLINED,
                        self.data.get('color', ft.Colors.PRIMARY),
                        tooltip="Refresh snapshots of outdated canvases",
                        on_click=self._refresh_canvas_snapshots,
                        mouse_cursor=ft.MouseCursor.CLICK,
                    ),
                    
                    
                    
                    ft.Container(expand=True),
                    ft.IconButton(
                        ft.Icons.CLOSE, ft.Colors.ON_SURFACE_VARIANT, on_click=hide_mini_widgets_container,
                        mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER,
                    ),
                ], spacing=0),
                ft.Divider(2, 2),
                #ft.Container(height=10),
                snapshot_mini_map,
            ], expand=True, scroll="none"),
            border=ft.Border.only(left=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            padding=ft.Padding.only(left=11, top=8, bottom=8),
            shadow=ft.BoxShadow(0, 1),
            expand=1,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
        )


        # TODO:

        # Returns the image control from the given string
        def build_image(image_str: str) -> ft.Image:
            return
        
        
        # Refresh the snapshots of all connected canvases
        def refresh_snapshots():
            pass

        # Sets the background color of the preview display
        async def set_preview_background_color(e):
            pass

        # Switch between vertical and horizontal preview display
        async def swap_preview_direction(e):
            new_direction = e.control.data
            self.update_data(**{'preview_direction': new_direction})

        async def reorder_snapshots(e: ft.OnReorderEvent):
            if e.old_index == e.new_index:
                return
            self.data['featured_images'].insert(e.new_index, self.data['featured_images'].pop(e.old_index))
            self.update_data(**{'featured_images': self.data.get('featured_images', [])})
            
            


        vertical_preview = ft.Column([

        ])

        horizontal_preview = ft.Row([

        ])

        # Load images into both controls above here ^

        preview_stack = ft.Stack([
            ft.Container(bgcolor="black", expand=True),
            ft.Container(vertical_preview, bgcolor=self.data.get('preview_background_color', ft.Colors.BLACK)),
            ft.Container(horizontal_preview, bgcolor=self.data.get('preview_background_color', ft.Colors.BLACK)),
        ], expand=3, alignment=ft.Alignment.CENTER)
        


        show_info_button = ft.IconButton(
            ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT_ROUNDED, self.data.get('color', ft.Colors.PRIMARY),
            on_click=show_mini_widgets_container, 
            opacity=1 if not self.data.get('show_info', True) else 0,
            disabled=self.data.get('show_info', True),
            mouse_cursor=ft.MouseCursor.CLICK if not self.data.get('show_info', True) else None,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
        )

        self.content = ft.Row([
            preview_stack,
            show_info_button,
            self.mini_widgets_container,
        ], expand=True)
        

    def reload_widget(self):
        return