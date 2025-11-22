import lk21
import urllib.parse

# Monkey Patch to ignore invalid URLs in lk21
original_urlparse = urllib.parse.urlparse

def safe_urlparse(url, *args, **kwargs):
    try:
        return original_urlparse(url, *args, **kwargs)
    except ValueError:
        # return empty parsed URL instead of crashing
        return original_urlparse("http://invalid.com")

urllib.parse.urlparse = safe_urlparse
