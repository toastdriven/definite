Quickstart
==========

::

    from definitely import FSM

    # You define all the valid states, as well as what their allowed
    # transitions are.
    class Workflow(FSM):
        allowed_transitions = {
            "draft": ["awaiting_review", "rejected"],
            "awaiting_review": ["draft", "reviewed", "rejected"],
            "reviewed": ["published", "rejected"],
            "published": None,
            "rejected": ["draft"],
        }
        default_state = "draft"

    # Right away, you can use the states/transitions as-is to enforce changes.
    workflow = Workflow()
    workflow.current_state() # "draft"

    workflow.transition_to("awaiting_review")
    workflow.transition_to("reviewed")

    workflow.is_allowed("published") # True

    # Invalid/disallowed transitions will throw an exception.
    workflow.current_state() # "reviewed"
    # ...which can only go to "published" or "rejected", but...
    workflow.transition_to("awaiting_review")
    # Traceback (most recent call last):
    # ...
    # workflow.TransitionNotAllowed: "reviewed" cannot transition to "awaiting_review"