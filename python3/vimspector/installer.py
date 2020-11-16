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
import contextlib
import functools
import gzip
import hashlib
import io
import os
import shutil
import ssl
import string
import subprocess
import sys
import tarfile
import time
import traceback
import zipfile
import json

from vimspector import install, gadgets

OUTPUT_VIEW = None


class Options:
  vimspector_base = None
  no_check_certificate = False
  quiet = False


options = Options()


def Configure( **kwargs ):
  for k, v in kwargs.items():
    setattr( options, k, v )


def Print( *args, **kwargs ):
  if not options.quiet:
    print( *args, **kwargs )


class MissingExecutable( Exception ):
  pass


def GetPATHAsList():
  paths = os.environ[ 'PATH' ].split( os.pathsep )
  if install.GetOS() == 'windows':
    paths.insert( 0, os.getcwd() )
  return paths


def FindExecutable( executable: str, paths=None ):
  if not paths:
    paths = GetPATHAsList()

  if install.GetOS() == 'windows':
    extensions = [ '.exe', '.bat', '.cmd' ]
  else:
    extensions = [ '' ]

  for extension in extensions:
    if executable.endswith( extension ):
      candidate = executable
    else:
      candidate = executable + extension

    for path in paths:
      filename = os.path.abspath( os.path.join( path, candidate ) )
      if not os.path.isfile( filename ):
        continue
      if not os.access( filename, os.F_OK | os.X_OK ):
        continue

      return filename

  raise MissingExecutable( f"Unable to find executable { executable } in path" )



def CheckCall( cmd, *args, **kwargs ):
  cmd[ 0 ] = FindExecutable( cmd[ 0 ] )

  if options.quiet:
    try:
      subprocess.check_output( cmd, *args, stderr=subprocess.STDOUT, **kwargs )
    except subprocess.CalledProcessError as e:
      print( e.output.decode( 'utf-8' ) )
      raise
  else:
    subprocess.check_call( cmd, *args, **kwargs )


def PathToAnyWorkingPython3():
  # We can't rely on sys.executable because it's usually 'vim' (fixme, not with
  # neovim?)
  paths = GetPATHAsList()

  if install.GetOS() == 'windows':
    candidates = [ os.path.join( sys.exec_prefix, 'python.exe' ),
                   'python.exe' ]
  else:
    candidates = [ os.path.join( sys.exec_prefix, 'bin', 'python3' ),
                   'python3',
                   'python' ]

  for candidate in candidates:
    try:
      return FindExecutable( candidate, paths=paths )
    except MissingExecutable:
      pass

  raise RuntimeError( "Unable to find a working python3" )


def RunInstaller( api_prefix, leave_open, *args, **kwargs ):
  from vimspector import utils, output, settings
  import vim

  if not args:
    args = settings.List( 'install_gadgets' )

  if not args:
    return

  args = GadgetListToInstallerArgs( *args )

  vimspector_home = utils.GetVimValue( vim.vars, 'vimspector_home' )
  vimspector_base_dir = utils.GetVimspectorBase()

  global OUTPUT_VIEW
  _ResetInstaller()

  with utils.RestoreCurrentWindow():
    vim.command( f'botright { settings.Int( "bottombar_height" ) }new' )
    win = vim.current.window
    OUTPUT_VIEW = output.OutputView( win, api_prefix )

  cmd = [
    PathToAnyWorkingPython3(),
    '-u',
    os.path.join( vimspector_home, 'install_gadget.py' ),
    '--quiet',
    '--update-gadget-config',
  ]
  if not vimspector_base_dir == vimspector_home:
    cmd.extend( [ '--basedir', vimspector_base_dir ] )
  cmd.extend( args )

  def handler( exit_code ):
    if exit_code == 0:
      if not leave_open:
        _ResetInstaller()
      utils.UserMessage( "Vimspector gadget installation complete!" )
      vim.command( 'silent doautocmd User VimspectorInstallSuccess' )
      if 'then' in kwargs:
        kwargs[ 'then' ]()
    else:
      utils.UserMessage( 'Vimspector gadget installation reported errors',
                         error = True )
      vim.command( 'silent doautocmd User VimspectorInstallFailed' )


  OUTPUT_VIEW.RunJobWithOutput( 'Installer',
                                cmd,
                                completion_handler = handler,
                                syntax = 'vimspector-installer' )
  OUTPUT_VIEW.ShowOutput( 'Installer' )


