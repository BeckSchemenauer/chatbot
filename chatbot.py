import socket
import sys
import time


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

        self.irc = IRC()
        self.irc.connect(server, port, channel, botnick, "", "")

    def get_response(self):
        return self.irc.get_response()

    def parse_response(self, msg):
        if "PRIVMSG" in msg and self.channel in msg and self.botnick + ":" in msg:

            time.sleep(1.5)

            if "die!" in msg:
                self.die()
            if "hello" in msg:
                self.say_hello(msg)
            if "usage" in msg or "who are you?" in msg:
                self.usage()
            if "users" in msg:
                self.names()
            if "forget" in msg:
                self.forget()

    def say_hello(self, msg):
        user_name = text.split(":")[1].split("!")[0]
        self.irc.send(self.channel, f"Hi there hello {user_name}")

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
        self.irc.send(self.channel, "forgetting everything")


## IRC Config
_server = "irc.libera.chat"  # Provide a valid server IP/Hostname
_port = 6667
_channel = "#csc482"
_botnick = "bg-test-bot"

bot = Bot(_server, _port, _channel, _botnick)

while True:
    text = bot.get_response()
    print("RECEIVED ==> ", text)

    bot.parse_response(text)
