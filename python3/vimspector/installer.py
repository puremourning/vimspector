#!/usr/bin/env python3

# vimspector - A multi-language debugging system for Vim
# Copyright 2019 Ben Jackson
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

from urllib import request
import io
import contextlib
import zipfile
import gzip
import shutil
import tarfile
import hashlib
import time
import ssl
import subprocess
import functools
import os
import sys

from vimspector import install


@contextlib.contextmanager
def CurrentWorkingDir( d ):
  cur_d = os.getcwd()
  try:
    os.chdir( d )
    yield
  finally:
    os.chdir( cur_d )


def MakeExecutable( file_path ):
  # TODO: import stat and use them by _just_ adding the X bit.
  print( 'Making executable: {}'.format( file_path ) )
  os.chmod( file_path, 0o755 )



def WithRetry( f ):
  retries = 5
  timeout = 1 # seconds

  @functools.wraps( f )
  def wrapper( *args, **kwargs ):
    thrown = None
    for _ in range( retries ):
      try:
        return f( *args, **kwargs )
      except Exception as e:
        thrown = e
        print( "Failed - {}, will retry in {} seconds".format( e, timeout ) )
        time.sleep( timeout )
    raise thrown

  return wrapper


@WithRetry
def UrlOpen( *args, **kwargs ):
  return request.urlopen( *args, **kwargs )


def DownloadFileTo( url,
                    destination,
                    file_name = None,
                    checksum = None,
                    check_certificate = True ):
  if not file_name:
    file_name = url.split( '/' )[ -1 ]

  file_path = os.path.abspath( os.path.join( destination, file_name ) )

  if not os.path.isdir( destination ):
    os.makedirs( destination )

  if os.path.exists( file_path ):
    if checksum:
      if ValidateCheckSumSHA256( file_path, checksum ):
        print( "Checksum matches for {}, using it".format( file_path ) )
        return file_path
      else:
        print( "Checksum doesn't match for {}, removing it".format(
          file_path ) )

    print( "Removing existing {}".format( file_path ) )
    os.remove( file_path )

  r = request.Request( url, headers = { 'User-Agent': 'Vimspector' } )

  print( "Downloading {} to {}/{}".format( url, destination, file_name ) )

  if not check_certificate:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    kwargs = { "context":  context }
  else:
    kwargs = {}

  with contextlib.closing( UrlOpen( r, **kwargs ) ) as u:
    with open( file_path, 'wb' ) as f:
      f.write( u.read() )

  if checksum:
    if not ValidateCheckSumSHA256( file_path, checksum ):
      raise RuntimeError(
        'Checksum for {} ({}) does not match expected {}'.format(
          file_path,
          GetChecksumSHA254( file_path ),
          checksum ) )
  else:
    print( "Checksum for {}: {}".format( file_path,
                                         GetChecksumSHA254( file_path ) ) )

  return file_path


def GetChecksumSHA254( file_path ):
  with open( file_path, 'rb' ) as existing_file:
    return hashlib.sha256( existing_file.read() ).hexdigest()


def ValidateCheckSumSHA256( file_path, checksum ):
  existing_sha256 = GetChecksumSHA254( file_path )
  return existing_sha256 == checksum


def RemoveIfExists( destination ):
  if os.path.islink( destination ):
    print( "Removing file {}".format( destination ) )
    os.remove( destination )
    return

  N = 1


  def BackupDir():
    return "{}.{}".format( destination, N )

  while os.path.isdir( BackupDir() ):
    print( "Removing old dir {}".format( BackupDir() ) )
    try:
      shutil.rmtree( BackupDir() )
      print ( "OK, removed it" )
      break
    except OSError:
      print ( "FAILED" )
      N = N + 1

  if os.path.exists( destination ):
    print( "Removing dir {}".format( destination ) )
    try:
      shutil.rmtree( destination )
    except OSError:
      print( "FAILED, moving {} to dir {}".format( destination, BackupDir() ) )
      os.rename( destination, BackupDir() )


# Python's ZipFile module strips execute bits from files, for no good reason
# other than crappy code. Let's do it's job for it.
class ModePreservingZipFile( zipfile.ZipFile ):
  def extract( self, member, path = None, pwd = None ):
    if not isinstance( member, zipfile.ZipInfo ):
      member = self.getinfo( member )

    if path is None:
      path = os.getcwd()

    ret_val = self._extract_member( member, path, pwd )
    attr = member.external_attr >> 16
    os.chmod( ret_val, attr )
    return ret_val


def ExtractZipTo( file_path, destination, format ):
  print( "Extracting {} to {}".format( file_path, destination ) )
  RemoveIfExists( destination )

  if format == 'zip':
    with ModePreservingZipFile( file_path ) as f:
      f.extractall( path = destination )
  elif format == 'zip.gz':
    with gzip.open( file_path, 'rb' ) as f:
      file_contents = f.read()

    with ModePreservingZipFile( io.BytesIO( file_contents ) ) as f:
      f.extractall( path = destination )

  elif format == 'tar':
    try:
      with tarfile.open( file_path ) as f:
        f.extractall( path = destination )
    except Exception:
      # There seems to a bug in python's tarfile that means it can't read some
      # windows-generated tar files
      os.makedirs( destination )
      with CurrentWorkingDir( destination ):
        subprocess.check_call( [ 'tar', 'zxvf', file_path ] )


def MakeExtensionSymlink( vimspector_base, name, root ):
  MakeSymlink( install.GetGadgetDir( vimspector_base,
                                     install.GetOS() ),
               name,
               os.path.join( root, 'extension' ) ),


def MakeSymlink( in_folder, link, pointing_to ):
  RemoveIfExists( os.path.join( in_folder, link ) )

  in_folder = os.path.abspath( in_folder )
  pointing_to_relative = os.path.relpath( os.path.abspath( pointing_to ),
                                          in_folder )
  link_path = os.path.join( in_folder, link )

  if install.GetOS() == 'windows':
    # While symlinks do exist on Windows, they require elevated privileges, so
    # let's use a directory junction which is all we need.
    link_path = os.path.abspath( link_path )
    if os.path.isdir( link_path ):
      os.rmdir( link_path )
    subprocess.check_call( [ 'cmd.exe',
                             '/c',
                             'mklink',
                             '/J',
                             link_path,
                             pointing_to ] )
  else:
    os.symlink( pointing_to_relative, link_path )


def CloneRepoTo( url, ref, destination ):
  RemoveIfExists( destination )
  git_in_repo = [ 'git', '-C', destination ]
  subprocess.check_call( [ 'git', 'clone', url, destination ] )
  subprocess.check_call( git_in_repo + [ 'checkout', ref ] )
  subprocess.check_call( git_in_repo + [ 'submodule', 'sync', '--recursive' ] )
  subprocess.check_call( git_in_repo + [ 'submodule',
                                         'update',
                                         '--init',
                                         '--recursive' ] )


def AbortIfSUperUser( force_sudo ):
  # TODO: We should probably check the effective uid too
  is_su = False
  if 'SUDO_COMMAND' in os.environ:
    is_su = True

  if is_su:
    if force_sudo:
      print( "*** RUNNING AS SUPER USER DUE TO force_sudo! "
             "    All bets are off. ***" )
    else:
      sys.exit( "This script should *not* be run as super user. Aborting." )
