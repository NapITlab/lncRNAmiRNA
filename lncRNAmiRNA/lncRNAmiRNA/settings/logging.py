
LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format':
                '%(levelname)s %(asctime)s\n'
                '%(module)s %(pathname)s %(funcName)s %(process)d %(thread)d\n'
                '%(message)s',
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
        'simple': {
            'format':
                '%(asctime)s %(levelname)s\n'
                '%(pathname)s %(funcName)s:\n'
                '%(message)s',
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
        'simple_coloured': {
            'format':
                '%(asctime)s %(levelname)s\n'
                '%(pathname)s %(funcName)s:\n'
                '%(message)s',
            'datefmt': "%Y-%m-%d %H:%M:%S",
            '()': 'djangocolors_formatter.DjangoColorsFormatter',  # colored output
        },
    },
    'filters': {
        'info': {
            '()': 'lncRNAmiRNA.logging_filters.InfoFilter'
        },
    },
    'handlers': {
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'simple_coloured'
        },
        'telegram_error': {
            'level': 'ERROR',
            'class': 'telegram_handler.TelegramHandler',
            'token': '1761856112:AAEseRh0F4KlBrKD3Bn_IE3ibPSQLt1kNh8',
            'chat_id': '65722146',
            'formatter': 'simple'
        },
        'telegram_info': {
            'level': 'INFO',
            'class': 'telegram_handler.TelegramHandler',
            'token': '1752229277:AAFGv0IsRYDx8wtJ_Tql07cSUs12S1AjjsU',
            'chat_id': '65722146',
            'formatter': 'simple',
            'filters': ['info', ]
        }
    },
    'root': {
        'handlers': ['console', ],
        'level': 'INFO',
    },
    'loggers': {
        'lncRNAmiRNA_model': {
            'handlers': ['console', ],
            'level': 'DEBUG',
            'propagate': False,
        },
        'lncRNAmiRNA_model.telegram': {
            'handlers': ['telegram_info', 'telegram_error'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}
