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


Demo factories for the NPS survey modal — one window per survey state.
"""
from unittest.mock import MagicMock

from proton.vpn.app.gtk.demo.registry import register_demo
from proton.vpn.app.gtk.demo.mocks import mock_controller
from proton.vpn.app.gtk.widgets.main.pull_notifications.nps_survey_modal import NPSSurveyModal


def _modal(state: "NPSSurveyModal.State") -> NPSSurveyModal:
    modal = NPSSurveyModal(
        mock_controller(),
        MagicMock(name="submit_handler"),
        MagicMock(name="dismiss_handler"),
    )
    modal.set_survey_state(state)
    return modal


@register_demo("nps-modal", label="prompt")
def nps_prompt() -> NPSSurveyModal:
    """NPS survey modal in its initial prompt (score) state."""
    return _modal(NPSSurveyModal.State.PROMPT)


@register_demo("nps-modal", label="feedback")
def nps_feedback() -> NPSSurveyModal:
    """NPS survey modal in its written-feedback state."""
    return _modal(NPSSurveyModal.State.FEEDBACK)


@register_demo("nps-modal", label="submitted")
def nps_submitted() -> NPSSurveyModal:
    """NPS survey modal in its post-submission thank-you state."""
    return _modal(NPSSurveyModal.State.SUBMITTED)
