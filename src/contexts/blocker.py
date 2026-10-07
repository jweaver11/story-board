
import flet as ft
from dataclasses import dataclass
import asyncio

@ft.observable
@dataclass
class BlockerState:
    visible: bool = False    # If we should block the page for demanding opterations
    async def block_page(self):   # Block the page
        self.visible = True
        await asyncio.sleep(0.05)
    def unblock_page(self):     # Unblock the page
        self.visible = False

@ft.component
def Blocker(blocker_state: BlockerState):
    ''' A small spinning ring to block interactions with the page while demanding calculations happen '''
    return ft.Container(
        ft.Row([
            ft.ProgressRing(width=100, height=100)
        ], alignment=ft.MainAxisAlignment.CENTER), 
        expand=True, 
        visible=blocker_state.visible, 
        blur=5, left=0, right=0, top=0, bottom=0,
        key="blocker"
    )