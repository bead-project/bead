'''
Proto-Beads & their filesystem layout
'''

import os
import zipfile

from . import layouts
from . import meta
from . import tech
from .bead import Bead

# technology modules
persistence = tech.persistence
securehash = tech.securehash
fs = tech.fs


# generated with `uuidgen -t`
META_VERSION = 'aaa947a6-1f7a-11e6-ba3a-0021cc73492e'


class Workspace(Bead):

    directory: fs.Path

    def __init__(self, directory):
        self.directory = fs.Path(directory).resolve()

    @property
    def is_valid(self):
        dir = self.directory
        return all(
            (
                (dir / layouts.Workspace.INPUT).is_dir(),
                (dir / layouts.Workspace.OUTPUT).is_dir(),
                (dir / layouts.Workspace.TEMP).is_dir(),
                (dir / layouts.Workspace.BEAD_META).is_file()))

    @property
    def _meta_filename(self):
        return self.directory / layouts.Workspace.BEAD_META

    @property
    def meta(self):
        return persistence.file_load(self._meta_filename)

    @meta.setter
    def meta(self, meta):
        persistence.file_dump(meta, self._meta_filename)

    # Bead properties
    @property
    def kind(self):
        return self.meta[meta.KIND]

    @property
    def name(self):
        return self.directory.name

    @property
    def inputs(self):
        return tuple(meta.parse_inputs(self.meta))

    # faked Bead properties
    @property
    def content_id(self):
        # note, that it is not a valid, unique
        # content_id for referencing
        # however it is easily recognisable on graphs
        return f'<WORKSPACE {self.directory}>'

    @property
    def freeze_time_str(self):
        return tech.timestamp.timestamp()

    @property
    def box_name(self):
        return '<UNSAVED>'

    # workspace constructors
    def create(self, kind):
        '''
        Set up an empty project structure.

        Works with either an empty directory or a directory to be created.
        '''
        dir = self.directory
        assert not dir.exists()

        self.create_directories()

        bead_meta = {
            meta.KIND: kind,
            meta.INPUTS: {}}
        fs.write_file(
            dir / layouts.Workspace.BEAD_META,
            persistence.dumps(bead_meta))

        assert self.is_valid

    def create_directories(self):
        dir = self.directory
        fs.ensure_directory(dir)
        fs.ensure_directory(dir / layouts.Workspace.INPUT)
        fs.make_readonly(dir / layouts.Workspace.INPUT)
        fs.ensure_directory(dir / layouts.Workspace.OUTPUT)
        fs.ensure_directory(dir / layouts.Workspace.TEMP)
        fs.ensure_directory(dir / layouts.Workspace.META)

    def pack(self, zipfilename, freeze_time, comment):
        '''
        Create archive from workspace.
        '''
        zipfilename = fs.Path(zipfilename)
        assert not zipfilename.exists()
        try:
            _ZipCreator().create(zipfilename.as_posix(), self, freeze_time, comment)
        except (RuntimeError, Exception):
            if zipfilename.exists():
                zipfilename.unlink()
            raise

    def has_input(self, input_nick):
        '''
        Is there an input defined for input_nick?

        NOTE: it is not necessarily loaded!
        '''
        return input_nick in self.meta[meta.INPUTS]

    def is_loaded(self, input_nick):
        return (self.directory / layouts.Workspace.INPUT / input_nick).is_dir()

    def add_input(self, input_nick, kind, content_id, freeze_time_str):
        m = self.meta
        m[meta.INPUTS][input_nick] = {
            meta.INPUT_KIND: kind,
            meta.INPUT_CONTENT_ID: content_id,
            meta.INPUT_FREEZE_TIME: freeze_time_str}
        self.meta = m

    def delete_input(self, input_nick):
        assert self.has_input(input_nick)
        if self.is_loaded(input_nick):
            self.unload(input_nick)
        m = self.meta
        del m[meta.INPUTS][input_nick]
        self.meta = m

    @property
    def _input_map_filename(self):
        return self.directory / layouts.Workspace.INPUT_MAP

    @property
    def input_map(self):
        """
        Map from local (bead specific) input nicks to real (more widely recognised) bead names
        """
        try:
            return persistence.file_load(self._input_map_filename)
        except:
            return {}

    @input_map.setter
    def input_map(self, input_map):
        persistence.file_dump(input_map, self._input_map_filename)

    def get_input_bead_name(self, input_nick):
        '''
        Returns the name on which update works.
        '''
        return self.input_map.get(input_nick, input_nick)

    def set_input_bead_name(self, input_nick, bead_name):
        '''
        Sets the name to be used for updates in the future.
        '''
        input_map = self.input_map
        input_map[input_nick] = bead_name
        self.input_map = input_map

    def load(self, input_nick, bead):
        '''
        Make output data files in bead available under input directory
        '''
        input_dir = self.directory / layouts.Workspace.INPUT
        fs.make_writable(input_dir)
        try:
            self.add_input(
                input_nick,
                bead.kind, bead.content_id, bead.freeze_time_str)
            destination_dir = input_dir / input_nick
            bead.unpack_data_to(destination_dir)
            for f in fs.all_subpaths(destination_dir):
                fs.make_readonly(f)
        finally:
            fs.make_readonly(input_dir)

    def unload(self, input_nick):
        '''
        Remove files for given input
        '''
        assert self.has_input(input_nick)
        input_dir = self.directory / layouts.Workspace.INPUT
        fs.make_writable(input_dir)
        try:
            fs.rmtree(input_dir / input_nick)
        finally:
            fs.make_readonly(input_dir)

    def __repr__(self):
        # default values are printed as repr of the value
        return self.directory

    @classmethod
    def for_current_working_directory(cls):
        '''
        Create Workspace based on current working directory.

        Determine the correct Workspace for the current working directory.
        As a result, the returned workspace may be for a parent directory,
        if the cwd is under a valid workspace, but not at its root.

        Can return an invalid Workspace.
        '''
        cwd = cls(os.getcwd())
        ws = cwd
        while not ws.is_valid:
            parent = ws.directory / '..'
            if parent == ws.directory:
                return cwd
            ws = cls(parent)
        return ws


