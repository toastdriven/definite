Advanced Usage
==============

Here are some advanced ways you can use ``definite``.


Use External JSON Files
-----------------------

``definite`` has built-in support for loading states/transitions directly
from JSON files. This allows you to share the states with other code, or allow
non-technical users to edit them.

The JSON looks almost identical to the required attributes for a ``FSM``
subclass.

.. code-block:: javascript

    {
        allowed_transitions={
            "created": ["waiting"],
            "waiting": ["in_progress", "done"],
            "in_progress": ["done"],
            "done": null
        },
        default_state="created"
    }

However, it can be loaded & the classes created at runtime.

.. code-block:: python

    >>> import json
    >>> from definite import FSM

    # First, we load the JSON up.
    >>> state_data = json.loads("/path/to/above/file.json")

    # Then we can dynamically create the class based on the JSON.
    >>> JobFlow = FSM.from_json("JobFlow", state_data)

    # And then instantiate it & use it.
    >>> job_1 = JobFlow()
    >>> job_1.current_state()
    "created"
    >>> job_1.all_states()
    ["created", "done", "in_progress", "waiting"]


Certain Transition Logic
------------------------

When asked to perform a transition, the ``FSM`` class does things in a certain
order:

#. Check for validity/allowed-ness new state
#. If present, call the ``handle_any`` handler with the new state
#. If present, call the ``handle_<state_name>`` handler with the new state
#. Finally update the current state to the new state

Because of this order, you can take special actions *only* for transitions
between two certain states.

For example, the ``Workflow`` example from the :doc:`./tutorial` can reach
the ``rejected`` state from a variety of other states (``draft``,
``awaiting_review``, ``reviewed``).

If you're feeling malicious, you could send the writer a scathing email
only when the editor-in-chief rejects their story (the transition from
``reviewed`` to ``rejected``).

.. code-block:: python

    from .email import send_mail, FROM_EMAIL

    # This is the same as the tutorial code.
    class Workflow(FSM):
        allowed_transitions = {
            "draft": ["awaiting_review", "rejected"],
            "awaiting_review": ["draft", "reviewed", "rejected"],
            "reviewed": ["published", "rejected"],
            "published": None,
            "rejected": ["draft"],
        }
        default_state = "draft"

        # But here, we look for the `rejected` state.
        def handle_rejected(self, state_name):
            # The `state_name` here is "rejected".
            # But `self.current_state()` will tell you what the "old" state was!
            prev_state = self.current_state()

            # So if it was previously reviewed by the staff editors, it went
            # to the chief for publishing, but got rejected!
            if prev_state == "reviewed":
                # TIME TO BURN.
                msg = (
                    f"The editors let '{self.obj.title}' through, but the Chief"
                    "tossed it in the trash! Write better content!"
                )
                send_mail(
                    FROM_EMAIL,
                    self.obj.author.email,
                    "The Chief rejected you!",
                    msg
                )

Obviously, this is mean-spirited & would promote an unhealthy work environment.
Don't do this per-se, but the utility to control behavior down to certain
transitions has a lot of potential.


Auto-Create State Constants
---------------------------

``definite`` automatically does a fair amount of checking of state names for
validity. However, some programmers may prefer having constants for use instead
of the simple strings shown throughout these docs.

Because ``FSM`` is designed to be subclassed, you could override/extend the
built-in behavior to automatically create constants for use.

.. code-block:: python

    from definite import FSM


    class AutoConstantsFSM(FSM):
        # We'll latch onto the `setup` method, which is called when the class
        # is instantiated.
        def setup(self):
            # Make sure you call `super()` first.
            super().setup()

            # Then we can automatically create the constants on the class.
            for state_name in self.allowed_transitions.keys():
                setattr(self, state_name.upper(), state_name)

Then you simply inherit from your new subclass instead of ``FSM``.

.. code-block:: python

    class JobFlow(AutoConstantsFSM):
        allowed_transitions = {
            "created": ["waiting"],
            "waiting": ["in_progress", "done"],
            "in_progress": ["done"],
            "done": None,
        }
        default_state = "created"

Now all-caps versions of your states will be present on your instances.

.. code-block:: python

    >>> job_1 = JobFlow()
    >>> job_1.transition_to(job_1.WAITING)

