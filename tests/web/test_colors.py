import pytest

from tests.sketcher import Sketcher
from bead_cli.web.sketch import Sketch, Freshness


def test_new_version_marks_older_superseded():
    sketcher = Sketcher()
    sketcher.define('a1')

    sketch = Sketch.from_beads(tuple(sketcher.beads))
    sketch.color_beads()

    assert bead(sketch, 'a1').freshness == Freshness.UP_TO_DATE

    sketcher = Sketcher()
    sketcher.define('a1 a2')

    sketch = Sketch.from_beads(tuple(sketcher.beads))
    sketch.color_beads()

    assert bead(sketch, 'a1').freshness == Freshness.SUPERSEDED
    assert bead(sketch, 'a2').freshness == Freshness.UP_TO_DATE

    sketcher = Sketcher()
    sketcher.define('a1 a2 a3')

    sketch = Sketch.from_beads(tuple(sketcher.beads))
    sketch.color_beads()

    assert bead(sketch, 'a1').freshness == Freshness.SUPERSEDED
    assert bead(sketch, 'a2').freshness == Freshness.SUPERSEDED
    assert bead(sketch, 'a3').freshness == Freshness.UP_TO_DATE


def test_unconnected():
    sketcher = Sketcher()
    sketcher.define('a1 a2 b1 c2')

    sketch = Sketch.from_beads(tuple(sketcher.beads))
    sketch.color_beads()

    assert bead(sketch, 'a1').freshness == Freshness.SUPERSEDED
    assert bead(sketch, 'a2').freshness == Freshness.UP_TO_DATE
    assert bead(sketch, 'b1').freshness == Freshness.UP_TO_DATE
    assert bead(sketch, 'c2').freshness == Freshness.UP_TO_DATE


def test_up_to_date_input():
    sketcher = Sketcher()
    sketcher.define('a1 b1')
    sketcher.compile(
        """
        a1 -> b1
        """
    )

    sketch = Sketch.from_beads(tuple(sketcher.beads))
    sketch.color_beads()

    assert bead(sketch, 'a1').freshness == Freshness.UP_TO_DATE
    assert bead(sketch, 'b1').freshness == Freshness.UP_TO_DATE

    sketcher = Sketcher()
    sketcher.define('a1 a2 b1')
    sketcher.compile(
        """
        a2 -> b1
        """
    )

    sketch = Sketch.from_beads(tuple(sketcher.beads))
    sketch.color_beads()

    assert bead(sketch, 'a1').freshness == Freshness.SUPERSEDED

    assert bead(sketch, 'a2').freshness == Freshness.UP_TO_DATE
    assert bead(sketch, 'b1').freshness == Freshness.UP_TO_DATE


def test_out_of_date_input():
    sketcher = Sketcher()
    sketcher.define('a1 a2 b1')
    sketcher.compile(
        """
        a1 -> b1
        """
    )

    sketch = Sketch.from_beads(tuple(sketcher.beads))
    sketch.color_beads()

    assert bead(sketch, 'a1').freshness == Freshness.SUPERSEDED
    assert bead(sketch, 'b1').freshness == Freshness.OUT_OF_DATE


def test_phantom_input():
    sketcher = Sketcher()
    sketcher.define('d1 e1')
    sketcher.phantom('d1')
    sketcher.compile(
        """
        d1 --> e1
        """
    )

    sketch = Sketch.from_beads(tuple(sketcher.beads))
    sketch.color_beads()

    assert {'e'} == {bead.name for bead in sketcher.beads}
    assert len(list(sketcher.beads)) == 1
    assert len(sketch.beads) == 2

    assert bead(sketch, 'd1').freshness == Freshness.PHANTOM
    assert bead(sketch, 'e1').freshness == Freshness.OUT_OF_DATE


def test_impossible_loop():
    # sketcher are always forming a DAG, so this can not happen
    sketcher = Sketcher()
    sketcher.define('a1 b1')
    sketcher.compile(
        """
        a1 -> b1
        b1 -> a1
        """
    )

    sketch = Sketch.from_beads(tuple(sketcher.beads))
    with pytest.raises(ValueError):
        sketch.color_beads()


def test_coloring_is_transitive():
    sketcher = Sketcher()
    sketcher.define('a1    c1 d1 e1')
    sketcher.define('a2 b2 c2      ')
    sketcher.phantom('c1')
    sketcher.compile(
        """
        a1          c1 -> d1 -> e1
        a2 -> b2 -> c2
        """
    )

    sketch = Sketch.from_beads(tuple(sketcher.beads))
    sketch.color_beads()

    assert bead(sketch, 'a1').freshness == Freshness.SUPERSEDED
    assert bead(sketch, 'c1').freshness == Freshness.PHANTOM
    assert bead(sketch, 'd1').freshness == Freshness.OUT_OF_DATE
    assert bead(sketch, 'e1').freshness == Freshness.OUT_OF_DATE

    assert bead(sketch, 'a2').freshness == Freshness.UP_TO_DATE
    assert bead(sketch, 'b2').freshness == Freshness.UP_TO_DATE
    assert bead(sketch, 'c2').freshness == Freshness.UP_TO_DATE


def bead(sketch, name_version):
    for bead in sketch.beads:
        if bead.content_id == f'content_id_{name_version}':
            return bead
    raise ValueError('Dummy by name-version not found', name_version)
