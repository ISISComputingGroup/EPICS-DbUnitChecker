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

# list of records that should has an ASG defined
ASG_list = {'calc'}

# list of the accepted units. Standard prefixs to these units are also accepted and checked for below
# but we need to allow 'cm' explicitly as itr is a non-standard unit prefix for metre
allowed_prefixable_units = {'A', 'angstrom', 'bar', 'bit', 'byte', 'C', 'count', 'degree', 'eV', 'frame', 'hour',
                            'Hz', 'inch', 'interrupt', 'K', 'L', 'm', 'min', 'minute', 'ohm', 'Oersted', '%',
                            'photon', 'pixel', 'radian', 's', 'torr', 'step', 'T', 'V', 'Pa', 'W'}
allowed_unit_prefixes = {'T', 'G', 'M', 'k', 'm', 'u', 'n', 'p', 'f'}
allowed_non_prefixable_units = {'cm'}

dbs = list()


def err_src_fmt(db, rec):
    """
    Create an error string for the db record and file name
    Args:
        db: db record that error was in
        rec: the record the error was in

    Returns: location of the error

    """
    return str(rec) + " in " + str(db)


class TestPVUnits(unittest.TestCase):
    """
    Test class for db records
    """

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
                    dupes = set([i for i in fields if fields.count(i) > 1])
                    print "ERROR: Multiple of the same fields " + ','.join(dupes) + " on " + err_src_fmt(db, rec)

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

    def test_interest_calc_readonly(self):
        """
        This method checks that interesting PVs that are calc fields are set to
        readonly
        """
        err = 0

        for db in dbs:
            for rec in db.records:
                if rec.is_interest() and (rec.get_type() in ASG_list):
                    value = rec.get_field("ASG")

                    if value != "READONLY":
                        err += 1
                        print "ERROR: Missing ASG on " + err_src_fmt(db, rec)

        self.assertEqual(err, 0, msg="Missing ASG on interesting calculation \
                records in project")

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

    def allowed_unit(self, raw_unit):
        """
        This method checks that the given unit conforms to standard
        """
        # expand macro $(A) to a valid unit, expand $(A=B) to B
        processed_unit = re.sub(r'\$[({].*?=(.*)?[})]', r'\1', raw_unit)
        processed_unit = re.sub(r'\$[({].*?[})]', 'm', processed_unit)

        # remove 1\ as this is ok as a unit as in 1\m but 1 on its own is not ok
        processed_unit = re.sub(r'1/', '', processed_unit)

        # split unit amalgamations and remove powers
        units_with_powers = re.split(r'[/ ()]', processed_unit)
        # allow power but not negative power so m^-1. Reason is there is no latex so 1/m is much clearer here
        units_with_blanks = [re.sub(r'^([a-zA-Z]+)\^\d$', r'\1', u, 1) for u in units_with_powers]
        units = filter(None, units_with_blanks)

        def is_standalone_unit(u):
            return u in allowed_non_prefixable_units or u in allowed_prefixable_units

        def is_prefixed_unit(u):
            return any(len(u) > len(base_unit) and
                       u[-len(base_unit):] == base_unit and
                       u[:-len(base_unit)] in allowed_unit_prefixes
                       for base_unit in allowed_prefixable_units)

        return all(is_standalone_unit(u) or is_prefixed_unit(u) for u in units)

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
                ignored_dir = os.sep + d + os.sep
                if ignored_dir in db.directory:
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

    def test_log_info_tags(self):
        """
        This method checks logging records to check that logging tags are not repeated and that the period is not
        defined in two ways.
        """

        err = 0
        dbs_by_paths = {}
        # group dbs by directory hopefully these are all the db records for one IOC
        for db in dbs:
            dbs_by_path = dbs_by_paths.get(os.path.dirname(db.directory), [])
            dbs_by_path.append(db)
            dbs_by_paths[db.directory] = dbs_by_path

        for key, dir_dbs in dbs_by_paths.iteritems():
            log_fields = {}
            logging_period = None
            for db in dir_dbs:
                for rec in db.records:
                    for info in rec.infos:

                        info_name = info.name.lower().strip('"')
                        if info_name.startswith("log"):
                            previous_source = log_fields.get(info_name, None)
                            if previous_source is not None:
                                print "ERROR: Invalid logging config: {source} repeats the log info tag " \
                                      "{tag} (originally in {orig})".format(source=err_src_fmt(db, rec), tag=info_name,
                                                                            orig=err_src_fmt(*previous_source))
                                err += 1
                            else:
                                log_fields[info_name] = (db, rec)
                        if info_name == "log_period_seconds" or info_name == "log_period_pv":
                            if logging_period is None:
                                logging_period = (db, rec)
                            else:
                                print "ERROR: Invalid logging config: {source} alters the logging period type " \
                                    "(originally in {orig})".format(source=err_src_fmt(db, rec),
                                                                    tag=info_name, orig=err_src_fmt(*logging_period))
                                err += 1

        self.assertEqual(err, 0, msg="LOG infos repeated")


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


DEFAULT_DIRECTORY = os.path.join('..', '..', '..', 'test-reports')

if __name__ == '__main__':
    """
    Runs the unit tests
    """

    default_dirs = [os.path.join('..', '..', '..', 'ioc'),
                    os.path.join('..', '..', '..', 'support'), os.path.join('..', '..')]

    # Get output directory from command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output_dir', nargs=1, type=str, default=DEFAULT_DIRECTORY,
                        help='The directory to save the test reports')
    parser.add_argument('-i', '--input_dir', nargs='+', type=str, default=default_dirs,
                        help='The input directories to look for db files within')
    args = parser.parse_args()
    xml_dir = args.output_dir[0]

    # Load files
    try:
        set_up(args.input_dir)
    except ValueError as err:
        print(err.message)
        sys.exit(False)

    # Load tests
    units_suite = unittest.TestLoader().loadTestsFromTestCase(TestPVUnits)

    print "\n\n------ BEGINNING PV UNIT TESTS ------"

    ret_vals = list()
    ret_vals.append(xmlrunner.XMLTestRunner(output=xml_dir).run(units_suite).wasSuccessful())

    print "------ PV UNIT TESTS COMPLETE ------\n\n"

    # Return failure exit code if a test failed
    sys.exit(False in ret_vals)
