from constants import DETECTORS_FSVA
from gui.styles import Style

"""Схема секции метода измерений 1.

SECTION_M1 — верхняя часть секции (кнопки файлов и добавления частот),
применяется общим циклом панелей. SECTION_M1_BOTTOM — нижняя часть
(чекбоксы, накопления, S/N/Стоп), применяется миксином метода ПОСЛЕ
добавления таблицы — иначе она встанет ниже этого ряда.
"""

SECTION_M1 = [
    {
        'label': None,
        'type': 'hbox',
        'items': [
            {'type': 'button', 'key': 'm1_open',
             'icon': 'gui/icons/open_file.png', 'style': Style.BUT_SQUARE},
            {'type': 'button', 'key': 'm1_save',
             'icon': 'gui/icons/save_file.png', 'style': Style.BUT_SQUARE},
            {'type': 'button', 'key': 'm1_clear',
             'icon': 'gui/icons/clear.png', 'style': Style.BUT_SQUARE},
            {'type': 'spacer'},
            {'type': 'button', 'key': 'm1_add_cf', 'text': '+Fц',
                'style': Style.H_20},
            {'type': 'button', 'key': 'm1_add_mrk', 'text': '+Fмрк',
                'style': Style.H_20},
            {'type': 'button', 'key': 'm1_add_df', 'text': '+∆Fмрк',
                'style': Style.H_20},
            {'type': 'spacer'},
            {'type': 'button', 'key': 'm1_search',
                'icon': 'gui/icons/search.png', 'style': Style.BUT_SQUARE},
        ],
    },
]

SECTION_M1_BOTTOM = [
    {
        'label': None,
        'type': 'hbox',
        'items': [
            {
                'type': 'label',
                'key': 'lbl_det_s_meas',
                'text': 'Детекторы: S',
            },
            {
                'type': 'combo',
                'key': 'm1_det_s',
                'style': Style.COMBO_BOX,
                'items': list(DETECTORS_FSVA),
                'value': list(DETECTORS_FSVA)[1],
            },
            {
                'type': 'label',
                'key': 'lbl_det_n_meas',
                'text': 'N',
                'align': 'right',
            },
            {
                'type': 'combo',
                'key': 'm1_det_n',
                'style': Style.COMBO_BOX,
                'items': list(DETECTORS_FSVA),
                'value': list(DETECTORS_FSVA)[1],
            },
        ]
    },
    {
        'label': None,
        'type': 'hbox',
        'items': [
            {'type': 'button', 'key': 'm1_s', 'text': 'S',
             'style': Style.H_20, 'stretch': 1},
            {'type': 'button', 'key': 'm1_n', 'text': 'N',
             'style': Style.H_20, 'stretch': 1},
            {'type': 'button', 'key': 'm1_stop', 'text': 'Стоп',
             'style': Style.H_20, 'stretch': 1},
            {'type': 'double', 'key': 'm1_accum', 'min': 1, 'max': 100,
             'decimals': 0, 'value': 10, 'style': Style.SPIN_BOX,
             'stretch': 1},
            {'type': 'checkbox', 'key': 'm1_sel_only', 'text': 'Select',
             'stretch': 1},
            {'type': 'checkbox', 'key': 'm1_screens', 'text': 'Screen',
             'value': True, 'stretch': 1},
        ],
    },
]
