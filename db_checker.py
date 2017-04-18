"""@package docstring
This script finds all the EPICS db files in a given directory and parses the record
and field data into python classes. Arrays of Record instances can then be analysed
to find records that lack specific fields etc.
"""
import unittest
from loader import FileHolder
import xmlrunner
import argparse
import re
import sys
import os
from collections import defaultdict
from ignored_paths import ignored_names_paths

# list of those record types that should have a EGU field
EGU_list = {'ai', 'ao', 'calc', 'calcout', 'compress', 'dfanout', 'longin', 'longout', 'mbbo', 
            'mbboDirect', 'permissive', 'sel', 'seq', 'state', 'stringin', 'stringout', 'subArray', 
            'sub', 'waveform', 'archive', 'cpid', 'pid', 'steppermotor'}

EGU_sub_list = {'longin', 'longout', 'ai', 'ao'}

# list of the accepted units. Standard prefixs to these units are also accepted and checked for below
# but we need to allow 'cm' explicitly as itr is a non-standard unit prefix for metre
allowed_units = {'A', 'angstrom', 'bar', 'bit', 'byte', 'C', 'count', 'degree', 'eV', 'frame', 'hour', 
                 'Hz', 'inch', 'interrupt', 'K', 'L', 'm', 'min', 'minute', 'ohm', 'Oersted', '%', 
                 'photon', 'pixel', 'radian', 's','torr', 'step', 'T', 'V', 'cm', 'Pa'}

allowed_units_prefixes =  { 'T', 'G', 'M', 'k', 'm', 'u', 'n', 'p', 'f' }

dbs = list()

def err_src_fmt(db, rec):
    return str(rec) + " in " + str(db)


