Tutorial
========

`definite` lets you create small finite state machines. These are great for
tracking state, as well as triggering transition behavior when the states
change.


The Most Basic Example
----------------------

To start with, you'll need to import the ``FSM`` class from ``definite``, then
subclass it.

We'll define the tiniest fully-functional subclass we can, allowing just a
``start`` & ``end`` state. Beyond the subclassing ``FSM``, the only
requirements are defining the ``allowed_transitions`` and ``default_state``
attributes on the subclass.

.. code-block:: python

    from definite import FSM

    class Tiny(FSM):
        allowed_transitions = {
            "start": ["end"],
            "end": None,
        }
        default_state = "start"

.. note::
    You may be wondering why ``default_state`` is also required. A natural
    assumption would be that the first mentioned state in
    ``allowed_transitions`` would be the default.

    Only relatively recently in Python's history did dictionary ordering become
    guaranteed (`documented feature in 3.7`_). And even now, not all third-party
    tooling respects this.

    This could be solved in a variety of clever ways (special syntax, changing
    from a ``dict`` to a two-``tuple`` structure, using
    ``collections.OrderedDict``, etc.).

    But in the end, manually specifying it this way is clear, easy-to-read, &
    unsurprising/doesn't require special knowledge. Hence, having to specify it.

Now you can instantiate the new ``Tiny`` class. Each instance starts in the
provided default state of ``start``.

.. code-block:: python

    >>> tiny = Tiny()
    >>> tiny.current_state()
    "start"

There are also a variety of methods for inspecting what the ``FSM`` can do,
such as checking what states are available, if a given state is a
recognized/valid state, and if a given state can be transitioned to.

.. code-block:: python

    >>> tiny.all_states()
    ["end", "start"]
    >>> tiny.is_valid("start")
    True
    >>> tiny.is_valid("nopenopenope")
    False
    >>> tiny.is_allowed("end")
    True

From there, we can trigger a state change by tell it to transition to the
``end`` state.

.. code-block:: python

    >>> tiny.transition_to("end")
    >>> tiny.current_state()
    "end"

Just two states isn't very useful, so let's move on to a more complex example.


More States/Transitions
-----------------------

Enforcing workflows are a great use of finite state machines, so let's model
a possible workflow for a small publisher. We'll assume there are writers,
editors, and an editor-in-chief.

* Writers can only create drafts, then submit them for review.
* Editors perform the review, then decide whether to send it back for changes
  (back to draft), to mark it as reviewed for the editor-in-chief to look at,
  or to reject the story.
* Editor-in-chief looks at reviewed stories, then either publishes them or can
  reject them.

We can model all the states a news story could be in this:

.. code-block:: python

    from definite import FSM

    class Workflow(FSM):
        allowed_transitions = {
            "draft": ["awaiting_review", "rejected"],
            "awaiting_review": ["draft", "reviewed", "rejected"],
            "reviewed": ["published", "rejected"],
            "published": None,
            "rejected": ["draft"],
        }
        default_state = "draft"

Once this is defined, we can immediately start using it to guide what states
our business logic.

.. code-block:: python

    >>> workflow = Workflow()
    >>> workflow.current_state() # "draft"

    >>> workflow.transition_to("awaiting_review")
    >>> workflow.transition_to("reviewed")

    >>> workflow.is_allowed("published") # True

    # Invalid/disallowed transitions will throw an exception.
    >>> workflow.current_state() # "reviewed"
    # ...which can only go to "published" or "rejected", but...
    >>> workflow.transition_to("awaiting_review")
    # Traceback (most recent call last):
    # ...
    # workflow.TransitionNotAllowed: "reviewed" cannot transition to "awaiting_review"


Adding Transition Behavior
--------------------------

You can build your own logic around the FSMs anywhere, but ``definite`` also
supports adding your own transition logic directly to the state machine, keeping
the state & behavior together.

For instance, let's say our previous example should send emails when a story
is either waiting on review, or when it's available for the editor-in-chief to
publish.

