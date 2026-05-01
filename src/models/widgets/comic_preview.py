''' Class for the Notes widget. Displays as its own tab for easy access to pinning '''

import flet as ft
from models.views.story import Story
from models.widget import Widget
from utils.verify_data import verify_data
from styles.menu_option_style import MenuOptionStyle
from models.app import app
from utils.safe_string_checker import return_safe_name
from styles.text_field import TextField
import base64
from PIL import Image
from io import BytesIO
from styles.snack_bar import SnackBar
import asyncio
from flet_color_pickers import BlockPicker
    

class ComicPreview(Widget):

    # Constructor
    def __init__(self, title: str, page: ft.Page, directory_path: str, story: Story, data: dict = None, is_rebuilt: bool = False):

        # Check if we're new and need to create file
        is_new = False
        if data is None:
            is_new = True

        # Initialize from our parent class 'Widget'. 
        super().__init__(
            title = title,                      # Title of the note
            page = page,                        # Grabs our original page for convenience and consistency
            directory_path = directory_path,    # Path to our notes json file
            story = story,                      # Reference to our story object
            data = data,
            is_rebuilt = is_rebuilt
        )


        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {
                # Widget data
                'key': f"{self.directory_path}\\{return_safe_name(self.title)}_comic_preview", 
                'tag': "comic_preview",             # Tag to identify what type of object this is
                'color': app.settings.data.get('default_comic_preview_color', "primary"),
                'pin_location': app.settings.data.get('default_comic_preview_pin_location', "right") if data is None else data.get('pin_location', "right"),   # Default pin location for notes
                'preview_direction': "vertical",      # Default direction for comic preview, can be vertical or horizontal
                'preview_background_color': "#00000000",  # Background color shown in comic preview widgets
                'show_info': True,                    # Whether or not to show the info column on the left side of the page
                'can_add_canvases': True,               # Whether or not the user can add canvases to the preview (as opposed to just uploading images)
                'featured_canvases': [              # List to hold our featured_canvases of the canvases. Also allows png uploads
                    #{
                        #'key': "canvas_key or None" is None if its an uploaded image
                        #'title': "title of the snapshot, either canvas name or file name",
                        #'image': "base64 string of the image"
                    #}
                ],                      
            },
        )

        #self.body_container.padding = ft.Padding.only(left=16, top=16, bottom=16)
        

        # Saving creates the file if we're new
        if is_new:
            self.p.run_task(self.save_dict)
        
        if self.visible:
            self.reload_widget()         # Build our widget if it's visible on init

    def _get_menu_options(self):

        async def _change_color_clicked(e):
            # Updates our background color
            async def _set_background_color(e: ft.ControlEvent):
                self.data['preview_background_color'] = e.data
                await self.save_dict()
                self.preview_display_container.bgcolor = self.data.get('preview_background_color', ft.Colors.BLACK)
                self.preview_display_container.update()


            await self.story.close_menu()
            
            self.p.show_dialog(
                ft.AlertDialog(
                    title=ft.Text("Select Background Color"),
                    content=BlockPicker(
                        color=self.data.get('preview_background_color', "#00000000"),
                        available_colors=[
                            "#000000",
                            "#ffffff",
                            "#3b3b3b",
                            "#858585",
                            "#adadad",
                            "#ff1100",
                            "#d9ff00",
                            "#9c27b0",
                            "#3f51b5",
                            "#2196f3",
                            "#009688",
                            "#4caf50",
                            "#795548",
                            "#00000000",  # Transparent option

                        ],
                        on_color_change=_set_background_color,
                    ),
                    actions=[
                        ft.TextButton("Close", on_click=lambda _: self.p.pop_dialog(), style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK))
                    ]
                )
            )




        options = [
            MenuOptionStyle(
                on_click=_change_color_clicked,
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.data.get('color', 'primary'),),
                        ft.Text(
                            "Set BG Color", 
                            weight=ft.FontWeight.BOLD, 
                            
                        ), 
                    ],
                    tooltip="Change the background color of the comic preview",
                ),
            ),
        ]
        options.extend(super()._get_menu_options())
        return options

    # Called to find a canvas and load a snapshot from all its layers
    def _set_canvas_snapshot(self, canvas_key: str) -> str:

        def _blank_png() -> str:
            blank = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
            output = BytesIO()
            blank.save(output, format="PNG")
            return base64.b64encode(output.getvalue()).decode("utf-8")

        capture_list = []
        for widget in self.story.widgets:
            if widget.data['key'] == canvas_key:
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
    
    # Called to refresh any connected canvases featured_canvases that might be outdated
    async def _refresh_canvas_snapshots(self):
        self.story.blocker.visible = True
        self.story.blocker.update()
        await asyncio.sleep(0)
        for snapshot in self.data.get('featured_canvases', []):
            if snapshot.get('key'):
                snapshot['image'] = self._set_canvas_snapshot(snapshot['key'])
        await self.save_dict()
        self.reload_widget()
        if self.story.blocker.visible:
            self.story.blocker.visible = False
            self.story.blocker.update()


    # Called after any changes happen to the data that need to be reflected in the UI, usually just ones that require a rebuild
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        async def _remove_snapshot(e):
            self.story.blocker.visible = True
            self.story.blocker.update()
            await asyncio.sleep(0)
            idx = e.control.data
            self.data['featured_canvases'].pop(idx)
            await self.save_dict()

            self.reload_widget()
            if self.story.blocker.visible:
                self.story.blocker.visible = False
                self.story.blocker.update()

        async def _add_canvas_snapshot(e):
            self.story.blocker.visible = True
            self.story.blocker.update()
            await asyncio.sleep(0)
            key = e.control.data
            title = None
            for widget in self.story.widgets:
                if widget.data.get('key') == key:
                    title = widget.title    
            self.data['featured_canvases'].append({
                'key': key,
                'title': title,
                'image': self._set_canvas_snapshot(key)
            })
            await self.save_dict()
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
            await self.save_dict()
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
                            self.data['featured_canvases'].append({
                                'key': None,
                                'title': file_path.split("\\")[-1],
                                'image': encoded_string
                            })
                            

                    except Exception as _:
                        pass
                await self.save_dict()
                self.story.blocker.visible = True
                self.story.blocker.update()
                await asyncio.sleep(0)
                self.reload_widget()
                self.story.blocker.visible = False
                self.story.blocker.update()

        # Handles reordering our featured_canvases on the left side of the page
        async def _reorder_snapshots(e: ft.OnReorderEvent):
            if e.old_index == e.new_index:
                return
            self.story.blocker.visible = True
            self.story.blocker.update()
            await asyncio.sleep(0)
            self.data['featured_canvases'].insert(e.new_index, self.data['featured_canvases'].pop(e.old_index))
            await self.save_dict()
            self.reload_widget()
            if self.story.blocker.visible:
                self.story.blocker.visible = False
                self.story.blocker.update()

        # Handles showing/hiding all the canvases that are featured or could be featured in the preview
        async def _toggle_featured_canvases(e):
            self.data['can_add_canvases'] = not self.data.get('can_add_canvases', True)
            await self.save_dict()
            if self.data.get('can_add_canvases', True):
                e.control.icon = ft.Icons.EDIT_OUTLINED
                selectable_snapshots.visible = True
            else:
                e.control.icon = ft.Icons.EDIT_OFF_OUTLINED
                selectable_snapshots.visible = False
            e.control.update()
            selectable_snapshots.update()

        # Rebuild out tab to reflect any changes
        self.reload_tab()


        preview_display = ft.Column() if self.data.get('preview_direction', "vertical") == "vertical" else ft.Row()
        preview_display.spacing = 0
        preview_display.scroll = ft.ScrollMode.AUTO
        preview_display.expand = 2

        preview_display.controls = []

        for snapshot in self.data.get('featured_canvases', []):
            preview_display.controls.append(ft.Image(snapshot.get('image', ""), ft.Text("Error loading image"), fit=ft.BoxFit.CONTAIN, data=snapshot.get('key')))

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

        



        # If we're not showing info, just give us a button to show info and return early
        if not self.data.get('show_info', True):

            self.body_container.content = ft.Row(
                [
                    preview_display_wrapper, 
                    ft.IconButton(
                        ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT_ROUNDED, self.data.get('color', ft.Colors.PRIMARY),
                        on_click=self._toggle_show_info, 
                        mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER,
                    )
                ], expand=True, spacing=0
            )
            self._render_widget()
            return 
        
        # Mini map with preview of all featured_canvases (very small) on the left side of the page
        snapshot_mini_map = ft.Column(
            [
                
                ft.Row([
                    ft.Text("Featured Canvases", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)), 
                    ft.IconButton(
                        ft.Icons.EDIT_OUTLINED if self.data.get('can_add_canvases', True) else ft.Icons.EDIT_OFF_OUTLINED, self.data.get('color', ft.Colors.PRIMARY),
                        tooltip="Add or remove canvases to be featured in the preview",
                        on_click=_toggle_featured_canvases,
                        mouse_cursor=ft.MouseCursor.CLICK,
                    )
                ], spacing=0)
                
                
            ],
            expand=1, scroll="auto", spacing=0
        )

        # Add featured canvases to the mini map that are reorderable
        featured_canvases = ft.ReorderableListView(scroll="auto", on_reorder=_reorder_snapshots)
        for idx, snapshot in enumerate(self.data.get('featured_canvases', [])):
            featured_canvases.controls.append(
                ft.ReorderableDragHandle(
                    ft.Row([
                        ft.Image(snapshot.get('image', ""), ft.Text("Error loading image"), fit=ft.BoxFit.CONTAIN, width=50, height=50),
                        ft.Text(snapshot.get('title', "Untitled"), weight=ft.FontWeight.BOLD),
                        
                        ft.Container(expand=True, height=50),
                        ft.IconButton(
                            ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR, on_click=_remove_snapshot, 
                            mouse_cursor=ft.MouseCursor.CLICK, data=idx,
                            tooltip="Remove from preview",
                        ),  # Only show delete button its an uploaded image
                        ft.Container(width=40)
                    ]),
                    data=snapshot.get('key')
                )
            )
        snapshot_mini_map.controls.append(featured_canvases)

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
        for widget in self.story.widgets:
            if widget.data.get('tag', "") == "canvas":
                selectable_snapshots.controls.append(
                    
                    ft.Row([
                        ft.IconButton(
                            ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, widget.data.get('color', ft.Colors.PRIMARY), on_click=_add_canvas_snapshot, 
                            mouse_cursor=ft.MouseCursor.CLICK, data=widget.data.get('key')
                        ),
                        ft.Image(self._set_canvas_snapshot(widget.data.get('key')), ft.Text("Error loading image"), fit=ft.BoxFit.CONTAIN, width=50, height=50),
                        ft.Text(f"\t\t{widget.title}", style=ft.TextStyle(weight=ft.FontWeight.BOLD), color=widget.data.get('color', None)),
                        
                    ], spacing=0, tight=True)
                )

       

        snapshot_mini_map.controls.append(selectable_snapshots)

        snapshot_mini_map_container = ft.Container(
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
                        ft.Icons.CLOSE, ft.Colors.ON_SURFACE_VARIANT, on_click=self._toggle_show_info,
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

        

        # Assign the body_container content as whatever view you have built in the widget
        self.body_container.content = ft.Row([preview_display_wrapper, snapshot_mini_map_container], spacing=0, expand=True)
        
        # Build in widget function that will handle loading our mini widgets and rendering the whole thing
        self._render_widget()