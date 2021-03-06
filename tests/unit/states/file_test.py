# Import python libs
import json

# Import Salt Testing libs
from salttesting import skipIf, TestCase
from salttesting.helpers import ensure_in_syspath
ensure_in_syspath('../../')

# Import third party libs
import yaml

try:
    from mock import MagicMock, patch
    has_mock = True
except ImportError:
    has_mock = False

if has_mock:
    import salt.states.file as filestate
    filestate.__salt__ = {
        'file.manage_file': False
    }
    filestate.__opts__ = {'test': False}


@skipIf(has_mock is False, 'mock python module is unavailable')
class TestFileState(TestCase):

    def test_serialize(self):
        def returner(contents, *args, **kwargs):
            returner.returned = contents
        returner.returned = None


        filestate.__salt__ = {
            'file.manage_file': returner
        }

        dataset = {
            "foo": True,
            "bar": 42,
            "baz": [1, 2, 3],
            "qux": 2.0
        }

        filestate.serialize('/tmp', dataset)
        self.assertEquals(yaml.load(returner.returned), dataset)

        filestate.serialize('/tmp', dataset, formatter="yaml")
        self.assertEquals(yaml.load(returner.returned), dataset)

        filestate.serialize('/tmp', dataset, formatter="json")
        self.assertEquals(json.loads(returner.returned), dataset)

    def test_contents_and_contents_pillar(self):
        def returner(contents, *args, **kwargs):
            returner.returned = contents
        returner.returned = None

        filestate.__salt__ = {
            'file.manage_file': returner
        }

        manage_mode_mock = MagicMock()
        filestate.__salt__['config.manage_mode'] = manage_mode_mock

        ret = filestate.managed('/tmp/foo', contents='hi', contents_pillar='foo:bar')
        self.assertEquals(False, ret['result'])

    def test_contents_pillar_adds_newline(self):
        # make sure the newline
        pillar_value = 'i am the pillar value'
        expected = '{}\n'.format(pillar_value)

        self.run_contents_pillar(pillar_value, expected)

    def test_contents_pillar_doesnt_add_more_newlines(self):
        # make sure the newline
        pillar_value = 'i am the pillar value\n'

        self.run_contents_pillar(pillar_value, expected=pillar_value)

    def run_contents_pillar(self, pillar_value, expected):
        def returner(contents, *args, **kwargs):
            returner.returned = (contents, args, kwargs)
        returner.returned = None

        filestate.__salt__ = {
            'file.manage_file': returner
        }

        path = '/tmp/foo'
        pillar_path = 'foo:bar'

        # the values don't matter here
        filestate.__salt__['config.manage_mode'] = MagicMock()
        filestate.__salt__['file.source_list'] = MagicMock(return_value=[None, None])
        filestate.__salt__['file.get_managed'] = MagicMock(return_value=[None, None, None])

        # pillar.get should return the pillar_value
        pillar_mock = MagicMock(return_value=pillar_value)
        filestate.__salt__['pillar.get'] = pillar_mock

        ret = filestate.managed(path, contents_pillar=pillar_path)

        # make sure the pillar_mock is called with the given path
        pillar_mock.assert_called_once_with(pillar_path)

        # make sure no errors are returned
        self.assertEquals(None, ret)

        # make sure the value is correct
        self.assertEquals(expected, returner.returned[1][-1])

if __name__ == '__main__':
    from integration import run_tests
    run_tests(TestFileState, needs_daemon=False)
