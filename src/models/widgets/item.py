''' Class for the Item widget. Displays as its own tab for easy access to pinning '''

import flet as ft
from models.views.story import Story
from models.widget import Widget
from utils.verify_data import verify_data
from styles.menu_option_style import MenuOptionStyle
from models.app import app
from utils.safe_string_checker import return_safe_name
from styles.text_field import TextField
    

class Item(Widget):

    # Constructor
    def __init__(self, title: str, page: ft.Page, directory_path: str, story: Story, data: dict = None, is_rebuilt: bool = False):

        # Check if we're new and need to create file
        is_new = False
        if data is None:
            is_new = True

        # Initialize from our parent class 'Widget'. 
        super().__init__(
            title = title,                      
            page = page,                        
            directory_path = directory_path,    
            story = story,                     
            data = data,
            is_rebuilt = is_rebuilt
        )

        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {
                # Widget data
                'key': f"{self.directory_path}\\{return_safe_name(self.title)}_item", 
                'tag': "item",             # Tag to identify what type of object this is
                'color': app.settings.data.get('default_item_color'),
                'pin_location': app.settings.data.get('default_item_pin_location', "right") if data is None else data.get('pin_location', "right"),   # Default pin location for items

                'image_base64': str, 
                'Description': str,

                # Item data - list of segments with title and string
                'item_data': [
                    {'title': "Type", 'content': ""},
                    {'title': "Rarity", 'content': ""}, 
                    {'title': "Effects", 'content': ""},
                    {'title': "Material", 'content': ""},
                    {'title': "Size", 'content': ""},
                    {'title': "Weight", 'content': ""},
                    {'title': "Lore", 'content': ""},
                    {'title': "Cost", 'content': ""},
                    {'title': "Locations", 'content': ""},
                    {'title': "Count", 'content': ""},
                    {'title': "Notes", 'content': ""},
                ]
            },
        )

        # Saving creates the file if we're new
        if is_new:
            self.p.run_task(self.save_dict)
        
        if self.visible:
            self.reload_widget()         # Build our widget if it's visible on init

    # Opens a dialog to create a new segment in the note and then saves and reloads
    async def _create_new_segment(self, e=None):

        # Adds our new segment to the bottom of the list
        async def create_segment(e=None):
            self.data['item_data'].append({"title": new_segment_tf.value, "content": ""})
            await self.save_dict()
            self.reload_widget()
            self.p.pop_dialog()

        new_segment_tf = ft.TextField(autofocus=True, capitalization=ft.TextCapitalization.WORDS, on_submit=create_segment)

        dlg = ft.AlertDialog(
            title=ft.Text("Segment Title"),
            content=new_segment_tf,
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.p.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                ft.TextButton("Create", on_click=create_segment, style=ft.ButtonStyle(mouse_cursor="click"))
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.p.show_dialog(dlg)

    # Saves content when text field is unfocused
    async def _save_segment(self, e):
        index = e.control.data
        if len(self.data['item_data']) > index:
            self.data['item_data'][index]['content'] = e.control.value
            await self.save_dict()

    # Deletes a segment from the item
    async def _delete_segment(self, e):
        index = e.control.data
        if len(self.data['item_data']) > index:
            del self.data['item_data'][index]
            await self.save_dict()
            self.reload_widget()

    # Called when clicking our upload image button
    async def _upload_item_image(self, e=None):

        files = await ft.FilePicker().pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "webp"])
        if files:

            file_path = files[0].path
            try:
                import base64

                with open(file_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    # Save to our data
                    self.data['image_base64'] = f"{encoded_string}"
                    await self.save_dict()
                    self.reload_widget()

            except Exception as _:
                pass

    # Called after any changes happen to the data that need to be reflected in the UI, usually just ones that require a rebuild
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # Rebuild out tab to reflect any changes
        self.reload_tab()

        if self.data.get('image_base64', ""):
            img = ft.Container(
                ft.Image(
                    src=self.data.get('image_base64', ""),
                    width=100,
                    height=100,
                    fit=ft.BoxFit.FILL,
                ), shape=ft.BoxShape.CIRCLE, clip_behavior=ft.ClipBehavior.ANTI_ALIAS
            )
        else:
            img = ft.Icon(ft.Icons.SHIELD_OUTLINED, size=100, color=self.data.get('color', "primary"), expand=False)
        
        # Hold our segment controls when we load the item data
        segments_list = []

        # Go through the item data and load the segments
        for idx, segment in enumerate(self.data.get('item_data', [])):
            key = segment.get('title', '')
            value = segment.get('content', '')
            segments_list.append(
                ft.Row([
                    TextField(
                        value, expand=True,
                        multiline=True, label=key, dense=True, capitalization=ft.TextCapitalization.SENTENCES, 
                        on_blur=self._save_segment,
                        data=idx,
                    ),
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR,
                        tooltip=f"Delete segment {key}",
                        on_click=self._delete_segment,
                        mouse_cursor="click", data=idx
                    )
                ])
            )

        description_text_field = TextField(
            self.data.get('Description', ""),
            label="Description", multiline=True, expand=True,
            capitalization=ft.TextCapitalization.SENTENCES, 
            on_blur=lambda e: self.data.__setitem__('Description', e.control.value) or self.p.run_task(self.save_dict)
        )


        upload_image_button = ft.IconButton(img, tooltip="Upload Image", on_click=self._upload_item_image, mouse_cursor="click")

        add_segment_button = ft.TextButton(
            "Add New Segment", ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, 
            tooltip="Add New Segment to Item",
            on_click=self._create_new_segment, 
            style=ft.ButtonStyle(self.data.get('color', ft.Colors.PRIMARY), icon_size=20, mouse_cursor=ft.MouseCursor.CLICK, text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)),
        )
        
        body = ft.Column(
            expand=True, horizontal_alignment=ft.CrossAxisAlignment.START,
            controls=[ft.Row([upload_image_button, description_text_field])] + segments_list + [add_segment_button]
        )

        # Assign the body_container content as whatever view you have built in the widget
        self.body_container.content = body
        
        # Build in widget function that will handle loading our mini widgets and rendering the whole thing
        self._render_widget()
        