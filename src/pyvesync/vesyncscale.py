"""VeSync API for controlling scales."""

import json
from pyvesync.vesyncbasedevice import VeSyncBaseDevice
from pyvesync.helpers import Helpers as helpers
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class VeSyncESF24(VeSyncBaseDevice):
    """Etekcity BT ESF24 Scale Class."""

    def __init__(self, details, manager):
        """Initilize ES14 Class."""
        super(VeSyncESF24, self).__init__(details, manager)

        self.details = {}
        self.user_list = []

    def bt_data_builder(self, data: list):
        """Build weighing data dictionary."""
        data_dict = defaultdict(list)
        for point in data:
            if point.get('subUserID') is None:
                point['subUserID'] = 0
            data_dict[point.get('subUserID')].append(point)
        return data_dict

    def get_details(self):
        """Build details dictionary."""
        body = helpers.req_body(self.manager, 'devicedetail')
        body['pageSize'] = 100
        body['page'] = 1
        body['debugMode'] = False
        body['allData'] = True
        body['method'] = 'getWeighingDataV2'
        body['configModule'] = self.config_module
        head = helpers.req_headers(self.manager)

        r, _ = helpers.call_api(
            '/cloud/v2/deviceManaged/getWeighingDataV2',
            method='post',
            headers=head,
            json=body
        )
        subuser_dict = {}
        if r is not None and helpers.code_check(r):
            if not isinstance(r.get('result', {}).get('weightDatas'), list):
                logger.warning("Error in getting %s weight data", self.device_name)
                return
            subuser_dict = self.bt_data_builder(r.get('result').get('weightDatas'))

        self.details = subuser_dict

    def firmware_update(self) -> bool:
        """Override firmware update method."""
        return False

    def update(self):
        """Get weighing data and set data dictionaries."""
        self.get_details()
        user_list = self.get_subusers()
        self.user_list = user_list

    def get_subusers(self):
        """Get list of subusers"""
        user_list = []
        if len(self.details) > 0:
            for user in self.details:
                user_list.append(user)
        return user_list

    def get_user_data(self, user=0) -> list:
        """Get list of one users data points as list of dicts."""
        if len(self.get_subusers()) == 1:
            user = self.get_subusers()[0]
        if user is None or user not in self.user_list:
            logger.debug('Subuser not found - %s', user)
            return []
        return self.details[user]

    def user_dict(self, user=0) -> dict:
        """Return Dict of User Data in Grams"""
        user_dict = {}
        if user is None or user not in self.user_list:
            logger.debug('Subuser not found - %s', user)
            return user_dict
        for point in self.details.get(user):
            timestamp = point.get('timestamp')
            weight = point.get('weightG')
            user_dict[timestamp] = weight
        return user_dict

    def user_json_kg(self, user=0):
        """Return JSON of User Data timestamp: weight"""
        user_dict = self.user_dict(user)
        json_dict = {}
        for k, v in user_dict.items():
            if isinstance(v, float) or isinstance(v, int):
                json_dict[k] = v/1000
        return json.dumps(json_dict)

    def user_json_lb(self, user=0):
        """Return JSON of User Data timestamp: weight"""
        user_dict = self.user_dict(user)
        json_dict = {}
        for k, v in user_dict.items():
            if isinstance(v, float) or isinstance(v, int):
                json_dict[k] = v/453.592
        return json.dumps(json_dict)