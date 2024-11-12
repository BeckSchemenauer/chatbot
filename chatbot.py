import socket
import sys
import time
import threading


class IRC:
    irc = socket.socket()

    def __init__(self):
        # Deefine the socket
        self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def command(self, msg):
        self.irc.send(bytes(msg + "\n", "UTF-8"))

    def send(self, channel, msg):
        # Transfer data
        self.command("PRIVMSG " + channel + " :" + msg)

    def connect(self, server, port, channel, botnick, botpass, botnickpass):
        # Connect to the server
        print("Connecting to: " + server)
        self.irc.connect((server, port))

        # Perform user authentication
        self.command("USER " + botnick + " " + botnick + " " + botnick + " :python")
        self.command("NICK " + botnick)
        # self.irc.send(bytes("NICKSERV IDENTIFY " + botnickpass + " " + botpass + "\n", "UTF-8"))
        time.sleep(5)

        # join the channel
        self.command("JOIN " + channel)

    def get_response(self):
        time.sleep(1)
        # Get the response
        resp = self.irc.recv(2040).decode("UTF-8")

        if resp.find('PING') != -1:
            self.command('PONG ' + resp.split()[1] + '\r')

        return resp


class Bot:
    def __init__(self, server, port, channel, botnick):
        self.server = server
        self.port = port
        self.channel = channel
        self.botnick = botnick
        self.in_conversation = False
        self.is_first_speaker = True
        self.time_since_last_contact = 0
        self.running = True

        # Start the background thread to update time_since_last_contact
        self.thread = threading.Thread(target=self._update_time_since_last_contact)
        self.thread.daemon = True  # Ensures the thread stops when the program exits
        self.thread.start()

        self.irc = IRC()
        self.irc.connect(server, port, channel, botnick, "", "")

    def _update_time_since_last_contact(self):
        # Increment time_since_last_contact every second
        while self.running:
            time.sleep(1)  # Wait for 1 second
            self.time_since_last_contact += 1  # Increase by 1

    def stop(self):
        # Stop the background thread
        self.running = False
        self.thread.join()

    def get_response(self):
        return self.irc.get_response()

    def parse_response(self, text):
        if "PRIVMSG" in text and self.channel in text and self.botnick + ":" in text:

            time.sleep(1.5)

            if "die!" in text:
                self.die()
            if "hello" in text:
                self.respond_to_hello(text)
            if "usage" in text or "who are you?" in text:
                self.usage()
            if "users" in text:
                self.names()
            if "forget" in text:
                self.forget()

    def respond_to_hello(self, text):
        user_name = text.split(":")[1].split("!")[0]
        msg = text.split(':', 2)[-1]
        response_msg = ""

        if self.in_conversation:
            if self.is_first_speaker:
                # Bot is giving secondary outreach
                response_msg = f"Yo {user_name}, I said hi"
            else:
                # Bot is responding to secondary outreach
                response_msg = f"{self.time_since_last_contact} umm, hi"
        else:
            # New conversation, bot is second speaker
            self.is_first_speaker = False
            self.in_conversation = True
            response_msg = f"Hi there hello {user_name}"

        self.time_since_last_contact = 0
        self.irc.send(self.channel, response_msg)

    def die(self):
        self.irc.send(self.channel, "really? OK, fine.")
        self.irc.command("QUIT")
        sys.exit()

    def usage(self):
        self.irc.send(self.channel, f"My name is {self.botnick}. I was created by Beck S and Gavin L, CSC482-01")

    def names(self):
        # Send the NAMES command to get the user list
        self.irc.command(f"NAMES {self.channel}")

        # Retrieve and parse the response
        response = ""
        while True:
            resp = self.get_response()
            response += resp
            if f" 353 {self.botnick} " in resp:  # '353' is the numeric reply for NAMES
                # Parse the user list from the response
                user_list = resp.split(f" 353 {self.botnick} ")[-1].split(':')[1].strip()
                print("Users in channel:", user_list)
                self.irc.send(self.channel, f"Users: {user_list}")
                return
            elif f" 366 {self.botnick} " in resp:  # '366' is the end of NAMES list
                return

    def forget(self):
        self.in_conversation = False
        self.is_first_speaker = True
        self.time_since_last_contact = 0

        self.irc.send(self.channel, "forgetting everything")


## IRC Config
_server = "irc.libera.chat"  # Provide a valid server IP/Hostname
_port = 6667
_channel = "#csc482"
_botnick = "bg-test-bot"

bot = Bot(_server, _port, _channel, _botnick)

while True:
    response = bot.get_response()
    print("RECEIVED ==> ", response)

    bot.parse_response(response)
