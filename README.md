# HRpQCT-Knee-Seg

this repo contains an installable package for doing automated HR-pQCT knee segmentation

The vision of this repository is that we have command line utilities for all of
the steps in the HR-pQCT knee segmentation pipeline. Then there is no more
"projects" folder in a monorepo that explodes in complexity. Instead, you
install this package and then in a separate project repo you put the slurm
and shell scripts for processing your data in the way you need to, which
will depend on the specific study.

TODO:

1. Add a command line utility for each step in the pipeline
2. Add a command line utility that you can run in a different directory that
   will create all of the shell and slurm files required for either
   cross-sectional or longitudinal processing of HR-pQCT knee images
3. Improve the documentation in this repo to properly explain how to use the
   utilities and how everything works
4. Long term goal - perhaps add command line utilities that link up to the
   preprocessing and training scripts so that someone could retrain the models
   if they had more data and wanted to - or so you could use this to
   train models
   on entirely different datasets.. the approach here isn't necessarily specific
   to just knees
