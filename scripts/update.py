import logging
import os
from argparse import ArgumentParser
from copy import copy
from dataclasses import dataclass, field
from logging import getLogger
from pathlib import Path
from shutil import copyfile
from typing import Optional, Dict

DEFAULT_WORKDIR = Path(__file__).parent.parent.absolute()

logging.basicConfig(level=logging.DEBUG)
logger = getLogger(__file__)


@dataclass
class File:

    origin: Path
    destination: Path

    def __post_init__(self):

        if isinstance(self.origin, str):
            self.origin = Path(self.origin)

        origin_original = copy(self.origin)
        self.origin = self.origin.absolute()

        if not self.origin.exists():
            raise FileNotFoundError(f"`{origin_original}` resolved to `{str(self.origin)}`")

        if isinstance(self.destination, str):
            self.destination = Path(self.destination)

        self.destination = self.destination.absolute()

    @property
    def destination_hold(self):
        return Path(self.destination.parent / f"hold_{self.destination.name}")

    def update(self):

        logger.debug(f"copying `{self.origin.name}` --> `{self.destination.name}`")

        if self.destination.exists():
            logger.debug(f"holding the existing file")
            copyfile(self.destination, self.destination_hold)

        copyfile(self.origin, self.destination)

        logger.debug("done")

    def delete_destination_hold(self):

        logger.debug(f"deleting the file `{self.destination_hold}`")

        if not self.destination_hold.exists():
            logger.debug(f"it doesn't exist, skipping...")
            return

        os.remove(self.destination_hold)

        logger.debug("done")


def get_files_default_mapping() -> dict:
    # noinspection PyTypeChecker
    return dict(
        cv_one_page=File(
            origin="../cv/cv-one-page.en.pdf",
            destination="./files/cv.en.pdf",
        )
    )


def goto_workdir(workdir: Optional[str]):

    if workdir is not None:
        raise NotImplementedError(f"i haven't implemented workdir != None yet (:")

    if workdir is None:
        logger.info("using default workdir")
        logger.debug(f"{DEFAULT_WORKDIR=}")
        workdir = DEFAULT_WORKDIR  # the root of the website repo

    os.chdir(workdir)


def _files_update(mapping: Dict[str, File]) -> None:
    for key, file in mapping.items():
        logger.info(f"updating `{key}`")
        file.update()


def _purge_holds(mapping: Dict[str, File]) -> None:
    for key, file in mapping.items():
        logger.info(f"purge the hold of `{key}`")
        file.delete_destination_hold()


files_command = "files"
purge_holds_command = "purge-holds"


def main_files(files_command: str, workdir: Optional[str], mapping: Optional[str]):
    """

    :param files_command:
    :param workdir:
    :param mapping:
    :return:
    """

    goto_workdir(workdir)

    if mapping is not None:
        raise NotImplementedError(f"i haven't implemented mapping != None yet (:")

    if mapping is None:
        logger.info("using default files mapping")
        mapping = get_files_default_mapping()

    if files_command is None:
        _files_update(mapping)

    elif files_command == purge_holds_command:
        _purge_holds(mapping)

    else:
        NotImplementedError(f"{files_command=}")


if __name__ == "__main__":

    parser = ArgumentParser(
        prog="update",
        description="Automatically update my website with external resources (e.g.: my cv in pdf).",
    )

    parser.add_argument("--workdir", type=str, default=None, help="An absolute path in the file system. The script changes to this directory and *relative paths* are taken from there. Default: root of the repository.")

    commands = parser.add_subparsers(dest="command")

    # ============================================= files ============================================
    files_parser = commands.add_parser(files_command, description="update files in the /files directory such as my cv", help="stuff in the directory /files")

    files_parser.add_argument("--mapping", type=str, default=None, help=f"An absolute path in the file system. An .ini-like file mapping the origin-> destination of the files to be updated. Defaul: defined in `{__file__}`.")

    files_commands = files_parser.add_subparsers(dest="files_command")

    # ============================================= purge-holds ======================================

    purge_holds_parser = files_commands.add_parser(
        purge_holds_command,
        description="get rid of the hold_ files in the /files directory",
    )

    # ============================================= exec ======================================

    args = parser.parse_args()
    logger.debug(f"{args=}")

    command2main_mapping = {
        files_command: main_files,
    }

    command = args.command

    if command is None:
        logger.warning("No command given. Call option -h for help.")
        exit(0)

    logger.debug(f"{command=}")
    main = command2main_mapping[command]
    logger.debug(f"{main.__name__=}")
    del args.command

    args_dict = vars(args)
    logger.debug(f"{args=}")

    try:
        main(**args_dict)

    except Exception as ex:
        logger.exception(ex)
        exit(1)

    exit(0)
