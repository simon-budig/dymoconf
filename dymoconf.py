#!/usr/bin/env python3

# dymoconf.py
#
# a small utility to scan and configure networks for the
# DYMO LabelManager Wireless PnP
#
# (c) 2017 Simon Budig <simon@budig.de>
#
# Thanks to the DYMO Software Development team
# for providing insight into the data structures being handed around.

import sys, time
import ctypes
import usb

class PrintableLittleEndianStructure (ctypes.LittleEndianStructure):
   def __repr__ (self):
      s = "[\n"
      for k in self.__class__._fields_:
         s += "  %s: %r\n" % (k[0], getattr (self, k[0]))
      s += "]"
      return s


class NetworkStatus (PrintableLittleEndianStructure):
   # The response to the ESC W <0x0c> command
   # (response ID <0x8c>)
   _fields_ = [
      ("general_status",           ctypes.c_uint8, 3),
      ("wifi_scan_status",         ctypes.c_uint8, 3),
      ("flash_status",             ctypes.c_uint8, 2),

      ("wifi_connection_status",   ctypes.c_uint8, 4),
      ("wifi_network_status",      ctypes.c_uint8, 4),

      ("wired_connection_status",  ctypes.c_uint8, 4),
      ("wired_network_status",     ctypes.c_uint8, 4),

      ("wifi_signal_strength",     ctypes.c_uint8, 7),
      ("wifi_signal_status",       ctypes.c_uint8, 1),

      ("flash_updating_progress",  ctypes.c_uint8, 7),
      ("flash_updating_readiness", ctypes.c_uint8, 1),
   ]


class SystemStatus (PrintableLittleEndianStructure):
   # The response to the ESC A command
   _fields_ = [
      ("reserved",             ctypes.c_uint8, 2),
      ("tape_jam",             ctypes.c_uint8, 1),
      ("overheated",           ctypes.c_uint8, 1),
      ("cutter_jam",           ctypes.c_uint8, 1),
      ("printer_busy",         ctypes.c_uint8, 1),
      ("cassette_present",     ctypes.c_uint8, 1),
      ("auto_cutter_enabled",  ctypes.c_uint8, 1),

      ("tape_width_detail",    ctypes.c_uint8),

      ("battery_details",      ctypes.c_uint8, 4),
      ("battery_status",       ctypes.c_uint8, 2),
      ("external_pwr_present", ctypes.c_uint8, 1),
      ("low_power",            ctypes.c_uint8, 1),

      ("battery_charge_level", ctypes.c_uint8),
      ("raw_battery_voltage",  ctypes.c_uint16),
   ]


class ObjCmd (PrintableLittleEndianStructure):
   # the request for an ESC W command
   _pack_ = 1
   _fields_ = [
      ("escape", ctypes.c_uint8),
      ("W",      ctypes.c_uint8),
      ("obj_id", ctypes.c_uint8),
      ("length", ctypes.c_uint32),
   ]


class ObjResp (PrintableLittleEndianStructure):
   # the response to an ESC W command
   _pack_ = 1
   _fields_ = [
      ("response_id", ctypes.c_uint8),
      ("length",      ctypes.c_uint16),
      ("status",      ctypes.c_uint8),
   ]


class NetworkInfo (PrintableLittleEndianStructure):
   _fields_ = [
      ("ap",       ctypes.c_uint8 * 6),
      ("channel",  ctypes.c_uint8),
      ("UNKNOWN1", ctypes.c_uint8 * 2),
      ("enc",      ctypes.c_uint8 * 2),
      ("UNKNOWN2", ctypes.c_uint8),
      ("essid",    ctypes.c_uint8 * 32),
   ]

