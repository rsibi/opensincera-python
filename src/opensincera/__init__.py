from importlib.metadata import version as _version

__all__ = ["__version__"]

__version__ = _version("opensincera-python")


def hello() -> str:
    return "Hello from opensincera!"
