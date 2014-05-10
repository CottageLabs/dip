########################################################
## Generic Packager classes
########################################################

class PackagerException(Exception):
    pass

class Packager(object):
    def package(self, dip, out_dir, **packager_args):
        return None
    def cleanup(self, dip, package_dir, package_info, **packager_args):
        pass

class PackageInfo(object):
    def __init__(self, path, file_paths, metadata_formats, filename, mimetype):
        self.path = path
        self.file_paths = file_paths
        self.metadata_formats = metadata_formats
        self.filename = filename
        self.mimetype = mimetype

########################################################
## SimpleZip implementation
########################################################
# Note we do the imports here rather than at the top 
# just for the purposes of keeping all the dependencies
# together

import zipfile, os
class SimpleZipPackager(Packager):
    """
    Packager which makes a simple flat zip file out of the files in the dip

    The packager args can be any of the following:

    metadata_files - True/False - should the packager include all of the metadata files
    deposit_files - True/False - should the packager include all of the dip's files
    remove_zip - True/False - on completion of deposit, should the created package be removed

    """
    def package(self, dip, out_dir, **packager_args):
        # sort out the arguments/paths to use
        out_zip = os.path.join(out_dir, "SimpleZip.zip")
        do_md = packager_args.get("metadata_files", True)
        do_files = packager_args.get("deposit_files", True)

        # check that some packaging is going to be done
        if not do_md and not do_files:
            raise PackagerException("SimpleZipPackager must be instructed to deposit either metadata files, deposit files or both")

        # use these to record the objects that get packaged
        file_paths = []
        metadata_formats = []

        # create the zip
        with zipfile.ZipFile(out_zip, "w") as z:
            if do_md:
                metadata_files = dip.get_metadata_files()
                for mf in metadata_files:
                    metadata_formats.append(mf.format)
                    z.write(mf.path, self._filename(mf.path))
            if do_files:
                deposit_files = dip.get_files()
                for df in deposit_files:
                    file_paths.append(df.path)
                    z.write(df.path, self._filename(df.path))
        
        return PackageInfo(out_zip, file_paths, metadata_formats, "SimpleZip.zip", "application/zip")

    def cleanup(self, dip, package_dir, package_info, **packager_args):
        # sort out the arguments/paths to use
        out_zip = os.path.join(package_dir, "SimpleZip.zip")
        remove_zip = packager_args.get("remove_zip", False)
        if not remove_zip:
            return
        os.unlink(out_zip)

    def _filename(self, path):
        parts = os.path.split(path)
        return parts[1]
        
##########################################################
# Packager Factory and configuration
##########################################################
# Configuration needs to be at the bottom of the file, so
# we just put the PackagerFactory here too to keep it all
# together

class PackagerFactory(object):
    @classmethod
    def load_packager(cls, package_identifier):
        klazz = PACKAGERS.get(package_identifier)
        return klazz()

# FIXME: a proper solution would load these dynamically, perhaps from some
# installation directory.  For the time being, our PackagerFactory just
# gets them from here
PACKAGERS = {
    "http://purl.org/net/sword/package/SimpleZip" : SimpleZipPackager
}