class LabelManager (object):
   def __init__ (self):
      # LabelManager PnP has two personalities...
      self.dev = usb.core.find (idVendor  = 0x0922,
                                idProduct = 0x1008)
      if not self.dev:
         self.dev = usb.core.find (idVendor  = 0x0922,
                                   idProduct = 0x1007)
         if not self.dev:
            raise ValueError ("LabelManager not found")

      d = self.dev

      self.serialno = usb.util.get_string (d, d.iSerialNumber)

      cfg = d.get_active_configuration ()
      if cfg is None:
         d.set_configuration ()

      for cfg in d:
         intf = usb.util.find_descriptor (cfg, find_all=True, bInterfaceClass=3)
         for i in intf:
            if d.is_kernel_driver_active (i.bInterfaceNumber):
               d.detach_kernel_driver (i.bInterfaceNumber)
            # print (i)
            # for ep in i:
            #    print (" - " + repr (ep))

            self.ep_in = usb.util.find_descriptor (i, custom_match = (lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN))
            self.ep_out = usb.util.find_descriptor (i, custom_match = (lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT))

            usb.util.claim_interface (d, i.bInterfaceNumber)

   def sendrecv (self, outdata=None, expect_answer=False):
      if outdata != None:
         # discard pending data
         try:
            while True:
               self.ep_in.read (64, timeout=10)
         except usb.core.USBError:
            pass
         # print ("--> %r" % outdata)
         while outdata:
            self.ep_out.write (outdata[:64])
            outdata = outdata[64:]

      if expect_answer:
         indata = bytes (self.ep_in.read (64, timeout=3000))
         # print ("<-- %r" % indata)
         return indata


   def sendrecv_objcmd (self, cmd, extra_data=b"", expect_answer=True):
      outdata = bytes (ObjCmd (0x1b, ord ("W"), cmd, len (extra_data) + 7))
      outdata += extra_data
      data = self.sendrecv (outdata, expect_answer)
      if expect_answer:
         resp = ObjResp.from_buffer_copy (data)
         target_length = resp.length - len (data)
         data = data[4:]

         while target_length > 0:
            ret = self.sendrecv (expect_answer=True)
            data += ret
            target_length -= len (ret)

         # print ("Object %02x --> Response %02x (%d bytes)" %
         #        (cmd, resp.response_id, resp.length))

         return (resp.response_id, resp.length, resp.status, data)


   def get_network_state (self):
      reply = self.sendrecv_objcmd (0x0c)

      return  NetworkStatus.from_buffer_copy (reply[3])


   # Object 0x08 contains at least the MAC address of the wifi interface
   def get_interface_info (self):
      ret = lw.sendrecv_objcmd (0x08, expect_answer=True)
      return (ret[3][4:10])


   def get_system_state (self):
      reply = self.sendrecv ("\x1bA", True)

      return SystemStatus.from_buffer_copy (reply)


   def set_enable_wifi (self, enable):
      if (enable):
         self.sendrecv ("\x1bI\x01")
      else:
         self.sendrecv ("\x1bI\x00")


   def set_network_config (self, network):
      data  = b"\x00"
      data += bytes (network.enc)
      data += bytes (network.ap)
      data += bytes (network.essid)
      data += bytes (57 - len (data))   # padding to the 1st hid package
      data += bytes (pw, "utf-8")
      data += bytes (0xb9 - len (data)) # padding to the 3rd hid package

      ret = self.sendrecv_objcmd (0x02, data, expect_answer=True)
      # print (ret)
      # what does it return?


   # actually it is not clear yet what object 0x05 does.
   def set_network_active (self):
      return self.sendrecv_objcmd (0x05, bytes (57), expect_answer=True)


   def start_wifi_scan (self):
      self.sendrecv_objcmd (0x00)


   def get_scanned_networks (self):
      ret = self.sendrecv_objcmd (0x01, expect_answer=True)

      networks = []

      data = ret[3]
      num_networks = data[0]
      data = bytes (data[60:])
      while data:
         network = NetworkInfo.from_buffer_copy (data)
         networks.append (network)
         data = data[64:]

      return networks



if __name__ == '__main__':
   try:
      lw = LabelManager ()
   except ValueError:
      print ("No LabelManager found")
      sys.exit (-1)

   print ("Connected to LabelManager (serial no. %s)" % lw.serialno)
   r = lw.get_system_state ()
   # print (r)

   print ("Starting up Wifi: ", end="", flush=True)
   lw.set_enable_wifi (True)
   # needs some time to settle - otherwise ESC W <0x0c> might not respond
   time.sleep (1)

   while True:
      r = lw.get_network_state ()
      if r.wifi_network_status == 1 or r.wifi_network_status == 3:
         break;
      else:
         print ("%d" % r.wifi_network_status, end="", flush=True)
      print (".", end="", flush=True)
      time.sleep (1)
   print (" done.\n");

   mac_addr = lw.get_interface_info ()
   print ("MAC-Address: " + "-".join (["%02x" % c for c in mac_addr]))

   # ret = lw.sendrecv_objcmd (0x04, b"\x00" * 57, expect_answer=True)
   # print (ret)

   print ("Scanning for Wifi Networks: ", end="", flush=True)
   lw.start_wifi_scan ();

   while True:
      r = lw.get_network_state ()
      if r.wifi_scan_status == 2:
         break;
      print (".", end="", flush=True)
      time.sleep (1)
   print (" done.\n");

   print ("Networks found:")
   networks = lw.get_scanned_networks ()

   idx = 1
   for n in networks:
      print ("%2d) %s (%s, Ch: %d, Enc: (%d, %d))" %
             (idx,
              "".join ([chr (c) for c in n.essid]),
              ":".join (["%02x" % c for c in n.ap]),
              n.channel,
              n.enc[0], n.enc[1]))
      idx += 1

   nw = -1

   print ("\nEnter target network number:")
   while nw < 0 or nw >= len (networks):
      nw = int (input ("--> ")) - 1
   pw = input ("Password: ")

   # print ("Configuring Wifi")
   lw.set_network_config (networks[nw])

   print ("Connecting to Wifi: ", end="", flush=True)

   while True:
      r = lw.get_network_state ()
      if r.wifi_connection_status == 2:
         break;
      if r.wifi_connection_status >= 3:
         print ("\nwifi failed to connect with status %d" % r.wifi_connection_status)
         sys.exit (-1)
      print (".", end="", flush=True)
      time.sleep (1)
   print (" done.\n");

