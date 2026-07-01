from models.views.story import Story
from utils.safe_string_checker import return_safe_name

# Called to check if our widget titles are unique
def check_widget_unique(story: Story, new_key: str) -> tuple[str, bool]:
    """
    Check if the given widget is unique within the story.
    """

    for w in story.widgets:
        if return_safe_name(w.data.get('key', '')).lower() == return_safe_name(new_key).lower():
            return f"Title must be unique.", False
 
    return "", True 