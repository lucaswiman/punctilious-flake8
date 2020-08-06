import setuptools

requires = [
    "flake8 > 3.0.0",
]

flake8_entry_point = 'flake8.extension'

setuptools.setup(
    name="punctilious-flake8",
    license="MIT",
    version="0.0.1",
    description="Some extra checks for flake8.",
    author="Lucas Wiman",
    author_email="lucas.wiman@gmail.com",
    url="https://github.com/lucaswiman/punctilious-flake8",
    packages=[
        "punctilious_flake8",
    ],
    install_requires=requires,
    entry_points={
        flake8_entry_point: [
            'PNC = punctilious_flake8:Plugin',
        ],
    },
    classifiers=[
        "Framework :: Flake8",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Quality Assurance",
    ],
)