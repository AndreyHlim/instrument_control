from constants import SIGNAL_FORMS
from gui.styles import Style

# ВЫПАДАЮЩИЙ СПИСОК ЭЛЕМЕНТОВ ДЛЯ УПРАВЛЕНИЯ ГЕНЕРАТОРОМ НЧ
SECTION_SINGEN = [
    {
        "label": "Частота",
        'widgets': [
            {
                "type": "double",
                "key": "tb_freq_sin",
                "min": 100,
                "max": 20000,
                "value": 1000,
                "decimals": 0,
                "suffix": " Гц",
                "style": Style.SPIN_BOX,
                "stretch": 2,
            },
            {
                'type': 'label',
                'text': 'Напряжение',
                "stretch": 2,
            },
            {
                "type": "double",
                "key": "tb_lvl_sound",
                "label": "Напряжение",
                "min": 0,
                "max": 4,
                "value": 0.1,
                "suffix": " В",
                "style": Style.SPIN_BOX,
                "stretch": 2,
            },
        ]
    },
    {
        "label": "Форма сигнала",
        "widgets": [
            {
                "type": "combo",
                "key": "combo_form_sound",
                "items": SIGNAL_FORMS,
                "stretch": 4,
                "style": Style.H_18,
            },
            {
                "type": "checkbox",
                "key": "check_on_sound",
                "text": "Вкл",
                "value": False,
                "stretch": 2,
            }
        ]
    },
]
