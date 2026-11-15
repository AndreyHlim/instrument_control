"""Схема секции метода измерений 2 (ЧМ) — заготовка."""

SECTION_M2 = [
    {
        'label': 'Частота несущей',
        'type': 'freq_edit',
        'key': 'fm_carrier',
        'text': '100 МГц',
    },
    {
        'label': 'Девиация',
        'type': 'value_edit',
        'key': 'fm_deviation',
        'text': '75',
    },
    {
        'label': None,
        'type': 'hbox',
        'items': [
            {'type': 'button', 'key': 'fm_start', 'text': 'Старт'},
            {'type': 'spacer'},
            {'type': 'button', 'key': 'fm_stop', 'text': 'Стоп'},
        ],
    },
]
