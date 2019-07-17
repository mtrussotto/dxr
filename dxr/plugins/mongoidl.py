"""mongoidl: Add annotations for Mongo IDL files

"""

from fnmatch import fnmatchcase
from funcy import merge
import os
import sys
from os.path import join, basename, splitext, isfile
from collections import namedtuple

from dxr.indexers import (FileToIndex as FileToIndexBase,
                          TreeToIndex as TreeToIndexBase)
from dxr.mime import icon
from dxr.utils import browse_file_url, unicode_for_display
from dxr.plugins import Plugin
from dxr.config import AbsPath

def _q(s):
    return '"' + s + '"'

class TreeToIndex(TreeToIndexBase):
    def __init__(self, plugin_name, tree, vcs_cache):
        super(TreeToIndex, self).__init__(plugin_name, tree, vcs_cache)
        sys.stderr.write("TREE PATH = "+str(self.tree)+"\n")
        self.old_idlc="buildscripts/tools/idlc"

    def pre_build(self):
        self._temp_folder = os.path.join(self.tree.temp_folder,
                                         'plugins',
                                         self.plugin_name)

    def environment(self, vars_):
        """Set up environment variables to trigger analysis dumps from .

        We'll store all the harvested metadata in the plugins temporary folder.

n        """
        plugin_folder = os.path.dirname(__file__)
        env = {
            'IDLC': " ".join(_q(x) for x in [sys.executable,
                                             os.path.join(plugin_folder, "mongoidl-idl.py"),
                                             "--temp_folder",
                                             os.path.join(self._temp_folder, "files"),
                                             "--source_folder",
                                             self.tree.source_folder,
                                             os.path.join(self.tree.source_folder, self.plugin_config.orig_idlc)])
        }
        return merge(vars_, env)
        
    def file_to_index(self, path, contents):
        return FileToIndex(path,
                           contents,
                           self.plugin_name,
                           self.tree, self._temp_folder)


class FileToIndex(FileToIndexBase):
    def _metapath(self, path):
        if path[0] == os.path.sep:
            return os.path.join(self._temp_folder, "files", os.path.normpath(path)[1:])
        return os.path.join(self._temp_folder, "files", os.path.normpath(path))

    def __init__(self, path, contents, plugin_name, tree, temp_folder):
        super(FileToIndex, self).__init__(path, contents, plugin_name, tree)
        self._temp_folder = temp_folder
        metapath = self._metapath(path)
        self._has_data = os.path.exists(metapath);
        self._links = dict()
        if self._has_data:
            sys.stderr.write("File to index = " + self.path + "\n")
            for line in open(metapath):
                kv = line.rstrip("\r\n").split(':', 1);
                title = None
                if len(kv) == 2 and kv[0] == "SOURCEGEN":
                    title = "Generated Source"
                if len(kv) == 2 and kv[0] == "HEADERGEN":
                    title = "Generated Header"
                if len(kv) == 2 and kv[0] == "IDLSOURCE":
                    title = "IDL source file"
                if title:
                    self._links[kv[0]] = (4, title,
                                          [(icon(kv[1]),
                                           unicode_for_display(basename(kv[1])),
                                           browse_file_url(self.tree.name,
                                                           unicode_for_display(kv[1])))])

    def is_interesting(self):
        return self._has_data
    
    def links(self):
        """Add a link TBD.
        """
        print "RETURNING " + str(self._links.values())
        return self._links.values()
        # yield (4,
        #        dual_exts.title,
        #        [(icon(dual_path),
        #          unicode_for_display(basename(dual_path)),
        #          browse_file_url(self.tree.name,
        #                          unicode_for_display(dual_path)))])

plugin = Plugin(
    tree_to_index = TreeToIndex,
    config_schema = {
        'orig_idlc': str
    }
)

