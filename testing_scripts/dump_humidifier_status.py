"""Dump raw VeSync device list and humidifier status for unsupported-device debugging.

Usage:
    python testing_scripts/dump_humidifier_status.py --email EMAIL --password PASSWORD \
        [--filter S451S] [--output vesync_dump.json]

Logs in, prints every device returned by the VeSync device list API (device type,
config module, firmware, etc.) and, for each device whose deviceType matches
``--filter``, issues a raw ``bypassV2`` ``getHumidifierStatus`` call so the full JSON
result can be shared in a GitHub issue or used to build a response model. This works
even when the device is not in pyvesync's device map. Account identifiers are redacted
from the output file.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

from pyvesync import VeSync
from pyvesync.models.vesync_models import RequestDeviceListModel
from pyvesync.utils.device_mixins import BYPASS_V2_BASE
from pyvesync.utils.helpers import Helpers

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s: %(message)s')
logging.getLogger('pyvesync').setLevel(logging.DEBUG)
logger = logging.getLogger('dump')

REDACT_KEYS = {'cid', 'uuid', 'macID', 'accountID', 'token', 'deviceId', 'ownerShip'}
REQUEST_KEYS = (
    'acceptLanguage',
    'appVersion',
    'phoneBrand',
    'phoneOS',
    'accountID',
    'debugMode',
    'traceId',
    'timeZone',
    'token',
    'userCountryCode',
)


def redact(obj: Any) -> Any:  # noqa: ANN401
    """Recursively redact identifying keys."""
    if isinstance(obj, dict):
        return {
            k: ('<redacted>' if k in REDACT_KEYS else redact(v)) for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [redact(i) for i in obj]
    return obj


async def main(email: str, password: str, dev_filter: str, output: str) -> None:
    """Run the dump."""
    async with VeSync(email, password) as manager:
        if not await manager.login():
            logger.error('Login failed')
            sys.exit(1)

        # Raw device list (includes devices pyvesync does not know about)
        req = RequestDeviceListModel(
            token=manager.auth.token,
            accountID=manager.auth.account_id,
            timeZone=manager.time_zone,
        )
        resp, _ = await manager.async_call_api(
            '/cloud/v1/deviceManaged/devices',
            'post',
            headers=Helpers.req_header_bypass(),
            json_object=req.to_dict(),
        )
        devices = (resp or {}).get('result', {}).get('list', []) or []
        logger.info('Device list returned %d devices', len(devices))
        for dev in devices:
            logger.info(
                '  %-30s type=%-18s configModule=%-28s firm=%s',
                dev.get('deviceName'),
                dev.get('deviceType'),
                dev.get('configModule'),
                dev.get('currentFirmVersion'),
            )

        await manager.update()
        known = {d.cid for d in manager.devices}
        dump: dict[str, Any] = {'device_list': redact(devices), 'status': {}}

        pattern = re.compile(dev_filter, re.IGNORECASE)
        for dev in devices:
            if not pattern.search(dev.get('deviceType', '')):
                continue
            logger.info(
                'Device %s (%s) %s pyvesync device map',
                dev.get('deviceName'),
                dev.get('deviceType'),
                'IS in' if dev.get('cid') in known else 'is NOT in',
            )
            body = Helpers.get_defaultvalues_attributes(REQUEST_KEYS).copy()
            body.update(Helpers.get_manager_attributes(manager, REQUEST_KEYS))
            body.update(
                {
                    'method': 'bypassV2',
                    'cid': dev['cid'],
                    'deviceId': dev['cid'],
                    'configModule': dev.get('configModule'),
                    'configModel': dev.get('configModule'),
                    'payload': {
                        'method': 'getHumidifierStatus',
                        'source': 'APP',
                        'data': {},
                    },
                }
            )
            r, status = await manager.async_call_api(
                BYPASS_V2_BASE + 'bypassV2',
                'post',
                headers=Helpers.req_header_bypass(),
                json_object=body,
            )
            logger.info(
                'getHumidifierStatus HTTP %s:\n%s', status, json.dumps(r, indent=2)
            )
            # Key by name as well as type so several units of one model do not overwrite
            key = f"{dev.get('deviceName')} ({dev.get('deviceType')})"
            dump['status'][key] = redact(r)

        for hum in manager.devices.humidifiers:
            if pattern.search(hum.device_type):
                logger.info(
                    'pyvesync parsed state for %s:\n%s',
                    hum.device_name,
                    hum.state.to_json(indent=True),
                )

    Path(output).write_text(  # noqa: ASYNC240 - one-off write after API calls finish
        json.dumps(dump, indent=2), encoding='utf-8'
    )
    logger.info('Wrote redacted dump to %s', output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--email', required=True)
    p.add_argument('--password', required=True)
    p.add_argument(
        '--filter', default='S451S', help='regex on deviceType (default S451S)'
    )
    p.add_argument('--output', default='vesync_dump.json')
    a = p.parse_args()
    asyncio.run(main(a.email, a.password, a.filter, a.output))
