"""Real public Gazebo #44528260284: localization /get_parameters responsive
0.026005s while /manage_nodes SHUTDOWN request timed out at 30.000372s.
In Nav2 Jazzy /is_active and /manage_nodes share the same MutuallyExclusive
callback group; /get_parameters does not. Probe that group read-only once.
Never replay SHUTDOWN or extend scan 300ms/CM120ms/Guard150ms.
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
    spec=importlib.util.spec_from_file_location("g07_loc_cb_probe",SRC)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

class ManagerCallbackGroupProbe(unittest.TestCase):
    def test_nav2_same_group_probe_is_read_only_and_ttl_unchanged(self):
        s=SRC.read_text()
        self.assertIn("def probe_localization_manage_callback_group(",s)
        self.assertIn('"/lifecycle_manager_localization/is_active"',s)
        self.assertIn("Trigger.Request()",s)
        self.assertIn('stages["localization_manage_group_probe"]=',s)
        self.assertIn('if key=="localization" and ack["status"]=="SERVICE_TIMEOUT":',s)
        self.assertIn('"BLOCKED_LIFECYCLE_"+key.upper()',s)
        self.assertEqual(s.count('command="shutdown"'),1)
        self.assertNotIn("retry_shutdown",s)
        self.assertNotIn("SCAN_TTL_SEC = 0.5",s)

    def test_readonly_same_group_response_is_not_shutdown_ack(self):
        m=load()
        class Trigger:
            class Request: pass
        std=types.ModuleType("std_srvs")
        srv=types.ModuleType("std_srvs.srv")
        srv.Trigger=Trigger
        keys=("std_srvs","std_srvs.srv")
        old={k:sys.modules.get(k) for k in keys}
        sys.modules["std_srvs"]=std;sys.modules["std_srvs.srv"]=srv
        class Future:
            def done(self):return True
            def result(self):return types.SimpleNamespace(success=True,message="")
        class Client:
            def __init__(self):self.calls=0
            def wait_for_service(self,timeout_sec):return True
            def call_async(self,req):
                assert isinstance(req,Trigger.Request)
                self.calls+=1
                return Future()
        class Node:
            def __init__(self):self.client=Client()
            def create_client(self,kind,name):
                assert kind is Trigger
                assert name=="/lifecycle_manager_localization/is_active"
                return self.client
            def destroy_client(self,client):self.client_destroyed=True
            def destroy_node(self):self.node_destroyed=True
        class Fake:
            def create_node(self,*args,**kwargs):
                self.node=Node()
                return self.node
            def spin_until_future_complete(self,node,fut,timeout_sec):
                assert 0<timeout_sec<=2.0
        fake=Fake()
        try:
            v=m.probe_localization_manage_callback_group(fake,timeout_sec=2.0)
        finally:
            for k,oldval in old.items():
                if oldval is None:sys.modules.pop(k,None)
                else:sys.modules[k]=oldval
        self.assertEqual(v["status"],"MANAGE_CALLBACK_GROUP_RESPONSIVE")
        self.assertTrue(v["request_sent"])
        self.assertTrue(v["is_active"])
        self.assertNotIn("shutdown_ack",v)
        self.assertEqual(fake.node.client.calls,1)
        self.assertTrue(fake.node.node_destroyed)

    def test_absent_callback_group_response_must_hold(self):
        m=load()
        class Trigger:
            class Request:pass
        std=types.ModuleType("std_srvs")
        srv=types.ModuleType("std_srvs.srv")
        srv.Trigger=Trigger
        keys=("std_srvs","std_srvs.srv")
        old={k:sys.modules.get(k) for k in keys}
        sys.modules["std_srvs"]=std;sys.modules["std_srvs.srv"]=srv
        class Future:
            def done(self):return False
        class Client:
            def wait_for_service(self,timeout_sec):return True
            def call_async(self,request):return Future()
        class Node:
            def create_client(self,kind,name):return Client()
            def destroy_client(self,c):pass
            def destroy_node(self):pass
        class Fake:
            def create_node(self,*a,**k):return Node()
            def spin_until_future_complete(self,*a,**k):pass
        try:
            v=m.probe_localization_manage_callback_group(Fake(),timeout_sec=2)
        finally:
            for k,oldval in old.items():
                if oldval is None:sys.modules.pop(k,None)
                else:sys.modules[k]=oldval
        self.assertEqual(v["status"],"MANAGE_CALLBACK_GROUP_NO_ACK")
        self.assertFalse(v.get("shutdown_ack",False))

if __name__=="__main__":unittest.main()
