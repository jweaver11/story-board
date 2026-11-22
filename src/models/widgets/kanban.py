"""Kanban board widget."""

import uuid

import flet as ft
import flet_shadcn_ui as shad
import asyncio
from models.views.story import Story
from models.widget import Widget
from styles.colors import colors
from styles.highlight_button import HighlightButton

BOARD_BG_COLOR = ft.Colors.SURFACE_CONTAINER_LOW
CARD_BG_COLOR = ft.Colors.SURFACE_CONTAINER_HIGHEST


class Kanban(Widget):
    def __init__(self, title: str, directory_path: str, story: Story, data: dict = {}, is_new: bool = False):
        super().__init__(title=title, directory_path=directory_path, story=story, data=data, is_new=is_new)

        if self.is_new:
            self.data.update({
                'tag': "kanban",
                'board_data': [
                    {
                        'column_title': '', 
                        'color': 'primary',
                        'cards': [
                            {'value': '', 'strikethrough': False}
                        ],
                    }
                ],
            })

    def build(self):
        super().build()

        def textfield_border(radius=None):
            return {
                ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                    side=ft.BorderSide(color=ft.Colors.TRANSPARENT), border_radius=radius,
                ),
                ft.ControlState.FOCUSED: ft.OutlineInputBorder(
                    side=ft.BorderSide(color=ft.Colors.ON_SURFACE, width=2), border_radius=radius,
                ),
            }

        boards = self.data.setdefault('board_data', [])

        def new_card_data():
            return {'value': '', 'strikethrough': False}

        def save():
            self.update_data(board_data=boards)

        def reorder(e, items):
            if e.old_index is None or e.new_index is None:
                raise ValueError("Reorder event is missing an index")
            if e.old_index == e.new_index:
                return
            items.insert(e.new_index, items.pop(e.old_index))
            e.control.controls.insert(e.new_index, e.control.controls.pop(e.old_index))
            save()
            e.control.update()

        def identity_index(items, item):
            return next(index for index, value in enumerate(items) if value is item)

        def color_popover(set_color):
            def close(e=None):
                popover.open = False
                popover.update()

            def toggle(e):
                popover.open = not popover.open
                popover.update()

            def select(e):
                set_color(e.control.data)
                close()

            popover = shad.Popover(
                shad.MenuItem(
                    leading=ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, ft.Colors.PRIMARY, size=20),
                    content=ft.Row(
                        [ft.Text("Color"), ft.Icon(ft.Icons.ARROW_RIGHT, ft.Colors.OUTLINE, size=16)],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    on_click=toggle, close_on_click=False,
                ),
                ft.Column([
                    shad.MenuItem(
                        content=ft.Icon(ft.Icons.CIRCLE, color=color, size=20),
                        on_click=select, close_on_click=True, data=color, tooltip=color,
                    ) for color in colors
                ], tight=True, spacing=0, width=100, height=240, scroll=ft.ScrollMode.AUTO),
                on_dismiss=close,
            )
            return popover

        def build_board(board):
            cards = board.setdefault('cards', [])

            def build_card(card):
                def save_value(e):
                    card['value'] = e.control.value
                    save()

                def toggle_strikethrough(e):
                    card['strikethrough'] = not card.get('strikethrough', False)
                    decoration = ft.TextDecoration.LINE_THROUGH if card['strikethrough'] else ft.TextDecoration.NONE
                    value_field.text_style.decoration = decoration
                    done_chip.selected = card['strikethrough']
                    save()
                    value_field.update()
                    done_chip.update()

                def delete_card(e):
                    index = identity_index(cards, card)
                    cards.pop(index)
                    card_list.controls.pop(index)
                    save()
                    card_list.update()

                decoration = ft.TextDecoration.LINE_THROUGH if card.get('strikethrough', False) else ft.TextDecoration.NONE
                value_field = ft.TextField(
                    value=card.get('value', ''), hint_text="Describe your task",
                    dense=True, multiline=True, capitalization=ft.TextCapitalization.SENTENCES,
                    text_style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD, decoration=decoration, decoration_thickness=2),
                    border=textfield_border(8),
                    on_change=save_value, expand=True
                )
                done_chip = ft.Chip(
                    label="Done", padding=0,
                    selected=card.get('strikethrough', False),
                    on_select=toggle_strikethrough,
                    tooltip="Toggle strikethrough",
                    selected_color=ft.Colors.SURFACE,
                    visual_density=ft.VisualDensity.COMPACT,
                )
                delete_chip = ft.Chip(
                    #label="Delete",
                    padding=0,
                    label=ft.Icon(ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, size=16),
                    on_click=delete_card,
                    tooltip="Delete card",
                    visual_density=ft.VisualDensity.COMPACT,
                )
                card_control = ft.Container(
                    ft.Column([
                        value_field,
                        ft.Row([done_chip, delete_chip], spacing=4, wrap=True, margin=ft.Margin.only(left=8, bottom=4), alignment=ft.MainAxisAlignment.END),
                    ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
                    bgcolor=CARD_BG_COLOR,
                    border_radius=8, margin=ft.Margin.only(bottom=8),
                )
                return ft.ReorderableDragHandle(
                    card_control,
                    mouse_cursor=ft.MouseCursor.GRAB,
                    key=str(uuid.uuid4()),
                )

            def add_card(e):
                card = new_card_data()
                cards.append(card)
                card_list.controls.append(build_card(card))
                save()
                card_list.update()
                
            def delete_board(e):
                index = identity_index(boards, board)
                boards.pop(index)
                boards_lv.controls.pop(index)
                save()
                boards_lv.update()

            def set_board_color(color):
                board['color'] = color
                header_tf.text_style.color = color
                save()
                header_control.update()

            def save_title(e):
                board['column_title'] = e.control.value
                save()

            card_list = ft.ReorderableListView(
                controls=[build_card(card) for card in cards],
                show_default_drag_handles=False,
                on_reorder=lambda e: reorder(e, cards),
                padding=ft.Padding.only(left=8, right=8, top=4)
            )
            menu = shad.ContextMenu(
                HighlightButton(ft.Icon(ft.Icons.MORE_HORIZ, ft.Colors.ON_SURFACE_VARIANT), use_padding=True),
                [
                    shad.MenuItem("Add Task", ft.Icon(ft.Icons.ADD, ft.Colors.PRIMARY, 20), on_click=add_card),
                    shad.Separator(ft.Margin.symmetric(vertical=4)),
                    color_popover(set_board_color),
                    shad.Separator(ft.Margin.symmetric(vertical=4)),
                    shad.MenuItem("Delete Column", ft.Icon(ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, 20), on_click=delete_board),
                ],
                open_on_tap=True,
                tooltip="Column options",
            )

            header_tf = ft.TextField(
                value=board.get('column_title', ''), hint_text="Column title", expand=True,
                dense=True, capitalization=ft.TextCapitalization.WORDS,
                text_style=ft.TextStyle(weight=ft.FontWeight.W_600, size=16, color=board.get('color', 'primary')),
                border=textfield_border(8),
                on_change=save_title, 
            )
            header_control = ft.Container(
                ft.Row([
                    header_tf,
                    menu,
                ], spacing=0),
                border_radius=8,
            )
            board_control = ft.Container(
                ft.Column([header_control, card_list], spacing=0, expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
                bgcolor=BOARD_BG_COLOR, border_radius=8,
            )
            return ft.Container(
                ft.Column([
                    ft.ReorderableDragHandle(
                        board_control,
                        mouse_cursor=ft.MouseCursor.GRAB,
                    ),
                ],  expand=True, scroll=ft.ScrollMode.HIDDEN, spacing=0),
                width=300, margin=ft.Margin.only(right=10), alignment=ft.Alignment.TOP_CENTER,
                key=str(uuid.uuid4()),
            )

        def add_board(e):
            board = {'column_title': '', 'cards': [new_card_data()], 'color': 'primary'}
            boards.append(board)
            boards_lv.controls.append(build_board(board))
            save()
            boards_lv.update()

        boards_lv = ft.ReorderableListView(
            controls=[build_board(board) for board in boards],
            horizontal=True, expand=True, show_default_drag_handles=False,
            on_reorder=lambda e: reorder(e, boards),
            scroll=ft.ScrollMode.ALWAYS
        )

        self.description_tf.bgcolor = ft.Colors.SURFACE
        self.description_tf.margin = ft.Margin.only(top=10)
        self.description_tf.label = "Scope"
        self.description_tf.hint_text = "What parts of your story this Kanban Board covers..."
        self.description_tf.hint_style = ft.TextStyle(italic=True)

        self.padding = ft.Padding.only(top=10, left=10, right=10, bottom=5)
        #self.bgcolor = ft.Colors.SURFACE_CONTAINER

        self.content = ft.Column([
            ft.Row(
                [
                    boards_lv,
                    shad.Button(
                        ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY), 
                        bgcolor=ft.Colors.SURFACE, hover_bgcolor=ft.Colors.SURFACE_CONTAINER, 
                        on_click=add_board, size=shad.ButtonSize.SM
                    )
                ], expand=True, scroll=ft.ScrollMode.ALWAYS, spacing=0, vertical_alignment=ft.CrossAxisAlignment.START),
            ft.Row([self.description_tf]),
        ], expand=True, spacing=0)
