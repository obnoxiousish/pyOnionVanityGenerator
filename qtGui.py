import contextlib
import sys
import multiprocessing
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton, QSpinBox, QLineEdit, QHBoxLayout
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from main import generate_infinite_keys, Ed25519KeyGen  # Assuming your script is named main.py
import json
from time import sleep

class OnionGenThread(QThread):
    counter_updated = pyqtSignal(int)

    def __init__(self, num_threads, target_string):
        super().__init__()
        self.num_threads = num_threads
        self.target_string = target_string
        self.stopped = False

    def run(self):
        global_counter = multiprocessing.Value('i', 0)
        cpu_count = self.num_threads

        processes = []
        for i in range(cpu_count):
            process = multiprocessing.Process(target=generate_infinite_keys, args=(global_counter, i, self.target_string))
            process.start()
            processes.append(process)

        while not self.stopped:
            self.counter_updated.emit(global_counter.value)
            sleep(0.1)

        for p in processes:
            p.terminate()

    def stop(self):
        self.stopped = True

class OnionGenApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.load_config()
        self.gen_thread = None  # Store the reference to the generation thread

    def initUI(self):
        self.setWindowTitle('Onion Vanity Generator')
        self.setGeometry(100, 100, 300, 200)

        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor(30, 30, 30))
        self.setPalette(p)

        layout = QVBoxLayout()

        self.label = QLabel("Total keys generated: 0")
        self.label.setStyleSheet("color: lightgray")
        layout.addWidget(self.label)

        self.thread_picker = QSpinBox()
        self.thread_picker.setRange(1, 9999)  # Or whatever max you want
        self.thread_picker.setValue(4)
        self.thread_picker.setStyleSheet("color: lightgray; background-color: black")
        layout.addWidget(self.thread_picker)

        self.target_string = QLineEdit()
        self.target_string.setPlaceholderText("String to match")
        self.target_string.setStyleSheet("color: lightgray; background-color: black")
        layout.addWidget(self.target_string)

        self.start_button = QPushButton("Start Generating")
        self.start_button.setStyleSheet("color: lightgray; background-color: black")
        self.start_button.clicked.connect(self.start_generating)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setStyleSheet("color: lightgray; background-color: black")
        self.stop_button.clicked.connect(self.stop_generating)
        layout.addWidget(self.stop_button)

        self.load_button = QPushButton("Load Config")
        self.load_button.setStyleSheet("color: lightgray; background-color: black")
        self.load_button.clicked.connect(self.load_config)
        layout.addWidget(self.load_button)

        self.save_button = QPushButton("Save Config")
        self.save_button.setStyleSheet("color: lightgray; background-color: black")
        self.save_button.clicked.connect(self.save_config)
        layout.addWidget(self.save_button)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.show()

    def load_config(self):
        with contextlib.suppress(FileNotFoundError):
            with open('config.json', 'r') as config_file:
                config_data = json.load(config_file)
                if 'matchString' in config_data:
                    self.target_string.setText(config_data['matchString'])
                if 'threadCount' in config_data:
                    self.thread_picker.setValue(config_data['threadCount'])

    def save_config(self):
        config_data = {
            'matchString': self.target_string.text(),
            'threadCount': self.thread_picker.value(),
        }
        with open('config.json', 'w') as config_file:
            json.dump(config_data, config_file, indent=4)

    def start_generating(self):
        num_threads = self.thread_picker.value()
        target_string = self.target_string.text()
        
        # Check if the generation thread is already running and stop it
        if self.gen_thread and self.gen_thread.isRunning():
            self.stop_generating()
        
        self.gen_thread = OnionGenThread(num_threads, target_string)
        self.gen_thread.counter_updated.connect(self.update_counter)
        self.gen_thread.start()

    def stop_generating(self):
        if self.gen_thread and self.gen_thread.isRunning():
            self.gen_thread.stop()

    def update_counter(self, counter):
        self.label.setText(f"Total keys generated: {counter}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = OnionGenApp()
    sys.exit(app.exec())
