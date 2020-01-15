"""Tests for handling failed builds"""

from dxr.exceptions import BuildError
from dxr.testing import SingleFileTestCase


class BuildFailureTests(SingleFileTestCase):
    source = r"""A bunch of garbage"""

    @classmethod
    def index(cls):
        """Make sure indexing twice doesn't fail."""
        super(BuildFailureTests, cls).index()
        super(BuildFailureTests, cls).index()

    def test_nothing(self):
        """A null test just to make the setup method run"""
