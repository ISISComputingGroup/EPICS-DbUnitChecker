import unittest
from utils import db_checks


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


class TestPVUnits(unittest.TestCase):

    def __init__(self, methodName, db=None):
        super(TestPVUnits, self).__init__(methodName=methodName)
        self.db = db

    @ignore(["superlogics.db", "lakeshore336.db", "motor.db"], "Historical failures have not been addressed")
    @ignore(["EPICS_V4"], "Vendor-supplied DBs")
    @ignore(["DbUnitChecker"], "Contains integration tests which deliberately fail")
    def test_multiple_pvs_warning(self):
        """
        This method warns if there are multiple PVs with the same name in the project
        """
        failures = db_checks.get_multiple_instances(self.db)
        self.assertEqual(len(failures), 0, msg=db_checks.build_failure_message(
            "Multiple fields on PVs in {}".format(self.db.directory), failures))

    @ignore([
        "moxa1210_aliases.db",
        "moxa12XX_aliases.db",
        "separator_voltage.db",
        "separator_current.db",
        "isActiveEurothrm.db"
    ], "Mutually exclusive guards prevent this from ever happening")
    @ignore(["optics", "danfysikMps8000"], "Vendor-supplied DBs")
    @ignore(["Mezflipr_common.db"], "Complex macro guards cannot be understood by DbUnitChecker.")
    @ignore(["axisUtil.db", "motorUtil.db"], "Complex macro guards cannot be understood by DbUnitChecker.")
    @ignore(["DbUnitChecker"], "Contains integration tests which deliberately fail")
    def test_multiple_properties_on_pvs(self):
        """
        This method checks that interesting PVs have units
        """
        failures = db_checks.get_multiple_properties_on_pvs(self.db)
        self.assertEqual(len(failures), 0, msg=db_checks.build_failure_message(
            "Multiple fields on PVs in {}".format(self.db.directory), failures))

    @ignore(["DbUnitChecker"], "Contains integration tests which deliberately fail")
    def test_interest_units(self):
        """
        This method checks that interesting PVs have units
        """
        failures = db_checks.get_interest_units(self.db)
        self.assertEqual(len(failures), 0, msg=db_checks.build_failure_message(
            "Interesting PVs with no units in {}".format(self.db.directory), failures))

    @ignore(["DbUnitChecker"], "Contains integration tests which deliberately fail")
    def test_interest_calc_readonly(self):
        """
        This method checks that interesting PVs that are calc fields are set to
        readonly
        """
        failures = db_checks.get_interest_calc_readonly(self.db)
        self.assertEqual(len(failures), 0, msg=db_checks.build_failure_message(
            "Writable calc records in {}".format(self.db.directory), failures))

    @ignore(["DbUnitChecker"], "Contains integration tests which deliberately fail")
    def test_desc_length(self):
        """
        This method checks that the description length on all PVs is no longer than 40 chars
        """
        failures = db_checks.get_desc_length(self.db)
        self.assertEqual(len(failures), 0, msg=db_checks.build_failure_message(
            "Description too long in {}".format(self.db.directory), failures))

    @ignore(["optics", "CALab", "danfysikMps8000", "EPICS_V4", "EdwardsNextTurbo"], "Vendor-supplied DBs")
    @ignore(["ether_ip", "seq"], "Vendor-supplied DBs")
    @ignore(["isisdae.db", "qepro.template"], "Historical failures not addressed")
    @ignore(["DbUnitChecker"], "Contains integration tests which deliberately fail")
    def test_units_valid(self):
        """
        This method loops through all found records and finds the unique units. It then checks these units are standard
        """
        failures = db_checks.get_units_valid(self.db)     
        self.assertEqual(len(failures), 0, msg=db_checks.build_failure_message(
            "Invalid units in {}".format(self.db.directory), failures))

    @ignore(["DbUnitChecker"], "Contains integration tests which deliberately fail")
    def test_interest_descriptions(self):
        """
        This method checks all records marked as interesting for description fields
        """
        failures = db_checks.get_interest_descriptions(self.db)
        self.assertEqual(len(failures), 0, msg=db_checks.build_failure_message(
            "Missing description in {}".format(self.db.directory), failures))

    @ignore(["DbUnitChecker"], "Contains integration tests which deliberately fail")
    @ignore(["HVCAENx527ch.db"], "These are externally provided DBs")
    def test_interest_syntax(self):
        """
        This method tests that all interesting PVs that are not in the names exception list are capitalised and
        contain only A-Z 0-9 _ :
        """
        failures = db_checks.get_interest_syntax(self.db)
        self.assertEqual(len(failures), 0, msg=db_checks.build_failure_message(
             "PV syntax incorrect in {}".format(self.db.directory), failures))

    @ignore(["DbUnitChecker"], "Contains integration tests which deliberately fail")
    def test_log_info_tags(self):
        """
        This method checks logging records to check that logging tags are not repeated and that the period is not
        defined in two ways.
        """
        failures = db_checks.get_log_info_tags(self.db)
        self.assertEqual(len(failures), 0, msg=db_checks.build_failure_message(
            "Duplicated log infos in {}".format(self.db.directory), failures))
