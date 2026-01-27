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
            #padding=ft.padding.all(8),
            padding=ft.padding.only(left=8, top=8, bottom=8),
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
        self.visible = self.data['visible']
        

        # Control for our title
        self.title_control = ft.TextField(
            value=self.title,
            label=None, expand=True,
        )

        # Control for our content/body
        self.content_control = ft.TextField(
            label="Body",
            expand=True,
            multiline=True,
        )

    # Called when saving changes in our mini widgets data to the OWNERS json file
    def save_dict(self):
        ''' Saves our current data to the OWNERS json file using this objects dictionary path '''

        try:
        
            # If our data is None (we just got deleted), we don't save ourselves to owners data
            if self.data is None:
                pass

            # Otherwise, save like normal
            else:

                # Our data is correct, so we update our immidiate parents data to match
                self.owner.data[self.key][self.title] = self.data

            # Recursively updates the parents data until owner=owner (widget), which saves to file
            self.owner.save_dict()
            
            # This keeps everyones data in sync so we can infinitely nest mini widgets if we want, like for arcs in timelines

        except Exception as e:
            print(f"Error saving mini widget data to {self.title}: {e}")
            

    # Called when deleting our mini widget
    def delete_dict(self):
        ''' Deletes our data from all live widget/mini widget objects that we nest in, and saves the owners file '''

        try:
            print("Called mini widget delete dict")

            # Applies the UI changes by removing ourselves from the mini widgets list
            if self in self.owner.mini_widgets:
                self.owner.mini_widgets.remove(self)

            # Remove our data
            self.data = None

            # Remove the data of our owner (parent) widget/mini widget to match
            # By deleting the owner data manually here, it will cascade up the chain when save_dict is called
            self.owner.data[self.key].pop(self.title, None)
            
            
            # Applies the changes up the chain
            self.owner.save_dict()

            # Reload the widget if we have to
            self.owner.reload_widget()

            # Also reload the active rail to reflect changes
            self.owner.story.active_rail.content.reload_rail() 

            self.data = None

            print("Passed all checks")

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
            self.title = new_name.capitalize()
            self.data['title'] = new_name

            # Update our owners data to match
            self.owner.data[self.key][new_name] = self.owner.data[self.key].pop(old_name)

            # Save the changes up the chain
            self.save_dict()

            # Reload the UI to reflect changes
            self.reload_mini_widget()

            # Also reload the active rail to reflect changes
            self.owner.story.active_rail.content.reload_rail() 

        # Catch errors
        except Exception as e:
            print(f"Error renaming mini widget {old_name} to {new_name}: {e}")
        

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

        self.reload_mini_widget(no_update=True)
        self.owner.reload_widget()

    def hide_mini_widget(self, e=None, update: bool=False):
        ''' Hides our mini widget '''
        print("Hiding mini widget:", self.title)
        
        if not self.visible:
            return
        
        self.data['visible'] = False
        self.visible = False

        if self.data.get('is_pinned', False):
            self.data['is_pinned'] = False

        self.save_dict()

        if update:
            self.reload_mini_widget()
            self.owner.reload_widget()
        

    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_mini_widget(self, no_update: bool=False):
        ''' Reloads our mini widget UI based on our data '''

        # Add option to have the mini widget show on larger portion of screen, like an expand button at bottom left or right
        # Add edit button next to title to be in edit mode

        # Create body content
        self.content = ft.Column(
            [
                self.title_control,
                self.content_control,
            ],
            expand=True,
        )

        if no_update:
            return
        else:
            self.p.update()
            self.update()
            

    
        

        