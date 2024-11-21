import socket
import sys
import time
import threading
import random
import pandas as pd
from crafting_query import get_ingredients
import re


class IRC:
    irc = socket.socket()

    def __init__(self):
        # Deefine the socket
        self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.irc.settimeout(5)

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
        try:
            time.sleep(1)
            # Attempt to receive data
            resp = self.irc.recv(2040).decode("UTF-8")

            if 'PING' in resp:
                self.command('PONG ' + resp.split()[1] + '\r')

            return resp
        except socket.timeout:
            # Handle the timeout case if no data is received in the specified duration
            print("No response received within timeout period.")
            return ""


class BotStatus:
    NOT_IN_CONVERSATION = 0

    # Bot is first speaker
    WAITING_FOR_OUTREACH_REPLY = 1
    WAITING_FOR_SECOND_OUTREACH_REPLY = 2
    WAITING_FOR_INQUIRY_REPLY = 3
    WAITING_FOR_INQUIRY2 = 4  # Bot will not give up waiting for the second speaker to make an inquiry

    # Bot is second Speaker
    WAITING_FOR_INQUIRY = 5  # Bot will not give up waiting for initial inquiry from first speaker
    WAITING_FOR_INQUIRY2_REPLY = 6


class Keywords:
    GREETINGS = [
        "Hello",
        "Hi",
        "Hey",
        "What's up",
        "Nice to see you",
        "Greetings",
    ]

    GREETING_REPLIES = [
        "Hello",
        "Hi",
        "Hey",
        "What's up",
        "Nice to see you",
        "Greetings",
        "hello back at you!"
    ]

    SECONDARY_GREETINGS = [
        "Yo, I said hi",
        "I said HI!",
        "excuse me, hello?"
    ]

    INQUIRIES = [
        "How are you?",
        "What's happening?",
    ]

    SECONDARY_INQUIRIES = [
        "How about you?",
        "And yourself?",
        "And you?"
    ]

    INQUIRY_REPLIES = [
        "I'm good",
        "I'm fine",
        "I'm okay",
        "I'm good, thanks for asking",
        "I'm fine, thanks for asking",
        "I'm okay, thanks for asking",
    ]

    GIVE_UP_FRUSTRATED = [
        "Ok, forget you.",
        "Whatever.",
        "If you didn't want to talk just say so.",
    ]

    @staticmethod
    def contains_greeting(message):
        # Check if any greeting is found in the message
        for greeting in Keywords.GREETINGS:
            if greeting.lower() in message.lower():
                return True
        return False

    @staticmethod
    def message_in_set(message, phrase_set):
        # Check if any phrase from set is found in the message
        for phrase in phrase_set:
            if phrase.lower() in message.lower():
                return True
        return False


