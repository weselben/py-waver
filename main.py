import asyncio
import ggwave
import pyaudio
import threading
import datetime

# Configuration
PROTOCOL_ID = 4  # The ID for the ultrasound protocol
VOLUME = 100  # The volume of the output sound

class SoundCommunication:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.lock = threading.Lock()

    def send(self, message):
        with self.lock:
            # generate audio waveform for string message
            waveform = ggwave.encode(message, protocolId=PROTOCOL_ID, volume=VOLUME)

            print(f"Transmitting text '{message}' ...")
            stream = self.p.open(format=pyaudio.paFloat32, channels=1, rate=48000, output=True, frames_per_buffer=4096)
            stream.write(waveform, len(waveform) // 4)
            stream.stop_stream()
            stream.close()

    def receive(self):
        stream = self.p.open(format=pyaudio.paFloat32, channels=1, rate=48000, input=True, frames_per_buffer=1024)

        print('Listening ...')
        instance = ggwave.init()

        try:
            while True:
                with self.lock:
                    data = stream.read(1024, exception_on_overflow=False)
                    res = ggwave.decode(instance, data)
                    if (not res is None):
                        try:
                            received_text = res.decode("utf-8")
                            self.print_message(received_text)
                        except:
                            pass
        except KeyboardInterrupt:
            pass

        ggwave.free(instance)

        stream.stop_stream()
        stream.close()

    @staticmethod
    def print_message(message):
        print(f"{datetime.datetime.now()} | Received text: {message}")


if __name__ == "__main__":
    comms = SoundCommunication()

    # Start the receiver in a separate thread
    threading.Thread(target=comms.receive, daemon=True).start()

    # CLI for the sender
    while True:
        message = input("Enter a message to send: ")
        comms.send(message)
