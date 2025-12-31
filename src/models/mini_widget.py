'''
Parent class for mini widgets, which are extended flet containers used as information displays on the side of the parent widget
Makes showing detailed information easier without rending and entire widget where it doesn't make sense
Mini widgets either are exclusive (only they are shown), or shared (additional mini widgets can be shown at same time)
Mini widgets are stored in their OWNERS (Widget) json file, not their own file
Some mini widgets can have their own files IN ADDITION to normal storage, such as maps or drawings storing images
'''


import flet as ft
from models.widget import Widget
from handlers.verify_data import verify_data


class MiniWidget(ft.Container):

    # Constructor. All mini widgets require a title, owner widget, father (parent), page reference...
    # Dictionary path, and optional data dictionary
    def __init__(
        self, 
        title: str,                     # Title of the widget that will show up on its tab
        owner: Widget,                  # The widget that contains this mini widget.
        father,                         # Immidiate parent widget or mini widget that holds us (Since some mini widget)
        page: ft.Page,                  # Grabs our original page for convenience and consistency
        key: str,                       # Key to identify this mini widget (by title) within its fathers data
        side_location: str = None,      # Side of the widget the mini widget shows on
        data: dict = None               # Data passed in for this mini widget
    ):

        # Parent constructor
        super().__init__(
            expand=4,
            border_radius=ft.border_radius.all(10),
            border=ft.border.all(2, ft.Colors.SECONDARY_CONTAINER),
            padding=ft.padding.all(8),
            data=data,     
            bgcolor=ft.Colors.with_opacity(.7, ft.Colors.SURFACE),
            blur=5,
        )

        
        # Set our parameters
        self.title: str = title.capitalize()                        
        self.owner: Widget = owner                          
        self.father = father                        
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
                'side_location': side_location if side_location is not None else "right",     # Side of the widget the mini widget shows on
                'custom_fields': dict,        # Dictionary for any custom fields the mini widget wants to store
            },
        )

        # Apply our visibility
        self.visible = self.data['visible']
        

        # Control for our title
        self.title_control = ft.TextField(
            value=self.title,
            label=None,
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
        
            # If our data is None (we just got deleted), we don't save ourselves to fathers data
            if self.data is None:
                pass

            # Otherwise, save like normal
            else:

                # Our data is correct, so we update our immidiate parents data to match
                self.father.data[self.key][self.title] = self.data

            # Recursively updates the parents data until father=owner (widget), which saves to file
            self.father.save_dict()
            
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

            # Remove the data of our father (parent) widget/mini widget to match
            # By deleting the father data manually here, it will cascade up the chain when save_dict is called
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

            # Update our fathers data to match
            self.father.data[self.key][new_name] = self.father.data[self.key].pop(old_name)

            # Save the changes up the chain
            self.save_dict()

            # Reload the UI to reflect changes
            self.reload_mini_widget()

            # Also reload the active rail to reflect changes
            self.owner.story.active_rail.content.reload_rail() 

        # Catch errors
        except Exception as e:
            print(f"Error renaming mini widget {old_name} to {new_name}: {e}")
        

    # Called when clicking x to hide the mini widget
    def toggle_visibility(self, e=None, value: bool=None):
        ''' Shows or hides our mini widget, depending on current state '''

        # If we passed in a value, use it
        if value is not None:

            self.data['visible'] = value
            self.visible = value

        # Otherwise, toggle our current state
        else:
            self.data['visible'] = not self.data['visible']
            self.visible = self.data['visible']


        # If we are now visible, hide all other mini widgets
        if self.visible:
            
            for mini_widget in self.owner.mini_widgets:
                
                if mini_widget.visible and mini_widget != self:
                    mini_widget.toggle_visibility(value=False)
                    break

        print(f"Mini widget {self.title} visibility set to {self.visible}")
        # Save switch to file
        self.save_dict()

        #self.update()
        self.p.update()
        

    # Called whenever we hover over our mini widget on the right as a psuedo focus
    def on_hover(self, e: ft.HoverEvent):
        print(e)
        

    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_mini_widget(self):
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

        # Call render function
        self._render_mini_widget()

    def _render_mini_widget(self, no_update: bool=False):
        ''' Renders our mini widget UI based on our data '''

        # Give Uniform mini titles and styling

        if no_update:
            return
        
        else:

            self.p.update()
        

        