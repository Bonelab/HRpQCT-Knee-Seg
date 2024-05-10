'''Test command line interface setup'''

import unittest
import subprocess

from tests.config_cli import cfg


class TestCommandLineInterfeceSetup(unittest.TestCase):
    '''Test command line interface setup

    The help section of all expected command line tools are ran here
    to guarantee they were exported by setup.cfg using pbr
    '''

    def runner(self, entry_point):
        command = [entry_point, '-h']
        self.assertTrue(
            cfg['RUN_CALL'](command),
            'Could not run command \"{}\"'.format(' '.join(command))
        )

    def test_hrkMask2AIM(self):
        '''Can run `hrkMask2AIM`'''
        self.runner('hrkMask2AIM')


    def test_hrkMasks2AIMs(self):
        '''Can run `hrkMasks2AIMs`'''
        self.runner('hrkMasks2AIMs')


    def test_hrkParseLogs(self):
        '''Can run `hrkParseLogs`'''
        self.runner('hrkParseLogs')


    def test_hrkCombineROIMasks(self):
        '''Can run `hrkCombineROIMasks`'''
        self.runner('hrkCombineROIMasks')


    def test_hrkGenerateAffineAtlas(self):
        '''Can run `hrkGenerateAffineAtlas`'''
        self.runner('hrkGenerateAffineAtlas')


    def test_hrkInferenceEnsemble(self):
        '''Can run `hrkInferenceEnsemble`'''
        self.runner('hrkInferenceEnsemble')


    def test_hrkIntersectMasks(self):
        '''Can run `hrkIntersectMasks`'''
        self.runner('hrkIntersectMasks')


    def test_hrkPostProcessSegmentation(self):
        '''Can run `hrkPostProcessSegmentation`'''
        self.runner('hrkPostProcessSegmentation')


    def test_hrkMaskImage(self):
        '''Can run `hrkMaskImage`'''
        self.runner('hrkMaskImage')


    def test_hrkPreProcess2DSlices(self):
        '''Can run `hrkPreProcess2DSlices`'''
        self.runner('hrkPreProcess2DSlices')


    def test_hrkPreProcess2dot5DSliceStacks(self):
        '''Can run `hrkPreProcess2dot5DSliceStacks`'''
        self.runner('hrkPreProcess2dot5DSliceStacks')


    def test_hrkPreProcess3DPatches(self):
        '''Can run `hrkPreProcess3DPatches`'''
        self.runner('hrkPreProcess3DPatches')


    def test_hrkPreProcess3DPatchesFromNPZ(self):
        '''Can run `hrkPreProcess3DPatchesFromNPZ`'''
        self.runner('hrkPreProcess3DPatchesFromNPZ')


    def test_hrkTrainSeGAN_CV(self):
        '''Can run `hrkTrainSeGAN_CV`'''
        self.runner('hrkTrainSeGAN_CV')


    def test_hrkTrainSegResNetVAE_CV(self):
        '''Can run `hrkTrainSegResNetVAE_CV`'''
        self.runner('hrkTrainSegResNetVAE_CV')


    def test_hrkTrainUNet_CV(self):
        '''Can run `hrkTrainUNet_CV`'''
        self.runner('hrkTrainUNet_CV')


    def test_hrkTrainSeGAN_Final(self):
        '''Can run `hrkTrainSeGAN_Final`'''
        self.runner('hrkTrainSeGAN_Final')


    def test_hrkTrainSegResNetVAE_Final(self):
        '''Can run `hrkTrainSegResNetVAE_Final`'''
        self.runner('hrkTrainSegResNetVAE_Final')


    def test_hrkTrainUNet_Final(self):
        '''Can run `hrkTrainUNet_Final`'''
        self.runner('hrkTrainUNet_Final')


    def test_hrkTrainSeGAN_TransferCV(self):
        '''Can run `hrkTrainSeGAN_TransferCV`'''
        self.runner('hrkTrainSeGAN_TransferCV')


    def test_hrkTrainSegResNetVAE_TransferCV(self):
        '''Can run `hrkTrainSegResNetVAE_TransferCV`'''
        self.runner('hrkTrainSegResNetVAE_TransferCV')


    def test_hrkTrainUNet_TransferCV(self):
        '''Can run `hrkTrainUNet_TransferCV`'''
        self.runner('hrkTrainUNet_TransferCV')


    def test_hrkVisualize2DPanning(self):
        '''Can run `hrkVisualize2DPanning`'''
        self.runner('hrkVisualize2DPanning')

    def test_hrkGenerateROIs(self):
        '''Can run `hrkGenerateROIs`'''
        self.runner('hrkGenerateROIs')

    def test_hrkCrossSectional(self):
        '''Can run `hrkCrossSectional`'''
        self.runner('hrkCrossSectional')

    def test_hrkLongitudinal(self):
        '''Can run `hrkLongitudinal`'''
        self.runner('hrkLongitudinal')



if __name__ == '__main__':
    unittest.main()
