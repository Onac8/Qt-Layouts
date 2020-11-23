# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets, uic
import sys, os
from record_window import RecordWindow
from stream_window import StreamWindow
from option_window import OptionWindow
import logging
import app_api
ACTUAL_PATH = os.path.dirname(__file__)
sys.path.append(os.path.join(ACTUAL_PATH, '../modules'))
sys.path.append(os.path.join(ACTUAL_PATH, '../railwatch_modules'))
from ssh_tunneling import ssh_tunneling


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, log_window, user, configObj, proxy, tunnels, deco_proxy=None, site_offline=None, ssh_ports=None, site_ip_dns=None):
        super().__init__()
        uic.loadUi('main_window.ui', self) # Load the .ui file
        self.setWindowTitle('RailWatch Desktop App')
        
        self.log_window = log_window
        self.user = user
        self.configObj = configObj
        self.config = self.configObj.read_config()
        self.proxy = proxy #server/disp proxy
        self.tunnels = tunnels
        self.user_privileges = app_api.get_user_privileges(self.configObj, self.user)
        self.site_offline = site_offline
        self.deco_proxy = deco_proxy
        self.ssh_ports = ssh_ports
        self.site_ip_dns = site_ip_dns
        
        self.sites = None
        self.my_ip = app_api.get_my_ip()
        
        self.loadDefaultValues()
        
        logging.debug('Layout created.')
        
        #Buttons & dropwdown signals-------------------------------------------
        self.comboBox.currentIndexChanged.connect(self.on_comboBox_clicked) # Selected site
        self.pushButton_streaming.clicked.connect(self.on_pushButtonStreaming_clicked)# Streaming window 
        self.pushButton_recordings.clicked.connect(self.on_pushButtonRecords_clicked)# Records window
        self.pushButton_conf.clicked.connect(self.on_pushButtonConf_clicked)
        self.pushButton_disconnect.clicked.connect(self.on_pushButtonDisconnect_clicked)
            
    
    def loadDefaultValues(self):
        app_api.check_conn(self.tunnels, self.proxy, self.config['users_keys_path'][self.user])
        if not self.site_offline:
            self.sites = self.proxy.get_places()
            self.proxy.report_conection(self.user, self.my_ip)
            logging.debug('App [online mode]: Getting site names...')
            self.comboBox.clear()
            self.comboBox.addItem('Seleccione un puesto')
            self.comboBox.addItems(self.sites)
        else:
            self.comboBox.clear()
            self.comboBox.addItem('Seleccione un puesto')
            self.comboBox.addItem(self.site_offline)
            self.sites = self.site_offline
        
        self.pushButton_conf.setIcon(QtGui.QIcon(self.get_icon_path('configure')))
        self.pushButton_conf.setIconSize(QtCore.QSize(24,24))
        if self.user_privileges.get('disp_conf') == False: #only railwatch and ena have this privilege
            self.pushButton_conf.setEnabled(False)
            
    
    def on_pushButtonStreaming_clicked(self): # showing streaming window
        app_api.check_conn(self.tunnels, self.proxy, self.config['users_keys_path'][self.user])
        if self.site_offline:
            logging.debug('Getting camera links (offline)...')
            links = self.proxy.get_urls_rtsp()
            self.proxy.report_conection(self.user, self.my_ip)
            self.do_stream(links)
        else:
            if not self.sites: #Connection lost case
                logging.warning("Connection lost. Trying to reconnect...")
                self.show_error_dialog()
            else:
                logging.debug('Getting camera links...')
                site = self.comboBox.currentText()
                logging.debug('USER: ' + self.user + '..... SITE: ' + site)
                links = self.proxy.get_urls_rtsp(site, self.user)
                self.proxy.report_conection(self.user, self.my_ip)
                self.do_stream(links)


    def on_pushButtonRecords_clicked(self): # showing streaming window
        if self.site_offline:
            logging.debug('Getting site IP (offline)...')
            self.do_records(self.site_offline)
        else:
            if not self.sites: # Connection lost case
                logging.warning("Connection lost. Trying to reconnect...")
                self.show_error_dialog()
            else:
                logging.debug('Getting site ID...')
                site_id = self.comboBox.currentText()
                self.do_records(site_id)
                

    def on_pushButtonConf_clicked(self):
        self.do_options()
        
        
    def on_pushButtonDisconnect_clicked(self):
        self.clean_connections()
        self.log_window.show()
        self.deleteLater()
        

    def on_comboBox_clicked(self):
        if self.comboBox.currentText() in self.sites: # sitio concreto seleccionado 
            self.pushButton_streaming.setEnabled(True)
            self.pushButton_recordings.setEnabled(True)
        else:
            self.pushButton_streaming.setEnabled(False)
            self.pushButton_recordings.setEnabled(False)
      
        
    def do_stream(self, links):
        stream_window = StreamWindow(links)
        logging.debug('Creating Record Window --> ' + str(stream_window))
        stream_window.activateWindow()
        stream_window.exec_()
        
        
    def do_records(self, site_id):
        record_window = RecordWindow(site_id, self.site_ip_dns, self.proxy, self.tunnels, self.configObj, self.site_offline, self.user, self.user_privileges, self.ssh_ports)
        logging.debug('Creating Record Window --> ' + str(record_window))
        record_window.exec_()

    
    def do_options(self):
        if not self.site_offline:
            option_window = OptionWindow(self, self.proxy, self.tunnels, self.configObj, self.user)
        else:
            option_window = OptionWindow(self, self.proxy, self.tunnels, self.configObj, self.user, self.deco_proxy, self.site_offline, self.ssh_ports)
        logging.debug('Creating Option Window --> ' + str(option_window))
        option_window.exec_()
        logging.debug('OptionWindow closed. Loading new/default values...')
        self.loadDefaultValues()
        
        
    def show_error_dialog(self):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setText('No se puede conectar con el servidor.')
        if self.site_offline:
            msg.setInformativeText('Introduzca IP, puerto y proxy válidos.')
            msg.setWindowTitle("Error de conexión")
        else:
            msg.setInformativeText('Pruebe de nuevo, o modo "offline"')
            msg.setWindowTitle("Error de conexion (offline)")            
        msg.exec_()        
    
    
    def get_icon_path(self, icon):
        path = self.config["icons_folder"] + icon + ".svg"
        return path
    
    
    def clean_connections(self):
        if self.proxy: self.proxy._pyroRelease()
        if self.deco_proxy: self.deco_proxy._pyroRelease()
        logging.debug('Proxy/s closed')
        
        if self.tunnels:
            ssh_tunneling.close_tunnels(self.tunnels)
            self.tunnels.clear()
            logging.debug('Tunnels closed')
            
    
    def closeEvent(self, event):
        self.clean_connections()
        self.deleteLater()
                
    
    
def main():
    app = QtWidgets.QApplication(sys.argv)
    ui = MainWindow() 
    
    menu = QtWidgets.QMenu()
    
    app_icon = QtGui.QIcon()
    app_icon.addFile('app_icon.png')
    app.setWindowIcon(app_icon)
    
    tray_icon = QtWidgets.QSystemTrayIcon()
    tray_icon.setIcon(app_icon)
    tray_icon.setContextMenu(menu)
    tray_icon.show()
    tray_icon.setToolTip("RailWatch")
    tray_icon.showMessage("hoge", "moge")
    
    ui.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()
    

