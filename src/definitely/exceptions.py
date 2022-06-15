class DefinitelyAnError(Exception):
    """
    A base exception for the others to inherit from.
    """

    pass


class InvalidState(DefinitelyAnError):
    """
    Raised when an unknown state is attempted to be transitioned to.
    """

    pass


class TransitionNotAllowed(DefinitelyAnError):
    """
    Raised when the provide state is not allowed to be transitioned to.
    """

    pass


class InvalidHandler(DefinitelyAnError):
    """
    Raised when a `handle_*` attribute is present, but can not be called.
    """

    pass


class InvalidDefaultState(DefinitelyAnError):
    """
    Raised when no default state has been specified on a FSM subclass.
    """

    pass


class NoStatesDefined(DefinitelyAnError):
    """
    Raised when no states/transitions have been specified on a FSM subclass.
    """

    pass
