import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("FLET_APP_STORAGE_DATA", tempfile.gettempdir())

import flet as ft
from flet.utils.validation import validate
from models.widget import Widget
from models.widgets.radar_chart import RadarChart


class RadarChartTests(unittest.TestCase):
    def setUp(self):
        self.widget = RadarChart.__new__(RadarChart)
        ft.Container.__init__(self.widget, data={
            "chart_data": {
                "nodes": ["A", "B", "C"],
                "data_sets": [],
                "min_value": 0,
                "max_value": 20,
                "tick_count": 2,
            },
        })
        self.widget.needs_file_write = False
        self.widget.sidebar_header = ft.Row()
        self.widget.sidebar_body = ft.Column()
        self.widget.sidebar_notes_label = ft.Row()
        self.widget.sidebar_notes_column = ft.Column()
        self.widget.toggle_sidebar_visibility_button = ft.Container()
        self.widget.sidebar = ft.Container()
        self.build_patch = patch.object(Widget, "build")
        self.update_patch = patch.object(ft.Control, "update")
        self.build_patch.start()
        self.update_patch.start()
        self.addCleanup(self.build_patch.stop)
        self.addCleanup(self.update_patch.stop)
        self.widget.build()
        self.chart = self.widget.content.controls[0].controls[0].controls[1]
        self.datasets = self.widget.sidebar_body.controls[1]
        self.add_dataset = self.widget.sidebar_body.controls[0].controls[1]
        self.add_node = self.widget.sidebar_body.controls[2].controls[1]

    def fire(self, control, name, value=None, data=None):
        if value is not None:
            control.value = value
        result = getattr(control, name)(SimpleNamespace(control=control, data=data))
        if asyncio.iscoroutine(result):
            asyncio.run(result)

    def add_data_set(self):
        self.fire(self.add_dataset, "on_click")

    def test_dataset_can_be_added_deleted_and_added_again(self):
        self.add_data_set()
        self.assertEqual(len(self.chart.data_sets), 2)
        self.fire(self.datasets.controls[0].trailing, "on_click")
        self.assertEqual(self.widget.data["chart_data"]["data_sets"], [])
        self.assertEqual(len(self.chart.data_sets), 1)

        self.add_data_set()
        self.assertEqual(len(self.widget.data["chart_data"]["data_sets"]), 1)
        self.assertEqual(len(self.chart.data_sets), 2)
        validate(self.chart)

    def test_dataset_sliders_are_reindexed_after_deletion(self):
        self.add_data_set()
        self.add_data_set()
        self.fire(self.datasets.controls[0].trailing, "on_click")

        self.fire(self.datasets.controls[0], "on_change", data=False)
        self.assertFalse(self.widget.data["chart_data"]["data_sets"][0]["expanded"])
        slider = self.datasets.controls[0].controls[0].controls[1]
        self.assertEqual(slider.data, (0, 0))
        self.fire(slider, "on_change", 13)
        self.fire(slider, "on_change_end", 13)
        self.assertEqual(self.widget.data["chart_data"]["data_sets"][0]["entries"][0], 13)
        self.assertEqual(self.chart.data_sets[1].entries[0].value, 13)

    def test_dataset_titles_and_colors_keep_working_after_deletion(self):
        self.add_data_set()
        self.add_data_set()
        self.fire(self.datasets.controls[0].trailing, "on_click")

        dataset_keys = self.widget.content.controls[0].controls[0].controls[0]
        title_field = dataset_keys.controls[0].content.controls[1]
        self.fire(title_field, "on_change", "Renamed")
        self.assertEqual(self.widget.data["chart_data"]["data_sets"][0]["title"], "Renamed")
        self.assertEqual(self.datasets.controls[0].title.value, "Renamed")

        color_option = self.datasets.controls[0].leading.items[1]
        self.fire(color_option, "on_click")
        new_color = color_option.data[1]
        self.assertEqual(self.widget.data["chart_data"]["data_sets"][0]["color"], new_color)
        self.assertEqual(self.chart.data_sets[1].border_color, new_color)
        self.assertEqual(
            self.datasets.controls[0].leading.content.content.content.color,
            new_color,
        )

    def test_added_node_has_editable_dataset_entry_and_reindexes_after_delete(self):
        self.add_data_set()
        self.fire(self.add_node, "on_click")
        self.fire(self.add_node, "on_click")
        tile = self.datasets.controls[0]
        self.assertEqual(len(tile.controls), 5)
        self.assertEqual(tile.controls[4].controls[1].data, (0, 4))

        self.fire(self.widget.sidebar_body.controls[3].controls[3].content.suffix, "on_click")
        node_field = self.widget.sidebar_body.controls[3].controls[3].content
        self.assertEqual(node_field.data, 3)
        self.assertEqual(tile.controls[3].controls[1].data, (0, 3))

        self.fire(node_field, "on_change", "Renamed")
        self.assertEqual(self.widget.data["chart_data"]["nodes"][3], "Renamed")
        slider = tile.controls[3].controls[1]
        self.fire(slider, "on_change", 14)
        self.fire(slider, "on_change_end", 14)
        self.assertEqual(self.widget.data["chart_data"]["data_sets"][0]["entries"][3], 14)

    def test_invalid_scale_input_does_not_crash_or_change_chart_data(self):
        self.add_data_set()
        settings = self.widget.sidebar_header.controls[-1].items
        max_field = settings[5]
        self.fire(max_field, "on_blur", "")
        self.assertEqual(max_field.value, "20")
        self.assertIsNotNone(max_field.error_text)
        self.assertEqual(self.widget.data["chart_data"]["max_value"], 20)

        self.fire(max_field, "on_blur", "30")
        slider = self.datasets.controls[0].controls[0].controls[1]
        self.assertEqual(self.widget.data["chart_data"]["max_value"], 30)
        self.assertIsNone(max_field.error_text)
        self.assertEqual((slider.max, slider.divisions), (30, 30))


if __name__ == "__main__":
    unittest.main()
