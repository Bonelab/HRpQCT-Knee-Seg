from __future__ import annotations

from typing import List, Optional, Tuple

def write_slurm_script(
    fn: str,
    commands: List[str],
    job_name: str,
    time: str,
    mem: str,
    num_cpus: int,
    conda_path: str,
    conda_env: str,
    partition: Optional[str] = None,
    num_gpus: Optional[int] = None,
    email: Optional[str] = None,
    environment_variables: Optional[List[Tuple[str, str]]] = None
) -> None:
    '''
    Write a slurm script.

    Parameters
    ----------
    fn : str
        Path to the file to write the script to.

    commands : List[str]
        List of commands to run in the script.

    job_name : str
        Name of the job.

    time : str
        Time to reserve the resources for.

    mem : str
        Memory to reserve.

    num_cpus : int
        Number of CPUs to reserve.

    conda_path : str
        Path to the conda installation.

    conda_env : str
        Name of the conda environment to activate.

    partition : Optional[str], optional
        Partition to reserve the resources from, by default None.

    num_gpus : Optional[int], optional
        Number of GPUs to reserve, by default None.

    email : Optional[str], optional
        Email address to send notifications to, by default None.

    environment_variables : Optional[List[Tuple[str, str]]], optional
        List of environment variables to set, by default None.
    '''
    with open (fn, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('####### Reserve computing resources #############\n')
        f.write(f'#SBATCH --nodes=1\n')
        f.write(f'#SBATCH --ntasks=1\n')
        f.write(f'#SBATCH --cpus-per-task={num_cpus}\n')
        f.write(f'#SBATCH --time={time}\n')
        f.write(f'#SBATCH --mem={mem}\n')
        if partition is not None:
            f.write(f'#SBATCH --partition={partition}\n')
        if num_gpus is not None:
            f.write(f'#SBATCH --gres=gpu:{num_gpus}\n')
        f.write(f'#SBATCH --job-name={job_name}\n')
        if email is not None:
            f.write(f'#SBATCH --mail-user={email}\n')
            f.write('#SBATCH --mail-type=BEGIN\n')
            f.write('#SBATCH --mail-type=END\n')
            f.write('#SBATCH --mail-type=FAIL\n')
        f.write('\n')
        f.write('####### Set environment variables ###############\n')
        f.write(f'export PATH="{conda_path}:$PATH"\n')
        f.write('export PYTHONUNBUFFERED=1\n')
        if environment_variables is not None:
            for var, val in environment_variables:
                f.write(f'export {var}="{val}"\n')
        f.write('\n')
        f.write('####### Run your script #########################\n')
        f.write(f'source activate {conda_env}\n')
        for command in commands:
            f.write(f'{command}\n')
