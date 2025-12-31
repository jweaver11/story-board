import re
import unicodedata

# Called when creating data that needs to be normalized, like directory names, file_names, JSON keys, etc.
def return_safe_name(text: str, prefix="item_") -> str:
    """ Sanitizes the string and returns the safe version of it """
    
    if not text:
        return prefix + "0"
    
    # Normalize unicode (remove accents, etc.)
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    
    # Remove/replace invalid chars
    # For files/folders/JSON keys: no / \ : * ? " < > | and control chars
    text = re.sub(r'[<>:"/\\|?*\x00-\x1F\x7F]', '_', text)
    
    # JSON values are more permissive but collapse multiple spaces/control chars
    text = re.sub(r'[\x00-\x1F\x7F]+', '', text)
    
    # Trim and limit length (filesystem safe)
    text = text.strip().strip('_')
    if len(text) > 255:
        text = text[:252] + "..."
    
    # If empty after sanitizing, use prefix
    return prefix + re.sub(r'[^a-zA-Z0-9_-]', '_', text) if not text else text
