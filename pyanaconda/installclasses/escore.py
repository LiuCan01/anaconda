#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from pyanaconda.installclass import BaseInstallClass
from pyanaconda.product import productName
from pyanaconda import network
from pyanaconda import nm
from pyanaconda.kickstart import getAvailableDiskSpace
from blivet.partspec import PartSpec
from blivet.platform import platform
from blivet.devicelibs import swap
from blivet.size import Size

class ESBaseInstallClass(BaseInstallClass):
    name = "EasyStack Cloud Linux"
    sortPriority = 30001
    if not productName.startswith("EasyStack Cloud Linux"):
        hidden = True
    defaultFS = "xfs"

    bootloaderTimeoutDefault = 5

    ignoredPackages = ["ntfsprogs", "reiserfs-utils", "hfsplus-tools"]

    installUpdates = False

    _l10n_domain = "comps"

    efi_dir = "escore"

    help_placeholder = "ESCorePlaceholder.html"
    help_placeholder_with_links = "ESCorePlaceholderWithLinks.html"

    def configure(self, anaconda):
        BaseInstallClass.configure(self, anaconda)
        self.setDefaultPartitioning(anaconda.storage)

    def setNetworkOnbootDefault(self, ksdata):
        if any(nd.onboot for nd in ksdata.network.network if nd.device):
            return
        # choose the device used during installation
        # (ie for majority of cases the one having the default route)
        dev = network.default_route_device() \
              or network.default_route_device(family="inet6")
        if not dev:
            return
        # ignore wireless (its ifcfgs would need to be handled differently)
        if nm.nm_device_type_is_wifi(dev):
            return
        network.update_onboot_value(dev, "yes", ksdata)

    def __init__(self):
        BaseInstallClass.__init__(self)

class ESAtomicInstallClass(ESBaseInstallClass):
    name = "ESCore Atomic Host"
    sortPriority=21001
    hidden = not productName.startswith(("ESCore Atomic Host", "ESCore Linux Atomic"))

    def setDefaultPartitioning(self, storage):
        autorequests = [PartSpec(mountpoint="/", fstype=storage.defaultFSType,
                                size=Size("1GiB"), maxSize=Size("3GiB"), grow=True, lv=True)]

        bootreqs = platform.setDefaultPartitioning()
        if bootreqs:
            autorequests.extend(bootreqs)

        disk_space = getAvailableDiskSpace(storage)
        swp = swap.swapSuggestion(disk_space=disk_space)
        autorequests.append(PartSpec(fstype="swap", size=swp, grow=False,
                                    lv=True, encrypted=True))

        for autoreq in autorequests:
            if autoreq.fstype is None:
                if autoreq.mountpoint == "/boot":
                    autoreq.fstype = storage.defaultBootFSType
                    autoreq.size = Size("300MiB")
                else:
                    autoreq.fstype = storage.defaultFSType

        storage.autoPartitionRequests = autorequests

