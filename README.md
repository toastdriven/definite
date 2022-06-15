# `definitely`

Simple finite state machines.

Perfect for representing workflows.


## Quickstart

```python
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


# Additionally, you can set up extra code to fire on given state changes.
class Workflow(FSM):
    # Same transitions & default state.
    allowed_transitions = {
        "draft": ["awaiting_review", "rejected"],
        "awaiting_review": ["draft", "reviewed", "rejected"],
        "reviewed": ["published", "rejected"],
        "published": None,
        "rejected": ["draft"],
    }
    default_state = "draft"

    # Define a `handle_<state_name>` method on the class.
    def handle_awaiting_review(self, new_state, obj):
        spell_check_results = check_spelling(obj.content)
        msg = (
            f"{obj.title} ready for review. "
            f"{len(spell_check_results)} spelling errors."
        )
        send_email(to=editor_email, message=msg)

    def handle_published(self, new_state, obj):
        obj.pub_date = datetime.datetime.utcnow()
        obj.save()

    # You can also setup code that fires on **ANY** valid transition with the
    # special `handle_any` method.
    def handle_any(self, new_state, obj):
        obj.state = new_state
        obj.save()

# We start the same.
workflow = Workflow()
workflow.current_state() # "draft"

from news.models import NewsPost
news_post = NewsPost.objects.create(
    title="Hello world!",
    content="This iz our frist post!",
    state="draft",
)

# But when we trigger this change (& newly pass our `NewsPost` object)...
workflow.transition_to("awaiting_review", news_post)
# ...it triggers the spell check & the email we defined above, as well as
# hitting the `handle_any` method & updating the `state` field in the DB.
```


## Installation

`pip install definitely`


## Requirements

* Python 3.6+


## Testing

`$ pytest .`


## License

New BSD
