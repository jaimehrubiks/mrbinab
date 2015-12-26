import asyncio
import threading

import telepot
import time
from telepot.delegate import per_chat_id
from telepot.async.delegate import create_open

"""
NAME:           Mr. bINAB telegram bot
AUTHOR:         Jaime Hidalgo García
DESCRIPTION:    Proof of concept for DHSAI [Distributed human simulated artificial intelligence]

THANKS TO:      - Telegram.
                - Telepot lib (by nickoala)

CONTRIBUTORS:

LICENSE:        BPL V3 in file "LICENSE"
"""

# Configuration
TIMEOUT_SECONDS = 200


# End configuration


class User(telepot.helper.ChatHandler):

    def __init__(self, seed_tuple, timeout):
        super(User, self).__init__(seed_tuple, timeout)
        self._connected = False
        self._id = None
        self._peerid = None

    @asyncio.coroutine
    def open(self, initial_msg, seed):
        yield from self.sender.sendMessage('boot_message')
        return True  # prevent on_message() from being called on the initial message

    @asyncio.coroutine
    def disconnect(self, remote):
        yield from self.sender.sendMessage(u"forced_disconnect")
        if remote:
            yield from user_list.get(self._peerid).disconnect(False)
        raise telepot.helper.WaitTooLong

    @asyncio.coroutine
    def start_peer(self, peerid):
        self._peerid = peerid
        self._connected = True
        yield from self.sender.sendMessage(u"connected_a2")

    @asyncio.coroutine
    def send_message(self, message):
        yield from self.sender.sendMessage(message)

    @asyncio.coroutine
    def on_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance2(msg)

        if content_type != 'text':
            return

        message = msg['text']

        if not self._connected:

            if self._id is None: self._id = msg['from']['id']
            if self._id not in user_list: user_list[self._id] = self

            if message == "/init":
                self._peerid = in_out_queue(self._id)
                if self._peerid == 0:
                    yield from self.sender.sendMessage('connected_a1')
                else:
                    self._connected = True
                    yield from self.sender.sendMessage('connected_b')
                    try:
                        yield from user_list.get(self._peerid).start_peer(self._id)
                    except Exception as e:
                        print(e)

            else:
                yield from self.sender.sendMessage(u"Utilice /init o espere")
            return

        if message == "/end":
            yield from user_list.get(self._peerid).disconnect(True)

        # Connected. Message forwarder
        yield from user_list.get(self._peerid).send_message(message)
        # Message forwarder end
        return

    @asyncio.coroutine
    def on_close(self, exception):
        if isinstance(exception, telepot.helper.WaitTooLong):
            yield from self.sender.send_message("Game expired - timeout.")
            del user_list[self._id]


def in_out_queue(id_temp):
    global nextpeer
    with nextpeer_lock:
        if nextpeer == 0:
            nextpeer = id_temp
            temp = 0
        else:
            temp = nextpeer
            nextpeer = 0
    return temp


# Store your API key in a file named "token.txt" (remember to .gitignore it)
keyFile = open('token.txt', 'r')
TOKEN = keyFile.readline()
keyFile.close()

# Delegator Bot class in asynchronous mode // SET TIMEOUT
bot = telepot.async.DelegatorBot(TOKEN, [
    (per_chat_id(), create_open(User, TIMEOUT_SECONDS)),
])
loop = asyncio.get_event_loop()
loop.create_task(bot.messageLoop())

# Program Start
print('Server up and running')
user_list = {}
nextpeer = 0
nextpeer_lock = threading.Lock()
loop.run_forever()
