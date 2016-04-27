# -*- coding: utf-8 -*-
import json
import os
import uuid

import pytest

from sqlalchemydiff.util import CompareResult, InspectorFactory, IgnoreManager
from mock import Mock, patch, call


class TestCompareResult(object):

    def test___init__(self):
        info, errors = Mock(), Mock()

        result = CompareResult(info, errors)

        assert info == result.info
        assert errors == result.errors

    def test_is_match(self):
        info, errors = {}, {}
        result = CompareResult(info, errors)

        assert True == result.is_match

        result.errors = {1: 1}
        assert False == result.is_match

    def test_dump_info(self):
        info = {'some': 'info'}
        filename = '{}.txt'.format(uuid.uuid4())
        result = CompareResult(info, {})

        result.dump_info(filename=filename)

        with open(filename, 'rU') as stream:
            assert info == json.loads(stream.read())

        os.unlink(filename)

    def test_dump_errors(self):
        errors = {'some': 'errors'}
        filename = '{}.txt'.format(uuid.uuid4())
        result = CompareResult({}, errors)

        result.dump_errors(filename=filename)

        with open(filename, 'rU') as stream:
            assert errors == json.loads(stream.read())

        os.unlink(filename)


class TestInspectorFactory(object):

    @pytest.yield_fixture
    def create_engine_mock(self):
        with patch('sqlalchemydiff.util.create_engine') as m:
            yield m

    @pytest.yield_fixture
    def inspect_mock(self):
        with patch('sqlalchemydiff.util.inspect') as m:
            yield m

    def test_from_uri(self, inspect_mock, create_engine_mock):
        uri = 'some-db-uri/some-db-name'
        inspector = InspectorFactory.from_uri(uri)

        create_engine_mock.assert_called_once_with(uri)
        inspect_mock.assert_called_once_with(create_engine_mock.return_value)

        assert inspect_mock.return_value == inspector


class TestIgnoreManager:

    @pytest.fixture
    def ignore_data(self):
        return [
            'table-A.pk.id',
            'table-A.fk.user_id',
            'table-A.fk.address_id',
            'table-B.pk.root_id',
            'table-C.col.telephone',
            'table-C.idx.admin_id',
        ]

    def test_init_empty(self):
        im = IgnoreManager([])

        assert {} == im.ignore

    def test_init(self, ignore_data):
        im = IgnoreManager(ignore_data)

        expected_map = {
            'table-A': {
                'pk': ['id'],
                'fk': ['user_id', 'address_id'],
            },
            'table-B': {
                'pk': ['root_id'],
            },
            'table-C': {
                'col': ['telephone'],
                'idx': ['admin_id'],
            },
        }

        assert expected_map == im.ignore

    def test_init_strip(self):
        ignore_data = ['  table-A  .  pk  .  id  ']

        im = IgnoreManager(ignore_data)

        expected_map = {
            'table-A': {
                'pk': ['id']
            }
        }

        assert expected_map == im.ignore

    def test_identifier_incorrect(self):
        ignore_data = ['table-A.unknown.some-name']

        with pytest.raises(ValueError) as err:
            IgnoreManager(ignore_data)

        assert (
            "unknown is invalid. It must be in ['pk', 'fk', 'idx', 'col']",
        ) == err.value.args

    @pytest.mark.parametrize('clause',
        [
            'none',
            'too.few',
            'too.many.definitely.for-sure',
        ]
    )
    def test_incorrect_clause(self, clause):
        ignore_data = [clause]

        with pytest.raises(ValueError) as err:
            IgnoreManager(ignore_data)

        assert (
            '{} is not a well formed clause: table_name.identifier.name'
            .format(clause),
        ) == err.value.args

    @pytest.mark.parametrize('clause',
        [
            '.pk.b',
            'a.pk.',
        ]
    )
    def test_incorrect_empty_clause(self, clause):
        ignore_data = [clause]

        with pytest.raises(ValueError) as err:
            IgnoreManager(ignore_data)

        assert (
            '{} is not a well formed clause: table_name.identifier.name'
            .format(clause),
        ) == err.value.args


# test empty clause between dots (all three positions)
# test type error on single clause
# test get
# ...
