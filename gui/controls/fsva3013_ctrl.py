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
            },
            {
                'type': 'button',
                "key": "but_reflvl_down",
                "text": "▼",
                "stretch": 1,
            },
            {
                "type": "label",
                "key": "label_reflevel",
                "stretch": 8,
                "style": (
                    "qproperty-alignment: 'AlignHCenter|AlignVCenter'; "
                    "border: 1px solid #ababab; "  # Тонкая серая рамка
                    # "border-radius: 2px; "          # Небольшое скругления
                    # "padding: 2px 5px; "            # Отступы внутри рамки
                    "background-color: #ffffff;"    # Белый фон под текстом
                ),
            },
            {
                "type": "combo",
                "key": "amp_unit",
                "items": ['dBm', 'dBµV', 'dBmV', 'V',
                          'W', 'dBV', 'dBµV/Hz', 'dBmV/Hz'],

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
            },
            {
                'type': 'button',
                "key": "but_ref_range_down",
                "text": "▼",
                "stretch": 1,
            },
            {
                "type": "label",
                "key": "label_range",
                "stretch": 8,
                "style": (
                    "qproperty-alignment: 'AlignHCenter|AlignVCenter'; "
                    "border: 1px solid #ababab; "  # Тонкая серая рамка
                    # "border-radius: 2px; "          # Небольшое скругления
                    # "padding: 2px 5px; "            # Отступы внутри рамки
                    "background-color: #ffffff;"    # Белый фон под текстом
                ),
            },
        ]
    },
    # Preamp
    {
        "label": "Preamp",
        "type": "combo",
        "key": "combo_preamp",
        "items": ['Off', '15 dB', '30 dB']
    },
    # Atten
    {
        "label": "Atten, dB",
        "widgets": [
            {
                'type': 'button',
                "key": "but_atten_down",
                "icon": "gui/icons/left.png",
                "stretch": 1
            },
            {
                "type": "label",
                "key": "label_atten",
                "stretch": 8,
                "style": (
                    "qproperty-alignment: 'AlignHCenter|AlignVCenter'; "
                    "border: 1px solid #ababab; "  # Тонкая серая рамка
                    # "border-radius: 2px; "          # Небольшое скругления
                    # "padding: 2px 5px; "            # Отступы внутри рамки
                    "background-color: #ffffff;"    # Белый фон под текстом
                )
            },
            {
                'type': 'button',
                "key": "but_atten_up",
                "icon": "gui/icons/right.png",
                "stretch": 1
            }
        ]
    },
]

# ВЫПАДАЮЩИЙ СПИСОК ЭЛЕМЕНТОВ ДЛЯ УПРАВЛЕНИЯ ЧАСТОТОЙ
SECTION_FREQ = [
    # Center
    {
        "label": "Center",
        "widgets": [
            {
                'type': 'button',
                "key": "but_cf_up",
                "text": "▲",
                "stretch": 1
            },
            {
                'type': 'button',
                "key": "but_cf_down",
                "text": "▼",
                "stretch": 1
            },
            {
                "type": "label",
                "key": "label_center",
                "stretch": 8,
                "style": (
                    "qproperty-alignment: 'AlignHCenter|AlignVCenter'; "
                    "border: 1px solid #ababab; "  # Тонкая серая рамка
                    # "border-radius: 2px; "          # Небольшое скругления
                    # "padding: 2px 5px; "            # Отступы внутри рамки
                    "background-color: #ffffff;"    # Белый фон под текстом
                )
            },
        ]
    },
    # Span
    {
        "label": "Span",
        "widgets": [
            {
                'type': 'button',
                "key": "but_span_up",
                "text": "▲",
                "stretch": 1
            },
            {
                'type': 'button',
                "key": "but_span_down",
                "text": "▼",
                "stretch": 1
            },
            {
                "type": "label",
                "key": "label_span",
                "stretch": 8,
                "style": (
                    "qproperty-alignment: 'AlignHCenter|AlignVCenter'; "
                    "border: 1px solid #ababab; "  # Тонкая серая рамка
                    # "border-radius: 2px; "          # Небольшое скругления
                    # "padding: 2px 5px; "            # Отступы внутри рамки
                    "background-color: #ffffff;"    # Белый фон под текстом
                )
            },
            {
                'type': 'button',
                "key": "but_span_set_stepcf",
                "text": "=StepCF",
                "stretch": 1
            },
        ]

    },
    # Step CF
    {
        "label": "CF Step",
        "widgets": [
            {
                "type": "double",
                "key": "tb_cfstep",
                "min": 0.001,
                "max": 5000,
                "value": 0.001,
                "stretch": 8,
            },
            {
                'type': 'button',
                "key": "but_stepcf_set_span",
                "text": "=Span",
                "stretch": 1
            },
        ]
    },
]

# ВЫПАДАЮЩИЙ СПИСОК ЭЛЕМЕНТОВ ДЛЯ УПРАВЛЕНИЯ RBW/VBW
SECTION_RBW = [
    {
        "label": "RBW",
        "widgets": [
            {
                'type': 'button',
                "key": "but_rbw_up",
                "text": "▲",
                "stretch": 1,
            },
            {
                'type': 'button',
                "key": "but_rbw_down",
                "text": "▼",
                "stretch": 1,
            },
            {
                "type": "label",
                "key": "label_rbw",
                "stretch": 8,
                "style": (
                    "qproperty-alignment: 'AlignHCenter|AlignVCenter'; "
                    "border: 1px solid #ababab; "  # Тонкая серая рамка
                    "background-color: #ffffff;"    # Белый фон под текстом
                ),
            },
            {
                "type": "combo",
                "key": "rbw_unit",
                "items": ['Гц', 'кГц', 'МГц', 'ГГц'],
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
            },
            {
                'type': 'button',
                "key": "but_vbw_down",
                "text": "▼",
                "stretch": 1,
            },
            {
                "type": "label",
                "key": "label_vbw",
                "stretch": 8,
                "style": (
                    "qproperty-alignment: 'AlignHCenter|AlignVCenter'; "
                    "border: 1px solid #ababab; "  # Тонкая серая рамка
                    "background-color: #ffffff;"    # Белый фон под текстом
                ),
            },
            {
                "type": "combo",
                "key": "vbw_unit",
                "items": ['Гц', 'кГц', 'МГц', 'ГГц'],
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
