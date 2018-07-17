#!/usr/bin/env python
import os
import sys
import cdat_info

class DV3DTestRunner(cdat_info.TestRunnerBase):
    def _prep_nose_options(self):
        opt = super(DV3DTestRunner, self)._prep_nose_options()
        if self.args.vtk is not None:
            vtk_name = "vtk-cdat"
            cdat_info.run_command(
                "conda install -f -y -c {} vtk-cdat".format(self.args.vtk),
                True, False, True)
        return opt


test_suite_name = 'dv3d'

workdir = os.getcwd()
runner = DV3DTestRunner(test_suite_name, options=["--vtk"], 
                        options_files=[
                       "tests/dv3d_runtests.json"], 
                        get_sample_data=True, 
                        test_data_files_info="Share/test_data_files.txt")
ret_code = runner.run(workdir)

sys.exit(ret_code)

