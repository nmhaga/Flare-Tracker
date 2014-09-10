import datetime

import sys
sys.path.append('../') # but pytest have to be called from test directory
# That also affect to the 'sample_url.html' file below.
import src_code
import swp_database
import unittest

class test_src_code(unittest.TestCase):
    def test_True(self):
        self.assertTrue(True)
        
    def test_read_solarsoft_data(self):
        #TODO: change assertTrue to assertEqual where applicable. 
        with open('sample_url.html', 'r') as sample_file:
            result = src_code.read_solarsoft_data(sample_file)
        # Test length
        self.assertTrue(len(result) == 6)
        # Test start time
        self.assertTrue(result[0][0] == datetime.datetime(2014,9,2,0,8,0))
        self.assertTrue(result[-1][0] == datetime.datetime(2014,9,2,20,56,0))
        # Test Peak
        self.assertTrue(result[0][1] == datetime.datetime(2014,9,2,0,16,0))
        self.assertTrue(result[1][1] == datetime.datetime(2014,9,2,0,16,0))
        # Test GOES_flare
        self.assertTrue(result[0][2] == src_code.convert_flare_format_into_decimal('C2.3'))
        self.assertTrue(result[2][2] == src_code.convert_flare_format_into_decimal('C2.6'))
        # Test DerivedPosition
        #TODO: fix the code so that we don't need the .strip()
        self.assertEqual(result[0][3].strip(), 'N06W80')
        self.assertEqual(result[3][3].strip(), 'S14W05')
        # Test NewR
        self.assertTrue(result[0][4] == '2149')
        self.assertTrue(result[4][4] == '2152')
        
    def test_get_peakdate_from_startdate(self):
        self.assertTrue( src_code.get_peakdate_from_startdate(start = "2014/01/01 00:00:00", peak = "00:06:00") == datetime.datetime(2014, 1, 1, 0,6,0))
        self.assertTrue( src_code.get_peakdate_from_startdate(start = "2013/12/31 23:58:50", peak = "00:06:00") == datetime.datetime(2014, 1, 1, 0,6,0))
             
    def test_generate_filename(self):
        self.assertTrue(src_code.generate_filename(date = datetime.datetime(2014,9,8), cadence=1) == "20140908_Gp_xr_1m.txt")
        
        self.assertTrue(src_code.generate_filename(date = datetime.datetime(2014,9,8), cadence=5) == "20140908_Gp_xr_5m.txt")
        
    #test this method: goes_flare = convert_flare_format_into_decimal(goes_class)


class test_database_parts_of_src_code(unittest.TestCase):
     
    def setUp(self): 
        self.session = src_code.initialise_database()
        self.dt = datetime.datetime(1990, 9, 19, 9, 19)
        
    def tearDown(self): #takes stuff out of the database. :) 
        res = self.session.query(swp_database.Solarsoft).filter(swp_database.Solarsoft.ut_datetime == self.dt).all()
        for item in res: 
            self.session.delete(item)
        self.session.commit()
        
    def test_True(self):
        self.assertTrue(True)     
        
    def test_fake_data_isnt_duplicated_in_database(self):
        resultset = [(self.dt, self.dt, 0.0001, "N19W19", 1919)]
        src_code.insert_solarsoft_data(resultset, self.session)    
        src_code.insert_solarsoft_data(resultset, self.session)
        res = self.session.query(swp_database.Solarsoft).filter(swp_database.Solarsoft.ut_datetime == self.dt).all()
        
        self.assertEqual(len(res), 1)
    
    def test_fake_data_isnt_duplicated_in_database_even_if_in_same_list(self):
        result = (self.dt, self.dt, 0.0001, "N19W19", 1919)
        resultset = [result,result] 
        src_code.insert_solarsoft_data(resultset, self.session)
        res = self.session.query(swp_database.Solarsoft).filter(swp_database.Solarsoft.ut_datetime == self.dt).all()
        
        self.assertEqual(len(res), 1)
        
if __name__ == "__main__":
    unittest.main()
        
