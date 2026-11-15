"""Схема секции метода измерений 1 (АМ) — заготовка.

Поля-заглушки подобраны по смыслу АМ-измерений (несущая, глубина
модуляции); при наполнении реальными элементами замените или дополните.
"""

SECTION_M1 = [
    {
        'label': 'Частота несущей',
        'type': 'freq_edit',
        'key': 'am_carrier',
        'text': '937,5 МГц',
    },
    {
        'label': 'Глубина модуляции',
        'type': 'value_edit',
        'key': 'am_depth',
        'text': '30',
    },
    {
        'label': None,
        'type': 'hbox',
        'items': [
            {'type': 'button', 'key': 'am_start', 'text': 'Старт'},
            {'type': 'spacer'},
            {'type': 'button', 'key': 'am_stop', 'text': 'Стоп'},
        ],
    },
]