class _ZipCreator:
    def __init__(self):
        self.hashes = {}
        self.zipfile = None

    def add_hash(self, path, hash):
        assert path not in self.hashes
        self.hashes[path] = hash

    def add_file(self, path, zip_path):
        assert self.zipfile
        path_str = path.as_posix() if hasattr(path, 'as_posix') else str(path)
        zip_path_str = zip_path.as_posix() if hasattr(zip_path, 'as_posix') else str(zip_path)
        self.zipfile.write(path_str, zip_path_str)
        self.add_hash(
            zip_path_str,
            securehash.file(open(path_str, 'rb'), os.path.getsize(path_str)))

    def add_path(self, path, zip_path):
        path_str = path.as_posix() if hasattr(path, 'as_posix') else str(path)
        if os.path.isdir(path_str):
            self.add_directory(path, zip_path)
        else:
            assert os.path.isfile(path_str), '%s is neither a file nor a directory' % path_str
            self.add_file(path, zip_path)

    def add_directory(self, path, zip_path):
        path_str = path.as_posix() if hasattr(path, 'as_posix') else str(path)
        for f in os.listdir(path_str):
            self.add_path(path / f, zip_path / f)

    def add_string_content(self, zip_path, string):
        assert self.zipfile
        zip_path_str = zip_path.as_posix() if hasattr(zip_path, 'as_posix') else str(zip_path)
        bytes = string.encode('utf-8')
        self.zipfile.writestr(zip_path_str, bytes)
        self.add_hash(zip_path_str, securehash.bytes(bytes))

    def create(self, zip_file_name, workspace, timestamp, comment):
        assert workspace.is_valid
        user_compression_preference = os.environ.get('BEAD_ZIP_COMPRESSION')
        compression = {
            'off': zipfile.ZIP_STORED,
            'stored': zipfile.ZIP_STORED,
            # these are not universally supported compression methods
            # 'lzma': zipfile.ZIP_LZMA,
            # 'bz2': zipfile.ZIP_BZIP2,
            'deflated': zipfile.ZIP_DEFLATED,
        }.get(user_compression_preference, zipfile.ZIP_DEFLATED)
        try:
            with zipfile.ZipFile(
                zip_file_name,
                mode='w',
                compression=compression,
                allowZip64=True,
            ) as self.zipfile:
                self.zipfile.comment = comment.encode('utf-8')
                self.add_data(workspace)
                self.add_code(workspace)
                self.add_meta(workspace, timestamp)
        finally:
            self.zipfile = None

    def add_code(self, workspace):
        source_directory = workspace.directory
        source_directory_str = source_directory.as_posix()

        def is_code(f):
            return f not in {
                layouts.Workspace.INPUT.as_posix(),
                layouts.Workspace.OUTPUT.as_posix(),
                layouts.Workspace.META.as_posix(),
                layouts.Workspace.TEMP.as_posix()}

        for f in sorted(os.listdir(source_directory_str)):
            if is_code(f):
                self.add_path(
                    source_directory / f,
                    layouts.Archive.CODE / f)

    def add_data(self, workspace):
        self.add_directory(
            workspace.directory / layouts.Workspace.OUTPUT,
            layouts.Archive.DATA)

    def add_meta(self, workspace, timestamp):
        bead_meta = {
            meta.META_VERSION: META_VERSION,
            meta.KIND: workspace.kind,
            meta.FREEZE_TIME: timestamp,
            meta.INPUTS: {
                input.name: {
                    meta.INPUT_KIND: input.kind,
                    meta.INPUT_CONTENT_ID: input.content_id,
                    meta.INPUT_FREEZE_TIME: input.freeze_time_str}
                for input in workspace.inputs},
            meta.FREEZE_NAME: workspace.name}

        self.add_string_content(layouts.Archive.BEAD_META, persistence.dumps(bead_meta))
        self.add_string_content(layouts.Archive.MANIFEST, persistence.dumps(self.hashes))
        persistence.zip_dump(workspace.input_map, self.zipfile, layouts.Archive.INPUT_MAP)
