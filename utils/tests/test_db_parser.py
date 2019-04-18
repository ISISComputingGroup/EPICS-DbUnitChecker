import unittest
import mock
from utils import db_parser
from utils.EPICS_collections import Record, Db, Field


class TestDbParser(unittest.TestCase):

    def test_GIVEN_db_line_with_field_in_comment_WHEN_called_THEN_return_no_failure(self):
        dummy_line =  'field(CALC, "(C=0||C=2)?A:B")  # If heater is present and switched off, display persistent field, else display PSU field'
        required_result = 'field(CALC, "(C=0||C=2)?A:B")  \n'
        actual_result = db_parser.remove_comments(dummy_line)
        self.assertEqual(required_result, actual_result)

    def test_GIVEN_db_line_with_hashtag_in_string_WHEN_called_THEN_return_no_failure(self):
        dummy_line =  'field(CALC, "(C=0||C=2)?A:#C")'
        required_result = 'field(CALC, "(C=0||C=2)?A:#C")\n'
        actual_result = db_parser.remove_comments(dummy_line)
        self.assertEqual(required_result, actual_result)

    def test_GIVEN_db_line_with_multiple_fields_in_string_WHEN_called_THEN_return_no_failure(self):
        dummy_line =  'field(CALC, "(C=0||C=2)?A:#D") #This is a comment with field in it'
        required_result = 'field(CALC, "(C=0||C=2)?A:#D") \n'
        actual_result = db_parser.remove_comments(dummy_line)
        self.assertEqual(required_result, actual_result)

    def test_GIVEN_db_line_with_commented_out_field_WHEN_called_THEN_return_no_failure(self):
        dummy_line =  '#This is a comment with field in it field(CALC, "(C=0||C=2)?A:#D") '
        required_result = '\n'
        actual_result = db_parser.remove_comments(dummy_line)
        self.assertEqual(required_result, actual_result)
    
    def test_GIVEN_db_line_with_multiple_hashtags_and_comments_WHEN_called_THEN_return_no_failure(self):
        dummy_line = 'field(CALC, "A#B?B:(A#B?A:C") # field comment'
        required_result = 'field(CALC, "A#B?B:(A#B?A:C") \n'
        actual_result = db_parser.remove_comments(dummy_line)
        self.assertEqual(required_result, actual_result)

    def test_GIVEN_text_with_multifields_WHEN_called_THEN_get_props_return_list_of_fields_no_failure(self):
        required_result = [Field('DESC', "test description"), Field("EGU", "m/s")]
        record = ('record(ao, "SHOULDPASS:m_OVER_s")\n'
        '{\n'
        'field(DESC, "test description")\n'
        'field(EGU, "m/s")\n'
        '}')
        success = True
        actual_result = db_parser._get_props('field', record)
        if actual_result is None:
            success = False
        if len(actual_result) is not len(required_result):
            success = False
        for (a,b) in zip(actual_result, required_result):
            success = success and a.name == b.name and a.value == b.value

        self.assertEqual(success, True)
      
    def test_GIVEN_text_with_field_in_string_WHEN_called_THEN_get_props_returns_no_failure(self):

        required_result = [Field('DESC', "test description"), Field("EGU", "m/s")]
        record = ('record(ao, "SHOULDPASS:m_OVER_s")\n'
        '{\n'
        '"field"(DESC, "test description")\n'
        'field(EGU, "m/s")\n'
        '}')
        success = True
        actual_result = db_parser._get_props('field', record)
        if actual_result is None:
            success = False
        if len(actual_result) is not len(required_result):
            success = False
        for (a,b) in zip(actual_result, required_result):
            success = success and a.name == b.name and a.value == b.value

        self.assertEqual(success, True)

    def test_GIVEN_text_without_keyword_WHEN_called_THEN_return_failure(self):
        
        required_result = [Field('DESC', "test description"), Field("EGU", "m/s")]
        record = ('record(ao, "SHOULDPASS:m_OVER_s")\n'
        '{\n'
        '"field"(DESC, "test description")\n'
        'field(EGU, "m/s")\n'
        '}')
        success = True
        actual_result = db_parser._get_props('info', record)
        if actual_result is None:
            success = False
        if len(actual_result) is not len(required_result):
            success = False
        for (a,b) in zip(actual_result, required_result):
            success = success and a.name == b.name and a.value == b.value
        self.assertEqual(success, False)

    def test_GIVEN_properly_formatted_record_text_WHEN_called_THEN_return_no_failure(self):

        required_result = "SHOULDPASS:m_OVER_s"
        record = 'record(ao, "SHOULD, PASS:m_OVER_s")'
        actual_result = db_parser._check_string(record)
        self.assertEqual(required_result, actual_result)

    def test_GIVEN_properly_formatted_record_text_with_commas_WHEN_called_THEN_return_no_failure(self):

        required_result = "SHOULD, (PASS:m_OVER_s)"
        record = 'record(ao, "SHOULD, (PASS:m_OVER_s)")'
        actual_result = db_parser._check_string(record)
        self.assertEqual(required_result, actual_result)
