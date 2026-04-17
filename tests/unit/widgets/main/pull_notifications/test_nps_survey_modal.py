"""
Copyright (c) 2026 Proton AG

This file is part of Proton VPN.

Proton VPN is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Proton VPN is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ProtonVPN.  If not, see <https://www.gnu.org/licenses/>.
"""
from unittest.mock import Mock

from proton.vpn.app.gtk.widgets.main.pull_notifications.nps_survey_modal import \
    NPSSurveyModal, \
    LimitedTextView, \
    ProtonReport
from tests.unit.testing_utils import process_gtk_events


def build_nps_survey(submit_handler=None, dismiss_handler=None):
    return NPSSurveyModal(
        controller=Mock(),
        submit_handler=submit_handler or Mock(),
        dismiss_handler=dismiss_handler or Mock()
    )


class TestProtonReport:

    def test_set_submitted_false_uses_default_texture(self):
        report = ProtonReport()

        report.set_submitted(False)

        assert report.paintable == report.texture

    def test_set_submitted_true_uses_success_texture(self):
        report = ProtonReport()

        report.set_submitted(True)

        assert report.paintable == report.texture_success


class TestLimitedTextView:

    def test_typing_within_limit_is_accepted(self):
        view = LimitedTextView(max_chars=10)

        view.get_buffer().insert_at_cursor("hello")

        assert view.char_count == 5
        assert not view.is_at_limit

    def test_typing_to_exact_limit_is_accepted(self):
        view = LimitedTextView(max_chars=5)

        view.get_buffer().insert_at_cursor("hello")

        assert view.char_count == 5
        assert view.is_at_limit

    def test_typing_beyond_limit_is_truncated(self):
        view = LimitedTextView(max_chars=5)

        view.get_buffer().insert_at_cursor("hello world")

        assert view.char_count == 5

    def test_paste_that_partially_fits_is_truncated_to_limit(self):
        view = LimitedTextView(max_chars=10)
        view.get_buffer().insert_at_cursor("hello")  # 5 chars

        view.get_buffer().insert_at_cursor(" world!!!")  # 9 chars, only 5 fit

        assert view.char_count == 10
        assert view.is_at_limit

    def test_paste_into_full_buffer_is_rejected(self):
        view = LimitedTextView(max_chars=5)
        view.get_buffer().insert_at_cursor("hello")

        view.get_buffer().insert_at_cursor("x")

        assert view.char_count == 5


class TestNPSSurveyInitialState:

    def test_score_buttons_created_for_every_score_value(self):
        survey = build_nps_survey()

        assert len(survey.score_buttons) == NPSSurveyModal.MAX_SCORE + 1

    def test_score_button_labels_match_score_values(self):
        survey = build_nps_survey()

        for expected_score, button in enumerate(survey.score_buttons):
            assert button.get_label() == str(expected_score)

    def test_initial_state_is_prompt(self):
        survey = build_nps_survey()

        assert survey.state == NPSSurveyModal.State.PROMPT

    def test_title_shows_survey_question_initially(self):
        survey = build_nps_survey()

        assert survey.title == NPSSurveyModal.TITLE_SURVEY


class TestNPSSurveyFeedbackState:

    def test_select_score_transitions_to_feedback_state(self):
        survey = build_nps_survey()

        survey.select_score(5)

        assert survey.state == NPSSurveyModal.State.FEEDBACK


class TestNPSSurveySubmission:

    def test_submit_calls_handler_with_score_and_feedback(self):
        submit_handler = Mock()
        survey = build_nps_survey(submit_handler=submit_handler)
        survey.select_score(8)
        survey.feedback_text = "Great VPN!"

        survey.submit()
        process_gtk_events()

        submit_handler.assert_called_once_with(8, "Great VPN!")

    def test_submit_with_empty_feedback_passes_empty_string(self):
        submit_handler = Mock()
        survey = build_nps_survey(submit_handler=submit_handler)
        survey.select_score(5)

        survey.submit()
        process_gtk_events()

        submit_handler.assert_called_once_with(5, "")

    def test_submit_without_score_does_not_call_handler(self):
        submit_handler = Mock()
        survey = build_nps_survey(submit_handler=submit_handler)

        survey.submit()
        process_gtk_events()

        submit_handler.assert_not_called()

    def test_submit_transitions_to_submitted_state(self):
        survey = build_nps_survey()
        survey.select_score(5)

        survey.submit()
        process_gtk_events()

        assert survey.state == NPSSurveyModal.State.SUBMITTED


class TestNPSSurveySubmittedState:

    def test_submitted_state_updates_title_to_thanks(self):
        survey = build_nps_survey()

        survey.set_survey_state(NPSSurveyModal.State.SUBMITTED)

        assert survey.title == NPSSurveyModal.SUBMITTED_TITLE

    def test_submitted_state_appends_subtitle(self):
        survey = build_nps_survey()

        survey.set_survey_state(NPSSurveyModal.State.SUBMITTED)

        assert survey.subtitle == NPSSurveyModal.SUBMITTED_SUBTITLE

    def test_submitted_state_disconnects_dismiss_handler(self):
        dismiss_handler = Mock()
        survey = build_nps_survey(dismiss_handler=dismiss_handler)

        survey.set_survey_state(NPSSurveyModal.State.SUBMITTED)
        survey.emit("close-request")
        process_gtk_events()

        dismiss_handler.assert_not_called()


class TestNPSSurveyDismiss:

    def test_dismiss_handler_called_on_close_before_submission(self):
        dismiss_handler = Mock()
        survey = build_nps_survey(dismiss_handler=dismiss_handler)

        survey.emit("close-request")
        process_gtk_events()

        dismiss_handler.assert_called_once()
