

import flet as ft

class ContextMenu(ft.ContextMenu):

    def __init__(
            self, 
            content: ft.Control, 
            primary_items: list[ft.PopupMenuItem] = None, 
            secondary_items: list[ft.PopupMenuItem] = None, 
            key: str = None
        ):

        super().__init__(
            content=content,
            primary_items=primary_items,
            secondary_items=secondary_items,
            key=key,
            primary_trigger=ft.ContextMenuTrigger.DOWN if primary_items else None,
            secondary_trigger=ft.ContextMenuTrigger.DOWN if secondary_items else None,
        )