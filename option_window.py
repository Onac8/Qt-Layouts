from PyQt5 import QtCore, QtGui, QtWidgets, uic
import sys
from json_window import JsonWindow
from background_window import BackgroundWindow
from detection_zone_window import DetectionZoneWindow
import logging
import app_api

class OptionWindow(QtWidgets.QDialog):
    def __init__(self, main_window, proxy, tunnels, configObj, user, deco_proxy=None, site_offline=None, ssh_ports=None):
        super().__init__()
        self.main_window = main_window
        uic.loadUi('option_window.ui', self) # Load the .ui file
        self.setWindowTitle('RailWatch Desktop App - Opciones')
        
        self.configObj = configObj # CONFIG_MODULE_OBJ
        self.config = configObj.read_config()
        
        self.user = user
        self.users = app_api.get_user_list(self.configObj)
        self.proxy = proxy
        self.tunnels = tunnels
        self.deco_proxy = deco_proxy
        self.site_offline = site_offline
        self.ssh_ports = ssh_ports
        self.my_ip = app_api.get_my_ip()
        self.button_apply = None
        self.button_reset = None
        self.user_privileges = app_api.get_user_privileges(self.configObj, self.user)
        
        if not self.site_offline:
            app_api.check_conn(self.tunnels, self.proxy, self.config['users_keys_path'][self.user])
            self.sites = self.proxy.get_places() #all sites stored in CentralS (list)
            self.proxy.report_conection(self.user, self.my_ip)
        else: # Direct mode
            self.sites = self.site_offline
        
        #Loading default values
        self.loadDefaultValues()
        
        logging.debug('[Conf]: Layout created.')
        
        #SIGNALS AND SLOTS-----------------------------------------------------
        self.listWidgetDevices.currentItemChanged.connect(self.on_listWidgetDevices_clicked) # Selected DEVICE -- Lateral BAR
        #Server
        self.comboBox_server.currentIndexChanged.connect(self.on_comboBox_server_clicked) # Selected site SC
        self.comboBox_server_2.currentIndexChanged.connect(self.on_comboBox_server_2_clicked) # Selected site SC
        self.pushButton_server.clicked.connect(self.on_pushButton_addSite) # Selected site GRABADOR
        self.pushButton_server_2.clicked.connect(self.on_pushButton_showSiteConfig)
        self.pushButton_server_3.clicked.connect(self.on_pushButton_deleteSite)
        self.pushButton_server_4.clicked.connect(self.on_pushButton_showAllConfig)
        self.pushButton_server_5.clicked.connect(self.on_pushButton_showSiteConfig_2)
        #Grabador
        self.comboBox_grabador.currentIndexChanged.connect(self.on_comboBox_grabador_clicked) # Selected site GRABADOR
        self.pushButton_grabador.clicked.connect(self.on_pushButton_showRecorderConfig)
        self.pushButton_grabador_2.clicked.connect(self.on_pushButton_reset_grabador)
        #Deco
        self.comboBox_deco.currentIndexChanged.connect(self.on_comboBox_deco_clicked) # Selected site DECO
        self.pushButton_deco_1.clicked.connect(self.on_pushButton_showDecoConfig)
        self.pushButton_deco_2.clicked.connect(self.on_pushButton_setDecoBackground)
        self.pushButton_deco_3.clicked.connect(self.on_pushButton_reset_deco)
        self.pushButton_deco_set_zone.clicked.connect(self.on_pushButton_setDecoZone)
        #App
        self.comboBox_app.currentIndexChanged.connect(self.on_comboBox_app_clicked) # Selected user APP
        self.pushButton_app_2.clicked.connect(self.on_pushButton_showAppConfig)
        self.pushButton_app_1.clicked.connect(self.on_pushButton_selectFolder)
        #Apply, Cancel, Accept, Reset
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).clicked.connect(self.on_buttonBox_apply)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.on_buttonBox_reject)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.on_buttonBox_accept) #Apply, accept and leave
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Reset).clicked.connect(self.on_buttonBox_reset_app)
        
        
        #Signals to activate apply--------------------------------
        #Server
        self.lineEdit_server_1.textEdited.connect(self.on_applyOn)
        self.lineEdit_server_2.textEdited.connect(self.on_applyOn)
        self.lineEdit_server_3.textEdited.connect(self.on_applyOn)
        self.spinBox_server.valueChanged.connect(self.on_applyOn)
        self.lineEdit_server_5.textEdited.connect(self.on_applyOn)
        self.lineEdit_server_6.textEdited.connect(self.on_applyOn)
        self.lineEdit_server_7.textEdited.connect(self.on_applyOn)
        self.lineEdit_server_11.textEdited.connect(self.on_applyOn)
        self.lineEdit_server_12.textEdited.connect(self.on_applyOn)
        self.spinBox_server_2.valueChanged.connect(self.on_applyOn)
        self.spinBox_server_4.valueChanged.connect(self.on_applyOn)
        #Grabador
        self.lineEdit_grabador_1.textEdited.connect(self.on_applyOn)
        self.doubleSpinBox_grabador_1.valueChanged.connect(self.on_applyOn)
        self.lineEdit_grabador_2.textEdited.connect(self.on_applyOn)
        self.lineEdit_grabador_3.textEdited.connect(self.on_applyOn)
        self.lineEdit_grabador_4.textEdited.connect(self.on_applyOn)
        self.lineEdit_grabador_7.textEdited.connect(self.on_applyOn)
        self.lineEdit_grabador_8.textEdited.connect(self.on_applyOn)
        self.lineEdit_grabador_5.textEdited.connect(self.on_applyOn)
        self.lineEdit_grabador_6.textEdited.connect(self.on_applyOn)
        #Deco
        self.lineEdit_deco_1.textEdited.connect(self.on_applyOn)
        self.lineEdit_deco_2.textEdited.connect(self.on_applyOn)
        self.lineEdit_deco_3.textEdited.connect(self.on_applyOn)
        self.doubleSpinBox_deco.valueChanged.connect(self.on_applyOn)
        #App
        self.lineEdit_app_1.textChanged.connect(self.on_applyOn)
        self.checkBox_app_1.clicked.connect(self.on_applyOn)
        self.checkBox_app_2.clicked.connect(self.on_applyOn)
        self.checkBox_app_3.clicked.connect(self.on_applyOn)
        self.checkBox_app_4.clicked.connect(self.on_applyOn)
        self.lineEdit_app_2.textEdited.connect(self.on_applyOn)
        self.spinBox_app.valueChanged.connect(self.on_applyOn)
        self.lineEdit_app_4.textEdited.connect(self.on_applyOn)
        
    
    def loadDefaultValues(self):
        #Device option list (items + icons)--------------------------------------------
        self.listWidgetDevices.clear()
        logging.debug('[Conf]: Loading default values lateral widgets...')
        if not self.site_offline:
            if self.user_privileges['server_conf']: # user = ena/custom
                item = QtWidgets.QListWidgetItem(QtGui.QIcon(app_api.get_icon_path(self.configObj,'servidores')), 'Servidor Central')
                self.listWidgetDevices.addItem(item)
            if self.user_privileges['app_conf']: # user = ena/custom
                item = QtWidgets.QListWidgetItem(QtGui.QIcon(app_api.get_icon_path(self.configObj,'escritorio')), 'App')
                self.listWidgetDevices.addItem(item)
            if self.user_privileges['disp_conf']: # user = ena/railwatch/custom
                item = QtWidgets.QListWidgetItem(QtGui.QIcon(app_api.get_icon_path(self.configObj,'camera')), 'Grabador')
                self.listWidgetDevices.addItem(item)
                item = QtWidgets.QListWidgetItem(QtGui.QIcon(app_api.get_icon_path(self.configObj,'detector-de-metales')), 'Detector')
                self.listWidgetDevices.addItem(item)
        else:
            item = QtWidgets.QListWidgetItem(QtGui.QIcon(app_api.get_icon_path(self.configObj,'escritorio')), 'App')
            self.listWidgetDevices.addItem(item)
            item = QtWidgets.QListWidgetItem(QtGui.QIcon(app_api.get_icon_path(self.configObj,'camera')), 'Grabador')
            self.listWidgetDevices.addItem(item)
            item = QtWidgets.QListWidgetItem(QtGui.QIcon(app_api.get_icon_path(self.configObj,'detector-de-metales')), 'Detector')
            self.listWidgetDevices.addItem(item)
            
        self.listWidgetDevices.setIconSize(QtCore.QSize(40,40))
        
        # Getting Apply, Reset Buttons
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('Aceptar')
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('Cancelar')
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setText('Aplicar')
        self.button_reset = self.buttonBox.button(QtWidgets.QDialogButtonBox.Reset)
        self.button_reset.setText('Restaurar valores por defecto (APP)')
        self.button_apply = self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply)
        self.button_apply.setText('Aplicar')
        self.button_apply.setEnabled(False) # Apply button disabled by default
        self.button_reset.setEnabled(True)
        
        
        # Adding sites/users to ComboBoxes
        logging.debug('[Conf]: Loading combo boxes values...')
        if self.proxy and self.sites:
            if not self.site_offline:
                self.comboBox_server.addItems(self.sites)
                self.comboBox_server_2.addItems(self.sites)
                self.comboBox_grabador.addItems(self.sites)
                self.comboBox_deco.addItems(self.sites)
                self.comboBox_app.addItems(self.users)
            else: # only one row (offline)
                self.comboBox_grabador.addItem(self.sites)
                self.comboBox_deco.addItem(self.sites)
                self.comboBox_app.addItems(self.users)
        
        # Central server
        logging.debug('[Conf]: Setting placeholders...')
        self.lineEdit_server_1.setPlaceholderText('Mostoles_Madrid_Paso_1')
        self.lineEdit_server_9.setPlaceholderText('-40,10 [lat,lon]')
        self.lineEdit_server_2.setPlaceholderText('192.168.1.30')
        self.lineEdit_server_3.setPlaceholderText('recorder_cmd')
        self.lineEdit_server_4.setPlaceholderText('192.168.1.31')
        self.lineEdit_server_8.setPlaceholderText('deco_cmd')
                
        # App
        logging.debug('[Conf]: Setting app values...')
        self.pushButton_app_1.setIcon(QtGui.QIcon(app_api.get_icon_path(self.configObj,'carpeta')))
        self.pushButton_app_1.setIconSize(QtCore.QSize(25,25))
        
        self.lineEdit_app_1.setText(app_api.get_recordings_folder(self.configObj)) # CHANGE PATH IF W10 OR LINUX (C:USERS:USER:DOWNLOADS | USER/HOME/DOWNLOADS)
        self.lineEdit_app_2.setText(app_api.get_server_ip(self.configObj))
        self.spinBox_app.setValue(app_api.get_server_port(self.configObj))
        self.lineEdit_app_4.setText(app_api.get_server_proxy(self.configObj))
    #--------------------------------------------------------------------------
        
    
    #Menu lateral--------------------------
    def on_listWidgetDevices_clicked(self):
        logging.debug('[Conf]: Lateral List Widget clicked: ' + self.listWidgetDevices.currentItem().text())
        if self.listWidgetDevices.currentItem().text() == 'Servidor Central':
            self.tabStackWidget.setCurrentWidget(self.centralServerWidget)
        elif self.listWidgetDevices.currentItem().text() == 'Grabador':
            self.tabStackWidget.setCurrentWidget(self.grabadorWidget)
        elif self.listWidgetDevices.currentItem().text() == 'Detector':
            self.tabStackWidget.setCurrentWidget(self.detectorWidget)
        elif self.listWidgetDevices.currentItem().text() == 'App':
            self.tabStackWidget.setCurrentWidget(self.desktopAppWidget)
        
    
    def on_pushButton_addSite(self):
        app_api.check_conn(self.tunnels, self.proxy, self.config['users_keys_path'][self.user])
        logging.debug('[Central Server Conf]: Adding new site...')
        site_name = self.lineEdit_server_1.text() #if new_name = old_name --> modified  | otherwise new site added
        coords = self.lineEdit_server_9.text()
        grabador_ip = self.lineEdit_server_2.text()
        grabador_proxy = self.lineEdit_server_3.text()
        grabador_puerto = self.spinBox_server.value()
        deco_ip = self.lineEdit_server_4.text()
        deco_proxy = self.lineEdit_server_8.text()
        deco_puerto = self.spinBox_server_3.value()
        
        if (site_name and coords and 
            grabador_ip and grabador_proxy and grabador_puerto and 
            deco_ip and deco_proxy and deco_puerto):
            
            lat_lon = self.lineEdit_server_9.text().split(',')
            if len(lat_lon) == 2:
                self.pushButton_server.setEnabled(False)
                self.proxy.cs_add_place(site_name, grabador_ip, grabador_puerto, grabador_proxy, lat_lon, deco_ip, deco_puerto, deco_proxy)
                self.proxy.report_conection(self.user, self.my_ip)
            else:
                logging.warning('[Central Server Conf]: Error adding site (coords invalid format).')
                self.show_inputError_dialog('coords')
        else:
            logging.warning('[Central Server Conf]: Error adding site (one or more empty forms).')
            self.show_inputError_dialog('add_site')
        
    
    # TO DO---------------
    # TO DO---------------
    def on_pushButton_deleteSite(self):
        site_name = self.comboBox_server_2.currentText()
        pass
    #---------------------
    
    
    def on_pushButton_selectFolder(self):
        logging.debug('[App Conf]: Choosing new default recordings folder...')
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Eliga una carpeta", './', QtWidgets.QFileDialog.ShowDirsOnly)
        self.lineEdit_app_1.setText(path)
        self.on_applyOn()
        logging.debug('[App Conf]: New recordings folder selected.')
        
        
    def on_applyOn(self):
        logging.debug('[Conf]: Conf values changed. "Apply" button enabled.')
        self.button_apply.setEnabled(True)
        
        
        
    #  Apply  |  Cancel  |  Accept  |  Defaults  | Close -------------------------------
    def on_buttonBox_apply(self):
        self.saveOptions()
    
    def on_buttonBox_reject(self):
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.reject()
    
    def on_buttonBox_accept(self):
        if self.button_apply.isEnabled():
            self.saveOptions()
            self.accept() 
        else:
            self.accept() 
            
    def on_pushButton_reset_grabador(self):
        self.show_forms('disable_grabador', False)
        # app_api.check_conn(self.tunnels, self.proxy, self.config['users_keys_path'][self.user])
        # if site_grabador in self.sites: # sitio concreto seleccionado
        # self.proxy.set_recorder_default_cnf(site_grabador, self.user)
        
            
    def on_pushButton_reset_deco(self):
        self.show_forms('disable_deco', False)
        # app_api.check_conn(self.tunnels, self.proxy, self.config['users_keys_path'][self.user])
        # site_deco = self.comboBox_deco.currentText()
        # if site_deco in self.sites: # sitio concreto seleccionado
            # self.proxy.set_deco_default_cnf(self.site_deco, self.user)
        
        
    def on_buttonBox_reset_app(self):
        self.button_reset.setEnabled(False)
        self.button_apply.setEnabled(True)
        self.show_forms('disable_app', False)
        
        
    def closeEvent(self, event):
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.reject()
    # -------------------------------------------------------------------------
    
    
    # Configs (JSONs)--------------------------------------------------------------------------
    def on_pushButton_showAllConfig(self):
        logging.debug('[Central Server Conf]:Printing config: All')
        self.do_json_window('all', 'all')
    
    def on_pushButton_showSiteConfig(self):
        site = self.comboBox_server_2.currentText()
        logging.debug('[Central Server Conf]:Printing config: ' + site)
        self.do_json_window(site, 'site')
        
    def on_pushButton_showSiteConfig_2(self):
        site = self.comboBox_server.currentText()
        logging.debug('[Central Server Conf]: Printing config: ' + site)
        self.do_json_window(site, 'site')
    
    def on_pushButton_showRecorderConfig(self):
        site = self.comboBox_grabador.currentText()
        logging.debug('[Recorder Conf]: Printing config: recorder')
        self.do_json_window(site, 'recorder')
    
    def on_pushButton_showDecoConfig(self):
        site = self.comboBox_deco.currentText()
        logging.debug('[Deco Conf]: Printing config: deco')
        self.do_json_window(site, 'deco')
        
    def on_pushButton_showAppConfig(self):
        logging.debug('[App Conf]: Printing config: app')
        self.do_json_window('app', 'app')
    
    
    #Combo boxes clicked-----------------------------------------------------------------------
    def on_comboBox_server_clicked(self):
        app_api.check_conn(self.tunnels, self.proxy, self.config['users_keys_path'][self.user])
        site = self.comboBox_server.currentText()
        if site in self.sites: # sitio concreto seleccionado 
            self.show_forms('server', True)
            self.lineEdit_server_5.setText(site)
            self.lineEdit_server_6.setText(self.proxy.get_ip(site, 'recorder'))
            self.lineEdit_server_7.setText(self.proxy.get_proxy_name(site, 'recorder'))
            self.lineEdit_server_11.setText(self.proxy.get_ip(site, 'deco'))
            self.lineEdit_server_12.setText(self.proxy.get_proxy_name(site, 'deco'))
            coords = ', '.join([str(v) for v in self.proxy.get_coords(site)])
            self.lineEdit_server_10.setText(coords)
            self.spinBox_server_2.setValue(self.proxy.get_port(site, 'recorder'))
            self.spinBox_server_4.setValue(self.proxy.get_port(site, 'deco'))
            self.proxy.report_conection(self.user, self.my_ip)
        else:
            self.show_forms('server', False)
    
    
    def on_comboBox_server_2_clicked(self):
        site = self.comboBox_server_2.currentText()
        if site in self.sites: # sitio concreto seleccionado 
            self.show_forms('site', True)
        else:
            self.show_forms('site', False)
           
           
    def on_comboBox_grabador_clicked(self):
        app_api.check_conn(self.tunnels, self.proxy, self.config['users_keys_path'][self.user])
        site = self.comboBox_grabador.currentText()
        if site in self.sites: # sitio concreto seleccionado 
            if not self.site_offline:
                recorder_conf = self.proxy.get_recorder_config(site, self.user) # JSON File
            else:
                recorder_conf = self.proxy.get_config()
            self.show_forms('grabador', True)
            self.doubleSpinBox_grabador_1.setValue(float(recorder_conf['limite_disco_libre_gb']))
            self.lineEdit_grabador_1.setText(self.comboBox_grabador.currentText())
            # self.lineEdit_grabador_2.setText(self.proxy.get_proxy_name(site, 'recorder'))
            self.lineEdit_grabador_3.setText(recorder_conf['recordings_folder'])
            self.lineEdit_grabador_4.setText(recorder_conf['pilot_path'])
            self.lineEdit_grabador_7.setText(recorder_conf['activation_signal'])
            self.lineEdit_grabador_8.setText(recorder_conf['desactivation_signal'])
            self.proxy.report_conection(self.user, self.my_ip)
        else:
            self.show_forms('grabador', False)
            
    
    def on_comboBox_deco_clicked(self):
        app_api.check_conn(self.tunnels, self.proxy, self.config['users_keys_path'][self.user])
        site = self.comboBox_deco.currentText()
        if site in self.sites: # sitio concreto seleccionado 
            deco_conf = self.get_deco_conf(site)
            self.show_forms('deco', True)
            zone_str = [str(i) for i in deco_conf['algoritmo']['puntos_zona_deteccion']]
            zone_to_str = ', '.join(zone_str)
            self.lineEdit_deco_1.setText(deco_conf['video']['directorio_fondos'])
            self.lineEdit_deco_2.setText(zone_to_str)
            self.doubleSpinBox_deco.setValue(int(deco_conf['algoritmo']['porcentaje_deteccion']))
            self.lineEdit_deco_3.setText(deco_conf['video']['directorio_fondos'])
            # if not self.pushButton_deco_set_zone.isEnabled(): # Detection zone modified already
                # self.lineEdit_deco_2.setEnabled(False)
        else:
            self.show_forms('deco', False)
            
            
    def on_comboBox_app_clicked(self): #if user can access here, he has privileges
        user = self.comboBox_app.currentText()
        if user in self.users:
            self.show_forms('app', True)
            privileges = app_api.get_user_privileges(self.configObj, user)
            self.checkButtons(user,privileges)
        else:
            self.show_forms('app', False)
    #----------------------------------------------------------------------------------        
    
    
    def get_deco_conf(self, site): 
        if not self.site_offline:
            deco_conf = self.proxy.get_deco_config(site, self.user) # JSON File
        else:
            video_config = self.deco_proxy.get_config('video')
            algoritmo_config = self.deco_proxy.get_config('algoritmo')
            deco_conf = {}
            deco_conf['video'] = video_config
            deco_conf['algoritmo'] = algoritmo_config
        self.proxy.report_conection(self.user, self.my_ip)
        return deco_conf
    
    
    def show_forms(self, device, boolean):
        if device == 'server':
            self.lineEdit_server_5.setEnabled(boolean)
            self.lineEdit_server_6.setEnabled(boolean)
            self.lineEdit_server_7.setEnabled(boolean)
            self.lineEdit_server_10.setEnabled(boolean)
            self.lineEdit_server_11.setEnabled(boolean)
            self.lineEdit_server_12.setEnabled(boolean)
            self.spinBox_server_2.setEnabled(boolean)
            self.spinBox_server_4.setEnabled(boolean)
            self.pushButton_server_5.setEnabled(boolean)
        if device == 'site':
            self.pushButton_server_2.setEnabled(boolean)
            self.pushButton_server_3.setEnabled(boolean)
        if device == 'grabador':
            self.doubleSpinBox_grabador_1.setEnabled(boolean)
            self.lineEdit_grabador_1.setEnabled(boolean)
            self.lineEdit_grabador_2.setEnabled(boolean)
            self.lineEdit_grabador_3.setEnabled(boolean)
            self.lineEdit_grabador_4.setEnabled(boolean)
            self.lineEdit_grabador_7.setEnabled(boolean)
            self.lineEdit_grabador_8.setEnabled(boolean)
            self.lineEdit_grabador_5.setEnabled(boolean)
            self.lineEdit_grabador_6.setEnabled(boolean)
            self.pushButton_grabador.setEnabled(boolean)
            self.pushButton_grabador_2.setEnabled(boolean)
        if device == 'deco':
            self.lineEdit_deco_1.setEnabled(boolean)
            self.lineEdit_deco_2.setEnabled(boolean)
            self.pushButton_deco_set_zone.setEnabled(boolean)
            self.doubleSpinBox_deco.setEnabled(boolean)
            self.lineEdit_deco_3.setEnabled(boolean)
            self.pushButton_deco_2.setEnabled(boolean)
            self.pushButton_deco_1.setEnabled(boolean)
            self.pushButton_deco_3.setEnabled(boolean)
        if device == 'app':
            self.checkBox_app_1.setEnabled(boolean)
            self.checkBox_app_2.setEnabled(boolean)
            self.checkBox_app_3.setEnabled(boolean)
            self.checkBox_app_4.setEnabled(boolean)
        if device == 'disable_grabador':
            self.comboBox_grabador.setEnabled(boolean)
            self.show_forms('grabador', False)
        if device == 'disable_deco':
            self.comboBox_deco.setEnabled(boolean)
            self.show_forms('deco', False)
        if device == 'disable_app':
            self.lineEdit_app_1.setEnabled(boolean)
            self.pushButton_app_1.setEnabled(boolean)
            self.show_forms('app', False)
            self.groupBox_app_1.setEnabled(boolean)
            self.groupBox_app_2.setEnabled(boolean)
            self.groupBox_app_3.setEnabled(boolean)
            

    def checkButtons(self, user, privileges):
        self.checkBox_app_1.setChecked(privileges['disp_conf'])
        self.checkBox_app_2.setChecked(privileges['server_conf'])
        self.checkBox_app_3.setChecked(privileges['get_report'])
        self.checkBox_app_4.setChecked(privileges['offline_mode'])


    def do_json_window(self, site, site_id):
        app_api.check_conn(self.tunnels, self.proxy, self.config['users_keys_path'][self.user])
        if not self.deco_proxy:
            json_window = JsonWindow(self.proxy, site, self.config, site_id, self.user)
        else:
            json_window = JsonWindow(self.proxy, site, self.config, site_id, self.user, self.deco_proxy)
        # option_window.raise_()
        # json_window.show()
        json_window.exec_()
    
    
    def on_pushButton_setDecoBackground(self):
        app_api.check_conn(self.tunnels, self.proxy, self.config['users_keys_path'][self.user])
        
        site = self.comboBox_deco.currentText()
        if not self.deco_proxy:
            camera_link = self.proxy.get_thermal_url(site, self.user)
            logging.debug('[Deco conf] Creating termal camera widget -> Camera: ' + camera_link)
            background_window = BackgroundWindow(self.proxy, camera_link, self.configObj, self.user, site)
        else:
            camera_link = self.proxy_deco.get_thermal_url()
            logging.debug('[Deco conf] Creating termal camera widget (offline) -> Camera: ' + camera_link)
            background_window = BackgroundWindow(self.proxy, camera_link, self.configObj, self.user, site, self.deco_proxy)
        
        background_window.exec_()
        self.proxy.report_conection(self.user, self.my_ip)
        
    
    def on_pushButton_setDecoZone(self):
        app_api.check_conn(self.tunnels, self.proxy, self.config['users_keys_path'][self.user])
        
        site = self.comboBox_deco.currentText()
        if not self.deco_proxy:
            camera_link = self.proxy.get_thermal_url(site, self.user)
            deco_config = self.get_deco_conf(site)
            logging.debug('[Deco conf] Getting deco detection zone manually...')
            detectionZone_window = DetectionZoneWindow(self.proxy, camera_link, self.user, site, deco_config)
        else:
            camera_link = self.proxy.get_thermal_url()
            deco_config = self.get_deco_conf(site)
            logging.debug('[Deco conf] Getting deco detection zone manually (offline)...')
            detectionZone_window = DetectionZoneWindow(self.proxy, camera_link, self.user, site, deco_config, self.deco_proxy)
        
        detectionZone_window.exec_()
        self.proxy.report_conection(self.user, self.my_ip)
        # self.pushButton_deco_set_zone.setEnabled(False)
        self.on_comboBox_deco_clicked()
        
        
    #Savings-------------------------------------------------------------------------    
    def saveOptions(self): # set all options
        app_api.check_conn(self.tunnels, self.proxy, self.config['users_keys_path'][self.user])
        
        self.saveOptions_server()
        self.saveOptions_recorder()
        self.saveOptions_deco()
        self.saveOptions_app()
        
        #RESET CASES----------------------------------------------------------
        if not self.comboBox_grabador.isEnabled():
            site_grabador = self.comboBox_grabador.currentText()
            self.proxy.set_recorder_default_cnf(site_grabador, self.user)
            
        if not self.comboBox_deco.isEnabled():
            site_deco = self.comboBox_deco.currentText()
            self.proxy.set_deco_default_cnf(site_deco, self.user)
        
        if not self.button_reset.isEnabled(): # Button pressed
            self.configObj.set_default_config()
        #----------------------------------------------------------------------
        
        self.button_apply.setEnabled(False) #for new invokes
        self.proxy.report_conection(self.user, self.my_ip) #only one call? or one by one in each method?
        
     
    def saveOptions_server(self):
        if self.lineEdit_server_5.isEnabled(): #checking if section is enabled and not empty forms
            if (self.lineEdit_server_5.text() and self.lineEdit_server_6.text() and self.lineEdit_server_10.text() and
                self.lineEdit_server_7.text() and self.spinBox_server_2.value() and self.lineEdit_server_11.text() and
                self.lineEdit_server_12.text() and self.spinBox_server_4.value()):
                coords = self.lineEdit_server_10.text().strip().split(',')
                coords = [float(i) for i in coords]
                self.proxy.cs_add_place(self.lineEdit_server_5.text(), self.lineEdit_server_6.text(), self.spinBox_server_2.value(),
                                        self.lineEdit_server_7.text(), coords, self.lineEdit_server_11.text(),
                                        self.spinBox_server_4.value(), self.lineEdit_server_12.text())
            else:
                self.show_inputError_dialog()            
        
        
    def saveOptions_recorder(self):
        if self.lineEdit_grabador_1.isEnabled(): #checking if section is enabled
            site = self.comboBox_grabador.currentText()
            if not self.site_offline:
                if site != self.lineEdit_grabador_1.text():
                    self.proxy.change_recorder_siteid(site, self.user, site)
                if self.doubleSpinBox_grabador_1.value() > 0:
                    self.proxy.change_limit_free_disk(site, self.user, self.doubleSpinBox_grabador_1.value())
                else:
                    self.show_inputError_dialog('limit_gb')
                if self.lineEdit_grabador_3.text():
                    self.proxy.change_recordings_folder(site, self.user, self.lineEdit_grabador_3.text())
                if self.lineEdit_grabador_4.text():
                    self.proxy.change_recorder_pilotpath(site, self.user, self.lineEdit_grabador_4.text())
                if self.lineEdit_grabador_7.text():
                    self.proxy.change_activation_signal(site, self.user, self.lineEdit_grabador_7.text())
                if self.lineEdit_grabador_8.text():
                    self.proxy.change_desactivation_signal(site, self.user, self.lineEdit_grabador_8.text())
                if self.lineEdit_grabador_5.text():
                    self.proxy.add_camera_rtsp(site, self.user, self.lineEdit_grabador_5.text())
                    self.proxy.add_camera_http(site, self.user, self.lineEdit_grabador_5.text())
                if self.lineEdit_grabador_6.text():
                    self.proxy.rm_camera_ip(site, self.user, self.lineEdit_grabador_6.text())
                # self.proxy.change_proxy_name(site, self.user, self.lineEdit_grabador_2.text()) --> IMPLEMENT
            else:
                if site != self.lineEdit_grabador_1.text():
                    self.proxy.change_siteid(site)
                if self.doubleSpinBox_grabador_1.value() > 0:
                    self.proxy.change_limit_free_disk(self.doubleSpinBox_grabador_1.value())
                else:
                    self.show_inputError_dialog('limit_gb')
                if self.lineEdit_grabador_3.text():
                    self.proxy.change_recordings_folder(self.lineEdit_grabador_3.text())
                if self.lineEdit_grabador_4.text():
                    self.proxy.change_pilotpath(self.lineEdit_grabador_4.text())
                if self.lineEdit_grabador_7.text():
                    self.proxy.change_activation_signal(self.lineEdit_grabador_7.text())
                if self.lineEdit_grabador_8.text():
                    self.proxy.change_desactivation_signal(self.lineEdit_grabador_8.text())
                if self.lineEdit_grabador_5.text():
                    self.proxy.add_camera_rtsp(self.lineEdit_grabador_5.text())
                    self.proxy.add_camera_http(self.lineEdit_grabador_5.text())
                if self.lineEdit_grabador_6.text():
                    self.proxy.rm_camera_ip(self.lineEdit_grabador_6.text())
                # self.proxy.change_proxy_name(site, self.user, self.lineEdit_grabador_2.text()) --> IMPLEMENT


    def saveOptions_deco(self):
        if self.lineEdit_deco_1.isEnabled(): #checking if section is enabled
            point_list = self.lineEdit_deco_2.text().split(',')
            point_list_int = [int(i) for i in point_list]
            site = self.comboBox_deco.currentText()
            try:
                if not self.site_offline:
                    if self.lineEdit_deco_1.text():
                        pass #IMPLEMENT
                    if self.lineEdit_deco_2.text():
                        logging.info(point_list_int)
                        self.proxy.set_detection_zone(site, self.user, point_list_int)
                    if self.lineEdit_deco_3.text():
                        pass #IMPLEMENT
                    if self.doubleSpinBox_deco.value():
                        self.proxy.set_detection_perc(site, self.user, self.doubleSpinBox_deco.value())
                else:
                    if self.lineEdit_deco_1.text():
                        pass #IMPLEMENT
                    if self.lineEdit_deco_2.text():
                        self.deco_proxy.set_detection_zone(point_list_int)
                    if self.lineEdit_deco_3.text():
                        pass #IMPLEMENT
                    if self.doubleSpinBox_deco.value():
                        self.deco_proxy.set_detection_perc(self.doubleSpinBox_deco.value())
            except Exception as ex:
                        logging.warning('[Deco Conf]: {}'.format(ex))
                
    
    def saveOptions_app(self):
        #check values like privileges, server_ip, server_port, server_proxy. MESSAGE PLS REBOOT APP
        if self.lineEdit_app_1.text() != app_api.get_recordings_folder(self.configObj): #checking if new folder selected
            path = self.lineEdit_app_1.text() + '/'
            app_api.change_recordings_folder(self.configObj, path)
        if self.checkBox_app_1.isEnabled():
            privileges = app_api.get_user_privileges(self.configObj, self.comboBox_app.currentText())
            privileges['disp_conf'] = True if self.checkBox_app_1.isChecked() else False
            privileges['server_conf'] = True if self.checkBox_app_2.isChecked() else False
            privileges['get_report'] = True if self.checkBox_app_3.isChecked() else False
            privileges['offline_mode'] = True if self.checkBox_app_4.isChecked() else False
            app_api.change_user_privileges(self.configObj, self.comboBox_app.currentText(), privileges) 
        if self.lineEdit_app_2.text() and self.lineEdit_app_2.text() != app_api.get_server_ip(self.configObj):
            self.configObj.add_variable_config('central_server_ip', self.lineEdit_app_2.text())
        if self.spinBox_app.value() and self.spinBox_app.value() != app_api.get_server_port(self.configObj):
            self.configObj.add_variable_config('remote_tunnel_port', self.spinBox_app.value())
        if self.lineEdit_app_4.text() and self.lineEdit_app_4.text() != app_api.get_server_proxy(self.configObj):
            self.configObj.add_variable_config('central_server_proxy', self.lineEdit_app_4.text())
    
    
    def show_inputError_dialog(self, error=None):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setText('Introduzca los datos de entrada correctamente')
        if 'coords' in error:
            msg.setInformativeText('Introduzca unas coordenadas válidas (Lat, Lon).')
            msg.setWindowTitle("Error al añadir")
        elif 'add_site' in error:
            msg.setInformativeText('Introduzca todos los datos.')
            msg.setWindowTitle("Error al añadir")
        elif 'limit_gb' in error:
            msg.setInformativeText('El tamaño en disco no pueden ser 0 GB.')
            msg.setWindowTitle("Error al modificar")
        elif 'error' in error:
            pass
        else:
            msg.setInformativeText('Introduzca todos los datos.')
            msg.setWindowTitle("Error al añadir")            
        msg.exec_()  
    
    
# MAIN-------------------------------------------------------------------------
def main():
    # app = QtWidgets.QApplication(sys.argv)
    # ui = OptionWindow()
    # ui.show()
    # sys.exit(app.exec_())
    pass

if __name__ == "__main__":
    main()