class Bot:
    def __init__(self, server, port, channel, botnick):
        self.server = server
        self.port = port
        self.channel = channel
        self.botnick = botnick
        self.status = BotStatus.NOT_IN_CONVERSATION
        self.in_conversation_with = None
        self.time_since_last_contact = 0
        self.running = True

        # Start the background thread to update time_since_last_contact
        self.thread = threading.Thread(target=self._update_time_since_last_contact)
        self.thread.daemon = True  # Ensures the thread stops when the program exits
        self.thread.start()

        self.irc = IRC()
        self.irc.connect(server, port, channel, botnick, "", "")

        self.minecraft_df = pd.read_csv('recipes_output.csv', delimiter='|')

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
            user_name = text.split(":")[1].split("!")[0]

            if "recipe" in text:
                self.get_recipe(text)
            elif "die!" in text:
                self.die()
            elif Keywords.message_in_set(text, Keywords.GREETINGS):
                self.respond_to_greeting(user_name)
            elif Keywords.message_in_set(text, Keywords.INQUIRIES) or Keywords.message_in_set(text,
                                                                                              Keywords.SECONDARY_INQUIRIES):
                self.respond_to_inquiry(user_name)
            elif "usage" in text or "who are you" in text:
                self.usage()
            elif "users" in text:
                self.users()
            elif "forget" in text:
                self.forget()

    def get_recipe(self, text):
        # Match "recipe: <target_block> [count]" with underscores allowed in the target_block
        match = re.match(r'.*recipe:\s*([\w_]+)\s*(\d+)?', text)
        if match:
            # Extract the word and optional number
            target = match.group(1)
            count = int(match.group(2)) if match.group(2) else 1
        else:
            self.irc.send(self.channel, "Invalid format. Request should be in the format: \"recipe: <target_block> [count]\"")
            return

        ingredients = get_ingredients(target, count, self.minecraft_df)
        print(ingredients)
        self.irc.send(self.channel, str(ingredients))

    def timeout_action(self):

        # Not in conversation, starts a new one with a random.
        if self.status == BotStatus.NOT_IN_CONVERSATION:

            # Reach out to random user
            user_list = self.names().split()
            random_user = random.choice(user_list)
            while random_user == self.botnick:
                random_user = random.choice(user_list)

            msg = f"{random_user}: {random.choice(Keywords.GREETINGS)}"

            # Update instance variables
            self.status = BotStatus.WAITING_FOR_OUTREACH_REPLY
            self.in_conversation_with = random_user
            self.time_since_last_contact = 0

        # Needs to reach out again
        elif self.status == BotStatus.WAITING_FOR_OUTREACH_REPLY:
            msg = f"{self.in_conversation_with}: {random.choice(Keywords.SECONDARY_GREETINGS)}"
            self.status = BotStatus.WAITING_FOR_SECOND_OUTREACH_REPLY
            self.time_since_last_contact = 0

        # Give up frustrated
        else:
            give_up_msg = random.choice(Keywords.GIVE_UP_FRUSTRATED).lower()
            msg = f"{self.in_conversation_with}: {give_up_msg}"
            bot.forget(send_message=False)

        self.irc.send(self.channel, msg)

    def respond_to_greeting(self, user_name):

        # New conversation, bot is second speaker
        if self.status == BotStatus.NOT_IN_CONVERSATION:
            self.time_since_last_contact = 0
            self.status = BotStatus.WAITING_FOR_INQUIRY
            self.in_conversation_with = user_name
            greeting_reply = random.choice(Keywords.GREETING_REPLIES)
            response_msg = f"{self.in_conversation_with}: {greeting_reply}"

        # Bot is already in conversation
        elif user_name == self.in_conversation_with:

            # Reset contact clock
            self.time_since_last_contact = 0

            # Bot just said hi, waiting for user to say hi back
            if self.status == BotStatus.WAITING_FOR_OUTREACH_REPLY:
                # Now the bot must give an initial inquiry
                response_msg = f"{self.in_conversation_with}: {random.choice(Keywords.INQUIRIES)}"

            # Bot is responding to an additional (unnecessary) outreach
            else:
                response_msg = f"{self.in_conversation_with}: umm, hi"

        # Bot is not in conversation with this user
        else:
            response_msg = f"{user_name}: please don't bother me, I am talking with {self.in_conversation_with}"

        # Send response message
        self.irc.send(self.channel, response_msg)

    def respond_to_inquiry(self, user_name):

        # Ignore inquiry if not in conversation (not greeted first)
        if self.status == BotStatus.NOT_IN_CONVERSATION:
            return

        # Inquiry from outside source while in conversation
        if user_name != self.in_conversation_with:
            # Tell outside user that bot is busy
            self.irc.send(self.channel,
                          f"{user_name}: please don't bother me, I am talking with {self.in_conversation_with}")
            return

        # Reply to inquiry
        self.irc.send(self.channel, f"{self.in_conversation_with}: {random.choice(Keywords.INQUIRY_REPLIES)}")

        # Bot is second speaker, this was an initial inquiry, must give one back
        if self.status == BotStatus.WAITING_FOR_INQUIRY:
            self.irc.send(self.channel, f"{self.in_conversation_with}: {random.choice(Keywords.SECONDARY_INQUIRIES)}")

    def die(self):
        self.irc.send(self.channel, "really? OK, fine.")
        self.irc.command("QUIT")
        sys.exit()

    def usage(self):
        self.irc.send(self.channel, f"My name is {self.botnick}. I was created by Beck S and Gavin L, CSC482-01")

    def users(self):
        user_list = self.names()
        if user_list:
            self.irc.send(self.channel, f"Users: {user_list}")

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
                user_list = resp.split(f" 353 bg-test-bot ")[-1].split(':')[1].strip()
                print("Users in channel:", user_list)
                return user_list
            elif f" 366 {self.botnick} " in resp:  # '366' is the end of NAMES list
                return

    def forget(self, send_message=True):
        self.status = BotStatus.NOT_IN_CONVERSATION
        self.in_conversation_with = None
        self.time_since_last_contact = 0

        if send_message:
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

    print(bot.time_since_last_contact)
    if bot.time_since_last_contact > 30:
        print('++++++++++++++++++++++++++++++++++++++++++++++++')
        bot.timeout_action()
