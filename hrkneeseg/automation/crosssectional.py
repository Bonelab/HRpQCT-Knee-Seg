from __future__ import annotations

from argparse import Namespace
from hrkneeseg.automation.parser import create_parser


def crossectional(args: Namespace) -> None:
    pass


def main():
    args = create_parser("Cross-sectional").parse_args()
    crossectional(args)


if __name__ == '__main__':
    main()
