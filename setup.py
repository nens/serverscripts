from setuptools import setup


version = "2.12.dev0"

long_description = "\n\n".join([open("README.rst").read(), open("CHANGES.rst").read()])

install_requires = (
    [
        # This shall remain empty upon pain of death.
        #
        # We're being installed on servers and we don't want to pollute the
        # system-wide python lib directory with dependencies.
        #
        # Not even 'six' or 'requests' is allowed. (Note: six.py is included as a
        # file!)
    ],
)

tests_require = [
    "coverage",
    "mock",
    "pytest",
    "pytest-cov",
    "pytest-flakes",
    "pipenv",
    "virtualenv",
]

setup(
    name="serverscripts",
    version=version,
    description="Python scripts for sysadmin tasks on every linux server",
    long_description=long_description,
    # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[],
    keywords=[],
    author="Reinout van Rees",
    author_email="reinout.vanrees@nelen-schuurmans.nl",
    url="",
    license="GPL",
    packages=["serverscripts"],
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={"test": tests_require},
    entry_points={
        "console_scripts": [
            "apache-info = serverscripts.apache:main",
            "checkout-info = serverscripts.checkouts:main",
            "cifsfixer = serverscripts.cifsfixer:main",
            "database-info = serverscripts.database:main",
            "docker-info = serverscripts.docker:main",
            "geoserver-info = serverscripts.geoserver:main",
            "haproxy-info = serverscripts.haproxy:main",
            "nginx-info = serverscripts.nginx:main",
            # The one below runs all above ones, except for cifsfixer
            "gather-all-info = serverscripts.script:main",
        ]
    },
)
