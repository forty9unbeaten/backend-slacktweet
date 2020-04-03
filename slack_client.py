#!/usr/bin/env python3
"""A standalone Slack client implementation
see https://slack.dev/python-slackclient/
"""
import os
import slack
import logging
import re
import random
import argparse
import sys
import dotenv

# exit program if not run in python3 environment
if sys.version_info[0] < 3:
    print('\n\tThis is a Python 3 program...\n')
    sys.exit()


class SlackClient:

    def __init__(self, bot_name, oauth_token):
        self.logger = self.config_logger('slack_client', 'slack_client.log')
        self.token = oauth_token
        self.bot_name = bot_name
        self.bot_id = self.get_bot_id(bot_name)
        self.rtm_client = slack.RTMClient(token=oauth_token)
        self.rtm_client.run_on(event='hello')(self.handle_hello)
        self.rtm_client.run_on(event='message')(self.handle_message)

    def config_logger(self, logger_name, log_file):
        '''
        Instantiates a logger that specifically logs information pertaining to
        a SlackClient instance

        Parameters:
            logger_name --> name to apply to the logger instance
            log_file --> name and extension of the file in which the
            log records will be written
            log_level --> the level to set the logger instance
            (default is INFO)

        Return:
            a logger instance

        '''
        logger = logging.getLogger(logger_name)

        # log formatting
        log_format = ('%(asctime)s.%(msecs)d03 | %(name)s | %(levelname)s |' +
                      ' %(lineno)d | %(message)s')
        log_date_format = '[%b %d, %Y] %H:%M:%S'
        formatter = logging.Formatter(fmt=log_format, datefmt=log_date_format)

        # stream an file handlers
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # set log level, defaults to 'INFO'
        logger.setLevel(os.environ['LOG_LVL'])

        return logger

    def get_bot_id(self, bot_name):
        '''
        queries Slack Web API to retrieve the bot's ID

        Parameters:
            bot_name --> the name of the bot to look for

        Returns:
            string representing the bot ID
        '''
        users = slack.WebClient(token=self.token).users_list()
        self.logger.debug('Connected to Web API to get Bot ID')
        for user in users['members']:
            if user.get('real_name', None) and user['real_name'] == bot_name:
                self.logger.debug('Bot ID found')
                return user['id']

    def handle_hello(self, **payload):
        '''
        The callback that fires when a 'hello' event is received from
        a successful RTMClient connection
        '''
        self.logger.info('RTM Client has connected; "Hello" event recevied')
        web_client = self.rtm_client._web_client
        assert web_client is not None

        web_client.chat_postMessage(
            token=self.token,
            channel='robs-test-channel',
            text='I\'m Alive!'
        )

    def handle_message(self, **payload):
        '''
        callback method that fires when RTMClient recieves a 'message' event

        Parameters:
            payload --> message event payload

        Return:
            None
        '''
        self.logger.info('\'message\' event recieved from RTM Client.')
        web_client = self.rtm_client._web_client
        assert web_client is not None
        data = payload['data']

        # check that payload data contains text, meaning it is a message
        if data.get('text', None):
            self.logger.debug('Checking if message mentions bot')
            bot_id_regex = f'<@{self.bot_id}>'
            is_at_bot = re.search(bot_id_regex, data['text'])

            if is_at_bot:
                # message mentions bot and user expects a response
                self.logger.debug(
                    'Message mentions bot, looking for appropriate response')
                command = re.sub(bot_id_regex, '', data['text']).strip()

                if command == 'help':
                    # 'help' command
                    self.logger.info(
                        'Help command recieved, sending help message')
                    self.send_help(
                        web_client, data['channel'], ('Hi! Here\'s what' +
                                                      ' I can do...'))
                elif command == 'exit' or command == 'quit':
                    self.logger.info(
                        'Exit command received, exiting and sending ' +
                        'exit message')
                    self.handle_exit(web_client, data['channel'])

                else:
                    # unrecognized command
                    self.logger.info(
                        'Unrecognized command, showing help message')
                    comments = [
                        'You know I don\'t speak spanish...',
                        'Nobody knows what it means, but it\'s provocative',
                        'Aim for the bushes...',
                        'I\'m a peacock, you gotta let me fly!',
                        'Did I hear a \'niner\' in there?',
                        'Maybe there\'s some sort of a translation problem...'
                    ]
                    rand_num = random.randint(0, len(comments) - 1)
                    self.send_help(
                        web_client, data['channel'], comments[rand_num])

    def send_help(self, client, channel, message):
        '''
        posts a custom message followed by the help block

        Parameters:
            client --> the Slack WebClient instance
            channel --> the channel to post the message
            message --> the message to show above the help block

        Return:
            None
        '''
        self.logger.debug('Attempting to send help message')
        client.chat_postMessage(
            token=self.token,
            channel=channel,
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{message}"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ("```Commands I understand:\n" +
                                 "help -->\t\tShow this message\n" +
                                 "ping -->\t\tShow uptime of this bot\n" +
                                 "exit -->\t\tKill the bot\n" +
                                 "quit -->\t\tSame as 'exit'\n" +
                                 "list -->\t\tList current Twitter filters\n" +
                                 "add  -->\t\tAdd some Twitter filters\n" +
                                 "del  -->\t\tRemove some Twitter filters\n" +
                                 "clear-->\t\tRemove all Twitter filters\n" +
                                 "raise-->\t\tManual exception handler test```"
                                 )
                    }
                }
            ]
        )
        self.logger.info('Help message sent')

    def handle_exit(self, client, channel):
        '''
        sends a message to the appropriate Slack channel and closes the
        RTM Client connection

        Parameters:
            client --> the Slack Web Client to call Slack Web API
            channel --> the channel to send the 'exit' message

        Return:
            None
        '''
        messages = [
            'Adios!',
            'Until next time!',
            'Take it easy!',
            'Au revoir!',
            'Later alligator!'
        ]
        rand_num = random.randint(0, len(messages) - 1)
        self.logger.debug('Attempting to send exit message')
        client.chat_postMessage(
            token=self.token,
            channel=channel,
            text=messages[rand_num]
        )
        self.logger.info('Exit message sent successfully')
        self.rtm_client.stop()
        self.logger.info('Closed RTM client connection')


def create_parser(args):
    '''
    creates an argument parser that handles command-line arguments

    Parameters:
        args --> arguments included on command line

    Return:
        an ArgParser instance
    '''
    parser = argparse.ArgumentParser(
        description=('A Slackbot that interacts with the user and' +
                     ' serves as a filter for a Twitter stream'),
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '-l', '-log',
        help=('integer that sets the log level for program log output' +
              '\n0: DEBUG\n1: INFO(DEFAULT)\n2: WARNING' +
              '\n3: ERROR\n4: CRITICAL'),
        default=1,
        metavar='',
        dest='log_lvl'
    )
    return parser


def main(args):
    dotenv.load_dotenv('./.env')
    parser = create_parser(args)
    ns = parser.parse_args()
    # set log level as environment variable
    log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    os.environ['LOG_LVL'] = log_levels[int(ns.log_lvl)]

    slack_bot = SlackClient('RobsTweetBot', os.environ['SLACK_TOKEN'])
    slack_bot.rtm_client.start()


if __name__ == '__main__':
    main(sys.argv[1:])
