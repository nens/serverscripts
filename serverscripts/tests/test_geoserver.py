from serverscripts import geoserver

import os


OUR_DIR = os.path.dirname(__file__)


def test_broken_config_file():
    broken_config_example = os.path.join(OUR_DIR, "example_rabbitmq_zabbix_broken.json")
    assert geoserver.load_config(broken_config_example) is None


def test_config_file():
    config_example = os.path.join(OUR_DIR, "example_geoserver.json")
    configuration = geoserver.load_config(config_example)
    assert isinstance(configuration, list)
    assert configuration[0]["geoserver_name"] == "geoserver9.lizard.net"


def test_extract_from_logfiles():
    lines = geoserver.extract_from_logfiles(
        os.path.join(OUR_DIR, "example_geoserver_logs/access.log")
    )
    assert len(lines) == 439
    # ^^^ this used to be 210, but now I'm also looking at LAYERS= instead of
    # only layers= in the query parameters...


def test_extract_workspaces_info():
    geoserver_configuration = {
        "geoserver_name": "geoserver.staging.lizard.net",
        "logfile": os.path.join(OUR_DIR, "example_geoserver_logs/access.log"),
        "data_dir": os.path.join(OUR_DIR, "example_geoserver_data/"),
    }
    workspaces = geoserver.extract_workspaces_info(geoserver_configuration)
    assert isinstance(workspaces, list)
    assert "database_server" in workspaces[0]
