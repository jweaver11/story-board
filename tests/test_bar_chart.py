import asyncio
import json
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
from models.widgets.bar_chart import BarChart


class BarChartTests(unittest.TestCase):
    def setUp(self):
        self.widget = BarChart.__new__(BarChart)
        ft.Container.__init__(self.widget, data={
            "chart_data": {"groups": [], "max_y": 20},
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
        self.chart = self.widget.content.controls[0].controls[0].content
        self.groups = self.widget.sidebar_body.controls[1]
        self.add_group = self.widget.sidebar_body.controls[0].controls[1]
        self.settings = self.widget.sidebar_header.controls[-1].items

    def fire(self, control, name, value=None):
        if value is not None:
            control.value = value
        result = getattr(control, name)(SimpleNamespace(control=control))
        if asyncio.iscoroutine(result):
            asyncio.run(result)

    def add_rod(self, group):
        self.fire(self.groups.controls[group].controls[1].controls[1], "on_click")

    def test_expanding_group_preserves_groups_and_allows_adding_rods(self):
        self.fire(self.add_group, "on_click")
        tile = self.groups.controls[0]
        tile.expanded = False
        self.fire(tile, "on_change")
        self.assertIsInstance(self.widget.data["chart_data"]["groups"], list)
        self.assertFalse(self.widget.data["chart_data"]["groups"][0]["expanded"])
        self.add_rod(0)
        self.assertEqual(len(self.chart.groups[0].rods), 2)
        self.assertEqual(len(self.widget.data["chart_data"]["groups"][0]["rods"]), 2)
        self.assertIsInstance(self.chart.top_axis.labels, list)

    def test_delete_reindexes_every_callback_and_chart_position(self):
        self.fire(self.add_group, "on_click")
        self.fire(self.add_group, "on_click")
        self.add_rod(1)
        self.fire(self.groups.controls[0].trailing, "on_click")
        self.assertEqual(self.chart.groups[0].x, 0)
        tile = self.groups.controls[0]
        tile.expanded = False
        self.fire(tile, "on_change")
        label = self.chart.bottom_axis.labels[0].label
        self.fire(label, "on_change", "Renamed")
        self.assertEqual(tile.title.value, "Renamed")
        self.assertEqual(self.widget.data["chart_data"]["groups"][0]["name"], "Renamed")
        self.add_rod(0)
        self.fire(tile.controls[2].controls[4], "on_click")
        slider = tile.controls[2].controls[2]
        self.fire(slider, "on_change", 7)
        self.fire(slider, "on_change_end", 7)
        self.assertEqual(self.chart.groups[0].rods[0].to_y, 7)
        self.assertEqual(self.widget.data["chart_data"]["groups"][0]["rods"][0]["to_y"], 7)
        self.assertEqual(len(tile.controls) - 2, 2)

    def test_color_change_updates_rod_and_sidebar_after_deletion(self):
        self.fire(self.add_group, "on_click")
        self.add_rod(0)
        self.fire(self.groups.controls[0].controls[2].controls[4], "on_click")
        row = self.groups.controls[0].controls[2]
        menu = row.controls[0]
        option = menu.items[1]
        self.fire(option, "on_click")
        color = option.data[2]
        self.assertEqual(self.widget.data["chart_data"]["groups"][0]["rods"][0]["color"], color)
        self.assertEqual(self.chart.groups[0].rods[0].color, color)
        self.assertEqual(row.controls[2].active_color, color)
        self.assertEqual(menu.content.content.content.color, color)

    def test_max_y_validates_and_updates_existing_sliders(self):
        self.fire(self.add_group, "on_click")
        max_field = self.settings[5]
        self.fire(max_field, "on_blur", "30")
        slider = self.groups.controls[0].controls[2].controls[2]
        self.assertEqual((self.chart.max_y, slider.max, slider.divisions), (30, 30, 30))
        self.assertEqual(self.groups.controls[0].controls[2].controls[3].value, "30")
        for invalid in ("0", "9", "invalid", "", "9" * 5000, "9007199254740992"):
            self.fire(max_field, "on_blur", invalid)
            self.assertEqual(self.chart.max_y, 30)
            self.assertEqual(max_field.value, "30")
        self.assertEqual(self.widget.data["chart_data"]["max_y"], 30)
        self.assertIsNotNone(max_field.error_text)
        self.fire(max_field, "on_blur", "10")
        self.assertIsNone(max_field.error_text)
        validate(slider)

    def test_settings_apply_to_new_rods_and_groups_and_empty_groups(self):
        validate(self.settings[7].controls[1])
        self.fire(self.settings[0], "on_change", True)
        self.fire(self.settings[1], "on_change", False)
        self.fire(self.settings[6].controls[1], "on_change_end", 55)
        self.fire(self.settings[7].controls[1], "on_change_end", 12)
        self.fire(self.add_group, "on_click")
        self.add_rod(0)
        group = self.chart.groups[0]
        self.assertTrue(group.group_vertically)
        self.assertEqual(group.spacing, 12)
        self.assertTrue(all(rod.width == 55 and rod.border_radius is not None for rod in group.rods))
        self.fire(self.groups.controls[0].controls[2].controls[4], "on_click")
        self.fire(self.groups.controls[0].controls[2].controls[4], "on_click")
        self.assertEqual(group.rods, [])
        self.add_rod(0)
        self.assertEqual(len(group.rods), 1)

    def test_save_reload_preserves_groups_rods_and_expansion(self):
        self.fire(self.add_group, "on_click")
        tile = self.groups.controls[0]
        tile.expanded = False
        self.fire(tile, "on_change")
        with tempfile.TemporaryDirectory() as directory:
            self.widget.data.update(id="chart", title="Chart", directory_path=directory)
            asyncio.run(self.widget.save_file())
            saved = json.loads((Path(directory) / "chart.json").read_text(encoding="utf-8"))
        self.widget.data = saved
        self.widget.build()
        reloaded = self.widget.sidebar_body.controls[-4]
        self.assertFalse(reloaded.controls[0].expanded)
        self.assertEqual(len(saved["chart_data"]["groups"][0]["rods"]), 1)
        self.fire(reloaded.controls[0].controls[1].controls[1], "on_click")
        self.assertEqual(len(saved["chart_data"]["groups"][0]["rods"]), 2)


if __name__ == "__main__":
    unittest.main()
