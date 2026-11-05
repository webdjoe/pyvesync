"""Unit tests for ErrorCodes.get_error_info() and Helpers.parse_error_code()."""

from pyvesync.utils.errors import ErrorCodes, ErrorTypes
from pyvesync.utils.helpers import Helpers

# CAF-DC111S-AEU endCook on an idle chamber (DC111 HAR, PR #536). The code has
# no ErrorCodes entry, and none in the APK's CloudErrorCode either.
END_COOK_IDLE = {
    'traceId': 'TRACE_ID',
    'code': 0,
    'msg': 'request success',
    'result': {
        'traceId': 'TRACE_ID',
        'code': 11923000,
        'msg': 'af_iot_bypass_end_cook',
        'result': {},
    },
}


def test_unknown_code_keeps_code_and_msg():
    info = ErrorCodes.get_error_info(11923000, 'af_iot_bypass_end_cook')
    assert info.name == 'UNKNOWN'
    assert info.error_type == ErrorTypes.UNKNOWN_ERROR
    assert info.code == 11923000
    assert 'af_iot_bypass_end_cook' in info.message


def test_unknown_inner_code_from_bypassv2_response():
    info = Helpers.parse_error_code(END_COOK_IDLE)
    assert info.name == 'UNKNOWN'
    assert info.code == 11923000
    assert 'af_iot_bypass_end_cook' in info.message


def test_unknown_code_without_msg():
    info = ErrorCodes.get_error_info(11923000)
    assert info.code == 11923000
    assert info.message == 'Unknown error'


def test_non_numeric_code_keeps_msg():
    info = ErrorCodes.get_error_info('abc', 'oops')
    assert info.name == 'UNKNOWN'
    assert info.code is None
    assert 'oops' in info.message


def test_known_code_matches_on_thousand():
    # Regression guard: the APK and pyvesync both look up (code / 1000) * 1000.
    info = ErrorCodes.get_error_info(11910123, 'busy')
    assert info.name == 'BYPASS_LEFT_ZONE_COOKING'
    assert info.code == 11910123
    assert info.message.endswith(' - busy')


def test_unknown_lookup_does_not_change_the_shared_entry():
    ErrorCodes.get_error_info(11923000, 'first')
    info = ErrorCodes.get_error_info(11923000, 'second')
    assert 'first' not in info.message
