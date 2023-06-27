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
      'three_plus': lambda operand: 3 + operand
    }
    CHOICES = {
      'five': '5ive!'
    }

    def AskForInput( prompt, default_value = None, completion = None ):
      if default_value is not None:
        return default_value

      return 'typed text'

    d = {
      'dollar': '$$',
      'not_a_var': '$${test}',
      'one': '${one}',
      'two': '${one} and ${two}',
      'three': '${three}',
      'successor_to_three': '${three_plus(1)}',
      'three_with_default': '${three_with_default:${three\\}}', # uses calculus
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
      'successor_to_three': '4',
      'three_with_default': '3',
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

  def test_ParseVariables( self ):
    tests = [
      {
        # Mock for AskForInput
        'AskForInput': RuntimeError,
        # Formatl arguments to ParseVariables
        'in': {
          'variables_list': [ { 'a': 'A' }, { 'b': '${a}' } ],
          'mapping': {},
          'calculus': {},
          'user_choices': {}
        },
        # Expected return, i.e. expected
        'out': { 'a': 'A', 'b': 'A' }
      },
      # List of vars, interdependent
      {
        'AskForInput': [ 'first', 'third' ],
        'in': {
          'variables_list': [
            {
              'first': '${first:first}',
            },
            {
              'second': 'second, ${first}',
              'third': '${first:last} and ${third:third}',
            },
            {
              'fourth': '${first}, ${second} and ${third}'
            }
          ],
          'mapping': {},
          'calculus': {},
          'user_choices': {}
        },
        'out': {
          'first': 'first',
          'second': 'second, first',
          'third': 'first and third',
          'fourth': 'first, second, first and first and third'
        }
      },
      # Calculus with arguments
      {
        'AskForInput': RuntimeError,
        'in': {
          'variables_list': {
            'not_in_list': '${is_in_list( "x", [ "y", "z" ] )}',
            'in_list': '${is_in_list( "x", [ "${why}", "x", "z" ] )}',
            'not_in_listj#json': '${is_in_list( "x", [ "y", "z" ] )}',
            'in_listj#json':
              '${is_in_list( "x", [ "${why}", "x", "${zed}" ] )}',
          },
          'mapping': {
            'why': 'y',
            'zed': 'z'
          },
          'calculus': {
            'is_in_list':
              lambda needle, haystack: 'true' if needle in haystack else 'false'
          },
          'user_choices': {}
        },
        'out': {
          'not_in_list': 'false',
          'in_list': 'true',
          'not_in_listj': False,
          'in_listj': True,
        }
      }
    ]

    for test in tests:
      with patch( 'vimspector.utils.AskForInput',
                  side_effect = test[ 'AskForInput' ] ):
        self.assertDictEqual( utils.ParseVariables( **test[ 'in' ] ),
                              test[ 'out' ] )


assert unittest.main( module=__name__,
                      testRunner=unittest.TextTestRunner( sys.stdout ),
                      exit=False ).result.wasSuccessful()
