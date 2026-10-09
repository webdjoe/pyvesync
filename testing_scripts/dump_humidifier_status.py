"""Dump raw VeSync device list and humidifier status for unsupported-device debugging.

Usage:
    python testing_scripts/dump_humidifier_status.py --email EMAIL --password PASSWORD \
        [--filter S451S] [--output vesync_dump.json] [--watch SECONDS]

Logs in, prints every device returned by the VeSync device list API (device type,
config module, firmware, etc.) and, for each device whose deviceType matches
``--filter``, issues a raw ``bypassV2`` ``getHumidifierStatus`` call so the full JSON
result can be shared in a GitHub issue or used to build a response model. This works
even when the device is not in pyvesync's device map. Account identifiers are redacted
from the output file.

With ``--watch SECONDS`` the status calls repeat at that interval and only the fields
that changed since the previous poll are printed, which helps catch transient states
(tank lifted, running dry, drying cycle). Each poll costs one API call per matching
device, so keep the interval modest to stay within the VeSync daily quota.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import sys
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
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


def _diff(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """Return the keys whose values differ between two status results."""
    return {
        k: new.get(k) for k in sorted(set(old) | set(new)) if old.get(k) != new.get(k)
    }


async def main(
    email: str, password: str, dev_filter: str, output: str, watch: int
) -> None:
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
        targets = [d for d in devices if pattern.search(d.get('deviceType', ''))]

        async def fetch_status(dev: dict[str, Any]) -> dict[str, Any] | None:
            """Call getHumidifierStatus for a raw device list entry."""
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
            r, _ = await manager.async_call_api(
                BYPASS_V2_BASE + 'bypassV2',
                'post',
                headers=Helpers.req_header_bypass(),
                json_object=body,
            )
            return r

        def status_key(dev: dict[str, Any]) -> str:
            return f'{dev.get("deviceName")} ({dev.get("deviceType")})'

        for dev in targets:
            logger.info(
                'Device %s (%s) %s pyvesync device map',
                dev.get('deviceName'),
                dev.get('deviceType'),
                'IS in' if dev.get('cid') in known else 'is NOT in',
            )
            r = await fetch_status(dev)
            logger.info('getHumidifierStatus:\n%s', json.dumps(r, indent=2))
            dump['status'][status_key(dev)] = redact(r)

        for hum in manager.devices.humidifiers:
            if pattern.search(hum.device_type):
                logger.info(
                    'pyvesync parsed state for %s:\n%s',
                    hum.device_name,
                    hum.state.to_json(indent=True),
                )

        if watch > 0:
            try:
                await watch_loop(manager, targets, fetch_status, status_key, dump, watch)
            finally:
                # Ctrl+C cancels the task; make sure what we have is written out.
                _write_dump(dump, output)
            return

    _write_dump(dump, output)


def _write_dump(dump: dict[str, Any], output: str) -> None:
    """Write the dump atomically so an interrupted run never leaves an empty file."""
    tmp = Path(output).with_suffix('.tmp')
    tmp.write_text(json.dumps(dump, indent=2), encoding='utf-8')
    tmp.replace(output)
    logger.info('Wrote redacted dump to %s', output)


async def watch_loop(
    manager: VeSync,
    targets: list[dict[str, Any]],
    fetch_status: Callable[[dict[str, Any]], Awaitable[dict[str, Any] | None]],
    status_key: Callable[[dict[str, Any]], str],
    dump: dict[str, Any],
    watch: int,
) -> None:
    """Poll matching devices and record only the fields that change."""
    del manager
    logger.info('Watching %d device(s) every %ds; Ctrl+C to stop', len(targets), watch)
    last: dict[str, dict[str, Any]] = {}
    for dev in targets:
        full = dump['status'].get(status_key(dev)) or {}
        last[dev['cid']] = (full.get('result') or {}).get('result') or {}
    dump['watch'] = []
    try:
        while True:
            await asyncio.sleep(watch)
            for dev in targets:
                r = await fetch_status(dev)
                inner = ((r or {}).get('result') or {}).get('result') or {}
                changed = _diff(last[dev['cid']], inner)
                if changed:
                    logger.info('%s changed: %s', dev.get('deviceName'), changed)
                    dump['watch'].append(
                        {
                            'time': datetime.now(UTC).isoformat(),
                            'device': dev.get('deviceName'),
                            'changed': changed,
                        }
                    )
                    last[dev['cid']] = inner
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info('Watch stopped')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--email', required=True)
    p.add_argument('--password', required=True)
    p.add_argument(
        '--filter', default='S451S', help='regex on deviceType (default S451S)'
    )
    p.add_argument('--output', default='vesync_dump.json')
    p.add_argument(
        '--watch',
        type=int,
        default=0,
        help='poll matching devices every N seconds and log changed fields',
    )
    a = p.parse_args()
    try:
        asyncio.run(main(a.email, a.password, a.filter, a.output, a.watch))
    except KeyboardInterrupt:
        logger.info('Interrupted')
