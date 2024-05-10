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
from hrkneeseg.automation.common import create_segmentation_slurm_files


def create_shell_files() -> None:
    raise NotImplementedError


def create_slurm_files(
    automation_subdir: str,
    bone: str,
    side: str,
    postsurgery: bool,
    image: str,
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

    bone : str
        Name of the bone.

    side : str
        Side of the body.

    postsurgery : bool
        Whether the image is post-surgical.

    image : str
        Name of the image.

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
    slurm_dir = os.path.join(automation_subdir, image, "slurm")
    try:
        os.mkdir(slurm_dir)
    except FileExistsError:
        pass
    shell_submit_script_lines = ["#!/bin/bash"]

    shell_submit_script_lines += create_segmentation_slurm_files(
        slurm_dir,
        postsurgery,
        image,
        working_dir,
        conda_dir,
        conda_env,
        segmentation_models,
        "JID_PP",
        email
    )


    # finally, create a submit_all.sh script and return a line that
    # can be added to the shell batch submit script
    with open(os.path.join(automation_subdir, image, "submit_all.sh"), "w") as f:
        f.write("\n".join(shell_submit_script_lines))
    return f"./{os.path.join(automation_subdir, image, 'submit_all.sh')}"


def crossectional(args: Namespace) -> None:

    # we don't want people using this until it is
    # properly implemented and tested
    raise NotImplementedError

    params = vars(args)
    with open(args.yaml, "r") as file:
        config = yaml.safe_load(file)
    params = {**params, **config}
    print(echo_arguments("Cross-Sectional Automation", params))
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
                data["image"]
            ))
        except FileExistsError:
            pass
        if params["mode"] == "slurm":
            batch_submit_lines.append(
                create_slurm_files(
                    params["automation_dir"],
                    data["bone"],
                    data["side"],
                    data["postsurgery"],
                    data["image"],
                    params["working_directory"],
                    params["atlas_directory"],
                    params["conda_directory"],
                    params["environment"],
                    params["segmentation_models"],
                    params["email"],
                )
            )
        elif params["mode"] == "shell":
            raise NotImplementedError("Shell mode not implemented yet.")
        else:
            raise ValueError(f"Invalid mode: {params['mode']}")
    with open(os.path.join(params["automation_dir"], "submit_all.sh"), "w") as f:
        f.write("\n".join(batch_submit_lines))



def main():
    args = create_parser("Cross-sectional").parse_args()
    crossectional(args)


if __name__ == '__main__':
    main()
