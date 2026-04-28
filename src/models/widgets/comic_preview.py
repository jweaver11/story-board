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
                'show_info': True,                    # Whether or not to show the info column on the left side of the page
                'can_add_canvases': True,               # Whether or not the user can add canvases to the preview (as opposed to just uploading images)
                'snapshots': [              # List to hold our snapshots of the canvases. Also allows png uploads
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


    # Called after any changes happen to the data that need to be reflected in the UI, usually just ones that require a rebuild
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        async def _remove_snapshot(e):
            idx = e.control.data
            self.data['snapshots'].pop(idx)
            await self.save_dict()
            # Remove from mini map
            included_canvases.controls.pop(idx)
            included_canvases.update()
           
            preview_display.controls.pop(idx)
            preview_display.update()
            

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
                            self.data['snapshots'].append({
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

        # Handles reordering our snapshots on the left side of the page
        async def _reorder_snapshots(e: ft.OnReorderEvent):
            if e.old_index == e.new_index:
                return
            self.data['snapshots'].insert(e.new_index, self.data['snapshots'].pop(e.old_index))
            await self.save_dict()
            self.reload_widget()

        # Handles showing/hiding all the canvases that are included or could be included in the preview
        async def _toggle_included_canvases(e):
            self.data['can_add_canvases'] = not self.data.get('can_add_canvases', True)
            await self.save_dict()
            if self.data.get('can_add_canvases', True):
                can_add_canvases_button.content.controls[1].icon = ft.Icons.EDIT_OUTLINED
                selectable_snapshots.visible = True
            else:
                can_add_canvases_button.content.controls[1].icon = ft.Icons.EDIT_OFF_OUTLINED
                selectable_snapshots.visible = False
            can_add_canvases_button.update()
            selectable_snapshots.update()

        # Handles connecting/removing a canavs snapshot
        async def _toggle_canvas_inclusion(e):
            canvas_key = e.control.data
            included_canvas_keys = [snapshot.get('key') for snapshot in self.data.get('snapshots', [])]

            # If we're adding a canvas
            if canvas_key in included_canvas_keys:

                # Remove from data
                self.data['snapshots'] = [snapshot for snapshot in self.data.get('snapshots', []) if snapshot.get('key') != canvas_key]

                # Remove from mini map
                for control in included_canvases.controls:
                    if control.data == canvas_key:
                        included_canvases.controls.remove(control)
                        break
                
                # Remove from preview
                for control in preview_display.controls:
                    if control.data == canvas_key:
                        preview_display.controls.remove(control)
                        break

            # If we're removing a canvas
            else:
                # Add to data
                canvas_widget = next((widget for widget in self.story.widgets if widget.data.get('key') == canvas_key), None)
                snapshot = self._set_canvas_snapshot(canvas_key)
                if canvas_widget:

                    self.data['snapshots'].append({
                        'key': canvas_key,
                        'title': canvas_widget.title,
                        'image': snapshot
                    })

                    # Add to mini map
                    included_canvases.controls.append(
                        ft.ReorderableDragHandle(   
                            ft.Row([
                                ft.Text(canvas_widget.title, weight=ft.FontWeight.BOLD),
                                ft.Image(snapshot, ft.Text("Error loading image"), fit=ft.BoxFit.CONTAIN, width=50, height=50)
                            ]),
                            data=canvas_key
                        )
                    )
                    

                    # Add to preview   
                    preview_display.controls.append(ft.Image(snapshot, ft.Text("Error loading image"), fit=ft.BoxFit.CONTAIN, data=canvas_key))
                    

            await self.save_dict()
            included_canvases.update()
            preview_display.update()

        # Rebuild out tab to reflect any changes
        self.reload_tab()

        # Button to toggle the preview direction between vertical and horizontal
        toggle_preview_direction_button = ft.IconButton(
            ft.Icons.SWAP_VERT if self.data.get('preview_direction', "vertical") == "vertical" else ft.Icons.SWAP_HORIZ,
            self.data.get('color', ft.Colors.PRIMARY),
            tooltip="Toggle preview direction",
            on_click=_toggle_preview_direction,
            mouse_cursor=ft.MouseCursor.CLICK,
        )


        preview_display = ft.Column() if self.data.get('preview_direction', "vertical") == "vertical" else ft.Row()
        preview_display.spacing = 0
        preview_display.scroll = ft.ScrollMode.AUTO
        preview_display.expand = 2

        preview_display.controls = []

        for snapshot in self.data.get('snapshots', []):
            preview_display.controls.append(ft.Image(snapshot.get('image', ""), ft.Text("Error loading image"), fit=ft.BoxFit.CONTAIN, data=snapshot.get('key')))

        preview_display_container = ft.Container(
            ft.Row([
                ft.Container(expand=1), 
                preview_display, 
                ft.Container(expand=1)
            ], 
            expand=True, spacing=0, scroll="none", vertical_alignment=ft.CrossAxisAlignment.START
            ) if self.data.get('preview_direction', "vertical") == "vertical" else ft.Column([
                ft.Container(expand=1), 
                preview_display, 
                ft.Container(expand=1)
            ], expand=True, spacing=0, scroll="none", horizontal_alignment=ft.CrossAxisAlignment.START
            ),
            expand=3,
            alignment=ft.Alignment.CENTER
        )

        # If we're not showing info, just give us a button to show info and return early
        if not self.data.get('show_info', True):

            self.body_container.content = ft.Row(
                [
                    preview_display_container, 
                    ft.IconButton(
                        ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT_ROUNDED, self.data.get('color', ft.Colors.PRIMARY),
                        on_click=self._toggle_show_info, 
                        mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER,
                    )
                ], expand=True, spacing=0
            )
            self._render_widget()
            return 
        
        # Mini map with preview of all snapshots (very small) on the left side of the page
        snapshot_mini_map = ft.Column(
            [
                ft.Row([
                    ft.Text(
                        f"\t{self.title}", theme_style=ft.TextThemeStyle.TITLE_LARGE, 
                        color=self.data.get('color', None), weight=ft.FontWeight.BOLD, 
                    ),
                    toggle_preview_direction_button,
                    
                    ft.Container(expand=True),
                    ft.IconButton(
                        ft.Icons.CLOSE, ft.Colors.ON_SURFACE_VARIANT, on_click=self._toggle_show_info,
                        mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER,
                    ),
                ], spacing=0),
                ft.Divider(2, 2),
                can_add_canvases_button := ft.TextButton(
                    ft.Row([
                        ft.Text(
                        "Included", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)
                    ), 
                        ft.Icon(
                            ft.Icons.EDIT_OUTLINED if self.data.get('can_add_canvases', True) else ft.Icons.EDIT_OFF_OUTLINED,
                            self.data.get('color', None)
                        )
                    ], tight=True),
                    tooltip="Add or remove canvases to be included in the preview",
                    style=ft.ButtonStyle(text_style=ft.TextStyle(weight=ft.FontWeight.BOLD), mouse_cursor="click", color=self.data.get('color', ft.Colors.PRIMARY)),
                    on_click=_toggle_included_canvases,
                ),
            ],
            expand=1, scroll="none"
        )

        # Add included canvases to the mini map that are reorderable
        included_canvases = ft.ReorderableListView(scroll="auto", on_reorder=_reorder_snapshots)
        for idx, snapshot in enumerate(self.data.get('snapshots', [])):
            included_canvases.controls.append(
                ft.ReorderableDragHandle(
                    ft.Row([
                        ft.Text(snapshot.get('title', "Untitled"), weight=ft.FontWeight.BOLD),
                        ft.Image(snapshot.get('image', ""), ft.Text("Error loading image"), fit=ft.BoxFit.CONTAIN, width=50, height=50),
                        ft.Container(expand=True),
                        ft.IconButton(
                            ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR, on_click=_remove_snapshot, 
                            mouse_cursor=ft.MouseCursor.CLICK, data=idx
                        ) if not snapshot.get('key') else ft.Container(),  # Only show delete button its an uploaded image
                        ft.Container(width=40)
                    ]),
                    data=snapshot.get('key')
                )
            )
        snapshot_mini_map.controls.append(included_canvases)

        selectable_snapshots = ft.Column(
            [ft.Divider(2, 2)], 
            scroll="none", expand=True,
            visible=True if self.data.get('can_add_canvases', True) else False
        )

        # For loop to add all canvases in story as options to be included in the preview
        for widget in self.story.widgets:
            if widget.data.get('tag', "") == "canvas":
                selectable_snapshots.controls.append(
                    ft.Checkbox(
                        widget.title, 
                        value=widget.data.get('key') in [snapshot.get('key') for snapshot in self.data.get('snapshots', [])], 
                        on_change=_toggle_canvas_inclusion, 
                        data=widget.data.get('key'),
                        mouse_cursor=ft.MouseCursor.CLICK,
                        label_style=ft.TextStyle(color=widget.data.get('color', None), weight=ft.FontWeight.BOLD),
                    )
                )

        snapshot_mini_map.controls.append(selectable_snapshots)

        selectable_snapshots.controls.append(
            ft.TextButton(
                "Upload Image",
                ft.Icons.FILE_UPLOAD_OUTLINED,
                on_click=_upload_snapshot_clicked,
                style=ft.ButtonStyle(text_style=ft.TextStyle(weight=ft.FontWeight.BOLD), mouse_cursor=ft.MouseCursor.CLICK, color=self.data.get('color', ft.Colors.PRIMARY)),
            )
        )
        

        snapshot_mini_map_container = ft.Container(
            snapshot_mini_map,
            border=ft.Border.only(left=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            padding=ft.Padding.only(left=11, top=8, bottom=8),
            shadow=ft.BoxShadow(0, 1),
            expand=1,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
        )

        

        # Assign the body_container content as whatever view you have built in the widget
        self.body_container.content = ft.Row([preview_display_container, snapshot_mini_map_container], spacing=0, expand=True)
        
        # Build in widget function that will handle loading our mini widgets and rendering the whole thing
        self._render_widget()
        