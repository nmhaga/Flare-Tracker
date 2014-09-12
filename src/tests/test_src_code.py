from datetime import datetime

import sys
sys.path.append('../') # but pytest have to be called from test directory
# That also affect to the 'sample_url.html' file below.
import src_code
from swp_database import Solarsoft, Xrayflux
import unittest

class test_src_code(unittest.TestCase):
    def test_True(self):
        self.assertTrue(True)
        
    def test_read_solarsoft_data(self):
        with open('sample_url.html', 'r') as sample_file:
            result = src_code.read_solarsoft_data(sample_file)
        
        # Test length
        self.assertEqual(len(result), 6)
        
        # Test start time
        Start_dt1 = datetime(2014,9,2,0,8,0)
        Start_dt2 = datetime(2014,9,2,20,56,0)
        self.assertEqual(result[0].ut_datetime, Start_dt1)
        self.assertEqual(result[-1].ut_datetime, Start_dt2)
        
        # Test Peak
        peak_dt1 = datetime(2014,9,2,0,16,0)
        peak_dt2 = datetime(2014,9,2,0,16,0)
        self.assertEqual(result[0].peak, peak_dt1)
        self.assertEqual(result[1].peak, peak_dt2)
 
        # Test DerivedPosition
        expectedPos1 = 'N06W80'
        expectedPos2 = 'S14W05'
        self.assertEqual(result[0].derived_position, expectedPos1)
        self.assertEqual(result[3].derived_position, expectedPos2)
        
        # Test NewR
        expectedReg1 = '2149'
        expectedReg2 = '2152'
        self.assertEqual(result[0].region, expectedReg1)
        self.assertEqual(result[4].region, expectedReg2)
    
        
    def test_get_peakdate_from_startdate(self):
        start_value = "2013/12/31 23:58:50"
        peak_value = "00:06:00"
        expected = datetime(2014, 1, 1, 0,6,0)
        self.assertEqual(src_code.get_peakdate_from_startdate(start=start_value, peak=peak_value), expected)
             
    def test_generate_filename(self):
        self.assertEqual(src_code.generate_filename(date=datetime(2014,9,8), cadence=1), "20140908_Gp_xr_1m.txt")
        
        self.assertEqual(src_code.generate_filename(date=datetime(2014,9,8), cadence=5), "20140908_Gp_xr_5m.txt")
        
    #test this method: goes_flare = convert_flare_format_into_decimal(goes_class)
    def test_convert_flare_format_into_decimal(self):
        testvalue = src_code.convert_flare_format_into_decimal('C2.3')
        expectedvalue = 2.2999999999999996e-06
        
        self.assertEqual(testvalue, expectedvalue)
     
class test_solarsoft_database_parts_of_src_code(unittest.TestCase):
     
    def setUp(self): 
        self.session = src_code.initialise_database()
        self.dt = datetime(1990, 9, 19, 9, 19)
        
    def tearDown(self): #takes stuff out of the database. :) 
        res = self.session.query(Solarsoft).filter(Solarsoft.ut_datetime == self.dt).all()  
        for item in res: 
            self.session.delete(item)
        self.session.commit()
        
    def test_True(self):
        self.assertTrue(True)     
        
    def test_fake_data_isnt_duplicated_in_database(self):
        resultset = [Solarsoft(ut_datetime=self.dt, peak=self.dt, goes_class=0.0001, derived_position="N19W19", region=1919)]
        src_code.insert_solarsoft_data(resultset, self.session)    
        src_code.insert_solarsoft_data(resultset, self.session)
        res = self.session.query(Solarsoft).filter(Solarsoft.ut_datetime == self.dt).all()
        
        self.assertEqual(len(res), 1)
    
    def test_fake_data_isnt_duplicated_in_database_even_if_in_same_list(self):
    
        result = Solarsoft(ut_datetime=self.dt, peak=self.dt, goes_class=0.0001, derived_position="N19W19", region=1919)
        resultset = [result,result] 
        src_code.insert_solarsoft_data(resultset, self.session)
        res = self.session.query(Solarsoft).filter(Solarsoft.ut_datetime == self.dt).all()
        
        self.assertEqual(len(res), 1)

class test_XrayFlux_database_parts_of_src_code(unittest.TestCase):
     
    def setUp(self): 
        self.session = src_code.initialise_database()
        self.dt = datetime(1990, 9, 19, 9, 19)
        
    def tearDown(self): #takes stuff out of the database. :) 
        res = self.session.query(Xrayflux).filter(Xrayflux.ut_datetime == self.dt).all()  
        for item in res: 
            self.session.delete(item)
        self.session.commit()
        
    def test_True(self):
        self.assertTrue(True)     
        
    def test_fake_XR_data_isnt_duplicated_in_database(self):
        resultset = [Xrayflux(ut_datetime=self.dt, longx=float(9.79e-07), short=float(1.39e-08))]
        src_code.insert_xrayflux_data(resultset, self.session)    
        src_code.insert_xrayflux_data(resultset, self.session)
        res = self.session.query(Xrayflux).filter(Xrayflux.ut_datetime == self.dt).all()
        
        self.assertEqual(len(res), 1)
    
    def test_fake_XR_data_isnt_duplicated_in_database_even_if_in_same_list(self):
    
        result = Xrayflux(ut_datetime=self.dt, longx=float(9.79e-07), short=float(1.39e-08))
        resultset = [result,result] 
        src_code.insert_xrayflux_data(resultset, self.session)
        res = self.session.query(Xrayflux).filter(Xrayflux.ut_datetime == self.dt).all()
        
        self.assertEqual(len(res), 1)
        
if __name__ == "__main__":
    unittest.main()
        
