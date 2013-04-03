from distutils.core import setup

import tokenize, pydoc

def get_module_meta(modfile):
    docstring = None
    version = [(tokenize.NAME, '__version__'), (tokenize.OP, '=')]
    f = open(modfile,'r')
    for toknum, tokval, _, _, _ in tokenize.generate_tokens(lambda: f.readline()):
        if not docstring:
            if toknum == tokenize.STRING:
                docstring = tokval
                continue
        if len(version):
            if (toknum, tokval) == version[0]:
                version.pop(0)
        else:
            version = tokval
            break
    if docstring is None:
        raise ValueError("could not find docstring in %s" % modfile)
    if not isinstance(version, basestring):
        raise ValueError("could not find __version__ in %s" % modfile)
    # unquote :
    docstring = docstring[3:]
    docstring = docstring[:-3]
    version = version[1:]
    version = version[:-1]
    return (version,) + pydoc.splitdoc(docstring)

version, description, long_description = get_module_meta("./scholar/__init__.py")

setup(
        name='GoogleScholar',
        version='0.2',
        description='Fetch information from Google Scholar',
        author='Luciano Bello',
        author_email='luciano (a) debian (.) org',
        url='https://github.com/lbello/chalmers-web/tree/master/scholar',
        packages=['scholar',],
        license='Do What the Fuck You Want to Public License',
        long_description=long_description,
)
