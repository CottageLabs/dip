import os, shutil, datetime
from . import TestController
import xml.etree.ElementTree as etree
import dip

DIP_DIR = "dip_test_dir"

class TestConnection(TestController):
    
    def setUp(self):
        if os.path.isdir(DIP_DIR):
            shutil.rmtree(DIP_DIR)
        
    def tearDown(self):
        if os.path.isdir(DIP_DIR):
            shutil.rmtree(DIP_DIR)
    
    def test_01_create_new(self):
        # construct a new blank DIP
        d = dip.DIP(DIP_DIR)
        
        # check that all the correct files and directories have been made
        assert os.path.isdir(DIP_DIR)
        assert os.path.isfile(os.path.join(DIP_DIR, "deposit.json"))
        assert os.path.isdir(os.path.join(DIP_DIR, "metadata"))
        assert os.path.isdir(os.path.join(DIP_DIR, "history"))
        assert os.path.isdir(os.path.join(DIP_DIR, "packages"))
        assert os.path.isfile(os.path.join(DIP_DIR, "metadata", "dcterms.xml"))
        
        # check that we can retrieve the basic properties from the DIP object
        di = d.deposit_info_raw
        dc = d.dc_xml
        
        assert di is not None
        assert dc is not None
        
        # check the essential structure of the basic deposit info
        assert di['created'] is not None
        assert len(di['files']) == 0
        assert len(di['endpoints']) == 0
        assert len(di['metadata']) == 1
        
        # check the details of the created date
        created = datetime.datetime.strptime(di['created'], "%Y-%m-%dT%H:%M:%SZ")
        n = datetime.datetime.now()
        assert created <= n
        
        # check that the registered metadata file is the dcterms one
        assert di['metadata'][0]["path"] == "metadata/dcterms.xml"
        
        # check the essential structure of the basic DC
        assert dc.tag == "metadata"
        assert len(dc) == 0
        
        # cleanup after ourselves
        shutil.rmtree(DIP_DIR)
        
        
    def test_02_update_parts(self):
        # construct a new blank DIP
        d = dip.DIP(DIP_DIR)
        
        # check that we can update the deposit.json file
        n = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        nd = {
            "created" : n,
            "files" : [{"whatever" : "a file"}],
            "endpoints" : [{"endpoint" : "wibble"}],
            "metadata" : []
        }
        d.deposit_info_raw = nd
        
        di = d.deposit_info_raw
        assert di['created'] == n
        assert len(di['files']) == 1
        assert len(di['endpoints']) == 1
        assert len(di['metadata']) == 0
        
        # check that we can update the dc xml file
        nm = etree.Element("other")
        etree.SubElement(nm, "sub")
        d.dc_xml = nm
        
        dc = d.dc_xml
        assert dc.tag == "other"
        assert len(dc) == 1
        
        # cleanup after ourselves
        shutil.rmtree(DIP_DIR)
    
    def test_03_init_existing(self):
        # construct a new blank DIP
        d = dip.DIP(DIP_DIR)
        
        # update the deposit.json file
        n = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        nd = {
            "created" : n,
            "files" : [{"whatever" : "a file"}],
            "endpoints" : [{"endpoint" : "wibble"}],
            "metadata" : []
        }
        d.deposit_info_raw = nd
        
        # update the dc xml file
        nm = etree.Element("other")
        etree.SubElement(nm, "sub")
        d.dc_xml = nm
        
        # now construct another deposit object over the same directory
        d2 = dip.DIP(DIP_DIR)
        
        di = d2.deposit_info_raw
        assert di['created'] == n
        assert len(di['files']) == 1
        assert len(di['endpoints']) == 1
        assert len(di['metadata']) == 0
        
        dc = d2.dc_xml
        assert dc.tag == "other"
        
        
        assert len(dc) == 1
        
