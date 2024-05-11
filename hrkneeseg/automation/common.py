from __future__ import annotations

from typing import List, Optional
import os

from hrkneeseg.automation.write_slurm_script import write_slurm_script


def create_segmentation_slurm_files(
    slurm_dir: str,
    postsurgery: bool,
    image: str,
    working_dir: str,
    conda_dir: str,
    conda_env: str,
    segmentation_models: List[dict],
    last_jid_var: str,
    email: Optional[str] = None,
    timecode: Optional[str] = None
) -> List[str]:
    '''
    Create slurm scripts and shell batch submit script
    for a single image, and return a line that can be
    added to the shell batch submit script.

    Parameters
    ----------
    slurm_dir : str
        Path to the automation directory.

    postsurgery : bool
        Whether the image is post-surgical.

    image : str
        Name of the image.

    working_dir : str
        Path to the working directory.

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

    last_jid_var : str
        Name of the variable that will store the job id of the last job
        that needs to finish before the workflow can continue.

    email : Optional[str], optional
        Email address to send notifications to.
        Defaults to `None`.

    timecode : Optional[str]
        The timecode to create a subdirectory for the slurm scripts.

    Returns
    -------
    List[str]
        Lines that can be added to the shell batch submit script.
    '''
    if timecode is not None:
        try:
            os.mkdir(os.path.join(slurm_dir, timecode))
        except FileExistsError:
            pass
        slurm_dir = os.path.join(slurm_dir, timecode)
    shell_submit_script_lines = []
    # Step 0: Convert to Nifti
    slurm_convert_to_nifti = os.path.join(slurm_dir, "0_convert_to_nifti.slurm")
    write_slurm_script(
        slurm_convert_to_nifti,
        [
            (
                f"hrkAIMs2NIIs "
                f"{os.path.join(working_dir, 'aims', f'{image}.AIM')} "
                f"{os.path.join(working_dir, 'niftis')} "
                f"-ow"
            ),
        ],
        f"{image}_0_convert_to_nii",
        "2:00:00",
        "64G",
        1,
        conda_dir,
        conda_env,
        email=email
    )
    shell_submit_script_lines.append(
        f"JID_NII=$(sbatch {slurm_convert_to_nifti} | tr -dc \"0-9\")"
    )
    # Step 1: Inference
    slurm_inference = os.path.join(slurm_dir, "1_inference.slurm")
    write_slurm_script(
        slurm_inference,
        (
            [
                f"hrkInferenceEnsemble \\",
                f"{os.path.join(working_dir, 'niftis', f'{image.lower()}.nii.gz')} \\",
                f"{os.path.join(working_dir, 'model_masks')} {image.lower()} \\",
                f"-hf \\"
            ]
            + [
                f"{sm['hyperparameters']} \\"
                for sm in segmentation_models
            ] + [
                f"-cf \\"
            ] + [
                f"{sm['checkpoint']} \\"
                for sm in segmentation_models
            ] + [
                f"-mt {' '.join([sm['type'] for sm in segmentation_models])} \\",
                f"-pw 128 -bs 2 -ow --cuda -o 0.25"
            ]
        ),
        f"{image}_1_inference",
        "4:00:00",
        "150G",
        2,
        conda_dir,
        conda_env,
        email=email,
        partition="gpu-v100",
        num_gpus=1
    )
    shell_submit_script_lines.append(
        f"JID_INF=$(sbatch --dependency=afterok:${{JID_NII}} {slurm_inference} | tr -dc \"0-9\")"
    )
    # Step 2: Post-processing
    slurm_post_processing = os.path.join(slurm_dir, "2_post_processing.slurm")
    write_slurm_script(
        slurm_post_processing,
        [
            f"hrkPostProcessSegmentation \\",
            f"{os.path.join(working_dir, 'model_masks', f'{image.lower()}_ensemble_inference_mask.nii.gz')} \\",
            f"{os.path.join(working_dir, 'model_masks')} {image.lower()} \\",
            f"{'-t' if postsurgery else ''} -ow \\"
        ],
        f"{image}_2_post_processing",
        "3:00:00",
        "200G",
        1,
        conda_dir,
        conda_env,
        email=email
    )
    shell_submit_script_lines.append(
        f"{last_jid_var}=$(sbatch --dependency=afterok:${{JID_INF}} {slurm_post_processing} | tr -dc \"0-9\")"
    )
    # Step 3: Convert to AIM
    slurm_convert_to_aim = os.path.join(slurm_dir, "3_convert_to_aim.slurm")
    write_slurm_script(
        slurm_convert_to_aim,
        [
            f"hrkMasks2AIMs \\",
            f"{os.path.join(working_dir, 'model_masks', f'{image.lower()}_postprocessed_mask.nii.gz')} \\",
            f"{os.path.join(working_dir, 'aims', f'{image}.AIM')} \\",
            f"{os.path.join(working_dir, 'roi_masks', image)} \\",
            f"-cv 1 2 {'3' if postsurgery else ''} \\",
            f"-cl CORT_MASK TRAB_MASK {'TUNNEL_MASK' if postsurgery else ''} \\",
            f"-l \"Generated using the code at: https://github.com/Bonelab/HRpQCT-Knee-Seg\" \\",
            f"-ow \\",
        ],
        f"{image}_3_convert_to_aim",
        "2:00:00",
        "100G",
        2,
        conda_dir,
        conda_env,
        email=email
    )
    shell_submit_script_lines.append(
        f"sbatch --dependency=afterok:${{{last_jid_var}}} {slurm_convert_to_aim}"
    )
    # Step 4: Visualizations
    slurm_visualizations = os.path.join(slurm_dir, "4_segmentation_visualizations.slurm")
    write_slurm_script(
        slurm_visualizations,
        [
            f"hrkVisualize2DPanning \\",
            f"{os.path.join(working_dir, 'niftis', f'{image.lower()}.nii.gz')} \\",
            f"{os.path.join(working_dir, 'model_masks', f'{image.lower()}_ensemble_inference_mask.nii.gz')} \\",
            f"{os.path.join(working_dir, 'visualizations', f'{image.lower()}_inference')} \\",
            f"-ib -400 1400 -pd 1 -ri -cens 10 \\",
            f"hrkVisualize2DPanning \\",
            f"{os.path.join(working_dir, 'niftis', f'{image.lower()}.nii.gz')} \\",
            f"{os.path.join(working_dir, 'model_masks', f'{image.lower()}_postprocessed_mask.nii.gz')} \\",
            f"{os.path.join(working_dir, 'visualizations', f'{image.lower()}_postprocessed')} \\",
            f"-ib -400 1400 -pd 1 -ri -cens 10 \\"
        ],
        f"{image}_4_segmentation_visualizations",
        "1:00:00",
        "100G",
        1,
        conda_dir,
        conda_env,
        email=email
    )
    shell_submit_script_lines.append(
        f"sbatch --dependency=afterok:${{{last_jid_var}}} {slurm_visualizations}"
    )

    return shell_submit_script_lines


