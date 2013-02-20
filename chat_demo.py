#!/usr/bin/env python
#------------------------------------------------------------------------------
#   chat_demo.py
#   Copyright 2009 Jim Storch
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain a
#   copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#------------------------------------------------------------------------------

"""
Chat Room Demo for Miniboa.
"""

from miniboa import TelnetServer, AUTOSENSING

IDLE_TIMEOUT = 300
CLIENT_LIST = []
SERVER_RUN = True


def on_connect(client):
    """
    Sample on_connect function.
    Handles new connections.
    """
    print("Connection from %s accepted." % client.addrport())
    client.detect_term_caps()
    broadcast('^R%s ^Yjoins the Server.\n^d' % client.addrport() )
    CLIENT_LIST.append(client)
    client.send_cc("^s^RWelcome to the ^YServer^R, %s.\n^dType 'help' for list of commands" % client.addrport() )


def on_disconnect(client):
    """
    Sample on_disconnect function.
    Handles lost connections.
    """
    print("%s disconnected" % client.addrport())
    CLIENT_LIST.remove(client)
    broadcast('^R%s ^Yleaves the Server.\n^d' % client.addrport() )


def kick_idle():
    """
    Looks for idle clients and disconnects them by setting active to False.
    """
    ## Who hasn't been typing?
    for client in CLIENT_LIST:
        if client.idle() > IDLE_TIMEOUT:
            print('-- Kicking idle client from %s' % client.addrport())
            broadcast("^YKicked ^R%s's ^Yass out for being idle too long!\n^d" % client.addrport())
            client.active = False


def process_clients():
    """
    Check each client, if client.cmd_ready == True then there is a line of
    input available via client.get_command().
    """
    
    for client in CLIENT_LIST:
        if(client.client_state == AUTOSENSING):
            client.check_auto_sense()
            return        
        if client.active and client.cmd_ready:
            ## If the client sends input echo it to the chat room
            chat(client)


def broadcast(msg):
    """
    Send msg to every client.
    """
    for client in CLIENT_LIST:
        client.send_cc(msg)


def chat(client):
    """
    Echo whatever client types to everyone.
    """
    global SERVER_RUN
    msg = client.get_command()
    #print('^R%s says, ^B"%s"^d' % (client.addrport(), msg))

    for guest in CLIENT_LIST:
        if guest != client:
            guest.send_cc('^R%s says,^Y %s\n^d' % (client.addrport(), msg))
        else:
            guest.send_cc('^RYou say,^Y %s\n^d' % msg)

    cmd = msg.lower()
    ## bye = disconnect
    if cmd == 'bye':
        client.active = False
    ## shutdown == stop the server
    elif cmd == 'shutdown':
        SERVER_RUN = False
    elif cmd == 'pmodeon':
        eon(client)
    elif cmd == 'pmodeoff':
        eof(client)
    elif cmd == 'stat':
        dostat(client)
    elif cmd == 'help':
        dohelp(client)
        
def eon(client):
    client.send_cc("^YEcho toggled: ^RON^Y.^d\n")
    client.password_mode_on()
    client.telnet_echo_password = True
    
def eof(client):
    client.send_cc("^YEcho toggled: ^ROFF^Y.^d\n")
    client.password_mode_off()
    client.telnet_echo_password = False

def dostat(client):
    client.send_cc("^G**************** ^YCurrent Telnet Stats ^G****************\n")
    client.send_cc("^YBytes Sent:^R %i\n^d" % (client.bytes_sent))
    client.send_cc("^YBytes Received:^R %i\n^d" % (client.bytes_received))
    client.send_cc("^YTerminal Type:^R %s\n^d" % (client.terminal_type))
    client.send_cc("^YTerminal Speed:^R %s\n^d" % (client.terminal_speed))
    client.send_cc("^YWindow Size:^R %s x %s\n^d" % (client.columns, client.rows))
    client.send_cc("\n^G**************** ^YTelnet Options ^G****************^d\n")
    if len(client.telnet_opt_dict) < 1:
        client.send_cc("^YNo Telnet Options Requested or Set^d\n")
    for key in client.telnet_opt_dict:
        client.send_cc("^YClient:^R %s ^YValue: ^R%s\n^d" % (client.telnet_opt_dict[key].option_text, client.telnet_opt_dict[key].remote_option))
        client.send_cc("^YServer:^R %s ^YValue: ^R%s\n^d" % (client.telnet_opt_dict[key].option_text, client.telnet_opt_dict[key].local_option))
    client.send_cc("\n^G****************************************************^d\n")
        
def dohelp(client):
    client.send_cc("\n^G**************** ^YCommands ^G****************^d\n")
    client.send_cc("^YCurrent available commands are:\n")
    client.send_cc("^Rbye - Logs you out\n")
    client.send_cc("shutdown - shuts down the server\n")
    client.send_cc("stat - Show the status of your connection\n")
    client.send_cc("pmodeon - turns password mode on (echo off)\n")
    client.send_cc("pmodeoff - turns password mode off (echo on)\n")
    client.send_cc("\n^G********************************************^d\n")
        
#------------------------------------------------------------------------------
#       Main
#------------------------------------------------------------------------------

if __name__ == '__main__':

    ## Simple chat server to demonstrate connection handling via the
    ## async and telnet modules.

    ## Create a telnet server with a port, address,
    ## a function to call with new connections
    ## and one to call with lost connections.

    telnet_server = TelnetServer(
        port=7777,
        address='',
        on_connect=on_connect,
        on_disconnect=on_disconnect,
        timeout = .05
        )

    print(">> Listening for connections on port %d.  CTRL-C to break."
        % telnet_server.port)

    ## Server Loop
    while SERVER_RUN:
        telnet_server.poll()        ## Send, Recv, and look for new connections
        kick_idle()                 ## Check for idle clients
        process_clients()           ## Check for client input

    print(">> Server shutdown.")
