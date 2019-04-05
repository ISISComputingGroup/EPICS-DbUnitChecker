"""@package docstring
This script finds all the EPICS db files in a given directory and parses the record
and field data into python classes. Arrays of Record instances can then be analysed
to find records that lack specific fields etc.
"""
import unittest

import time

from loader import parsed_files
import xmlrunner
import argparse
import re
import sys
import os
from collections import defaultdict

# list of those record types that should have a EGU field
EGU_list = {'ai', 'ao', 'calc', 'calcout', 'compress', 'dfanout', 'longin', 'longout', 'mbbo', 
            'mbboDirect', 'permissive', 'sel', 'seq', 'state', 'stringin', 'stringout', 'subArray', 
            'sub', 'waveform', 'archive', 'cpid', 'pid', 'steppermotor'}

EGU_sub_list = {'longin', 'longout', 'ai', 'ao'}

# list of records that should has an ASG defined
ASG_list = {'calc'}

# list of the accepted units. Standard prefixs to these units are also accepted and checked for below
# but we need to allow 'cm' explicitly as itr is a non-standard unit prefix for metre
allowed_prefixable_units = {'A', 'angstrom', 'au', 'bar', 'B', 'bit', 'byte', 'C', 'count', 'degree', 'eV', 'frame', 'g', 'G',
                            'hour', 'Hz', 'H', 'inch', 'interrupt', 'K', 'L', 'm', 'min', 'minute', 'ohm', 'Oersted',
                            '%', 'photon', 'pixel', 'radian', 's', 'torr', 'step', 'T', 'V', 'Pa', 'deg', 'stp', 'W'}
allowed_unit_prefixes = {'T', 'G', 'M', 'k', 'm', 'u', 'n', 'p', 'f'}
allowed_non_prefixable_units = {
    'cm',
    'cdeg'
}
allowed_standalone_units = {
    'cdeg/ss',  # Needed by the GORC. Latter is a special case because cdeg/s^2 too long}
}


