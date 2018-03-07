import basedv3d


class DV3DHov(basedv3d.DV3DTest):
    def testIt(self):
        self.runTest("Hovmoller_volume_test")
