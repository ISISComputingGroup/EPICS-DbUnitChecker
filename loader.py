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


class FileHolder:

    def __init__(self):
        self.dbs = []

    def load_files(self, path, file_types):
        """
        This method will search a given directory, including all sub-directories, for files of type file_type.
        It will then attempt to determine if the files are in EPICS format.
        The method will return a list of those files suspected of being EPICS format.
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

                    self.dbs.append(SingleFile(filename, text, timestamp))

    def get_files(self):
        return self.dbs

    def parse_files(self):
        """
        Method that stores all the records from all found files and returns a list of them
        """
        for db in self.dbs:
            yield parse_db(db)

    def load_checked(self):
        """
        This method will load a list of all the dbs checked to be good by the program
        """
        good_dirs = []
        if os.path.exists("./ignore.txt"):
            with open("./ignore.txt", 'r') as f:
                good_dirs = f.read().split(';')
        return good_dirs

    def save_checked(self):
        """
        This method will save a list of all the dbs checked to be good by the program
        """
        for db in self.dbs:
            # save in format 'directory;'
            with open("./ignore.txt", 'w') as f:
                f.write('{};'.format(db.get_dir()))
