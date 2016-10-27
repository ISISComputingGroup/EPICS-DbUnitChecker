import re
from EPICS_collections import Db, Record, Field


def _check_string(text):
    """
    Helper function to return the data between the next comma and closed bracket, even if it's a string containing
    commas/brackets
    """
    quote_pos = text.find('"')
    if quote_pos < text.find(')') and quote_pos != -1:
        # Data is a string
        return text.split('"')[1]
    else:
        # Data is not a string
        return re.split('[,)]', text)[1]


def _get_props(keyword, text):
    """
    This method searches for valid EPICS formatted data under the given keyword in the text, specifically
    avoiding strings containing that keyword. E.g. info and field
    A list of this data is returned.
    """
    fields = []
    while text.find(keyword) != -1:
        # check keyword is not in string
        search = re.search(r'"[^"\n]*?'+keyword+'[^"\n]*?"', text)

        if search and (search.start() < text.find(keyword)):
            # string comes first so cut it out and repeat
            text = text[search.end():]
        else:
            # info is not in a string so add to record
            text = text[text.find(keyword)+4:]
            name = re.split('[(,]', text)[1]
            val = _check_string(text)
            fields.append(Field(name, val))

    return fields


def parse_db(db_file):
        """
        This method will parse the text found in the EPICS db files to form groups of Record
        and Field instances.
        """

        text = ""
        temp_text = db_file.get_text()

        # remove comments but keep any # that appear in strings (may be able to do better in regex?)
        for line in iter(temp_text.splitlines()):
            if not (line.find('#') != -1 and (line.find('#') < line.find('"') or line.find('"') == -1)):
                # is not a comment so add to be parsed
                text += line + '\n'

        recs = []

        # cut out the text before the first record
        rec_pos = text.find("record")
        text = text[rec_pos+5:]

        while rec_pos != -1:

            # cut out record data
            rec_type = re.split('[(,]', text)[1]

            pv_name = _check_string(text)

            # cut out field data (any data between braces)
            braced_text = text[text.find('{')+1:text.find('}')]
            field_text = braced_text

            # check for info field
            infos = _get_props("info", field_text)

            # find fields
            fields = _get_props("field", field_text)

            # populate records list
            rec = Record(rec_type.strip(), pv_name, infos, fields)
            recs.append(rec)

            # find next record
            # check if the next instance of record occurs in a string

            if re.search('"[^"]*record[^"]*?"', braced_text):
                rec_pos = re.search('"[^"]*record[^"]*?"', text).end()  # find where record is used in a string
                text = text[rec_pos+5:]

            rec_pos = text.find("record")
            text = text[rec_pos+5:]

        return Db(db_file.get_dir(), recs)