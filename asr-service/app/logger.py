import logging
import json
import os
from logging.handlers import RotatingFileHandler


class MyLogger:
    def __init__(self, log_dir: str, info_file: str, error_file: str, level: str):
        self.logger = logging.getLogger("asr_service")
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        self.log_dir = log_dir
        self.info_file = info_file
        self.error_file = error_file
        self._configure_handlers()

    def _configure_handlers(self):
        if not self.logger.handlers:
            info_hdl = logging.StreamHandler()
            info_hdl.setLevel(logging.INFO)
            info_hdl.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
            self.logger.addHandler(info_hdl)

            err_hdl = logging.StreamHandler()
            err_hdl.setLevel(logging.ERROR)
            err_hdl.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
            self.logger.addHandler(err_hdl)

            os.makedirs(self.log_dir, exist_ok=True)
            
            info_file = RotatingFileHandler(os.path.join(self.log_dir, self.info_file))
            info_file.setLevel(logging.INFO)
            info_file.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
            self.logger.addHandler(info_file)

            error_file = RotatingFileHandler(os.path.join(self.log_dir, self.error_file))
            error_file.setLevel(logging.ERROR)
            error_file.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
            self.logger.addHandler(error_file)

    def info(self, **kwargs):
        self.logger.info(json.dumps(kwargs, ensure_ascii=False))

    def error(self, **kwargs):
        self.logger.error(json.dumps(kwargs, ensure_ascii=False))