We can expand on transition behavior by adding "handlers" to specific states.
In ``definite``, any method prefixed with ``handle_`` followed by the desired
state name will **automatically** be called when changing to that state.

So, to send emails when ``awaiting_review`` & ``reviewed`` are met, we'd
implement the following handlers.

.. code-block:: python

    from email.message import EmailMessage
    import smtplib

    from definite import FSM


    FROM_EMAIL = "no-reply@example.com"
    EDITORS_EMAIL = "ed-staff@example.com"
    CHIEF_EMAIL = "chief@example.com"


    # To keep with the standard library theme, here's a very basic email-sending
    # function. Probably not very production-friendly.
    def send_mail(from_addr, to_addr, subject, message):
        msg = EmailMessage()
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.set_content(message)

        smtp = smtplib.SMTP('localhost')
        smtp.send_message(msg)
        smtp.quit()


    # Here's our already-written FSM...
    class Workflow(FSM):
        allowed_transitions = {
            "draft": ["awaiting_review", "rejected"],
            "awaiting_review": ["draft", "reviewed", "rejected"],
            "reviewed": ["published", "rejected"],
            "published": None,
            "rejected": ["draft"],
        }
        default_state = "draft"

        # ...but here we add our new handlers!
        def handle_awaiting_review(self, state_name):
            msg = "There's a story awaiting review. Go log in & check it out!"
            send_mail(
                FROM_EMAIL,
                EDITORS_EMAIL,
                "Story ready for review!",
                msg
            )

        def handle_reviewed(self, state_name):
            msg = "There's a story ready for publishing. Please have a look!"
            send_mail(
                FROM_EMAIL,
                CHIEF_EMAIL,
                "Story ready for publishing!",
                msg
            )

These handlers (``handle_awaiting_review`` & ``handle_reviewed``) will
automatically be called upon transition. For example:

.. code-block:: python

    >>> storyflow = Workflow()
    # Some work happens, then...

    >>> storyflow.transition_to("awaiting_review")
    # During this transition, the ``handle_awaiting_review`` method gets called
    # and the email is sent to the editors!

    >>> workflow.transition_to("reviewed")
    # And similarly with the editor-in-chief!


Using/Affecting External Objects
--------------------------------

We've got better encapsulization, but there are a couple shortcomings of the
last example.

#. The emails don't include any information about *which* story got changed.
#. Because they're stored in the database, we're presumably having to manually
    manage the status of each story.

To improve on this, we'll introduce two more concepts: the ability for a FSM
to be specific to an external object, and the special ``handle_any`` transition
handler.

.. note::
    For brevity, we're going to omit that same email code in all the future
    examples. Assume it's still defined, or that you've put it in its own
    module & are importing it.

First, external objects. By passing **ANY** Python object in during
initialization, you can enable the FSM to use it during transition handlers.
We'll make a couple small tweaks to our existing handlers.

.. code-block:: python

    class Workflow(FSM):
        allowed_transitions = {
            "draft": ["awaiting_review", "rejected"],
            "awaiting_review": ["draft", "reviewed", "rejected"],
            "reviewed": ["published", "rejected"],
            "published": None,
            "rejected": ["draft"],
        }
        default_state = "draft"

        def handle_awaiting_review(self, state_name):
            # Note that we're now using a format string & `self.obj` here!
            msg = f"'{self.obj.title}' is awaiting review. Go log in & check it out!"
            send_mail(
                FROM_EMAIL,
                EDITORS_EMAIL,
                "Story ready for review!",
                msg
            )

        def handle_reviewed(self, state_name):
            # Note that we're now using a format string & `self.obj` here!
            msg = f"'{self.obj.title}' is ready for publishing. Please have a look!"
            send_mail(
                FROM_EMAIL,
                CHIEF_EMAIL,
                "Story ready for publishing!",
                msg
            )

