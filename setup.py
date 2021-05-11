# -*- coding: utf-8 -*-

import sys
#from distutils.core import setup
from setuptools import setup
import py2exe
import struct
from wxtail import __doc__ as doc, __version__, appName

NVERSION = __version__
APLICACION = appName
DESCRIPCION = doc
AUTOR = 'Juan Hevilla Guerrero'
AUTOR_EMAIL = 'j.hevilla@diagram.es'
URL_EMPRESA = 'http://www.diagram.es/'
NOM_EMPRESA = 'Diagram Software, S.L'
COPYRIGHT = '(C) Diagram Software, S.L'
LICENCIA = 'Software propietario'

bits = struct.calcsize("P") * 8
if bits == 64:
    # bundle_files = 3
    bundle_files = 1
else:
    bundle_files = 1


class Target(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


includes = []

excludes = ['Carbon', 'readline']

packages = []

dll_excludes = []

icon_resources = [(1, "wxtail.ico")]
bitmap_resources = []
other_resources = []

data = {
    "icon_resources": icon_resources,
    "bitmap_resources": bitmap_resources,
    "other_resources": other_resources,
    "version": NVERSION,
    "company_name": NOM_EMPRESA,
    "copyright": COPYRIGHT,
    "name": APLICACION,
    "script": f"{APLICACION}.py",
}

windows_target = Target(**data)

data = {
    "options": {
        "py2exe": {
            "compressed": 2,
            "optimize": 2,
            "includes": includes,
            "excludes": excludes,
            "packages": packages,
            "dll_excludes": dll_excludes,
            "bundle_files": bundle_files,
            "dist_dir": "dist",
            "xref": False,
            "skip_archive": False,
            "ascii": False,
            "custom_boot_script": ''
        }
    },
    "data_files": [],
    "zipfile": None,
    "name": APLICACION,
    "version": NVERSION,
    "description": DESCRIPCION,
    "author": AUTOR,
    "author_email": AUTOR_EMAIL,
    "maintainer": AUTOR,
    "maintainer_email": AUTOR_EMAIL,
    "url": URL_EMPRESA,
    "windows": [windows_target],
}

setup(**data)
