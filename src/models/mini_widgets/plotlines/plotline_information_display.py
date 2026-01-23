import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
from models.widgets.plotline import Plotline


# Display that makes Plotlines share much uniformaty in their information display like arcs do
class PlotlineInformationDisplay(MiniWidget):

    # Constructor. Requires title, owner widget, page reference, and optional data dictionary
    def __init__(self, title: str, owner: Widget, father: Plotline, page: ft.Page, key: str, data: dict=None):

        # Parent constructor
        super().__init__(
            title=title,        
            owner=owner,                    
            father=father,                  # In this case, father is always the Plotline or arc we belong to
            page=page,          
            key=key,  # Not used, but its required so just whatever works
            data=None,      # No data is used here, so NEVER reference it. Use self.owner.data instead
        ) 
        
        # Since we only reference out owners data and not our own, we don't need to verify it here

        # Set our visibility based on our owners data
        self.visible = self.owner.data.get('information_display_visibility', True)

        self.reload_mini_widget()

    

    # Called when saving changes to our Plotline object
    def save_dict(self):
        ''' Overwrites standard mini widget save and save our Plotlines data instead '''
        try:
            self.owner.save_dict()
        except Exception as e:
            print(f"Error saving Plotline information display data to {self.owner.title}: {e}")

    # Called to toggle our visibility
    def toggle_visibility(self, e=None, value: bool=None):
        ''' Toggles our visibility and updates our owners data accordingly '''

        # Update our visibility
        self.owner.data['information_display_visibility'] = not self.visible if value is None else value
        self.visible = self.owner.data.get('information_display_visibility', True)

        # IF we hit that we are visible, and not special exclusive, hide all other exclusive mini widgets on the same side
        if self.visible:
            for mini_widget in self.owner.mini_widgets:
                if mini_widget.visible and mini_widget != self and mini_widget.data.get('side_location', 'right') == self.data.get('side_location', 'right'):
                    mini_widget.toggle_visibility(value=False)

        self.save_dict()
        self.reload_mini_widget()
        self.owner.reload_widget()

    # Called when clicking the edit mode button
    def _edit_mode_clicked(self, e=None):
        ''' Switches between edit mode and not for the character '''

        # Change our edit mode data flag, and save it to file
        self.owner.data['edit_mode'] = not self.owner.data['edit_mode']
        self.save_dict()

        # Reload the widget. The reload widget should load differently depending on if we're in edit mode or not
        self.reload_mini_widget()
        self.owner._render_widget()
    
    # Called if our widget is in edit view. 
    def _edit_mode_view(self):
        ''' Returns our character data with input capabilities '''

        def _get_help_text(key: str="") -> str:
            ''' Returns help text for certain fields '''
            match key:
                
                
                
                case _:
                    return None


        def _load_dict_data(dict: dict, container: ft.Container, sub_key: str=""):
            ''' Loads data from a dict into a given container '''
            for key, value in dict.items():
                if isinstance(value, str):
                    text_control = ft.TextField(
                        expand=True, value=value, dense=True, multiline=True, hint_text=_get_help_text(key),
                        capitalization=ft.TextCapitalization.SENTENCES, adaptive=True, label=key.capitalize(),
                        on_blur=lambda e, k=key: self._update_world_data(key=sub_key, **{k: e.control.value})
                    )

                    container.content.controls.append(
                        ft.Row([
                            text_control,
                            ft.IconButton(
                                tooltip="Delete Field", icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.ERROR,   
                                on_click=lambda e, k=key: self._delete_world_data(sub_key=sub_key, **{k: None})
                            ),
                        ])
                    )

        self.title_control = ft.Row([
            ft.Icon(ft.Icons.TIMELINE_ROUNDED, self.owner.data.get('color', None)),
            ft.Text(self.data['title'], weight=ft.FontWeight.BOLD, selectable=True, overflow=ft.TextOverflow.FADE),
            ft.IconButton(tooltip="Edit Mode", icon=ft.Icons.EDIT_OFF_OUTLINED, icon_color=self.owner.data.get('color', None), on_click=self._edit_mode_clicked),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.CLOSE,
                tooltip=f"Close {self.title}",
                on_click=lambda e: self.toggle_visibility(value=False),
            ),
        ])

        content = ft.Column([
            self.title_control,
            ft.Divider(height=2, thickness=2),
            ft.Container(expand=True, height=10),
        ], expand=True, tight=True, spacing=0, scroll="auto")

        content.controls.append(
            ft.Row([
                ft.Container(width=6), 
                ft.Text("Summary", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True),
            ], spacing=0),
            
        )
        self.content = content
        

    # Called when reloading our mini widget UI
    def reload_mini_widget(self):

        if self.owner.data.get('edit_mode', False):
            self._edit_mode_view()
            self._render_mini_widget()
            return

        self.title_control = ft.Row([
            ft.Icon(ft.Icons.TIMELINE_ROUNDED, self.owner.data.get('color', None)),
            ft.Text(self.data['title'], weight=ft.FontWeight.BOLD, selectable=True, overflow=ft.TextOverflow.FADE),
            ft.IconButton(tooltip="Edit Mode", icon=ft.Icons.EDIT_OUTLINED, icon_color=self.owner.data.get('color', None), on_click=self._edit_mode_clicked),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.CLOSE,
                tooltip=f"Close {self.title}",
                on_click=lambda e: self.toggle_visibility(value=False),
            ),
        ])
        

        content = ft.Column([
            self.title_control,
            ft.Divider(height=2, thickness=2),
            ft.Container(expand=True, height=10),
        ], expand=True, tight=True, spacing=0, scroll="auto")

        summary_container = ft.Container(            # For basic info
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE), 
            content=ft.TextField(
                expand=True, value=self.owner.data.get('summary', ""), dense=True, multiline=True,
                capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                on_blur=lambda e: self.owner.change_data(**{'summary': e.control.value}),
                border=ft.InputBorder.NONE,                  
            ),
        )

        content.controls.append(
            ft.Row([
                ft.Container(width=6), 
                ft.Text("Summary", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True),
            ], spacing=0),
            
        )

        content.controls.append(ft.Row([summary_container]))

        



        # TODO: Add 'Events', which shows in order of plot points, arcs, and markers on the plotline

        # SUmmary
        # Events
        # Plot points
        # arcs
        # Markers
        # LEft and right edge label, time label, divisions

        

        self.content = content

        #self.p.update()