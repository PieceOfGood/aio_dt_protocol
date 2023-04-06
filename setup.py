from setuptools import setup, find_packages
import re
from pathlib import Path


NAME = "aio_dt_protocol"
CURRENT_DIR = Path(__file__).parent
DIST_DIR = CURRENT_DIR / "build"
INIT_FILE_PATH = CURRENT_DIR / NAME / "__init__.py"

with open(INIT_FILE_PATH, encoding="utf-8") as f:
    INIT_CONTENT = f.read()

VERSION: str = re.findall(r"__version__[^\"']+\"([^\"']+)", INIT_CONTENT)[0]
AUTHOR: str = re.findall(r"__author__[^\"']+\"([^\"']+)", INIT_CONTENT)[0]
EMAIL: str = re.findall(r"__email__[^\"']+\"([^\"']+)", INIT_CONTENT)[0]

PACKAGES = find_packages()

with open("README.md", encoding="utf-8") as f:
    DESCRIPTION = f.read()


setup(
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=EMAIL,
    description="Asynchronous wrapper over Chromium browser debugger protocol.",
    long_description=DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/PieceOfGood/aio_dt_protocol",
    license="BSD 3-Clause",
    packages=PACKAGES,
    install_requires=["websockets>=10.0.0"],

    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX"
    ]
)
