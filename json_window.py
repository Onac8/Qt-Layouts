# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets, uic
import logging, math
import json


class JsonWindow(QtWidgets.QDialog):
    def __init__(self, proxy, site, config_app, site_id, user, deco_proxy=None):
        super().__init__()
        uic.loadUi('json_window.ui', self) # Load the .ui file
        self.setWindowTitle('RailWatch Desktop App - Archivo de configuración')

        self.proxy = proxy
        self.user = user
        self.site = site
        self.config_app = config_app
        self.deco_proxy = deco_proxy
        self.site_id = site_id
        
        if self.site == 'all':
            config = self.proxy.get_cs_config()
        elif self.site == 'app':
            config = self.config_app
        elif self.site_id == 'recorder':
            if not self.deco_proxy:
                config = self.proxy.get_recorder_config(self.site, self.user)
            else:
                config = self.proxy.get_config()
        elif self.site_id == 'deco':
            if not self.deco_proxy:
                config = self.proxy.get_deco_config(self.site, self.user)
            else:
                video_config = self.deco_proxy.get_config('video')
                algoritmo_config = self.deco_proxy.get_config('algoritmo')
                config = {}
                config['video'] = video_config
                config['algoritmo'] = algoritmo_config
        else: # site_id = 'site' in this case -- all CS site conf
            config = self.proxy.get_cs_config()['places'][self.site]
        config_str = json.dumps(config, indent=4)
        self.textEdit.setText(config_str)