import flet as ft
from models.mini_widget import MiniWidget
from models.widgets.plotline import Plotline
import asyncio
from models.dataclasses.events import Event
from utils.verify_data import verify_data


# Display that makes Plotlines share much uniformaty in their information display like arcs do
class PlotlineInformationDisplay(MiniWidget):

    # Constructor. Requires title, widget widget, page reference, and optional data dictionary
    def __init__(self, title: str, widget: Plotline,  page: ft.Page, key: str, data: dict=None):

        # Check if we're new and need to create file
        is_new = False
        if data is None:
            is_new = True

        # Parent constructor
        super().__init__(
            title=title,        
            widget=widget,                    
            page=page,          
            key=key,  
            data=data,      
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
        self.divisions_column = ft.Column(spacing=0, scroll="none")

        if is_new:
            self.p.run_task(self.save_dict)

        # Reloads the information display of the canvas
        self.reload_mini_widget()

    # Called when saving changes in our mini widgets data to the widgetS json file
    async def save_dict(self):
        ''' Saves our current data to the widgetS json file using this objects dictionary path '''

        try:
            # Our data is correct, so we update our immidiate parents data to match
            self.widget.data[self.key] = self.data

            # Recursively updates the parents data until widget=widget (widget), which saves to file
            await self.widget.save_dict()

        except Exception as e:
            print(f"Error saving mini widget data to {self.title}: {e}")


    # Called when changing our widgets data from some event
    async def _change_our_data(self, e):
        ''' Sorts what data to change and how, and if we need to rebuild or just update the page '''

        if isinstance(e.control.data, list):
            key = e.control.data[0]
            idx = e.control.data[1]
            delete_idx = e.control.data[2] if len(e.control.data) > 2 else False

            # If we're deleting from a list, we'll need a reload
            if delete_idx:
                self.data.get(key, []).pop(idx)
                await self.save_dict()

                # Rebuild our canvas
                await self.widget.rebuild_plotline_canvas()

                # Remove the control for this division. Reloading would fix, but lose our scroll placement
                for control in self.divisions_column.controls:
                    if isinstance(control, ft.Container) and isinstance(control.content, ft.Row):
                    
                        text_control = control.content.controls[0]
                        if text_control.data[1] == idx:
                            self.divisions_column.controls.remove(control)
                            break

                # Update the controls indexes after the deleted one. 
                for control in self.divisions_column.controls:
                    if isinstance(control, ft.Container) and isinstance(control.content, ft.Row):
                        text_control = control.content.controls[0]      # Update both text and delete button indexes
                        delete_button = control.content.controls[1]
                        if text_control.data[0] == 'Divisions' and text_control.data[1] >= idx:
                            text_control.data[1] -= 1
                            delete_button.data[1] -= 1

                #self.p.update()

            else:
                self.data.get(key, [])[idx] = e.control.value
                await self.save_dict()
                await self.widget.rebuild_plotline_canvas()
                
        else:
            key = e.control.data
            value = e.control.value
            self._change_our_data_instant(key, value)
            await self.widget.rebuild_plotline_canvas()

    
    def _change_our_data_instant(self, key, value):
        ''' Changes our widgets data instantly '''
        self.data[key] = value
        self.p.run_task(self.widget.save_dict)
        

    # Called when reloading our mini widget UI
    def reload_mini_widget(self):

        async def _new_divisions_clicked(e=None):
            ''' Called to add a new division to the bottom of the divisions list '''
            text_control = ft.TextField(
                expand=True, value=len(self.data.get('Divisions', [])) + 1, dense=True, 
                capitalization=ft.TextCapitalization.SENTENCES,
                on_blur=self._change_our_data,
                data=['Divisions', len(self.data.get('Divisions', [])), False],
                focus_color=self.widget.data.get('color', None),
                cursor_color=self.widget.data.get('color', None),
                focused_border_color=self.widget.data.get('color', None),
            )

            self.divisions_column.controls.append(
                ft.Container(
                    ft.Row([
                        text_control,
                        ft.IconButton(
                            ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR,
                            tooltip="Delete Division", 
                            on_click=self._change_our_data,
                            data=['Divisions', len(self.data.get('Divisions', [])), True],
                        ),
                        
                    ]), margin=ft.Margin.only(left=20, right=20)
                )
            )

            current_divisions = self.data.get('Divisions', [])
            current_divisions.append(str(len(current_divisions) + 1))

            self.data['Divisions'] = current_divisions
            await self.save_dict()
            self.update()

        timeline_icon = ft.Icon(ft.Icons.TIMELINE, self.widget.data.get('color', None))
        plotline_title_text = ft.GestureDetector(
            ft.Text(f"\t\t{self.data['title']}\t\t", weight=ft.FontWeight.BOLD, tooltip=f"Rename {self.title}"),
            on_double_tap=self.widget._rename_clicked,
            on_tap=self.widget._rename_clicked,
            on_secondary_tap=lambda _: self.widget.story.open_menu(self.widget._get_menu_options()),
            mouse_cursor="click", hover_interval=500
        )

        pin_button = ft.IconButton(
            ft.Icons.PUSH_PIN_OUTLINED if not self.data.get('is_pinned', False) else ft.Icons.PUSH_PIN_ROUNDED,
            self.widget.data.get('color', None),
            tooltip="Pin Information Display" if not self.data.get('is_pinned', False) else "Unpin Information Display",
            on_click=self._toggle_pin,
            mouse_cursor="click"
        )

        close_button = ft.IconButton(
            ft.Icons.CLOSE, ft.Colors.ON_SURFACE_VARIANT,
            tooltip=f"Close {self.title}",
            on_click=self.hide_mini_widget,
            mouse_cursor="click"
        )

            
        title_control = ft.Row([
            timeline_icon,
            plotline_title_text,
            pin_button,
            ft.Container(expand=True),      # Spacer
            close_button
        ], spacing=0)
        

          # Start with some spacing at the top


        summary_tf = ft.TextField(
            expand=True, label="Summary", value=self.data.get('Summary', ""), dense=True, multiline=True,
            capitalization=ft.TextCapitalization.SENTENCES,
            on_blur=self._change_our_data,
            data='Summary', 
            focus_color=self.widget.data.get('color', None),
            cursor_color=self.widget.data.get('color', None),
            focused_border_color=self.widget.data.get('color', None),
            label_style=ft.TextStyle(color=self.widget.data.get('color', None)),
        )


        plotline_side_labels = ft.Row([
            ft.TextField(
                expand=True, label="Left Label", value=self.data.get('Left Label', ""), dense=True, 
                capitalization=ft.TextCapitalization.SENTENCES,
                on_blur=self._change_our_data,
                data='Left Label',
                focus_color=self.widget.data.get('color', None),
                cursor_color=self.widget.data.get('color', None),
                focused_border_color=self.widget.data.get('color', None),
                label_style=ft.TextStyle(color=self.widget.data.get('color', None)),
            ),
            ft.TextField(
                expand=True, label="Right Label", value=self.data.get('Right Label', ""), dense=True, 
                capitalization=ft.TextCapitalization.SENTENCES,
                on_blur=self._change_our_data,
                data='Right Label',
                focus_color=self.widget.data.get('color', None),
                cursor_color=self.widget.data.get('color', None),
                focused_border_color=self.widget.data.get('color', None),
                label_style=ft.TextStyle(color=self.widget.data.get('color', None)),
            )
        ])



        time_label_tf = ft.TextField(
            expand=True, label="Time Label", value=self.data.get('Time Label', ""), dense=True,
            capitalization=ft.TextCapitalization.SENTENCES,
            on_blur=self._change_our_data,
            data='Time Label',
            focus_color=self.widget.data.get('color', None),
            cursor_color=self.widget.data.get('color', None),
            focused_border_color=self.widget.data.get('color', None),
            label_style=ft.TextStyle(color=self.widget.data.get('color', None)),
        )


        # Go through and list all our events in order. We'll sort them by their left positions
        events_list = []

        for pp in self.widget.plot_points.values():
            events_list.append(Event(tag='plot_point', left=pp.data.get('left', 0), title=pp.title, color=pp.data.get('color', 'secondary')))

        # Arcs have a right position, so we calc how far that is from left, and add a new event there as well
        for arc in self.widget.arcs.values():
            events_list.append(Event(tag='arc_start', left=arc.data.get('left', 0), title=arc.title, color=arc.data.get('color', 'secondary')))
            arc_width = arc.data.get('width', 0)
            arc_end: int = arc.data.get('left', 0) + arc_width  
            events_list.append(Event(tag='arc_end', left=arc_end, title=arc.title, color=arc.data.get('color', 'secondary')))

        for marker in self.widget.markers.values():
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
                    f"\n◆ {event.title} ◆\n", 
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
                elif previous_span.text.endswith("➜\t\t") and span.text.endswith("◆\n"):     # Remove arrows that lead to marker
                    events_spans[idx - 1] = ft.TextSpan(previous_span.text[:-3], style=previous_span.style)

            # Remove arrow from the end of the last event
            if idx == len(events_spans) - 1:
                if span.text.endswith("\t\t➜\t\t"):
                    events_spans[idx] = ft.TextSpan(span.text[:-6], style=span.style)

        # Make our text control with our built spans
        events_text = ft.Text(spans=events_spans, selectable=True, expand=True)

        # Container to hold the text control for events
        events_container = ft.Container(               
            padding=ft.Padding.all(6), border_radius=ft.BorderRadius.all(10), expand=True,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), 
            content=ft.Row([events_text]),
        )

        events_label = ft.Row([
            ft.Container(width=6), 
            ft.Text(
                "Sequence of Events", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=14), 
                tooltip="The order of events that occur in this plotline"
            ),
            
        ], spacing=0)
        

        divisions_label = ft.Row([
            ft.Container(width=6), 
            ft.Text("Divisions", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=14), tooltip="The number and label of the divisions on this plotline."),
            ft.Container(width=10),
            ft.IconButton(
                ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, self.widget.data.get('color' "primary"),
                tooltip="Add Division", on_click=_new_divisions_clicked,
                mouse_cursor="click"
            )
        ], spacing=0)

        # Returns list of our controls, for plot points, arcs, or markers depending on the key we pass in
        def _get_events(key: str) -> ft.Column:
            ''' Includes the title and a delete button for each event, and a message if there are no events of that type '''
            column = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.START, spacing=0, scroll="none")

            if key == "plot_points":
                for pp in self.widget.plot_points.values():
                    column.controls.append(
                        ft.Row([
                            ft.Container(
                                ft.Text(pp.title, color=pp.data.get('color', None), expand=True, overflow=ft.TextOverflow.ELLIPSIS, weight=ft.FontWeight.BOLD), 
                                on_click=lambda e, p=pp: p.show_mini_widget(), expand=True, padding=ft.Padding.only(left=20)
                            ),
                            ft.Container(
                                ft.IconButton(
                                    ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, on_click=lambda e, p=pp: p._delete_clicked(),
                                    tooltip="Delete Plot Point", style=ft.ButtonStyle(padding=ft.Padding.all(0))
                                ), margin=ft.Margin.only(right=20)
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    )
                if not column.controls:
                    column.controls.append(ft.Text("No plot points added yet.", color=ft.Colors.OUTLINE))
            
            elif key == "arcs":
                for arc in self.widget.arcs.values():
                    column.controls.append(
                        ft.Row([
                            ft.Container(
                                ft.Text(arc.title, color=arc.data.get('color', None), expand=True, overflow=ft.TextOverflow.ELLIPSIS, weight=ft.FontWeight.BOLD), 
                                on_click=lambda e, a=arc: a.show_mini_widget(), expand=True, padding=ft.Padding.only(left=20)
                            ),
                            ft.Container(
                                ft.IconButton(
                                    ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, on_click=lambda e, a=arc: a._delete_clicked(),
                                    tooltip="Delete Arc", style=ft.ButtonStyle(padding=ft.Padding.all(0))
                                ), margin=ft.Margin.only(right=20)
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    )
                if not column.controls:
                    column.controls.append(ft.Text("No arcs added yet.", color=ft.Colors.OUTLINE))
            
            elif key == "markers":
                for marker in self.widget.markers.values():
                    column.controls.append(
                        ft.Row([
                            ft.Container(
                                ft.Text(marker.title, color=marker.data.get('color', None), expand=True, overflow=ft.TextOverflow.ELLIPSIS, weight=ft.FontWeight.BOLD),
                                on_click=lambda e, m=marker: m.show_mini_widget(), expand=True, padding=ft.Padding.only(left=20)
                            ),
                            ft.Container(
                                ft.IconButton(
                                    ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, on_click=lambda e, m=marker: m._delete_clicked(),
                                    tooltip="Delete Marker", style=ft.ButtonStyle(padding=ft.Padding.all(0))
                                ), margin=ft.Margin.only(right=20)
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    )
                if not column.controls:
                    column.controls.append(ft.Text("No markers added yet.", color=ft.Colors.OUTLINE))
            return column


        plot_points_label = ft.Row([
            ft.Container(width=6),
            ft.Text("Plot Points", weight=ft.FontWeight.BOLD),
            ft.Container(width=6),
            ft.IconButton(
                ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, self.widget.data.get('color' "primary"), tooltip="Create New Plot Point", data="plot_point", 
                on_click=self.widget.new_item_clicked, #style=ft.ButtonStyle(padding=ft.Padding.all(0)),
                mouse_cursor="click"
            )
        ], spacing=0)

        plot_points_list = _get_events("plot_points")

        arcs_label = ft.Row([
            ft.Container(width=6),
            ft.Text("Arcs",  weight=ft.FontWeight.BOLD),
            ft.Container(width=6),
            ft.IconButton(
                ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, self.widget.data.get('color' "primary"), tooltip="Create New Arc", data="arc", 
                on_click=self.widget.new_item_clicked, #style=ft.ButtonStyle(padding=ft.Padding.all(0)),
                mouse_cursor="click"
            )
        ], spacing=0)

        arcs_list = _get_events("arcs") 

        markers_label = ft.Row([
            ft.Container(width=6),
            ft.Text("Markers", weight=ft.FontWeight.BOLD),
            ft.Container(width=6),
            ft.IconButton(
                ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, self.widget.data.get('color' "primary"),tooltip="Create New Marker", data="marker", 
                on_click=self.widget.new_item_clicked, #style=ft.ButtonStyle(padding=ft.Padding.all(0)),
                mouse_cursor="click"
            )
        ], spacing=0)

        markers_list = _get_events("markers")


        self.divisions_column.controls.clear()  
        
        # Add all our current divisions
        for idx, division in enumerate(self.data.get('Divisions', [])):
            # Create text control for this division
            text_control = ft.TextField(
                expand=True,  value=division, dense=True, 
                capitalization=ft.TextCapitalization.SENTENCES,
                on_blur=self._change_our_data,
                data=['Divisions', idx, False],
                focus_color=self.widget.data.get('color', None),
                cursor_color=self.widget.data.get('color', None),
                focused_border_color=self.widget.data.get('color', None),
            )

            # Add to a row with delete button to remove divisions
            self.divisions_column.controls.append(
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
            

        custom_fields_label = ft.Row([
            ft.Container(width=6),
            ft.Text("Custom Fields", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), selectable=True),
            ft.IconButton(
                ft.Icons.NEW_LABEL_OUTLINED, self.widget.data.get('color' "primary"), tooltip="Add Custom Field",
                on_click=lambda e: self._new_custom_field_clicked(),
                mouse_cursor="click"
            ),
        ], spacing=0)

        custom_fields_column = self._build_custom_fields_column()


        # Build the main body content of our info display
        content = ft.Column(
            expand=True, tight=True, scroll="auto", alignment=ft.MainAxisAlignment.START, 
            controls=[
                ft.Container(height=1), # Spacer
                summary_tf,             # Summary

                plotline_side_labels,       # Labels
                time_label_tf,

                events_label,       # Events
                events_container,
                
                plot_points_label,  # Plot Points
                plot_points_list,

                arcs_label,         # Arcs
                arcs_list,

                markers_label,      # Markers
                markers_list,
                
                divisions_label,        # Divisions
                ft.Container(self.divisions_column, margin=ft.Margin.symmetric(horizontal=20)),

                custom_fields_label,     # Custom Fields
                ft.Container(custom_fields_column, margin=ft.Margin.symmetric(horizontal=20)),
            ]
        )

        

        column = ft.Column([
            title_control,
            ft.Divider(height=2, thickness=2),
            content
        ], expand=True, scroll="none", tight=True, alignment=ft.MainAxisAlignment.START)
        
        self.content = column

        try:
            self.update()
        except Exception as _:
            pass
