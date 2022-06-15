from .fsm import FSM

__author__ = "Daniel Lindsley"
__license__ = "New BSD"
__version__ = (1, 0, 0, "alpha")


def get_version(full=False):
    """
    Returns the version information.

    Args:
        full (bool): Switches between short semver & the long/full version,
            including release information. Default is `False` (short).

    Returns:
        str: The version string
    """
    short_version = ".".join([str(bit) for bit in __version__[:3]])

    if not full:
        return short_version

    remainder = "-".join([str(bit) for bit in __version__[3:]])
    return f"{short_version}-{remainder}"


__all__ = ["FSM", "get_version", "__author__", "__license__", "__version__"]
