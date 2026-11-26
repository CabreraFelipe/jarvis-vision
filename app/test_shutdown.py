import os,sys,threading,time,subprocess,unittest
from pathlib import Path
from shutdown import Shutdown

class ShutdownTests(unittest.TestCase):
    def test_cooperative_release(self):
        stop=threading.Event();released=threading.Event();s=Shutdown()
        def worker():
            stop.wait(3);released.set()
        s.start(worker);s.begin([stop])
        self.assertTrue(s.wait(1));self.assertTrue(released.is_set())
        self.assertIsNone(s.start(lambda:None))
    def test_extra_capture_worker(self):
        stop=threading.Event();worker=threading.Thread(target=stop.wait,daemon=True);worker.start()
        s=Shutdown();s.begin([stop],[worker]);self.assertTrue(s.wait(1))
    def test_blocked_worker_bounded(self):
        release=threading.Event();s=Shutdown();s.start(release.wait)
        try:
            s.begin([]);start=time.monotonic();self.assertFalse(s.wait(.03))
            self.assertLess(time.monotonic()-start,1)
        finally:release.set();s.wait(1)
    def test_close_idempotent(self):
        s=Shutdown();a=threading.Event();b=threading.Event();s.begin([a]);s.begin([b])
        self.assertTrue(a.is_set());self.assertFalse(b.is_set())
    def test_watchdog_exits_only_own_process_with_update_code(self):
        code="import threading,time;from shutdown import Shutdown;s=Shutdown();s.start(threading.Event().wait);s.begin([],exit_code=42,deadline=.15);time.sleep(30)"
        proc=subprocess.run([sys.executable,'-c',code],cwd=Path(__file__).parent,timeout=5)
        self.assertEqual(proc.returncode,42)
if __name__=='__main__':unittest.main()