Then, when we go to use the workflow, we pass the news story to the constructor.
The FSM will save a reference to it & exposes it as ``self.obj`` to the
handlers.

.. note::
    For convenience, we'll use a Django model here. But there's nothing
    stopping you from using whatever else, like SQLAlchemy's ORM, a Redis
    key/value, flat files, even built-in Python objects like ``dict``!

.. code-block:: python

    >>> from news.models import NewsStory

    >>> story = NewsStory.objects.create(
    ...     title="Hello, world!",
    ...     content="This is our very first story!",
    ...     author=some_writer,
    ...     state="draft",
    ... )

    # We pass it in here via the `obj=...` kwarg!
    >>> workflow = Workflow(obj=story)

    # Now when we make the transition to the new state, the editors will get
    # a customized email telling them the title of the story that's ready for
    # review!
    >>> storyflow.transition_to("awaiting_review")

Another improvement we can make is to persist the ``Workflow`` state in the
database. So if a different server loads the story, the correct state will be
preserved there. We'll implement this using the ``handle_any`` method.

The special ``handle_any`` method fires on **ANY/ALL** state changes, making it
easy to add behavior that should happen with any change of state.

.. code-block:: python

    class Workflow(FSM):
        allowed_transitions = {
            "draft": ["awaiting_review", "rejected"],
            "awaiting_review": ["draft", "reviewed", "rejected"],
            "reviewed": ["published", "rejected"],
            "published": None,
            "rejected": ["draft"],
        }
        default_state = "draft"

        # Here's the new code!
        def handle_any(self, state_name):
            # The `state` field on the model isn't special, just a plain old
            # `CharField`. But we can push all the FSM's changes right onto it.
            self.obj.state = self.current_state()
            self.obj.save()

        def handle_awaiting_review(self, state_name):
            # Same as before...

        def handle_reviewed(self, state_name):
            # Same as before...

Now when we work with the story, we're also persisting the state to the DB.

.. code-block:: python

    # Same as before.
    >>> from news.models import NewsStory
    >>> story = NewsStory.objects.create(
    ...     title="Hello, world!",
    ...     content="This is our very first story!",
    ...     author=some_writer,
    ...     state="draft",
    ... )
    >>> workflow = Workflow(obj=story)

    # First, show that nothing has changed yet & no handlers have fired.
    >>> story.state
    "draft"
    >>> workflow.current_state()
    "draft"

    # But now, when we trigger the transition, both the `handle_any` & the
    # `handle_awaiting_review` will fire!
    >>> storyflow.transition_to("awaiting_review")
    # Email sent!

    # Proof that `handle_any` fired!
    >>> story.state
    "awaiting_review"

This is great for generic things like adding logging, persisting to long-term
storage, or performing integrity checks.

The final change to make is that we can pass the story's current state to
the ``Workflow`` when creating it, making it so that no matter what server loads
the story, the FSM is always in the matching state.

.. code-block:: python

    >>> from news.models import NewsStory
    # We'll assume there's already some stories in the database.
    >>> story = NewsStory.objects.get(title="Hello, world!")

    # Here, we pass in the `initial_state` from the model, to synchronize the
    # FSM to the correct state.
    >>> workflow = Workflow(obj=story, initial_state=obj.state)

    # Note that there's nothing special/magical about the `state` field name
    # on the model. Hence the explicit use of `initial_state=...`.


Conclusion
----------

We've learned how to define simple finite state machines, ones with complex
state interactions, how to use the everyday parts of the API, and how to build
in behaviors!

However, there's more that can be done with ``definite``:

* You can store your states/transitions in external JSON files
* You can implement logic that only happens on certain transitions
* You can auto-create constants for your states

You can find examples of these within the :doc:`./advanced` guide.

Alternatively, you can dive into the API references, such as the
:doc:`../api/fsm` reference.

Enjoy!


.. _`documented feature in 3.7`: https://docs.python.org/3/library/stdtypes.html?highlight=preserve#mapping-types-dict
