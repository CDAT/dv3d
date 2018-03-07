from __future__ import unicode_literals
import unittest
import subprocess
import checkimage
import shlex

class DV3DTest(unittest.TestCase):
    def runTest(self, name):
        cmd = "python tests/dv3d_execute_test.py {} False uvcdat-testdata/baselines/dv3d".format(name)
        p = subprocess.Popen(shlex.split(cmd),stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        o,e = p.communicate()

        print("ERRORS:",e)
        print("OUTPUT:",o)
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
        print("IMGS:",img, ref)
        ret = checkimage.check_result_image(img, ref)
        self.assertEqual(ret+p.returncode,0)
