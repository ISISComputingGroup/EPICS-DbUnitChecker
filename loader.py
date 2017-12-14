from os.path import join
from db_parser import parse_db
import os


DIRECTORIES_TO_ALWAYS_IGNORE = [
    ".git",
    "O.Common",
    "O.windows-x64",
    "bin",
    "lib",
    "include",
    ".project",
    "areaDetector",  # Has some huge DBs which take forever to parse.
]


class SingleFile:
    def __init__(self, directory, text, timestamp):
        self.directory = directory
        self.text = text
        self.timestamp = timestamp

    def get_time(self):
        return self.timestamp

    def get_dir(self):
        return self.directory

    def get_text(self):
        return self.text


def _load_files(path, file_types):
    """
    This method will search a given directory, including all sub-directories, for files of type in file_types.
    It will then attempt to determine if the files are in EPICS format.

    Args:
        path: the path to load DBs from
        file_types: a list of file extensions that are expected

    Yields:
        files that are in EPICS format
    """
    for root, dirs, files in os.walk(os.path.normpath(path)):
        dirs[:] = [d for d in dirs if d not in DIRECTORIES_TO_ALWAYS_IGNORE]

        for f in [f for f in files if any(f.endswith(file_type) for file_type in file_types)]:
            filename = os.path.abspath(join(root, f))

            with open(filename) as _file:
                text = _file.read()

            # check db is EPICS
            if not(text.find("record") == -1):

                # get the timestamp of the last modification on the file
                timestamp = os.stat(filename)[8]

                yield SingleFile(filename, text, timestamp)


def parsed_files(path, file_types):
    """
    Generator of parsed DB files.

    Args:
        path: the path to load DBs from
        file_types: a list of file extensions that are expected

    Yields:
        parsed db files
    """
    for db in _load_files(path, file_types):
        try:
            yield parse_db(db)
        except ValueError as e:
            raise ValueError("Failed to parse DB '{}'. Exception was: {}".format(db.directory, e))
