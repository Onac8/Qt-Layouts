# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets, uic
import logging
import hashlib
from main_window import MainWindow
import json
import os, sys
import app_api
import argparse
from setup_logger import MyLogger
from Pyro5.api import Proxy
ACTUAL_PATH = os.path.dirname(__file__)
sys.path.append(os.path.join(ACTUAL_PATH, '../modules'))
sys.path.append(os.path.join(ACTUAL_PATH, '../railwatch_modules'))
from config_module.config_module import ConfigModule
from ssh_tunneling import ssh_tunneling
import init_log
import time

###############################################################################
###############################PYINSTALLER#####################################
#pyuic5 -x xxx.ui -o xxx.py
#pyinstaller --onefile --windowed --name="RAILWATCH_APP" log_window.py
###############################################################################
###############################################################################

CONFIG_FILE_PATH = "./config_file.json"
CONFIG_FILE_DEFAULT = "./default_config_file.json"

def parse_args ():
    parser = argparse.ArgumentParser(description="Desktop App")
    parser.add_argument('--log', help="Set the logging level [DEBUG|INFO|WARNING|ERROR|CRITICAL]")
    args = parser.parse_args()
    return args



class LogWindow(QtWidgets.QMainWindow):
    def __init__(self, configObj):
        super().__init__()
        logging.debug('Creating Log Window Qt Layout --> ' + str(self))
        uic.loadUi('log_window_v2.ui', self) # Load the .ui file
        self.setWindowTitle('RailWatch Desktop App')
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        
        self.configObj = configObj
        self.config = self.configObj.read_config()
        
        self.offline = False
        self.offline_remote = False
        self.proxy = None
        self.proxy_deco = None
        self.tunnels = [] #All SSH Tunnel connections
        # self.tunnel_deco = None
        self.user = None
        self.main_window = None
        self.ssh_agent = False #SSH key agent false = WIN32/64 (default), else Linux
        
        if sys.platform != "win32":
            self.ssh_agent = True
        
        
        # self.pushButton_app_1.setIcon(QtGui.QIcon(app_api.get_icon_path(self.configObj,'carpeta')))
        # self.pushButton_app_1.setIconSize(QtCore.QSize(25,25))
        
        logging.debug('Layout created!')
        
        #SIGNALS--------------------------------------------------------
        self.pushButton_validate.clicked.connect(self.on_pushButtonLog_clicked)
        self.groupBox.clicked.connect(self.on_pushOffline_checked)
        self.groupBox_2.clicked.connect(self.on_pushOfflineRemote_checked)
        
        
    def on_pushButtonLog_clicked(self):
        if not self.offline:
            self.user = self.check_user(self.lineEdit_user.text(), self.lineEdit_pass.text())
            if self.user:
                self.do_tunnels_proxy()
            else:
                logging.warning('Unrecognized User/Password.')
                self.show_error_dialog('auth')
        else:
            self.user = self.check_user(self.lineEdit_user.text(), self.lineEdit_pass.text())
            if not self.user:
                logging.warning('Unrecognized User/Password.')
                self.show_error_dialog('auth')
            elif(not self.lineEdit_ip.text() or not self.lineEdit_ip_deco.text() 
                 or not self.lineEdit_proxy.text() or not self.lineEdit_proxy_deco.text() 
                 or not self.spinBox_port.value() or not self.spinBox_port_deco.value()):
                self.show_error_dialog('offline')
            elif app_api.get_user_privileges(self.configObj, self.user)['offline_mode'] == False : 
                self.show_error_dialog('not_auth')
                logging.warning('Offline mode: permission denied. User dont have the proper privileges. Redirecting to loggin...')
            elif self.offline_remote:
                if (not self.spinBox_port_3.value() or not self.spinBox_port_4.value()):
                    self.show_error_dialog('offline')
                else:
                    self.do_tunnels_proxy()
            else:    
                self.do_tunnels_proxy()
        
    
    def on_pushOffline_checked(self):
        if self.groupBox.isChecked():
            self.offline = True
            self.groupBox_2.setEnabled(True)
        else:
            self.offline = False
            self.groupBox_2.setEnabled(False)
            
    
    def on_pushOfflineRemote_checked(self):
        if self.groupBox_2.isChecked():
            self.offline_remote = True
        else:
            self.offline_remote = False

    
    def do_tunnels_proxy(self):
        self.tunnels.clear()
        if self.offline:
            try:
                self.tunnels.append(self.get_ssh_tunnel())
                self.tunnels.append(self.get_ssh_tunnel(True))
                logging.debug('SSH Tunnel created (offline) --> ' + str(self.tunnels))
                self.proxy = self.get_proxy(self.tunnels[0]) #Creating disp "proxy"
                self.proxy_deco = self.get_proxy(self.tunnels[1], True)
                logging.debug('Proxy created (offline, recorder) --> ' + str(self.proxy))
                logging.debug('Proxy created (offline, recorder) --> ' + str(self.proxy_deco))
                
                # Reporting connection to central server
                ip = app_api.get_my_ip()
                if ip:
                    app_api.check_conn(self.tunnels, self.proxy, self.config['users_keys_path'][self.user])
                    self.proxy.report_conection(self.user, ip)
                
                self.do_main()
            except Exception as ex: # Cannot connect to disp
                logging.warning('SSH Tunnel: ' + str(ex) + ' .Connection Error. Cannot connect to dispositive. Please retry...')
                self.show_error_dialog('conn')
        else:
            try:
                self.tunnels.append(self.get_ssh_tunnel())
                logging.debug('SSH Tunnel created --> ' + str(self.tunnels))
                self.proxy = self.get_proxy(self.tunnels[0]) #Creating server "proxy"
                logging.debug('Proxy created --> ' + str(self.proxy))
                    
                # Reporting connection to central server
                ip = app_api.get_my_ip()
                if ip:
                    app_api.check_conn(self.tunnels, self.proxy, self.config['users_keys_path'][self.user])
                    self.proxy.report_conection(self.user, ip)
                
                self.do_main()
            except Exception as ex: # Cannot connect to server
                logging.warning('SSH Tunnel: ' + str(ex) +  '. Connection Error. Cannot connect to Central Server. Going offline...')
                self.show_error_dialog('conn')
            
    
    def get_ssh_tunnel(self, is_tunnel_deco=False):
        if self.offline_remote:
            if is_tunnel_deco:
                ssh_p = self.spinBox_port_4.value()
            else:
                ssh_p = self.spinBox_port_3.value()
        else:
            ssh_p = 22
            
        if self.offline:
            if is_tunnel_deco: # first direct tunnel
                logging.debug('Setting up SSH Tunnel in offline mode --> Direct connection to device (deco)...')
                tunnel= ssh_tunneling.create_tunnel(self.lineEdit_ip_deco.text(), 
                                                  self.spinBox_port_deco.value(),
                                                  self.lineEdit_user.text(),
                                                  self.config['users_keys_path'][self.user], 
                                                  agent = self.ssh_agent, 
                                                  ssh_port = ssh_p)
            else: # second direct tunnel
                logging.debug('Setting up SSH Tunnel in offline mode --> Direct connection to device (recorder)...')
                tunnel= ssh_tunneling.create_tunnel(self.lineEdit_ip.text(), 
                                                      self.spinBox_port.value(),
                                                      self.lineEdit_user.text(),
                                                      self.config['users_keys_path'][self.user], 
                                                      agent = self.ssh_agent,
                                                      ssh_port = ssh_p)
        else:
            logging.debug('Setting up SSH Tunnel in standard mode --> Connection through Central Server...')
            tunnel= ssh_tunneling.create_tunnel(self.config['central_server_ip'], 
                                                self.config['central_server_port'],
                                                self.user,
                                                self.config['users_keys_path'][self.user], 
                                                agent = self.ssh_agent)
        return tunnel
    
    
    def get_proxy(self, tunnel, is_deco_proxy=False):  
        tunnel_ip_ports_list = tunnel.local_bind_addresses
        local_ip, local_port = tunnel_ip_ports_list[0]
        if self.offline:
            if is_deco_proxy:
                logging.debug('Getting Pyro Proxy in offline mode -> Direct connection to device (deco)...')
                uri = 'PYRO:' + self.lineEdit_proxy_deco.text() + '@' + str(local_ip) + ':' + str(local_port)
            else:
                logging.debug('Getting Pyro Proxy in offline mode -> Direct connection to device (recorder)...')
                uri = 'PYRO:' + self.lineEdit_proxy.text() + '@' + str(local_ip) + ':' + str(local_port)
        else:
            logging.debug('Getting Pyro Proxy in standard mode -> Connection through Central Server...')
            uri = 'PYRO:' + self.config["central_server_proxy"] + '@' + str(local_ip) + ':' + str(local_port)
          
        proxy = Proxy(uri)
        return proxy
    
    
    def do_main(self):
        if not self.offline:
            self.main_window = MainWindow(self, self.user, self.configObj, self.proxy, self.tunnels)
            logging.debug('Creating Main Window (direct mode =' + str(self.offline) + ') --> ' + str(self.main_window))
        else:
            app_api.check_conn(self.tunnels, self.proxy, self.config['users_keys_path'][self.user])
            site_offline = self.proxy.get_config()['site_id']
            ssh_ports = [self.spinBox_port_3.value(),self.spinBox_port_4.value()]
            self.main_window = MainWindow(self, self.user, self.configObj, self.proxy, self.tunnels, self.proxy_deco, site_offline, ssh_ports, self.lineEdit_ip.text())
            logging.debug('Creating Main Window (offline =' + str(self.offline) + ') --> ' + str(self.main_window))
        self.main_window.show()
        # self.hide_buttons()
        self.hide()
    
    
    # def hide_buttons(self):
    #     self.lineEdit_user.setEnabled(False)
    #     self.lineEdit_pass.setEnabled(False)
    #     self.pushButton_validate.setEnabled(False)
    #     self.groupBox.setEnabled(False)
    #     self.label_4.setText('¡Validado!')
        
    
    # User checking -----------------------------------------------------------
    '''
    Checking user+password combination. Return real user if success, empty string otherwise. 
    '''
    def check_user(self, user, password):
        if user and password:
            hash_str = self.do_hash(user, password) # getting hash
            return self.check_hash_json(user, hash_str)
        else:
            return user
        
    def do_hash(self, user, password):
        coin = user + password
        joker = hashlib.md5()
        joker.update(coin.encode('utf-8'))        
        return joker.hexdigest()
    
    def check_hash_json(self, key, hash_str):
        user = ''
        with open('joker.json') as f:
            data = json.load(f)
            for key, value in data.items():
                if data[key] == hash_str : user=key
        return user
    #--------------------------------------------------------------------------
    
    
    def show_error_dialog(self, text):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        if 'conn' in text:
            msg.setWindowTitle("Error de conexión")
            msg.setText('No se puede conectar con el servidor/dispositivo. Inténtelo de nuevo')
        elif 'auth' in text:
            msg.setWindowTitle("Error de identificación")
            msg.setText('Usuario y/o contraseña incorrectos. Inténtelo de nuevo')
        elif 'offline' in text:
            msg.setWindowTitle("Error de identificación")
            msg.setText('Introduzca todos los parámetros')
        elif 'not_auth' in text:
            msg.setWindowTitle("Error de identificación")
            msg.setText('No tiene permisos para acceder al modo directo')
        else:
            msg.setText('Introduzca usuario y contraseña')
        msg.exec_()
    
    
    def clean_connections(self):
        if self.proxy: self.proxy._pyroRelease()
        if self.proxy_deco: self.proxy_deco._pyroRelease()
        logging.debug('Proxy/s closed')
        
        if self.tunnels:
            ssh_tunneling.close_tunnels(self.tunnels)
            self.tunnels.clear()
            logging.debug('Tunnels closed')
    
    
    def closeEvent(self, event):
        self.clean_connections()
    
    
