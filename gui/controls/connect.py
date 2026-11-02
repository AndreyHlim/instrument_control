from gui.styles import Style

# ВЫПАДАЮЩИЙ СПИСОК ЭЛЕМЕНТОВ ДЛЯ ПОДКЛЮЧЕНИЯ К ПРИБОРАМ
SECTION_INSTR = [
    # Анализатор FSVA3013
    {
        'label': 'IP анализатора',
        'widgets': [
            {
                "type": "text_box",
                "key": "tb_ip_analyzer",
                "text": '10.255.0.100',
                "stretch": 1,
                "style": Style.TEXT_BOX,
            },
            {
                'type': 'button',
                "key": "but_analyzer_conn",
                "text": 'Подключиться',
                "stretch": 1,
                "style": Style.H_20,
            },
            {
                'type': 'button',
                "key": "but_analyzer_web",
                "icon": "gui/icons/browser.png",
                "stretch": 1,
                "style": Style.BUT_SQUARE,
            },
        ]
    },
    # НЧ Генератор Agilent 33220a
    {
        'label': 'IP НЧ генератора',
        'widgets': [
            {
                "type": "text_box",
                "key": "tb_ip_singen",
                "text": '10.255.0.236',
                "stretch": 1,
                "style": Style.TEXT_BOX,
            },
            {
                'type': 'button',
                "key": "but_singen_conn",
                "text": 'Подключиться',
                "stretch": 1,
                "style": Style.H_20,
            },
            {
                'type': 'button',
                "key": "but_singen_web",
                "icon": "gui/icons/browser.png",
                "stretch": 1,
                "style": Style.BUT_SQUARE,
            },
        ]
    },
]
