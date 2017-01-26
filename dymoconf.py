#!/usr/bin/env python3

import time
import usb
import array

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
               for idx in range (3):
                  self.ep_out.write ("\x1bA\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" 
                                     )
                  print (self.ep_in.read (64))
                  time.sleep (1)

               print ("Bringing up Wifi Interface (?)")

               self.ep_out.write ("\x1bI\x01\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" 
                                  )
               time.sleep (1)

               while True:
                  self.ep_out.write ("\x1bW\x0c\x07\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" 
                                     )
                  data = self.ep_in.read (64)
                  print (data)
                  if data[4] == 0x0a:
                     break
                  time.sleep (1)

               print ("Querying info")

               self.ep_out.write ("\x1bW\x08\x40\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" 
                                  )
               data = self.ep_in.read (64)
               print (data)
               data = self.ep_in.read (64)
               print ("".join (chr(c) for c in data))
               data = self.ep_in.read (64)
               print ("".join (chr(c) for c in data))
               data = self.ep_in.read (64)
               print ("".join (chr(c) for c in data))

               while True:
                  self.ep_out.write ("\x1bW\x0c\x07\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" 
                                     )
                  data = self.ep_in.read (64)
                  print (data)
                  if data[4] == 0x12:
                     break
                  time.sleep (1)

               print ("Reading unknown data")

               self.ep_out.write ("\x1bW\x04\x40\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" 
                                  )
               data = self.ep_in.read (64)
               print (data)
               data = self.ep_in.read (64)
               print (data)

               print ("Initiate Network Scan")

               self.ep_out.write ("\x1bW\x00\x07\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" 
                                  )
               data = self.ep_in.read (64)
               print (data)

               self.ep_out.write ("\x1bW\x0c\x07\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" 
                                  )
               print (self.ep_in.read (64))
               time.sleep (1)

               while True:
                  self.ep_out.write ("\x1bW\x0c\x07\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" 
                                     )
                  data = self.ep_in.read (64)
                  print (data)
                  if data[4] == 0x12:
                     break
                  time.sleep (1)

               print ("reading network data")
               self.ep_out.write ("\x1bW\x01\x40\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" 
                                  )
               data = self.ep_in.read (64)
               print (data)

               networks = []

               for idx in range (data[4]):
                  data = self.ep_in.read (64)
                  networks.append ((data[:6], data[6], data[9:11], data[12:]))

               print ("\n------------")

               for idx in range (len (networks)):
                  n = networks[idx]

                # print ("Address: " + ":".join (["%02x" % c for c in data[:6]]))
                # print ("Channel: %d" % data[6])
                # print ("Managed: %d" % data[7])
                # print ("Power:   %d" % data[8])
                # print (data[9:12])
                # print ("ESSID:   " + "".join (chr (c) for c in data[12:]))

                  print ("%-2d) %s (%s, Ch: %d, Enc: (%d, %d))" %
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

               data = array.array ('B', [0x1b, 0x57, 0x02, 0xc0,
                                         0x00, 0x00, 0x00, 0x00])
               data += n[2]
               data += n[0]
               data += n[3]

               data = data[:64]
               if (len (data) < 64):
                  data += array.array ('B', [0] * (64 - len (data)))

               print ("writing: %r" % data)
               self.ep_out.write (data)

               data = array.array ('B', [ord(c) for c in pw])
               data = data[:64]
               if (len (data) < 64):
                  data += array.array ('B', [0] * (64 - len (data)))

               print ("writing: %r" % data)
               self.ep_out.write (data)

               data = array.array ('B', [0] * 64)

               print ("writing: %r" % data)
               self.ep_out.write (data)

               data = self.ep_in.read (64)
               print (data)
               data = self.ep_in.read (64)
               print (data)
               data = self.ep_in.read (64)
               print (data)

               print ("activating new network (?)")
               self.ep_out.write ("\x1bW\x05\x40\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                  "\x00\x00\x00\x00\x00\x00\x00\x00" 
                                  )
               data = self.ep_in.read (64)
               print (data)

               while True:
                  self.ep_out.write ("\x1bW\x0c\x07\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" +
                                     "\x00\x00\x00\x00\x00\x00\x00\x00" 
                                     )
                  data = self.ep_in.read (64)
                  print (data)
                  if data[4] == 0x02:
                     break
                  time.sleep (1)

if __name__ == '__main__':
   lw = LabelWriter ()

