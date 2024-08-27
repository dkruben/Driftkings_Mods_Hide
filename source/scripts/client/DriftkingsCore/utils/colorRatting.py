# -*- coding: utf-8 -*-
__all__ = ('color_tables',)


class ColorRating:
    def __init__(self, scale_name, colors):
        self.scale_name = scale_name
        self.colors = colors

    def table(self):
        return {
            'ScaleColor': self.scale_name,
            'colors': self.colors
        }


noob_meter_colors = {
    'wn8': [
        {'value': 300, 'color': '#BB0000'},
        {'value': 600, 'color': '#FF0000'},
        {'value': 900, 'color': '#FF6600'},
        {'value': 1200, 'color': '#F8F400'},
        {'value': 1500, 'color': '#99CC00'},
        {'value': 1750, 'color': '#00CC00'},
        {'value': 2300, 'color': '#66BBFF'},
        {'value': 2900, 'color': '#CC66CC'},
        {'value': 999999, 'color': '#FF00FF'}
    ],
    'eff': [
        {'value': 615, 'color': '#BB0000'},
        {'value': 870, 'color': '#FF0000'},
        {'value': 1175, 'color': '#F8F400'},
        {'value': 1525, 'color': '#99CC00'},
        {'value': 1850, 'color': '#00CC00'},
        {'value': 9999, 'color': '#CC66CC'}
    ],
    'x': [
        {'value': 16.4, 'color': '#FE0E00'},
        {'value': 33.4, 'color': '#FE7903'},
        {'value': 52.4, 'color': '#60FF00'},
        {'value': 75.4, 'color': '#60FF00'},
        {'value': 92.4, 'color': '#02C9B3'},
        {'value': 999, 'color': '#D042F3'}
    ],
    'tdb': [
        {'value': 499, 'color': '#FE0E00'},
        {'value': 749, 'color': '#FE7903'},
        {'value': 999, 'color': '#60FF00'},
        {'value': 1799, 'color': '#60FF00'},
        {'value': 2499, 'color': '#02C9B3'},
        {'value': 9999, 'color': '#D042F3'}
    ],
    'diff': [
        {'value': -1, 'color': '#FE0E00'},
        {'value': 0, 'color': '#F3FF3F'},
        {'value': 99999, 'color': '#60FF00'}
    ]
}

xvm_colors = {
    'wn8': [
        {'value': 397, 'color': '#FE0E00'},
        {'value': 914, 'color': '#FE7903'},
        {'value': 1489, 'color': '#60FF00'},
        {'value': 2231, 'color': '#60FF00'},
        {'value': 2979, 'color': '#02C9B3'},
        {'value': 999999, 'color': '#D042F3'}
    ],
    'eff': [
        {'value': 598, 'color': '#FE0E00'},
        {'value': 874, 'color': '#FE7903'},
        {'value': 1079, 'color': '#F8F400'},
        {'value': 1540, 'color': '#60FF00'},
        {'value': 1868, 'color': '#02C9B3'},
        {'value': 9999, 'color': '#D042F3'}
    ],
    'x': [
        {'value': 16.4, 'color': '#FE0E00'},
        {'value': 33.4, 'color': '#FE7903'},
        {'value': 52.4, 'color': '#60FF00'},
        {'value': 75.4, 'color': '#60FF00'},
        {'value': 92.4, 'color': '#02C9B3'},
        {'value': 999, 'color': '#D042F3'}
    ],
    'tdb': [
        {'value': 499, 'color': '#FE0E00'},
        {'value': 749, 'color': '#FE7903'},
        {'value': 999, 'color': '#60FF00'},
        {'value': 1799, 'color': '#60FF00'},
        {'value': 2499, 'color': '#02C9B3'},
        {'value': 9999, 'color': '#D042F3'}
    ],
    'diff': [
        {'value': -1, 'color': '#FE0E00'},
        {'value': 0, 'color': '#F3FF3F'},
        {'value': 99999, 'color': '#60FF00'}
    ]
}

wot_labs_colors = {
    'wn8': [
        {'value': 450, 'color': '#FE0E00'},
        {'value': 984, 'color': '#FE7903'},
        {'value': 1577, 'color': '#F8F400'},
        {'value': 2368, 'color': '#60FF00'},
        {'value': 3182, 'color': '#02C9B3'},
        {'value': 999999, 'color': '#D042F3'}
    ],
    'eff': [
        {'value': 604, 'color': '#FE0E00'},
        {'value': 884, 'color': '#FE7903'},
        {'value': 1187, 'color': '#F8F400'},
        {'value': 1547, 'color': '#60FF00'},
        {'value': 1872, 'color': '#02C9B3'},
        {'value': 999999, 'color': '#D042F3'}
    ],
    'x': [
        {'value': 16.5, 'color': '#FE0E00'},
        {'value': 33.5, 'color': '#FE7903'},
        {'value': 52.5, 'color': '#F8F400'},
        {'value': 75.5, 'color': '#60FF00'},
        {'value': 92.5, 'color': '#02C9B3'},
        {'value': 999, 'color': '#D042F3'}
    ],
    'tdb': [
        {'value': 499, 'color': '#FE0E00'},
        {'value': 749, 'color': '#FE7903'},
        {'value': 999, 'color': '#F8F400'},
        {'value': 1799, 'color': '#60FF00'},
        {'value': 2499, 'color': '#02C9B3'},
        {'value': 9999, 'color': '#D042F3'}
    ],
    'diff': [
        {'value': -1, 'color': '#FE0E00'},
        {'value': 0, 'color': '#F3FF3F'},
        {'value': 99999, 'color': '#60FF00'}
    ]
}


color_tables = [
    ColorRating('NoobMeter', noob_meter_colors).table(),
    ColorRating('XVM', xvm_colors).table(),
    ColorRating('WotLabs', wot_labs_colors).table()
]
