class DefinitelyAnError(Exception):
    pass


class InvalidState(DefinitelyAnError):
    pass


class TransitionNotAllowed(DefinitelyAnError):
    pass


class InvalidHandler(DefinitelyAnError):
    pass


class InvalidDefaultState(DefinitelyAnError):
    pass


class NoStatesDefined(DefinitelyAnError):
    pass
