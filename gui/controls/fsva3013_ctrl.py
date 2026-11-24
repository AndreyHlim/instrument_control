from constants import (ADD_TRACE, AMP_UNITS, ANT_NAMES, DETECTORS_FSVA,
                       MARKER_TRACES, PREAMP_VAL, RBW_TYPES_FILTER, TRACE_ACC,
                       TRACE_MODES)
from gui.styles import Style

# ВЫПАДАЮЩИЙ СПИСОК ЭЛЕМЕНТОВ ДЛЯ УПРАВЛЕНИЯ АМПЛИТУДОЙ
SECTION_AMP = [
    # Ref lvl и Range
    {
        "label": "Ref lvl",
        "widgets": [
            {
                "type": "value_edit",
                "key": "label_reflevel",
                "stretch": 1,
                "style": Style.LBL_BORDER,
            },
            {
                "type": "combo",
                "key": "amp_unit",
                "items": AMP_UNITS,
                "stretch": 1,
                'style': Style.COMBO_BOX,
            },
            {
                'type': 'label',
                'text': 'Range, dB',
                'key': 'lbl_range',
                "stretch": 1,
                'align': 'right',
            },
            {
                "type": "value_edit",
                "key": "label_range",
                "stretch": 1,
                "style": Style.LBL_BORDER,
            },
        ]
    },
    # Atten и PreAmp
    {
        "label": "Atten, dB",
        "widgets": [
            {
                "type": "value_edit",
                "key": "label_atten",
                "stretch": 1,
                "style": Style.LBL_BORDER,
            },
            {
                'type': 'checkbox',
                'key': 'atten_auto',
                'text': 'Auto         ',
                "stretch": 1,
            },
            {
                "type": "label",
                "text": "PreAmp",
                "stretch": 1,
                "key": "label_preamp",
                "align": "right",
            },
            {
                "type": "combo",
                "key": "combo_preamp",
                "items": PREAMP_VAL,
                "stretch": 1,
                'style': Style.COMBO_BOX,
            },
        ]
    },
    {
        'type': 'combo',
        'label': 'Калибровка',
        'key': 'combo_transducer',
        'items': ANT_NAMES.values(),
        'style': Style.COMBO_BOX,
    },
]

# ВЫПАДАЮЩИЙ СПИСОК ЭЛЕМЕНТОВ ДЛЯ УПРАВЛЕНИЯ ЧАСТОТОЙ
SECTION_FREQ = [
    # Center и Step
    {
        "label": "Center",
        "widgets": [
            {
                'type': 'button',
                "key": "but_cf_up",
                "text": "▲",
                "stretch": 1,
                "style": Style.BUT_SQUARE,
            },
            {
                'type': 'button',
                "key": "but_cf_down",
                "text": "▼",
                "stretch": 1,
                "style": Style.BUT_SQUARE,
            },
            {
                "type": "freq_edit",
                "key": "label_center",
                "text": "",
                "stretch": 4,
                "style": Style.LBL_BORDER,
            },
            {
                'type': 'label',
                'key': 'lbl_step',
                'text': 'Шаг',
                "stretch": 1,
            },
            {
                "type": "freq_edit",
                "key": "tb_cfstep",
                "stretch": 3,
                "style": Style.LBL_BORDER,
            },
            {
                'type': 'button',
                "key": "but_stepcf_set_span",
                "text": "=Span",
                "stretch": 2,
                "style": Style.VAL_CFSTEP_TO_SPAN,
            },
        ]
    },
    # Span
    {
        "label": "Span",
        "widgets": [
            {
                "type": "freq_edit",
                "key": "label_span",
                "stretch": 4,
                "style": Style.LBL_BORDER,
            },
            {
                'type': 'button',
                "key": "but_span_set_stepcf",
                "text": "=Шаг",
                "stretch": 2,
                "style": Style.BUT_SPAN_TO_STEPCF,
            },
            {
                'type': 'button',
                "key": "but_span_set_div2",
                "text": "/2",
                "stretch": 1,
                "style": Style.BUT_SQUARE,
            },
            {
                'type': 'button',
                "key": "but_span_set_mul2",
                "text": "*2",
                "stretch": 1,
                "style": Style.BUT_SQUARE,
            },
        ]

    },
    {
        'label': 'Старт',
        'widgets': [
            {
                'type': 'freq_edit',
                'key': 'freq_start',
                "stretch": 8,
                "style": Style.LBL_BORDER,
            },
            {
                'type': 'label',
                'key': 'lbl_stop',
                "stretch": 1,
                'text': 'Стоп',
                'align': 'right',
            },
            {
                'type': 'freq_edit',
                'key': 'freq_stop',
                "stretch": 7,
                "style": Style.LBL_BORDER,
            },
        ]
    }
]

# ВЫПАДАЮЩИЙ СПИСОК ЭЛЕМЕНТОВ ДЛЯ УПРАВЛЕНИЯ RBW/VBW
SECTION_RBW = [
    {
        "type": "combo",
        "label": "Фильтр",
        "key": "rbw_type_filter",
        "items": RBW_TYPES_FILTER,
        'style': Style.COMBO_BOX,
    },
    {
        "label": "RBW",
        "widgets": [
            {
                "type": "wheel_label",
                "key": "label_rbw",
                "stretch": 8,
                "style": Style.LBL_BORDER,
            },
            {
                "type": "checkbox",
                "key": "rbw_auto",
                "text": "Auto",
                "value": False,
                "stretch": 1,
            },
            {
                'type': 'label',
                'key': 'lbl_vbw',
                "text": "VBW",
                "stretch": 1,
            },
            {
                "type": "wheel_label",
                "key": "label_vbw",
                "stretch": 8,
                "style": Style.LBL_BORDER,
            },
            {
                "type": "checkbox",
                "key": "vbw_auto",
                "text": "Auto",
                "value": False,
                "stretch": 1,
            },
        ]
    },
]

