# dymoconf.py

This is a python script to allow configuring the Wireless configuration
from Linux hosts.

It started from reverse-engineering the USB protocol, but got a huge
boost from the DYMO Software Development team, who actually turned out
to be approachable and were happy to provide detailed information about
the protocol. Thanks, I appreciate that a lot!

Obviously all bugs in this program are my fault, not theirs.



## usage

To use this script simply run the python script with sufficient
privileges to access the printers USB device - e.g. by starting it as
root.

It will then talk to the printer and start a Wifi Scan on the printer.
After 10-30s the discovered networks will be printed. Find your desired
network and enter its number at the prompt. The script will then prompt
for the Wifi password (it will be shown in clear text when you type it
in!)

In the end it will activate the new network configuration in the
printer.

If the printer behaves weird or no longer responds for some reason
unplug it from USB and remove the battery for a few seconds.



## Technical Background ("the missing manual")

Dymo has published a very useful Technical Reference for its LabelWriter
family of printers, at the time of writing this is available at
http://download.dymo.com/dymo/technical-data-sheets/LW%20450%20Series%20Technical%20Reference.pdf .

It describes in detail the commands for the labelwriters, which also
incorporates some tape-specific commands since there are labelwriters
that also can print label tape.

However, since there apparently are no wireless labelwriters, this
reference fails to document the commands necessary for the configuration
necessary. The following is a description of my understanding of the
additional commands. Use at your own risk...

These commands are sent to the HID interface of the printer. I have not
yet tested sending these to the Printer interface (when enabled).


### <esc> I _n_    Set Wifi Interface Status

1b 40 ?

 _n_ | result
-----|-------
0x00 | disable wifi interface
0x01 | enable wifi interface

This enables or disables the wifi interface. It takes some time to wake
up, allow a little bit of time (>= 1s) before querying the wifi state.


### <esc> Z 0x01

1b 5a 01

This switches the printer to a different USB profile, where a USB
printer interface is available in addition to a HID and Mass Storage
interfaces.


### <esc> W _n_ _l1_ _l2_ _l3_ _l4_ _n1_.._nx_

1b 57 ? ? ? ? ? ? ?

This is an interface to the configuration storage of the printer. _n_
identifies an object, _l1_ to _l4_ specify the length of the data
(including the command itself, little endian) and _n1_ to _nx_ are the
extra payload data.

The response to this command consists of a single byte response-id, a
two byte length value (total amount of data in the response) plus a
single status byte, followed by the payload of the response.

I know about the following object / response ids


#### Object 0x00   Initiate Wireless Network Scan

1b 57 00 07 00 00 00

This initiates a network scan. This will take some time to finish. The
state of the scan can be queried via the 0x0c object.


#### Object 0x01   Query Network Scan Results

1b 57 01 07 00 00 00

When the scan has finished (check via the 0x0c object) this object
contains the scanned networks. Response: 0x81


#### Object 0x02   Set Network Config

1b 57 02 c0 00 00 00 < 185 bytes of network parameters >

This sets the network parameters for the desired network. this command
consists of three HID packages a 64 bytes, the data is padded with
zeroes, the total size of the configuration command is 192 bytes.

[TODO: description of the bytes follows]


#### Object 0x04   (TODO)

This gets queried by the dymo setup tool, have not yet figured out what
this is good for - it has Response 0x84 which in my case is all zeroes.


#### Object 0x05   (TODO) Activate New Network Configuration

1b 57 05 40 00 00 00 <57 zeroes>

This seems to be necessary to activate the new network configuration.
This expects 57 bytes of zeroes as data (i.e. padded to 64 bytes).


#### Object 0x08   (TODO) Query Network Interface

1b 57 08 07 00 00 00

This queries information about the network interface. Among other
information this contains the MAC-Address of the printer.

(TODO: after power on this returns 00:01:02:03:04:05, not sure what is
necessary to get the *actual* mac-address there...)


#### Object 0x0c   Query Network Status

1b 57 0c 07 00 00 00

This queries the wifi network status. Response: 0x8c




#### Response 0x81    Network Scan Response

#### Response 0x84    (TODO)

#### Response 0x8c    Network Status Repsponse

0x8c 0xc0 0x00 <status> <network status>
