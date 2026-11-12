from copy import deepcopy

from models.dataclasses.character_template import default_character_template_data
from models.dataclasses.item_template import default_item_template_data
from models.dataclasses.world_template import default_world_template_data


TEMPLATE_DEFAULTS = {
    "character": default_character_template_data,
    "world": default_world_template_data,
    "item": default_item_template_data,
}


def get_template(settings: dict, widget_type: str):
    key = f"{widget_type}_template"
    if key not in settings:
        legacy = settings.get(f"{widget_type}_templates", {})
        active = settings.get(f"active_{widget_type}_template")
        template = legacy.get(active, legacy.get("Default"))
        if isinstance(template, dict) and "title" in template and "template_data" in template:
            template = template["template_data"]
        if template is None:
            template = TEMPLATE_DEFAULTS[widget_type]()
        settings[key] = deepcopy(template)
        if widget_type != "item":
            for section, fields in settings[key].items():
                if not isinstance(fields, dict):
                    settings[key][section] = {}
    return settings[key]
