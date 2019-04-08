import unittest
import mock
from utils import db_checks

class TestDbChecks(unittest.TestCase):
    def test_GIVEN_db_with_no_records_WHEN_multi_called_THEN_return_no_failure(self):
        dbs = mock.Mock()
        dbs.records = []
        failures = db_checks.get_multiple_instances(dbs)
        self.assertEqual(len(failures), 0)

    def test_GIVEN_db_with_multiple_pvs_WHEN_called_THEN_return_no_success(self):
        pass
    
    def test_GIVEN_db_with_multiple_properties_on_pv_WHEN_called_then_return_failure(self):
        pass
    
    def test_GIVEN_db_with_single_properties_on_pvs_WHEN_called_then_return_no_failure(self):
        pass

    def test_GIVEN_db_with_interesting_pvs_with_no_units_WHEN_called_then_return_failure(self):
        pass

    def test_GIVEN_db_with_interesting_pvs_with_units_WHEN_called_then_return_no_failure(self):
        pass

    def test_GIVEN_db_with_interesting_calc_set_as_readonly_WHEN_called_then_return_no_failure(self):
        pass

    def test_GIVEN_db_with_interesting_calc_not_set_as_readonly_WHEN_called_then_return_failure(self):
        pass

    def test_GIVEN_db_with_pv_desc_length_greater_than_40_WHEN_called_then_return_failure(self):
        pass

    def test_GIVEN_db_with_pv_desc_length_40_or_less_WHEN_called_then_return_no_failure(self):
        pass
    
    def test_GIVEN_db_with_invalid_units_WHEN_called_then_return_failure(self):
        pass

    def test_GIVEN_db_with_valid_units_WHEN_called_then_return_no_failure(self):
        pass

    def test_GIVEN_db_with_desc_on_interesting_records_WHEN_called_then_return_no_failure(self):
        pass

    def test_GIVEN_db_with_no_desc_on_interesting_records_WHEN_called_then_return_failure(self):
        pass

    def test_GIVEN_db_with_correct_syntax_on_interesting_records_WHEN_called_then_return_no_failure(self):
        pass

    def test_GIVEN_db_with_incorrect_syntax_on_interesting_records_WHEN_called_then_return_failure(self):
        pass  

    def test_GIVEN_db_with_unique_logging_tags_and_period_WHEN_called_then_return_no_failure(self):
        pass

    def test_GIVEN_db_with_repeated_logging_tags_and_period_WHEN_called_then_return_failure(self):
        pass            
    """  
    def test_GIVEN_db    
        This method checks that no PVs have duplicate fields
    """