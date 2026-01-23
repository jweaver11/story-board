from models.views.story import Story
from utils.safe_string_checker import return_safe_name

# Called to check if our widget titles are unique
def check_widget_unique(story: Story, new_key: str) -> tuple[str, bool]:
    """
    Check if the given widget is unique within the story.
    """

    for w in story.widgets:
        #print(
            #f"{return_safe_name(w.data.get('key', '')).lower()} \n{return_safe_name(new_key).lower()}\n\n\n"
        #)
    
        if return_safe_name(w.data.get('key', '')).lower() == return_safe_name(new_key).lower():
            return f"Title must be unique.", False
        
        
        
    if new_key.endswith("World Building") or new_key.endswith("Family Tree View"):
        return "Reserved title, please choose another.", False


    return "", True 