def RunUpdate( api_prefix, leave_open, *args ):
  from vimspector import utils, settings
  Configure( vimspector_base = utils.GetVimspectorBase() )

  insatller_args = list( args )
  insatller_args.extend( settings.List( 'install_gadgets' ) )

  current_adapters = ReadAdapters( read_existing = True )
  for adapter_name in current_adapters.keys():
    insatller_args.extend( FindGadgetForAdapter( adapter_name ) )

  if insatller_args:
    insatller_args.append( '--upgrade' )
    RunInstaller( api_prefix, leave_open, *insatller_args )


def _ResetInstaller():
  global OUTPUT_VIEW
  if OUTPUT_VIEW:
    OUTPUT_VIEW.Reset()
    OUTPUT_VIEW = None


def Abort():
  _ResetInstaller()
  from vimspector import utils
  utils.UserMessage( 'Vimspector installation aborted',
                     persist = True,
                     error = True )


def GadgetListToInstallerArgs( *gadget_list ):
  installer_args = []
  for name in gadget_list:
    if name.startswith( '-' ):
      installer_args.append( name )
      continue

    try:
      gadget = gadgets.GADGETS[ name ]
    except KeyError:
      continue

    if not gadget.get( 'enabled', True ):
      installer_args.append( f'--force-enable-{ gadget[ "language" ] }' )
    else:
      installer_args.append( f'--enable-{ gadget[ "language" ] }' )

  return installer_args


def FindGadgetForAdapter( adapter_name ):
  candidates = []
  for name, gadget in gadgets.GADGETS.items():
    v = {}
    v.update( gadget.get( 'all', {} ) )
    v.update( gadget.get( install.GetOS(), {} ) )

    adapters = {}
    adapters.update( v.get( 'adapters', {} ) )
    adapters.update( gadget.get( 'adapters', {} ) )

    if adapter_name in adapters:
      candidates.append( name )

  return candidates


class Manifest:
  manifest: dict

  def __init__( self ):
    self.manifest = {}
    self.Read()

  def Read( self ):
    try:
      with open( install.GetManifestFile( options.vimspector_base ), 'r' ) as f:
        self.manifest = json.load( f )
    except OSError:
      pass

  def Write( self ):
    with open( install.GetManifestFile( options.vimspector_base ), 'w' ) as f:
      json.dump( self.manifest, f )


  def Clear( self, name: str ):
    try:
      del self.manifest[ name ]
    except KeyError:
      pass


  def Update( self, name: str,  gadget_spec: dict ):
    self.manifest[ name ] = gadget_spec


  def RequiresUpdate( self, name: str, gadget_spec: dict ):
    try:
      current_spec = self.manifest[ name ]
    except KeyError:
      # It's new.
      return True

    # If anything changed in the spec, update
    if not current_spec == gadget_spec:
      return True

    # Always update if the version string is 'master'. Probably a git repo
    # that pulls master (which tbh we shouldn't have)
    if current_spec.get( 'version' ) in ( 'master', '' ):
      return True
    if current_spec.get( 'repo', {} ).get( 'ref' ) == 'master':
      return True

    return False


def ReadAdapters( read_existing = True ):
  all_adapters = {}
  if read_existing:
    try:
      with open( install.GetGadgetConfigFile( options.vimspector_base ),
                 'r' ) as f:
        all_adapters = json.load( f ).get( 'adapters', {} )
    except OSError:
      pass

  # Include "built-in" adapter for multi-session mode
  all_adapters.update( {
    'multi-session': {
      'port': '${port}',
      'host': '${host}'
    },
  } )

  return all_adapters


def WriteAdapters( all_adapters, to_file=None ):
  adapter_config = json.dumps ( { 'adapters': all_adapters },
                                indent=2,
                                sort_keys=True )

  if to_file:
    to_file.write( adapter_config )
  else:
    with open( install.GetGadgetConfigFile( options.vimspector_base ),
               'w' ) as f:
      f.write( adapter_config )


def InstallGeneric( name, root, gadget ):
  extension = os.path.join( root, 'extension' )
  for f in gadget.get( 'make_executable', [] ):
    MakeExecutable( os.path.join( extension, f ) )

  MakeExtensionSymlink( name, root )


