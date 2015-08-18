__author__ = 'ffv81422'

import re

"""
This file holds the classes to hold the record and field data
"""

class Record:
    """
    This class holds all the data about each record, including a list of
    fields within the record, and allows the constituent fields to be
    interrogated.
    """

    def __init__(self, directory, type, pv, infos, fields):
        self.directory  = directory
        self.type       = type
        self.pv         = pv
        self.fields     = fields
        self.infos      = infos

        #Test for whether the PV is a simulation
        if re.search(r'.SIM(:.|$)',pv) != None:
            self.simulation = True
        else:
            self.simulation = False

        #Test for whether the PV is a disable
        if re.search(r'DISABLE',pv) != None:
            self.disable = True
        else:
            self.disable = False

    def isSim(self):
        return self.simulation

    def isDisable(self):
        return self.disable

    def __str__(self):
        return str(self.directory) + "\\" + str(self.pv)

    def hasField(self, search):
        """
        This method checks all contained fields for instances of a pv given by the search input
        """
        for field in self.fields:
            if field.name == search:
                return True
        return False

    def getField(self, search):
        """
        This method returns a list of the values of all contained fields that match the search input
        """
        found_values = []
        for field in self.fields:
            if field.name == search:
                found_values.append(field.value)

        return found_values

    def getType(self):
        """
        This method returns the PV type
        """
        return self.type

    def getInfo(self, search):
        """
        This method returns a list of the values of all contained info fields that match the search input
        """
        found_values = []
        for info in self.infos:
            if info.name == search:
                found_values.append(info.value)

        return found_values

    def isInterest(self):
        """
        This method returns whether or not the record is of interest
        """
        for info in self.infos:
            if info.name == "INTEREST":
                return True
        return False

class Field:
    """
    This class holds all the data about each field within a record
    """
    def __init__(self, name, value):
        self.name   = name.strip()
        self.value  = value

    def __str__(self):
        return str(self.name) + ":" + str(self.value)
