from __future__ import annotations

# external imports
from typing import List, Optional
from argparse import Namespace
import yaml
import os

# bonelab imports
from bonelab.util.echo_arguments import echo_arguments
from bonelab.util.time_stamp import message

# internal imports
from hrkneeseg.automation.parser import create_parser
from hrkneeseg.automation.write_slurm_script import write_slurm_script
from hrkneeseg.automation.common import (
    create_segmentation_slurm_files,
    create_atlas_registration_slurm_files
)


def create_shell_files() -> None:
    raise NotImplementedError


def create_slurm_files(
    automation_subdir: str,
    name: str,
    bone: str,
    side: str,
    postsurgery: bool,
    baseline: str,
    followups: List[str],
    working_dir: str,
    atlas_dir: str,
    conda_dir: str,
    conda_env: str,
    segmentation_models: List[dict],
    email: Optional[str] = None
) -> str:
    '''
    Create slurm scripts and shell batch submit script
    for a single image, and return a line that can be
    added to the shell batch submit script.

    Parameters
    ----------
    automation_subdir : str
        Path to the automation directory.

    name : str
        Name of the image series.

    bone : str
        Name of the bone.

    side : str
        Side of the body.

    postsurgery : bool
        Whether the image is post-surgical.

    baseline : str
        Name of the baseline image.

    followups : List[str]
        List of names of follow-up images.

    working_dir : str
        Path to the working directory.

    atlas_dir : str
        Path to the atlas directory.

    conda_dir : str
        Path to the conda directory.

    conda_env : str
        Name of the conda environment.

    segmentation_models : List[dict]
        List of dictionaries containing the following entries:
            - type : str
                Model type.
            - hyperparameters : str
                Path to a yaml containing hyperparameters for the model.
            - checkpoint : str
                Path to the model checkpoint.

    email : Optional[str], optional
        Email address to send notifications to.
        Defaults to `None`.

    Returns
    -------
    str
        Line that can be added to the shell batch submit script.
    '''
    slurm_dir = os.path.join(automation_subdir, name, "slurm")
    try:
        os.mkdir(slurm_dir)
    except FileExistsError:
        pass
    shell_submit_script_lines = ["#!/bin/bash"]

    all_images = [baseline] + followups
    seg_jid_vars = [f"JID_SEG_COMPLETE_{i}" for i in range(len(all_images))]
    atlas_jid_vars = [f"JID_ATLAS_COMPLETE_{i}" for i in range(len(all_images))]

    for t, (seg_jid_var, atlas_jid_var, image) in enumerate(zip(seg_jid_vars, atlas_jid_vars, all_images)):
        shell_submit_script_lines += create_segmentation_slurm_files(
            slurm_dir,
            postsurgery,
            image,
            working_dir,
            conda_dir,
            conda_env,
            segmentation_models,
            seg_jid_var,
            email,
            time_series_idx=t
        )
        shell_submit_script_lines += create_atlas_registration_slurm_files(
            slurm_dir,
            side,
            bone,
            postsurgery,
            image,
            working_dir,
            atlas_dir,
            conda_dir,
            conda_env,
            seg_jid_var,
            atlas_jid_var,
            email,
            time_series_idx=t
        )


    # finally, create a submit_all.sh script and return a line that
    # can be added to the shell batch submit script
    with open(os.path.join(automation_subdir, name, "submit_all.sh"), "w") as f:
        f.write("\n".join(shell_submit_script_lines))
    return f"./{os.path.join(automation_subdir, name, 'submit_all.sh')}"


def longitudinal(args: Namespace) -> None:
    params = vars(args)
    with open(args.yaml, "r") as file:
        config = yaml.safe_load(file)
    params = {**params, **config}
    print(echo_arguments("Longitudinal Automation", params))
    try:
        os.mkdir(args.automation_dir)
    except FileExistsError:
        pass
    try:
        os.mkdir(params["automation_dir"])
    except FileExistsError:
        pass
    with open(os.path.join(params["automation_dir"], "params.yaml"), "w") as f:
        yaml.dump(params, f)
    batch_submit_lines = ["#!/bin/bash"]
    for data in params["data"]:
        try:
            os.mkdir(os.path.join(
                params["automation_dir"],
                data["name"]
            ))
        except FileExistsError:
            pass
        if params["mode"] == "slurm":
            batch_submit_lines.append(
                create_slurm_files(
                    params["automation_dir"],
                    data["name"],
                    data["bone"],
                    data["side"],
                    data["postsurgery"],
                    data["baseline"],
                    data["followups"],
                    params["working_directory"],
                    params["atlas_directory"],
                    params["conda_directory"],
                    params["environment"],
                    params["segmentation_models"],
                    params["email"]
                )
            )
        elif params["mode"] == "shell":
            raise NotImplementedError("Shell mode not implemented yet.")
        else:
            raise ValueError(f"Invalid mode: {params['mode']}")
    with open(os.path.join(params["automation_dir"], "submit_all.sh"), "w") as f:
        f.write("\n".join(batch_submit_lines))


def main():
    args = create_parser("Longitudinal").parse_args()
    longitudinal(args)


if __name__ == '__main__':
    main()
