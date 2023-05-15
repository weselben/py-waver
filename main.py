from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLineEdit, QLabel
from PyQt5.QtGui import QColor
import sys
import threading
import datetime
import ggwave
import pyaudio

# Configuration
PROTOCOL_ID = 5  # The ID for the ultrasound protocol
VOLUME = 100  # The volume of the output sound

class SoundCommunication:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.lock = threading.Lock()
        self.last_sent_message = None
        self.last_sent_time = None

    def send(self, message):
        with self.lock:
            # generate audio waveform for string message
            waveform = ggwave.encode(message, protocolId=PROTOCOL_ID, volume=VOLUME)
            stream = self.p.open(format=pyaudio.paFloat32, channels=1, rate=48000, output=True, frames_per_buffer=4096)
            stream.write(waveform, len(waveform) // 4)
            stream.stop_stream()
            stream.close()
            self.last_sent_message = message
            self.last_sent_time = datetime.datetime.now()

    def receive(self, textArea):
        stream = self.p.open(format=pyaudio.paFloat32, channels=1, rate=48000, input=True, frames_per_buffer=1024)
        instance = ggwave.init()

        try:
            while True:
                with self.lock:
                    data = stream.read(1024, exception_on_overflow=False)
                    res = ggwave.decode(instance, data)
                    if (not res is None):
                        try:
                            received_text = res.decode("utf-8")
                            if (received_text == self.last_sent_message and
                                (datetime.datetime.now() - self.last_sent_time).total_seconds() < 1):
                                continue
                            textArea.append(f"{datetime.datetime.now()} | Received text: {received_text}")
                        except Exception as e:
                            textArea.setTextColor(QColor(255, 165, 0))  # Set text color to orange
                            textArea.append(f"{datetime.datetime.now()} | Error: {str(e)}")
                            textArea.setTextColor(QColor(0, 0, 0))  # Reset text color to black
        except KeyboardInterrupt:
            pass

        ggwave.free(instance)
        stream.stop_stream()
        stream.close()

class MyApp(QWidget):
    def __init__(self, soundComm):
        super().__init__()

        self.soundComm = soundComm

        self.initUI()

    def initUI(self):
        vbox = QVBoxLayout()

        self.textArea = QTextEdit()
        self.textArea.setReadOnly(True)
        vbox.addWidget(self.textArea)

        self.inputLine = QLineEdit()
        self.inputLine.returnPressed.connect(self.send_message)  # Connect the returnPressed signal to the send_message function
        vbox.addWidget(self.inputLine)

        self.sendButton = QPushButton("Send")
        self.sendButton.clicked.connect(self.send_message)
        vbox.addWidget(self.sendButton)

        self.setLayout(vbox)

        self.setWindowTitle('Sound Communication')
        self.setGeometry(300, 300, 300, 200)
        self.show()

    def send_message(self):
        message = self.inputLine.text()
        threading.Thread(target=self.soundComm.send, args=(message,), daemon=True).start()  # Run the send method in a separate thread
        self.textArea.append(f"{datetime.datetime.now()} | Sent text: {message}")
        self.inputLine.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    soundComm = SoundCommunication()
    ex = MyApp(soundComm)

    threading.Thread(target=soundComm.receive, args=(ex.textArea,), daemon=True).start()

    sys.exit(app.exec_())