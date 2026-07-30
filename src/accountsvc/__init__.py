"""accountsvc - user account microservice."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("accountsvc")
except PackageNotFoundError:  # pragma: no cover - only hit in uninstalled dev trees
    __version__ = "0.0.0"

__all__ = ["__version__"]
