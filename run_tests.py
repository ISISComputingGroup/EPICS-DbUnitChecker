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

def run_own_unit_tests(xml_dir):

    print("Running self-tests...")
    suite = unittest.TestLoader().discover(os.path.join("utils", "tests"))
    return xmlrunner.XMLTestRunner(output=str(xml_dir), stream=sys.stdout).run(suite).wasSuccessful()

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

def run_all_tests(xml_dir, input_dir):
    
    if not run_own_unit_tests(xml_dir):
        return False
    
    return run_system_tests(xml_dir, input_dir)
        
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

    xml_dir = args.output_dir[0]
    success = run_all_tests(xml_dir, args.input_dir)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
  