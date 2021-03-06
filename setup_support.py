# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the DataLad package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##


import os
from os.path import dirname, join as opj

from distutils.core import Command
from distutils.errors import DistutilsOptionError
import datetime
import formatters as fmt

cmdline_command_names = (
    'containers-list',
    'containers-add',
    'containers-remove',
    'containers-run',
)

def _path_rel2file(p):
    return opj(dirname(__file__), p)


def get_version():
    """Load version of datalad from version.py without entailing any imports
    """
    # This might entail lots of imports which might not yet be available
    # so let's do ad-hoc parsing of the version.py
    with open(opj(dirname(__file__), 'datalad_container', 'version.py')) as f:
        version_lines = list(filter(lambda x: x.startswith('__version__'), f))
    assert (len(version_lines) == 1)
    return version_lines[0].split('=')[1].strip(" '\"\t\n")


class BuildManPage(Command):
    # The BuildManPage code was originally distributed
    # under the same License of Python
    # Copyright (c) 2014 Oz Nahum Tiram  <nahumoz@gmail.com>

    description = 'Generate man page from an ArgumentParser instance.'

    user_options = [
        ('manpath=', None, 'output path for manpages'),
        ('rstpath=', None, 'output path for RST files'),
        ('parser=', None, 'module path to an ArgumentParser instance'
         '(e.g. mymod:func, where func is a method or function which return'
         'a dict with one or more arparse.ArgumentParser instances.'),
    ]

    def initialize_options(self):
        self.manpath = opj('build', 'man')
        self.rstpath = opj('docs', 'source', 'generated', 'man')
        self.parser = 'datalad.cmdline.main:setup_parser'

    def finalize_options(self):
        if self.manpath is None:
            raise DistutilsOptionError('\'manpath\' option is required')
        if self.rstpath is None:
            raise DistutilsOptionError('\'rstpath\' option is required')
        if self.parser is None:
            raise DistutilsOptionError('\'parser\' option is required')
        self.manpath = _path_rel2file(self.manpath)
        self.rstpath = _path_rel2file(self.rstpath)
        mod_name, func_name = self.parser.split(':')
        fromlist = mod_name.split('.')
        try:
            mod = __import__(mod_name, fromlist=fromlist)
            self._parser = getattr(mod, func_name)(
                ['datalad'],
                formatter_class=fmt.ManPageFormatter,
                return_subparsers=True)

        except ImportError as err:
            raise err

        self.announce('Writing man page(s) to %s' % self.manpath)
        self._today = datetime.date.today()

    def run(self):

        dist = self.distribution
        #homepage = dist.get_url()
        #appname = self._parser.prog
        appname = 'datalad'

        sections = {
            'Authors': """{0} is developed by {1} <{2}>.""".format(
                appname, dist.get_author(), dist.get_author_email()),
        }

        dist = self.distribution
        for cls, opath, ext in ((fmt.ManPageFormatter, self.manpath, '1'),
                                (fmt.RSTManPageFormatter, self.rstpath, 'rst')):
            if not os.path.exists(opath):
                os.makedirs(opath)
            for cmdname in cmdline_command_names:
                p = self._parser[cmdname]
                cmdname = "{0}{1}".format(
                    'datalad-' if cmdname != 'datalad' else '',
                    cmdname)
                format = cls(cmdname, ext_sections=sections, version=get_version())
                formatted = format.format_man_page(p)
                with open(opj(opath, '{0}.{1}'.format(
                        cmdname,
                        ext)),
                        'w') as f:
                    f.write(formatted)


class BuildRSTExamplesFromScripts(Command):
    description = 'Generate RST variants of example shell scripts.'

    user_options = [
        ('expath=', None, 'path to look for example scripts'),
        ('rstpath=', None, 'output path for RST files'),
    ]

    def initialize_options(self):
        self.expath = opj('docs', 'examples')
        self.rstpath = opj('docs', 'source', 'generated', 'examples')

    def finalize_options(self):
        if self.expath is None:
            raise DistutilsOptionError('\'expath\' option is required')
        if self.rstpath is None:
            raise DistutilsOptionError('\'rstpath\' option is required')
        self.expath = _path_rel2file(self.expath)
        self.rstpath = _path_rel2file(self.rstpath)
        self.announce('Converting example scripts')

    def run(self):
        opath = self.rstpath
        if not os.path.exists(opath):
            os.makedirs(opath)

        from glob import glob
        for example in glob(opj(self.expath, '*.sh')):
            exname = os.path.basename(example)[:-3]
            with open(opj(opath, '{0}.rst'.format(exname)), 'w') as out:
                fmt.cmdline_example_to_rst(
                    open(example),
                    out=out,
                    ref='_example_{0}'.format(exname))