def InstallCppTools( name, root, gadget ):
  extension = os.path.join( root, 'extension' )

  # It's hilarious, but the execute bits aren't set in the vsix. So they
  # actually have javascript code which does this. It's just a horrible horrible
  # hack that really is not funny.
  MakeExecutable( os.path.join( extension, 'debugAdapters', 'OpenDebugAD7' ) )
  with open( os.path.join( extension, 'package.json' ) ) as f:
    package = json.load( f )
    runtime_dependencies = package[ 'runtimeDependencies' ]
    for dependency in runtime_dependencies:
      for binary in dependency.get( 'binaries' ):
        file_path = os.path.abspath( os.path.join( extension, binary ) )
        if os.path.exists( file_path ):
          MakeExecutable( os.path.join( extension, binary ) )

  MakeExtensionSymlink( name, root )


def InstallBashDebug( name, root, gadget ):
  MakeExecutable( os.path.join( root, 'extension', 'bashdb_dir', 'bashdb' ) )
  MakeExtensionSymlink( name, root )


def InstallDebugpy( name, root, gadget ):
  wd = os.getcwd()
  root = os.path.join( root, 'debugpy-{}'.format( gadget[ 'version' ] ) )
  os.chdir( root )
  try:
    CheckCall( [ sys.executable, 'setup.py', 'build' ] )
  finally:
    os.chdir( wd )

  MakeSymlink( name, root )


def InstallTclProDebug( name, root, gadget ):
  configure = [ 'sh', './configure' ]

  if install.GetOS() == 'macos':
    # Apple removed the headers from system frameworks because they are
    # determined to make life difficult. And the TCL configure scripts are super
    # old so don't know about this. So we do their job for them and try and find
    # a tclConfig.sh.
    #
    # NOTE however that in Apple's infinite wisdom, installing the "headers" in
    # the other location is actually broken because the paths in the
    # tclConfig.sh are pointing at the _old_ location. You actually do have to
    # run the package installation which puts the headers back in order to work.
    # This is why the below list is does not contain stuff from
    # /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform
    #  '/Applications/Xcode.app/Contents/Developer/Platforms'
    #    '/MacOSX.platform/Developer/SDKs/MacOSX.sdk/System'
    #    '/Library/Frameworks/Tcl.framework',
    #  '/Applications/Xcode.app/Contents/Developer/Platforms'
    #    '/MacOSX.platform/Developer/SDKs/MacOSX.sdk/System'
    #    '/Library/Frameworks/Tcl.framework/Versions'
    #    '/Current',
    for p in [ '/usr/local/opt/tcl-tk/lib' ]:
      if os.path.exists( os.path.join( p, 'tclConfig.sh' ) ):
        configure.append( '--with-tcl=' + p )
        break


  with CurrentWorkingDir( os.path.join( root, 'lib', 'tclparser' ) ):
    CheckCall( configure )
    CheckCall( [ 'make' ] )

  MakeSymlink( name, root )


def InstallNodeDebug( name, root, gadget ):
  with CurrentWorkingDir( root ):
    CheckCall( [ 'npm', 'install' ] )
    CheckCall( [ 'npm', 'run', 'build' ] )
  MakeSymlink( name, root )


def InstallLuaLocal( name, root, gadget ):
  with CurrentWorkingDir( root ):
    CheckCall( [ 'npm', 'install' ] )
    CheckCall( [ 'npm', 'run', 'build' ] )
  MakeSymlink( name, root )


