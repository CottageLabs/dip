import os, shutil, datetime, time
from . import TestController
#import xml.etree.ElementTree as etree
from lxml import etree
import dip

DIP_DIR = "dip_test_dir"
PRES_DIR = "dip_preserve_dir"
RESOURCES = os.path.join("tests", "resources")
TESTFILE_MD5 = "6fd9af1196c0f77e463bf2dcfdbef852"
TESTFILE2_MD5 = "8a86db9c36f1f7a0d8905afe3649b886"

class TestConnection(TestController):
    
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
        # os.rename(DIP_DIR, PRES_DIR)
    
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
        
    
    def test_04_endpoint(self):
        # a blank endpoint
        e = dip.Endpoint()
        assert e.id is not None
        assert len(e.raw.keys()) == 1
        
        # an endpoint with its properties (except id)
        e = dip.Endpoint(sd_iri="sd", col_iri="col", package="package", username="un", obo="obo")
        assert e.sd_iri == "sd"
        assert e.col_iri == "col"
        assert e.package == "package"
        assert e.username == "un"
        assert e.obo == "obo"
        assert e.id is not None
        
        # an endpoint with all its properties, including id
        e = dip.Endpoint(sd_iri="sd", col_iri="col", package="package", username="un", obo="obo", id="1234")
        assert e.sd_iri == "sd"
        assert e.col_iri == "col"
        assert e.package == "package"
        assert e.username == "un"
        assert e.obo == "obo"
        assert e.id == "1234"
        
        raw = e.raw
        
        assert raw['sd_iri'] == "sd"
        assert raw['col_iri'] == "col"
        assert raw['package'] == "package"
        assert raw['username'] == "un"
        assert raw['obo'] == "obo"
        assert raw['id'] == "1234"
    
    def test_05_set_endpoint(self):
        # a fully populated endpoint
        e = dip.Endpoint(sd_iri="sd", col_iri="col", package="package", username="un", obo="obo")
        
        # a deposit object we can work with
        d = dip.DIP(DIP_DIR)

        # set the endpoint directly
        e2 = d.set_endpoint(endpoint=e)
        
        assert e2.id is not None
        assert e2.col_iri == e.col_iri
        assert e2.sd_iri == e.sd_iri
        assert e2.package == e.package
        assert e2.username == e.username
        assert e2.obo == e.obo
        
        assert len(d.deposit_info_raw['endpoints']) == 1
        assert d.deposit_info_raw['endpoints'][0]['col_iri'] == "col"
        
        # set an endpoint by parameters
        d.set_endpoint(sd_iri="sd2", col_iri="col2", package="package2", username="un2", obo="obo2")
        
        assert len(d.deposit_info_raw['endpoints']) == 2
        assert d.deposit_info_raw['endpoints'][1]['col_iri'] == "col2"
        
        # set an endpoint with conflicting parameters
        e = dip.Endpoint(sd_iri="sd3", col_iri="col3", package="package3", username="un3", obo="obo3")
        e3 = d.set_endpoint(endpoint=e, sd_iri="sd4")
        
        assert e3.sd_iri == "sd3"
        
    def test_06_replace_endpoint(self):
        # a fully populated endpoint
        e = dip.Endpoint(sd_iri="sd", col_iri="col", package="package", username="un", obo="obo")
        
        # a deposit object we can work with
        d = dip.DIP(DIP_DIR)

        # set the endpoint directly
        e2 = d.set_endpoint(endpoint=e)
        
        # a replacement endpoint
        e3 = dip.Endpoint(sd_iri="sd3", col_iri="col3", package="package3", username="un3", obo="obo3", id=e2.id)
        
        # replace the endpoint
        d.set_endpoint(endpoint=e3)
        
        assert len(d.deposit_info_raw['endpoints']) == 1
        assert d.deposit_info_raw['endpoints'][0]['col_iri'] == "col3"
    
    def test_07_get_endpoint(self):
        # a fully populated endpoint
        e = dip.Endpoint(sd_iri="sd", col_iri="col", package="package", username="un", obo="obo")
        
        # a deposit object we can work with
        d = dip.DIP(DIP_DIR)

        # set the endpoint directly
        e2 = d.set_endpoint(endpoint=e)
        
        es = d.get_endpoints()
        assert len(es) == 1
        assert es[0].sd_iri == "sd"
        
        e3 = d.get_endpoint(e2.id)
        assert e3.col_iri == "col"
        
        # cleanup after ourselves
        self._cleanup()
        
    def test_08_remove_endpoint(self):
        # a fully populated endpoint
        e = dip.Endpoint(sd_iri="sd", col_iri="col", package="package", username="un", obo="obo")
        
        # a deposit object we can work with
        d = dip.DIP(DIP_DIR)

        # set the endpoint directly
        e2 = d.set_endpoint(endpoint=e)
        
        assert d.get_endpoint(e2.id) is not None
        
        # now remove the endpoint by id
        d.remove_endpoint(e2.id)
        
        assert d.get_endpoint(e2.id) is None
        
    def test_09_remove_endpoint_errors(self):
        # a fully populated endpoint
        e = dip.Endpoint(sd_iri="sd", col_iri="col", package="package", username="un", obo="obo")
        
        # a deposit object we can work with
        d = dip.DIP(DIP_DIR)

        # set the endpoint directly
        e2 = d.set_endpoint(endpoint=e)
        
        with self.assertRaises(NotImplementedError):
            d.remove_endpoint(e2.id, True)
    
    def test_10_init_errors(self):
        # try and create a DIP on a path which is actually a file
        f = open(DIP_DIR, "wb")
        f.write("file")
        f.close()
        with self.assertRaises(dip.InitialiseException):
            d = dip.DIP(DIP_DIR)
        self._cleanup()
        
        # try and create a dip where the deposit.json file is actually a directory
        os.makedirs(os.path.join(DIP_DIR, "deposit.json"))
        with self.assertRaises(dip.InitialiseException):
            d = dip.DIP(DIP_DIR)
        
    def test_11_add_file_not_exists(self):
        d = dip.DIP(DIP_DIR)
        with self.assertRaises(dip.InitialiseException):
            d.set_file("wibble")
        
    def test_12_add_new_file(self):
        # first let's add and check a new file
        d = dip.DIP(DIP_DIR)
        testfile = os.path.join(RESOURCES, "testfile.txt")
        d.set_file(testfile)
        
        assert len(d.deposit_info_raw['files']) == 1
        
        fr = d.deposit_info_raw['files'][0]
        
        assert fr['path'] == os.path.join("..", testfile)
        assert fr['md5'] == TESTFILE_MD5
        
        created = datetime.datetime.strptime(fr['added'], "%Y-%m-%dT%H:%M:%SZ")
        updated = datetime.datetime.strptime(fr['added'], "%Y-%m-%dT%H:%M:%SZ")
        n = datetime.datetime.now()
        assert created <= n
        assert updated <= n
        assert updated == created
        
        # try adding the same file again, which will hopefully have no particular effect
        d.set_file(testfile)
        
        assert len(d.deposit_info_raw['files']) == 1
        
        fr = d.deposit_info_raw['files'][0]
        
        assert fr['path'] == os.path.join("..", testfile) # the path should have been transformed in this way
        assert fr['md5'] == TESTFILE_MD5
        
        created = datetime.datetime.strptime(fr['added'], "%Y-%m-%dT%H:%M:%SZ")
        updated = datetime.datetime.strptime(fr['added'], "%Y-%m-%dT%H:%M:%SZ")
        n = datetime.datetime.now()
        assert created <= n
        assert updated <= n
        assert updated == created
        
        # now try adding a new file
        tf2 = os.path.join(RESOURCES, "testfile2.txt")
        d.set_file(tf2)
        
        assert len(d.deposit_info_raw['files']) == 2
        
        fr = d.deposit_info_raw['files'][1]
        
        assert fr['path'] == os.path.join("..", tf2)
        assert fr['md5'] == TESTFILE2_MD5
    
    def test_13_get_files(self):
        d = dip.DIP(DIP_DIR)
        testfile = os.path.join(RESOURCES, "testfile.txt")
        d.set_file(testfile)
        tf2 = os.path.join(RESOURCES, "testfile2.txt")
        d.set_file(tf2)
        
        files = d.get_files()
        assert len(files) == 2
        for f in files:
            assert f.path in [os.path.abspath(testfile), os.path.abspath(tf2)]
            assert f.md5 in [TESTFILE_MD5, TESTFILE2_MD5]
    
    def test_14_update_existing_file(self):
        d = dip.DIP(DIP_DIR)
        testfile = os.path.join(RESOURCES, "testfile.txt")
        d.set_file(testfile)
        
        # now, let's exchange testfile.txt for testfile2.txt
        self._update_file()
        
        # now add the new file, and check that the item gets updated
        d.set_file(testfile)
        
        # now make some assertions
        f = d.get_file(testfile)
        assert f.path == os.path.abspath(testfile)
        assert f.md5 == TESTFILE2_MD5
    
    def test_15_remove_file(self):
        d = dip.DIP(DIP_DIR)
        testfile = os.path.join(RESOURCES, "testfile.txt")
        d.set_file(testfile)
        
        assert len(d.get_files()) == 1
        
        d.remove_file(testfile)
        
        assert len(d.get_files()) == 0
        
        d.set_file(testfile)
        tf2 = os.path.join(RESOURCES, "testfile2.txt")
        d.set_file(tf2)
        
        assert len(d.get_files()) == 2
        
        d.remove_file(tf2)
        
        fs = d.get_files()
        assert len(fs) == 1
        assert fs[0].path == os.path.abspath(testfile)
        assert fs[0].md5 == TESTFILE_MD5
        
    def test_16_empty_deposit_state(self):
        d = dip.DIP(DIP_DIR)
        ds = d.get_state()
        assert len(ds.states) == 0
        
    def test_17_ds_files_no_endpoints(self):
        d = dip.DIP(DIP_DIR)
        testfile = os.path.join(RESOURCES, "testfile.txt")
        d.set_file(testfile)
        tf2 = os.path.join(RESOURCES, "testfile2.txt")
        d.set_file(tf2)
        
        ds = d.get_state()
        assert len(ds.states) == 2, len(ds.states)
        
        # expected states:
        # - 2 x NO_ACTION
        for state, file_record, endpoint_record in ds.states:
            assert state == dip.DepositState.NO_ACTION
            assert endpoint_record is None
        
    def test_18_ds_endpoints_no_files(self):
        d = dip.DIP(DIP_DIR)
        e1 = dip.Endpoint(sd_iri="sd", col_iri="col", package="package", username="un", obo="obo")
        d.set_endpoint(endpoint=e1)
        e2 = dip.Endpoint(sd_iri="sd2", col_iri="col2", package="package2", username="un2", obo="obo2")
        d.set_endpoint(endpoint=e2)
        
        ds = d.get_state()
        assert len(ds.states) == 0        
    
    def test_19_ds_new_files_with_endpoints(self):
        d = dip.DIP(DIP_DIR)
        
        testfile = os.path.join(RESOURCES, "testfile.txt")
        d.set_file(testfile)
        tf2 = os.path.join(RESOURCES, "testfile2.txt")
        d.set_file(tf2)
        
        e1 = dip.Endpoint(sd_iri="sd", col_iri="col", package="package", username="un", obo="obo")
        d.set_endpoint(endpoint=e1)
        e2 = dip.Endpoint(sd_iri="sd2", col_iri="col2", package="package2", username="un2", obo="obo2")
        d.set_endpoint(endpoint=e2)
        
        ds = d.get_state()
        
        # one state per endpoint
        assert len(ds.states) == 4, len(ds.states)
        
        count = 0
        for state, file_record, endpoint_record in ds.states:
            if endpoint_record.endpoint.sd_iri == "sd":
                if file_record.path == os.path.abspath(testfile):
                    assert state == dip.DepositState.NOT_DEPOSITED
                    count += 1
                elif file_record.path == os.path.abspath(tf2):
                    assert state == dip.DepositState.NOT_DEPOSITED
                    count += 1
            elif endpoint_record.endpoint.sd_iri == "sd2":
                if file_record.path == os.path.abspath(testfile):
                    assert state == dip.DepositState.NOT_DEPOSITED
                    count += 1
                elif file_record.path == os.path.abspath(tf2):
                    assert state == dip.DepositState.NOT_DEPOSITED
                    count += 1
        # make sure we checked them all
        assert count == 4
    
    def test_20_ds_modified_file_no_endpoints(self):
        d = dip.DIP(DIP_DIR)
        
        testfile = os.path.join(RESOURCES, "testfile.txt")
        d.set_file(testfile)
        tf2 = os.path.join(RESOURCES, "testfile2.txt")
        d.set_file(tf2)
        
        # we want to wait a moment to make sure that we can tell the difference between
        # the added and updated timestamps
        time.sleep(2)
        
        # now, let's update the first test file
        self._update_file()
        
        ds = d.get_state()
        
        assert len(ds.states) == 2 # expect one state per file
        
        # now we expect the file records to have been updated
        fr = d.get_file(testfile)
        assert fr.path == os.path.abspath(testfile)
        assert fr.md5 == TESTFILE2_MD5
        assert fr.updated > fr.added
        
    def test_21_ds_modified_file_with_endpoints(self):
        d = dip.DIP(DIP_DIR)
        
        testfile = os.path.join(RESOURCES, "testfile.txt")
        d.set_file(testfile)
        tf2 = os.path.join(RESOURCES, "testfile2.txt")
        d.set_file(tf2)
        
        e1 = dip.Endpoint(sd_iri="sd", col_iri="col", package="package", username="un", obo="obo")
        d.set_endpoint(endpoint=e1)
        e2 = dip.Endpoint(sd_iri="sd2", col_iri="col2", package="package2", username="un2", obo="obo2")
        d.set_endpoint(endpoint=e2)
        
        # now mark each of the files as being deposited into each of the endpoints
        for fr in d.get_files():
            fr._mark_deposited(e1.id)
            fr._mark_deposited(e2.id)
        
        # we want to wait a moment to make sure that we can tell the difference between
        # the added and updated timestamps
        time.sleep(2)
        
        # now, let's update the first test file
        self._update_file()
        
        ds = d.get_state()
        
        assert len(ds.states) == 4 # one per file per endpoint
        
        count = 0
        for state, file_record, endpoint_record in ds.states:
            if endpoint_record.endpoint.sd_iri == "sd":
                if file_record.path == os.path.abspath(testfile):
                    assert state == dip.DepositState.OUT_OF_DATE
                    count += 1
                elif file_record.path == os.path.abspath(tf2):
                    assert state == dip.DepositState.UP_TO_DATE
                    count += 1
            elif endpoint_record.endpoint.sd_iri == "sd2":
                if file_record.path == os.path.abspath(testfile):
                    assert state == dip.DepositState.OUT_OF_DATE
                    count += 1
                elif file_record.path == os.path.abspath(tf2):
                    assert state == dip.DepositState.UP_TO_DATE
                    count += 1
        # make sure we checked them all
        assert count == 4
        
    def test_22_empty_dc(self):
        d = dip.DIP(DIP_DIR)
        
        # check that there are currently no dc values, via direct access of the metadata file
        mdfs = d.get_metadata_files()
        assert len(mdfs) == 1
        
        # file path checks
        p = mdfs[0].path
        assert p.endswith("dcterms.xml")
        
        # check that the file is empty
        with open(p) as f:
           doc = etree.parse(f)
        xml = doc.getroot()
         
        assert len(xml.getchildren()) == 0
        
    def test_23_add_dc(self):
        d = dip.DIP(DIP_DIR)
        
        d.add_dublin_core("identifier", "123456")
        d.add_dublin_core("title", "A title", "en")
        d.add_dublin_core("title", "Titlen", "no")
        d.add_dublin_core("creator", "Richard")
        
        mdfs = d.get_metadata_files()
        assert len(mdfs) == 1
        
        mdf = d.get_metadata_file("dcterms")
        assert mdf is not None
        
        # check that the file contains the correct xml
        with open(mdf.path) as f:
           doc = etree.parse(f)
        xml = doc.getroot()
        
        assert len(xml.getchildren()) == 4
        
        count = 0
        for child in xml:
            if child.tag.endswith("identifier"):
                assert child.text == "123456"
                count += 1
            if child.tag.endswith("title"):
                if child.get("{http://www.w3.org/XML/1998/namespace}lang") == "en":
                    assert child.text == "A title"
                    count += 1
                if child.get("{http://www.w3.org/XML/1998/namespace}lang") == "no":
                    assert child.text == "Titlen"
                    count += 1
            if child.tag.endswith("creator"):
                assert child.text == "Richard"
                count += 1
        assert count == 4, count
        
    def test_24_add_retrieve_dc(self):
        # add dc values and then retrieve through the get_dc method
        d = dip.DIP(DIP_DIR)
        
        d.add_dublin_core("identifier", "123456")
        d.add_dublin_core("title", "A title", "en")
        d.add_dublin_core("title", "Titlen", "no")
        d.add_dublin_core("creator", "Richard")
        
        # try to get all the dc values
        a = d.get_dublin_core()
        assert len(a) == 4
        count = 0
        for dcterm, value, lang in a:
            if dcterm == "identifier":
                assert value == "123456"
                assert lang is None
                count += 1
            if dcterm == "title":
                if lang == "en":
                    assert value == "A title"
                    count += 1
                elif lang == "no":
                    assert value == "Titlen"
                    count += 1
            if dcterm == "creator":
                assert value == "Richard"
                assert lang is None
                count += 1
        assert count ==  4, count
        
        # now try to get them individually
        b = d.get_dublin_core("identifier")
        assert len(b) == 1
        assert b[0][0] == "identifier", b[0]
        assert b[0][1] == "123456"
        assert b[0][2] is None
        
        c = d.get_dublin_core("title", None, "en")
        assert len(c) == 1
        assert c[0][0] == "title"
        assert c[0][1] == "A title"
        assert c[0][2] == "en"
        
        e = d.get_dublin_core(dcterm="title", lang="no")
        assert len(e) == 1
        
        f = d.get_dublin_core(value="Richard")
        assert len(f) == 1
    
    def test_25_add_remove_dc(self):
        d = dip.DIP(DIP_DIR)
        
        d.add_dublin_core("identifier", "123456")
        d.add_dublin_core("title", "A title", "en")
        d.add_dublin_core("title", "Titlen", "no")
        d.add_dublin_core("creator", "Richard")
        
        # try to get all the dc values
        a = d.get_dublin_core()
        assert len(a) == 4
        
        # now remove one of the values
        d.remove_dublin_core("identifier")
        
        a = d.get_dublin_core()
        assert len(a) == 3
        for dcterm, value, lang in a:
            assert dcterm in ["title", "creator"]
        
        # now remove another value by two fields
        d.remove_dublin_core(dcterm="title", lang="en")
        
        a = d.get_dublin_core()
        assert len(a) == 2
        for dcterm, value, lang in a:
            assert lang in [None, "no"]
        
        # and another by value
        d.remove_dublin_core(value="Richard")
        
        a = d.get_dublin_core()
        assert len(a) == 1
        assert a[0][0] == "title"
        assert a[0][1] == "Titlen"
        assert a[0][2] == "no"
        
        # finally remove all remaining dublin core
        d.remove_dublin_core()
        a = d.get_dublin_core()
        assert len(a) == 0
