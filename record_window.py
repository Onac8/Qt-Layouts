# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets, uic
import os, logging
import sys
import paramiko
import threading
import subprocess
from datetime import datetime
import app_api
ACTUAL_PATH = os.path.dirname(__file__)
sys.path.append(os.path.join(ACTUAL_PATH, '../modules'))
sys.path.append(os.path.join(ACTUAL_PATH, '../railwatch_modules'))
from video_merger.video_merger import VideoMerger


class RecordWindow(QtWidgets.QDialog):
    def __init__(self, site_id, site_ip_dns, proxy, tunnels, configObj, is_offline, user, user_privileges, ssh_ports):
        super().__init__()
        uic.loadUi('record_window_2.ui', self) # Loading the .ui file
        self.setWindowTitle('RailWatch Desktop App - Grabaciones')
        
        # self.Form = Form
        self.site_id = site_id
        self.site_ip_dns = site_ip_dns
        self.proxy = proxy
        self.tunnels = tunnels
        self.configObj = configObj
        self.is_offline = is_offline
        self.user = user
        self.user_privileges = user_privileges
        self.ssh_ports = ssh_ports
        
        self.config = None
        self.output_path = None
        self.output_codec = None
        self.output_ext = None
        self.output_file_name = None
        
        self.loadDefaultValues()
        
        logging.debug('Layout created.')
        
        
        #SIGNALS--------------------------------------------------------
        self.listWidget.itemDoubleClicked.connect(lambda x:self.double_clicked_open_file(x))
        self.button.clicked.connect(self.on_search_button_clicked)
        self.button_report.clicked.connect(self.on_button_create_report)
        self.button_report2.clicked.connect(self.on_button_create_report_all)
        self.toolButton.clicked.connect(self.on_pushButton_selectFolder)
        
        
    def loadDefaultValues(self):
        self.config = self.configObj.read_config()
        
        self.lineEdit_recordFolder.setText(self.config['recordings_folder'])
        self.label.setText('')
        self.progressBar.hide()
        
        # TO MERGER------
        self.output_path = self.config['recordings_folder']
        self.output_codec = self.config['report_output_codec']
        self.output_ext = self.config['report_output_ext']
        self.output_file_name = datetime.now().strftime('REPORT_%Y_%m_%d_%H00')
        #-----------
        
        
    def on_search_button_clicked(self):
        self.listWidget.clear()
        self.label.setText('')
        self.progressBar.hide()
        records = self.check_date()
        records.sort()
        logging.debug("Detected files: " + str(records))
        
        if not records:
            self.listWidget.addItem('No se encontraron resultados en la fecha: ' + 
                                    str(self.calendarWidget.selectedDate().toString()) + 
                                    " | Hora: " + self.timeWidget.time().toString())
        else:
            for record in records:
                item = QtWidgets.QListWidgetItem(record)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable) # 0 unchecked | 2 checked
                item.setCheckState(QtCore.Qt.Unchecked)
                self.listWidget.addItem(item)
            self.set_buttons(True)


    def check_date(self):
        app_api.check_conn(self.tunnels, self.proxy, self.config['users_keys_path'][self.user])
        if self.is_offline:
            files = self.proxy.get_recordings_list() # file format : SITE-NAME_192.168.0.87_20200728_1449 
        else:
            files = self.proxy.get_recordings_list(self.site_id, self.user) 
            
        records=[]
        date = self.calendarWidget.selectedDate()
        hour = self.timeWidget.time().hour()
        for file in files:
            file_name = file.split('/')[-1]
            file_date = file_name.split('_')[2]
            file_hour = file_name.split('_')[-1]
            try:
                if (date.year() == int(file_date[0:4]) and 
                    date.month() == int(file_date[4:6]) and 
                    date.day() == int(file_date[6:8])):
                    if hour <= int(file_hour[0:2]) and int(file_hour[0:2]) < (hour+1):
                        records.append(file_name)
            except TypeError:
                logging.debug("Invalid file format detected...")
        if not records:
            logging.info("One or more invalid file format detected -> Ignored")
        return records
    

    def double_clicked_open_file(self, item):
        if not 'REPORT' in item.text():
            self.check_if_downloaded(item.text())
            
        path = self.config['recordings_folder'] + item.text()
        if sys.platform == "win32":
            try:
                os.startfile(os.path.normpath(path))
            except Exception as ex:
                logging.warning(str(ex))
                logging.warning("Can't open file: " + path)
        else:
            opener ="open" if sys.platform == "darwin" else "xdg-open"
            try:
                subprocess.call([opener, os.path.normpath(path)])
            except:
                logging.warning("Can't open file (Linux): " + path)
        
    
    #Report creator buttons----------------------------------------------------
    def on_button_create_report_all(self):
        files = []
        for i in range(self.listWidget.count()):
            self.check_if_downloaded(self.listWidget.item(i).text())
            file_path = self.config['recordings_folder'] +  self.listWidget.item(i).text()
            files.append(file_path)
        self.do_merger(files)
                
        
    def on_button_create_report(self):
        files = []
        for i in range (self.listWidget.count()):
            if self.listWidget.item(i).checkState() == 2: # 0 unchecked | 2 checked
                self.check_if_downloaded(self.listWidget.item(i).text())
                file_path = self.config['recordings_folder'] + self.listWidget.item(i).text()
                files.append(file_path)
                
        if files:
            self.do_merger(files)
        else:
            self.listWidget.clear()
            self.listWidget.addItem('Seleccione algún archivo para genererar el informe, o haga click en "Generar Informe Todos".')
            self.set_buttons(False)
    #--------------------------------------------------------------------------
            
    
    def on_pushButton_selectFolder(self):
        logging.debug('[Record Window]: Choosing new default recordings folder...')
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Eliga una carpeta", './', QtWidgets.QFileDialog.ShowDirsOnly)
        path = path + '/'
        self.lineEdit_recordFolder.setText(path)
        app_api.change_recordings_folder(self.configObj, path)
        self.loadDefaultValues()
        logging.debug('[Record Window]: New recordings folder selected.')
    
    
    def check_if_downloaded(self, file):
        local_files = app_api.get_recordings_list(self.configObj)
        if file in local_files:
            logging.debug("File downloaded already: " + file)
            self.label.setText("Archivo ya descargado: " + file)
        else:
            logging.debug("Downloading file -> " + file)
            self.label.setText("Descargando archivo -> " + file)
            self.do_ftp(file)
            logging.debug("File downloaded in " + self.config['recordings_folder'] + file)
        
    
    def get_icon_path(self, icon):
        path = self.config["icons_folder"] + icon + ".svg"
        return path
    
    def set_buttons(self, boolean):
        if self.user_privileges.get('get_report') == True:
            self.button_report.setEnabled(boolean)
            self.button_report2.setEnabled(boolean)
        

    def do_merger(self, files):
        logging.debug("Generating report video for those %s files...", self.listWidget.count())
        self.listWidget.clear()
        self.progressBar.show()
        self.progressBar.reset()
        self.listWidget.addItem('Generando video. Puede tardar unos minutos. Por favor, espere...')
        self.label.setText("Generando video reporte...")
        
        merger = VideoMerger(files, self.output_path, self.output_codec, self.output_ext, self.output_file_name)
        try:
            merger.generate(False)
            self.progressBar.setEnabled(True)
            while merger.is_in_progress():
                progress = merger.get_progress()
                self.progressBar.setValue(progress)
                logging.debug(progress)
            if merger.is_done():
                self.progressBar.setValue(100)
                self.label.setText("¡Informe generado!")
                self.listWidget.clear()
                file_name = self.output_file_name + '.' + self.output_ext
                self.listWidget.addItem(file_name)
        except Exception as e:
            self.listWidget.clear()
            self.listWidget.addItem('No se pudo generar el informe: ' + e)
            self.set_buttons(False)        
    

    def do_ftp(self, file):
        app_api.check_conn(self.tunnels, self.proxy, self.config['users_keys_path'][self.user])
        
        localpath = self.config['recordings_folder'] + file
        localpath = os.path.normpath(localpath)
        if sys.platform == "win32":
            key_path = paramiko.RSAKey.from_private_key_file(self.config['users_keys_path'][self.user])
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                if self.is_offline:
                    remotepath = self.proxy.get_recordings_folder() + file #Example: /grabaciones/Ing_192.168.0.87_20200728_1400.mp4
                    ssh.connect(self.site_ip_dns, username=self.user, port=self.ssh_ports[0], pkey = key_path)
                    # ssh.connect(self.site_id, username='adrianriao', port=self.ssh_ports[0], pkey = key_path)
                else:
                    remotepath = self.proxy.get_recordings_folder(self.site_id, self.user) + file
                    site_ip_dns = self.proxy.get_ip(self.site_id, 'recorder')
                    puerto = self.proxy.get_ssh_port(self.site_id, 'recorder')
                    ssh.connect(site_ip_dns, port=puerto, username=self.user, pkey = key_path)
                    # ssh.connect(self.proxy.get_ip(self.site_id, 'recorder'), port=puerto, username='adrianriao', pkey = key_path)
                sftp = ssh.open_sftp()
                sftp.get(remotepath, localpath)
                sftp.close()
                ssh.close()
            except Exception as ex:
                logging.warning('[Record Window]: ' + str(ex))
        else:
            key_path = self.config['users_keys_path'][self.user]
            remotepath = self.user + '@'
            try:
                if self.is_offline:
                    remotepath += self.site_ip_dns + ':/' + self.proxy.get_recordings_folder() + file #Example: /grabaciones/Ing_192.168.0.87_20200728_1400.mp4
                    subprocess.call(['scp', '-i', key_path, '-P', str(self.ssh_ports[0]), remotepath, localpath])
                else:
                    site_ip_dns = self.proxy.get_ip(self.site_id, 'recorder')
                    remotepath += site_ip_dns + ':/' + self.proxy.get_recordings_folder(self.site_id, self.user) + file
                    logging.warning(remotepath)
                    logging.warning(localpath)
                    subprocess.call(['scp', '-i', key_path, remotepath, localpath])
            except Exception as ex:
                logging.warning('[Record Window]: ' + str(ex))
            

def main():
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = RecordWindow('ingenieria', 'central_server', 'false', 'ena')
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())
        
if __name__ == "__main__":
    main()    

