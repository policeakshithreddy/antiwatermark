from setuptools import setup, find_packages

setup(
    name="antiwatermark",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "antiwatermark=antiwatermark.cli:main",
        ],
    },
    install_requires=[],
    python_requires=">=3.8",
)
