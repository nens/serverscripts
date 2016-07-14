import json
from pprint import pprint
from serverscripts import rabbitmq
from unittest import TestCase

import os


class GitAndEggInfoTestCase(TestCase):

    def setUp(self):
        our_dir = os.path.dirname(__file__)
        self.config_example = os.path.join(
            our_dir, 'example_rabbitmq_zabbix.json')
        self.broken_config_example = os.path.join(
            our_dir, 'example_rabbitmq_zabbix_broken.json')
        self.queues_stdout_example = os.path.join(
            our_dir, 'example_queues_stdout_example.txt')

    def test_parse_queues_stdout(self):
        queues_stdout = ''
        with open(self.queues_stdout_example, 'r') as queues_file:
            queues_stdout = queues_file.read()
            pprint(queues_stdout)
            
        queues = rabbitmq.parse_queues_stdout(queues_stdout)
        pprint(queues)
        self.assertGreater(len(queues), 1)

    def test_get_max_queue(self):
        test_case = ('q1', 10)
        queues = {'q1': 10, 'q2': 3, 'z': -1}
        result = rabbitmq.get_max_queue(queues)
        self.assertEquals(result, test_case)

    def test_load_config_file(self):
        status, content = rabbitmq.load_config(self.config_example)
        self.assertEquals((status, isinstance(content, dict)), (rabbitmq.SUCCEEDED, True))

    def test_load_config_file_broken_content(self):
        status, content = rabbitmq.load_config(self.broken_config_example)
        self.assertEquals(status, rabbitmq.FAILED)

    def test_rabbitmqctl_not_exists(self):
        vhost = 'asdasda'
        status, result = rabbitmq.retrieve_queues(vhost)
        pprint("Status %s, result %s" % (status, result))
        self.assertEquals(status, rabbitmq.FAILED)

    def test_validate_configuration_empty(self):
        configuration = {}
        is_valid =  rabbitmq.validate_configuration(configuration)
        self.assertFalse(is_valid)

    def test_validate_configuration_no_messages_limit(self):
        configuration = {
            'flooding': {'queues_limit': 23},
            'lizard-nxt': {'queues_limit': 1, 'messages_limit': 200}
        }
        is_valid =  rabbitmq.validate_configuration(configuration)
        self.assertFalse(is_valid)

    def test_validate_configuration_no_queues_limit(self):
        configuration = {
            'flooding': {'queues_limit': 23, 'messages_limit': 200},
            'lizard-nxt': {'messages_limit': 200}
        }
        is_valid =  rabbitmq.validate_configuration(configuration)
        self.assertFalse(is_valid)

    def test_validate_configuration_queues_not_int(self):
        configuration = {
            'flooding': {'queues_limit': 'dfdf', 'messages_limit': 200},
            'lizard-nxt': {'messages_limit': '200', 'queues_limit': 1}
        }
        is_valid =  rabbitmq.validate_configuration(configuration)
        self.assertFalse(is_valid)

    def test_validate_configuration_messages_not_int(self):
        configuration = {
            'flooding': {'queues_limit': 22, 'messages_limit': ''},
            'lizard-nxt': {'messages_limit': 200, 'queues_limit': 1}
        }
        is_valid =  rabbitmq.validate_configuration(configuration)
        self.assertFalse(is_valid)

    def test_validate_configuration_valid(self):
        configuration = {
            'flooding': {'queues_limit': 22, 'messages_limit': 22},
            'lizard-nxt': {'messages_limit': '20', 'queues_limit': 1}
        }
        is_valid =  rabbitmq.validate_configuration(configuration)
        self.assertTrue(is_valid)
