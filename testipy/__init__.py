#!/usr/bin/env python3

import logging


__version__ = "0.9.5"
__app__ = "TestiPy"
__app_full__ = "Python Test Tool"
__author__ = "Pedro Nunes"
__author_email__ = "pjn2work@google.com"


def get_exec_logger():
    return logging.getLogger("testipy")
