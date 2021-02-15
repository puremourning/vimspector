import sys
import unittest
from unittest.mock import patch
from vimspector import utils


class TestExpandReferencesInDict( unittest.TestCase ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.maxDiff = 4096

  def test_ExpandReferencesInDict( self ):
    mapping = {
      'one': 'one',
      'two': 'TWO',
      'bool': True,
      'words': 'these are some words'
    }
    calculus = {
      'three': lambda : 1 + 2,
    }
    CHOICES = {
      'five': '5ive!'
    }

    def AskForInput( prompt, default_value = None ):
      if default_value is not None:
        return default_value

      return 'typed text'

    d = {
      'dollar': '$$',
      'not_a_var': '$${test}',
      'one': '${one}',
      'two': '${one} and ${two}',
      'three': '${three}',
      'four': '${four}',
      'five': '${five}',
      'list': [ '*${words}' ],
      'list1': [ 'start', '*${words}', 'end' ],
      'list2': [ '*${words}', '${three}' ],
      'list3': [ '${one}', '*${words}', 'three' ],
      'dict#json': '{ "key": "value" }',
      'bool#json': 'false',
      'one_default': '${one_default:one}',
      'two_default': '${two_default_1:one} and ${two_default_2:two}',
      'one_default2': '${one_default2:${one\\}}',
      'two_default2':
        '${two_default2_1:${one\\}} and ${two_default2_2:${two\\}}',
      'unlikely_name#json#s': 'true',
      'empty_splice': [ '*${empty:}' ],
    }

    e = {
      'dollar': '$',
      'not_a_var': '${test}',
      'one': 'one',
      'two': 'one and TWO',
      'three': '3',
      'four': 'typed text',
      'five': '5ive!',
      'list': [ 'these', 'are', 'some', 'words' ],
      'list1': [ 'start', 'these', 'are', 'some', 'words', 'end' ],
      'list2': [ 'these', 'are', 'some', 'words', '3' ],
      'list3': [ 'one', 'these', 'are', 'some', 'words', 'three' ],
      'dict': {
        'key': 'value',
      },
      'bool': False,
      'one_default': 'one',
      'two_default': 'one and two',
      'one_default2': 'one',
      'two_default2': 'one and TWO',
      'unlikely_name#json': 'true',
      'empty_splice': [],
    }

    with patch( 'vimspector.utils.AskForInput', side_effect = AskForInput ):
      utils.ExpandReferencesInDict( d, mapping, calculus, CHOICES )

    self.assertDictEqual( d, e )


assert unittest.main( module=__name__,
                      testRunner=unittest.TextTestRunner( sys.stdout ),
                      exit=False ).result.wasSuccessful()
