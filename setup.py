import os
import setuptools
from testipy import __app__, __version__, __author__, __author_email__


curr_path = os.path.dirname(os.path.abspath(__file__))


readme = os.path.join(curr_path, "README.md")
print(f"Reading {readme}")
try:
    with open(readme, "r") as fh:
        long_description = fh.read()
except Exception:
    long_description = """
    Testing tool for python with:
      - Test selection/execution
      - Test management
      - Test reporting
    """

requirements = os.path.join(curr_path, "testipy", "requirements.txt")
print(f"Installing {requirements}")
with open(requirements, "r") as fr:
    install_requires = [
        line.strip() for line in fr if line.strip() and not line.startswith("#")
    ]


extras_require = {
    "dev": [
        "pre-commit>=2.21",
        "flake8>=3.9",
    ]
}


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
    packages=setuptools.find_namespace_packages(include=("*",)),
    include_package_data=True,
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={"console_scripts": ["testipy = testipy.__main__:run_testipy"]},
    keywords=["testing", "reporting", "behave"],
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)
