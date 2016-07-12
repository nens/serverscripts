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
        config_data = rabbitmq.load_config(self.config_example)
        pprint(config_data)
        self.assertEquals(len(config_data), 2)
