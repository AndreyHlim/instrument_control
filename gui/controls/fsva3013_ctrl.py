from constants import (AMP_UNITS, ANT_NAMES, DETECTORS_FSVA, FREQ_DIM,
                       PREAMP_VAL, RBW_TYPES_FILTER, TRACE_ACC)
from gui.styles import Style

# ВЫПАДАЮЩИЙ СПИСОК ЭЛЕМЕНТОВ ДЛЯ УПРАВЛЕНИЯ АМПЛИТУДОЙ
SECTION_AMP = [
    # Ref lvl
    {
        "label": "Ref lvl",
        "widgets": [
            {
                'type': 'button',
                "key": "but_reflvl_up",
                "text": "▲",
                "stretch": 1,
                "style": Style.BUT_SQUARE,
            },
            {
                'type': 'button',
                "key": "but_reflvl_down",
                "text": "▼",
                "stretch": 1,
                "style": Style.BUT_SQUARE,
            },
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
            },
        ]
    },
    # Range
    {
        "label": "Range, dB",
        "widgets": [
            {
                'type': 'button',
                "key": "but_ref_range_up",
                "text": "▲",
                "stretch": 1,
                "style": Style.BUT_SQUARE,
            },
            {
                'type': 'button',
                "key": "but_ref_range_down",
                "text": "▼",
                "stretch": 1,
                "style": Style.BUT_SQUARE,
            },
            {
                "type": "value_edit",
                "key": "label_range",
                "stretch": 8,
                "style": Style.LBL_BORDER,
            },
        ]
    },
    # Atten
    {
        "label": "Atten, dB",
        "widgets": [
            {
                'type': 'button',
                "key": "but_atten_up",
                "text": "▲",
                "stretch": 1,
                "style": Style.BUT_SQUARE,
            },
            {
                'type': 'button',
                "key": "but_atten_down",
                "text": "▼",
                "stretch": 1,
                "style": Style.BUT_SQUARE,
            },
            {
                "type": "value_edit",
                "key": "label_atten",
                "stretch": 1,
                "style": Style.LBL_BORDER,
            },
            {
                "type": "label",
                "text": "PreAmp",
                "stretch": 1,
                "key": "label_preamp",
                "align": "right",
            },
            {
                "label": "Preamp",
                "type": "combo",
                "key": "combo_preamp",
                "items": PREAMP_VAL,
                "stretch": 2,
            },
        ]
    },
    {
        'type': 'combo',
        'label': 'Калибровка',
        'key': 'combo_transducer',
        'items': ANT_NAMES.values(),
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
        "label": "Тип фильтра",
        "key": "rbw_type_filter",
        "items": RBW_TYPES_FILTER,
    },
    {
        "label": "RBW",
        "widgets": [
            {
                'type': 'button',
                "key": "but_rbw_up",
                "text": "▲",
                "stretch": 1,
                "style": Style.BUT_SQUARE,
            },
            {
                'type': 'button',
                "key": "but_rbw_down",
                "text": "▼",
                "stretch": 1,
                "style": Style.BUT_SQUARE,
            },
            {
                "type": "label",
                "key": "label_rbw",
                "stretch": 8,
                "style": Style.LBL_BORDER,
            },
            {
                "type": "combo",
                "key": "rbw_unit",
                "items": FREQ_DIM.keys(),
                "stretch": 1,
            },
            {
                "type": "checkbox",
                "key": "rbw_auto",
                "text": "Auto",
                "value": False,
                "stretch": 1,
            }
        ]
    },
    {
        "label": "VBW",
        "widgets": [
            {
                'type': 'button',
                "key": "but_vbw_up",
                "text": "▲",
                "stretch": 1,
                "style": Style.BUT_SQUARE,
            },
            {
                'type': 'button',
                "key": "but_vbw_down",
                "text": "▼",
                "stretch": 1,
                "style": Style.BUT_SQUARE,
            },
            {
                "type": "label",
                "key": "label_vbw",
                "stretch": 8,
                "style": Style.LBL_BORDER,
            },
            {
                "type": "combo",
                "key": "vbw_unit",
                "items": FREQ_DIM.keys(),
                "stretch": 1,
            },
            {
                "type": "checkbox",
                "key": "vbw_auto",
                "text": "Auto",
                "value": False,
                "stretch": 1,
            }
        ]
    },
]

# ВЫПАДАЮЩИЙ СПИСОК ЭЛЕМЕНТОВ ДЛЯ УПРАВЛЕНИЯ SWEEP
SECTION_SWEEP = [
    {
        "label": "Детектор",
        "type": "combo",
        "key": "combo_det",
        "items": DETECTORS_FSVA.keys(),
    },
    {
        "label": "Накопление",
        "type": "combo",
        "key": "combo_trace_acc",
        "items": TRACE_ACC.keys(),
    },
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

]

# ВЫПАДАЮЩИЙ СПИСОК ЭЛЕМЕНТОВ ДЛЯ УПРАВЛЕНИЯ MARKERS
SECTION_MRK = [
    {
        'label': 'Marker 1',
        'widgets': [
            {
                'type': 'checkbox',
                'key': 'check_auto_max',
                'text': 'Автослежение',
                'value': False,
                "stretch": 1,
            },
            {
                'type': 'button',
                "key": "but_mrk_to_cf",
                "text": "В центр",
                "stretch": 1,
                # "style": Style.VAL_CFSTEP_TO_SPAN,
            },
        ]
    },
]
