'''
Parent class for mini widgets, which are extended flet containers used as information displays on the side of the parent widget
Makes showing detailed information easier without rending and entire widget where it doesn't make sense
Mini widgets either are exclusive (only they are shown), or shared (additional mini widgets can be shown at same time)
Mini widgets are stored in their OWNERS (Widget) json file, not their own file
Some mini widgets can have their own files IN ADDITION to normal storage, such as maps or drawings storing images
'''


import flet as ft
from models.widget import Widget
from utils.verify_data import verify_data
from styles.menu_option_style import MenuOptionStyle
from styles.colors import colors
import asyncio

class MiniWidget(ft.Container):

    # Constructor. All mini widgets require a title, owner widget, page reference...
    # Dictionary path, and optional data dictionary
    def __init__(
        self, 
        title: str,                     # Title of the widget that will show up on its tab
        owner: Widget,                  # The widget that contains this mini widget.
        page: ft.Page,                  # Grabs our original page for convenience and consistency
        key: str,                       # Key to identify this mini widget (by title) within its owners data
        side_location: str = None,      # Side of the widget the mini widget shows on
        data: dict = None               # Data passed in for this mini widget
    ):

        # Parent constructor
        super().__init__(
            expand=True,
            border_radius=ft.border_radius.all(10),
            border=ft.border.all(2, ft.Colors.SECONDARY_CONTAINER),
            padding=ft.padding.all(8),
            data=data,     
            bgcolor=ft.Colors.with_opacity(.7, ft.Colors.SURFACE),
            blur=5,
        )

        
        # Set our parameters
        self.title: str = title                      
        self.owner: Widget = owner                          
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

        # Apply our visibility
        self.visible = self.data.get('visible', True)
        

    # Called when saving changes in our mini widgets data to the OWNERS json file
    def save_dict(self):
        ''' Saves our current data to the OWNERS json file using this objects dictionary path '''

        try:
        
            # If our data is None (we just got deleted), we don't save ourselves to owners data
            if self.data is None:
                self.owner.data[self.key].pop(self.title, None)

            # Otherwise, save like normal
            else:

                # Our data is correct, so we update our immidiate parents data to match
                self.owner.data[self.key][self.title] = self.data

            # Recursively updates the parents data until owner=owner (widget), which saves to file
            self.owner.save_dict()

        except Exception as e:
            print(f"Error saving mini widget data to {self.title}: {e}")
            

    # Called when deleting our mini widget
    def delete_dict(self):
        ''' Deletes our data from all live widget/mini widget objects that we nest in, and saves the owners file '''

        try:

            # Applies the UI changes by removing ourselves from the mini widgets list
            if self in self.owner.mini_widgets:
                self.owner.mini_widgets.remove(self)

            tag = self.data.get('tag', '')  

            match tag:
                case "plot_point":
                    del self.owner.plot_points[self.title]
                case "marker":
                    del self.owner.markers[self.title]
                case "arc":
                    del self.owner.arcs[self.title]
                case "comment":
                    del self.owner.comments[self.title]

                case _:
                    print("Invalid mw key")
                

            # Remove our data.
            self.data = None
            self.save_dict()

            # Reload the widget if we have to
            self.owner.reload_widget()

            # Also reload the active rail to reflect changes
            self.owner.story.active_rail.content.reload_rail() 
            self.owner.story.close_menu_instant()

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

            self.save_dict()

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

            self.save_dict()

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

            # Update our owners data to match
            self.owner.data[self.key][new_name] = self.owner.data[self.key].pop(old_name)

            tag = self.data.get('tag', '')
            match tag:
                case "plot_point":
                    self.owner.plot_points[new_name] = self.owner.plot_points.pop(old_name)
                case "marker":
                    self.owner.markers[new_name] = self.owner.markers.pop(old_name)
                case "arc":
                    self.owner.arcs[new_name] = self.owner.arcs.pop(old_name)
                case "comment":
                    self.owner.comments[new_name] = self.owner.comments.pop(old_name)

                case _:
                    print("Invalid mw key")

            # Save the changes up the chain
            self.save_dict()

            # Reload the UI to reflect changes
            if hasattr(self, 'reload_plotline_control'):
                self.reload_plotline_control()
                
            if self.visible:
                self.reload_mini_widget()
            if hasattr(self.owner, 'information_display'):
                if self.owner.information_display.visible:
                    self.owner.information_display.reload_mini_widget() 
            self.owner.reload_widget()


            # Also reload the active rail to reflect changes
            self.owner.story.active_rail.content.reload_rail() 

        # Catch errors
        except Exception as e:
            print(f"Error renaming mini widget {old_name} to {new_name}: {e}")

    # Called to toggle pin
    async def _toggle_pin(self, e):
        ''' Pins or unpins our information display '''
            
        self.data['is_pinned'] = not self.data.get('is_pinned', False)
        self.save_dict()
        e.control.icon = ft.Icons.PUSH_PIN_OUTLINED if not self.data.get('is_pinned', False) else ft.Icons.PUSH_PIN_ROUNDED
        e.control.tooltip = "Pin Connection" if not self.data.get('is_pinned', False) else "Unpin Connection"
        self.p.update()
        

    def show_mini_widget(self, e=None):
        ''' Shows our mini widget '''

        if self.visible:
            return

        self.data['visible'] = True
        self.visible = True
        self.save_dict()

        for mw in self.owner.mini_widgets:
            if mw != self and mw.data.get('is_pinned', False) == False:
                mw.hide_mini_widget() 
            #else:
                #print(f"Not hiding pinned mini widget {mw.title} becuase its pinned or just clicked to show itself")

        self.reload_mini_widget(no_update=True)
        self.owner._render_widget()

    def hide_mini_widget(self, e=None, update: bool=False):
        ''' Hides our mini widget '''
        
        # Return early if we are already hidden or pin
        if not self.visible:
            return
        
        # Update our visibility
        self.data['visible'] = False
        self.visible = False

        if self.data.get('is_pinned', False):   # If we are pinned, unpin ourselves when hiding
            self.data['is_pinned'] = False

        self.save_dict()



        if update:

            self.reload_mini_widget()
            self.owner._render_widget()


    def _get_menu_options(self) -> list[ft.Control]:

        # Color, rename
        return [
            MenuOptionStyle(
                on_click=self._rename_clicked,
                content=ft.Row([
                    ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED),
                    ft.Text(
                        "Rename", 
                        weight=ft.FontWeight.BOLD, 
                        color=ft.Colors.ON_SURFACE
                    ), 
                ]),
            ),
            MenuOptionStyle(
                content=ft.PopupMenuButton(
                    expand=True, tooltip="Change this item's color",
                    padding=ft.Padding(0,0,0,0),
                    content=ft.Container(
                        ft.Row([ft.Icon(ft.Icons.COLOR_LENS_OUTLINED), ft.Text("Color", weight=ft.FontWeight.BOLD)]),
                        padding=ft.padding.all(8), border_radius=ft.border_radius.all(6),
                    ),
                    items=self._get_color_options()
                ),
                no_padding=True
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

            for mw in self.owner.mini_widgets:
                if mw != self and mw.data.get('key', '') == self.data.get('key', '') and mw.data.get('title', '').lower() == title.lower():
                    is_unique = False
                    error_text = "Name already exists"
                

            # If we are NOT unique, show our error text
            if not is_unique:
                text_field.error_text = error_text

            # Otherwise remove our error text
            else:
                text_field.error_text = None
                
            self.p.update()

        # Called when submitting our textfield.
        def _submit_name(e):
            ''' Checks that we're unique and renames the widget if so. on_blur is auto called after this, so we handle that as well '''

            # Non local variables
            nonlocal is_unique, text_field, submitting, current_name
            
            name = text_field.value
            if name == current_name:
                self.p.close(dlg)
                return

            # Set submitting to True
            submitting = True

            # If it is, call the rename function. It will do everything else
            if is_unique:
                self.rename(name)
                self.p.close(dlg)
                
            # Otherwise make sure we show our error
            else:
                text_field.error_text = "Name already exists"
                text_field.focus()                                  # Auto focus the textfield
                
        # Our text field that our functions use for renaming and referencing
        text_field = ft.TextField(
            value=self.title, 
            dense=True, capitalization=ft.TextCapitalization.WORDS,
            focus_color=self.data.get('color', ft.Colors.PRIMARY),
            border_color=self.data.get('color', ft.Colors.PRIMARY),
            autofocus=True,
            data=self.data.get('tag', ''),
            text_style=ft.TextStyle(
                color=ft.Colors.ON_SURFACE,
                weight=ft.FontWeight.BOLD,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
            on_submit=_submit_name,
            on_change=_name_check,
            on_blur=_cancel_rename,
        )

        rename_button = ft.TextButton("Rename", on_click=_submit_name, style=ft.ButtonStyle(color=ft.Colors.PRIMARY))

        dlg = ft.AlertDialog(
            title=ft.Text(f"Rename {self.title}", weight=ft.FontWeight.BOLD),
            content=text_field,
            actions=[
                ft.TextButton("Cancel", style=ft.ButtonStyle(ft.Colors.ERROR), on_click=lambda e: self.p.close(dlg)),
                rename_button   
            ]
        )

        # Clears our popup menu button and applies to the UI
        self.p.overlay.clear()
        self.p.open(dlg)

    # Called when color button is clicked
    def _get_color_options(self) -> list[ft.Control]:
        ''' Returns a list of all available colors for icon changing '''

        # Called when a color option is clicked on popup menu to change icon color
        async def _change_icon_color(color: str):
            ''' Passes in our kwargs to the widget, and applies the updates '''

            self.change_data(**{'color': color})

            if hasattr(self, 'icon_button'):        # Locations and plotpoints have this
                self.icon_button.icon_color = color

            if hasattr(self, 'left_drag_handle') and hasattr(self, 'right_drag_handle'):     # Arcs have these
                self.left_drag_handle.content.color = color
                self.right_drag_handle.content.color = color

            if hasattr(self, 'reload_plotline_control'):
                self.reload_plotline_control()

            
            
            self.reload_mini_widget()
            self.owner.reload_widget()
            # Change our icon to match, apply the update
            self.owner.story.active_rail.content.reload_rail()

            await asyncio.sleep(0.3)
            await self.owner.story.close_menu()
            
            

        # List for our colors when formatted
        color_controls = [] 

        # Create our controls for our color options
        for color in colors:
            color_controls.append(
                ft.PopupMenuItem(
                    content=ft.Text(color.capitalize(), weight=ft.FontWeight.BOLD, color=color),
                    on_click=lambda e, col=color: self.p.run_task(_change_icon_color, col)
                )
            )

        return color_controls
    
    # Called when the delete button is clicked in the menu options
    def _delete_clicked(self, e=None):
        ''' Deletes this file from the story '''
        from models.app import app

        def _delete_confirmed(e=None):
            ''' Deletes the widget after confirmation '''
            self.p.close(dlg)
            self.delete_dict()
            

        # Append an overlay to confirm the deletion
        dlg = ft.AlertDialog(
            title=ft.Text(f"Are you sure you want to delete {self.title} forever? This cannot be undone!", weight=ft.FontWeight.BOLD),
            alignment=ft.alignment.center,
            title_padding=ft.padding.all(25),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.p.close(dlg)),
                ft.TextButton("Delete", on_click=_delete_confirmed, style=ft.ButtonStyle(color=ft.Colors.ERROR)),
            ]
        )

        self.owner.story.close_menu_instant()

        if app.settings.data.get('confirm_item_delete', False):
            self.p.open(dlg)
        else:
            _delete_confirmed()

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

        if no_update:
            return
        else:
            self.p.update()
            

    
        

        