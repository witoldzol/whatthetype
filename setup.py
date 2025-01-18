from setuptools import setup
import pathlib

# Read the contents of your README file
current_directory = pathlib.Path(__file__).parent
long_description = (current_directory / "README.md").read_text()

setup(
    name="whatthetype",
    version="0.9",
    packages=["whatthetype"],
    author="Witold Zolnowski",
    description="Derives type hints from data captured during runtime. Updates source files with type hints. USE SOURCE CONTROL before upating in-place!!!!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["autopep8>=2.0.0"],
)
