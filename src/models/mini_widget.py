'''
Parent class for mini widgets, which are extended flet containers used as information displays on the side of the parent widget
Makes showing detailed information easier without rending and entire widget where it doesn't make sense
Mini widgets either are exclusive (only they are shown), or shared (additional mini widgets can be shown at same time)
Mini widgets are stored in their widgetS (Widget) json file, not their own file
Some mini widgets can have their own files IN ADDITION to normal storage, such as maps or drawings storing images
'''


import flet as ft
from models.widget import Widget
from utils.verify_data import verify_data
from styles.menu_option_style import MenuOptionStyle
from styles.colors import colors
import asyncio
from utils.safe_string_checker import return_safe_name

class MiniWidget(ft.Container):

    # Constructor. All mini widgets require a title, widget widget, page reference...
    # Dictionary path, and optional data dictionary
    def __init__(
        self, 
        title: str,                     # Title of the widget that will show up on its tab
        widget: Widget,                  # The widget that contains this mini widget.
        page: ft.Page,                  # Grabs our original page for convenience and consistency
        key: str,                       # Key to identify this mini widget (by title) within its widgets data
        side_location: str = None,      # Side of the widget the mini widget shows on
        data: dict = None               # Data passed in for this mini widget
    ):

        # Parent constructor
        super().__init__(
            expand=True,
            border_radius=ft.BorderRadius.all(10),
            border=ft.Border.all(2, ft.Colors.SECONDARY_CONTAINER),
            padding=ft.Padding.all(8),
            data=data,     
            bgcolor=ft.Colors.with_opacity(.7, ft.Colors.SURFACE),
            blur=5,
        )

        
        # Set our parameters
        self.title: str = title                      
        self.widget: Widget = widget                          
        self.p: ft.Page = page                               
        self.key: str = key     


        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   # Pass in our object so we can access its data and change it
            {   
                'title': self.title,          # Title of the mini widget, should match the object title
                'tag': "mini_widget",         # Default mini widget tag, but should be overwritten by child classes
                'visible': True,              # If the widget is visible
                'is_shown_on_widget': True,          # If the mini widget is shown on the parent widget. Some widgets can toggle this off
                'is_pinned': False,           # If the mini widget is pinned open and will remain open
                'side_location': side_location if side_location is not None else "right",     # Side of the widget the mini widget shows on
                'custom_fields': dict,        # Dictionary for any custom fields the mini widget wants to store
            },
        )

        if data is None:
            self.p.run_task(self.save_dict)

        # Apply our visibility
        self.visible = self.data.get('visible', True)
        
    # Called every time the mouse moves over our rail
    async def _set_menu_coords(self, e: ft.PointerEvent):
        ''' Stores our mouse positioning so we know where to open menus '''
        self.widget.story.mouse_x = e.global_position.x 
        self.widget.story.mouse_y = e.global_position.y

    # Called when saving changes in our mini widgets data to the widgetS json file
    async def save_dict(self):
        ''' Saves our current data to the widgetS json file using this objects dictionary path '''

        try:
        
            # If our data is None (we just got deleted), we don't save ourselves to widgets data
            if self.data is None:
                self.widget.data[self.key].pop(self.title, None)

            # Otherwise, save like normal
            else:

                # Our data is correct, so we update our immidiate parents data to match
                self.widget.data[self.key][self.title] = self.data

            # Recursively updates the parents data until widget=widget (widget), which saves to file
            await self.widget.save_dict()

        except Exception as e:
            print(f"Error saving mini widget data to {self.title}: {e}")
            

    # Called when deleting our mini widget
    def delete_dict(self):
        ''' Deletes our data from all live widget/mini widget objects that we nest in, and saves the widgets file '''

        try:

            # Applies the UI changes by removing ourselves from the mini widgets list
            if self in self.widget.mini_widgets:
                self.widget.mini_widgets.remove(self)

            tag = self.data.get('tag', '')  

            match tag:
                case "plot_point":
                    self.widget.delete_plot_point(self)
                case "marker":
                    self.widget.delete_marker(self)
                case "arc":
                    self.widget.delete_arc(self)
                case "comment":
                    self.widget.delete_comment(self.title)
                case "location":
                    self.widget.delete_location(self)

                case _:
                    print("Invalid mw key")
                

            # Remove our data.
            self.data = None
            self.p.run_task(self.save_dict)

            # Reload the widget if we have to
            self.widget.reload_widget()

            # Also reload the active rail to reflect changes
            self.widget.story.active_rail.content.reload_rail() 
            self.widget.story.close_menu_instant()

        # Catch errors
        except Exception as e:
            print(f"Error deleting mini widget {self.title}: {e}")

    # Called for little data changes
    def change_data(self, **kwargs):
        ''' Changes a key/value pair in our data and saves the json file '''
        # Called by:
        # mini_widget.change_data(**{'key': value, 'key2': value2})

        try:
            for key, value in kwargs.items():
                self.data.update({key: value})

            self.p.run_task(self.save_dict)

        # Handle errors
        except Exception as e:
            print(f"Error changing data {key}:{value} in widget {self.title}: {e}")

    def change_custom_field(self, **kwargs):
        ''' Changes a key/value pair in our custom fields dictionary and saves the json file '''
        # Called by:
        # widget.change_custom_field(**{'key': value, 'key2': value2})

        try:
            for key, value in kwargs.items():
                self.data['custom_fields'].update({key: value})

            self.p.run_task(self.save_dict)

        # Handle errors
        except Exception as e:
            print(f"Error changing custom field {key}:{value} in widget {self.title}: {e}")

    


    def rename(self, new_name: str):
        ''' Renames our mini widget, updating all references and data accordingly '''

        try:

            # Store old name for reference
            old_name = self.title

            # Update our title and data
            self.title = new_name
            self.data['title'] = new_name

            # Update our widgets data to match
            self.widget.data[self.key][new_name] = self.widget.data[self.key].pop(old_name)

            tag = self.data.get('tag', '')
            match tag:
                case "plot_point":
                    self.widget.plot_points[new_name] = self.widget.plot_points.pop(old_name)
                case "marker":
                    self.widget.markers[new_name] = self.widget.markers.pop(old_name)
                case "arc":
                    self.widget.arcs[new_name] = self.widget.arcs.pop(old_name)
                case "comment":
                    self.widget.comments[new_name] = self.widget.comments.pop(old_name)
                case "location":
                    self.widget.locations[new_name] = self.widget.locations.pop(old_name)

                case _:
                    print("Invalid mw key")

            # Save the changes up the chain
            self.p.run_task(self.save_dict)

            # Reload the UI to reflect changes
            if hasattr(self, 'reload_plotline_control'):
                self.reload_plotline_control()

            if hasattr(self, 'reload_map_control') and hasattr(self, 'map_label'):
                self.map_label.text = new_name
                self.reload_map_control()
                
            if self.visible:
                self.reload_mini_widget()
            if hasattr(self.widget, 'information_display'):
                if self.widget.information_display.visible:
                    self.widget.information_display.reload_mini_widget() 
            self.widget.reload_widget()


            # Also reload the active rail to reflect changes
            self.widget.story.active_rail.content.reload_rail() 

        # Catch errors
        except Exception as e:
            print(f"Error renaming mini widget {old_name} to {new_name}: {e}")

    # Called to toggle pin
    async def _toggle_pin(self, e):
        ''' Pins or unpins our information display '''
            
        self.data['is_pinned'] = not self.data.get('is_pinned', False)
        await self.save_dict()
        e.control.icon = ft.Icons.PUSH_PIN_OUTLINED if not self.data.get('is_pinned', False) else ft.Icons.PUSH_PIN_ROUNDED
        e.control.tooltip = "Pin Connection" if not self.data.get('is_pinned', False) else "Unpin Connection"
        e.control.update()
        

    async def show_mini_widget(self, e=None):
        ''' Shows our mini widget '''

        #print("Show called for", self.title)

        if self.visible:
            return
        
        self.widget.story.blocker.visible = True
        self.widget.story.blocker.update()
        await asyncio.sleep(0)

        self.data['visible'] = True
        self.visible = True
        await self.save_dict()

        # If we show this mini widget, hide all other mini widgets that are not pinned
        for mw in self.widget.mini_widgets:
            if mw != self and mw.data.get('is_pinned', False) == False:
                await mw.hide_mini_widget() 

        self.update()
        self.widget.story.blocker.visible = False
        self.widget.story.blocker.update()


    async def hide_mini_widget(self, e=None):
        ''' Hides our mini widget '''

        #print("Hide called for", self.title)
        
        # Return early if we are already hidden or pin
        if not self.visible:
            return
        
        self.widget.story.blocker.visible = True
        self.widget.story.blocker.update()
        await asyncio.sleep(0)
        
        # Update our visibility
        self.data['visible'] = False
        self.visible = False
        self.data['is_pinned'] = False # Make sure to unpin us if we are pinned

        await self.save_dict()
        self.update()
        self.widget.story.blocker.visible = False
        self.widget.story.blocker.update()


    def _new_custom_field_clicked(self, e=None):
        ''' Called when the new field button is clicked '''

        if 'custom_fields' not in self.data:
            self.data['custom_fields'] = {} 

        def create_field(e): #show in edit view
            '''Called when user confirms the field name'''
            
            field_name = return_safe_name(field_name_input.value)
            
            if not field_name:
                self.p.pop_dialog()
                return  # Don't create if empty
            
            # Add the field to data if it doesn't exist
            if field_name not in self.data['custom_fields']:
                self.data['custom_fields'][field_name] = ""
            
            # Save and reload
            self.p.run_task(self.save_dict)
            self.p.pop_dialog()
            self.reload_mini_widget()       
            

        # Create a dialog to ask for the field name
        field_name_input = ft.TextField(
            label="Field Name", hint_text=f"New Custom Field Name",
            autofocus=True, capitalization=ft.TextCapitalization.SENTENCES,
            on_submit=create_field,     # Closes the overlay when submitting
        )
        
        dlg = ft.AlertDialog(
            title=ft.Text(f"Create New Custom Field"),
            content=field_name_input,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.p.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR)),
                ft.TextButton("Create", on_click=create_field),
            ],
        )
        
        
        dlg.open = True
        self.p.show_dialog(dlg)


    def _delete_custom_field_clicked(self, field_name: str):

        if field_name in self.data.get('custom_fields', {}):
            del self.data['custom_fields'][field_name]
            self.p.run_task(self.save_dict)
            self.reload_mini_widget()

    def _build_custom_fields_column(self) -> ft.Column:
        ''' Builds our column of custom fields for this mini widget '''
        controls = []
        for field_name, field_value in self.data.get('custom_fields', {}).items():
            controls.append(
                ft.Row([
                    ft.TextField(
                        value=field_value, expand=True, label=field_name, capitalization=ft.TextCapitalization.SENTENCES,   
                        on_blur=lambda e, fn=field_name: self.change_custom_field(**{fn: e.control.value})
                    ),
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, tooltip="Delete Custom Field",
                        on_click=lambda e, fn=field_name: self._delete_custom_field_clicked(fn)
                    ),
                
                ],)
            )
        return ft.Column(controls, spacing=8)


    def _get_menu_options(self) -> list[ft.Control]:

        # Color, rename
        return [
            MenuOptionStyle(
                on_click=self._rename_clicked,
                content=ft.Row([
                    ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, self.data.get('color', 'primary'),),
                    ft.Text(
                        "Rename", 
                        weight=ft.FontWeight.BOLD, 
                        
                    ), 
                ]),
            ),
            MenuOptionStyle(
                ft.SubmenuButton(
                    ft.Row([
                        ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.data.get('color', "primary")), 
                        ft.Text("Color", weight=ft.FontWeight.BOLD, expand=True),
                        ft.Icon(ft.Icons.ARROW_RIGHT),
                    ], expand=True),
                    self._get_color_options(), 
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    tooltip="Change this widget's color"
                ),
                no_padding=True, no_effects=True
            ),
            MenuOptionStyle(
                on_click=self._delete_clicked,
                content=ft.Row([
                    ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, ft.Colors.ERROR),
                    ft.Text("Delete", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True),
                ]),
            )
        ]
        
    def _rename_clicked(self, e):
        ''' Replaces our widget title with a text field to rename it '''

        # Track if our name is unique for checks, and if we're submitting or not
        is_unique = True
        submitting = False

        # Grab our current name for comparison
        current_name = self.title.lower()

        # Called when clicking outside the input field to cancel renaming
        def _cancel_rename(e):
            ''' Puts our name back to static and unalterable '''

            # Grab our submitting state
            nonlocal submitting

            # Since this auto calls on submit, we need to check. If it is cuz of a submit, do nothing
            if submitting:
                submitting = not submitting     # Change submit status to False so we can de-select the textbox
                return
            

        # Called everytime a change in textbox occurs
        def _name_check(e):
            ''' Checks if the name is unique within its type of widget '''


            # Nonlocal variables
            nonlocal is_unique, submitting

            # Set submitting to false, and unique to True
            submitting = False
            is_unique = True

            # Grab out title and tag from the textfield, and set our new key to compare
            title = e.control.value
            if title.lower() == current_name:
                return

            for mw in self.widget.mini_widgets:
                if mw != self and mw.data.get('key', '') == self.data.get('key', '') and mw.data.get('title', '').lower() == title.lower():
                    is_unique = False
                    error_text = "Name already exists"
                

            # If we are NOT unique, show our error text
            if not is_unique:
                text_field.error = error_text

            # Otherwise remove our error text
            else:
                text_field.error = None
                
            text_field.update()

        # Called when submitting our textfield.
        def _submit_name(e):
            ''' Checks that we're unique and renames the widget if so. on_blur is auto called after this, so we handle that as well '''

            # Non local variables
            nonlocal is_unique, text_field, submitting, current_name
            
            name = text_field.value
            if name == current_name:
                self.p.pop_dialog()
                return

            # Set submitting to True
            submitting = True

            # If it is, call the rename function. It will do everything else
            if is_unique:
                self.rename(name)
                self.p.pop_dialog()
                
            # Otherwise make sure we show our error
            else:
                text_field.error = "Name already exists"
                text_field.focus()                                  # Auto focus the textfield
                
        # Our text field that our functions use for renaming and referencing
        text_field = ft.TextField(
            value=self.title, 
            dense=True, capitalization=ft.TextCapitalization.WORDS,
            focus_color=self.data.get('color', ft.Colors.PRIMARY),
            border_color=self.data.get('color', ft.Colors.PRIMARY),
            autofocus=True,
            data=self.data.get('tag', ''),
            on_submit=_submit_name,
            on_change=_name_check,
            on_blur=_cancel_rename,
        )

        rename_button = ft.TextButton("Rename", on_click=_submit_name, style=ft.ButtonStyle(color=ft.Colors.PRIMARY, mouse_cursor="click"))

        dlg = ft.AlertDialog(
            title=ft.Text(f"Rename {self.title}", weight=ft.FontWeight.BOLD),
            content=text_field,
            actions=[
                ft.TextButton("Cancel", style=ft.ButtonStyle(ft.Colors.ERROR, mouse_cursor="click"), on_click=lambda e: self.p.pop_dialog()),
                rename_button   
            ]
        )

        # Clears our popup menu button and applies to the UI
        self.widget.story.close_menu_instant()
        self.p.show_dialog(dlg)

    # Called when color button is clicked
    def _get_color_options(self) -> list[ft.Control]:
        ''' Returns a list of all available colors for icon changing '''

        # Called when a color option is clicked on popup menu to change icon color
        def _change_icon_color(color: str):
            ''' Passes in our kwargs to the widget, and applies the updates '''

            self.change_data(**{'color': color})

            if hasattr(self, 'icon_button'):        # Locations and plotpoints have this
                self.icon_button.icon_color = color

            if hasattr(self, 'left_drag_handle') and hasattr(self, 'right_drag_handle'):     # Arcs have these
                self.left_drag_handle.content.color = color
                self.right_drag_handle.content.color = color

            if hasattr(self, 'reload_plotline_control'):
                self.reload_plotline_control()

            if hasattr(self, 'map_control'):
                self.reload_map_control()

            if hasattr(self, 'map_label'):
                self.map_label.color = color

            self.reload_mini_widget()
            #self.widget.reload_widget()
            # Change our icon to match, apply the update
            self.widget.story.active_rail.content.reload_rail()

            #await asyncio.sleep(0.3)
            self.widget.story.close_menu_instant()
            
            

        # List for our colors when formatted
        color_controls = [] 

        # Create our controls for our color options
        for color in colors:
            color_controls.append(
                ft.MenuItemButton(
                    content=ft.Text(color.capitalize(), weight=ft.FontWeight.BOLD, color=color),
                    on_click=lambda e, col=color: _change_icon_color(col), close_on_click=True,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click")
                )
            )

        return color_controls
    
    # Called when the delete button is clicked in the menu options
    def _delete_clicked(self, e=None):
        ''' Deletes this file from the story '''
        from models.app import app

        def _delete_confirmed(e=None):
            ''' Deletes the widget after confirmation '''
            self.p.pop_dialog()
            self.delete_dict()
            

        # Append an overlay to confirm the deletion
        dlg = ft.AlertDialog(
            title=ft.Text(f"Are you sure you want to delete {self.title} forever? This cannot be undone!", weight=ft.FontWeight.BOLD),
            alignment=ft.Alignment.CENTER,
            title_padding=ft.Padding.all(25),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.p.pop_dialog()),
                ft.TextButton("Delete", on_click=_delete_confirmed, style=ft.ButtonStyle(color=ft.Colors.ERROR)),
            ]
        )

        self.widget.story.close_menu_instant()

        if app.settings.data.get('confirm_item_delete', False):
            self.p.show_dialog(dlg)
        else:
            _delete_confirmed()

    def before_update(self):
        print(f"Successful update for mini widget {self.title}")
        return super().before_update()

    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_mini_widget(self, no_update: bool=False):
        ''' Reloads our mini widget UI based on our data '''

        # Add option to have the mini widget show on larger portion of screen, like an expand button at bottom left or right
        # Add edit button next to title to be in edit mode

        # Create body content
        self.content = ft.Column(
            [],
            expand=True,
        )

        try:
            if no_update:
                return
            else:
                self.update()
        except Exception as _:
            pass

    
        

        