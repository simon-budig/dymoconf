#!/usr/bin/env python3

import sys, time
import ctypes, struct
import usb

class PrintableLittleEndianStructure (ctypes.LittleEndianStructure):
   def __repr__ (self):
      s = "[\n"
      for k in self.__class__._fields_:
         s += "  %s: %r\n" % (k[0], getattr (self, k[0]))
      s += "]"
      return s

class NetworkStatus (PrintableLittleEndianStructure):
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


class LabelWriter (object):
   def __init__ (self):
      self.dev = usb.core.find (idVendor=0x0922, idProduct=0x1007, find_all=True)

      if not self.dev:
         raise ValueError ("LabelWriter not found")

      for d in self.dev:
         cfg = d.get_active_configuration ()
         if cfg is None:
            d.set_configuration ()
         for cfg in d:
            intf = usb.util.find_descriptor (cfg, find_all=True, bInterfaceClass=3)
            for i in intf:
               if d.is_kernel_driver_active (i.bInterfaceNumber):
                  print ("detach")
                  d.detach_kernel_driver (i.bInterfaceNumber)
               print (i)
               for ep in i:
                  print (" - " + repr (ep))

               self.ep_in = usb.util.find_descriptor (i, custom_match = (lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN))
               self.ep_out = usb.util.find_descriptor (i, custom_match = (lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT))

               usb.util.claim_interface (d, i.bInterfaceNumber)


   def sendrecv (self, outdata=None, expect_answer=False):
      if outdata != None:
         # discard pending data
         while True:
            try:
               self.ep_in.read (64, timeout=10)
            except:
               break
         # print ("--> %r" % outdata)
         while outdata:
            self.ep_out.write (outdata[:64])
            outdata = outdata[64:]

      if expect_answer:
         return self.ep_in.read (64, timeout=3000)


   def sendrecv_objcmd (self, cmd, extra_data=b"", expect_answer=True):
      outdata = struct.pack ("<BBBI", 0x1b, ord ("W"),
                             cmd, len (extra_data) + 7)
      outdata += extra_data
      data = self.sendrecv (outdata, expect_answer)
      if expect_answer:
         response_id = data[0]
         length = data[1] + data[2] * 256
         status = data[3]
         target_length = length - len (data)
         data = data[4:]

         while target_length > 0:
            ret = self.sendrecv (expect_answer=True)
            data += ret
            target_length -= len (ret)

         return (response_id, length, status, data)


   def get_network_state (self):
      reply = self.sendrecv_objcmd (0x0c)

      return  NetworkStatus.from_buffer_copy (reply[3])


   def get_system_state (self):
      reply = self.sendrecv ("\x1bA", True)

      return SystemStatus.from_buffer_copy (reply)


   def switch_wifi (self, enable):
      if (enable):
         self.sendrecv ("\x1bI\x01")
      else:
         self.sendrecv ("\x1bI\x00")


   def start_wifi_scan (self):
      self.sendrecv_objcmd (0x00)



if __name__ == '__main__':
   lw = LabelWriter ()

   r = lw.get_system_state ()
   print (r)

   print ("Starting up Wifi: ", end="", flush=True)
   lw.switch_wifi (True)

   while True:
      r = lw.get_network_state ()
      if r.wifi_network_status == 1 or r.wifi_network_status == 3:
         break;
      else:
         print ("%d" % r.wifi_network_status, end="", flush=True)
      print (".", end="", flush=True)
      time.sleep (1)
   print (" done.\n");

   ret = lw.sendrecv_objcmd (0x08, expect_answer=True)
   print (ret)

   ret = lw.sendrecv_objcmd (0x04, b"\x00" * 57, expect_answer=True)
   print (ret)

   print ("Scanning for Wifi Networks: ", end="", flush=True)
   lw.start_wifi_scan ();

   while True:
      r = lw.get_network_state ()
      if r.wifi_scan_status == 2:
         break;
      print (".", end="", flush=True)
      time.sleep (1)
   print (" done.\n");

   print ("Querying scanned networks")
   ret = lw.sendrecv_objcmd (0x01, expect_answer=True)

   networks = []

   data = ret[3]
   num_networks = data[0]
   data = bytes (data[60:])
   print (data)
   for idx in range (num_networks):
      ap      = data[:6]
      managed = data[6]
      enc     = data[9:11]
      name    = data[12:].split (b"\x00")[0]
      networks.append ((ap, managed, enc, name))
      data = data[64:]
      print (data)

   print ("\n------------")

   for idx in range (len (networks)):
      n = networks[idx]

      print ("%2d) %s (%s, Ch: %d, Enc: (%d, %d))" %
             (idx + 1,
              "".join ([chr (c) for c in n[3]]),
              ":".join (["%02x" % c for c in n[0]]),
              n[1],
              n[2][0], n[2][1]))

   nw = -1

   while nw < 0 or nw >= len (networks):
      nw = int (input ("> ")) - 1
   pw = input ("PW: ")

   n = networks[nw]

   data  = b"\x00" + n[2] + n[0] + n[3]
   data += bytes (57 - len (data))
   data += bytes (pw, "utf-8")
   data += bytes (0xc0 - len (data))

   print ("Configuring Wifi")
   ret = lw.sendrecv_objcmd (0x02, data, expect_answer=True)
   print (ret)

   print ("Connecting to Wifi: ", end="", flush=True)
   ret = lw.sendrecv_objcmd (0x05, bytes (57), expect_answer=True)
   print (ret)

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

