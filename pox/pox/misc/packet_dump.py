# Copyright 2012 James McCauley
#
# This file is part of POX.
#
# POX is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# POX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with POX.  If not, see <http://www.gnu.org/licenses/>.

"""
A simple component that dumps packet_in info to the log.

Use --verbose for really verbose dumps.
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt
from pox.lib.util import dpidToStr

log = core.getLogger()

_verbose = None
_max_length = None
_types = None
_show_by_default = None

def _handle_PacketIn (event):
  packet = event.parsed

  show = _show_by_default
  p = packet
  while p:
    if p.__class__.__name__.lower() in _types:
      if _show_by_default:
        # This packet is hidden
        return
      else:
        # This packet should be shown
        show = True
        break
      return
    if not hasattr(p, 'next'): break
    p = p.next

  if not show: return

  msg = dpidToStr(event.dpid) + ": "
  msg = ""
  if _verbose:
    msg += packet.dump()
  else:
    p = packet
    while p:
      if isinstance(p, basestring):
        msg += "[%s bytes]" % (len(p),)
        break
      msg += "[%s]" % (p.__class__.__name__,)
      p = p.next

  if _max_length:
    if len(msg) > _max_length:
      msg = msg[:_max_length-3]
      msg += "..."
  core.getLogger("dump:" + dpidToStr(event.dpid)).debug(msg)


def launch (verbose = False, max_length = 110, full_packets = True,
            hide = '', show = ''):
  global _verbose, _max_length, _types, _show_by_default
  _verbose = verbose
  _max_length = max_length
  hide = hide.replace(',', ' ').replace('|', ' ')
  hide = set([p.lower() for p in hide.split()])
  show = show.replace(',', ' ').replace('|', ' ')
  show = set([p.lower() for p in show.split()])

  if hide and show:
    raise RuntimeError("Can't both show and hide packet types")

  if show:
    _types = show
  else:
    _types = hide
  _show_by_default = not not hide

  if full_packets:
    # Send full packets to controller
    core.openflow.miss_send_len = 0xffff

  core.openflow.addListenerByName("PacketIn", _handle_PacketIn)

  log.info("Packet dumper running")
