"""@package docstring
This script finds all the EPICS db files in a given directory and parses the record
and field data into python classes. Arrays of Record instances can then be analysed
to find records that lack specific fields etc.

Dominic Oram
"""
import unittest
from loader import FileHolder
import xmlrunner
import argparse
import re

#list of those record types that should have a EGU field
EGU_list = {'ai', 'ao', 'calc', 'calcout', 'compress', 'dfanout', 'longin', 'longout', 'mbbo', 'mbboDirect', 'permissive',\
    'sel', 'seq', 'state', 'stringin', 'stringout', 'subArray', 'sub', 'waveform', 'archive', 'cpid', 'pid', 'steppermotor'}

#list of the accepted units
allowed_units = {'A', 'angstrom', 'bar', 'bit', 'byte', 'C', 'count', 'degree', 'eV', 'hour', 'Hz', 'inch', \
              'interrupt', 'K', 'L', 'm', 'minute', 'ohm', '%', 'photon', 'pixel', 'radian', 's', 'torr', 'step', 'V'}

recs = []

class TestPVUnits(unittest.TestCase):

    def dont_test_units_exist(self):
        """
        This method looks through the EPICS dbs and checks whether they require EGU fields and notes if those fields are blank
        or if there are multiple units. The test is failed if any important PVs lack fields and a warning is written to
        console for missing units on other PVs.
        """

        no_EGU      = []
        blank_EGU   = []
        multi_EGU   = []
        imp_noEGU   = []
        RBV_noEGU   = []

        for rec in self.recs:
            rec_type = rec.getType()

            #check if record type should have EGU and is not a simulation or disable
            if (rec_type in EGU_list) and not (rec.isSim()) and not (rec.isDisable()):
                unit = rec.getField("EGU")
                if len(unit) == 0:
                    #check for no units
                    if rec.isInterest():
                        imp_noEGU.append(rec)
                    elif rec.isReadback():
                        RBV_noEGU.append(rec)
                    no_EGU.append(rec)
                elif unit[0] == "":
                    #check for blank units
                    if rec.isInterest():
                        imp_noEGU.append(rec)
                    elif rec.isReadback():
                        RBV_noEGU.append(rec)
                    blank_EGU.append(rec)
                elif len(unit) != 1:
                    #check for multiple units
                    multi_EGU.append(rec)

        print "Warning: Number of PVs missing EGU field: " + str(len(no_EGU))
        print "Warning: Number of PVs with blank units: " + str(len(blank_EGU))
        print "Warning: Number of PVs with multiple units: " + str(len(multi_EGU))
        if len(imp_noEGU) > 0:
            for bad in imp_noEGU:
                print str(bad)
            self.assertEqual(imp_noEGU, 0, msg = "ERROR: Number of interesting PVs with invalid units: " + str(len(imp_noEGU)))
        if len(RBV_noEGU) > 0:
            #for bad in RBV_noEGU:
            #    print str(bad)
            self.assertEqual(RBV_noEGU, 0, msg = "ERROR: Number of RBVs with invalid units: " + str(len(RBV_noEGU)))

    def allowed_unit(self, unit):
        """
        This method checks that the given unit conforms to standard
        """
        if unit in allowed_units:
            return True

        #otherwise check for macro
        if unit[0] == "$":
            return True

        #otherwise split unit amalgamations
        units = re.split(r'[/ ()]', unit)
        for u in units:
            if not (u in allowed_units):
                #may be to the power of
                if not (re.match(r"\^[-]?\d", u)):
                    #may be prefixed
                    if not (re.match(r'T|G|M|k|m|u|n|p|f', u[0]) and u[1:] in allowed_units):
                        #special case of cm
                        if not u == "cm":
                            return False

        return True

    def test_units_valid(self):
        """
        This method loops through all found records and finds the unique units. It then checks these units are standard
        """
        #Holds the records sorted by unit
        saved_units = dict({})
        unitLabel = []
        unitsArray = []
        for rec in recs:
            unit = rec.getField("EGU")

            #add the units to the appropriate place in the dictionary
            if len(unit) == 1 and unit[0] != "":
                if unit[0] in saved_units:
                    saved_units[unit[0]] += 1
                    unitsArray[unitLabel.index(unit[0])].append(rec)
                else:
                    saved_units[unit[0]] = 1
                    unitLabel.append(unit[0])
                    unitsArray.append([])
                    unitsArray[unitLabel.index(unit[0])].append(rec)

        invalid = 0
        for ind, label in enumerate(unitLabel):
            if not self.allowed_unit(label):
                invalid += 1
                print str(label) + ":"
                for item in unitsArray[ind]:
                    print "     " + str(item)

        print "Units in project and number of instances: " + str(saved_units)

        self.assertEqual(invalid, 0)

    def test_interest_descriptions(self):
        """
        This method checks all records marked as interesting for description fields
        """
        err = 0
        errString = ""
        for rec in recs:
            if rec.isInterest() and len(rec.getField("DESC")) != 1:
                print "Missing description on: " + str(rec)
                errString += str(rec) + ", "

                err += 1

        self.assertTrue(err == 0, "Missing description on interesting fields: " + errString)

    def test_interest_syntax(self):
        """
        This method tests that all interesting PVs are capitalised and contain only a-z A-Z 0-9 _ :
        """
        for rec in recs:
            if rec.isInterest():
                se = re.search('[^\w_:]', rec.pv)
                self.assertFalse(se is None, "CHARACTER ERROR: " + rec.pv + " contains illegal characters")

                self.assertTrue(rec.pv.isupper(), "CASING ERROR: " + rec.pv + " should be upper-case")

def setUp():
    """
    This set up method loads and parses the db and template files prior to testing.
    """

    global recs

    dbs = FileHolder()

    for file_type in ['.db', '.template']:

        dbs.loadFiles('..\\..\\ioc', file_type)
        dbs.loadFiles('..\\..\\support', file_type)
        dbs.loadFiles('..\\', file_type)

    num = dbs.getFileNum()
    print "Number of EPICS dbs Found: " + str(num)

    #dbs.saveChecked()

    recs = dbs.parseFiles()

    print "Num of recs: " + str(len(recs))


DEFAULT_DIRECTORY = '..\\..\\test-reports'

if __name__ == '__main__':
    """
    Runs the unit tests
    """

    # Get output directory from command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output_dir', nargs=1, type=str, default=[DEFAULT_DIRECTORY],
                        help='The directory to save the test reports')
    args = parser.parse_args()
    xml_dir = args.output_dir[0]

    # Load files
    setUp()

    # Load tests
    units_suite = unittest.TestLoader().loadTestsFromTestCase(TestPVUnits)

    print "\n\n------ BEGINNING PV UNIT TESTS ------"

    xmlrunner.XMLTestRunner(output=xml_dir).run(units_suite)

    print "------ PV UNIT TESTS COMPLETE ------\n\n"