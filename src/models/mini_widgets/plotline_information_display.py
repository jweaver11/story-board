import flet as ft
from models.mini_widget import MiniWidget
from models.widgets.plotline import Plotline
import asyncio
from models.dataclasses.events import Event
from utils.verify_data import verify_data


# Display that makes Plotlines share much uniformaty in their information display like arcs do
class PlotlineInformationDisplay(MiniWidget):

    # Constructor. Requires title, owner widget, page reference, and optional data dictionary
    def __init__(self, title: str, owner: Plotline,  page: ft.Page, key: str, data: dict=None):

        # Parent constructor
        super().__init__(
            title=title,        
            owner=owner,                    
            page=page,          
            key=key,  # Not used, but its required so just whatever works
            data=data,      # No data is used here, so NEVER reference it. Use self.owner.data instead
        ) 
        
        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   # Pass in our object so we can access its data and change it
            {   
                'title': self.title,          # Title of the mini widget, should match the object title
                'tag': "plotline_information_display",         # Default mini widget tag, but should be overwritten by child classes

                # Plotline data
                'Summary': str,
                'Time Label': "Years",                          # Label for the time axis (any str they want)
                'Left Label': "0",                              # Start label
                'Right Label': "10",                            # Start and end date of the branch, for plotline view
                'Divisions': ["1", "2", "3", "4", "5", "6", "7", "8", "9"],    # List len is the num of divisions, and each value is its label
            },
        )

        # Holds our row controls for our divisions so we can add/remove without rebuilding
        self.divisions_column = ft.Column(spacing=0, scroll="auto")

        self.reload_mini_widget()

    

    # Called when saving changes to our Plotline object
    def save_dict(self):
        ''' Overwrites standard mini widget save and save our Plotlines data instead '''
        try:
            self.owner.save_dict()
        except Exception as e:
            print(f"Error saving Plotline information display data to {self.owner.title}: {e}")

    

    # Called when changing our owners data from some event
    async def _change_our_data(self, e):
        ''' Sorts what data to change and how, and if we need to rebuild or just update the page '''

        if isinstance(e.control.data, list):
            key = e.control.data[0]
            idx = e.control.data[1]
            delete_idx = e.control.data[2] if len(e.control.data) > 2 else False

            # If we're deleting from a list, we'll need a reload
            if delete_idx:
                self.data.get(key, []).pop(idx)
                self.save_dict()

                # Rebuild our canvas
                await self.owner.rebuild_plotline_canvas(no_update=True)

                # Remove the control for this division. Reloading would fix, but lose our scroll placement
                for control in self.divisions_column.controls:
                    if isinstance(control, ft.Row):
                        text_control = control.controls[0]
                        if text_control.data[1] == idx:
                            self.divisions_column.controls.remove(control)
                            break

                # Update the controls indexes after the deleted one. 
                for control in self.divisions_column.controls:
                    if isinstance(control, ft.Row):
                        text_control = control.controls[0]      # Update both text and delete button indexes
                        delete_button = control.controls[1]
                        if text_control.data[0] == 'Divisions' and text_control.data[1] >= idx:
                            text_control.data[1] -= 1
                            delete_button.data[1] -= 1

                self.p.update()

            else:
                self.data.get(key, [])[idx] = e.control.value
                self.save_dict()
                await self.rebuild_plotline_canvas(no_update=True)
                
        else:
            key = e.control.data
            value = e.control.value
            self._change_our_data_instant(key, value)
            await self.owner.rebuild_plotline_canvas(no_update=True)

    
    def _change_our_data_instant(self, key, value):
        ''' Changes our owners data instantly '''
        self.data[key] = value
        self.owner.save_dict()
        

    # Called when reloading our mini widget UI
    def reload_mini_widget(self, no_update: bool=False):

        async def _new_divisions_clicked(e=None):
            ''' Called to add a new division to the bottom of the divisions list '''
            text_control = ft.TextField(
                expand=True, value=len(self.data.get('Divisions', [])) + 1, dense=True, 
                capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                on_blur=self._change_our_data,
                data=['Divisions', len(self.data.get('Divisions', [])), False],
                focus_color=self.owner.data.get('color', None),
                cursor_color=self.owner.data.get('color', None),
                focused_border_color=self.owner.data.get('color', None),
            )

            self.divisions_column.controls.append(
                ft.Row([
                    text_control,
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR,
                        tooltip="Delete Division", 
                        on_click=self._change_our_data,
                        data=['Divisions', len(self.data.get('Divisions', [])), True],
                    ),
                ])
            )

            current_divisions = self.data.get('Divisions', [])
            current_divisions.append(str(len(current_divisions) + 1))

            self.data['Divisions'] = current_divisions
            self.save_dict()
            self.p.update()

            
        title_control = ft.Row([
            ft.Icon(ft.Icons.TIMELINE, self.owner.data.get('color', None)),
            
            ft.GestureDetector(
                ft.Text(f"\t\t{self.data['title']}\t\t", weight=ft.FontWeight.BOLD, tooltip=f"Rename {self.title}"),
                on_double_tap=self.owner._rename_clicked,
                on_tap=self.owner._rename_clicked,
                on_secondary_tap=lambda e: self.owner.story.open_menu(self.owner._get_menu_options()),
                mouse_cursor="click", on_hover=self.owner._hover_tab, hover_interval=500
            ),
            ft.IconButton(
                ft.Icons.PUSH_PIN_OUTLINED if not self.data.get('is_pinned', False) else ft.Icons.PUSH_PIN_ROUNDED,
                self.owner.data.get('color', None),
                tooltip="Pin Information Display" if not self.data.get('is_pinned', False) else "Unpin Information Display",
                on_click=self._toggle_pin
            ),
            ft.Container(expand=True),
            ft.IconButton(
                ft.Icons.CLOSE, ft.Colors.ON_SURFACE_VARIANT,
                tooltip=f"Close {self.title}",
                on_click=lambda e: self.hide_mini_widget(update=True),
            ),
        ])
        

        content = ft.Column(expand=True, tight=True, scroll="auto", alignment=ft.MainAxisAlignment.START, controls=[ft.Container(height=1)])  # Start with some spacing at the top



        # Summary
        content.controls.append(
            ft.TextField(
                expand=True, label="Summary", value=self.data.get('Summary', ""), dense=True, multiline=True,
                capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                on_blur=self._change_our_data,
                data='Summary', 
                focus_color=self.owner.data.get('color', None),
                cursor_color=self.owner.data.get('color', None),
                focused_border_color=self.owner.data.get('color', None),
                label_style=ft.TextStyle(color=self.owner.data.get('color', None)),
            )
        )

        
        # Our labels
        content.controls.append(
            ft.Row([
                ft.TextField(
                    expand=True, label="Left Label", value=self.data.get('Left Label', ""), dense=True, 
                    capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                    on_blur=self._change_our_data,
                    data='Left Label',
                    focus_color=self.owner.data.get('color', None),
                    cursor_color=self.owner.data.get('color', None),
                    focused_border_color=self.owner.data.get('color', None),
                    label_style=ft.TextStyle(color=self.owner.data.get('color', None)),
                ),
                ft.TextField(
                    expand=True, label="Right Label", value=self.data.get('Right Label', ""), dense=True, 
                    capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                    on_blur=self._change_our_data,
                    data='Right Label',
                    focus_color=self.owner.data.get('color', None),
                    cursor_color=self.owner.data.get('color', None),
                    focused_border_color=self.owner.data.get('color', None),
                    label_style=ft.TextStyle(color=self.owner.data.get('color', None)),
                )
            ])
        )

        content.controls.append(
            ft.TextField(
                expand=True, label="Time Label", value=self.data.get('Time Label', ""), dense=True,
                capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                on_blur=self._change_our_data,
                data='Time Label',
                focus_color=self.owner.data.get('color', None),
                cursor_color=self.owner.data.get('color', None),
                focused_border_color=self.owner.data.get('color', None),
                label_style=ft.TextStyle(color=self.owner.data.get('color', None)),
            )
        )

        


        # Go through and list all our events in order. We'll sort them by their left positions
        events_list = []

        for pp in self.owner.plot_points.values():
            events_list.append(Event(tag='plot_point', left=pp.data.get('left', 0), title=pp.title, color=pp.data.get('color', 'secondary')))

        # Arcs have a right position, so we calc how far that is from left, and add a new event there as well
        for arc in self.owner.arcs.values():
            events_list.append(Event(tag='arc_start', left=arc.data.get('left', 0), title=arc.title, color=arc.data.get('color', 'secondary')))
            arc_width = arc.data.get('width', 0)
            arc_end: int = arc.data.get('left', 0) + arc_width  
            events_list.append(Event(tag='arc_end', left=arc_end, title=arc.title, color=arc.data.get('color', 'secondary')))

        for marker in self.owner.markers.values():
            events_list.append(Event(tag='marker', left=marker.data.get('left', 0), title=marker.title, color=marker.data.get('color', 'secondary')))

        # Sort that list
        events_list = sorted(events_list, key=lambda e: e.left)

        # Hold our text spans for the events
        events_spans = []

        # Go through our events and make spans for them so we can see
        for idx, event in enumerate(events_list):

            if event.tag == 'arc_start':
                events_spans.append(ft.TextSpan(f"{event.title} Begins\t\t➜\t\t", style=ft.TextStyle(color=event.color, word_spacing=4)))
            elif event.tag == 'arc_end':
                events_spans.append(ft.TextSpan(f"{event.title} Ends\t\t➜\t\t", style=ft.TextStyle(color=event.color, word_spacing=4)))
            elif event.tag == 'marker':
                events_spans.append(ft.TextSpan(
                    f"\n{event.title}\n", 
                    style=ft.TextStyle(color=event.color, weight=ft.FontWeight.BOLD, word_spacing=4)
                ))
            else:
                events_spans.append(ft.TextSpan(f"{event.title}\t\t➜\t\t", style=ft.TextStyle(color=event.color, word_spacing=3)))

        # Clean up spans a bit.
        for idx, span in enumerate(events_spans):
            # Remove newline if marker is first event
            if idx == 0:
                if span.text.startswith("\n"):
                    events_spans[idx] = ft.TextSpan(span.text[1:], style=span.style)

            # Remove all the new lines between markers that have no events between them
            previous_span = events_spans[idx - 1] if idx > 0 else None
            if previous_span:
                if previous_span.text.endswith("\n") and span.text.startswith("\n"):
                    events_spans[idx - 1] = ft.TextSpan(previous_span.text[:-1], style=previous_span.style)

            # Remove arrow from the end of the last event
            if idx == len(events_spans) - 1:
                if span.text.endswith("\t\t➜\t\t"):
                    events_spans[idx] = ft.TextSpan(span.text[:-6], style=span.style)
                    

        # Make our text control with our built spans
        events_text = ft.Text(spans=events_spans, selectable=True, expand=True)

        # Container to hold the text control for events
        events_container = ft.Container(               
            padding=ft.padding.all(6), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT), 
            content=events_text,
        )

        # Add the label and the events container
        content.controls.append(
            ft.Row([
                ft.Container(width=6), 
                ft.Text("Events", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=14), color=self.owner.data.get('color', None), tooltip="The order of events that occur in this plotline"),
                
            ], spacing=0)
        )

        content.controls.append(ft.Row([events_container]))

        

        # Add the label and the Divisions container
        content.controls.append(
            ft.Row([
                ft.Container(width=6), 
                ft.Text("Divisions", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=14), color=self.owner.data.get('color', None), tooltip="The number and label of the divisions on this plotline."),
                ft.Container(width=10),
                ft.IconButton(
                    ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                    tooltip="Add Division", on_click=_new_divisions_clicked
                )
            ], spacing=0)
        )

        # Container for our divisions list
        divisions_container = ft.Container(               
            padding=ft.padding.all(6), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT), 
            content=self.divisions_column,
        )
        
        # Add all our current divisions
        for idx, division in enumerate(self.data.get('Divisions', [])):
            # Create text control for this division
            text_control = ft.TextField(
                expand=True,  value=division, dense=True, 
                capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                on_blur=self._change_our_data,
                data=['Divisions', idx, False],
                focus_color=self.owner.data.get('color', None),
                cursor_color=self.owner.data.get('color', None),
                focused_border_color=self.owner.data.get('color', None),
            )

            # Add to a row with delete button to remove divisions
            divisions_container.content.controls.append(
                ft.Row([
                    text_control,
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR,
                        tooltip="Delete Division", 
                        on_click=self._change_our_data,
                        data=['Divisions', idx, True],
                    ),
                ])
            )

        content.controls.append(divisions_container.content)

        column = ft.Column([
            title_control,
            ft.Divider(height=2, thickness=2),
            content
        ], expand=True, scroll="none", tight=True, alignment=ft.MainAxisAlignment.START)
        
        self.content = column

        if no_update:
            return
        else:
            self.p.update()
