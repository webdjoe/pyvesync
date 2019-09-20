"""Helper functions for VeSync API."""

import hashlib
import logging
import time
import requests

logger = logging.getLogger(__name__)

API_BASE_URL = 'https://smartapi.vesync.com'
API_RATE_LIMIT = 30
API_TIMEOUT = 5

DEFAULT_TZ = 'America/New_York'

APP_VERSION = '2.5.1'
PHONE_BRAND = 'SM N9005'
PHONE_OS = 'Android'
MOBILE_ID = '1234567890123456'
USER_TYPE = '1'


class Helpers:
    """VeSync Helper Functions."""

    @staticmethod
    def req_headers(manager):
        """Build header for api requests."""
        headers = {
            'accept-language': 'en',
            'accountId': manager.account_id,
            'appVersion': APP_VERSION,
            'content-type': 'application/json',
            'tk': manager.token,
            'tz': manager.time_zone
        }
        return headers

    @staticmethod
    def req_body_base(manager):
        """Return universal keys for body of api requests."""
        return {
            'timeZone': manager.time_zone,
            'acceptLanguage': 'en'
        }

    @staticmethod
    def req_body_auth(manager):
        """Keys for authenticating api requests."""
        return {
            'accountID': manager.account_id,
            'token': manager.token
        }

    @staticmethod
    def req_body_details():
        """Detail keys for api requests."""
        return {
            'appVersion': APP_VERSION,
            'phoneBrand': PHONE_BRAND,
            'phoneOS': PHONE_OS,
            'traceId': str(int(time.time()))
        }

    @classmethod
    def req_body(cls, manager, type_):
        """Builder for body of api requests."""
        body = {}

        if type_ == 'login':
            body = {
                **cls.req_body_base(manager),
                **cls.req_body_details()
            }
            body['email'] = manager.username
            body['password'] = cls.hash_password(manager.password)
            body['devToken'] = ''
            body['userType'] = USER_TYPE
            body['method'] = 'login'
        elif type_ == 'devicedetail':
            body = {
                **cls.req_body_base(manager),
                **cls.req_body_auth(manager),
                **cls.req_body_details()
            }
            body['method'] = 'devicedetail'
            body['mobileId'] = MOBILE_ID
        elif type_ == 'devicelist':
            body = {
                **cls.req_body_base(manager),
                **cls.req_body_auth(manager),
                **cls.req_body_details(),
            }
            body['method'] = 'devices'
            body['pageNo'] = '1'
            body['pageSize'] = '50'
        elif type_ == 'devicestatus':
            body = {
                **cls.req_body_base(manager),
                **cls.req_body_auth(manager)
            }
        elif type_ == 'energy_week':
            body = {
                **cls.req_body_base(manager),
                **cls.req_body_auth(manager),
                **cls.req_body_details()
            }
            body['method'] = 'energyweek'
            body['mobileId'] = MOBILE_ID
        elif type_ == 'energy_month':
            body = {
                **cls.req_body_base(manager),
                **cls.req_body_auth(manager),
                **cls.req_body_details()
            }
            body['method'] = 'energymonth'
            body['mobileId'] = MOBILE_ID
        elif type_ == 'energy_year':
            body = {
                **cls.req_body_base(manager),
                **cls.req_body_auth(manager),
                **cls.req_body_details()
            }
            body['method'] = 'energyyear'
            body['mobileId'] = MOBILE_ID
        elif type_ == 'bypass':
            body = {
                **cls.req_body_base(manager),
                **cls.req_body_auth(manager),
                **cls.req_body_details()
            }
            body['method'] = 'bypass'
        elif type_ == 'bypass_config':
            body = {
                **cls.req_body_base(manager),
                **cls.req_body_auth(manager),
                **cls.req_body_details()
            }
            body['method'] = 'firmwareUpdateInfo'

        return body

    @staticmethod
    def calculate_hex(hex_string):
        """Credit for conversion to itsnotlupus/vesync_wsproxy."""
        hex_conv = hex_string.split(':')
        converted_hex = (int(hex_conv[0], 16) + int(hex_conv[1], 16))/8192

        return converted_hex

    @staticmethod
    def hash_password(string):
        """Encode password."""
        return hashlib.md5(string.encode('utf-8')).hexdigest()

    @staticmethod
    def call_api(api: str, method: str,
                 json: dict = None, headers: dict = None):
        """Make API calls by passing endpoint, header and body."""
        response = None
        status_code = None

        try:
            logger.debug("[%s] calling '%s' api", method, api)
            if method == 'get':
                r = requests.get(
                    API_BASE_URL + api, json=json,
                    headers=headers, timeout=API_TIMEOUT
                )
            elif method == 'post':
                r = requests.post(
                    API_BASE_URL + api, json=json,
                    headers=headers, timeout=API_TIMEOUT
                )
            elif method == 'put':
                r = requests.put(
                    API_BASE_URL + api, json=json,
                    headers=headers, timeout=API_TIMEOUT
                )
        except requests.exceptions.RequestException as e:
            logger.waring(e)
        except Exception as e:
            logger.warning(e)
        else:
            if r.status_code == 200:
                status_code = 200
                response = r.json()
            else:
                logger.debug('Unable to fetch %s%s', API_BASE_URL, api)
        finally:
            return (response, status_code)

    @staticmethod
    def code_check(r: dict) -> bool:
        """Test if code == 0 for successful API call."""
        if isinstance(r, dict) and r.get("code") == 0:
            return True
        return False

    @staticmethod
    def build_details_dict(r: dict) -> dict:
        """Build details dictionary from API response."""
        return {
            'active_time': r.get('activeTime', 0),
            'energy': r.get('energy', 0),
            'night_light_status': r.get('nightLightStatus', None),
            'night_light_brightness': r.get('nightLightBrightness', None),
            'night_light_automode': r.get('nightLightAutomode', None),
            'power': r.get('power', 0),
            'voltage': r.get('voltage', 0)
        }

    @staticmethod
    def build_energy_dict(r: dict) -> dict:
        """Build energy dictionary from API response."""
        return {
            'energy_consumption_of_today': r.get(
                'energyConsumptionOfToday', 0),
            'cost_per_kwh': r.get('costPerKWH', 0),
            'max_energy': r.get('maxEnergy', 0),
            'total_energy': r.get('totalEnergy', 0),
            'currency': r.get('currency', 0),
            'data': r.get('data', 0)
        }

    @staticmethod
    def build_config_dict(r: dict) -> dict:
        """Build configuration dictionary from API response."""
        if r.get("theshold") is not None:
            threshold = r.get('threshold')
        else:
            threshold = r.get('threshHold')
        return {
            'current_firmware_version': r.get("currentFirmVersion"),
            'latest_firmware_version': r.get("latestFirmVersion"),
            'maxPower': r.get("maxPower"),
            'threshold': threshold,
            'power_protection': r.get("powerProtectionStatus"),
            'energy_saving_status': r.get("energySavingStatus")
        }
