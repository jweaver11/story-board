import asyncio
import base64
import inspect
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, PropertyMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("FLET_APP_STORAGE_DATA", tempfile.gettempdir())

import flet as ft
import flet_shadcn_ui as shad

from models.widget import Widget
from models.widgets.template import Template


class TemplateTests(unittest.TestCase):
    def setUp(self):
        self.page = SimpleNamespace(
            platform=SimpleNamespace(is_mobile=lambda: False),
            show_dialog=Mock(), pop_dialog=Mock(),
        )
        self.widget = Template.__new__(Template)
        ft.Container.__init__(self.widget, data={
            'section_data': {'First': {'Shared': 'one'}, 'Second': {'Shared': 'two'}},
            'additional_images': [],
        })
        self.widget.needs_file_write = False
        self.widget.description_tf = ft.TextField()
        self.widget.select_image_button = ft.Text('Thumbnail')
        for target in (
            patch.object(Widget, 'build'),
            patch.object(ft.Control, 'update'),
            patch.object(Template, 'page', new_callable=PropertyMock, return_value=self.page),
        ):
            target.start()
            self.addCleanup(target.stop)
        self.widget.build()

    def controls(self):
        tabs = self.widget.content
        header, views = tabs.content.controls
        overview = views.controls[0]
        return tabs, header, views, overview

    def test_editing_duplicate_fields_keeps_sections_and_views_in_sync(self):
        _, _, views, overview = self.controls()
        overview_field = overview.controls[2].controls[1].controls[1].content.controls[1]
        section_field = views.controls[2].controls[0].controls[0].content.controls[1]
        overview_field.value = 'changed'
        overview_field.on_blur(SimpleNamespace(control=overview_field))
        self.assertEqual(self.widget.data['section_data']['First']['Shared'], 'one')
        self.assertEqual(self.widget.data['section_data']['Second']['Shared'], 'changed')
        self.assertEqual(section_field.value, 'changed')
        section_field.value = 'section edit'
        section_field.on_blur(SimpleNamespace(control=section_field))
        self.assertEqual(overview_field.value, 'section edit')

    def test_add_and_confirm_delete_section_updates_tabs_and_persists(self):
        tabs, header, views, _ = self.controls()
        self.assertIsInstance(header.controls[0].content.controls[1], ft.Container)
        self.assertIsInstance(header.controls[0].content.controls[2], shad.ContextMenu)
        new_section = header.controls[2]
        new_section.value = 'New Section'
        asyncio.run(new_section.on_submit(None))
        self.assertIn('New Section', self.widget.data['section_data'])
        self.assertEqual(tabs.length, 4)
        self.assertEqual(len(views.controls), 4)

        tabs.selected_index = 3
        menu = header.controls[0].content.controls[2]
        menu.items[0].on_click(None)
        self.assertIn('Second', self.widget.data['section_data'])
        dialog = self.page.show_dialog.call_args.args[0]
        dialog.actions[1].on_click(None)
        self.assertNotIn('Second', self.widget.data['section_data'])
        self.assertEqual(tabs.length, 3)
        self.assertEqual(tabs.selected_index, 2)
        self.assertEqual(len(views.controls), 3)
        with tempfile.TemporaryDirectory() as directory:
            self.widget.data.update(id='template', title='Template', directory_path=directory)
            asyncio.run(self.widget.save_file())
            saved = json.loads((Path(directory) / 'template.json').read_text(encoding='utf-8'))
        self.assertNotIn('Second', saved['section_data'])
        self.assertIn('New Section', saved['section_data'])

    def test_add_and_delete_field_updates_both_views(self):
        _, _, views, overview = self.controls()
        new_field = views.controls[1].controls[1].controls[1]
        new_field.value = 'Role'
        asyncio.run(new_field.on_submit(SimpleNamespace(control=new_field)))
        self.assertIn('Role', self.widget.data['section_data']['First'])
        self.assertEqual(len(overview.controls[2].controls[0].controls), 3)
        self.assertEqual(len(views.controls[1].controls[0].controls), 2)
        card = views.controls[1].controls[0].controls[1]
        card.content.controls[0].controls[1].on_click(None)
        self.assertNotIn('Role', self.widget.data['section_data']['First'])
        self.assertEqual(len(overview.controls[2].controls[0].controls), 2)

    def test_add_replace_remove_and_limit_images(self):
        _, _, _, overview = self.controls()
        gallery = overview.controls[0].controls[1]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'image.png'
            path.write_bytes(b'image')
            picker = SimpleNamespace(pick_files=AsyncMock(return_value=[SimpleNamespace(path=str(path))]))
            with patch('models.widgets.template.ft.FilePicker', return_value=picker):
                self.assertTrue(inspect.iscoroutinefunction(gallery.controls[0].items[0].on_click))
                for _ in range(4):
                    asyncio.run(gallery.controls[-1].items[0].on_click(None))
                self.assertEqual(len(self.widget.data['additional_images']), 4)
                self.assertEqual(len(gallery.controls), 4)
                path.write_bytes(b'replacement')
                asyncio.run(gallery.controls[1].items[0].on_click(None))
                self.assertEqual(self.widget.data['additional_images'][1], base64.b64encode(b'replacement').decode())
                gallery.controls[1].items[1].on_click(None)
                self.assertEqual(len(self.widget.data['additional_images']), 3)
                self.assertEqual(len(gallery.controls), 4)

    def test_image_read_error_is_reported_without_changing_images(self):
        _, _, _, overview = self.controls()
        gallery = overview.controls[0].controls[1]
        picker = SimpleNamespace(pick_files=AsyncMock(return_value=[SimpleNamespace(path=None)]))
        with patch('models.widgets.template.ft.FilePicker', return_value=picker):
            asyncio.run(gallery.controls[0].items[0].on_click(None))
        self.assertEqual(self.widget.data['additional_images'], [])
        self.assertIsInstance(self.page.show_dialog.call_args.args[0], shad.Toast)

    def test_empty_sections_and_list_fields_render(self):
        self.widget.data['section_data'] = {}
        self.widget.build()
        tabs, header, views, _ = self.controls()
        self.assertEqual(tabs.length, 1)
        self.assertEqual(header.controls[0].content.controls[0].content.value, 'Overview')
        self.widget.data['section_data'] = {'First': {'List': ['a']}}
        self.widget.build()
        _, _, views, overview = self.controls()
        self.assertEqual(overview.controls[2].controls[0].controls[1].content.controls[1].value, 'Coming soon')
        self.assertEqual(views.controls[1].controls[0].controls[0].content.controls[1].value, 'Coming soon')

    def test_section_layout_and_tab_selection(self):
        self.widget.data['section_data']['Third'] = {'Another': ''}
        self.widget.build()
        tabs, header, views, overview = self.controls()
        tab_controls = header.controls[0].content.controls
        self.assertIsInstance(tab_controls[2], shad.ContextMenu)
        self.assertIsInstance(tab_controls[2].content, ft.Container)
        tab_controls[2].content.on_click(None)
        self.assertEqual(tabs.selected_index, 2)
        self.assertEqual(tab_controls[2].content.bgcolor, ft.Colors.SURFACE)
        self.assertEqual(tab_controls[0].bgcolor, ft.Colors.TRANSPARENT)
        tab_controls[3].content.on_click(None)
        self.assertEqual(tabs.selected_index, 3)
        self.assertEqual(tab_controls[3].content.bgcolor, ft.Colors.SURFACE)
        tabs.selected_index = 1
        tabs.on_change(SimpleNamespace(control=tabs))
        self.assertEqual(tab_controls[1].bgcolor, ft.Colors.SURFACE)

        section = views.controls[2]
        fields, actions = section.controls
        self.assertTrue(fields.wrap)
        self.assertEqual(fields.controls[0].width, 400)
        self.assertEqual(fields.controls[0].max_width, 400)
        self.assertEqual(actions.controls[0].content, 'New Field')
        self.assertIsNotNone(actions.controls[0].leading)
        self.assertIs(overview.controls[0].controls[0], self.widget.select_image_button)
        gallery = overview.controls[0].controls[1]
        self.assertTrue(gallery.wrap)
        self.assertEqual(gallery.width, 260)

    def test_flat_item_fields_are_migrated_without_losing_existing_sections(self):
        self.widget.data = {
            'tag': 'item',
            'section_data': {'Basic': {'Type': 'sword'}, 'Rarity': 'rare'},
        }
        self.widget.build()
        self.assertEqual(self.widget.data['section_data'], {
            'Basic': {'Type': 'sword', 'Rarity': 'rare'},
        })
        self.assertTrue(self.widget.needs_file_write)
        _, _, views, _ = self.controls()
        self.assertEqual(len(views.controls), 2)

    def test_new_widgets_use_independent_type_specific_templates(self):
        settings = {'item_template': {'Name': 'ring'}, 'world_template': {'Places': {'City': ''}}}

        def init_widget(widget, **kwargs):
            ft.Container.__init__(widget, data={})
            widget.is_new = True

        with patch.object(Widget, '__init__', init_widget), patch(
            'models.widgets.template.app.settings', SimpleNamespace(data=settings)
        ):
            item = Template('Item', '', None, {'tag': 'item'}, True)
            world = Template('World', '', None, {'tag': 'world'}, True)
        self.assertEqual(item.data['section_data'], {'Basic': {'Name': 'ring'}})
        world.data['section_data']['Places']['City'] = 'Changed'
        self.assertEqual(settings['world_template']['Places']['City'], '')


if __name__ == '__main__':
    unittest.main()
