from setuptools import setup, find_packages
 
setup(
    # This is the name of your PyPI-package.
    name='muteria',    
    python_requires='>3.2.2',
    # Update the version number for new releases
    version='0.0',
    description='Software Analysis and Testing Framework',
    author='Thierry Titcheu Chekam',
    author_email='thierry_tct@yahoo.com',
    url='https://github.com/muteria/muteria',
    #packages = [],
    packages=find_packages(),
    include_package_data=True,
    #install_requires = [],
    # The name of your scipt, and also the command you'll be using for calling it
    scripts=['muteria'],

    classifiers=[
        'Development Status :: 1 - Alpha',
        'Natural Language :: English',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Analysis',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
        'Operating System :: POSIX :: BSD',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ]
)