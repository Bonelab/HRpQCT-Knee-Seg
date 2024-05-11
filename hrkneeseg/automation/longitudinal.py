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


ROI_CODES = {
    "femur": [10, 11, 12, 13, 14, 15, 16, 17],
    "tibia": [30, 31, 32, 33, 34, 35, 36, 37],
}


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
    timecodes: List[str],
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

    for (seg_jid_var, atlas_jid_var, image, t) in zip(seg_jid_vars, atlas_jid_vars, all_images, timecodes):
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
            timecode=t
        )
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
                seg_jid_var,
                atlas_jid_var,
                email,
                timecode=t
            )
    if bone == "patella":
        # if we have been given a patella, just do the segmentation and then
        # stop, as we don't have an atlas for the patella
        with open(os.path.join(automation_subdir, name, "submit_all.sh"), "w") as f:
            f.write("\n".join(shell_submit_script_lines))
        return f"./{os.path.join(automation_subdir, name, 'submit_all.sh')}"

    longitudinal_registration_slurm = os.path.join(slurm_dir, "6_longitudinal_registration.sh")
    longitudinal_registration_commands = []
    longitudinal_registration_commands.append(
        "echo \"Step 1: mask the images with the postprocessed model masks\""
    )
    for image in [baseline] + followups:
        longitudinal_registration_commands += [
            f"hrkMaskImage \\",
            f"{os.path.join(working_dir, 'niftis', f'{image.lower()}.nii.gz')} \\",
            f"{os.path.join(working_dir, 'model_masks', f'{image.lower()}_postprocessed_mask.nii.gz')} \\",
            f"{os.path.join(working_dir, 'niftis', f'{image.lower()}_masked.nii.gz')} \\",
            f"--dilate-amount 35 --background-class 0 --background-value -1000 -ow"
        ]
    longitudinal_registration_commands.append(
        "echo \"Step 2: longitudinal registration\""
    )
    longitudinal_registration_commands += [
        f"mkdir {os.path.join(working_dir, 'registrations', baseline)}",
        f"blRegistrationLongitudinal \\",
        f"{os.path.join(working_dir, 'registrations', baseline)} {name.lower()} \\",
        f"{os.path.join(working_dir, 'niftis', f'{baseline.lower()}_masked.nii.gz')} \\",
    ]
    for followup in followups:
        longitudinal_registration_commands += [
            f"{os.path.join(working_dir, 'niftis', f'{followup.lower()}_masked.nii.gz')} \\"
        ]
    longitudinal_registration_commands += [
        f"--baseline-label {timecodes[0]} --follow-up-labels {' '.join(timecodes[1:])} \\"
    ]
    longitudinal_registration_commands += [
        "--max-iterations 1000 \\",
        "--downsampling-shrink-factor 4 \\",
        "--downsampling-smoothing-sigma 1 \\",
        "--shrink-factors 16 8 4 2 1 --smoothing-sigmas 8 4 2 1 0.1 \\",
        "--plot-metric-history \\",
        "--optimizer Powell \\",
        "--similarity-metric Correlation \\",
        "--similarity-metric-sampling-strategy Regular --similarity-metric-sampling-rate 0.3 \\",
        "--interpolator Linear \\",
        "--centering-initialization Geometry \\",
        "--overwrite"
    ]
    longitudinal_registration_commands.append(
        "echo \"Step 3: remove masked images\""
    )
    for image in [baseline] + followups:
        longitudinal_registration_commands.append(
            f"rm {os.path.join(working_dir, 'niftis', f'{image.lower()}_masked.nii.gz')}"
        )
    write_slurm_script(
        longitudinal_registration_slurm,
        longitudinal_registration_commands,
        f"{name}_6_longitudinal_registration",
        "6:00:00",
        "150GB",
        1,
        conda_dir,
        conda_env,
        email=email,
    )
    shell_submit_script_lines.append(
        (
            f"JID_REG=$(sbatch --dependency=afterok:{':'.join([f'${{{ajv}}}' for ajv in atlas_jid_vars])} "
            f"{longitudinal_registration_slurm} | tr -dc \"0-9\")"
        )
    )
    generate_rois_slurm = os.path.join(slurm_dir, "7_generate_rois.sh")
    generate_rois_commands = []
    generate_rois_commands.append(
        "echo \"Step 1: transform the followup image segmentations to the baseline reference frame\""
    )
    for followup, timecode in zip(followups, timecodes[1:]):
        generate_rois_commands += [
            f"blRegistrationApplyTransform \\",
            f"{os.path.join(working_dir, 'model_masks', f'{followup.lower()}_postprocessed_mask.nii.gz')} \\",
            f"{os.path.join(working_dir, 'registrations', baseline, f'{name.lower()}_{timecode}_transform.txt')} \\",
            f"{os.path.join(working_dir, 'registrations', baseline, f'{name.lower()}_{timecode}_bone_mask_baseline.nii.gz')} \\",
            f"-fi {os.path.join(working_dir, 'model_masks', f'{followup.lower()}_postprocessed_mask.nii.gz')} \\",
            "-int NearestNeighbour -ow"
        ]
    generate_rois_commands.append(
        "echo \"Step 2: transform the followup image atlas masks to the baseline reference frame\""
    )
    for followup, timecode in zip(followups, timecodes[1:]):
        generate_rois_commands += [
            f"blRegistrationApplyTransform \\",
            f"{os.path.join(working_dir, 'atlas_registrations', f'{followup.lower()}_atlas_mask_transformed.nii.gz')} \\",
            f"{os.path.join(working_dir, 'registrations', baseline, f'{name.lower()}_{timecode}_transform.txt')} \\",
            f"{os.path.join(working_dir, 'registrations', baseline, f'{name.lower()}_{timecode}_atlas_mask_baseline.nii.gz')} \\",
            f"-fi {os.path.join(working_dir, 'model_masks', f'{followup.lower()}_postprocessed_mask.nii.gz')} \\",
            "-int NearestNeighbour -ow"
        ]
    generate_rois_commands.append(
        "echo \"Step 3: Find the intersection of the atlas masks in the baseline reference frame\""
    )
    generate_rois_commands += [
        f"hrkIntersectMasks \\",
        f"-i \\"
        f"{os.path.join(working_dir, 'atlas_registrations', f'{baseline}_atlas_mask_transformed.nii.gz')} \\"
    ]
    for followup, timecode in zip(followups, timecodes[1:]):
        generate_rois_commands += [
            f"{os.path.join(working_dir, 'registrations', baseline, f'{name.lower()}_{timecode}_atlas_mask_baseline.nii.gz')} \\"
        ]
    generate_rois_commands += [
        f"-o {os.path.join(working_dir, 'registrations', baseline, f'{name}_atlas_masks_overlapped_baseline.nii.gz')} \\",
        f"-c 1 2 -ow"
    ]
    generate_rois_commands += [
        f"echo \"Step 4: Generate the ROIs in the baseline reference frame with the overlapped atlas masks\"",
        f"hrkGenerateROIs \\"
        f"{os.path.join(working_dir, 'model_masks', f'{baseline.lower()}_postprocessed_mask.nii.gz')} \\",
        f"{bone} \\",
        f"{os.path.join(working_dir, 'registrations', baseline, f'{name}_atlas_masks_overlapped_baseline.nii.gz')} \\",
        f"{os.path.join(working_dir, 'roi_masks')} \\",
        f"{baseline.lower()} \\",
        f"--axial-dilation-footprint 40 -ow"
    ]
    for followup, timecode in zip(followups, timecodes[1:]):
        generate_rois_commands += [
            f"hrkGenerateROIs \\"
            f"{os.path.join(working_dir, 'registrations', baseline, f'{name.lower()}_{timecode}_bone_mask_baseline.nii.gz')} \\",
            f"{bone} \\",
            f"{os.path.join(working_dir, 'registrations', baseline, f'{name.lower()}_{timecode}_atlas_mask_baseline.nii.gz')} \\",
            f"{os.path.join(working_dir, 'roi_masks')} \\",
            f"{followup.lower()}_baseline \\",
            f"--axial-dilation-footprint 40 -ow"
        ]
    generate_rois_commands.append(
        "echo \"Step 5: Transform the followup ROIs to the followup reference frames\""
    )
    for followup, timecode in zip(followups, timecodes[1:]):
        generate_rois_commands += [
            f"blRegistrationApplyTransform \\",
            f"{os.path.join(working_dir, 'roi_masks', f'{followup.lower()}_baseline_allrois_mask.nii.gz')} \\",
            f"{os.path.join(working_dir, 'registrations', baseline, f'{name.lower()}_{timecode}_transform.txt')} \\",
            f"{os.path.join(working_dir, 'roi_masks', f'{followup.lower()}_allrois_mask.nii.gz')} \\",
            f"-fi {os.path.join(working_dir, 'model_masks', f'{followup.lower()}_postprocessed_mask.nii.gz')} \\",
            "-int NearestNeighbour -it -ow"
        ]
    generate_rois_commands += [
        f"for ROI_CODE in {' '.join(map(str, ROI_CODES[bone]))}; ",
        f"do",
    ]
    for followup, timecode in zip(followups, timecodes[1:]):
        generate_rois_commands += [
            f"  blRegistrationApplyTransform \\",
            f"  {os.path.join(working_dir, 'roi_masks', f'{followup.lower()}_baseline_roi${{ROI_CODE}}_mask.nii.gz')} \\",
            f"  {os.path.join(working_dir, 'registrations', baseline, f'{name.lower()}_{timecode}_transform.txt')} \\",
            f"  {os.path.join(working_dir, 'roi_masks', f'{followup.lower()}_roi${{ROI_CODE}}_mask.nii.gz')} \\",
            f"  -fi {os.path.join(working_dir, 'model_masks', f'{followup.lower()}_postprocessed_mask.nii.gz')} \\",
            "  -int NearestNeighbour -it -ow"
        ]
    generate_rois_commands.append("done")
    write_slurm_script(
        generate_rois_slurm,
        generate_rois_commands,
        f"{name}_7_generate_rois",
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
    rois_to_aims_slurm = os.path.join(slurm_dir, "8_rois_to_aims.slurm")
    rois_to_aims_commands = []
    for image in  [baseline] + followups:
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
        f"{name}_8_rois_to_aims",
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

    visualize_slurm = os.path.join(slurm_dir, "9_rois_to_gifs.sh")
    visualize_commands = []
    for image in [baseline] + followups:
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
        f"{name}_9_visualize",
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
                    data["timecodes"],
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
