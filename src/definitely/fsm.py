from . import constants
from . import exceptions  # import InvalidState, TransitionNotAllowed


class FSM(object):
    """
    The base finite state machine class.

    In normal usage, you should subclass this class. In doing so, you must
    define your own `allowed_transitions` and `default_state` attributes on the
    subclass.

    Args:
        obj (Any): (Optional) An object to perform actions on as part of any
            transition handlers. For example, triggering a save on that
            object, updating that object's internal state, sending
            notifications about it, etc. Default is `None`.
        initial_state (str): The initial state the instance should start in.
            Default is `None` (use the `default_state`).
    """

    allowed_transitions = {}
    default_state = constants.UNKNOWN_STATE

    # For convenience, add the exceptions onto ourself, for easy raising &
    # catching.
    InvalidState = exceptions.InvalidState
    TransitionNotAllowed = exceptions.TransitionNotAllowed

    def __init__(self, obj=None, initial_state=None):
        self._state_names = []
        self.obj = obj
        self._current_state = self.default_state

        # Trigger all the setup/caching.
        self.setup()

        if initial_state is not None:
            if self.is_valid(initial_state):
                self._current_state = initial_state

    def setup(self):
        """
        A mostly-internal method for setting up required data.

        Can be used to re-trigger this build if you're doing something
        advanced/spicy.

        No arguments or return values.
        """
        if not len(self.allowed_transitions):
            raise exceptions.NoStatesDefined(
                f"'allowed_transitions' not defined on {self}"
            )

        if self.default_state == constants.UNKNOWN_STATE:
            raise exceptions.InvalidDefaultState(
                f"'default_state' not defined on {self}"
            )

        self._state_names = self.allowed_transitions.keys()

    @classmethod
    def from_json(cls, name, json_data):
        """
        Construct a new (sub)class, based on JSON data.

        Useful for storing states/transitions externally & loading them at
        runtime.

        Args:
            name (str): The desired (sub)class name.
            json_data (dict): A dictionary containing an `allowed_transitions`
                dictionary and a `default_state` key/value.

        Returns:
            FSM: A newly built subclass of FSM.
        """
        new_cls = type(
            name,
            (cls,),
            {
                "allowed_transitions": json_data.get("allowed_transitions", {}),
                "default_state": json_data.get("default_state", {}),
            },
        )
        return new_cls

    def current_state(self):
        """
        What state the FSM is currently in.

        Returns:
            str: The current state.
        """
        return self._current_state

    def all_states(self):
        """
        All the valid state names for the FSM.

        Returns:
            list: All the state names.
        """
        return sorted(self._state_names)

    def is_valid(self, state_name):
        """
        Identifies if the provided state name is a recognized/valid name.

        Args:
            state_name (str): The name to check.

        Returns:
            bool: If it's valid, returns True. Otherwise, returns False.
        """
        return state_name in self._state_names

    def is_allowed(self, state_name):
        """
        From the current state, identifies if transitioning to the provided
        state name is allowed.

        Args:
            state_name (str): The state to transition to.

        Returns:
            bool: If the transition would be allowed, returns True. Otherwise,
                returns False.
        """
        current_state = self.current_state()
        available_transitions = self.allowed_transitions.get(current_state, None)

        if available_transitions is None:
            available_transitions = []

        return state_name in available_transitions

    def _call_handler(self, handler_name, state_name):
        handle_specific = getattr(self, handler_name, None)

        if handle_specific is not None:
            if not callable(handle_specific):
                raise exceptions.InvalidHandler(
                    f"The '{handler_name}' attribute is not callable"
                )

            return handle_specific(state_name)

    def transition_to(self, state_name):
        """
        Triggers a state transition to the provided state name.

        If the special `handle_any` method is defined on the FSM subclass, it
        will *always* be called, regardless of what state name is provided.

        If a `handle_<state_name>` method is defined on the FSM subclass, it
        will be called.

        Args:
            state_name (str): The state to transition to.

        Returns:
            None

        Raises:
            InvalidState: If the state name is invalid.
            TransitionNotAllowed: If the transition isn't allowed from the
                current state.
            InvalidHandler: If a handler is present on the FSM, but is not
                callable.
        """
        if not self.is_valid(state_name):
            raise self.InvalidState(f"'{state_name}' is not a recognized state.")

        if not self.is_allowed(state_name):
            raise self.TransitionNotAllowed(
                f"'{self.current_state()}' cannot transition to '{state_name}'"
            )

        # The state transition is allowed.
        # Check & run for the `handle_any` method first, ...
        handle_any = "handle_any"
        self._call_handler(handle_any, state_name)

        # ...then the specific `handle_<state_name>` method.
        handler_name = f"handle_{state_name}"
        self._call_handler(handler_name, state_name)

        # Finally, we update our internal state.
        self._current_state = state_name
