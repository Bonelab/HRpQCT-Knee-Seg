from __future__ import annotations

from argparse import Namespace
from hrkneeseg.automation.parser import create_parser


def longitudinal(args: Namespace) -> None:
    pass


def main():
    args = create_parser("Longitudinal").parse_args()
    longitudinal(args)


if __name__ == '__main__':
    main()
