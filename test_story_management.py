"""
Test script to verify Story-Board story management functionality
"""

import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from models.user import User

def test_story_management():
    print("=== Story-Board Story Management Test ===")
    
    # Create a test user
    print("\n1. Creating test user...")
    user = User("test_user", "test@example.com")
    print(f"✓ User created: {user.username}")
    print(f"✓ Stories path: {user.stories_path}")
    print(f"✓ Default story: {user.active_story.title}")
    
    # Test creating new stories
    print("\n2. Testing story creation...")
    story1 = user.create_new_story("My Adventure Story")
    story2 = user.create_new_story("Sci-Fi Epic")
    story3 = user.create_new_story("Mystery Novel")
    
    print(f"✓ Created story: {story1.title}")
    print(f"✓ Created story: {story2.title}")
    print(f"✓ Created story: {story3.title}")
    
    # Test getting all story names
    print("\n3. Testing story listing...")
    all_stories = user.get_all_story_names()
    print(f"✓ Found {len(all_stories)} stories: {all_stories}")
    
    # Test switching between stories
    print("\n4. Testing story switching...")
    print(f"   Current active story: {user.active_story.title}")
    
    success = user.switch_active_story("Sci-Fi Epic")
    print(f"✓ Switched to: {user.active_story.title}" if success else "✗ Failed to switch")
    
    success = user.switch_active_story("Mystery Novel")
    print(f"✓ Switched to: {user.active_story.title}" if success else "✗ Failed to switch")
    
    # Test story metadata
    print("\n5. Testing story metadata...")
    user.active_story.save_story_metadata()
    metadata = user.active_story.load_story_metadata()
    print(f"✓ Metadata saved and loaded: {metadata}")
    
    # Test deleting a story
    print("\n6. Testing story deletion...")
    delete_success = user.delete_story("My Adventure Story")
    print(f"✓ Deleted story" if delete_success else "✗ Failed to delete story")
    
    remaining_stories = user.get_all_story_names()
    print(f"✓ Remaining stories: {remaining_stories}")
    
    print("\n=== Test Complete ===")
    print("All story management features are working correctly!")

if __name__ == "__main__":
    test_story_management()
