''' 
Master Story class that contains data and methods for the entire story 
This is a dead-end model. Imports nothing else from project, or things will ciruclar import
'''

import flet as ft
import os
import pickle

class Story:
    # Constructor for when new story is created
    def __init__(self, title: str, file_path: str):
       
        self.title=title # Gives our story a title when its created
        self.file_path=file_path  # Gives us a path to save/load the story

        # Create the directory structure if it doesn't exist
        os.makedirs(self.file_path, exist_ok=True)
        for folder in ["characters", "notes", "pins", "plotlines", "scenes"]:
            os.makedirs(os.path.join(self.file_path, folder), exist_ok=True)


        self.top_pin = ft.Row(height=0, spacing=0, controls=[])
        self.left_pin = ft.Column(width=0, spacing=0, controls=[])
        self.main_pin = ft.Row(expand=True, spacing=0, controls=[])
        self.right_pin = ft.Column(width=0, spacing=0, controls=[])
        self.bottom_pin = ft.Row(height=0, spacing=0, controls=[])

        # Our master row that holds all our widgets
        self.widgets = ft.Row(spacing=0, expand=True, controls=[])

        # Master stack that holds our widgets
        # And our drag targets when we start dragging widgets.
        # We do this so there is a receiver (drag target) for the widget even if a pin is empty and hidden
        self.master_stack = ft.Stack(expand=True, controls=[self.widgets])


        # Default active workspace rail if none selected/on startup rn
        self.default_rail = [ft.TextButton("Select a workspace")]

        # Map of all the workspace rails - Rails must be a list of flet controls
        self.workspace_rails = {
            0: self.default_rail,
        }  

        # Format our active rail 
        self.active_rail = ft.Column(  
            spacing=0,
            controls=self.workspace_rails[0],    # On startup, set to char rail
        )  

        # Make a list for positional indexing
        self.characters = []    # Dict of character object. Used for storing/deleting characters
        
        # Store page reference for loading objects later
        self.page_reference = None


    def load_story_objects(self):
        print("load story objects called")
        # Load all our objects from our story file.
        
        # Load characters
        characters_path = os.path.join(self.file_path, "characters")
        if os.path.exists(characters_path):
            for filename in os.listdir(characters_path):
                if filename.endswith('.pkl'):
                    character_path = os.path.join(characters_path, filename)
                    character_data = self.load_object_from_file(character_path, self.page_reference)
                    if character_data:
                        # Check if this is serializable character data or an old character object
                        if isinstance(character_data, dict) and 'tag' in character_data and character_data['tag'] == 'character':
                            # This is serialized character data, we need to recreate the character
                            # For now, just store the data - we'll recreate the character when page is available
                            self.characters.append(character_data)
                            print(f"Loaded character data: {character_data['title']}")
                        elif hasattr(character_data, 'title'):
                            # This is an old character object
                            self.characters.append(character_data)
                            print(f"Loaded character object: {character_data.title}")
        
        # Load pins layout if it exists
        pins_path = os.path.join(self.file_path, "pins")
        if os.path.exists(pins_path):
            for pin_name in ["top_pin", "left_pin", "main_pin", "right_pin", "bottom_pin"]:
                pin_file = os.path.join(pins_path, f"{pin_name}.pkl")
                if os.path.exists(pin_file):
                    try:
                        pin_data = self.load_object_from_file(pin_file, self.page_reference)
                        if pin_data and hasattr(self, pin_name):
                            # Check if the loaded data is a proper Flet control
                            if hasattr(pin_data, 'controls'):
                                setattr(self, pin_name, pin_data)
                                print(f"Loaded pin: {pin_name}")
                            else:
                                print(f"Invalid pin data for {pin_name}, keeping default")
                    except Exception as e:
                        print(f"Error loading pin {pin_name}: {e}")
                        # Keep the default pin that was created in __init__
        
        print(f"Loaded {len(self.characters)} characters for story: {self.title}")
    
    def save_story_metadata(self):
        """Save story metadata including title and other basic info"""
        try:
            import json
            metadata = {
                "title": self.title,
                "file_path": self.file_path,
                "character_count": len(self.characters),
                "created_at": getattr(self, 'created_at', None),
                "last_modified": getattr(self, 'last_modified', None)
            }
            
            metadata_file = os.path.join(self.file_path, "story_metadata.json")
            os.makedirs(os.path.dirname(metadata_file), exist_ok=True)
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Story metadata saved: {metadata_file}")
        except Exception as e:
            print(f"Error saving story metadata: {e}")
    
    def load_story_metadata(self):
        """Load story metadata from file"""
        try:
            import json
            metadata_file = os.path.join(self.file_path, "story_metadata.json")
            
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Update story properties from metadata
                self.title = metadata.get("title", self.title)
                self.created_at = metadata.get("created_at")
                self.last_modified = metadata.get("last_modified")
                
                print(f"Story metadata loaded: {self.title}")
                return metadata
            else:
                print("No metadata file found")
                return None
        except Exception as e:
            print(f"Error loading story metadata: {e}")
            return None
        


    # Add our created object to story. This will add it to any lists it should be in, pin location, etc.
    # All our story objects are extended flet containers, and require a title, pin location, tag,...
    def save_object(self, obj):
        print("Adding object in story: " + obj.title)

        # Runs to save our character to our story object, and save it to file
        def save_character(obj):
            print("save character called")

            path = os.path.join(self.file_path, "characters", f"{obj.title}.pkl")   # Sets our correct path
            self.characters.append(obj) # Saves 
            print(path)
            self.save_object_to_file(obj, path)

        # Is called when the parent f
        def save_chapter(obj):
            print("save chapter called")
            print(obj)


        # Checks our objects tag, then figures out what to do with it
        if hasattr(obj, 'tag'):
            # Characters
            if obj.tag == "character":
                save_character(obj)
            # Chapters
            elif obj.tag == "chapter":
                save_chapter(obj)
            
            else:
                print("object does not have a valid tag")


        # If no tag exists, we do nothing
        else:
            print("obj has no tag, did not save it")

        from handlers.arrange_widgets import arrange_widgets
        arrange_widgets()

    # Deletes an object from the story, and calls function to remove it from file
    def delete_object(self, obj):
        print("Removing object from story: " + obj.title)

        # Remove from characters list if it is a character
        if hasattr(obj, 'tag') and obj.tag == "character":
            # Check our characters pin location, and remove its reference from there
            if hasattr(obj, 'pin_location'):
                if obj.pin_location == "top":
                    self.top_pin.controls.remove(obj)
                elif obj.pin_location == "left":
                    self.left_pin.controls.remove(obj)
                elif obj.pin_location == "main":
                    self.main_pin.controls.remove(obj)
                elif obj.pin_location == "right":
                    self.right_pin.controls.remove(obj)
                elif obj.pin_location == "bottom":
                    self.bottom_pin.controls.remove(obj)
            
            # Remove object from the characters list
            if obj in self.characters:
                self.characters.remove(obj)
            
            # Delete the character file
            character_file = os.path.join(self.file_path, "characters", f"{obj.title}.pkl")
            self.delete_object_from_file(obj, character_file)


    # Called by the save_object method to save the object to file storage
    def save_object_to_file(self, obj, file_path):
        print("object saved to file called")
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # For characters, we need to handle the complex structure with Flet controls
            if hasattr(obj, 'tag') and obj.tag == "character":
                # Create a serializable representation of the character
                serializable_data = {
                    'title': obj.title,
                    'tag': obj.tag,
                    'pin_location': getattr(obj, 'pin_location', 'left'),
                    'name': getattr(obj, 'title', ''),  # Character name
                    'character_data': self._extract_serializable_character_data(obj),
                }
                
                # Save the serializable data
                with open(file_path, 'wb') as f:
                    pickle.dump(serializable_data, f)
                print(f"Character data saved successfully to: {file_path}")
            else:
                # For other objects, try regular pickling
                with open(file_path, 'wb') as f:
                    pickle.dump(obj, f)
                print(f"Object saved successfully to: {file_path}")
                
        except Exception as e:
            print(f"Error saving object to file: {e}")
    
    def _extract_serializable_character_data(self, character_obj):
        """Extract serializable data from a character object"""
        try:
            serializable_data = {}
            if hasattr(character_obj, 'character_data'):
                for key, value in character_obj.character_data.items():
                    if hasattr(value, 'value'):  # Flet control with a value attribute
                        serializable_data[key] = value.value
                    elif isinstance(value, dict):
                        serializable_data[key] = value
                    elif isinstance(value, str):
                        serializable_data[key] = value
                    elif isinstance(value, list):
                        serializable_data[key] = value
                    else:
                        # For complex Flet controls, extract what we can
                        serializable_data[key] = str(value) if value is not None else ""
            return serializable_data
        except Exception as e:
            print(f"Error extracting character data: {e}")
            return {}
        
    # Load an object from file
    def load_object_from_file(self, file_path, page_reference):
        print("load object from file called")
        try:
            if file_path and os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    obj = pickle.load(f)
                print(f"Object loaded successfully from: {file_path}")
                return obj
            else:
                print(f"File does not exist: {file_path}")
                return None
        except Exception as e:
            print(f"Error loading object from file: {e}")
            return None

    # Called by the delete object method to permanently remove the object from file storage as well
    def delete_object_from_file(self, obj, file_path):
        print("delete object from file called")
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Object file deleted successfully: {file_path}")
            else:
                print(f"File does not exist, cannot delete: {file_path}")
        except Exception as e:
            print(f"Error deleting object file: {e}")
    
    def save_pins_layout(self):
        """Save the current pin layout to files"""
        try:
            pins_path = os.path.join(self.file_path, "pins")
            os.makedirs(pins_path, exist_ok=True)
            
            pins_to_save = {
                "top_pin": self.top_pin,
                "left_pin": self.left_pin,
                "main_pin": self.main_pin,
                "right_pin": self.right_pin,
                "bottom_pin": self.bottom_pin
            }
            
            for pin_name, pin_obj in pins_to_save.items():
                pin_file = os.path.join(pins_path, f"{pin_name}.pkl")
                self.save_object_to_file(pin_obj, pin_file)
                
            print("Pins layout saved successfully")
        except Exception as e:
            print(f"Error saving pins layout: {e}")
    
    def recreate_character_objects(self, page_reference):
        """Recreate character objects from serialized data when page is available"""
        from models.character import Character
        recreated_characters = []
        
        for char_data in self.characters:
            if isinstance(char_data, dict) and 'tag' in char_data and char_data['tag'] == 'character':
                try:
                    # Create a new character object
                    character = Character(char_data['title'], page_reference)
                    
                    # Restore basic properties
                    character.pin_location = char_data.get('pin_location', 'left')
                    
                    # Restore character data where possible
                    if 'character_data' in char_data:
                        for key, value in char_data['character_data'].items():
                            if key in character.character_data:
                                if hasattr(character.character_data[key], 'value'):
                                    character.character_data[key].value = value
                                else:
                                    character.character_data[key] = value
                    
                    recreated_characters.append(character)
                    print(f"Recreated character: {character.title}")
                    
                except Exception as e:
                    print(f"Error recreating character {char_data.get('title', 'unknown')}: {e}")
                    # Keep the original data if recreation fails
                    recreated_characters.append(char_data)
            else:
                # This is already a character object or other data
                recreated_characters.append(char_data)
        
        self.characters = recreated_characters
        self.page_reference = page_reference
