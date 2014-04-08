

class Packager(object):
    def package(self, dip, out_dir, **packager_args):
        pass

import zipfile, os
class SimpleZipPackager(Packager):
    def package(self, dip, out_dir, **packager_args):
        pass



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
