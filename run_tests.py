import unittest
import time
import xmlrunner
import argparse
import re
import sys
import os

from utils.tests.test_db_checks import TestDbChecks
from tests.pv_unit_tests import TestPVUnits
from utils.loader import parsed_files


DEFAULT_DIRECTORY = os.path.join('..', '..', '..', 'test-reports')

def set_up(directories):
    """
    This set up method generates parsed DB and template files.
    """
    for directory in directories:
        for parsed_file in parsed_files(directory, ['.db', '.template']):
            yield parsed_file

def suite():
    return unittest.TestLoader().discover(os.path.join("utils", "tests"))


def run_own_unit_tests():

    #want to run the test using /test as the input and output directory.

    #these were used by Dom to run the unit tests..
    runner = unittest.TextTestRunner()
    runner.run(suite())
    
def run_system_tests(xml_dir, input_dir):

    start = time.time()
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    print("Scanning files...")
    for db in set_up(input_dir):
        suite.addTests([TestPVUnits(test, db) for test in loader.getTestCaseNames(TestPVUnits)])

    print("Beginning PV unit tests...")

    success = xmlrunner.XMLTestRunner(output=xml_dir).run(suite).wasSuccessful()

    print("PV unit tests complete (Took {:.3f} sec)".format(time.time() - start))

    return success

def run_all_tests():
    pass

def main():

    default_dirs = [os.path.join('..', '..', '..', 'ioc'),
                    os.path.join('..', '..', '..', 'support'), os.path.join('..', '..')]

    # Get output directory from command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output_dir', nargs=1, type=str, default=DEFAULT_DIRECTORY,
                        help='The directory to save the test reports')
    parser.add_argument('-i', '--input_dir', nargs='+', type=str, default=default_dirs,
                        help='The input directories to look for db files within')
    args = parser.parse_args()

    #just try and get system tests running again..
    system_success = run_system_tests(args.output_dir[0], args.input_dir)
    
    
    sys.exit(0 if system_success else 1)
    #unit_success = run_own_unit_tests()


if __name__ == '__main__':
    main()
  