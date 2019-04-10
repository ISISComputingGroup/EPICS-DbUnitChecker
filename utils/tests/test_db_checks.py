import unittest
import mock
from utils import db_checks
from utils.EPICS_collections import Record, Db, Field

class TestDbChecks(unittest.TestCase):
    def test_GIVEN_db_with_no_records_WHEN_multi_called_THEN_return_no_failure(self):
        dbs = mock.Mock()
        dbs.records = []
        failures = db_checks.get_multiple_instances(dbs)
        self.assertEqual(len(failures), 0)

    def test_GIVEN_db_with_multiple_pvs_WHEN_called_THEN_return_failure(self):

        fields = [Field('EGU', "A"), Field('EGU', "A")]
        records = [Record('ao', 'SHOULDFAIL:MULTIPVS', None, fields), Record('ao', 'SHOULDFAIL', None, fields)]
        dbs = Db('/path', records)
        failures = db_checks.get_multiple_instances(dbs)
        self.assertNotEqual(len(failures), 0)

    def test_GIVEN_db_with_multiple_properties_on_pv_WHEN_called_then_return_failure(self):

        fields = [Field('EGU', "A"), Field('EGU', "A")]
        records = [Record('ao', 'SHOULDFAIL:MULTIPROPERTIES', None, fields)]
        dbs = Db('/path', records)
        failures = db_checks.get_multiple_properties_on_pvs(dbs)
        self.assertNotEqual(len(failures), 0)
        
    def test_GIVEN_db_with_single_properties_on_pvs_WHEN_called_then_return_no_failure(self):

        fields = [Field('EGU', "A"), Field('DESC', "This is a description")]
        records = [Record('ao', 'SHOULDFAIL:SINGLEPROPERTY', None, fields)]
        dbs = Db('/path', records)
        failures = db_checks.get_multiple_properties_on_pvs(dbs)
        self.assertEqual(len(failures), 0)
        
    def test_GIVEN_db_with_interesting_pvs_with_no_units_WHEN_called_then_return_failure(self):
  
        field = [Field('DESC', "This is a description")]
        info = [Field('INTEREST', "HIGH")]
        records = [Record('ao', 'SHOULDFAIL:NOUNITS', info, field)]
        dbs = Db('/path', records)
        failures = db_checks.get_interest_units(dbs)
        self.assertNotEqual(len(failures), 0)
        
    def test_GIVEN_db_with_interesting_pvs_with_units_WHEN_called_then_return_no_failure(self):
 
        fields = [Field('DESC', "This is a description"), Field('EGU', "A")]
        info = [Field('INTEREST', "HIGH")]
        records = [Record('ao', 'SHOULDPASS:UNITS', info, fields)]
        dbs = Db('/path', records)
        failures = db_checks.get_interest_units(dbs)
        self.assertEqual(len(failures), 0)
        
    def test_GIVEN_db_with_interesting_calc_set_as_readonly_WHEN_called_then_return_no_failure(self):
        
        fields = [Field('DESC', "This is a description"), Field('EGU', "A"), Field("ASG", "READONLY")]
        info = [Field('INTEREST', "HIGH")]
        records = [Record('calc', 'SHOULDPASS:CALCREADONLY', info, fields)]
        dbs = Db('/path', records)
        failures = db_checks.get_interest_calc_readonly(dbs)
        self.assertEqual(len(failures), 0)

    def test_GIVEN_db_with_interesting_calc_not_set_as_readonly_WHEN_called_then_return_failure(self):
        
        fields = [Field('DESC', "This is a description"), Field('EGU', "A")]
        info = [Field('INTEREST', "HIGH")]
        records = [Record('calc', 'SHOULDFAIL:ASGREADONLY', info, fields)]
        dbs = Db('/path', records)
        failures = db_checks.get_interest_calc_readonly(dbs)
        self.assertNotEqual(len(failures), 0)
        
    def test_GIVEN_db_with_pv_desc_length_greater_than_40_WHEN_called_then_return_failure(self):

        fields = [Field('DESC', "this text should be longer than 40 characters")]
        records = [Record('calc', 'SHOULDFAIL:LONGDESC', None, fields)]
        dbs = Db('/path', records)
        failures = db_checks.get_desc_length(dbs)
        self.assertNotEqual(len(failures), 0)
        
    def test_GIVEN_db_with_pv_desc_length_40_or_less_WHEN_called_then_return_no_failure(self):
        
        fields = [Field('DESC', "this text is short")]
        records = [Record('calc', 'SHOULDPASS:SHORTDESC', None, fields)]
        dbs = Db('/path', records)
        failures = db_checks.get_desc_length(dbs)
        self.assertEqual(len(failures), 0)
        
    def test_GIVEN_db_with_invalid_units_WHEN_called_then_return_failure(self):
 
        fields = [Field('EGU', "BADUNIT")]
        records = [Record('ao', 'SHOULDFAIL:BADUNIT', None, fields)]
        dbs = Db('/path', records)
        failures = db_checks.get_units_valid(dbs)
        self.assertNotEqual(len(failures), 0)
        
    def test_GIVEN_db_with_valid_units_WHEN_called_then_return_no_failure(self):
        
        fields = [Field('EGU', "A")]
        records = [Record('ao', 'SHOULDPASS:GOODUNIT', None, fields)]
        dbs = Db('/path', records)
        failures = db_checks.get_units_valid(dbs)
        self.assertEqual(len(failures), 0)
        
    def test_GIVEN_db_with_desc_on_interesting_records_WHEN_called_then_return_no_failure(self):

        fields = [Field('EGU', "A"), Field('DESC', "Test description")]
        info = [Field("INTEREST", "HIGH")]
        records = [Record('ao', 'SHOULDPASS:HASDESC', info, fields)]
        dbs = Db('/path', records)
        failures = db_checks.get_interest_descriptions(dbs)
        self.assertEqual(len(failures), 0)
        
    def test_GIVEN_db_with_no_desc_on_interesting_records_WHEN_called_then_return_failure(self):
       
        fields = [Field('EGU', "A")]
        info = [Field("INTEREST", "HIGH")]
        records = [Record('stringin', 'SHOULDFAIL:NODESC', info, fields)]
        dbs = Db('/path', records)
        failures = db_checks.get_interest_descriptions(dbs)
        self.assertNotEqual(len(failures), 0)

    def test_GIVEN_db_with_correct_syntax_on_interesting_records_WHEN_called_then_return_no_failure(self):
        
        fields = [Field('EGU', "A"), Field('DESC', "Test description")]
        info = [Field("INTEREST", "HIGH")]
        records = [Record('stringin', 'SHOULDPASS:GOODUNIT', info, fields)]
        dbs = Db('/path', records)
        failures = db_checks.get_interest_syntax(dbs)
        self.assertEqual(len(failures), 0)
        
    def test_GIVEN_db_with_incorrect_lowercase_syntax_on_interesting_records_WHEN_called_then_return_failure(self):
        fields = [Field('EGU', "A"), Field('DESC', "Test description")]
        info = [Field("INTEREST", "HIGH")]
        records = [Record('stringin', 'SHOULDFAIL:lowercase', info, fields)]
        dbs = Db('/path', records)
        failures = db_checks.get_interest_syntax(dbs)
        self.assertNotEqual(len(failures), 0)

    def test_GIVEN_db_with_incorrect_badchar_syntax_on_interesting_records_WHEN_called_then_return_failure(self):
        fields = [Field('EGU', "A"), Field('DESC', "Test description")]
        info = [Field("INTEREST", "HIGH")]
        records = [Record('stringin', 'SHOULDFAIL:b@dchar', info, fields)]
        dbs = Db('/path', records)
        failures = db_checks.get_interest_syntax(dbs)
        self.assertNotEqual(len(failures), 0)
    def test_GIVEN_db_with_unique_logging_tags_and_period_WHEN_called_then_return_no_failure(self):

        fields = [Field('DESC', "Test description")]
        info = [Field("LOG_HEADER1", "a header"), Field("LOG_periods_seconds", "another header")]
        records = [Record('ao', 'SHOULDPASS:HEADER_FIRST', info, fields)]
        dbs = Db('/path', records)
        failures = db_checks.get_log_info_tags(dbs)
        self.assertEqual(len(failures), 0)
        
    def test_GIVEN_db_with_repeated_logging_tags_and_period_WHEN_called_then_return_failure(self):
        
        fields = [Field('DESC', "Test description")]
        info = [Field("LOG_HEADER1", "a header"), Field("LOG_periods_seconds", "another header"),
                Field("LOG_HEADER1", "another header")
                ]
        records = [Record('ao', 'SHOULDFAIL:REPEAT_HEADER', info, fields)]
        dbs = Db('/path', records)
        failures = db_checks.get_log_info_tags(dbs)
        self.assertNotEqual(len(failures), 0)


    #need to come and fix this
    def test_GIVEN_db_with_repeated_period_WHEN_called_then_return_failure(self):
        
        fields = [Field('DESC', "Test description")]
        info = [Field("LOG_HEADER1", "a header"), Field("LOG_periods_seconds", "another header"),
                Field("LOG_period_pv", "another header")
                ]
        records = [Record('ao', 'SHOULDFAIL:REPEAT_PERIOD', info, fields)]
        dbs = Db('/path', records)
        failures = db_checks.get_log_info_tags(dbs)
        self.assertNotEqual(len(failures), 0)