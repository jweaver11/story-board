from models.views.story import Story
from models.widget import Widget

# Called to check if our widget titles are unique
def check_widget_unique(story: Story, widget: Widget) -> tuple[str, bool]:
    """
    Check if the given widget is unique within the story.
    """
    for w in story.widgets:
        if w.data.get('key', '') == widget.data.get('key', ''):
            return f"{widget.data.get('tag', 'Widget').capitalize()} must be unique.", False
        
    if widget.title == "World Building" or widget.title == "Family Tree View":
        return "Reserved title, please choose another.", False


    return "", True