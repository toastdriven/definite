import datetime
from unittest import mock

import pytest

from definitely import FSM


class BasicWorkflow(FSM):
    allowed_transitions = {
        "draft": ["awaiting_review", "rejected"],
        "awaiting_review": ["draft", "reviewed", "rejected"],
        "reviewed": ["published", "rejected"],
        "published": None,
        "rejected": ["draft"],
    }
    default_state = "draft"


class ComplexWorkflow(FSM):
    allowed_transitions = {
        "draft": ["awaiting_review", "rejected"],
        "awaiting_review": ["draft", "reviewed", "rejected"],
        "reviewed": ["published", "rejected"],
        "published": None,
        "rejected": ["draft"],
    }
    default_state = "draft"

    # Define a `handle_<state_name>` method on the class.
    def handle_awaiting_review(self, new_state):
        # spell_check_results = check_spelling(self.obj.content)
        # msg = (
        #     f"{self.obj.title} ready for review. "
        #     f"{len(spell_check_results)} spelling errors."
        # )
        # send_email(to=editor_email, message=msg)
        pass

    def handle_published(self, new_state):
        self.obj.pub_date = datetime.datetime.utcnow()
        self.obj.save()

    def handle_any(self, new_state):
        self.obj.state = new_state
        self.obj.save()


class FakeNewsPost(object):
    pub_date = None

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def save(self):
        # This would persist to a DB.
        pass


def test_basic():
    workflow = BasicWorkflow()
    assert workflow.current_state() == "draft"

    workflow.transition_to("awaiting_review")
    assert workflow.current_state() == "awaiting_review"
    workflow.transition_to("reviewed")
    assert workflow.current_state() == "reviewed"

    assert workflow.is_allowed("published")

    workflow.current_state()  # "reviewed"

    with pytest.raises(workflow.TransitionNotAllowed) as excinfo:
        workflow.transition_to("awaiting_review")

    assert "'reviewed' cannot transition to 'awaiting_review'" in str(excinfo.value)


def test_complex():
    workflow = ComplexWorkflow()
    assert workflow.current_state() == "draft"

    with mock.patch.object(workflow, "handle_any") as mock_handle_any:
        with mock.patch.object(workflow, "handle_awaiting_review") as mock_handle_ar:
            workflow.transition_to("awaiting_review")
            mock_handle_any.assert_called_once_with("awaiting_review")
            mock_handle_ar.assert_called_once_with("awaiting_review")

    with mock.patch.object(workflow, "handle_any") as mock_handle_any:
        workflow.transition_to("reviewed")
        mock_handle_any.assert_called_once_with("reviewed")
        assert workflow.current_state() == "reviewed"

    with mock.patch.object(workflow, "handle_any") as mock_handle_any:
        with mock.patch.object(workflow, "handle_published") as mock_handle_published:
            workflow.transition_to("published")
            mock_handle_any.assert_called_once_with("published")
            mock_handle_published.assert_called_once_with("published")

    assert workflow.current_state() == "published"

    with pytest.raises(workflow.TransitionNotAllowed) as excinfo:
        workflow.transition_to("draft")


def test_handlers():
    news_post = FakeNewsPost(
        title="Hello world!",
        content="This iz our frist post!",
        state="draft",
    )

    workflow = ComplexWorkflow(obj=news_post)
    assert workflow.current_state() == "draft"

    workflow.transition_to("awaiting_review")
    # It should've updated the state on the object!
    assert news_post.state == "awaiting_review"
    assert news_post.pub_date is None

    workflow.transition_to("reviewed")
    assert news_post.state == "reviewed"
    assert news_post.pub_date is None

    workflow.transition_to("published")
    # Both `handle_any` *AND* `handle_published` should've been called.
    assert news_post.state == "published"
    now = datetime.datetime.utcnow()
    assert news_post.pub_date.year == now.year

    assert workflow.current_state() == "published"
