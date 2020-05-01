import json
try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources

urls = json.loads(pkg_resources.read_text(__name__, 'urls.json'))