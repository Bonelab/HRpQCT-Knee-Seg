# HRpQCT-Knee-Seg

This repo contains an installable package for doing automated HR-pQCT knee segmentation. You can use it to do inference with an existing model, or to train a new model on your own data. The package is built on top of the [bonelab](https://github.com/Bonelab/Bonelab) and [bonelab-pytorch-lightning](https://github.com/Bonelab/bonelab-pytorch-lightning) packages.

## Installation

1. Go to https://github.com/Bonelab/bonelab-pytorch-lightning and follow the instructions to install the bonelab and bonelab-pytorch-lightning packages
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

`requirements_arc_c11.1.txt` is for using the NVIDIA A100 GPUs on the ARC cluster at the University of Calgary. You can install the package with this requirements file by running:

```bash
pip install -e . -r requirements_arc_c11.1.txt
```

`requirements_thegnu_c10.2.txt` is for using the NVIDIA Quadro P6000 GPUs on the `TheGNU` remote server in the lab. You can install the package with this requirements file by running:

```bash
pip install -e . -r requirements_thegnu_c10.2.txt
```

If you have other package version requirements, feel free to make your own
requirements file and install the package with that. However please note that
it's import that `bonelab-pytorch-lightning` and this package be installed
with a consistent requirements file.

## TODO:

1. Add a command line utility for each step in the pipeline (DONE)
2. Add a command line utility that you can run in a different directory that
   will create all of the shell and slurm files required for either
   cross-sectional or longitudinal processing of HR-pQCT knee images
3. Improve the documentation in this repo to properly explain how to use the
   utilities and how everything works
4. Add tests and github actions CI/CD
5. Long term goal - perhaps add command line utilities that link up to the
   preprocessing and training scripts so that someone could retrain the models
   if they had more data and wanted to - or so you could use this to
   train models on entirely different datasets.. the approach here isn't necessarily specific to just knees
6. Might be nice to have sphinx auto-documentation, but that's post-thesis stuff