def main():
    configObj= ConfigModule(CONFIG_FILE_PATH, CONFIG_FILE_DEFAULT)
    configObj_default = ConfigModule(CONFIG_FILE_DEFAULT, CONFIG_FILE_DEFAULT)
    config = configObj.read_config()
    
    #Login----------------
    args = parse_args()
    if args.log:
        loglevel = args.log
    else:
        loglevel = config['default_loglevel']
    setup_logger = MyLogger('', loglevel, config['log_path'], 
							filemode='maxzise', maxBytes=config['maxBytes_log'],
							backupCount=config['backupCount'])
    setup_logger.configurar_fichero()
    log_initializer = init_log.LogInitializer(config['log_path'], CONFIG_FILE_PATH, 'DESKTOP APP', config['default_loglevel'])
    log_initializer.print_init_log()
    log_initializer.print_version_log(config['version_file'])
    log_initializer.print_config_log()
    #--------------------
    
    #App - setting default recordings directory
    home = os.path.expanduser("~")
    # default_dir = os.path.join(home, "Downloads")
    default_dir = home + '/'
    configObj.add_variable_config('recordings_folder', default_dir)
    configObj_default.add_variable_config('recordings_folder', default_dir)
    
    #App loading
    app = QtWidgets.QApplication(sys.argv)
    ui = LogWindow(configObj)
    
    #App icons
    menu = QtWidgets.QMenu()
    app_icon = QtGui.QIcon()
    app_icon.addFile(app_api.get_icon_path(configObj, 'app'))
    app.setWindowIcon(app_icon)
    tray_icon = QtWidgets.QSystemTrayIcon()
    tray_icon.setIcon(app_icon)
    tray_icon.setContextMenu(menu)
    tray_icon.show()
    tray_icon.setToolTip("RailWatch App")
    
    #App show
    ui.show()
    sys.exit(app.exec_())
    ui.deleteLater()
    
if __name__ == "__main__":
    main()