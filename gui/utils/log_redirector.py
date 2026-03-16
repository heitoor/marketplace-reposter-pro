"""
Redirecionador de stdout para a fila de mensagens da GUI.
Captura print() do worker thread e envia para o log da interface.
"""

import threading
import queue


class ThreadAwareQueueWriter:
    """
    File-like object que intercepta writes do worker thread
    e os envia para uma queue. Writes de outras threads passam
    direto para o stream original.
    """

    def __init__(self, message_queue: queue.Queue, original_stream, worker_thread_id: int):
        self.queue = message_queue
        self.original = original_stream
        self.worker_thread_id = worker_thread_id

    def write(self, text: str):
        if threading.current_thread().ident == self.worker_thread_id:
            if text and text.strip():
                self.queue.put({"type": "log", "text": text.rstrip()})
        if self.original:
            self.original.write(text)

    def flush(self):
        if self.original:
            self.original.flush()

    def fileno(self):
        if self.original:
            return self.original.fileno()
        raise OSError("No fileno available")
