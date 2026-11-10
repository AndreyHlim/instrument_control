RBW_TYPES_FILTER = ['Normal (3dB)', 'CISPR (6dB)', 'Cannel',
                    'RRC', '5-Pole', 'MIL (6dB)']

FREQ_DIM = {
    'ГГц': 1e9,
    'МГц': 1e6,
    'кГц': 1e3,
    'Гц': 1.0,
}

AMP_UNITS = ['dBm', 'dBµV', 'dBmV', 'V', 'W',
             'dBV', 'dBµV/Hz', 'dBmV/Hz', 'dBµV/m']

PREAMP_VAL = ['Off', '15 dB', '30 dB']

SIGNAL_FORMS = ['SINusoid', 'SQUare', 'RAMP',
                'NRAMp', 'TRIangle', 'NOISe']

DETECTORS_FSVA = {
    'Auto Peak': 'APE',
    'Positive Peak': 'POS',
    'Negative Peak': 'NEG',
    'RMS': 'RMS',
    'Average': 'AVER',
    'Sample': 'SAMP',
    'Quasi-Peak': 'QPE',
}
DETECTORS_FSVA_REV = {v: k for k, v in DETECTORS_FSVA.items()}

TRACE_ACC = {
    'Clear Write': 'WRIT',
    'Max Hold': 'MAXH',
    'Min Hold': 'MINH',
    'Average': 'AVER',
    'View': 'VIEW',
    'Blank': 'BLAN',
}
TRACE_ACC_REV = {v: k for k, v in TRACE_ACC.items()}

ANT_NAMES = {
    "''": 'Не выбрана (0 дБ)',
    "'VULB-9160'": 'VULB9160 зав.№ 9160-3397',
    "'P6-59-886'": 'П6-59 зав.№ 886',
    "'P6-59-885'": 'П6-59 зав.№ 885',
}
