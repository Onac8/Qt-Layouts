# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets, uic
import logging
import os, sys
import cv2
ACTUAL_PATH = os.path.dirname(__file__)
sys.path.append(os.path.join(ACTUAL_PATH, '../modules'))
sys.path.append(os.path.join(ACTUAL_PATH, '../railwatch_modules'))
from streaming.streamer import CameraWidget


class BackgroundWindow(QtWidgets.QDialog):
    def __init__(self, proxy, camera_link, configObj, user, site, proxy_deco=None):
        super().__init__()
        uic.loadUi('background_window.ui', self) # Load the .ui file
        self.setWindowTitle('RailWatch Desktop App - Selector de fondo')

        self.proxy = proxy
        self.proxy_deco = proxy_deco
        self.user = user
        self.site = site
        self.configObj = configObj
        self.config = self.configObj.read_config()
        self.frame = None
        
        logging.debug('Creating camera widgets...')
        self.camera = CameraWidget(500, 400, camera_link)
        # self.gridLayout.addWidget(self.camera.get_video_frame(), 0, 0)
        self.verticalLayout.insertWidget(0, self.camera.get_video_frame())
        logging.debug('Display loaded. Streaming...')
        
        self.pushButton.clicked.connect(self.on_pushButton_getFrame)
        
        
    def on_pushButton_getFrame(self):
        self.frame = self.camera.get_actual_frame()
        retval, frame_jpeg = cv2.imencode('.jpeg', self.frame)
        frame_jpeg = self.frame.tobytes()
        try:
            if not self.proxy_deco:
                self.proxy.set_first_frame(self.site, self.user, frame_jpeg) #setting config_file_deco
            else:
                self.proxy_deco.set_first_frame(frame_jpeg)
            self.label.setText("¡Nuevo fondo añadido!")
        except Exception as ex:
            logging.warning('[Deco conf]: Cannot set first frame --> ' + str(ex))
            self.label.setText("¡NO nuevo fondo! (Fallo en comunicación con deco)")
        self.pushButton.setEnabled(False)
        
    def closeEvent(self, event):
        self.camera.stop_stream()
        camera_thread = self.camera.get_thread()
        camera_thread.join()
        logging.debug('[Deco conf]: Thermal Camera thread joined...')