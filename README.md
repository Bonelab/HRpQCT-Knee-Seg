# HRpQCT-Knee-Seg

This repo contains an installable package for doing automated HR-pQCT knee segmentation. You can use it to do inference with an existing model, or to train a new model on your own data. The package is built on top of the [bonelab](https://github.com/Bonelab/Bonelab) and [bonelab-pytorch-lightning](https://github.com/Bonelab/bonelab-pytorch-lightning) packages.

---

## Installation

1. Go to https://github.com/Bonelab/bonelab-pytorch-lightning and follow the instructions to install the `bonelab` and `bonelab-pytorch-lightning` packages
2. Clone this repository and install it. You can do this by running the following commands:

```bash

cd ~/Projects # or wherever you keep your repositories
git clone git@github.com:Bonelab/HRpQCT-Knee-Seg.git
cd HRpQCT-Knee-Seg
pip install -e .

```

NOTE 1: The `-e` flag is for "editable" mode. This means that if you make changes to the code in this repository, you don't have to reinstall the package. The changes will be reflected in the package immediately.

NOTE 2: The above install command will use the `requirements.txt` file and will
install the default versions of all of the dependencies. There are two special cases with special requirements file:

`requirements_arc_c11.1.txt` is for using the NVIDIA A100 GPU nodes on the ARC cluster at the University of Calgary, and also on `Groot`. You can install the package with this requirements file by running:

```bash
pip install -r requirements_arc_c11.1.txt -e .
```

`requirements_thegnu_c10.2.txt` is for using the NVIDIA Quadro P6000 GPUs on the `TheGNU` remote server in the lab. You can install the package with this requirements file by running:

```bash
pip install -r requirements_thegnu_c10.2.txt -e .
```

If you have other package version requirements, feel free to make your own
requirements file and install the package with that. However please note that
it's import that `bonelab-pytorch-lightning` and this package be installed
with a consistent requirements file.

---

## Command Line Apps

This is a list of all of the command-line apps that get installed when you install this package. For more specific usage instructions, run a command with the `-h` flag.

| Command                         | Description                                                                                                                                                              |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| hrkAIMs2NIIs                    | Convert an AIM and optionally, its associated masks, to NIIs                                                                                                             |
| hrkMask2AIM                     | Convert a mask to AIM, requires a base AIM that the mask will be lined up on.                                                                                            |
| hrkMasks2AIMs                   | Convert multiple masks to AIMs, requires a base AIM that the masks will be lined up on.                                                                                  |
| hrkParseLogs                    | Parse/collate the logs from a set of pytorch lightning model training runs.                                                                                              |
| hrkCombineROIMasks              | Combine multiple ROI masks into a single compartmental mask.                                                                                                             |
| hrkGenerateAffineAtlas          | Use a set of images and masks to construct an average atlas with affine registration.                                                                                    |
| hrkInferenceEnsemble            | Perform inference on an image uby ensembling multiple segmentation models.                                                                                               |
| hrkIntersectMasks               | Compute the intersection of two binary masks.                                                                                                                            |
| hrkPostProcessSegmentation      | Use morphological filtering operations to post-process a predicted bone compartment segmentation - designed for knee HR-pQCT images specifically.                        |
| hrkMaskImage                    | Given an image and a mask, will dilate the mask by some amount and then set the image voxels to zero outside of the dilated mask.                                        |
| hrkPreProcess2DSlices           | Preprocess a directory of AIMs to generate 2D slice patch samples to minimize file IO and processing time when training a segmentation model.                            |
| hrkPreProcess2dot5DSliceStacks  | Preprocess a directory of AIMs to generate 2.5D stacked slice patch samples to minimize file IO and processing time when training a segmentation model.                  |
| hrkPreProcess3DPatches          | Preprocess a directory of AIMs to generate 3D patch samples to minimize file IO and processing time when training a segmentation model.                                  |
| hrkPreProcess3DPatchesFromNPZ   | Preprocess a directory of AIMs that have been converted to NPZs to generate 3D patch samples to minimize file IO and processing time when training a segmentation model. |
| hrkTrainSeGAN_CV                | Train a SeGAN segmentation model usinf cross-validation.                                                                                                                 |
| hrkTrainSegResNetVAE_CV         | Train a SegResNetVAE using cross-validation.                                                                                                                             |
| hrkTrainUNet_CV                 | Train a UNet (or variant) using cross-validation.                                                                                                                        |
| hrkTrainSeGAN_Final             | Train a single SeGAN using 100% of the provided data as training data.                                                                                                   |
| hrkTrainSegResNetVAE_Final      | Train a single SegResNetVAE using 100% of the provided data as training data.                                                                                            |
| hrkTrainUNet_Final              | Train a single UNet (or variant) using 100% of the provided data as training data.                                                                                       |
| hrkTrainSeGAN_TransferCV        | Train a SeGAN using cross-validation, starting from a SeGAN that has been trained on another dataset.                                                                    |
| hrkTrainSegResNetVAE_TransferCV | Train a SegResNetVAE using cross-validation, starting from a SeGAN that has been trained on another dataset.                                                             |
| hrkTrainUNet_TransferCV         | Train a UNet (or variant) using cross-validation, starting from a SeGAN that has been trained on another dataset.                                                        |
| hrkVisualize2DPanning           | Reads in an image and masks and generates a 2D video or GIF that pans through the image, for qualitative data checking, motion scoring, etc.                             |
| hrkGenerateROIs                 | Generate peri-articular ROIs from a bone compartment segmentation and a atlas-based compartmental segmentation.                                                          |

---

## Segmenting Knee Images

Regardless of the study design, the first steps are to move your data from the `DATA` disk to the `PROJECTS` disk on the VMS system, and then transfer your data to ARC. This package does not provide scripts for automating any of that.

### Cross-sectional Data

Your data directory must be organized in the following way:

```bash
<STUDY NAME>
├── aims
├── atlas_registrations
├── model_masks
├── niftis
├── roi_masks
└── visualizations
```

In a cross-sectional study design, we will process all images independently from each other. So the steps listed below are to be applied to each image.

Steps:

1. Put the AIMs in the `aims` directory.
2. Convert the AIMs to NIfTI format using the `hrkAIMs2NIIs` command, and put the outputs in the `niftis` directory.
3. Perform inference on the images using the `hrkInferenceEnsemble` command, and put the outputs in the `model_masks` directory.
4. Post-process the segmentations using the `hrkPostProcessSegmentation` command, and put the outputs in the `model_masks` directory.
5. Convert the post-processed masks to AIMs using the `hrkMasks2AIMs` command, and put the outputs in the `roi_masks` directory.
6. If the image is from a LEFT knee, then mirror the NII using the `blImageMirror` command, and put the output in the `niftis` directory.
7. Register the (if LEFT, mirrored) image to the atlas using the `blRegistrationDemons` command, and put the output in the `atlas_registrations` directory.
8. Transform the atlas masks to the image using the `blRegistrationApplyTransform` command and put the output in the `atlas_registrations` directory.
9. If the image is from a LEFT knee, then mirror the transformed atlas masks using the `blImageMirror` command, and put the output in the `atlas_registrations` directory.
10. Generate the ROI masks using the `hrkGenerateROIs` command, and put the output in the `roi_masks` directory.
11. Convert the peri-articular ROI masks to AIMs using the `hrkMasks2AIMs` command, and put the outputs in the `roi_masks` directory.
12. Visualize the segmentations using the `hrkVisualize2DPanning` command, and put the outputs in the `visualizations` directory.
13. Visually check the visualization outputs to make sure the ROI masks are OK - you may need to go back and recrop your AIMs, or you may need to do some corrections to the bone compartment segmentations and rerun parts of the workflow. You can also use these visualizations for doing motion scoring.
14. Transfer all `*.AIM` files from `roi_masks` back to the VMS system, and do your analysis.
15. Clean up after yourself by deleting everything that is not an `*.AIM` file.

### Longitudinal Data

Your data directory must be organized in the following way:

```bash
<STUDY NAME>
├── aims
├── atlas_registrations
├── model_masks
├── niftis
├── registrations
├── roi_masks
└── visualizations
```

In a longitudinal study design, we will process images as time series. The steps below are to be applied to each set of images that are the same subject, the same side, the same bone, etc. at each time point.

Steps:

1. Put the AIMs in the `aims` directory.
2. Convert the AIMs to NIfTI format using the `hrkAIMs2NIIs` command, and put the outputs in the `niftis` directory.
3. Perform inference on the images using the `hrkInferenceEnsemble` command, and put the outputs in the `model_masks` directory.
4. Post-process the segmentations using the `hrkPostProcessSegmentation` command, and put the outputs in the `model_masks` directory.
5. Convert the post-processed masks to AIMs using the `hrkMasks2AIMs` command, and put the outputs in the `roi_masks` directory.
6. If the images are from a LEFT knee, then mirror the NIIs using the `blImageMirror` command, and put the outputs in the `niftis` directory.
7. Register the (if LEFT, mirrored) images to the atlas using the `blRegistrationDemons` command, and put the output in the `atlas_registrations` directory.
8. Transform the atlas masks to the images using the `blRegistrationApplyTransform` command and put the outputs in the `atlas_registrations` directory.
9. If the images are from a LEFT knee, then mirror the transformed atlas masks using the `blImageMirror` command, and put the outputs in the `atlas_registrations` directory.
10. Use the respective post-processed bone compartment masks to mask the images using the `hrkMaskImages` command, and put the outputs in the `niftis` directory.
11. Perform a longitudinal registration with the masked images using the `blRegistrationLongitudinal` command, and put the outputs in the `registrations` directory.
12. Delete the masked images.
13. Transform all follow-up bone compartment segmentations and atlas-based compartmental segmentations to the baseline image using the `blRegistrationApplyTransform` command, and put the outputs in the `registrations` directory.
14. Find the intersection of all atlas-based compartmental segmentations in the baseline frame using the `hrkIntersectMasks` command and put the output in the `registrations` directory.
15. Generate the peri-articular ROI masks in the baseline reference frame using the intersected atlas masks and the bone compartment segmentations that have been transformed to the baseline reference frame, using the `hrkGenerateROIs` command, and put the output in the `roi_masks` directory.
16. Transform the follow-up peri-articular ROI masks from the baseline frame to their respective follow-up frames using the `blRegistrationApplyTransform` command, and put the outputs in the `roi_masks` directory.
17. Convert the peri-articular ROI masks to AIMs using the `hrkMasks2AIMs` command, and put the outputs in the `roi_masks` directory.
18. Visualize the segmentations using the `hrkVisualize2DPanning` command, and put the outputs in the `visualizations` directory.
19. Visually check the visualization outputs to make sure the ROI masks are OK - you may need to go back and recrop your AIMs, or you may need to do some corrections to the bone compartment segmentations and rerun parts of the workflow. You can also use these visualizations for doing motion scoring.
20. Transfer all `*.AIM` files from `roi_masks` back to the VMS system, and do your analysis.
21. Clean up after yourself by deleting everything that is not an `*.AIM` file.

### Miscellaneous

The steps don't need to be done in the exact order presented above. For example, you can do the bone compartment segmentation steps at the same time as you register the image to the atlas and get the compartmental masks (and also do the longitudinal registrations in parallel). Also, only model inference will use a GPU, so every other step should be executed on a cluster node or machine where you are not blocking someone else's access to a GPU. Many of the CPU-intensive steps are slow, so it's not recommended to just run the whole workflow all the way through on a GPU node on ARC, or a GPU machine such as `TheGNU` or `Groot`.

---

## TODO:

1. Add a command line utility for each step in the pipeline (DONE)
2. Add a command line utility that you can run in a different directory that
   will create all of the shell and slurm files required for either
   cross-sectional or longitudinal processing of HR-pQCT knee images
3. Improve the documentation in this repo to properly explain how to use the
   utilities and how everything works (DONE)
4. Add tests and github actions CI/CD
5. Long term goal - perhaps add command line utilities that link up to the
   preprocessing and training scripts so that someone could retrain the models
   if they had more data and wanted to - or so you could use this to
   train models on entirely different datasets.. the approach here isn't necessarily specific to just knees
6. Might be nice to have sphinx auto-documentation, but that's post-thesis stuff
