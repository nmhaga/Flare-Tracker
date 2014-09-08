from urllib2 import Request, urlopen, URLError, HTTPError
import datetime

import src_code


def test_read_solarsoft_data():
    with open('sample_url.html', 'r') as sample_file:
        result = src_code.read_solarsoft_data(sample_file)
    # Test length
    assert len(result) == 6
    # Test start time
    assert result[0][0] == datetime.datetime(2014,9,2,0,8,0)
    assert result[-1][0] == datetime.datetime(2014, 9, 2,20,56,0)
    # Test Peak
    assert result[0][1] == datetime.datetime(2014,9,2,0,16,0)
    assert result[1][1] == datetime.datetime(2014,9,2,0,16,0)
    # Test GOES_flare
    assert result[0][2] == src_code.convert_flare_format_into_decimal('C2.3')
    assert result[2][2] == src_code.convert_flare_format_into_decimal('C2.6')
    # Test DerivedPosition
    assert result[0][3].strip() == 'N06W80'
    assert result[3][3].strip() == 'S14W05'
    # Test NewR
    assert result[0][4] == '2149'
    assert result[4][4] == '2152'
    
    