def InstallGagdet( name: str,
                   gadget: dict,
                   manifest: Manifest,
                   succeeded: list,
                   failed: list,
                   all_adapters: dict ):

  try:
    # Spec is an os-specific definition of the gadget
    spec = {}
    spec.update( gadget.get( 'all', {} ) )
    spec.update( gadget.get( install.GetOS(), {} ) )

    def save_adapters():
      # allow per-os adapter overrides. v already did that for us...
      all_adapters.update( spec.get( 'adapters', {} ) )
      # add any other "all" adapters
      all_adapters.update( gadget.get( 'adapters', {} ) )

    if 'download' in gadget:
      if 'file_name' not in spec:
        raise RuntimeError( "Unsupported OS {} for gadget {}".format(
          install.GetOS(),
          name ) )

      print( f"Installing {name}@{spec[ 'version' ]}..." )
      spec[ 'download' ] = gadget[ 'download' ]
      if not manifest.RequiresUpdate( name, spec ):
        save_adapters()
        print( " - Skip - up to date" )
        return

      destination = os.path.join(
        install.GetGadgetDir( options.vimspector_base ),
        'download',
        name,
        spec[ 'version' ] )

      url = string.Template( gadget[ 'download' ][ 'url' ] ).substitute( spec )

      file_path = DownloadFileTo(
        url,
        destination,
        file_name = gadget[ 'download' ].get( 'target' ),
        checksum = spec.get( 'checksum' ),
        check_certificate = not options.no_check_certificate )

      root = os.path.join( destination, 'root' )
      ExtractZipTo(
        file_path,
        root,
        format = gadget[ 'download' ].get( 'format', 'zip' ) )
    elif 'repo' in gadget:
      url = string.Template( gadget[ 'repo' ][ 'url' ] ).substitute( spec )
      ref = string.Template( gadget[ 'repo' ][ 'ref' ] ).substitute( spec )

      print( f"Installing {name}@{ref}..." )
      spec[ 'repo' ] = gadget[ 'repo' ]
      if not manifest.RequiresUpdate( name, spec ):
        save_adapters()
        print( " - Skip - up to date" )
        return

      destination = os.path.join(
        install.GetGadgetDir( options.vimspector_base ),
        'download',
        name )
      CloneRepoTo( url, ref, destination )
      root = destination

    if 'do' in gadget:
      gadget[ 'do' ]( name, root, spec )
    else:
      InstallGeneric( name, root, spec )

    save_adapters()
    manifest.Update( name, spec )
    succeeded.append( name )
    print( f" - Done installing {name}" )
  except Exception as e:
    if not options.quiet:
      traceback.print_exc()
    failed.append( name )
    print( f" - FAILED installing {name}: {e}".format( name, e ) )


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
  Print( 'Making executable: {}'.format( file_path ) )
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
        Print( "Failed - {}, will retry in {} seconds".format( e, timeout ) )
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
        Print( "Checksum matches for {}, using it".format( file_path ) )
        return file_path
      else:
        Print( "Checksum doesn't match for {}, removing it".format(
          file_path ) )

    Print( "Removing existing {}".format( file_path ) )
    os.remove( file_path )

  r = request.Request( url, headers = { 'User-Agent': 'Vimspector' } )

  Print( "Downloading {} to {}/{}".format( url, destination, file_name ) )

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
    Print( "Checksum for {}: {}".format( file_path,
                                         GetChecksumSHA254( file_path ) ) )

  return file_path


def GetChecksumSHA254( file_path ):
  with open( file_path, 'rb' ) as existing_file:
    return hashlib.sha256( existing_file.read() ).hexdigest()


def ValidateCheckSumSHA256( file_path, checksum ):
  existing_sha256 = GetChecksumSHA254( file_path )
  return existing_sha256 == checksum


def RemoveIfExists( destination ):
  try:
    os.remove( destination )
    Print( "Removed file {}".format( destination ) )
    return
  except OSError:
    pass

  N = 1


  def BackupDir():
    return "{}.{}".format( destination, N )

  while os.path.isdir( BackupDir() ):
    Print( "Removing old dir {}".format( BackupDir() ) )
    try:
      shutil.rmtree( BackupDir() )
      Print ( "OK, removed it" )
      break
    except OSError as e:
      Print ( f"FAILED to remove {BackupDir()}: {e}" )
      N = N + 1

  if os.path.exists( destination ):
    Print( "Removing dir {}".format( destination ) )
    try:
      shutil.rmtree( destination )
    except OSError:
      Print( "FAILED, moving {} to dir {}".format( destination, BackupDir() ) )
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
  Print( "Extracting {} to {}".format( file_path, destination ) )
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
        CheckCall( [ 'tar', 'zxvf', file_path ] )


def MakeExtensionSymlink( name, root ):
  MakeSymlink( name, os.path.join( root, 'extension' ) ),


def MakeSymlink( link, pointing_to, in_folder = None ):
  if not in_folder:
    in_folder = install.GetGadgetDir( options.vimspector_base )

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
    CheckCall( [ 'cmd.exe', '/c', 'mklink', '/J', link_path, pointing_to ] )
  else:
    os.symlink( pointing_to_relative, link_path )


def CloneRepoTo( url, ref, destination ):
  RemoveIfExists( destination )
  git_in_repo = [ 'git', '-C', destination ]
  CheckCall( [ 'git', 'clone', url, destination ] )
  CheckCall( git_in_repo + [ 'checkout', ref ] )
  CheckCall( git_in_repo + [ 'submodule', 'sync', '--recursive' ] )
  CheckCall( git_in_repo + [ 'submodule', 'update', '--init', '--recursive' ] )


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
