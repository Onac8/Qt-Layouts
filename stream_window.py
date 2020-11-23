# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets, uic
import sys, os
import logging
import math
ACTUAL_PATH = os.path.dirname(__file__)
sys.path.append(os.path.join(ACTUAL_PATH, '../modules'))
sys.path.append(os.path.join(ACTUAL_PATH, '../railwatch_modules'))
from streaming.streamer import CameraWidget


MAX_COLUMNS = 3

class StreamWindow(QtWidgets.QDialog):
    def __init__(self, links):
        super().__init__()
        uic.loadUi('stream_window.ui', self) # Load the .ui file
        self.setWindowTitle('RailWatch Desktop App - Streaming')
                
        logging.debug('Creating Streaming layout...')
        
        # Dynamically determine screen width/height
        self.screen_width = QtWidgets.QApplication.desktop().screenGeometry().width()
        self.screen_height = QtWidgets.QApplication.desktop().screenGeometry().height()
        
        # List of total cameras (threading)
        self.cameras = []
                
        logging.debug('Creating camera widgets...')
        rows = math.ceil((len(links)/MAX_COLUMNS)) # round up the number
        if rows==1: rows = 2 # in case 1-3 cameras
        for link in links:
            camera = CameraWidget(self.screen_width//MAX_COLUMNS, self.screen_height//rows, link) # Dinamic width/height.
            self.cameras.append(camera)
        
        logging.debug('Adding widgets to layout...')
        for i in range(len(self.cameras)): #All cameras loop
            self.gridLayout.addWidget(self.cameras[i].get_video_frame(),self.get_row(i),self.get_column(i),1,1) # Disposition (widget, width, height, rowspan, columnspan)
            logging.debug('Widget added...')
            
        logging.debug('Display loaded. Streaming...')
        # self.setLayout(self.gridLayout)


    def get_row(self, index):  
        if index <= 2:
            return 0
        if index > 2 and index <= 5:
            return 1
        if index > 5 and index <= 8:
            return 2
        if index > 8 and index <= 11:
            return 3
        
    def get_column(self,index):
        if index == 3 or index == 6 or index == 9 or index == 12:
            return 0
        else:
            return index
        
    def closeEvent(self, event):
        for camera in self.cameras:
            camera.stop_stream()
            camera_thread = camera.get_thread()
            camera_thread.join()
        

def main():
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = QtWidgets.QMainWindow()
    ui = StreamWindow()
    ui.setupUi(mainWindow)
    mainWindow.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()