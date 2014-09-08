import datetime

import sys
sys.path.append('../') # but pytest have to be called from test directory
# That also affect to the 'sample_url.html' file below.
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
    
def test_get_peakdate_from_startdate():
    assert  src_code.get_peakdate_from_startdate(start = "2014/01/01 00:00:00", peak = "00:06:00") == datetime.datetime(2014, 1, 1, 0,6,0)
    assert  src_code.get_peakdate_from_startdate(start = "2013/12/31 23:58:50", peak = "00:06:00") == datetime.datetime(2014, 1, 1, 0,6,0)
         
def test_generate_filename():
    assert src_code.generate_filename(date = datetime.datetime(2014,9,8), cadence=1) == "20140908_Gp_xr_1m.txt"
