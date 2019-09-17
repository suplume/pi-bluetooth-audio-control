#!/usr/bin/python

import os
import sys
import dbus
import dbus.service
import time
import json
import bluetooth
import SocketServer
from bluetooth import *
from SimpleHTTPServer import SimpleHTTPRequestHandler
from dbus.mainloop.glib import DBusGMainLoop

class Hid:
    MY_ADDRESS="B8:27:EB:60:2E:1E"
    MY_DEV_NAME="ARemote_Controller"

    P_CTRL =17
    P_INTR =19
    PROFILE_DBUS_PATH="/bluez/acontrol/bthid_profile"
    SDP_RECORD_PATH = sys.path[0] + "/sdp_record.xml"
    UUID="00001124-0000-1000-8000-00805f9b34fb"
    CONTROL_CMDS=[
            0x10, # previous track
            0x40, # next track
            0x20, # play / pause
            ]
    def read_sdp_service_record(self):
        try:
            fh = open(Hid.SDP_RECORD_PATH, "r")
        except:
            sys.exit("SDP record ERROR!")
        return fh.read()

    def close(self):
        self.ccontrol.close()
        self.cinterrupt.close()

    def send_cmd(self, key):
        self.input_report[2] = self.CONTROL_CMDS[key]
        self.cinterrupt.send(str(self.input_report));


    def release_cmd(self):
        self.input_report[2] = 0x00
        self.cinterrupt.send(str(self.input_report));

    def __init__(self):
        self.input_report=bytearray([
                0xa1,
                0x03,
                0x00,
                0x00,
                0x00])
        os.system("hciconfig hcio class 0x00250c")
        os.system("hciconfig hcio name " + self.MY_DEV_NAME)
        os.system("hciconfig hcio piscan")

        service_record=self.read_sdp_service_record()

        opts = {
            "ServiceRecord": service_record,
            "Role":"server",
            "RequireAuthentication": False,
            "RequireAuthorization": False
        }

        bus = dbus.SystemBus()
        manager = dbus.Interface(bus.get_object("org.bluez","/org/bluez"), "org.bluez.ProfileManager1")

        profile = dbus.service.Object(bus, Hid.PROFILE_DBUS_PATH)

        manager.RegisterProfile(Hid.PROFILE_DBUS_PATH, Hid.UUID, opts)

        bus_name = dbus.service.BusName("org.acontrol.bthidservice", bus=dbus.SystemBus())
        dbus.service.Object(bus_name, "/org/acontrol/bthidservice")

        self.scontrol=BluetoothSocket(L2CAP)
        self.sinterrupt=BluetoothSocket(L2CAP)

        self.scontrol.bind((self.MY_ADDRESS, self.P_CTRL))
        self.sinterrupt.bind((self.MY_ADDRESS, self.P_INTR))

        self.scontrol.listen(1)
        self.sinterrupt.listen(1)

        self.ccontrol,cinfo = self.scontrol.accept()
        self.cinterrupt,cinfo = self.sinterrupt.accept()

class JsonResponseHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        content_len = int(self.headers.get("content-length"))
        requestBody = self.rfile.read(content_len).decode('UTF-8')
        jsonData = json.loads(requestBody)
        self.send_response(200)
        self.send_header("Content-type", "Application/json")
        self.end_headers()
        hid.send_cmd(jsonData["control"])
        time.sleep(0.01)
        hid.release_cmd()

if __name__ == "__main__": 
    try:
        DBusGMainLoop(set_as_default=True)
        hid = Hid()
        server = SocketServer.TCPServer(("", 8000), JsonResponseHandler)
        server.serve_forever()
    except KeyboardInterrupt as ex:
        server.server_close()
        hid.close()
    except BluetoothError as ex:
        print("Bluetooth ERROR!")
