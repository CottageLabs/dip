########################################################
## Generic Packager classes
########################################################

class PackagerException(Exception):
    pass

class Packager(object):
    def package(self, dip, out_dir, **packager_args):
        return None

########################################################
## SimpleZip implementation
########################################################
# Note we do the imports here rather than at the top 
# just for the purposes of keeping all the dependencies
# together

import zipfile, os
class SimpleZipPackager(Packager):
    def package(self, dip, out_dir, **packager_args):
        out_zip = os.path.join(out_dir, "SimpleZip.zip")
        do_md = packager_args.get("metadata_files", True)
        do_files = packager_args.get("deposit_files", True)
        
        if not do_md and not do_files:
            raise PackagerException("SimpleZipPackager must be instructed to deposit either metadata files, deposit files or both")

        basedir = packager_args.get("basedir", dip.base_dir)

        with zipfile.ZipFile(out_zip, "w") as z:
            if do_md:
                metadata_files = dip.get_metadata_files()
                for mf in metadata_files:
                    z.write(mf.path, self._filename(mf.path))
            if do_files:
                deposit_files = dip.get_files()
                for df in deposit_files:
                    z.write(df.path, self._filename(df.path, basedir=basedir))
        
        return out_zip
        
    def _filename(self, path, basedir=None):
        if basedir:
            fullbase = os.path.abspath(basedir)
            fullpath = os.path.abspath(path)
            if fullpath.startswith(fullbase):
                return fullpath[len(fullbase):]
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
