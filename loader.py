from os.path import join
from db_parser import parse_db
from ignored_paths import ignored_paths
import os


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

    def load_files(self, path, file_type):
        """
        This method will search a given directory, including all sub-directories, for files of type file_type.
        It will then attempt to determine if the files are in EPICS format.
        The method will return a list of those files suspected of being EPICS format.
        """

        dbs = []
        ignores = self.load_checked()

        print "Searching for *" + file_type

        # walk through all files
        for root, dirs, files in os.walk(path):
            for f in files:
                # find dbs but ignoring certain directories
                if f.endswith(file_type) and not any(x in root for x in ignored_paths):
                    directory = join(root, f)
                    text = open(directory).read()
                    # check db is EPICS
                    if not(text.find("record") == -1):  # or text.find("field") == -1):
                        # print "Found Suspected EPICS db: %s" % directory

                        # check db hasn't already been checked
                        if directory in ignores:
                            print "same"
                        else:
                            # get the timestamp of the last modification on the file
                            timestamp = os.stat(directory)[8]

                            dbs.append(SingleFile(directory, text, timestamp))

        self.dbs.extend(dbs)

    def get_files(self):
        return self.dbs

    def parse_files(self):
        """
        Method that stores all the records from all found files and returns a list of them
        """
        return [parse_db(db) for db in self.dbs]

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
                f.write(str(db.get_dir()) + ';')