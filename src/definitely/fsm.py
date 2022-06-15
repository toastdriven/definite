from . import constants
from . import exceptions  # import InvalidState, TransitionNotAllowed


class FSM(object):
    allowed_transitions = {}
    default_state = constants.UNKNOWN_STATE

    # For convenience, add the exceptions onto ourself, for easy raising &
    # catching.
    InvalidState = exceptions.InvalidState
    TransitionNotAllowed = exceptions.TransitionNotAllowed

    def __init__(self, initial_state=None):
        self._state_names = []
        self._current_state = self.default_state

        # Trigger all the setup/caching.
        self.setup()

        if initial_state is not None:
            if self.is_valid(initial_state):
                self._current_state = initial_state

    def setup(self):
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
        # Construct a new class based on the JSON data.
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
        return self._current_state

    def all_states(self):
        return sorted(self._state_names)

    def is_valid(self, state_name):
        return state_name in self._state_names

    def is_allowed(self, state_name):
        current_state = self.current_state()
        available_transitions = self.allowed_transitions.get(current_state, None)

        if available_transitions is None:
            available_transitions = []

        return state_name in available_transitions

    def _call_handler(self, handler_name, state_name, obj=None):
        handle_specific = getattr(self, handler_name, None)

        if handle_specific is not None:
            if not callable(handle_specific):
                raise exceptions.InvalidHandler(
                    f"The '{handler_name}' attribute is not callable"
                )

            return handle_specific(state_name, obj)

    def transition_to(self, state_name, obj=None):
        if not self.is_valid(state_name):
            raise self.InvalidState(f"'{state_name}' is not a recognized state.")

        if not self.is_allowed(state_name):
            raise self.TransitionNotAllowed(
                f"'{self.current_state()}' cannot transition to '{state_name}'"
            )

        # The state transition is allowed.
        # Check & run for the `handle_any` method first, ...
        handle_any = "handle_any"
        self._call_handler(handle_any, state_name, obj)

        # ...then the specific `handle_<state_name>` method.
        handler_name = f"handle_{state_name}"
        self._call_handler(handler_name, state_name, obj)

        # Finally, we update our internal state.
        self._current_state = state_name
