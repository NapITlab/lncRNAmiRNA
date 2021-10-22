import logging


class InfoFilter(logging.Filter):
    def filter(self, record):
        """
        :param record:
        :type record: logging.LogRecord
        :return:
        """
        return record.levelname == "INFO" or record.levelname == "WARNING"
