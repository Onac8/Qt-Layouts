# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets, uic
import logging
import os, sys
import threading
import cv2


class DetectionZoneWindow(QtWidgets.QDialog):
    def __init__(self, proxy, camera_link, user, site, deco_config, proxy_deco=None):
        super().__init__()
        uic.loadUi('deadzone_window.ui', self) # Load the .ui file
        self.setWindowTitle('RailWatch Desktop App - Selector de fondo')

        self.proxy = proxy
        self.camera_link = camera_link
        self.proxy_deco = proxy_deco
        self.user = user
        self.site = site
        self.deco_config = deco_config
        self.puntos_or = []
        self.puntos = []
        self.x = None
        self.y = None
        self.img_original = None
        
        self.print_actual_zone()
        
        
        # Starting threading for imshow
        self.imshow_thread = threading.Thread(target=self.imshow_points, args=())
        self.imshow_thread.daemon = True
        self.imshow_thread.start()
        
        
        self.pushButton_save.clicked.connect(self.on_pushButton_save)
        self.pushButton_reset.clicked.connect(self.on_pushButton_reset)
        self.pushButton_point.clicked.connect(self.on_pushButton_point)
        # self.listWidget.currentRowChanged.connect(self.on_listWidgetText_changed)
    
    def print_actual_zone(self):
        cap = cv2.VideoCapture(self.camera_link)
        ret, img_original = cap.read()
        self.img_original = img_original
        self.puntos_or = self.deco_config['algoritmo']['puntos_zona_deteccion']
        self.dibujarPuntos(True)
        
        
    def on_pushButton_save(self):
        if self.puntos:
            point_list_int = [int(i) for i in self.puntos]
            try:
                if not self.proxy_deco: #normal mode
                    self.proxy.set_detection_zone(self.site, self.user, point_list_int)
                else: #direct mode
                    self.deco_proxy.set_detection_zone(point_list_int)
                self.pushButton_save.setEnabled(False)
            except Exception as ex:
                logging.warning('[Deco conf]: ' + str(ex))
            cv2.destroyAllWindows()
            logging.debug('[Deco conf]: Exit saving this points:')
            logging.debug(point_list_int)
        else:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setWindowTitle("Error de puntos")
            msg.setText('No hay puntos seleccionados. No guardamos.')
            msg.exec_()
            logging.debug('[Deco conf]: Exit saving 0 points...')
            self.puntos.clear()
            cv2.destroyAllWindows()
        
    
    def on_pushButton_reset(self):
        self.puntos.clear()
        self.listWidget.clear()
        cv2.imshow('puntos', self.img_original)

    
    def on_pushButton_point(self):
        if len(self.puntos) > 0:
            row = len(self.puntos)-1
            self.puntos = self.puntos[:-2]
            self.dibujarPuntos()
            self.listWidget.takeItem(self.listWidget.count()-1)
    
    
    # def on_listWidgetText_changed(self):
    #     if self.listWidget.count() != 0:
    #         self.pushButton_save.setEnabled(True)
    #         self.pushButton_point.setEnabled(True)
    #     else:
    #         self.pushButton_save.setEnabled(False)
    #         self.pushButton_point.setEnabled(False)
    
    def imshow_points(self):
        cv2.namedWindow('puntos')
        cv2.setMouseCallback('puntos', self.callback)
        cv2.imshow('puntos', self.img_original)
        cv2.waitKey()
        
        # MostrarPuntos()
        # self.finalice_thread()
    
    
    def callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.puntos.append(x)
            self.puntos.append(y)
            self.listWidget.addItem("({}, {}); ".format(x,y))
            self.dibujarPuntos()
    
    
    def dibujarPuntos(self, is_first=False):
        L = len(self.puntos)
        L_or = len(self.puntos_or)
        img = self.img_original.copy()
        if is_first:
            if L_or > 0:
                for i in range(0,L_or+2, 2):
                    cv2.line(img, (self.puntos_or[i%L_or], self.puntos_or[(i+1)%L_or]), (self.puntos_or[(i+2)%L_or], self.puntos_or[(i+3)%L_or]), (255, 0, 0))
                    self.img_original = img
        else:
            if L > 0:
                for i in range(0, L+2, 2):
                    cv2.line(img, (self.puntos[i%L], self.puntos[(i+1)%L]), (self.puntos[(i+2)%L], self.puntos[(i+3)%L]), (0, 255, 0))
        cv2.imshow('puntos', img)
        
        
    def closeEvent(self, event):
        logging.debug(self.listWidget.count())
        cv2.destroyAllWindows()
        logging.debug('[Deco conf]: Exit without saving...')