class TestPVUnits(unittest.TestCase):

    def test_multiple_pvs_warning(self):
        """
        This method warns if there are multiple PVs with the same name in the project
        """
        for db in dbs:
            dups = defaultdict(list)  # Makes a dict of lists
            for rec in db.records:
                dups[str(rec.pv)].append(rec)

            for k, v in dups.iteritems():
                if len(v) > 1:
                    print "WARNING: Multiple instances of " + err_src_fmt(db, k)

    def test_multiple_properties_on_pvs(self):
        """
        This method checks that no PVs have duplicate fields
        """
        err = 0

        for db in dbs:
            for rec in db.records:
                fields = rec.get_field_names()
                if len(set(fields)) != len(fields):
                    err += 1
                    print "ERROR: Multiple of the same fields on " + err_src_fmt(db, rec)

        self.assertEqual(err, 0, msg="Multiple fields on PVs in project")

    def test_interest_populated_fields_warning(self):
        """
        This method warns if interesting PVs don't have all fields populated
        """
        for db in dbs:
            for rec in db.records:
                if rec.is_interest():
                    fields_values = rec.get_field_values()

                    if None in fields_values or "" in fields_values:
                        print "WARNING: Blank fields on " + err_src_fmt(db, rec)

    def test_interest_units(self):
        """
        This method checks that interesting PVs have units
        """
        err = 0

        for db in dbs:
            for rec in db.records:
                if rec.is_interest() and not rec.is_disable() and (rec.get_type() in EGU_sub_list):
                    unit = rec.get_field("EGU")

                    if unit is None:
                        err += 1
                        print "ERROR: Missing units on " + err_src_fmt(db, rec)

        self.assertEqual(err, 0, msg="Missing units on interesting PVs in project")

    def test_desc_length(self):
        """
        This method checks that the description length on all PVs is no longer than 40 chars
        """
        err = 0
        for db in dbs:
            for rec in db.records:
                desc = rec.get_field("DESC")

                if desc is not None:
                    # remove macros
                    desc = re.sub(r'\$\([^)]*\)', '', desc)

                    if len(desc) > 40:
                        err += 1
                        print "ERROR: Description too long on " + err_src_fmt(db, rec)

        self.assertEqual(err, 0, msg="Overly long description in project")

    def allowed_unit(self, unit):
        """
        This method checks that the given unit conforms to standard
        """
        # expand macro $(A) to a valid unit, expand $(A=B) to B
        u = re.sub(r'\$[({].*?=(.*)?[})]', r'\1', unit)
        u = re.sub(r'\$[({].*?[})]', 'm', u)

        # split unit amalgamations
        units = re.split(r'[/ ()]', u)

        for u in units:
            # remove any powers of units e.g. mm^2 -> mm 
            u = re.sub(r'^([a-zA-Z]+)\^[-]?\d', r'\1', u, 1)
            if not (u in allowed_units):
                # may be prefixed
                if not ( (u[0] in allowed_units_prefixes) and (u[1:] in allowed_units) ):
                    return False

        return True

    def test_units_valid(self):
        """
        This method loops through all found records and finds the unique units. It then checks these units are standard
        """

        # Holds the records sorted by unit
        saved_units = dict()
        invalid = 0

        for db in dbs:
            for rec in db.records:
                unit = rec.get_field("EGU")

                # add the units to the appropriate place in the dictionary
                if unit is not None and unit != "":
                    if unit in saved_units:
                        saved_units[unit] += 1
                    else:
                        saved_units[unit] = 1
                    if not self.allowed_unit(unit):
                        invalid += 1
                        try:
                            unicode(str(unit), 'ascii')
                        except UnicodeDecodeError:
                            str_unit = ""
                        else:
                            str_unit = " (" + str(unit) + ")"

                        print "ERROR: Invalid units" + str_unit + " on " + err_src_fmt(db, rec)

        print "Units in project and number of instances: " + str(saved_units)

        self.assertEqual(invalid, 0, "Invalid units in project")

    def test_interest_descriptions(self):
        """
        This method checks all records marked as interesting for description fields
        """
        err = 0
        for db in dbs:
            for rec in db.records:
                if rec.is_interest() and not rec.has_field("DESC"):
                    print "ERROR: Missing description on " + err_src_fmt(db, rec)
                    err += 1

        self.assertEqual(err, 0, msg="Missing description on interesting PVs in project")

    def test_interest_syntax(self):
        """
        This method tests that all interesting PVs that are not in the names exception list are capitalised and
        contain only A-Z 0-9 _ :
        """
        err = 0
        for db in dbs:
            ignore = False

            for d in ignored_names_paths:
                dir = os.sep + d + os.sep
                if dir in db.directory:
                    ignore = True

            if not ignore:
                for rec in db.records:
                    if rec.is_interest():

                        mypv = re.sub(r'\$\(.*\)', '', rec.pv)  # remove macros
                        se = re.search(r'[^\w:]', mypv)
                        if se is not None:
                            print "ERROR: " + err_src_fmt(db, rec) + " contains illegal characters"
                            err += 1
                        if len(mypv) > 0 and not mypv.isupper():
                            print "ERROR: " + err_src_fmt(db, rec) + " should be upper-case"
                            err += 1

        self.assertEqual(err, 0, msg="PV syntax incorrect")


def set_up(directories):
    """
    This set up method loads and parses the db and template files prior to testing.
    """

    global dbs

    dbs = FileHolder()

    for directory in directories:
        for file_type in ['.db', '.template']:
            dbs.load_files(directory, file_type)

    # dbs.saveChecked()

    dbs = dbs.parse_files()

    print "Number of EPICS dbs Found: " + str(len(dbs))


DEFAULT_DIRECTORY = '..\\..\\..\\test-reports'

if __name__ == '__main__':
    """
    Runs the unit tests
    """

    default_dirs = [ os.path.join('..','..','..','ioc'),
        os.path.join('..','..','..','support'), os.path.join('..','..') ]

    # Get output directory from command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output_dir', nargs=1, type=str, default=DEFAULT_DIRECTORY,
                        help='The directory to save the test reports')
    parser.add_argument('-i', '--input_dir', nargs='+', type=str, default=default_dirs,
                        help='The input directories to look for db files within')
    args = parser.parse_args()
    xml_dir = args.output_dir[0]

    # Load files
    set_up(args.input_dir)

    # Load tests
    units_suite = unittest.TestLoader().loadTestsFromTestCase(TestPVUnits)

    print "\n\n------ BEGINNING PV UNIT TESTS ------"

    ret_vals = list()
    ret_vals.append(xmlrunner.XMLTestRunner(output=xml_dir).run(units_suite).wasSuccessful())

    print "------ PV UNIT TESTS COMPLETE ------\n\n"

    # Return failure exit code if a test failed
    sys.exit(False in ret_vals)
