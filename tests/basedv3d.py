from __future__ import unicode_literals
import unittest
import subprocess
from cdat_info import checkImage
import shlex
import os

class DV3DTest(unittest.TestCase):
    def runTest(self, name):
        if "COVERAGE_PROCESS_START" in os.environ:
            runner = "coverage run -a"
        else:
            runner = "python"
        cmd = "{} tests/dv3d_execute_test.py {} False uvcdat-testdata/baselines/dv3d".format(runner, name)
        print("COMMMAND:",cmd)
        p = subprocess.Popen(shlex.split(cmd),stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        o,e = p.communicate()

        print("ERRORS:",e.decode("utf-8"))
        print("OUTPUT:",o.decode("utf-8"))
        sp = o.split()
        for i,s in enumerate(sp[:-2]):
            try:
                s = s.decode("utf-8")
            except:
                pass
            #print("S IS:",s)
            if s == "IMG:": 
                img = sp[i+1]
                ref = sp[i+2]
        try:
            img = img.decode("utf-8")
            ref = ref.decode("utf-8")
        except:
            pass
        # print("IMGS:",img, ref)
        ret = checkImage(img, None, "", "", ref, pngReady=True, pngPathSet=True)
        self.assertEqual(ret+p.returncode,0)
