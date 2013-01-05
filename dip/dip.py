import os, datetime, json, uuid, hashlib
import xml.etree.ElementTree as etree

def _normalise_path(path, normalise_to):
    # path may either be:
    # - relative to the cwd of the script
    # - absolute
    #
    # we want it to be relative to the self.base_dir path
    real = os.path.realpath(path)
    rel = os.path.relpath(real, normalise_to)
    return rel

def _absolute_path(rel_path, from_path):
    path = os.path.normpath(os.path.join(from_path, rel_path))
    return os.path.abspath(path)

class DIP(object):
    
    def __init__(self, base_dir):
        # ensure that the base_dir exists
        self._guarantee_directory(base_dir)
       
        # store the base_dir parameter on the object
        # NOTE: base_dir is relative to the executing script, or an absolute path
        self.base_dir = base_dir
        
        # load the deposit info (which will initialise if necessary)
        self._load_deposit_info()
        
        # ensure that the history dir exists
        history_dir = os.path.join(self.base_dir, "history")
        self._guarantee_directory(history_dir)
        
        # ensure that the packages dir exists
        packages_dir = os.path.join(self.base_dir, "packages")
        self._guarantee_directory(packages_dir)
        
        # ensure that the metadata dir exists
        metadata_dir = os.path.join(self.base_dir, "metadata")
        self._guarantee_directory(metadata_dir)
        
        # load the dublin core (which will initialise if necessary)
        self._load_dc()
    
    @property
    def deposit_info_raw(self):
        return self._deposit_info_raw
    
    @deposit_info_raw.setter
    def deposit_info_raw(self, value):
        # FIXME: should probably do some value validation
        self._deposit_info_raw = value
        self._save_deposit_info()
        
    @property
    def dc_xml(self):
        return self._dc_xml
    
    @dc_xml.setter
    def dc_xml(self, value):
        # FIXME: should probably do some value validation
        self._dc_xml = value
        self._save_dc()
    
    def get_files(self):
        """
        Get a list of DepositFile objects currently part of this DIP
        """
        files = []
        for fr in self.deposit_info_raw['files']:
            files.append(DepositFile(self.base_dir, raw=fr))
        return files
        
    def get_file(self, path):
        # calculate the real path (in case this is a relative path)
        real_path = os.path.realpath(path)
        
        # now find out if we already have a record for that file
        for fr in self.deposit_info_raw['files']:
            if os.path.realpath(fr['path']) == real_path:
                return DepositFile(self.base_dir, raw=fr)
        return None
    
    def set_file(self, path):
        """
        Add the file at the specified path by-reference to the DIP.  This operation 
        will calculate the file's md5 at the point that it is added.
        
        If the file path already exists in the DIP, its record will be updated.
        
        Returns a DepositFile object representing the added file
        """
        # normalise the file path, to be relative to the self.base_dir, so that we can check it
        norm_path = _normalise_path(path, self.base_dir)
        
        # check that the file exists
        if not os.path.isfile(path):
            raise InitialiseException(path + " (normalised to " +  norm_path + ") is not a path to a file")
        
        # now find out if we already have a record for that file
        existing_record = None
        for fr in self.deposit_info_raw['files']:
            if fr['path'] == norm_path:
                existing_record = fr
                break
        
        # if we have an existing record for that file, just force an update
        if existing_record is not None:
            self._update_file_record(existing_record)
        else:
            # otherwise, add a new file record for that path
            self._add_file_record(path)
    
    def get_endpoints(self):
        """
        Get a list of Endpoint objects currently part of this DIP
        """
        endpoints = []
        for e in self.deposit_info_raw['endpoints']:
            endpoints.append(Endpoint(raw=e))
        return endpoints
        
    def get_endpoint(self, endpoint_id):
        for e in self.deposit_info_raw['endpoints']:
            if e['id'] == endpoint_id:
                return Endpoint(raw=e)
        return None
    
    def set_endpoint(self, endpoint=None, id=None, sd_iri=None, col_iri=None, package=None, username=None, obo=None):
        """
        Set the endpoint with the details provided.  There are 2 modes of operation:
        
        1/ provide an Endpoint object in the "endpoint" argument.  If it has an ID then it will
            replace any existing endpoint with the same id, if not it will be given an id and 
            added
        2/ provide the individual arguments for an endpoint object.  If an "id" argument is
            given then it will replace any existing endpoint with the same id, if not it will
            be given an id and added
        
        If the "endpoint" argument is provided, it will override any other arguments provided.
        
        When creating an endpoint, only the sd_iri is strictly necessary, although deposit will not
        be able to go ahead without a col_iri.
        
        The id should be a UUID4, and don't make it up yourself, if you don't have an id for the
        object leave it to this method to mint one for you
        
        Keyword arguments:
        endpoint    -   an Endpoint object to be added or replaced
        id          -   the id of the endpoint (a UUID4 string)
        sd_iri      -   root service document IRI of the endpoint
        col_iri     -   repository collection IRI to which initial deposits will be made
        package     -   package format identifier to use with this endpoint
        username    -   username to authenticate with
        obo         -   on behalf of user to deposit as
        
        Returns an Endpoint object
        """
        # if we are not supplied an endpoint, make an Endpoint object from the other params
        if endpoint is None:
            if sd_iri is None:
                raise InitialiseException("attempt to set endpoint without sd_iri - this is required")
            endpoint = Endpoint(sd_iri=sd_iri, col_iri=col_iri, package=package, username=username, obo=obo, id=id)
        
        # validate the sd_iri of the supplied endpoint
        if endpoint.sd_iri is None:
            raise InitialiseException("attempt to set endpoint without sd_iri - this is required")
        
        # determine if this is a new endpoint or not (and its position in the endpoints array)
        existing_index = -1
        if endpoint.id is not None:
            for i in range(len(self.deposit_info_raw['endpoints'])):
                if self.deposit_info_raw['endpoints'][i]['id'] == endpoint.id:
                    existing_index = i
                    break
        else:
            # otherwise, give the endpoint an id
            endpoint.id = str(uuid.uuid4())
        
        # if the endpoint already exists, remove it
        if existing_index > -1:
            del self.deposit_info_raw['endpoints'][existing_index] # FIXME: does this trigger the setter?
        
        # add the new endpoint to the deposit info
        self.deposit_info_raw['endpoints'].append(endpoint.raw)
        
        # FIXME: we may not need to do this, depending on how the two above
        # modify operations behave
        self._save_deposit_info()
        
        # return the endpoint object (the wrapped data structure is now part of the
        # deposit info on this object, and thus can be updated by reference)
        return endpoint
        
    def remove_endpoint(self, endpoint_id, delete_in_repository=False):
        """
        Remove the specified endpoint from the DIP, and optionally issue a DELETE
        request against the repository.
        
        Arguments:
        endpoint_id -   The ID (UUID) of the endpoint to be removed
        
        Keyword Arguments
        delete_in_repository    - issue a delete request against the repository first
        """
        if delete_in_repository:
            raise NotImplementedError("DELETE in repository on endpoint remove is not currently supported")
        
        existing_index = -1
        for i in range(len(self.deposit_info_raw['endpoints'])):
            if self.deposit_info_raw['endpoints'][i]['id'] == endpoint_id:
                existing_index = i
                break
        
        if existing_index > -1:
            del self.deposit_info_raw['endpoints'][existing_index]
            self._save_deposit_info()
        
    def get_history(self, endpoint_id):
        """
        get a DepositHistory object representing the deposit history on the supplied endpoint_id
        
        Arguments:
        endpoint_id -   the UUID of the endpoint whose history we are interested in
        """
        pass
    
    def get_metadata_files(self):
        """
        get a list of MetadataFile objects currently part of this DIP
        """
        pass
        
    def add_metadata_file(self, md_format, path=None, string=None):
        """
        Add a metadata file or string by-value to the DIP
        
        Arguments:
        md_format   -   a free text string, identifying the metadata format
        
        Keyword Arguments:
        path    -   path to the metadata file
        string  -   full string value of the contents of the metadata file
        
        You should only supply one of "path" or "string".  If both are provided, the
        "path" will take precedence
        """
        pass
        
    def add_dublin_core(self, dcterm, value, lang=None):
        """
        Add a Dublin Core value from the dcterms namespace, with optional language, to the DIP
        
        Arguments:
        dcterm  -   The field from the dcterms namespace
        value   -   The string value to put in the field
        
        Keyword Arguments:
        lang    -   The language of the value
        """
        pass
        
    def remove_dublin_core(self, dcterm=None, value=None, lang=None):
        """
        Remove any Dublin Core value which matches the parameters provided.  Leaving
        a keyword set to None is a wildcard which will match anything.
        
        Keyword Arguments:
        dcterm  -   The field from the dcterms namespace
        value   -   The string value to put in the field
        lang    -   The language of the value
        """
        pass
        
    def get_dublin_core(self, dcterm=None, value=None, lang=None):
        """
        Get a list of of any Dublin Core values which match the parameters provided.
        Leaving a keyword set to None is a wildcard which will match anything.
        """
        pass
        
    def get_state(self):
        """
        Check the following conditions of the DIP:
        
        1/ Which endpoints of the total list of endpoints has each metadata/file been deposited to
        2/ Which files have changed on disk since they were last deposited to each endpoint
        
        Return a DepositState object representing the results of this operation
        """
        pass
        
    def deposit(self, endpoint_id):
        """
        Carry out a deposit (create or update) operation of the DIP to the specified
        endpoint.
        
        Returns a tuple: (ResponseMeta, sword2.DepositReceipt)
        """
        pass
        
    def delete(self, endpoint_id):
        """
        Delete the object from the specified endpoint
        
        Returns a ResponseMeta object
        """
        pass
        
    def package(self, endpoint_id=None, packager=None):
        """
        package the DIP up as per either the supplied packager or the endpoint_id
        and return a read-only file handle
        """
        pass
    
    def get_repository_statement(self, endpoint_id):
        """
        Make a request to the specified endpoint to determine the state of the object
        in the repository.
        
        Returns a sword2.Statement object
        """
        pass
        
    def get_packager(self, endpoint_id=None):
        pass
        
    def _default_deposit_info(self):
        n = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        return {
            "created" : n,
            "files" : [],
            "endpoints" : [],
            "metadata" : [
                {
                    "path" : "metadata/dcterms.xml",
                    "format" : "dcterms",
                    "added" : n,
                    "modified" : n,
                    "endpoints" : []
                }
            ]
        }
    
    def _default_dc_xml(self):
        metadata = etree.Element("metadata")
        return metadata
    
    def _load_deposit_info(self):
        # get the path to the deposit.json file
        deposit_file = os.path.join(self.base_dir, "deposit.json")
        
        # initialise stuff - check that it is a file, and if it exists,
        # if it doesn't exist, create it with the default content
        if os.path.exists(deposit_file) and not os.path.isfile(deposit_file):
            raise InitialiseException(deposit_file + " exists, but does not resolve to a file")
        if not os.path.exists(deposit_file):
            default = self._default_deposit_info()
            with open(deposit_file, "wb") as f:
                f.write(json.dumps(default, sort_keys=True, indent=2))
        
        # read in the raw deposit info
        with open(deposit_file) as f:
            self._deposit_info_raw = json.load(f)
    
    def _save_deposit_info(self):
        with open(os.path.join(self.base_dir, "deposit.json"), "wb") as f:
            out = json.dumps(self.deposit_info_raw, sort_keys=True, indent=2)
            f.write(out)
            
    def _save_dc(self):
        # the path to the dcterms.xml file
        dcterms_file = os.path.join(self.base_dir, "metadata", "dcterms.xml")
        
        # wrap in an ElementTree document, and get it to handle writing it out
        tree = etree.ElementTree(element=self.dc_xml)
        tree.write(dcterms_file, xml_declaration=True)
            
    def _guarantee_directory(self, dir_path):
        if os.path.exists(dir_path) and not os.path.isdir(dir_path):
            raise InitialiseException(dir_path + " exists, and does not resolve to a directory")
        elif not os.path.exists(dir_path):
            os.makedirs(dir_path) # FIXME: do we need to care about the mode?
            
    def _load_dc(self):
        # the path to the dcterms.xml file
        dcterms_file = os.path.join(self.base_dir, "metadata", "dcterms.xml")
        
        # make sure that the DC namespace is registered with ElementTree
        etree.register_namespace("dcterms", "http://purl.org/dc/terms/")
        
        # first ensure that the dc exists
        if os.path.exists(dcterms_file) and not os.path.isfile(dcterms_file):
            raise InitialiseException(dcterms_file + " exists, but does not resolve to a file")
        if not os.path.exists(dcterms_file):
            xml = self._default_dc_xml()
            tree = etree.ElementTree(element=xml)
            tree.write(dcterms_file, xml_declaration=True)
        
        # now read the dc in
        with open(dcterms_file) as f:
            doc = etree.parse(f)
            self._dc_xml = doc.getroot()
            
    def _update_file_record(self, record):
        path = _absolute_path(record['path'], self.base_dir)
        with open(path) as f:
            checksum = hashlib.md5(f.read()).hexdigest()
        n = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        record['md5'] = checksum
        record['updated'] = n
        self._save_deposit_info()
    
    def _add_file_record(self, path):
        with open(path, "r") as f:
            checksum = hashlib.md5(f.read()).hexdigest()
        n = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        record = {
            "path" : _normalise_path(path, self.base_dir),
            "md5" : checksum,
            "added" : n,
            "updated" : n,
        }
        self.deposit_info_raw['files'].append(record)
        self._save_deposit_info()    
            
