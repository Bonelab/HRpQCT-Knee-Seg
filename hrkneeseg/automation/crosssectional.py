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
    ROI_CODES, create_segmentation_slurm_files,
    create_atlas_registration_slurm_files
)


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
    email: Optional[str] = None,
    segmentation_only: bool = False
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
        email=email
    )

    if segmentation_only:
        with open(os.path.join(automation_subdir, image, "submit_all.sh"), "w") as f:
            f.write("\n".join(shell_submit_script_lines))
        return f"./{os.path.join(automation_subdir, image, 'submit_all.sh')}"

    if (bone == "tibia") or (bone == "femur"):
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
            "JID_PP",
            "JID_REG",
            email=email
        )

    # generate ROIS

    generate_rois_slurm = os.path.join(slurm_dir, "6_generate_rois.sh")

    generate_rois_commands = [
        f"hrkGenerateROIs \\",
        f"{os.path.join(working_dir, 'model_masks', f'{image.lower()}_postprocessed_mask.nii.gz')} \\",
        f"{bone} \\",
        f"{os.path.join(working_dir, 'registrations', f'{image.lower()}_atlas_mask_transformed.nii.gz')} \\",
        f"{os.path.join(working_dir, 'roi_masks')} \\",
        f"{image.lower()} \\",
        f"--axial-dilation-footprint 40 -ow"
    ]

    write_slurm_script(
        generate_rois_slurm,
        generate_rois_commands,
        f"{image}_7_generate_rois",
        "8:00:00",
        "150GB",
        1,
        conda_dir,
        conda_env,
        email=email,
    )

    shell_submit_script_lines.append(
        f"JID_ROIS=$(sbatch --dependency=afterok:${{JID_REG}} {generate_rois_slurm} | tr -dc \"0-9\")"
    )
    # ROIs to AIMs

    rois_to_aims_slurm = os.path.join(slurm_dir, "7_rois_to_aims.slurm")
    rois_to_aims_commands = []
    for roi_code in ROI_CODES[bone]:
        rois_to_aims_commands += [
            f"hrkMask2AIM \\",
            f"{os.path.join(working_dir, 'roi_masks', f'{image.lower()}_roi{roi_code}_mask.nii.gz')} \\",
            f"{os.path.join(working_dir, 'aims', f'{image}.AIM')} \\",
            f"{os.path.join(working_dir, 'roi_masks', f'{image}_ROI{roi_code}_MASK.AIM')} \\",
            f"-l \"Generated using the code at: https://github.com/Bonelab/HRpQCT-Knee-Seg\" -ow",
        ]
    write_slurm_script(
        rois_to_aims_slurm,
        rois_to_aims_commands,
        f"{image}_8_rois_to_aims",
        "8:00:00",
        "100GB",
        2,
        conda_dir,
        conda_env,
        email=email
    )
    shell_submit_script_lines.append(
        f"sbatch --dependency=afterok:${{JID_ROIS}} {rois_to_aims_slurm}"
    )

    # ROIs to gifs

    visualize_slurm = os.path.join(slurm_dir, "8_rois_to_gifs.sh")
    visualize_commands = []
    visualize_commands += [
        f"hrkVisualize2DPanning \\",
        f"{os.path.join(working_dir, 'niftis', f'{image.lower()}.nii.gz')} \\",
        f"{os.path.join(working_dir, 'roi_masks', f'{image.lower()}_allrois_mask.nii.gz')} \\",
        f"{os.path.join(working_dir, 'visualizations', f'{image.lower()}_rois_reg')} \\",
        "-ib -400 1400 -pd 1 -ri -cens 10",
    ]
    write_slurm_script(
        visualize_slurm,
        visualize_commands,
        f"{image}_9_visualize",
        "1:30:00",
        "24GB",
        1,
        conda_dir,
        conda_env,
        email=email
    )
    shell_submit_script_lines.append(
        f"sbatch --dependency=afterok:${{JID_ROIS}} {visualize_slurm}"
    )

    # finally, create a submit_all.sh script and return a line that
    # can be added to the shell batch submit script
    with open(os.path.join(automation_subdir, image, "submit_all.sh"), "w") as f:
        f.write("\n".join(shell_submit_script_lines))
    return f"./{os.path.join(automation_subdir, image, 'submit_all.sh')}"


def crossectional(args: Namespace) -> None:

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
                    params["segmentation_only"]
                )
            )
        elif params["mode"] == "shell":
            raise NotImplementedError("Shell mode not implemented yet.")
        else:
            raise ValueError(f"Invalid mode: {params['mode']}")
    with open(os.path.join(params["automation_dir"], "submit_all.sh"), "w") as f:
        f.write("\n".join(batch_submit_lines))



def main():
    parser = create_parser("Cross-sectional")
    parser.add_argument(
        "--segmentation-only", "-so", action="store_true",
        help="Only run the segmentation step."
    )
    args = parser.parse_args()
    crossectional(args)


if __name__ == '__main__':
    main()
