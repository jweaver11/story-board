import flet as ft
from models.mini_widget import MiniWidget
from models.widgets.plotline import Plotline
import asyncio
from models.dataclasses.events import Event


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
        
        # Since we only reference out owners data and not our own, we don't need to verify it here

        # NOT USED, but plot points use it when dragging, so this needs a value
        self.data['visible'] = self.owner.data.get('information_display_visibility', True)

        # Set our visibility based on our owners data
        self.visible = self.owner.data.get('information_display_visibility', True)
        self.data['is_pinned'] = self.owner.data.get('information_display_is_pinned', False)

        self.reload_mini_widget()

    

    # Called when saving changes to our Plotline object
    def save_dict(self):
        ''' Overwrites standard mini widget save and save our Plotlines data instead '''
        try:
            self.owner.save_dict()
        except Exception as e:
            print(f"Error saving Plotline information display data to {self.owner.title}: {e}")

    # Called to toggle our visibility
    def show_mini_widget(self, e=None):
        ''' Toggles our visibility and updates our owners data accordingly '''

        if self.visible:
            return
        
        # Update our visibility
        self.owner.data['information_display_visibility'] = True
        super().show_mini_widget(e)

    def hide_mini_widget(self, e=None, update: bool=False):
        ''' Hides our mini widget '''

        self.owner.data['information_display_visibility'] = False
        self.owner.data['information_display_is_pinned'] = False
        super().hide_mini_widget(e, update)

    # Called when changing our owners data from some event
    async def _change_owner_data(self, e):
        ''' Sorts what data to change and how, and if we need to rebuild or just update the page '''

        if isinstance(e.control.data, list):
            key = e.control.data[0]
            idx = e.control.data[1]
            delete_idx = e.control.data[2] if len(e.control.data) > 2 else False

            # If we're deleting from a list, we'll need a reload
            if delete_idx:
                self.owner.data.get('plotline_data', {}).get(key, []).pop(idx)
                self.owner.save_dict()
                self.reload_mini_widget()
                await self.owner.rebuild_plotline_canvas(no_update=True)

            else:
                self.owner.data.get('plotline_data', {}).get(key, [])[idx] = e.control.value
                self.owner.save_dict()
                await self.owner.rebuild_plotline_canvas(no_update=True)
                
        else:
            key = e.control.data
            value = e.control.value
            self._change_owner_data_instant(key, value)
            await self.owner.rebuild_plotline_canvas(no_update=True)

    
    def _change_owner_data_instant(self, key, value):
        ''' Changes our owners data instantly '''
        self.owner.data['plotline_data'][key] = value
        self.owner.save_dict()

    async def _toggle_pin(self, e):
        ''' Pins or unpins our information display '''
            
        self.owner.data['information_display_is_pinned'] = not self.owner.data['information_display_is_pinned']
        self.data['is_pinned'] = self.owner.data['information_display_is_pinned']
        self.save_dict()
        self.reload_mini_widget()
        self.owner.reload_widget()
        

    # Called when reloading our mini widget UI
    def reload_mini_widget(self, no_update: bool=False, scroll_down: bool=False):

        async def _new_divisions_clicked(e):
            ''' Called to add a new division to the bottom of the divisions list '''
            text_control = ft.TextField(
                expand=True, value=len(self.owner.data.get('plotline_data', {}).get('Divisions', [])) + 1, dense=True, 
                capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                on_blur=self._change_owner_data,
                data=['Divisions', len(self.owner.data.get('plotline_data', {}).get('Divisions', [])), False],
                focus_color=self.owner.data.get('color', None),
                cursor_color=self.owner.data.get('color', None),
                focused_border_color=self.owner.data.get('color', None),
            )

            divisions_container.content.controls.insert(
                len(divisions_container.content.controls) - 1,
                ft.Row([
                    text_control,
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR,
                        tooltip="Delete Division", 
                        on_click=self._change_owner_data,
                        data=['Divisions', len(self.owner.data.get('plotline_data', {}).get('Divisions', [])), True],
                    ),
                ])
            )

            current_divisions = self.owner.data.get('plotline_data', {}).get('Divisions', [])
            current_divisions.append(str(len(current_divisions) + 1))

            await self.owner.change_data(divisions=current_divisions)
            
            self.p.update()
            
        title_control = ft.Row([
            ft.Icon(ft.Icons.TIMELINE, self.owner.data.get('color', None)),
            ft.Text(self.data['title'], weight=ft.FontWeight.BOLD, selectable=True, overflow=ft.TextOverflow.FADE),
            ft.IconButton(
                ft.Icons.PUSH_PIN_OUTLINED if not self.owner.data.get('information_display_is_pinned', False) else ft.Icons.PUSH_PIN_ROUNDED,
                self.owner.data.get('color', None),
                tooltip="Pin Information Display" if not self.owner.data.get('information_display_is_pinned', False) else "Unpin Information Display",
                on_click=self._toggle_pin
            ),
            ft.Container(expand=True),
            ft.IconButton(
                ft.Icons.CLOSE, ft.Colors.ON_SURFACE_VARIANT,
                tooltip=f"Close {self.title}",
                on_click=lambda e: self.hide_mini_widget(update=True),
            ),
        ])
        

        content = ft.Column(expand=True, tight=True, scroll="auto", alignment=ft.MainAxisAlignment.START, scroll_down=scroll_down)



        # Summary
        content.controls.append(
            ft.TextField(
                expand=True, label="Summary", value=self.owner.data.get('plotline_data', {}).get('Summary', ""), dense=True, multiline=True,
                capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                on_blur=self._change_owner_data,
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
                    expand=True, label="Left Label", value=self.owner.data.get('plotline_data', {}).get('Left Label', ""), dense=True, 
                    capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                    on_blur=self._change_owner_data,
                    data='Left Label',
                    focus_color=self.owner.data.get('color', None),
                    cursor_color=self.owner.data.get('color', None),
                    focused_border_color=self.owner.data.get('color', None),
                    label_style=ft.TextStyle(color=self.owner.data.get('color', None)),
                ),
                ft.TextField(
                    expand=True, label="Right Label", value=self.owner.data.get('plotline_data', {}).get('Right Label', ""), dense=True, 
                    capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                    on_blur=self._change_owner_data,
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
                expand=True, label="Time Label", value=self.owner.data.get('plotline_data', {}).get('Time Label', ""), dense=True,
                capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                on_blur=self._change_owner_data,
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

        content.controls.append(events_container)

        

        # Add the label and the Divisions container
        content.controls.append(
            ft.Row([
                ft.Container(width=6), 
                ft.Text("Events", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=14), color=self.owner.data.get('color', None), tooltip="The order of events that occur in this plotline"),
            ], spacing=0)
        )

        # Container for our divisions list
        divisions_container = ft.Container(               
            padding=ft.padding.all(6), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT), 
            content=ft.Column(spacing=0),
        )
        
        # Add all our current divisions
        for idx, division in enumerate(self.owner.data.get('plotline_data').get('Divisions', [])):
            # Create text control for this division
            text_control = ft.TextField(
                expand=True,  value=division, dense=True, 
                capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                on_blur=self._change_owner_data,
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
                        on_click=self._change_owner_data,
                        data=['Divisions', idx, True],
                    ),
                ])
            )

        # Add division button
        divisions_container.content.controls.append(
            ft.IconButton(
                ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                tooltip="Add Division", on_click=_new_divisions_clicked
            )
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