# ВЫПАДАЮЩИЙ СПИСОК ЭЛЕМЕНТОВ ДЛЯ УПРАВЛЕНИЯ SWEEP
SECTION_SWEEP = [
    {
        'label': 'Режим Sweep',
        'widgets': [
            {
                'type': 'radio',
                'key': 'radio_count',
                'text': 'continuously',
                'checked': False,
                "stretch": 1,
            },
            {
                'type': 'radio',
                'key': 'radio_single',
                'text': 'single',
                'checked': False,
                "stretch": 1,
            },
            {
                "type": "double",
                "key": "tb_sweep_count",
                "min": 1,
                "max": 50,
                'decimals': 0,
                "value": 1,
                "stretch": 1,
                "style": Style.SPIN_BOX,
            },
        ]
    }
]

# ВЫПАДАЮЩИЙ СПИСОК ЭЛЕМЕНТОВ ДЛЯ УПРАВЛЕНИЯ TRACES
SECTION_TRACES = [
    {
        'label': 'Основная:',
        'widgets': [
            {
                "type": "combo",
                "label": "Детектор",
                "key": "combo_det",
                "items": DETECTORS_FSVA.keys(),
                'style': Style.COMBO_BOX,
                'stretch': 1,
            },
            {
                "type": "combo",
                "label": "Накопление",
                "key": "combo_trace_acc",
                "items": list(TRACE_ACC.keys())[:4],
                'style': Style.COMBO_BOX,
                'stretch': 1,
            },
            {
                'type': 'checkbox',
                'key': 'chk_main_visible',
                'text': '',
                'value': True,          # True по умолчанию — трасса видна
                'stretch': 1,
                'style': Style.CHECKBOX,
            },
        ]
    },
    {
        'label': 'Трасса 1:',
        'widgets': [
            {
                'type': 'combo',
                'key': 'trc_1_acc',         # тип накопления
                'items': ADD_TRACE,
                'value': ADD_TRACE[0],      # 'Максимум'
                'style': Style.COMBO_BOX,
                'stretch': 1,
            },
            {
                'type': 'combo',
                'key': 'trc_1_on',          # режим Off/On/Hold
                'items': TRACE_MODES,       # 'Off' первым — дефолт
                'style': Style.COMBO_BOX,
                'stretch': 1,
            },
            {
                'type': 'button',
                'key': 'but_refresh_trc_1',
                "icon": "gui/icons/refresh.png",
                'stretch': 0,
                'style': Style.BUT_SQUARE,
            },
        ]
    },
    {
        'label': 'Трасса 2:',
        'widgets': [
            {
                'type': 'combo',
                'key': 'trc_2_acc',
                'items': ADD_TRACE,
                'value': ADD_TRACE[2],      # 'Средний'
                'style': Style.COMBO_BOX,
                'stretch': 1,
            },
            {
                'type': 'combo',
                'key': 'trc_2_on',
                'items': TRACE_MODES,
                'style': Style.COMBO_BOX,
                'stretch': 1,
            },
            {
                'type': 'button',
                'key': 'but_refresh_trc_2',
                "icon": "gui/icons/refresh.png",
                'stretch': 0,
                'style': Style.BUT_SQUARE,
            },
        ]
    },
]

# ВЫПАДАЮЩИЙ СПИСОК ЭЛЕМЕНТОВ ДЛЯ УПРАВЛЕНИЯ MARKERS
SECTION_MRK = [
    # Кнопки М1/М2 — checkable, взаимоисключающие (обработка в MarkersMixin)
    {
        'widgets': [
            {
                'type': 'button',
                'key': 'but_mrk_1',
                'text': 'Маркер 1',
                'checkable': True,
                'stretch': 1,
            },
            {
                'type': 'button',
                'key': 'but_mrk_2',
                'text': 'Маркер 2',
                'checkable': True,
                'stretch': 1,
            },
            {
                'type': 'combo',
                'key': 'combo_mrk_trace',
                'items': MARKER_TRACES,
                'value': MARKER_TRACES[0],
                'style': Style.COMBO_BOX,
                'stretch': 2,
            },
        ]
    },
    {
        'widgets': [
            {
                'type': 'button',
                'key': 'but_mrk_peak',
                'text': 'Peak',
                'stretch': 1,
            },
            {
                'type': 'button',
                'key': 'but_mrk_next_peak',
                'text': 'Next Peak',
                'stretch': 1,
            },
            {
                'type': 'checkbox',
                'key': 'chk_mrk_autopeak',
                'text': 'Auto Peak',
                'value': False,
                'stretch': 1,
            },
            {
                'type': 'checkbox',
                'key': 'chk_mrk_hold',
                'text': 'hold',
                'value': False,
                'stretch': 1,
            },
        ]
    },
    {
        'widgets': [
            {
                'type': 'button',
                'key': 'but_mrk_to_center',
                'text': 'В центр',
                'stretch': 1,
            },
            {
                'type': 'button',
                'key': 'but_mrk_delta_center',
                'text': 'Центр = ∆M',
                'stretch': 1,
            },
            {
                'type': 'button',
                'key': 'but_mrk_span_delta',
                'text': 'Span = ∆M',
                'stretch': 1,
            },
            {
                'type': 'button',
                'key': 'but_mrk_all_off',
                'text': 'All off',
                'stretch': 1,
            },
        ]
    },
]
