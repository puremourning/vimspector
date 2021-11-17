# vimspector - A multi-language debugging system for Vim
# Copyright 2021 Ben Jackson
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools
import typing
from collections.abc import Mapping

MEMO = {}


def memoize( func ):
  global MEMO

  @functools.wraps( func )
  def wrapper( *args, **kwargs ):
    dct = MEMO.setdefault( func, {} )
    key = ( args, frozenset( kwargs.items() ) )
    try:
      return dct[ key ]
    except KeyError:
      result = func( *args, **kwargs )
      dct[ key ] = result
      return result

  return wrapper


def override( target_dict: typing.MutableMapping,
              override_dict: typing.Mapping ):
  """Apply the updates in |override| to the dict |target|. This is like
  dict.update, but recursive. i.e. if the existing element is a dict, then
  override elements of the sub-dict rather than wholesale replacing.
  e.g.
  override(
    {
      'outer': { 'inner': { 'key': 'oldValue', 'existingKey': True } }
    },
    {
      'outer': { 'inner': { 'key': 'newValue' } },
      'newKey': { 'newDict': True },
    }
  )
  yields:
    {
      'outer': {
        'inner': {
           'key': 'newValue',
           'existingKey': True
        }
      },
      'newKey': { newDict: True }
    }
  """

  for key, value in override_dict.items():
    current_value = target_dict.get( key )
    if not isinstance( current_value, Mapping ):
      # Thing or Mapping overrides Thing or None
      target_dict[ key ] = value
    elif isinstance( value, Mapping ):
      # Mapping overrides mapping, recurse
      target_dict[ key ] = override( current_value, value )
    else:
      # Thing overrides Mapping
      target_dict[ key ] = value

  return target_dict
