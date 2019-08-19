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
        self.vhosts_stdout_example = os.path.join(
            our_dir, 'example_vhosts_stdout_example.txt')

    def test_parse_vhosts_stdout(self):
        vhosts_stdout = ''
        with open(self.vhosts_stdout_example, 'r') as vhosts_file:
            vhosts_stdout = vhosts_file.read()
            pprint(vhosts_stdout)

        vhosts = rabbitmq.parse_vhosts_stdout(vhosts_stdout)
        pprint(vhosts)
        self.assertGreater(len(vhosts), 1)

    def test_parse_vhosts_stdout_empty(self):
        vhosts_stdout = ''
        vhosts = rabbitmq.parse_vhosts_stdout(vhosts_stdout)
        pprint(vhosts)
        self.assertEqual(len(vhosts), 0)

    def test_parse_queues_stdout(self):
        queues_stdout = ''
        with open(self.queues_stdout_example, 'r') as queues_file:
            queues_stdout = queues_file.read()
            pprint(queues_stdout)

        queues = rabbitmq.parse_queues_stdout(queues_stdout)
        pprint(queues)
        self.assertGreater(len(queues), 1)

    def test_get_max_queue(self):
        queues = {'q1': 10, 'q2': 3, 'z': -1}
        result = rabbitmq.get_max_queue(queues)
        expected = ('q1', 10)
        assert result == expected

    def test_load_config_file(self):
        configuration = rabbitmq.load_config(self.config_example)
        self.assertGreater(len(configuration), 0)

    def test_load_config_file_broken_content(self):
        configuration = rabbitmq.load_config(self.broken_config_example)
        self.assertEqual(len(configuration), 0)

    def test_rabbitmqctl_not_exists(self):
        vhost = 'asdasda'
        queues = rabbitmq.retrieve_queues(vhost)
        pprint("'%s' contains '%s' queues." % (vhost, queues))
        self.assertEqual(queues, None)

    def test_rabbitmqctl_vhosts(self):
        vhosts = rabbitmq.retrieve_vhosts()
        pprint("broker contains '%s' vhosts." % vhosts)
        self.assertEqual(vhosts, None)

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
