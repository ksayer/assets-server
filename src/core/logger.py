import logging
import logging.config
import os


class InfoAndBelowFilter(logging.Filter):
    def filter(self, record):
        return record.levelno <= logging.INFO


def setup_logger(log_dir: str = 'logs', max_file_size: int = 10485760, backup_count: int = 5, level: str = 'INFO'):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    error_log_path = os.path.join(log_dir, 'errors.log')
    debug_log_path = os.path.join(log_dir, 'debug.log')

    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {'format': '%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(message)s'},
        },
        'filters': {
            'info_and_below': {
                '()': InfoAndBelowFilter,
            }
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
            },
            'error_file': {
                'level': 'WARNING',
                'formatter': 'standard',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': error_log_path,
                'maxBytes': max_file_size,
                'backupCount': backup_count,
            },
            'debug_file': {
                'level': 'DEBUG',
                'formatter': 'standard',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': debug_log_path,
                'maxBytes': max_file_size,
                'backupCount': backup_count,
                'filters': ['info_and_below'],
            },
        },
        'loggers': {
            'app_logger': {'handlers': ['console', 'error_file', 'debug_file'], 'level': level, 'propagate': False},
        },
        'root': {'level': 'INFO', 'handlers': ['console', 'error_file', 'debug_file']},
    }

    logging.config.dictConfig(config)
    return logging.getLogger('app_logger')
