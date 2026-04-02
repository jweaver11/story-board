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
        self.body_container.padding = ft.Padding.only(left=16, top=16, bottom=16)

        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {
                # Widget data
                'key': f"{self.directory_path}\\{return_safe_name(self.title)}_item", 
                'tag': "item",             # Tag to identify what type of object this is
                'color': app.settings.data.get('default_item_color'),
                'pin_location': app.settings.data.get('default_item_pin_location', "right") if data is None else data.get('pin_location', "right"),   # Default pin location for items

                'edit_mode': True,      # Whether we are in edit mode or not
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

    # Called when clicking the edit mode button
    def _edit_mode_clicked(self, e=None):
        ''' Switches between edit mode and not for the item  '''

        # Change our edit mode data flag, and save it to file
        self.data['edit_mode'] = not self.data['edit_mode']
        self.p.run_task(self.save_dict)

        # Reload the widget. The reload widget should load differently depending on if we're in edit mode or not
        self.reload_widget()

    def _edit_mode_view(self):
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
                    ),
                    ft.Container(width=1)
                ])
            )

        description_text_field = TextField(
            self.data.get('Description', ""),
            multiline=True, expand=True,
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
            expand=True, horizontal_alignment=ft.CrossAxisAlignment.START, scroll="auto",
            controls=[
                #ft.Container(height=1),
                ft.Row(
                    [
                        upload_image_button, 
                        ft.Column([
                            ft.Row([
                                ft.Text(f"Description", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=18), color=self.data.get('color', None)),
                                ft.IconButton(
                                    tooltip="Edit Mode", icon=ft.Icons.EDIT_OUTLINED, icon_color=self.data.get('color', None), 
                                    on_click=self._edit_mode_clicked, mouse_cursor="click"
                                ),
                            ]),
                            description_text_field
                        ], horizontal_alignment=ft.CrossAxisAlignment.START, expand=True, tight=True, spacing=0), 
                        ft.Container(width=6)
                ]
                )]
                + segments_list
                + [add_segment_button]
        )

        # Assign the body_container content as whatever view you have built in the widget
        self.body_container.content = body

    # Called after any changes happen to the data that need to be reflected in the UI, usually just ones that require a rebuild
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # Rebuild out tab to reflect any changes
        self.reload_tab()

        # Check if we're in edit mode or not. If yes, build the edit view like this
        if self.data.get('edit_mode', False):
            self._edit_mode_view()
            self._render_widget()
            return
        
        def _load_item_data_controls():
            ''' Loads data from a dict into a given container '''

            control_list = []
            if len(self.data.get('item_data', [])) == 0:
                control_list.append(ft.Text("No item data added yet", italic=True))
                return control_list
            
            # Go through our sections inside of our item data
            for dict in self.data.get('item_data', []):


                # List to hold text spans for each text control in the container
                text_span_list = []
                label = dict.get('title', '')
                value = dict.get('content', '')

                # Set a label and container to hold our text spans for each section
                #label = ft.Text(f"\t{label}", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=18), color=self.data.get('color', None))

                #control_list.append(label)
                
                if isinstance(value, str):

                    # If artifically created new lines, treat as bullet point list
                    if "\n" in value:
                        if label != "":
                            text_span_list.append(
                                ft.TextSpan(f"{label}:\n", ft.TextStyle(size=16, weight=ft.FontWeight.BOLD))
                            ) 

                        # Add the value for this key, with a bullet point if there are multiple values separated by new lines
                        values = [v.strip() for v in value.replace('\n', ',').split(',') if v.strip()]
                        for val in values:
                            text_span_list.append(ft.TextSpan(f"\t\u2022\t{val}\n"))

                    # Otherwise, just add the key and value normally
                    else:

                        # Add the each key for this section
                        if label != "":
                            text_span_list.append(
                                ft.TextSpan(f"{label}:\t\t", ft.TextStyle(16, weight=ft.FontWeight.BOLD))
                            )
                        text_span_list.append(ft.TextSpan(f"{value}\n"))     # Rest of the value

                # Container to hold the text control of our section info
                value = ft.Text(spans=text_span_list, size=16)

                # Remove unnecessary new line at the end for cleaner formatting
                last_span = text_span_list[-1] if text_span_list else None
                if last_span and last_span.text.endswith("\n"):
                    last_span.text = last_span.text[:-1]  # Remove the last new line for cleaner formatting

                # Add the label and container with our text spans to the control list for this section
                
                control_list.append(value)

            return control_list
        
        
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
            img = ft.Icon(ft.Icons.PERSON_OUTLINE, size=100, color=self.data.get('color', "primary"), expand=False)
            

        description_section = ft.Column([
            ft.Row([
                ft.Text(f"Description", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=18), color=self.data.get('color', None)),
                ft.IconButton(
                    tooltip="Edit Mode", icon=ft.Icons.EDIT_OUTLINED, icon_color=self.data.get('color', None), 
                    on_click=self._edit_mode_clicked, mouse_cursor="click"
                ),
            ]),
            ft.Container(
                ft.Text(
                    f"{self.data.get('Description', '')}", expand=True, size=16
                ), margin=ft.Margin.only(right=16)), # Forces container to take up space
            
        ], expand=True, spacing=0)

        
        # Header that holds our image, edit mode button, and about section
        header = ft.Row([
            ft.IconButton(img, tooltip="Upload Image", on_click=self._upload_item_image, mouse_cursor="click"),
            description_section
        ], vertical_alignment=ft.CrossAxisAlignment.START)


        # Body that holds the rest of our widget
        body = ft.Column(
            controls=[header],
            scroll="auto", expand=True, spacing=4
        )

        # Load in our item data controls after the header
        body.controls.extend(_load_item_data_controls())   

        # Set the body we built
        self.body_container.content = body
        
        # Build in widget function that will handle loading our mini widgets and rendering the whole thing
        self._render_widget()
        