import os
import setuptools
from testipy import __app__, __version__, __author__, __author_email__


app_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(app_path)
print(f"installing from {app_path}")


with open("README.md", "r") as fh:
    long_description = fh.read()


with open("testipy/requirements.txt", "r") as fr:
    install_requires = str(fr.read()).split("\n")
print("requires -", install_requires)


setuptools.setup(
    name=__app__,
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    description="Python test selection/execution/reporting tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pjn2work/testipy",
    setup_requires=["wheel"],
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    entry_points={"console_scripts": ["testipy = testipy.__main__:run_testipy"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9'
)
