# Copyright 2014 NEC Corporation.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import abc
import six

from oslo_config import cfg
from oslo_log import log as logging
from pkg_resources import iter_entry_points
from stevedore import driver

from magnum.common import exception


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class Driver(object):

    definitions = None

    @classmethod
    def load_entry_points(cls):
        for entry_point in iter_entry_points('magnum.drivers'):
            yield entry_point, entry_point.load(require=False)

    @classmethod
    def get_drivers(cls):
        '''Retrieves cluster drivers from python entry_points.

        Example:

        With the following classes:
        class Driver1(Driver):
            provides = [
                ('server_type1', 'os1', 'coe1')
            ]

        class Driver2(Driver):
            provides = [
                ('server_type2', 'os2', 'coe2')
            ]

        And the following entry_points:

        magnum.drivers =
            driver_name_1 = some.python.path:Driver1
            driver_name_2 = some.python.path:Driver2

        get_drivers will return:
            {
                (server_type1, os1, coe1):
                    {'driver_name_1': Driver1},
                (server_type2, os2, coe2):
                    {'driver_name_2': Driver2}
            }

        :return: dict
        '''

        if not cls.definitions:
            cls.definitions = dict()
            for entry_point, def_class in cls.load_entry_points():
                for cluster_type in def_class().provides:
                    cluster_type_tuple = (cluster_type['server_type'],
                                          cluster_type['os'],
                                          cluster_type['coe'])
                    providers = cls.definitions.setdefault(cluster_type_tuple,
                                                           dict())
                    providers['entry_point_name'] = entry_point.name
                    providers['class'] = def_class

        return cls.definitions

    @classmethod
    def get_driver(cls, server_type, os, coe):
        '''Get Driver.

        Returns the Driver class for the provided cluster_type.

        With the following classes:
        class Driver1(Driver):
            provides = [
                ('server_type1', 'os1', 'coe1')
            ]

        class Driver2(Driver):
            provides = [
                ('server_type2', 'os2', 'coe2')
            ]

        And the following entry_points:

        magnum.drivers =
            driver_name_1 = some.python.path:Driver1
            driver_name_2 = some.python.path:Driver2

        get_driver('server_type2', 'os2', 'coe2')
        will return: Driver2

        :param server_type: The server_type the cluster definition will build
                            on
        :param os: The operating system the cluster definition will build on
        :param coe: The Container Orchestration Environment the cluster will
                    produce

        :return: class
        '''

        definition_map = cls.get_drivers()
        cluster_type = (server_type, os, coe)

        if cluster_type not in definition_map:
            raise exception.ClusterTypeNotSupported(
                server_type=server_type,
                os=os,
                coe=coe)
        driver_info = definition_map[cluster_type]
        # TODO(muralia): once --drivername is supported as an input during
        # cluster create, change the following line to use driver name for
        # loading.
        return driver.DriverManager("magnum.drivers",
                                    driver_info['entry_point_name']).driver()

    @abc.abstractproperty
    def provides(self):
        '''return a list of (server_type, os, coe) tuples

           Returns a list of cluster configurations supported by this driver
        '''
        raise NotImplementedError("Subclasses must implement 'provides'.")

    @abc.abstractmethod
    def create_cluster(self, context, cluster, cluster_create_timeout):
        raise NotImplementedError("Subclasses must implement "
                                  "'create_cluster'.")

    @abc.abstractmethod
    def update_cluster(self, context, cluster, scale_manager=None,
                       rollback=False):
        raise NotImplementedError("Subclasses must implement "
                                  "'update_cluster'.")

    @abc.abstractmethod
    def delete_cluster(self, context, cluster):
        raise NotImplementedError("Subclasses must implement "
                                  "'delete_cluster'.")