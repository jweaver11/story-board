from models.views.story import Story
from models.widget import Widget

# Called to check if our widget titles are unique
def check_widget_unique(story: Story, new_key: str) -> tuple[str, bool]:
    """
    Check if the given widget is unique within the story.
    """
    for w in story.widgets:
        #print("Checking uniqueness for key:", new_key, "\nagainst existing key:", w.data.get('key', ''))
        if w.data.get('key', '') == new_key:
            return f"Title must be unique.", False
        
    if new_key.endswith("World Building") or new_key.endswith("Family Tree View"):
        return "Reserved title, please choose another.", False


    return "", True 