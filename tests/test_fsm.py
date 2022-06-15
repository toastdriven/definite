from unittest import mock

import pytest

from definitely import exceptions
from definitely.fsm import FSM


class BasicFlow(FSM):
    allowed_transitions = {
        "created": ["waiting"],
        "waiting": ["in_progress", "done"],
        "in_progress": ["waiting", "done"],
        "done": None,
    }
    default_state = "created"


class ComplexFlow(FSM):
    allowed_transitions = {
        "created": ["waiting"],
        "waiting": ["in_progress", "done"],
        "in_progress": ["waiting", "done"],
        "done": None,
    }
    default_state = "created"

    def handle_any(self, desired_state, obj=None):
        pass

    def handle_in_progress(self, desired_state, obj=None):
        pass


def test_empty_init():
    # If you use it without subclassing.
    with pytest.raises(exceptions.NoStatesDefined):
        fsm = FSM()

    # If you subclass but don't provide a default state.
    class JustTransitions(FSM):
        allowed_transitions = {
            "start": ["end"],
            "end": None,
        }

    with pytest.raises(exceptions.InvalidDefaultState):
        fsm = JustTransitions()


def test_init_and_setup():
    basic = BasicFlow()
    assert basic.allowed_transitions == {
        "created": ["waiting"],
        "waiting": ["in_progress", "done"],
        "in_progress": ["waiting", "done"],
        "done": None,
    }
    assert basic.default_state == "created"
    assert len(basic._state_names) > 0


def test_initial_state():
    basic = BasicFlow("waiting")
    assert basic._current_state == "waiting"


def test_current_state():
    basic = BasicFlow()
    assert basic.current_state() == "created"


def test_all_states():
    basic = BasicFlow()
    assert basic.all_states() == ["created", "done", "in_progress", "waiting"]


def test_is_valid():
    basic = BasicFlow()
    assert basic.is_valid("created")
    assert basic.is_valid("waiting")
    assert basic.is_valid("in_progress")
    assert basic.is_valid("done")

    # And invalid state names.
    assert basic.is_valid("nopenopenope") == False


def test__call_handler():
    class WithHandler(BasicFlow):
        def handle_waiting(self, state_name, obj=None):
            # We'll observe this with `mock`.
            pass

    fsm = WithHandler()

    with mock.patch.object(fsm, "handle_waiting") as mock_handler:
        fsm._call_handler("handle_waiting", "waiting")
        # It should find & call the correct handler method.
        mock_handler.assert_called_once_with("waiting", None)


def test_transition_to_basic():
    fsm = BasicFlow()
    assert fsm.current_state() == "created"

    fsm.transition_to("waiting")
    assert fsm.current_state() == "waiting"

    fsm.transition_to("in_progress")
    assert fsm.current_state() == "in_progress"

    fsm.transition_to("waiting")
    assert fsm.current_state() == "waiting"

    fsm.transition_to("done")
    assert fsm.current_state() == "done"


def test_transition_to_not_allowed():
    fsm = BasicFlow()

    with pytest.raises(fsm.TransitionNotAllowed):
        fsm.transition_to("done")


def test_transition_to_invalid():
    fsm = BasicFlow()

    with pytest.raises(fsm.InvalidState):
        fsm.transition_to("nopenopenope")


def test_transition_to_complex():
    fsm = ComplexFlow()
    assert fsm.current_state() == "created"

    job = {
        "id": "CCEE9690-6626-4827-AC1A-73A911278067",
    }

    with mock.patch.object(fsm, "handle_any") as mock_any:
        with mock.patch.object(fsm, "handle_in_progress") as mock_in_progress:
            fsm.transition_to("waiting", job)
            assert fsm.current_state() == "waiting"
            mock_any.assert_called_once_with("waiting", job)
            mock_in_progress.assert_not_called()

    with mock.patch.object(fsm, "handle_any") as mock_any:
        with mock.patch.object(fsm, "handle_in_progress") as mock_in_progress:
            fsm.transition_to("in_progress", job)
            assert fsm.current_state() == "in_progress"
            mock_any.assert_called_once_with("in_progress", job)
            mock_in_progress.assert_called_once_with("in_progress", job)

    with mock.patch.object(fsm, "handle_any") as mock_any:
        with mock.patch.object(fsm, "handle_in_progress") as mock_in_progress:
            fsm.transition_to("waiting", job)
            assert fsm.current_state() == "waiting"
            mock_any.assert_called_once_with("waiting", job)
            mock_in_progress.assert_not_called()

    with mock.patch.object(fsm, "handle_any") as mock_any:
        with mock.patch.object(fsm, "handle_in_progress") as mock_in_progress:
            fsm.transition_to("done", job)
            assert fsm.current_state() == "done"
            mock_any.assert_called_once_with("done", job)
            mock_in_progress.assert_not_called()


def test_from_json():
    # You can have external JSON definitions (or just a Python `dict`).
    json_definition = {
        "allowed_transitions": {
            "start": ["end"],
            "end": None,
        },
        "default_state": "start",
    }

    # Now we've got a new class.
    Whee = FSM.from_json("Whee", json_definition)

    whee = Whee()
    assert whee.current_state() == "start"

    with pytest.raises(Whee.InvalidState):
        whee.transition_to("nope")

    whee.transition_to("end")
    assert whee.current_state() == "end"
