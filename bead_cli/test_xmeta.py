from bead.archive import Archive
from bead.tech.fs import read_file, write_file


def test_meta_attributes_are_available_without_reading_the_archive(
    robot, bead_with_inputs, beads
):
    archive = beads[bead_with_inputs]
    archive_filename = archive.archive_filename

    def get_meta(a: Archive):
        return {
            'meta_version': a.meta_version,
            'content_id': a.content_id,
            'kind': a.kind,
            'freeze_time': a.freeze_time_str,
            'inputs': a.inputs,
            'input_map': a.input_map,
        }

    archive_attributes = get_meta(archive)

    robot.cli('xmeta', archive_filename)
    # damage the archive, so that all data must come from the xmeta file
    with robot.environment:
        write_file(archive_filename, '')
        assert read_file(archive_filename) == ''

    xmeta_archive = Archive(archive_filename)
    assert archive_attributes == get_meta(xmeta_archive)
