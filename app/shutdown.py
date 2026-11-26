"""Bounded cooperative shutdown for workers owned by the current JARVIS app."""
import os,threading,time

class Shutdown:
    def __init__(self):
        self.workers=[];self.closing=False
    def start(self,target,args=()):
        if self.closing:return None
        self.workers=[t for t in self.workers if t.is_alive()]
        worker=threading.Thread(target=target,args=args,daemon=True)
        self.workers.append(worker);worker.start();return worker
    def begin(self,stop_events,extra_threads=(),*,exit_code=None,deadline=5):
        if self.closing:return
        self.closing=True
        for event in stop_events:event.set()
        self.workers.extend(extra_threads)
        if exit_code is not None:
            # Only the executable entry point arms this last-resort self-exit.
            # Never kill by name/PID or touch an external service.
            def watchdog():
                time.sleep(deadline)
                os._exit(exit_code)
            threading.Thread(target=watchdog,daemon=True,name='jarvis-close-watchdog').start()
    def wait(self,seconds=2):
        end=time.monotonic()+seconds
        for worker in self.workers:
            if worker is not threading.current_thread() and worker.is_alive():
                worker.join(max(0,end-time.monotonic()))
        return not any(t.is_alive() for t in self.workers)
