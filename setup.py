#
#> python3 -m pip install --user --upgrade setuptools wheel
#
#> python3 setup.py sdist bdist_wheel
#> python3 -m pip install --user --upgrade twine
#> python3 -m twine upload dist/muteria-<version>.tar.gz
#> rm -rf dist build muteria.egg-info __pycache__/
#

import os
from setuptools import setup, find_packages

thisdir = os.path.dirname(os.path.abspath(__file__))

# get __version__, _framework_name
exec(open(os.path.join(thisdir, 'muteria', '_version.py')).read())

def get_long_description():
    with open(os.path.join(thisdir, "README.md"), "r") as fh:
        long_description = fh.read()
    return long_description

def get_requirements_list():
    """
    requirements_list = []
    with open(os.path.join(thisdir, "requirements.txt"), "r") as fh:
        for line in fh:
            req = line.strip().split()
            if len(req) > 0 and not req[0].startswith('#'):
                requirements_list.append(req[0])
    """
    requirements_list = [
        "numpy",
        "pandas",
        "scipy",
        "matplotlib",
        "networkx",
        "gitpython",
        "tqdm",
        "joblib",
        #docker # https://docker-py.readthedocs.io/en/stable/index.html
        #sh # easy subprocess creation
        #enum #(python 2.7)

        # SERVER
        #"flask",
        #"flask_socketio"
    ]

    return requirements_list

setup(
    # This is the name of your PyPI-package.
    name=_framework_name,    
    python_requires='>3.3.0',
    # Update the version number for new releases
    version=__version__,
    description='Software Analysis and Testing Framework',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    author='Thierry Titcheu Chekam',
    author_email='thierry_tct@yahoo.com',
    url='https://github.com/muteria/muteria',
    packages = ['muteria'],
    #packages=find_packages(),
    #py_modules = ['_version'],
    include_package_data=True,
    install_requires = get_requirements_list(),
    # The name of your scipt, and also the command you'll be using for calling it
    #scripts=['cli/muteria'],
    entry_points={
        'console_scripts': [
            'muteria=muteria.cli.cli:main',
        ],
    },

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Natural Language :: English',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
        'Operating System :: POSIX :: BSD',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ]
)
