from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import QtGui
import dslog2csv
import configparser
import glob
import csv
import sys
import os


class LogViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.config_file = 'config.ini'
        self.config = self.check_config()

        self.log_dir = self.config['DEFAULT']['LogLocation']
        self.output_dir = self.config['DEFAULT']['OutputLocation']

        self.filter = "Matches"

        self.title = 'DS Log Handler'
        self.left = 50
        self.top = 50
        self.width = 560
        self.height = 480

        self.list_view = None
        self.list_model = None
        self.type_radios = None
        self.log_row = None
        self.out_row = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.title)
        self.setFixedSize(self.width, self.height)

        self.log_row = ButtonRow("Log Folder:", self.log_dir)
        self.out_row = ButtonRow("Out Folder:", self.output_dir)
        self.type_radios = RadioGroup("Log Type:", "Matches", "Practice", "Both")
        self.connect_to_radios(self.type_radios)

        self.list_view = QListView()
        self.list_model = QtGui.QStandardItemModel(self.list_view)
        self.update_list_view()

        click_check = QPushButton('Export selected logs')
        click_check.clicked.connect(self.convert_files)

        layout = QVBoxLayout()
        layout.addLayout(self.log_row)
        layout.addLayout(self.out_row)
        layout.addLayout(self.type_radios)
        layout.addWidget(self.list_view)
        layout.addWidget(click_check)
        self.setLayout(layout)
        self.show()

    def update_list_view(self):
        log_files = [item[len(self.log_dir):] for item in glob.glob(self.log_dir + '*.dslog')]
        self.list_model.removeRows(0, self.list_model.rowCount())
        for log in log_files:
            if self.filter == "Matches":
                if os.path.exists(self.log_dir + log[:-6] + '.dsevents'):
                    self.list_model.appendRow(LogListItem(log))
            elif self.filter == "Practice":
                if not os.path.exists(self.log_dir + log[:-6] + '.dsevents'):
                    self.list_model.appendRow(LogListItem(log))
            elif self.filter == "Both":
                self.list_model.appendRow(LogListItem(log))
        self.list_view.setModel(self.list_model)

    def convert_files(self):
        self.prep_out_location()

        log_files = []
        for index in range(self.list_model.rowCount()):
            item = self.list_model.item(index)
            if item.checkState() == 2:
                file_type = item.text().split(".")[1]
                if file_type == "dslog":
                    log_files.append(item.text())

        # CODE BELOW IS REIMPLEMENTED FROM DSLOG2CSV
        get_match_info = self.filter == "Matches"

        col = ['inputfile', ]
        if get_match_info:
            col.append('match_info')
        col.extend(dslog2csv.DSLogParser.OUTPUT_COLUMNS)

        for in_name in log_files:
            in_file = self.log_dir + in_name
            match_info = None

            if get_match_info:
                event_file = dslog2csv.find_event_file(in_file)
                if event_file:
                    # TODO Figure out why find_match_info is dying
                    match_info = dslog2csv.find_match_info(event_file)

            if get_match_info and not match_info:
                print("bad match info")
                continue

            outname = self.output_dir + in_name[:-6] + ".csv"
            outstrm = open(outname, 'w')
            outcsv = csv.DictWriter(outstrm, fieldnames=col, extrasaction='ignore')
            outcsv.writeheader()

            dsparser = dslog2csv.DSLogParser(in_file)
            for rec in dsparser.read_records():
                rec['inputfile'] = in_file
                rec['match_info'] = match_info

                for i in range(16):
                    rec['pdp_{}'.format(i)] = rec['pdp_currents'][i]

                outcsv.writerow(rec)
            dsparser.close()
            outstrm.close()

    def check_config(self):
        config = configparser.ConfigParser()

        if not os.path.exists(self.config_file):
            config.set('DEFAULT', 'LogLocation', "C:/Users/Public/Documents/FRC/Log Files/")
            config.set('DEFAULT', 'OutputLocation', os.getenv("userprofile") + "/DS LOGS/")
            config.set('DEFAULT', 'FirstRun', "FALSE")
            self.write_config(config)
        else:
            config.read(self.config_file)

            if config['DEFAULT']['FirstRun'] != "FALSE":
                config.set('DEFAULT', 'OutputLocation', os.getenv("userprofile") + "/DS LOGS/")
                config.set('DEFAULT', 'FirstRun', "FALSE")
                self.write_config(config)

        return config

    def write_config(self, config):
        with open(self.config_file, 'w') as configfile:
            config.write(configfile)

    def prep_out_location(self):
        if not os.path.exists(self.config['DEFAULT']['OutputLocation']):
            os.makedirs(self.config['DEFAULT']['OutputLocation'])

    @pyqtSlot(str)
    def on_changed(self, string):
        self.filter = string
        self.update_list_view()

    def connect_to_radios(self, radio_obj):
        radio_obj.changed.connect(self.on_changed)


class LogListItem(QtGui.QStandardItem):
    def __init__(self, title):
        super().__init__(title)
        self.setCheckable(True)


class ButtonRow(QHBoxLayout):
    def __init__(self, label, text):
        super().__init__()

        self.line_edit = QLineEdit()
        self.line_edit.setText(text)
        self.line_edit.setEnabled(False)

        self.folder_picker = QPushButton("Choose folder")
        self.folder_picker.clicked.connect(self.pick_folder)

        self.addWidget(QLabel(label))
        self.addWidget(self.line_edit)
        self.addWidget(self.folder_picker)

    def pick_folder(self):
        folder_name = QFileDialog.getExistingDirectory(directory=self.line_edit.text())
        if len(folder_name) > 0:
            self.line_edit.setText(folder_name)


class RadioGroup(QHBoxLayout):
    changed = pyqtSignal(str)

    def __init__(self, label, i1, i2, i3):
        super().__init__()
        self.addWidget(QLabel(label))
        self.i1 = QRadioButton(i1)
        self.i1.toggled.connect(lambda: self.click_handler(self.i1))
        self.i2 = QRadioButton(i2)
        self.i2.toggled.connect(lambda: self.click_handler(self.i2))
        self.i3 = QRadioButton(i3)
        self.i3.toggled.connect(lambda: self.click_handler(self.i3))
        self.i1.setChecked(True)
        self.addWidget(self.i1)
        self.addWidget(self.i2)
        self.addWidget(self.i3)

    def click_handler(self, item):
        if item.isChecked():
            self.changed.emit(item.text())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    ex = LogViewer()
    sys.exit(app.exec_())
