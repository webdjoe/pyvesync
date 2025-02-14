"""pyvesync library constants."""


# Error Codes
RATE_LIMIT_CODES = [-11103086, -11000086]


HUMID_FEATURES: dict = {
    'Classic300S': {
        'module': 'VeSyncHumid200300S',
        'models': ['Classic300S', 'LUH-A601S-WUSB', 'LUH-A601S-AUSW'],
        'features': ['nightlight'],
        'mist_modes': ['auto', 'sleep', 'manual'],
        'mist_levels': list(range(1, 10))
    },
    'Classic200S': {
        'module': 'VeSyncHumid200S',
        'models': ['Classic200S'],
        'features': [],
        'mist_modes': ['auto', 'manual'],
        'mist_levels': list(range(1, 10))
    },
    'Dual200S': {
        'module': 'VeSyncHumid200300S',
        'models': ['Dual200S',
                   'LUH-D301S-WUSR',
                   'LUH-D301S-WJP',
                   'LUH-D301S-WEU'],
        'features': [],
        'mist_modes': ['auto', 'manual'],
        'mist_levels': list(range(1, 3))
    },
    'LV600S': {
        'module': 'VeSyncHumid200300S',
        'models': ['LUH-A602S-WUSR',
                   'LUH-A602S-WUS',
                   'LUH-A602S-WEUR',
                   'LUH-A602S-WEU',
                   'LUH-A602S-WJP',
                   'LUH-A602S-WUSC'],
        'features': ['warm_mist', 'nightlight'],
        'mist_modes': ['humidity', 'sleep', 'manual'],
        'mist_levels': list(range(1, 10)),
        'warm_mist_levels': [0, 1, 2, 3]
    },
    'OASISMISTEU': {
            'module': 'VeSyncHumid200300S',
            'models': ['LUH-O451S-WEU'],
            'features': ['warm_mist', 'nightlight'],
            'mist_modes': ['auto', 'manual'],
            'mist_levels': list(range(1, 10)),
            'warm_mist_levels': list(range(4))
    },
    'OASISMIST': {
            'module': 'VeSyncHumid200300S',
            'models': ['LUH-O451S-WUS',
                       'LUH-O451S-WUSR',
                       'LUH-O601S-WUS',
                       'LUH-O601S-KUS'],
            'features': ['warm_mist'],
            'mist_modes': ['auto', 'humidity', 'sleep', 'manual'],
            'mist_levels': list(range(1, 10)),
            'warm_mist_levels': list(range(4))
    },
    'OASISMIST1000S': {
            'module': 'VeSyncHumid1000S',
            'models': ['LUH-M101S-WUS'],
            'features': [],
            'mist_modes': ['auto', 'sleep', 'manual'],
            'mist_levels': list(range(1, 10))
    },
    'Superior6000S': {
            'module': 'VeSyncSuperior6000S',
            'models': ['LEH-S601S-WUS', 'LEH-S601S-WUSR'],
            'features': [],
            'mist_modes': ['auto', 'humidity', 'sleep', 'manual'],
            'mist_levels': list(range(1, 10))
    }
}


AIR_FEATURES: dict = {
    'Core200S': {
        'module': 'VeSyncAirBypass',
        'models': ['Core200S', 'LAP-C201S-AUSR', 'LAP-C202S-WUSR'],
        'modes': ['sleep', 'off', 'manual'],
        'features': ['reset_filter'],
        'levels': list(range(1, 4))
    },
    'Core300S': {
        'module': 'VeSyncAirBypass',
        'models': ['Core300S', 'LAP-C301S-WJP', 'LAP-C302S-WUSB', 'LAP-C301S-WAAA'],
        'modes': ['sleep', 'off', 'auto', 'manual'],
        'features': ['air_quality'],
        'levels': list(range(1, 5))
    },
    'Core400S': {
        'module': 'VeSyncAirBypass',
        'models': ['Core400S',
                   'LAP-C401S-WJP',
                   'LAP-C401S-WUSR',
                   'LAP-C401S-WAAA'],
        'modes': ['sleep', 'off', 'auto', 'manual'],
        'features': ['air_quality'],
        'levels': list(range(1, 5))
    },
    'Core600S': {
        'module': 'VeSyncAirBypass',
        'models': ['Core600S',
                   'LAP-C601S-WUS',
                   'LAP-C601S-WUSR',
                   'LAP-C601S-WEU'],
        'modes': ['sleep', 'off', 'auto', 'manual'],
        'features': ['air_quality'],
        'levels': list(range(1, 5))
    },
    'LV-PUR131S': {
        'module': 'VeSyncAir131',
        'models': ['LV-PUR131S', 'LV-RH131S'],
        'modes': ['manual', 'auto', 'sleep', 'off'],
        'features': ['air_quality'],
        'levels': list(range(1, 3))
    },
    'Vital100S': {
        'module': 'VeSyncAirBaseV2',
        'models': ['LAP-V102S-AASR', 'LAP-V102S-WUS', 'LAP-V102S-WEU',
                   'LAP-V102S-AUSR', 'LAP-V102S-WJP'],
        'modes': ['manual', 'auto', 'sleep', 'off', 'pet'],
        'features': ['air_quality'],
        'levels': list(range(1, 5))
    },
    'Vital200S': {
        'module': 'VeSyncAirBaseV2',
        'models': ['LAP-V201S-AASR', 'LAP-V201S-WJP', 'LAP-V201S-WEU',
                   'LAP-V201S-WUS', 'LAP-V201-AUSR', 'LAP-V201S-AUSR',
                   'LAP-V201S-AEUR'],
        'modes': ['manual', 'auto', 'sleep', 'off', 'pet'],
        'features': ['air_quality'],
        'levels': list(range(1, 5))
    },
    'EverestAir': {
        'module': 'VeSyncAirBaseV2',
        'models': ['LAP-EL551S-AUS', 'LAP-EL551S-AEUR',
                   'LAP-EL551S-WEU', 'LAP-EL551S-WUS'],
        'modes': ['manual', 'auto', 'sleep', 'off', 'turbo'],
        'features': ['air_quality', 'fan_rotate'],
        'levels': list(range(1, 4))
    },
    'SmartTowerFan': {
        'module': 'VeSyncTowerFan',
        'models': ['LTF-F422S-KEU', 'LTF-F422S-WUSR', 'LTF-F422_WJP', 'LTF-F422S-WUS'],
        'modes': ['normal', 'auto', 'advancedSleep', 'turbo', 'off'],
        'set_mode_method': 'setTowerFanMode',
        'features': ['fan_speed'],
        'levels': list(range(1, 13))
    }
}