def ignore(dbs, message):
    """
    Decorator to skip tests on certain DBs or paths
    Args:
        dbs: DBs or paths to skip on.
        message: skip message
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if any(db in self.db.directory for db in dbs):
                self.skipTest(message)
            func(self, *args, **kwargs)
        return wrapper
    return decorator


def build_failure_message(basemessage, submessages):
    """
    Builds a test failure message from a common descriptor and a list of individual failures.

    Args:
        basemessage: common base message
        submessages: list of submessages

    Returns:
        A formatted string containing the base and sub messages.
    """
    return "{}\n{}".format(basemessage, "\n".join("   -> " + s for s in submessages))


class TestPVUnits(unittest.TestCase):
    """
    Test class for db records
    """

    def __init__(self, methodName, db=None):
        super(TestPVUnits, self).__init__(methodName=methodName)
        self.db = db

    @ignore(["superlogics.db", "lakeshore336.db", "motor.db"], "Historical failures have not been addressed")
    @ignore(["EPICS_V4"], "Vendor-supplied DBs")
    @ignore(["DbUnitChecker"], "DB unit checker contains tests that deliberately fail, used as integration tests")
    def test_multiple_pvs_warning(self):
        """
        This method warns if there are multiple PVs with the same name in the project
        """
        failures = []

        dups = defaultdict(list)  # Makes a dict of lists
        for rec in self.db.records:
            dups[str(rec.pv)].append(rec)

        for k, v in dups.items():
            if len(v) > 1:
                failures.append("Multiple instances of {}".format(k))

        self.assertEqual(len(failures), 0, msg=build_failure_message(
            "Multiple fields on PVs in {}".format(self.db.directory), failures))

    @ignore(["moxa1210_aliases.db"], "Mutually exclusive guards prevent this from ever happening")
    @ignore(["moxa12XX_aliases.db"], "Mutually exclusive guards prevent this from ever happening")
    @ignore(["separator_voltage.db"], "Mutually exclusive guards prevent this from ever happening")
    @ignore(["separator_current.db"], "Mutually exclusive guards prevent this from ever happening")
    @ignore(["isActiveEurothrm.db"], "Mutually exclusive macro guards prevent this from ever happening")
    @ignore(["optics", "danfysikMps8000"], "Vendor-supplied DBs")
    @ignore(["DbUnitChecker"], "DB unit checker contains tests that deliberately fail, used as integration tests")
    @ignore(["Mezflipr_common.db"], "Complex macro guards cannot be understood by DbUnitChecker.")
    def test_multiple_properties_on_pvs(self):
        """
        This method checks that no PVs have duplicate fields
        """
        failures = []

        for rec in self.db.records:
            fields = rec.get_field_names()
            if len(set(fields)) != len(fields):
                dupes = set([i for i in fields if fields.count(i) > 1])
                failures.append("Multiple instances of fields {} on {}".format(','.join(dupes), rec))

        self.assertEqual(len(failures), 0, msg=build_failure_message(
            "Multiple fields on PVs in {}".format(self.db.directory), failures))

    @ignore(["DbUnitChecker"], "DB unit checker contains tests that deliberately fail, used as integration tests")
    def test_interest_units(self):
        """
        This method checks that interesting PVs have units
        """
        failures = []

        for rec in self.db.records:
            if rec.is_interest() and not rec.is_disable() and (rec.get_type() in EGU_sub_list):
                unit = rec.get_field("EGU")

                if unit is None:
                    failures.append("Missing units on {}".format(rec))

        self.assertEqual(len(failures), 0, msg=build_failure_message(
            "Interesting PVs with no units in {}".format(self.db.directory), failures))

    @ignore(["DbUnitChecker"], "DB unit checker contains tests that deliberately fail, used as integration tests")
    def test_interest_calc_readonly(self):
        """
        This method checks that interesting PVs that are calc fields are set to
        readonly
        """
        failures = []

        for rec in self.db.records:
            if rec.is_interest() and (rec.get_type() in ASG_list):
                value = rec.get_field("ASG")

                if value != "READONLY":
                    failures.append("Missing ASG on {}".format(rec))

        self.assertEqual(len(failures), 0, msg=build_failure_message(
            "Writable calc records in {}".format(self.db.directory), failures))

    @ignore(["DbUnitChecker"], "DB unit checker contains tests that deliberately fail, used as integration tests")
    def test_desc_length(self):
        """
        This method checks that the description length on all PVs is no longer than 40 chars
        """
        failures = []

        for rec in self.db.records:
            desc = rec.get_field("DESC")

            if desc is not None:
                # remove macros
                desc = re.sub(r'\$\([^)]*\)', '', desc)

                if len(desc) > 40:
                    failures.append("Description too long on {}".format(rec))

        self.assertEqual(len(failures), 0, msg=build_failure_message(
            "Description too long in {}".format(self.db.directory), failures))

    def allowed_unit(self, raw_unit):
        """
        This method checks that the given unit conforms to standard
        """
        if raw_unit in allowed_standalone_units:
            return True

        # expand macro $(A) to a valid unit, expand $(A=B) to B
        processed_unit = re.sub(r'\$[({].*?=(.*)?[})]', r'\1', raw_unit)
        processed_unit = re.sub(r'\$[({].*?[})]', 'm', processed_unit)

        # remove 1\ as this is ok as a unit as in 1\m but 1 on its own is not ok
        processed_unit = re.sub(r'1/', '', processed_unit)

        # split unit amalgamations and remove powers
        units_with_powers = re.split(r'[/ ()]', processed_unit)
        # allow power but not negative power so m^-1. Reason is there is no latex so 1/m is much clearer here
        units_with_blanks = [re.sub(r'^([a-zA-Z]+)\^[-]?\d$', r'\1', u, 1) for u in units_with_powers]
        units = filter(None, units_with_blanks)

        def is_standalone_unit(u):
            return u in allowed_non_prefixable_units or u in allowed_prefixable_units

        def is_prefixed_unit(u):
            return any(len(u) > len(base_unit) and
                       u[-len(base_unit):] == base_unit and
                       u[:-len(base_unit)] in allowed_unit_prefixes
                       for base_unit in allowed_prefixable_units)

        return all(is_standalone_unit(u) or is_prefixed_unit(u) for u in units)

    @ignore(["optics", "CALab", "DbUnitChecker", "danfysikMps8000", "EPICS_V4", "EdwardsNextTurbo"], "Vendor-supplied DBs")
    @ignore(["DbUnitChecker"], "DB unit checker contains tests that deliberately fail, used as integration tests")
    @ignore(["ether_ip"], "Vendor-supplied DBs")
    def test_units_valid(self):
        """
        This method loops through all found records and finds the unique units. It then checks these units are standard
        """
        failures = []

        for rec in self.db.records:
            unit = rec.get_field("EGU")

            if unit is not None and unit != "" and not self.allowed_unit(unit):
                failures.append("Invalid unit '{}' on {}".format(unit, rec))

        self.assertEqual(len(failures), 0, msg=build_failure_message(
            "Invalid units in {}".format(self.db.directory), failures))

    @ignore(["DbUnitChecker"], "DB unit checker contains tests that deliberately fail, used as integration tests")
    def test_interest_descriptions(self):
        """
        This method checks all records marked as interesting for description fields
        """
        failures = []

        for rec in self.db.records:
            if rec.is_interest() and not rec.has_field("DESC"):
                failures.append("Missing description on {}".format(rec))

        self.assertEqual(len(failures), 0, msg=build_failure_message(
            "Missing description in {}".format(self.db.directory), failures))

    @ignore(["HVCAENx527ch.db"], "These are externally provided DBs")
    @ignore(["DbUnitChecker"], "DB unit checker contains tests that deliberately fail, used as integration tests")
    def test_interest_syntax(self):
        """
        This method tests that all interesting PVs that are not in the names exception list are capitalised and
        contain only A-Z 0-9 _ :
        """
        failures = []

        for rec in self.db.records:
            if rec.is_interest():

                mypv = re.sub(r'\$\(.*\)', '', rec.pv)  # remove macros
                se = re.search(r'[^\w:]', mypv)
                if se is not None:
                    failures.append("{} contains illegal characters".format(rec))
                if len(mypv) > 0 and not mypv.isupper():
                    failures.append("{} should be upper-case".format(rec))

        self.assertEqual(len(failures), 0, msg=build_failure_message(
            "PV syntax incorrect in {}".format(self.db.directory), failures))

    @ignore(["DbUnitChecker"], "DB unit checker contains tests that deliberately fail, used as integration tests")
    def test_log_info_tags(self):
        """
        This method checks logging records to check that logging tags are not repeated and that the period is not
        defined in two ways.
        """
        failures = []

        dbs_by_paths = {}
        # group dbs by directory hopefully these are all the db records for one IOC
        dbs_by_path = dbs_by_paths.get(os.path.dirname(self.db.directory), [])
        dbs_by_path.append(self.db)
        dbs_by_paths[self.db.directory] = dbs_by_path

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
                                failures.append("Invalid logging config: {source} repeats the log info tag " \
                                                "{tag}".format(source=rec, tag=info_name))
                            else:
                                log_fields[info_name] = (db, rec)

                        if info_name == "log_period_seconds" or info_name == "log_period_pv":
                            if logging_period is None:
                                logging_period = (db, rec)
                            else:
                                failures.append("Invalid logging config: {source} alters the logging period " \
                                                "type".format(source=rec, tag=info_name))

        self.assertEqual(len(failures), 0, msg=build_failure_message(
            "Duplicated log infos in {}".format(self.db.directory), failures))


def set_up(directories):
    """
    This set up method generates parsed DB and template files.
    """
    for directory in directories:
        for parsed_file in parsed_files(directory, ['.db', '.template']):
            yield parsed_file


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

    start = time.time()

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    print("Scanning files...")
    for db in set_up(args.input_dir):
        suite.addTests([TestPVUnits(test, db) for test in loader.getTestCaseNames(TestPVUnits)])

    print("Beginning PV unit tests...")

    success = xmlrunner.XMLTestRunner(output=xml_dir).run(suite).wasSuccessful()

    print("PV unit tests complete (Took {:.3f} sec)".format(time.time() - start))

    # Return failure exit code if a test failed
    sys.exit(not success)
