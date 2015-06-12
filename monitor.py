# -*- coding: utf-8 -*-

import credentials
from libra import LibraController

if __name__ == '__main__':
    credentials.CFG.register_group(credentials.TGROUP)
    credentials.CFG(default_config_files=['libra.conf'])

    libra = LibraController()
    libra.prepare()
