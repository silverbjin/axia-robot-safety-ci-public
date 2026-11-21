"""C07 L2 #44540963499 Navigation manage shutdown request 40.000932s
with no Nav2 server shutdown transition before SIGINT, CM -11 and Guard1.
Probe the same mutually exclusive manager callback group read-only after
the ONE missing SHUTDOWN ack; capture RMW implementation. No retry/TTL change.
"""
import importlib.util
from pathlib import Path
import sys
import types
import unittest

ROOT=Path(__file__).resolve().parents[2]
STUDENT=ROOT/"student" if (ROOT/"student").is_dir() else ROOT.parent/"student"
TOOLS=STUDENT/"block_B/day07/h01_runtime/tools"
SRC=TOOLS/"p2_g07_ordered_shutdown.py"

def load():
    sys.path.insert(0,str(TOOLS))
    spec=importlib.util.spec_from_file_location("c07_nav_manage",SRC)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

class NavManagerAfterTimeout(unittest.TestCase):
    def test_c06_first_lifecycle_failure_does_not_become_clean_teardown(self):
        first={"status":"BLOCKED_LIFECYCLE_NAVIGATION_SERVICE_TIMEOUT",
               "navigation_service_request_sent":True,
               "navigation_response_elapsed_sec":40.000932,
               "navigation_ack":False,"localization_ack":False}
        self.assertFalse(first["navigation_ack"])
        self.assertFalse(first["localization_ack"])
        self.assertEqual(first["status"],"BLOCKED_LIFECYCLE_NAVIGATION_SERVICE_TIMEOUT")

    def test_same_callback_group_probe_is_read_only_with_single_request(self):
        m=load()
        class Trigger:
            class Request: pass
        old={k:sys.modules.get(k) for k in ("std_srvs","std_srvs.srv")}
        std=types.ModuleType("std_srvs")
        srv=types.ModuleType("std_srvs.srv")
        srv.Trigger=Trigger
        sys.modules["std_srvs"]=std
        sys.modules["std_srvs.srv"]=srv
        class Future:
            def done(self):return True
            def result(self):return types.SimpleNamespace(success=True)
        class Client:
            def __init__(self):self.calls=0
            def wait_for_service(self,timeout_sec):
                assert timeout_sec<=.5
                return True
            def call_async(self,request):
                assert isinstance(request,Trigger.Request)
                self.calls+=1
                return Future()
        class Node:
            def __init__(self):self.client=Client()
            def create_client(self,kind,name):
                assert name=="/lifecycle_manager_navigation/is_active"
                assert kind is Trigger
                return self.client
            def destroy_client(self,client):self.destroyed_client=True
            def destroy_node(self):self.destroyed=True
        class FakeRclpy:
            def create_node(self,*args,**kwargs):
                self.node=Node()
                return self.node
            def spin_until_future_complete(self,node,future,timeout_sec):
                assert 0<timeout_sec<=2.0
        fake=FakeRclpy()
        try:
            answer=m.probe_navigation_manage_callback_group(fake,timeout_sec=2.0)
        finally:
            for k,v in old.items():
                if v is None:sys.modules.pop(k,None)
                else:sys.modules[k]=v
        self.assertEqual(answer["status"],"MANAGE_CALLBACK_GROUP_RESPONSIVE")
        self.assertEqual(answer["is_active"],True)
        self.assertTrue(answer["request_sent"])
        self.assertNotIn("shutdown_ack",answer)
        self.assertEqual(fake.node.client.calls,1)

    def test_bounded_navigation_probe_without_reissuing_shutdown(self):
        src=SRC.read_text()
        self.assertIn("def probe_navigation_manage_callback_group(",src)
        self.assertIn('"/lifecycle_manager_navigation/is_active"',src)
        self.assertIn('stages["navigation_manage_group_probe"]=',src)
        self.assertIn('stages["rmw_implementation_identifier"]=',src)
        self.assertIn('if key=="navigation" and ack["status"]=="SERVICE_TIMEOUT":',src)
        self.assertEqual(src.count('command="shutdown"'),1)
        self.assertNotIn("retry_shutdown",src)
        self.assertIn("deadline = monotonic() + limit",src)
        self.assertIn('"BLOCKED_LIFECYCLE_"+key.upper()',src)

if __name__=="__main__":unittest.main()
