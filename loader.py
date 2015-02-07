__author__ = 'ffv81422'

from os.path import join
from db_parser import Parser
from ignored_paths import *
import os

class SingleFile:
    def __init__(self, directory, text, timestamp):
        self.directory = directory
        self.text = text
        self.timestamp = timestamp

    def getTime(self):
        return self.timestamp

    def getDir(self):
        return self.directory

    def getText(self):
        return self.text

class FileHolder:

    def __init__(self):
        self.dbs = []

    def loadFiles(self, path, file_type):
        """
        This method will search a given directory, including all sub-directories, for files of type file_type.
        It will then attempt to determine if the files are in EPICS format.
        The method will return a list of those files suspected of being EPICS format.
        """

        dbs = []
        ignores = self.loadChecked()

        print "Searching for *" + file_type

        #walk through all files
        for root, dirs, files in os.walk(path):
            for f in files:
                #find dbs but ignoring certain directories
                if f.endswith(file_type) and not any(x in root for x in ignored_paths()):
                    directory = join(root, f)
                    text = open(directory).read()
                    #check db is EPICS
                    if not(text.find("record") == -1):# or text.find("field") == -1):
                        #print "Found Suspected EPICS db: %s" % directory

                        #check db hasn't already been checked
                        if directory in ignores:
                            print "same"
                        else:
                            #get the timestamp of the last modification on the file
                            timestamp = os.stat(directory)[8]

                            dbs.append(SingleFile(directory, text, timestamp))

        self.dbs.extend(dbs)

    def getFiles(self):
        return self.dbs

    def parseFiles(self):
        """
        Method that stores all the records from all found files and returns a list of them
        """

        recs = []

        for db in self.dbs:
            parse = Parser(db)
            recs.extend(parse.parseDB())

        return recs

    def getFileNum(self):
        return len(self.dbs)

    def loadChecked(self):
        """
        This method will load a list of all the dbs checked to be good by the program
        """
        goodDirs = []
        if os.path.exists("./ignore.txt"):
            loadFile = open("./ignore.txt" ,'r')
            goodDirs = loadFile.read().split(';')
        return goodDirs

    def saveChecked(self):
        """
        This method will save a list of all the dbs checked to be good by the program
        """
        saveFile = open("./ignore.txt" ,'w')
        for f in self.dbs:
            #save in format 'directory;'
            saveFile.write(str(f.getDir()) + ';')
        saveFile.close()