from collections import OrderedDict

MODES_MAP = OrderedDict({
    'away': {
        'id': 1, 'name': 'AWAY', 'icon': 'house-person-leave'
    },
    'normal': {
        'id': 2, 'name': 'NORMAL', 'icon': 'house-user'
    },
    'intensive': {
        'id': 3, 'name': 'INTENSIVE', 'icon': 'users'
    },
    'boost': {
        'id': 4, 'name': 'BOOST', 'icon': 'gauge-max'
    },
    'kitchen': {
        'id': 5, 'name': 'KITCHEN', 'icon': 'cauldron'
    },
    'fireplace': {
        'id': 6, 'name': 'FIREPLACE', 'icon': 'fireplace'
    },
    'override': {
        'id': 7, 'name': 'OVERRIDE', 'icon': 'hand-point-up'
    },
    'holidays': {
        'id': 8, 'name': 'HOLIDAYS', 'icon': 'suitcase'
    }
})