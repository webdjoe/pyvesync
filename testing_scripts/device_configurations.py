"""Get configuration details from the API."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import aiofiles
import orjson

from pyvesync import VeSync
from pyvesync.models.vesync_models import RequestDeviceConfiguration

USERNAME = ''
PASSWORD = ''

vs_logger = logging.getLogger('pyvesync')
vs_logger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def parse_config(data: dict) -> dict[str, list[dict]]:
    """Parse the configuration data from the API into a nested dictionary."""
    result = {}
    # Navigate to productLineList
    data = orjson.loads(orjson.dumps(data))  # Ensure data is a dict
    config_list = data.get('result', {}).get('configList', [])
    for config in config_list:
        for item in config.get('items', []):
            item_value = item.get('itemValue')
            if isinstance(item_value, str):
                item_value = orjson.loads(item_value)

            product_lines = item_value.get('productLineList', [])
            for product_line in product_lines:
                for type_info in product_line.get('typeInfoList', []):
                    type_name = type_info.get('typeName')
                    if not type_name:
                        continue
                    models = []
                    for model_info in type_info.get('modelInfoList', []):
                        model = model_info.get('model')
                        if not model:
                            continue
                        # Add the full model_info dict under the model key
                        models.append({model: [model_info]})
                    if models:
                        result[type_name] = models
    return result


async def fetch_config(manager: VeSync) -> dict[Any, Any] | None:
    """Get full device configuration from the API."""
    endpoint = '/cloud/v1/app/getAppConfigurationV2'
    body = RequestDeviceConfiguration(
        accountID=manager.account_id,
        token=manager.token,
    )
    response, _ = await manager.async_call_api(
        api=endpoint,
        method='post',
        json_object=body,
    )
    return response


async def main() -> None:
    """Main function to fetch and display device configurations."""
    async with VeSync(USERNAME, PASSWORD, 'US') as manager:
        await manager.login()
        config = await fetch_config(manager)
        if not config:
            print('Failed to fetch configuration.')
            return
        parsed_config = parse_config(config)
        print(orjson.dumps(parsed_config, option=orjson.OPT_INDENT_2).decode('utf-8'))
        output_path = Path('models.json')
        async with aiofiles.open(output_path, 'w', encoding='utf-8') as file:
            await file.write(
                orjson.dumps(parsed_config, option=orjson.OPT_INDENT_2).decode('utf-8')
            )


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
