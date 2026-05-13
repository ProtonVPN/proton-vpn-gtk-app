"""
NPS Survey modal module.


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
from pathlib import Path
from enum import Enum, auto
from typing import Callable, Optional

from gi.repository import Gtk, Gdk

from proton.vpn.app.gtk.assets import icons
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.session.dataclasses import NPSSurveyResponse


class ProtonReport(Gtk.Box):
    """Proton Report Icon

    Wraps Gtk.Picture in a Gtk.Box to prevent vertical over-expansion.
    Gtk.Picture computes its natural height relative to the width offered by
    its parent, so in a wide modal it would expand well beyond ICON_HEIGHT via
    aspect-ratio scaling. With hexpand=False the box's layout pass uses the
    picture's own natural width as the height-for-width constraint, giving a
    stable ICON_HEIGHT.

    Gtk.Image was not used: in GTK 4.18 it ignores a paintable's intrinsic
    dimensions for sizing. set_pixel_size restores rendering but forces a
    square allocation, leaving dead space around a landscape paintable.
    """
    ICON_HEIGHT = 90

    def __init__(self):
        super().__init__()
        self.set_name("report")
        self.set_vexpand(False)
        self.set_hexpand(False)
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)

        pixbuf = icons.get(
            Path("NPS/report.svg"),
            height=self.ICON_HEIGHT
        )
        pixbuf_success = icons.get(
            Path("NPS/report-success.svg"),
            height=self.ICON_HEIGHT
        )
        self.texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.texture_success = Gdk.Texture.new_for_pixbuf(pixbuf_success)

        self._picture = Gtk.Picture()
        self._picture.set_hexpand(False)
        self._picture.set_vexpand(False)
        self._picture.set_can_shrink(False)
        self.append(self._picture)

        self.set_submitted(False)

    @property
    def paintable(self):
        """Returns the currently displayed paintable."""
        return self._picture.get_paintable()

    def set_submitted(self, success: bool):
        """Sets the report icon variant"""
        if success:
            self._picture.set_paintable(self.texture_success)
        else:
            self._picture.set_paintable(self.texture)


class LimitedTextView(Gtk.TextView):
    """A TextView that silently truncates input to a maximum character count.

    When typed or pasted input would exceed the limit, only the portion that
    fits is inserted.
    """

    def __init__(self, max_chars: int):
        super().__init__()
        self._max_chars = max_chars
        self.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._buffer = self.get_buffer()
        self._handler_id = safe_signal_connect(self._buffer, "insert-text", self._on_insert_text)
        safe_signal_connect(self, "unrealize", self._on_unrealize)

    @property
    def char_count(self) -> int:
        """Returns the current number of characters in the buffer."""
        return self._buffer.get_char_count()

    @property
    def is_at_limit(self) -> bool:
        """Returns True when the buffer has reached the character limit."""
        return self.char_count >= self._max_chars

    def _on_unrealize(self, _):
        if self._handler_id is not None:
            self._buffer.disconnect(self._handler_id)
            self._handler_id = None

    def _on_insert_text(self, buffer, _location, text, _length):
        remaining_allowed = self._max_chars - buffer.get_char_count()
        if len(text) > remaining_allowed:
            buffer.stop_emission_by_name("insert-text")
            if remaining_allowed > 0:
                # A fresh iter from the insert mark is used rather than
                # _location, which is only valid for the duration of the
                # stopped emission and may be in an undefined state after
                # stop_emission_by_name is called.
                insert_iter = buffer.get_iter_at_mark(buffer.get_insert())
                buffer.handler_block(self._handler_id)
                buffer.insert(insert_iter, text[:remaining_allowed])
                buffer.handler_unblock(self._handler_id)


NPSSubmitHandler = Callable[[int, str], None]
NPSDismissHandler = Callable[[], None]


# pylint: disable=too-many-instance-attributes
class NPSSurveyModal(Gtk.Window):
    """NPS Survey modal window."""
    TITLE_SURVEY = "How likely are you to recommend Proton VPN to a friend?"
    MAX_SCORE = 10
    SCORE_LOWER_DESCRIPTION = "0 is very unlikely"
    SCORE_UPPER_DESCRIPTION = "10 is very likely"
    FEEDBACK_PROMPT = "Please let us know why you gave that rating"
    FEEDBACK_OPTIONAL = "Optional"
    SUBMIT_BUTTON_TITLE = "Share anonymously"
    SUBMITTED_TITLE = "Thanks for your feedback"
    SUBMITTED_SUBTITLE = "Your feedback helps us improve Proton VPN."

    class State(Enum):
        """Represents the NPS Popover's configured state"""
        PROMPT = auto()
        FEEDBACK = auto()
        SUBMITTED = auto()

    def __init__(
        self,
        controller: Controller,
        submit_handler: NPSSubmitHandler,
        dismiss_handler: NPSDismissHandler
    ):
        super().__init__()
        self.set_modal(True)
        self.set_default_size(450, 595)
        self.set_resizable(False)
        self.set_name("nps-survey-modal")

        self._controller = controller
        self._submit_handler = submit_handler
        self._dismiss_handler = dismiss_handler
        self._dismiss_handler_id = \
            safe_signal_connect(self, "close-request", self._on_close_request)
        self._chosen_score: Optional[int] = None
        self._current_state: Optional[NPSSurveyModal.State] = None

        header_bar = Gtk.HeaderBar()
        header_bar.set_show_title_buttons(True)
        header_bar.set_decoration_layout(":close")
        header_bar.set_title_widget(Gtk.Box())
        self.set_titlebar(header_bar)

        self._container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._container.add_css_class("content")
        self._container.set_vexpand(True)
        self.set_child(self._container)

        self._build_icon_and_title()
        self._build_score()
        self._build_feedback_text()
        self._build_submit()

        self.set_survey_state(NPSSurveyModal.State.PROMPT)

    def _on_close_request(self, _):
        self._dismiss_handler()

    def _build_icon_and_title(self):
        self._icon = ProtonReport()
        self._title = Gtk.Label(label=NPSSurveyModal.TITLE_SURVEY)
        self._title.set_vexpand(False)
        self._title.add_css_class("title-label")
        self._title.set_wrap(True)
        self._title.set_justify(Gtk.Justification.CENTER)

        self._nps_description_layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._nps_description_layout.append(self._icon)
        self._nps_description_layout.append(self._title)
        self._container.append(self._nps_description_layout)

    def _on_clicked_score(self, button: Gtk.Button):
        chosen_score = int(button.get_label())
        self.select_score(chosen_score)

    def _build_score(self):
        self._score_layout = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._score_layout.add_css_class("score-layout")
        previous_button: Gtk.ToggleButton = None
        for score in range(NPSSurveyModal.MAX_SCORE+1):
            score_button = Gtk.ToggleButton.new_with_label(f"{score}")
            safe_signal_connect(score_button, "clicked", self._on_clicked_score)
            if score != 0:
                score_button.set_group(previous_button)
            score_button.set_hexpand(False)
            score_button.set_halign(Gtk.Align.CENTER)
            score_button.set_valign(Gtk.Align.CENTER)
            score_button.add_css_class("score-button")
            previous_button = score_button
            self._score_layout.append(score_button)

        self._score_description_layout = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._score_description_layout.add_css_class("score-description-layout")
        left_label = Gtk.Label(label=NPSSurveyModal.SCORE_LOWER_DESCRIPTION)
        right_label = Gtk.Label(label=NPSSurveyModal.SCORE_UPPER_DESCRIPTION)
        left_label.set_margin_start(0)
        left_label.set_hexpand(True)
        left_label.set_xalign(0.0)
        left_label.add_css_class("light-label")
        right_label.add_css_class("light-label")
        right_label.set_margin_end(0)
        self._score_description_layout.append(left_label)
        self._score_description_layout.append(right_label)

        self._container.append(self._score_layout)
        self._container.append(self._score_description_layout)

    def _build_feedback_text(self):
        self._prompt_label = Gtk.Label(label=NPSSurveyModal.FEEDBACK_PROMPT)
        self._prompt_label.set_xalign(0.0)
        self._prompt_label.add_css_class("feedback-prompt-label")

        self._scrolled_text_view = Gtk.ScrolledWindow()
        self._scrolled_text_view.add_css_class("feedback-scroll")
        self._scrolled_text_view.set_min_content_height(120)
        self._scrolled_text_view.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self._feedback_text_view = LimitedTextView(NPSSurveyResponse.COMMENT_CHAR_MAX_LENGTH)
        self._scrolled_text_view.set_child(self._feedback_text_view)

        self._feedback_footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._optional_label = Gtk.Label(label=NPSSurveyModal.FEEDBACK_OPTIONAL)
        self._optional_label.set_xalign(0.0)
        self._optional_label.set_hexpand(True)
        self._optional_label.add_css_class("light-label")
        self._optional_label.add_css_class("feedback-footer-label")
        self._char_counter_label = \
            Gtk.Label(label=f"0/{NPSSurveyResponse.COMMENT_CHAR_MAX_LENGTH}")
        self._char_counter_label.set_xalign(0.0)
        self._char_counter_label.set_margin_end(0)
        self._char_counter_label.add_css_class("light-label")
        self._char_counter_label.add_css_class("feedback-footer-label")
        self._feedback_footer.append(self._optional_label)
        self._feedback_footer.append(self._char_counter_label)

        safe_signal_connect(
            self._feedback_text_view.get_buffer(),
            "changed",
            self._on_text_changed
        )

        self._container.append(self._prompt_label)
        self._container.append(self._scrolled_text_view)
        self._container.append(self._feedback_footer)

    def _on_text_changed(self, _):
        count = self._feedback_text_view.char_count
        self._char_counter_label.set_label(
            f"{count}/{NPSSurveyResponse.COMMENT_CHAR_MAX_LENGTH}"
        )
        if self._feedback_text_view.is_at_limit:
            self._char_counter_label.add_css_class("char-counter-limit")
        else:
            self._char_counter_label.remove_css_class("char-counter-limit")

    def _build_submit(self):
        self._submit_button = Gtk.Button(label=NPSSurveyModal.SUBMIT_BUTTON_TITLE)
        self._submit_button.add_css_class("primary")
        self._submit_button.set_halign(Gtk.Align.CENTER)
        self._container.append(self._submit_button)
        safe_signal_connect(self._submit_button, "clicked", self._on_clicked_submit)

    def _on_clicked_submit(self, _: Gtk.Button):
        if self._chosen_score is None:
            # shouldn't happen
            return

        feedback_text = self.feedback_text
        self._submit_handler(self._chosen_score, feedback_text)
        self.set_survey_state(NPSSurveyModal.State.SUBMITTED)

    @property
    def state(self) -> "NPSSurveyModal.State":
        """Returns the current survey state."""
        return self._current_state

    @property
    def title(self) -> str:
        """Returns the current title label text."""
        return self._title.get_label()

    @property
    def subtitle(self) -> str | None:
        """Returns the subtitle label text, or None before the SUBMITTED state."""
        return self._subtitle.get_label() if hasattr(self, "_subtitle") else None

    @property
    def score_buttons(self) -> list[Gtk.ToggleButton]:
        """Returns the list of score toggle buttons in order."""
        buttons = []
        child = self._score_layout.get_first_child()
        while child:
            buttons.append(child)
            child = child.get_next_sibling()
        return buttons

    def select_score(self, score: int):
        """Selects a score and transitions to the FEEDBACK state."""
        self._chosen_score = score
        self.set_survey_state(NPSSurveyModal.State.FEEDBACK)

    @property
    def feedback_text(self) -> str:
        """Returns the current feedback text."""
        buffer = self._feedback_text_view.get_buffer()
        return buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)

    @feedback_text.setter
    def feedback_text(self, text: str):
        """Sets the feedback text."""
        self._feedback_text_view.get_buffer().set_text(text)

    def submit(self):
        """Programmatically triggers the submit action."""
        self._submit_button.emit("clicked")

    def set_survey_state(self, state: "NPSSurveyModal.State"):
        """Sets the current survey configuration"""
        self._current_state = state
        if state == NPSSurveyModal.State.PROMPT:
            self._scrolled_text_view.set_opacity(0)
            self._prompt_label.set_opacity(0)
            self._feedback_footer.set_opacity(0)
            self._scrolled_text_view.set_sensitive(False)
            self._submit_button.set_sensitive(False)

        if state == NPSSurveyModal.State.FEEDBACK:
            self._scrolled_text_view.set_opacity(1)
            self._prompt_label.set_opacity(1)
            self._feedback_footer.set_opacity(1)
            self._scrolled_text_view.set_sensitive(True)
            self._submit_button.set_sensitive(True)

        if state == NPSSurveyModal.State.SUBMITTED:
            self._scrolled_text_view.set_visible(False)
            self._prompt_label.set_visible(False)
            self._feedback_footer.set_visible(False)
            self._score_layout.set_visible(False)
            self._score_description_layout.set_visible(False)
            self._submit_button.set_visible(False)

            self._title.set_label(NPSSurveyModal.SUBMITTED_TITLE)
            self._subtitle = Gtk.Label(label=NPSSurveyModal.SUBMITTED_SUBTITLE)
            self._subtitle.add_css_class("subtitle-label")
            self._nps_description_layout.append(self._subtitle)
            self._nps_description_layout.set_valign(Gtk.Align.CENTER)
            self._nps_description_layout.set_vexpand(True)
            self._icon.set_submitted(True)
            self.add_css_class("submitted")

            self.disconnect(self._dismiss_handler_id)
