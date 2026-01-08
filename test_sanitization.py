
import os
import re

def sanitize_filename(name):
    # Retrieve the filename if it is a path
    name = os.path.basename(name)
    # Remove invalid characters on Windows
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Strip whitespace
    name = name.strip()
    return name

test_filenames = [
    "S01_E24_Sword_of_the_Demon_Hunter:_Kijin_Gentosho_480p_SUB_@animetelugu.mkv",
    "normal_file.mp4",
    "file/with/slashes.mkv",
    "file*star?.mp4",
    "  spaces  .mp4"
]

for name in test_filenames:
    sanitized = sanitize_filename(name)
    print(f"Original: '{name}' -> Sanitized: '{sanitized}'")
    # Verify it doesn't contain invalid chars
    if any(c in sanitized for c in '<>:"/\\|?*'):
        print(f"FAILED: {sanitized} contains invalid characters")
    else:
        print("PASSED")
