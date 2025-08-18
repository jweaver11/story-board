'''
Our user of the application. This model stores their info and certain UI elements,
and their stories. It is a dead end file, that only imports the story model.
All other files can import the user variable
'''
from models.story import Story
import flet as ft
import os

class User:
    def __init__(self, username: str, email: str):
        # Email and Username
        self.username = username
        self.email = email

        # Saving objects locally - Create project structure
        self.app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
        
        # If FLET_APP_STORAGE_DATA is not set, use a default path
        if self.app_data_path is None:
            # Use the storage directory in the project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.app_data_path = os.path.join(project_root, "storage", "data")
        
        print(f"Using app data path: {self.app_data_path}")
        
        # Create main project structure
        self.stories_path = os.path.join(self.app_data_path, "stories")
        self.settings_path = os.path.join(self.app_data_path, "settings")
        # Makes our initial default story the active one on creation
        self.active_story_path = os.path.join(self.stories_path, "default_story") 
        
        # Create directories if they don't exist
        os.makedirs(self.stories_path, exist_ok=True)
        os.makedirs(self.settings_path, exist_ok=True)
        
        # Create empty_story folder structure
        #self.default_story_path = os.path.join(self.stories_path, "empty_story")
        #os.makedirs(self.default_story_path, exist_ok=True)
        
        # Create Story object structure folders inside empty_story
        story_folders = [
            "characters",
            "notes",
            "pins",
            "plotlines",
            "scenes", 
            #"settings",
        ]
        
        # Creates our folders in the active story path
        for folder in story_folders:
            folder_path = os.path.join(self.active_story_path, folder)
            os.makedirs(folder_path, exist_ok=True)
        
        # Create story metadata file
        self.story_metadata_path = os.path.join(self.active_story_path, "story_info.json")

        # initialize the settings, before creating them in main
        # Also an extended flet container, so it shows up in the pins
        
        # Sets our settings to empty, and we create them in main.py since we need page reference
        self.settings = None 
        
        # Dict of all our stories. Starts empty and we'll load them
        self.stories = {}

        # Initialize default story if it doesn't exist
        if not os.path.exists(self.active_story_path):
            self.create_new_story("default_story")
        else:
            # Load the default story
            self.load_existing_story("default_story")
        
        # The selected story. Many part of the program call this selection
        self.active_story = self.stories.get('default_story')  # Default to default story

        # Saves our all_workspaces_rail to the user so it will always look how it was before closing the app
        # Saves their reorder, if collapsed or not, etc.
        # Main builds the actual rail, but it is an extended flet container
        self.all_workspaces_rail = ft.Container()

        self.workspace = ft.Container()


    def create_new_story(self, title: str):
        print("Create new story called")
        
        # Check if story already exists
        if title in self.stories:
            print(f"Story '{title}' already exists")
            return self.stories[title]
        
        # Create story directory path
        story_path = os.path.join(self.stories_path, title)
        
        # Create story folders if they don't exist
        story_folders = [
            "characters",
            "notes", 
            "pins",
            "plotlines",
            "scenes",
        ]
        
        for folder in story_folders:
            folder_path = os.path.join(story_path, folder)
            os.makedirs(folder_path, exist_ok=True)
        
        # Create a new story object and add it to our stories dict
        new_story = Story(title, story_path)
        new_story.save_story_metadata()  # Save metadata file
        
        self.stories[title] = new_story
        
        print(f"Created new story: {title}")
        return new_story

    def load_existing_story(self, title: str):
        """Load an existing story from the file system"""
        print(f"Loading existing story: {title}")
        
        story_path = os.path.join(self.stories_path, title)
        
        if not os.path.exists(story_path):
            print(f"Story path does not exist: {story_path}")
            return None
        
        # Create story object
        story = Story(title, story_path)
        
        # Load metadata
        story.load_story_metadata()
        
        # Load story objects (characters, etc.)
        story.load_story_objects()
        
        # Add to stories dict
        self.stories[title] = story
        
        print(f"Successfully loaded story: {title}")
        return story

    def get_all_story_names(self):
        """Get a list of all story names in the stories directory"""
        story_names = []
        try:
            if os.path.exists(self.stories_path):
                for item in os.listdir(self.stories_path):
                    story_dir = os.path.join(self.stories_path, item)
                    if os.path.isdir(story_dir):
                        # Check if it looks like a story directory (has expected folders)
                        expected_folders = ["characters", "notes", "pins", "plotlines", "scenes"]
                        if any(os.path.exists(os.path.join(story_dir, folder)) for folder in expected_folders):
                            story_names.append(item)
            return story_names
        except Exception as e:
            print(f"Error getting story names: {e}")
            return []

    def switch_active_story(self, story_title: str):
        """Switch to a different story as the active story"""
        print(f"Switching to story: {story_title}")
        
        # Load the story if it's not already loaded
        if story_title not in self.stories:
            story = self.load_existing_story(story_title)
            if not story:
                print(f"Failed to load story: {story_title}")
                return False
        
        # Set as active story
        self.active_story = self.stories[story_title]
        self.active_story_path = self.active_story.file_path
        
        print(f"Active story switched to: {story_title}")
        return True

    def delete_story(self, story_title: str):
        """Delete a story and its files"""
        print(f"Deleting story: {story_title}")
        
        if story_title == "default_story":
            print("Cannot delete the default story")
            return False
        
        try:
            # Remove from stories dict
            if story_title in self.stories:
                del self.stories[story_title]
            
            # Delete the story directory
            import shutil
            story_path = os.path.join(self.stories_path, story_title)
            if os.path.exists(story_path):
                shutil.rmtree(story_path)
            
            # If this was the active story, switch to default
            if self.active_story.title == story_title:
                self.switch_active_story("default_story")
            
            print(f"Successfully deleted story: {story_title}")
            return True
        except Exception as e:
            print(f"Error deleting story: {e}")
            return False

    # Called when we switch to another story
    # Switches our file path to the new story
    def set_active_story_path(self, story: Story):
        story_title = story.title
        
        print("Set active story path called")
        if os.path.exists(story.file_path):
            self.active_story_path = story.file_path
            self.active_story = story
            print(f"Active story path set to: {self.active_story_path}")
        else:
            print(f"Path does not exist: {story.file_path}")


    def __repr__(self):
        return f"User(username={self.username}, email={self.email})"

    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        return self.username == other.username and self.email == other.email
    


def load_user(username: str, email: str) -> User:
    # Check our user path. Active user variable??
    # If there is an active user, load them
    # Else, create a new user

    print("load user called")
    return create_user(username, email)

def create_user(username: str, email: str) -> User:
    user = User(username, email)
    return user



user = load_user("exp_user", "exp_email")