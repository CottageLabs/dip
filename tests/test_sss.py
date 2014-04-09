from . import TestController

import dip
from datetime import datetime
import os, shutil

SSS_SD = "http://localhost:8080/sd-uri"
SSS_COL = "http://localhost:8080/col-uri/f715c580-f79a-427d-a07f-abdeb99da397"
SSS_UN = "sword"
SSS_PW = "sword"

DIP_DIR = "dip_test_dir"
PRES_DIR = "dip_preserve_dir"
RESOURCES = os.path.join("tests", "resources")
TESTFILE_MD5 = "6fd9af1196c0f77e463bf2dcfdbef852"
TESTFILE2_MD5 = "8a86db9c36f1f7a0d8905afe3649b886"

class TestSSS(TestController):
    
    def _cleanup(self):
        # cleanup the DIP directory
        if os.path.isdir(DIP_DIR):
            shutil.rmtree(DIP_DIR)
        elif os.path.isfile(DIP_DIR):
            os.remove(DIP_DIR)
        
        # some tests mess around with the test file resources, so straighten
        # things out if necessary
        temp = os.path.join(RESOURCES, "testfile.txt.bak")
        if os.path.isfile(temp):
            testfile = os.path.join(RESOURCES, "testfile.txt")
            if os.path.isfile(testfile):
                os.remove(testfile)
            os.rename(temp, testfile)
    
    def _preserve_result(self):
        if os.path.exists(PRES_DIR):
            shutil.rmtree(PRES_DIR)
        shutil.copytree(DIP_DIR, PRES_DIR)
    
    def _update_file(self):
        testfile = os.path.join(RESOURCES, "testfile.txt")
        temp = os.path.join(RESOURCES, "testfile.txt.bak")
        tf2 = os.path.join(RESOURCES, "testfile2.txt")
        os.rename(testfile, temp)
        shutil.copy(tf2, testfile)
    
    def setUp(self):
        self._cleanup()
        
    def tearDown(self):
        self._cleanup()
    
    def test_01_metadata_deposit_create(self):
        d = dip.DIP(DIP_DIR)
        
        d.add_dublin_core("identifier", "123456")
        d.add_dublin_core("title", "A title", "en")
        d.add_dublin_core("title", "Titlen", "no")
        d.add_dublin_core("creator", "Richard")
        
        sss = dip.Endpoint(sd_iri=SSS_SD, col_iri=SSS_COL, package="package", username=SSS_UN)
        d.set_endpoint(endpoint=sss)
        
        d.deposit(sss.id, metadata_only=True, user_pass=SSS_PW)
    
    def test_02_metadata_deposit_update(self):
        d = dip.DIP(DIP_DIR)
        
        d.add_dublin_core("identifier", "123456")
        d.add_dublin_core("title", "A title", "en")
        d.add_dublin_core("title", "Titlen", "no")
        d.add_dublin_core("creator", "Richard")
        
        sss = dip.Endpoint(sd_iri=SSS_SD, col_iri=SSS_COL, package="package", username=SSS_UN)
        d.set_endpoint(endpoint=sss)
        
        d.deposit(sss.id, metadata_only=True, user_pass=SSS_PW)
        
        # now update it
        d.add_dublin_core("rights", "You have none!!!!")
        d.deposit(sss.id, metadata_only=True, user_pass=SSS_PW)
    
    def test_03_deposit_simple_zip(self):
        d = dip.DIP(DIP_DIR)
        
        d.add_dublin_core("identifier", "123456")
        d.add_dublin_core("title", "A title", "en")
        d.add_dublin_core("title", "Titlen", "no")
        d.add_dublin_core("creator", "Richard")
        
        testfile = os.path.join(RESOURCES, "testfile.txt")
        d.set_file(testfile)
        t2 = os.path.join(RESOURCES, "testfile2.txt")
        d.set_file(t2)
        
        sss = dip.Endpoint(sd_iri=SSS_SD, col_iri=SSS_COL, package="http://purl.org/net/sword/package/SimpleZip", username=SSS_UN)
        d.set_endpoint(endpoint=sss)
        
        d.deposit(sss.id, user_pass=SSS_PW)
        self._preserve_result()
        
        
