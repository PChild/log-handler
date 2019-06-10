from PyQt5.QtWidgets import *
from PyQt5 import QtGui
import dslog2csv
import configparser
import glob
import sys
import os


class LogViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.config_file = 'config.ini'
        self.config = self.check_config()

        self.log_dir = self.config['DEFAULT']['LogLocation']
        self.output_dir = self.config['DEFAULT']['OutputLocation']

        self.title = 'DS Log Handler'
        self.left = 50
        self.top = 50
        self.width = 260
        self.height = 480

        self.list_view = None
        self.list_model = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.title)
        self.setFixedSize(self.width, self.height)

        file_path = QPushButton('Show files path')
        file_path.clicked.connect(self.on_button_clicked)

        click_check = QPushButton('Export selected logs')
        click_check.clicked.connect(self.convert_files)

        self.list_view = QListView()
        self.list_model = QtGui.QStandardItemModel(self.list_view)
        self.update_list_view()

        layout = QVBoxLayout()
        layout.addWidget(file_path)
        layout.addWidget(self.list_view)
        layout.addWidget(click_check)
        self.setLayout(layout)
        self.show()

    def update_list_view(self):
        log_files = [item[len(self.log_dir):] for item in glob.glob(self.log_dir + '*')]
        for log in log_files:
            self.list_model.appendRow(LogListItem(log))
        self.list_view.setModel(self.list_model)

    def on_button_clicked(self):
        alert = QMessageBox()
        alert.setText(self.log_dir)
        alert.exec_()

    def convert_files(self):
        event_files = []
        log_files = []
        for index in range(self.list_model.rowCount()):
            item = self.list_model.item(index)
            if item.checkState() == 2:
                file_type = item.text().split(".")[1]
                if file_type == "dslog":
                    log_files.append(item.text())
                if file_type == "dsevents":
                    event_files.append(item.text())

            print(item.text(), item.checkState())

        self.prep_out_location()

    def check_config(self):
        config = configparser.ConfigParser()

        if not os.path.exists(self.config_file):
            config.set('DEFAULT', 'LogLocation', "C:\\Users\\Public\\Documents\\FRC\\Log Files\\")
            config.set('DEFAULT', 'OutputLocation', os.getenv("userprofile") + "\\DS LOGS\\")
            config.set('DEFAULT', 'FirstRun', "FALSE")
            self.write_config(config)
        else:
            config.read(self.config_file)

            if config['DEFAULT']['FirstRun'] != "FALSE":
                config.set('DEFAULT', 'OutputLocation', os.getenv("userprofile") + "\\DS LOGS\\")
                config.set('DEFAULT', 'FirstRun', "FALSE")
                self.write_config(config)

        return config

    def write_config(self, config):
        with open(self.config_file, 'w') as configfile:
            config.write(configfile)

    def prep_out_location(self):
        if not os.path.exists(self.config['DEFAULT']['OutputLocation']):
            os.makedirs(self.config['DEFAULT']['OutputLocation'])


class LogListItem(QtGui.QStandardItem):
    def __init__(self, title):
        super().__init__(title)
        self.setCheckable(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ex = LogViewer()
    sys.exit(app.exec_())
