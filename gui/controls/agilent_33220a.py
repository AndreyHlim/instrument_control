# ВЫПАДАЮЩИЙ СПИСОК ЭЛЕМЕНТОВ ДЛЯ УПРАВЛЕНИЯ ГЕНЕРАТОРОМ НЧ
SECTION_SINGEN = [
    {
        "type": "double",
        "key": "tb_freq_sin",
        "label": "Частота",
        "min": 100,
        "max": 20000,
        "value": 1000,
        "suffix": " Гц",
        "style": ("QDoubleSpinBox { qproperty-alignment: "
                  "'AlignHCenter|AlignVCenter'; }")
    },
    {
        "type": "double",
        "key": "tb_lvl_sound",
        "label": "Напряжение",
        "min": 0,
        "max": 4,
        "value": 0.1,
        "suffix": " В",
        "style": ("QDoubleSpinBox { qproperty-alignment: "
                  "'AlignHCenter|AlignVCenter'; }")
    },
    {
        "label": "Форма сигнала",
        "widgets": [
            {
                "type": "combo",
                "key": "combo_form_sound",
                "items": ['SINusoid', 'SQUare',
                          'RAMP', 'NRAMp',
                          'TRIangle', 'NOISe'],
                "stretch": 4,
            },
            {
                "type": "checkbox",
                "key": "check_on_sound",
                "text": "Вкл",
                "value": False,
                "stretch": 1,
            }
        ]
    },
]