def create_atlas_registration_slurm_files(
    slurm_dir: str,
    side: str,
    bone: str,
    postsurgery: bool,
    image: str,
    working_dir: str,
    atlas_dir: str,
    conda_dir: str,
    conda_env: str,
    dependent_jid_var: str,
    last_jid_var: str,
    email: Optional[str] = None,
    timecode: Optional[str] = None,
) -> List[str]:
    '''
    Create slurm scripts and shell batch submit script
    for a single image, and return a line that can be
    added to the shell batch submit script.

    Parameters
    ----------
    slurm_dir : str
        The directory to save the slurm scripts to.

    side : str
        The side of the knee being processed.

    bone : str
        The bone being processed.

    postsurgery : bool
        Whether the image is from a post-surgery scan.

    image : str
        The image being processed.

    working_dir : str
        The directory containing the image and model masks.

    atlas_dir : str
        The directory containing the atlas images.

    conda_dir : str
        The directory containing the conda environment.

    conda_env : str
        The name of the conda environment.

    dependent_jid_var : str
        The name of the variable containing the job id of the previous job.

    last_jid_var : str
        The name of the variable to store the job id of the current job.

    email : Optional[str]
        The email address to send notifications to.

    timecode : Optional[str]
        The timecode to create a subdirectory for the slurm scripts.
    '''
    if timecode is not None:
        try:
            os.mkdir(os.path.join(slurm_dir, timecode))
        except FileExistsError:
            pass
        slurm_dir = os.path.join(slurm_dir, timecode)
    shell_submit_script_lines = []
    # Step 5: Atlas Registration
    slurm_atlas_registration = os.path.join(slurm_dir, "5_atlas_registration.slurm")
    write_slurm_script(
        slurm_atlas_registration,
        [
            f"echo \"Step 1: mask the image with the postprocessed model mask\"",
            f"hrkMaskImage \\",
            f"{os.path.join(working_dir, 'niftis', f'{image.lower()}.nii.gz')} \\",
            f"{os.path.join(working_dir, 'model_masks', f'{image.lower()}_postprocessed_mask.nii.gz')} \\",
            f"{os.path.join(working_dir, 'niftis', f'{image.lower()}_masked.nii.gz')} \\",
            f"--dilate-amount 35 --background-class 0 --background-value -1000 -ow"
        ] + (
            [
                f"echo \"Step 2: LEFT knee, need to mirror it\"",
                f"blImageMirror \\",
                f"{os.path.join(working_dir, 'niftis', f'{image.lower()}_masked.nii.gz')} \\",
                f"0 \\",
                f"{os.path.join(working_dir, 'niftis', f'{image.lower()}_masked.nii.gz')} -ow",
            ] if side == "Left" else [
                f"echo \"Step 2: not LEFT knee, don't need to mirror it\""
            ]
        ) + [
            f"echo \"Step 3: register the nifti to the atlas\"",
            f"blRegistrationDemons \\",
            f"{os.path.join(working_dir, 'niftis', f'{image.lower()}_masked.nii.gz')} \\",
            f"{os.path.join(atlas_dir, bone, 'atlas.nii')} \\"
            f"{os.path.join(working_dir, 'atlas_registrations', f'{image.lower()}_atlas_transform.nii.gz')} \\",
            f"-mida -dsf 8 -dss 0.5 -ci Geometry -dt diffeomorphic \\",
            f"-mi 200 -ds 2 -us 2 -sf 16 8 4 2 -ss 8 4 2 1 -pmh -ow",
            f"echo \"Step 4: transform the atlas mask to the image\"",
            f"blRegistrationApplyTransform \\",
            f"{os.path.join(atlas_dir, bone, 'atlas_mask.nii.gz')} \\",
            f"{os.path.join(working_dir, 'atlas_registrations', f'{image.lower()}_atlas_transform.nii.gz')} \\",
            f"{os.path.join(working_dir, 'atlas_registrations', f'{image.lower()}_atlas_mask_transformed.nii.gz')} \\",
            f"--fixed-image {os.path.join(working_dir, 'niftis', f'{image.lower()}_masked.nii.gz')} \\",
            f"-int NearestNeighbour -ow",
        ] + (
            [
                f"echo \"Step 5: LEFT knee, need to mirror the image and transformed mask back\"",
                f"blImageMirror \\",
                f"{os.path.join(working_dir, 'atlas_registrations', f'{image.lower()}_atlas_mask_transformed.nii.gz')} \\",
                f"0 \\",
                f"{os.path.join(working_dir, 'atlas_registrations', f'{image.lower()}_atlas_mask_transformed.nii.gz')} \\",
                f"-int NearestNeighbour -ow"
            ] if side == "Left" else [
                f"echo \"Step 5: not LEFT knee, don't need to mirror the image and transformed mask back\""
            ]
        ) + [
            f"echo \"Step 6: remove the masked image\"",
            f"rm {os.path.join(working_dir, 'niftis', f'{image.lower()}_masked.nii.gz')}",
        ],
        f"{image}_5_atlas_registration",
        "3:00:00",
        "64G",
        1,
        conda_dir,
        conda_env,
        email=email
    )
    shell_submit_script_lines.append(
        f"{last_jid_var}=$(sbatch --dependency=afterok:{{{dependent_jid_var}}} {slurm_atlas_registration} | tr -dc \"0-9\")"
    )
    return shell_submit_script_lines
