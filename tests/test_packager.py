from . import TestController

import dip
from datetime import datetime
import os, shutil, zipfile

DIP_DIR = "dip_test_dir"
PRES_DIR = "dip_preserve_dir"
RESOURCES = os.path.join("tests", "resources")
TESTFILE_MD5 = "6fd9af1196c0f77e463bf2dcfdbef852"
TESTFILE2_MD5 = "8a86db9c36f1f7a0d8905afe3649b886"

class TestPackager(TestController):
    
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
    
    def setUp(self):
        self._cleanup()
        
    def tearDown(self):
        self._cleanup()
    
    def _preserve_result(self):
        if os.path.exists(PRES_DIR):
            shutil.rmtree(PRES_DIR)
        shutil.copytree(DIP_DIR, PRES_DIR)
    
    def test_01_package_simple_zip(self):
        # build a dip to zip
        d = dip.DIP(DIP_DIR)
        d.add_dublin_core("creator", "Richard")
        testfile = os.path.join(RESOURCES, "testfile.txt")
        d.set_file(testfile)
        t2 = os.path.join(RESOURCES, "testfile2.txt")
        d.set_file(t2)
        
        path = d.package(package_format="http://purl.org/net/sword/package/SimpleZip")
        
        z = zipfile.ZipFile(path)
        contents = z.namelist()
        
        assert len(contents) == 3
        assert "dcterms.xml" in contents
        assert "testfile.txt" in contents
        assert "testfile2.txt" in contents
        
        self._preserve_result()
