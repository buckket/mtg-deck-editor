from setuptools import setup

setup(
    name='mtg-deck-editor',
    version='1.0.0',

    url='https://github.com/buckket/mtg-deck-editor',

    author='buckket',
    author_email='buckket@cock.li',

    packages=['mtgdeckeditor'],
    package_data={
        '': ['*.GtkBuilder'],
    },

    zip_safe=True,
    include_package_data=True,

    platforms='any',

    install_requires=[
        'pyxdg',
        'requests',
        'requests-cache',
        'html5lib',
        'matplotlib',
        'PyGObject',
        'setuptools',
        'pip'
    ],

    entry_points={
        'gui_scripts': [
            'mtg-deck-editor = mtgdeckeditor.__main__:main',
        ]
    },

    description='A GUI deck editor for the card game Magic: The Gathering.',
    long_description=open('./README.rst', 'r').read(),

    keywords=['mtg', 'deck editor', 'card game'],

    license='GPLv3',
    classifiers=[
        'Programming Language :: Python',
        'Operating System :: OS Independent',
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Games/Entertainment',
    ],
)
