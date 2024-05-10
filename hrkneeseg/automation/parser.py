from __future__ import annotations

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

def create_parser(analysis_type: str) -> ArgumentParser:
    parser = ArgumentParser(
        description=f'{analysis_type} analysis',
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "yaml", type=str,
        help="Path to the YAML file containing the configuration"
    )
    parser.add_argument(
        "--automation-dir", "-ad", type=str, default="automation",
        help=(
            "Path to the automation directory, where shell and/or "
            "slurm scripts will be stored."
        )
    )
    parser.add_argument(
        "--mode", "-m", type=str, choices=["shell", "slurm"], default="slurm",
        help=(
            "Mode of automation. `shell` will create shell scripts that can be "
            "run on a local machine. `slurm` will create slurm scripts that can "
            "be submitted to a slurm cluster, along with a shell script to "
            "submit the slurm scripts with the correct dependency structure."
        )
    )
    parser.add_argument(
        "--email", "-e", type=str, default=None,
        help="Email address to send notifications to. Only applies to `slurm` mode."
    )
    return parser
