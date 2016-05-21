# -*- coding: utf-8 -*-
""" Code by Armin Ronacher.

https://github.com/mitsuhiko/rust-setuptools
"""
from __future__ import print_function

import os
import sys
import shutil
import subprocess

from distutils.cmd import Command
from distutils.command.install_lib import install_lib


if sys.platform == 'win32':
    DYNAMIC_LIB_SUFFIX = '.dll'
elif sys.platform == 'darwin':
    DYNAMIC_LIB_SUFFIX = '.dylib'
else:
    DYNAMIC_LIB_SUFFIX = '.so'


class RustBuildCommand(Command):
    description = 'build rust crates into Python extensions'

    user_options = []

    def initialize_options(self):
        for k, v in self.__class__.rust_build_args.items():
            setattr(self, k, v)

    def finalize_options(self):
        pass

    def run(self):
        if self.debug:
            debug_or_release = '--debug'
        else:
            debug_or_release = '--release'

        # Make sure that if pythonXX-sys is used, it builds against the
        # current executing python interpreter.
        bindir = os.path.dirname(sys.executable)
        if sys.platform == 'win32':
            path_sep = ';'
        else:
            path_sep = ':'

        env = dict(os.environ)
        env.update({
            # disables rust's pkg-config seeking for specified packages,
            # which causes pythonXX-sys to fall back to detecting the
            # interpreter from the path.
            'PYTHON_2.7_NO_PKG_CONFIG': '1',
            'PATH':  bindir + path_sep + env.get('PATH', '')
        })

        for crate_path, dest in self.cargo_crates:
            # Execute cargo.
            try:
                toml = os.path.join(crate_path, 'Cargo.toml')
                args = (['cargo', 'build', '--manifest-path', toml,
                    debug_or_release] + list(self.extra_cargo_args or []))
                if not self.quiet:
                    print(' '.join(args), file=sys.stderr)
                output = subprocess.check_output(args, env=env)
            except subprocess.CalledProcessError as e:
                msg = 'cargo failed with code: %d\n%s' % (e.returncode, e.output)
                raise Exception(msg)
            except OSError:
                raise Exception('Unable to execute cargo - this package '
                    'requires rust to be installed and cargo to be on the PATH')

            if not self.quiet:
                print(output, file=sys.stderr)

            # Find the shared library that cargo hopefully produced and copy
            # it into the build directory as if it were produced by
            # build_cext.
            if self.debug:
                suffix = 'debug'
            else:
                suffix = 'release'

            dylib_path = os.path.join(crate_path, 'target/', suffix)

            # Ask build_ext where the shared library would go if it had built it,
            # then copy it there.
            build_ext = self.get_finalized_command('build_ext')

            target = os.path.dirname(build_ext.get_ext_fullpath('x'))
            try:
                os.makedirs(target)
            except OSError:
                pass

            target = os.path.join(target, dest)

            for filename in os.listdir(dylib_path):
                if filename.endswith(DYNAMIC_LIB_SUFFIX):
                    shutil.copy(os.path.join(dylib_path, filename),
                                os.path.join(target, filename))


def build_rust_cmdclass(crates, debug=False,
                        extra_cargo_args=None, quiet=False):
    class _RustBuildCommand(RustBuildCommand):
        rust_build_args = {
            'cargo_crates': crates,
            'debug': debug,
            'extra_cargo_args': extra_cargo_args,
            'quiet': quiet,
        }

    return _RustBuildCommand


def build_install_lib_cmdclass(base=None):
    if base is None:
        base = install_lib
    class _RustInstallLibCommand(base):
        def build(self):
            base.build(self)
            if not self.skip_build:
                self.run_command('build_rust')
    return _RustInstallLibCommand


def rust_crates(dist, attr, value):
    dist.is_pure = lambda: False
    dist.cmdclass['build_rust'] = build_rust_cmdclass(value)
    dist.cmdclass['install_lib'] = build_install_lib_cmdclass(
        dist.cmdclass.get('install_lib'))
