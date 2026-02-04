# Simple class for connections between characters
from dataclasses import dataclass


@dataclass
class ConnectionDataClass:
    char1_key: str = ""                         # Character keys of the two characters in the connection
    char2_key: str = ""           
    char1_name: str = ""                        # Cached names of the two characters for easier identification
    char2_name: str = ""      
    type: str = "character"                     # Type of connection. character, world-timeline. Just character for now
    tags: str = None                            # Comma separated tags (friend, sibling, classmate, rival, etc)
    color: str = "primary"                      # Color name for connection representation
    icon: str = "connect_without_contact"       # Icon name for connection representation
    left: int = None                            # Absolute x position on a stack
    top: int = None                             # Absolute y position on a stack
    angle: int = None                           # Angle around primary character (1-360)
