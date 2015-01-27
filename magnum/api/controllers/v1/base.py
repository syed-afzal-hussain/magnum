# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import pecan
import wsme
from wsme import types as wtypes

from magnum.api.controllers import base
from magnum.api.controllers.v1 import types
from magnum.common import exception
from magnum.common import urlfetch
from magnum import objects


class K8sResourceBase(base.APIBase):

    _bay_uuid = None

    def _get_bay_uuid(self):
        return self._bay_uuid

    def _set_bay_uuid(self, value):
        if value and self._bay_uuid != value:
            try:
                bay = objects.Bay.get(pecan.request.context, value)
                self._bay_uuid = bay.uuid
            except exception.BayNotFound as e:
                # Change error code because 404 (NotFound) is inappropriate
                # response for a POST request to create a Service
                e.code = 400  # BadRequest
                raise e
        elif value == wtypes.Unset:
            self._bay_uuid = wtypes.Unset

    bay_uuid = wsme.wsproperty(types.uuid, _get_bay_uuid, _set_bay_uuid,
                               mandatory=True)
    """Unique UUID of the bay this runs on"""

    manifest_url = wtypes.text
    """URL for service file to create the service"""

    manifest = wtypes.text
    """Data for service to create the service"""

    def _get_manifest(self):
        if self.manifest is not wsme.Unset and self.manifest is not None:
            return self.manifest
        if (self.manifest_url is not wsme.Unset
                and self.manifest_url is not None):
            self.manifest = urlfetch.get(self.manifest_url)
            return self.manifest
