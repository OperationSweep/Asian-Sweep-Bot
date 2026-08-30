"""Message classification - the safety-critical part.

The distinction these tests protect: 'Serial Number missing for X' is safe to
continue past only when X is a material the workbook never serialises. The same
sentence about a material we DID send serials for means the entry failed.
"""

from __future__ import annotations

import pytest

import fixture as fx
from sap_agent.sap.messages import MessageClass, classify, worst

BULK = fx.NON_SERIALISED[:3]
SERIALISED = fx.SERIALISED[:2] + [fx.TRAY_LABEL]
A_BULK, A_SERIALISED = BULK[0], SERIALISED[0]
UNKNOWN_MATERIAL = "92QQQ00999ZZZ"


def check(kind, text):
    return classify(kind, text, BULK, SERIALISED)


class TestSerialMissing:
    def test_bulk_material_is_expected(self):
        result = check("W", f"Serial Number missing for {A_BULK}")
        assert result.message_class is MessageClass.EXPECTED_WARNING
        assert result.may_continue

    def test_serialised_material_is_critical(self):
        """SAP asking for a serial we sent means the entry did not land."""
        result = check("W", f"Serial Number missing for {A_SERIALISED}")
        assert result.message_class is MessageClass.CRITICAL_ERROR
        assert not result.may_continue

    def test_unknown_material_is_not_assumed_safe(self):
        """The operator's example is from another build - never auto-continue."""
        result = check("W", f"Serial Number missing for {UNKNOWN_MATERIAL}")
        assert result.message_class is MessageClass.UNKNOWN_MESSAGE
        assert not result.may_continue

    def test_material_is_extracted(self):
        assert check("W", f"Serial Number missing for {A_BULK}").material == A_BULK

    @pytest.mark.parametrize("text", [
        f"Serial number missing for {A_BULK}",
        f"SERIAL NUMBER MISSING FOR {A_BULK}",
        f"Serial Number missing for: {A_BULK}",
        f"Serial  Number  missing  for  {A_BULK}",
    ])
    def test_matching_tolerates_formatting(self, text):
        assert check("W", text).message_class is MessageClass.EXPECTED_WARNING

    def test_classification_is_case_insensitive_on_material(self):
        assert check("W", f"Serial Number missing for {A_BULK.lower()}").message_class \
            is MessageClass.EXPECTED_WARNING


class TestOtherMessages:
    def test_posting_confirmation_is_success(self):
        assert check("S", "Document 4900012345 posted").message_class \
            is MessageClass.SUCCESS

    def test_empty_status_bar_is_success(self):
        assert check("", "").message_class is MessageClass.SUCCESS

    @pytest.mark.parametrize("text,expected", [
        ("Order 900000001 is locked by user SMITH", MessageClass.RETRYABLE_ERROR),
        ("Document is being processed by another user", MessageClass.RETRYABLE_ERROR),
        ("Please try again later", MessageClass.RETRYABLE_ERROR),
        ("You are not authorized for movement type 261", MessageClass.CRITICAL_ERROR),
        ("Order 900000001 does not exist", MessageClass.CRITICAL_ERROR),
        ("Deficit of BA stock 3 PC", MessageClass.CRITICAL_ERROR),
        ("Posting period 08 2026 is not open", MessageClass.CRITICAL_ERROR),
        ("Order has already been posted", MessageClass.CRITICAL_ERROR),
    ])
    def test_known_patterns(self, text, expected):
        assert check("E", text).message_class is expected

    def test_unrecognised_error_type_is_critical(self):
        assert check("E", "Something entirely new").message_class \
            is MessageClass.CRITICAL_ERROR

    def test_unrecognised_warning_is_unknown_not_ignored(self):
        result = check("W", "Something entirely new")
        assert result.message_class is MessageClass.UNKNOWN_MESSAGE
        assert not result.may_continue

    def test_critical_is_checked_before_retryable(self):
        """'already been posted' must never be retried."""
        assert check("E", "Order already been posted, try again later").message_class \
            is MessageClass.CRITICAL_ERROR


class TestWorst:
    def test_picks_the_most_severe(self):
        result = worst([
            classify("S", "Document 1 posted", BULK, SERIALISED),
            classify("W", f"Serial Number missing for {A_SERIALISED}", BULK, SERIALISED),
        ])
        assert result.message_class is MessageClass.CRITICAL_ERROR

    def test_expected_warning_loses_to_unknown(self):
        result = worst([
            classify("W", f"Serial Number missing for {A_BULK}", BULK, SERIALISED),
            classify("W", "Mystery message", BULK, SERIALISED),
        ])
        assert result.message_class is MessageClass.UNKNOWN_MESSAGE

    def test_no_messages_is_success(self):
        assert worst([]).message_class is MessageClass.SUCCESS


class TestUncertainty:
    def test_a_lock_is_a_clean_failure_and_can_be_retried(self):
        result = check("E", "Order 900000001 is locked by user SMITH")
        assert result.uncertain is False

    def test_a_timeout_leaves_the_outcome_unknown(self):
        assert check("E", "Connection time out").uncertain is True

    def test_a_terminated_update_leaves_the_outcome_unknown(self):
        assert check("E", "Update was terminated").uncertain is True

    def test_an_unrecognised_message_leaves_the_outcome_unknown(self):
        assert check("W", "Never seen this").uncertain is True

    def test_a_success_is_not_uncertain(self):
        assert check("S", "Document 4900012345 posted").uncertain is False
