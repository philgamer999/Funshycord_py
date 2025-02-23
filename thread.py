import threading
import time

class WorkerThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.stop_event = threading.Event()

    def run(self):
        while not self.stop_event.is_set():
            print("Thread is running...")
            time.sleep(1)
        print("Thread is stopping...")

    def stop(self):
        self.stop_event.set()

# Start thread
worker = WorkerThread()
worker.start()

# Stop thread after 5 seconds
time.sleep(5)
worker.stop()
worker.join()  # Wait for the thread to finish
print("Thread has stopped.")
