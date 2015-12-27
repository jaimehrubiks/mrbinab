import asyncio
import threading
import os
import telepot
import telepot.async
from telepot.delegate import per_chat_id
from telepot.async.delegate import create_open
import gettext

"""
NAME:           Mr. bINAB telegram bot
AUTHOR:         Jaime Hidalgo García
DESCRIPTION:    Proof of concept for DHSAI [Distributed human simulated artificial intelligence]

THANKS TO:      - Telegram.
                - Telepot lib (by nickoala)

CONTRIBUTORS:

LICENSE:        BPL V3 in file "LICENSE"
"""

# Config
TIMEOUT_SECONDS = 200
LANGUAJE = "es"             # Choices: (def -debugMode-, es)
MAX_STATUS = 3              # Min value: 3 (To avoid initial conversation)
# End config


class User(telepot.helper.ChatHandler):
    def __init__(self, seed_tuple, timeout):
        super(User, self).__init__(seed_tuple, timeout)
        self._status = 0
        self._id = None
        self._peerid = None

    @asyncio.coroutine
    def open(self, initial_msg, seed):
        yield from self.sender.sendMessage(_('boot_message'))
        return False  # prevent on_message() from being called on the initial message

    @asyncio.coroutine
    def disconnect(self):
        yield from self.sender.sendMessage(_('forced_disconnect'))
        self._status = 0
        return

    @asyncio.coroutine
    def start_peer(self, peerid):
        self._peerid = peerid
        self._status = 4
        yield from self.sender.sendMessage(_('connected_a2'))

    @asyncio.coroutine
    def send_message(self, message):
        yield from self.sender.sendMessage(message)

    @asyncio.coroutine
    def on_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance2(msg)

        if content_type != 'text':
            return

        message = msg['text']

        if self._status < MAX_STATUS:
            if self._status == 0:
                self._id = msg['from']['id']
                user_list[self._id] = self
                self._status += 1
            elif self._status == 1:
                if message == '/init':
                    self._peerid = in_out_queue(self._id)
                    if self._peerid == 0:
                        yield from self.sender.sendMessage(_('connected_a1'))
                        self._status += 1
                    else:
                        self._status += 2
                        yield from self.sender.sendMessage(_('connected_b1'))
                        yield from user_list.get(self._peerid).start_peer(self._id)
                else:
                    yield from self.send_message(_('instructions'))
            return

        if message == "/end":
            yield from user_list.get(self._peerid).disconnect()
            yield from self.disconnect()
            return

        # Connected. Message forwarder
        print(message)
        yield from user_list.get(self._peerid).send_message(message)
        # Message forwarder end
        return

    @asyncio.coroutine
    def on_close(self, exception):
        if isinstance(exception, telepot.helper.WaitTooLong):
            yield from self.sender.send_message(_('timeout'))
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
script_dir = os.path.dirname(os.path.realpath('__file__'))
key_dir = os.path.join(script_dir, '../token.txt')
key_file = open('token.txt', 'r')
TOKEN = key_file.readline().strip()
key_file.close()

# Delegator Bot class in asynchronous mode // SET TIMEOUT
bot = telepot.async.DelegatorBot(TOKEN, [
    (per_chat_id(), create_open(User, TIMEOUT_SECONDS)),
])
loop = asyncio.get_event_loop()
loop.create_task(bot.messageLoop())

es = gettext.translation('binab', localedir='../locale', languages=[LANGUAJE])
es.install()

# Program Start
print('Server up and running')
user_list = {}
nextpeer = 0
nextpeer_lock = threading.Lock()
loop.run_forever()
