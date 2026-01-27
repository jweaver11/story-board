import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
from models.widgets.plotline import Plotline
import asyncio
from models.dataclasses.events import Event


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

    # Called when changing our owners data from some event
    async def _change_owner_data(self, e):
        ''' Sorts what data to change and how, and if we need to rebuild or just update the page '''

        if isinstance(e.control.data, list):
            key = e.control.data[0]
            idx = e.control.data[1]
            delete_idx = e.control.data[2] if len(e.control.data) > 2 else False

            # If we're deleting from a list, we'll need a reload
            if delete_idx:
                self.owner.data.get(key, []).pop(idx)
                self.owner.save_dict()
                self.reload_mini_widget()
                await self.owner.rebuild_plotline_canvas(no_update=True)

            else:
                self.owner.data.get(key, [])[idx] = e.control.value
                self.owner.save_dict()
                await self.owner.rebuild_plotline_canvas(no_update=True)
                
        else:
            key = e.control.data
            value = e.control.value
            self._change_owner_data_instant(key, value)
            await self.owner.rebuild_plotline_canvas(no_update=True)

    
    def _change_owner_data_instant(self, key, value):
        ''' Changes our owners data instantly '''
        self.owner.data[key] = value
        self.owner.save_dict()

        

    # Called when reloading our mini widget UI
    def reload_mini_widget(self):

        async def _new_divisions_clicked(e):
            ''' Called to add a new division to the bottom of the divisions list '''
            text_control = ft.TextField(
                expand=True, value=len(self.owner.data.get('divisions', [])) + 1, dense=True, 
                capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                on_blur=self._change_owner_data,
                data=['divisions', len(self.owner.data.get('divisions', [])), False],
                focus_color=self.owner.data.get('color', None),
                cursor_color=self.owner.data.get('color', None),
                focused_border_color=self.owner.data.get('color', None),
            )

            divisions_expansion_tile.controls.insert(
                len(divisions_expansion_tile.controls) - 1,
                ft.Row([
                    text_control,
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR,
                        tooltip="Delete Division", 
                        on_click=self._change_owner_data,
                        data=['divisions', len(self.owner.data.get('divisions', [])), True],
                    ),
                ])
            )

            current_divisions = self.owner.data.get('divisions', [])
            current_divisions.append(str(len(current_divisions) + 1))

            await self.owner.change_data(divisions=current_divisions)
            
            self.p.update()
            #text_control.focus()       # Broken and forces focus forever
            
        self.title_control = ft.Row([
            ft.Icon(ft.Icons.TIMELINE, self.owner.data.get('color', None)),
            ft.Text(self.data['title'], weight=ft.FontWeight.BOLD, selectable=True, overflow=ft.TextOverflow.FADE),
            ft.Container(expand=True),
            ft.IconButton(
                ft.Icons.CLOSE, ft.Colors.ON_SURFACE_VARIANT,
                tooltip=f"Close {self.title}",
                on_click=lambda e: self.toggle_visibility(value=False),
            ),
        ])
        

        content = ft.Column([
            self.title_control,
            ft.Divider(height=2, thickness=2),
            ft.Container(height=10)  # Spacing 
        ], expand=True, tight=True, spacing=0)


        # Summary
        content.controls.append(
            ft.TextField(
                expand=True, label="Summary", value=self.owner.data.get('summary', ""), dense=True, multiline=True,
                capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                on_blur=self._change_owner_data,
                data='summary', 
                focus_color=self.owner.data.get('color', None),
                cursor_color=self.owner.data.get('color', None),
                focused_border_color=self.owner.data.get('color', None),
                label_style=ft.TextStyle(color=self.owner.data.get('color', None)),
            )
        )
        content.controls.append(ft.Container(height=10))  # Spacing 

        
        # Our labels
        content.controls.append(
            ft.Row([
                ft.TextField(
                    expand=True, label="Left Label", value=self.owner.data.get('left_label', ""), dense=True, 
                    capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                    on_blur=self._change_owner_data,
                    data='left_label',
                    focus_color=self.owner.data.get('color', None),
                    cursor_color=self.owner.data.get('color', None),
                    focused_border_color=self.owner.data.get('color', None),
                    label_style=ft.TextStyle(color=self.owner.data.get('color', None)),
                ),
                ft.TextField(
                    expand=True, label="Time Label", value=self.owner.data.get('time_label', ""), dense=True,
                    capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                    on_blur=self._change_owner_data,
                    data='time_label',
                    
                    focus_color=self.owner.data.get('color', None),
                    cursor_color=self.owner.data.get('color', None),
                    focused_border_color=self.owner.data.get('color', None),
                    label_style=ft.TextStyle(color=self.owner.data.get('color', None)),
                ),
                ft.TextField(
                    expand=True, label="Right Label", value=self.owner.data.get('right_label', ""), dense=True, 
                    capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                    on_blur=self._change_owner_data,
                    data='right_label',
                    focus_color=self.owner.data.get('color', None),
                    cursor_color=self.owner.data.get('color', None),
                    focused_border_color=self.owner.data.get('color', None),
                    label_style=ft.TextStyle(color=self.owner.data.get('color', None)),
                )
            ])
        )
        content.controls.append(ft.Container(height=10))  # Spacing

        


        # Go through and list all our events in order
        events_list = []

        for pp in self.owner.plot_points.values():
            events_list.append(Event(tag='plot_point', x_alignment=pp.data.get('x_alignment', 0), title=pp.title, color=pp.data.get('color', 'secondary')))

        for arc in self.owner.arcs.values():
            events_list.append(Event(tag='arc_start', x_alignment=arc.data.get('x_alignment_start', 0), title=arc.title, color=arc.data.get('color', 'secondary')))
            events_list.append(Event(tag='arc_end', x_alignment=arc.data.get('x_alignment_end', 0), title=arc.title, color=arc.data.get('color', 'secondary')))

        for marker in self.owner.markers.values():
            events_list.append(Event(tag='marker', x_alignment=marker.data.get('x_alignment', 0), title=marker.title, color=marker.data.get('color', 'secondary')))

        # Sort that list
        events_list = sorted(events_list, key=lambda e: e.x_alignment)

        # Hold our text spans
        events_spans = []

        for idx, event in enumerate(events_list):

            if event.tag == 'arc_start':
                events_spans.append(ft.TextSpan(f"{event.title} Begins\t->\t"))
            elif event.tag == 'arc_end':
                events_spans.append(ft.TextSpan(f"{event.title} Ends\t->\t"))
            else:
                events_spans.append(ft.TextSpan(f"{event.title}\t->\t"))

            # Remove the arrow for the last one
            if idx == len(events_list) - 1:
                # Last one, no arrow
                events_spans[-1] = ft.TextSpan(events_spans[-1].text[:-4])

        # Make our text control with our built spans
        events_text = ft.Text(spans=events_spans, selectable=True)

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
        content.controls.append(ft.Container(height=6))  # Spacing

        content.controls.append(events_container)
        content.controls.append(ft.Container(height=10))  # Spacing

        # Create our divisions expansion tlie
        divisions_expansion_tile = ft.ExpansionTile(
            ft.Text("Divisions", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=14), color=self.owner.data.get('color', None), expand=True, tooltip="Simple evenly spaced division markers on the plotline",),
            controls=[], initially_expanded=self.owner.data.get('divisions_are_expanded', True), 
            collapsed_icon_color=self.owner.data.get('color', None),
            icon_color=self.owner.data.get('color', None), shape=ft.RoundedRectangleBorder(),
            on_change=lambda e: self._change_owner_data_instant('divisions_are_expanded', not self.owner.data.get('divisions_are_expanded', True))
        )
        
        # Add all our current divisions
        for idx, division in enumerate(self.owner.data.get('divisions', [])):
            # Create text control for this division
            text_control = ft.TextField(
                expand=True,  value=division, dense=True, 
                capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                on_blur=self._change_owner_data,
                data=['divisions', idx, False],
                focus_color=self.owner.data.get('color', None),
                cursor_color=self.owner.data.get('color', None),
                focused_border_color=self.owner.data.get('color', None),
            )

            # Add to a row with delete button to remove divisions
            divisions_expansion_tile.controls.append(
                ft.Row([
                    text_control,
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR,
                        tooltip="Delete Division", 
                        on_click=self._change_owner_data,
                        data=['divisions', idx, True],
                    ),
                ])
            )

        # Add division button
        divisions_expansion_tile.controls.append(
            ft.IconButton(
                ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                tooltip="Add Division", on_click=_new_divisions_clicked
            )
        )

        content.controls.append(divisions_expansion_tile)
        content.controls.append(ft.Container(height=10))

        # Markers, Plot Points, and Arcs

        # Format our final layout so the scrollbar doesn't sit overtop the content
        row = ft.Row(expand=True, controls=[content, ft.Container(width=8)], spacing=0)
    
        column = ft.Column([
            row
        ], expand=True, scroll="auto", tight=True)
        
        self.content = column

        #self.p.update()