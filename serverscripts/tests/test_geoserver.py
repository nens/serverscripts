from serverscripts import geoserver

import os


OUR_DIR = os.path.dirname(__file__)


def test_main():
    geoserver.main()


def test_broken_config_file():
    broken_config_example = os.path.join(OUR_DIR, "example_rabbitmq_zabbix_broken.json")
    assert geoserver.load_config(broken_config_example) is None


def test_config_file():
    config_example = os.path.join(OUR_DIR, "example_geoserver.json")
    configuration = geoserver.load_config(config_example)
    assert "geoserver9.lizard.net" in configuration
