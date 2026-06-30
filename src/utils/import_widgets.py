import flet as ft
import json
from models.widget import Widget
from models.widgets.document import Document
from models.widgets.note import Note
from models.widgets.canvas import Canvas
from models.widgets.canvas_board import CanvasBoard
from models.widgets.character import Character
from models.widgets.plotline import Plotline
from models.widgets.map import Map
from models.widgets.character_connection_map import CharacterConnectionMap
from models.widgets.item import Item
from models.widgets.world import World
from models.widgets.chart import Chart
from models.widgets.comic_preview import ComicPreview
from models.widgets.plot_chart import PlotChart


def import_widgets(file_paths: list[str], dir_path: str, story) -> list[Widget]:
    '''Accepts a list of directory paths and returns (error, widgets).'''

    page = story.page

    def create_widget() -> Widget:
        return

    # TODO: Check file type, tag

    error: list[ValueError] | None = None
    widgets: list[Widget] = []

    for fp in file_paths:
        ext = fp.split('.')[-1].lower()
        match ext:

            # Json from other widget exports
            case 'json':
                try:
                    with open(fp, "r", encoding='utf-8') as f:
                        data = json.load(f)
                        tag = data.get('tag', None)
                        if not tag: # Make sure it has a tag
                            continue
                        widgets.append(create_widget(data))

                except Exception:
                    pass

            # Images to turn into canvases
            case 'png' | 'jpg' | 'jpeg' | 'webp':
                pass

            # Text files to turn into documents
            case 'txt' | 'pdf' | 'docx' | 'md':
                pass
        pass