class InitialiseException(Exception):
    """
    Exception to be thrown if the initialisation of a DIP fails
    """
    def __init__(self, message):
        super(InitialiseException, self).__init__(self)
        self.message = message
    
    def __str__(self):
        return repr(self.message)
        
class Endpoint(object):
    def __init__(self, raw=None, sd_iri=None, col_iri=None, package=None, username=None, obo=None, id=None):
        if raw is not None:
            self.raw = raw
        else:
            self.raw = {}
            if sd_iri is not None:
                self.raw['sd_iri'] = sd_iri
            if col_iri is not None:
                self.raw['col_iri'] = col_iri
            if package is not None:
                self.raw['package'] = package
            if username is not None:
                self.raw['username'] = username
            if obo is not None:
                self.raw['obo'] = obo
            if id is not None:
                self.raw['id'] = id
        
        if self.raw.get('id') is None:
            self.raw['id'] = str(uuid.uuid4())
    
    @property
    def sd_iri(self):
        return self.raw.get('sd_iri')
    
    @sd_iri.setter
    def sd_iri(self, value):
        self.raw['sd_iri'] = value
    
    @property
    def col_iri(self):
        return self.raw.get('col_iri')
    
    @col_iri.setter
    def col_iri(self, value):
        self.raw['col_iri'] = value
        
    @property
    def package(self):
        return self.raw.get('package')
    
    @package.setter
    def package(self, value):
        self.raw['package'] = value
    
    @property
    def username(self):
        return self.raw.get('username')
    
    @username.setter
    def username(self, value):
        self.raw['username'] = value
    
    @property
    def obo(self):
        return self.raw.get('obo')
        
    @obo.setter
    def obo(self, value):
        self.raw['obo'] = value
    
    @property
    def id(self):
        return self.raw.get('id')
        
    @id.setter
    def id(self, value):
        self.raw['id'] = value
        
class DepositFile(object):
    def __init__(self, base_dir, raw={}):
        self.base_dir = base_dir
        self.raw = raw
        
    # path, md5, added, updated, endpoints
    
    @property
    def path(self):
        return _absolute_path(self.raw.get('path'), self.base_dir)
     
    @property
    def md5(self):
        return self.raw.get('md5')
    
    @property
    def added(self):
        return self.raw.get('added')
    
    @property
    def updated(self):
        return self.raw.get('updated')
    
    
