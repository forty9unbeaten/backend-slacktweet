#!/usr/bin/env python3
"""A standalone Slack client implementation
see https://slack.dev/python-slackclient/
"""
import os
import slack
import slack.errors
import logging
import re
import random
import argparse
import sys
import dotenv
import datetime
import signal
import textwrap
import asyncio


# exit program if not run in python3 environment
if sys.version_info[0] < 3:
    print('\n\tThis is a Python 3 program...\n')
    sys.exit()

# load environment variables into module
dotenv.load_dotenv('./.env')


class SlackClient:
    '''
    connects to a Slack channel and interacts with another
    user via various commands

    Arguments:
        oauth_token --> authentication token issed by Slack API
    '''

    def __init__(self, oauth_token):
        # logger configuration and start
        self.log_banner_start()

        # instance variable initialization
        self.token = oauth_token
        self.bot_id = self.get_bot_id()
        self.current_channel = ''
        self.start_time = datetime.datetime.now()
        self.filters = []
        self.twitter_client = None

        # RTMClient instantiation and event handlers
        self.rtm_client = slack.RTMClient(token=oauth_token, run_async=True)
        self.rtm_client.run_on(event='hello')(self.handle_hello)
        self.rtm_client.run_on(event='message')(self.handle_message)
        self.rtm_client.run_on(event='goodbye')(self.handle_goodbye)
        self.future = self.rtm_client.start()

    def check_channel_change(self, channel):
        '''
        checks current channel and comapares channel attached to 'message'
        event, changing current channel is necessary

        Parameters:
            channel --> channel attached to 'message' event

        Returns:
            None
        '''
        if self.current_channel != channel:
            logger.info(
                ('message event recieved on different channel, ' +
                 'changing Slack channels'))
            self.current_channel = channel

    def config_signal_handlers(self):
        '''
        Attach handler to various OS signals the program may recieve

        Parameters:
            None

        Return:
            None
        '''
        signals = [signal.SIGINT, signal.SIGTERM, signal.SIGHUP]
        for sig in signals:
            signal.signal(sig, self.os_signal_handler)
            logger.debug(
                f'{signal.Signals(sig).name} signal handler connected')
        logger.info('All signal handlers connected')

    def get_bot_id(self):
        '''
        queries Slack Web API to retrieve the bot's ID

        Parameters:
            None

        Returns:
            string representing the bot ID
        '''
        bot_info = slack.WebClient(token=self.token).auth_test()
        logger.debug('Connected to Web API to get Bot ID')
        return bot_info['user_id']

    def handle_add(self, filters):
        '''
        adds a filter to the list of current filters.

        Parameters:
            filters --> list of new filters to apply

        Return:
            None
        '''
        logger.debug('adding new filters to current filters')
        # parse filters seperated by commas
        if len(filters) > 1:
            filters = ' '.join(filters).split(',')
            filters = [filt.strip() for filt in filters]

        # add filters to current filters
        added_filters = ''
        for filt in filters:
            if filt not in self.filters:
                self.filters.append(filt)
                added_filters += f'{filt}\n'

        # send confirmation to user
        logger.debug(
            'attempting to send message to user confirming added filters')
        self.rtm_client._web_client.chat_postMessage(
            token=self.token,
            channel=self.current_channel,
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "I've added the following filters..."
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ("```Added filters:\n" +
                                 f"{added_filters}```")
                    }
                }
            ]
        )

        logger.info('Successfully sent \'add\' confirmation message')

    def handle_clear(self):
        '''
        clears the list of current filters

        Parameters:
            None

        Return:
            None
        '''

        logger.debug('Clearing list of current filters')
        self.filters = []
        logger.debug('All filters cleared, attempting to ' +
                     'send confirmation message')

        self.rtm_client._web_client.chat_postMessage(
            token=self.token,
            channel=self.current_channel,
            text='All filters cleared'
        )
        logger.info(
            'Successfuly cleared all filters and sent confirmation message')

    def handle_del(self, filters):
        '''
        deletes filters from the current filters list

        Parameters:
            filters --> the filters to be deleted

        Return:
            None
        '''
        logger.debug('deleting specified filters')
        # parse multiple filters to be deleted if necessary
        if len(filters) > 1:
            filters = ' '.join(filters).split(',')
            filters = [filt.strip() for filt in filters]

        # delete filters if they are currently active filters
        deleted_filters = ''
        for filt in filters:
            if filt in self.filters:
                self.filters.remove(filt)
                deleted_filters += f'{filt}\n'
        logger.debug(
            'Successfully deleted filters, attempting to send ' +
            'confirmation message')

        self.rtm_client._web_client.chat_postMessage(
            token=self.token,
            channel=self.current_channel,
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "All good!"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ("```Deleted Filters:\n" +
                                 f"{deleted_filters}```")

                    }
                }
            ]
        )
        logger.info('del confirmation message sent successfully')

    async def handle_exit(self):
        '''
        sends a message to the appropriate Slack channel and closes the
        RTM Client connection

        Parameters:
            None

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
        logger.debug('Attempting to send exit message')
        await self.rtm_client._web_client.chat_postMessage(
            token=self.token,
            channel=self.current_channel,
            text=messages[rand_num]
        )
        logger.info('Exit message sent successfully')

        # trigger RTMClient event loop cancellation
        self.future.cancel()

    def handle_goodbye(self, **payload):
        '''
        callback that fires when the RTMClient recieves a 'goodbye'
        event indiacating the server wants to close the connection

        Parameters:
            payload --> JSON payload sent by the server

        Return:
            None
        '''
        logger.info('Recieved \'goodbye\' event from server')
        logger.debug(
            'Attempting to reconnect to server and restart ' +
            'RTMClient event loop')
        self.run()

    def handle_hello(self, **payload):
        '''
        The callback that fires when a 'hello' event is received from
        a successful RTMClient connection

        Parameters:
            payload --> JSON payload sent by the server
        '''
        logger.info('RTM Client has connected')
        web_client = self.rtm_client._web_client
        assert web_client is not None

        web_client.chat_postMessage(
            token=self.token,
            channel='robs-test-channel',
            text='I\'m Alive!'
        )

    def handle_help(self, message):
        '''
        posts a custom message followed by the help block

        Parameters:
            message --> the message to show above the help block

        Return:
            None
        '''
        logger.debug('Attempting to send help message')
        self.rtm_client._web_client.chat_postMessage(
            token=self.token,
            channel=self.current_channel,
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
                        "text": ("```Commands I understand:\n\n" +
                                 "help  -->\tShow this message\n" +
                                 "ping  -->\tShow uptime of this bot\n" +
                                 "exit  -->\tKill the bot\n" +
                                 "quit  -->\tSame as 'exit'\n" +
                                 "list  -->\tList current Twitter filters\n" +
                                 "clear -->\tClear all current filters" +
                                 "\n\nMultiple argument commands. If adding " +
                                 "or deleting multiple filters, seperate " +
                                 "with commas\n\n" +
                                 "add <filter> -->\tAdd some Twitter " +
                                 "filters\n" +
                                 "del <filter> -->\tRemove some Twitter " +
                                 "filters\n```"
                                 )
                    }
                }
            ]
        )
        logger.info('Help message sent')

    def handle_list(self):
        '''
        list the active filters

        Parameters:
            None

        Return:
            None
        '''
        # format list of filters for dispaly in confirmation message
        logger.debug('Formatting list of filters')
        filter_string = ''
        if not self.filters:
            filter_string = 'None'
        else:
            filter_string = '\n'.join([filt for filt in self.filters])

        # send comfirmation message
        logger.debug('Successfully formatted filters list. ' +
                     'Attempting to send list command message')
        self.rtm_client._web_client.chat_postMessage(
            token=self.token,
            channel=self.current_channel,
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Here you go..."
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ("```Active Filters:\n" +
                                 f"{filter_string}```"
                                 )
                    }
                }
            ]
        )
        logger.info('Successfully sent list command message')

    async def handle_message(self, **payload):
        '''
        callback method that fires when RTMClient recieves a 'message' event

        Parameters:
            payload --> JSON payload sent by the server

        Return:
            None
        '''
        logger.info('\'message\' event recieved from RTM Client.')
        web_client = self.rtm_client._web_client
        assert web_client is not None
        data = payload['data']

        # check that payload data contains text, meaning it is a message
        if data.get('text', None):
            logger.debug('Checking if message mentions bot')
            bot_id_regex = f'<@{self.bot_id}>'
            is_at_bot = re.search(bot_id_regex, data['text'])

            if is_at_bot:
                # message mentions bot and user expects a response
                logger.debug(
                    ('Message mentions bot, looking for ' +
                     'appropriate response'))
                self.check_channel_change(data['channel'])
                command = re.sub(bot_id_regex, '',
                                 data['text']).strip().split()

                if len(command) == 1:
                    if command[0] == 'help':
                        # 'help' command
                        logger.info(
                            'Help command recieved, sending help message')
                        self.handle_help(
                            ('Hi! Here\'s what' +
                             ' I can do...'))

                    elif command[0] == 'ping':
                        # command to show uptime
                        logger.info(
                            'Ping command recieved, sending uptime report')
                        self.handle_ping()

                    elif command[0] == 'exit' or command[0] == 'quit':
                        # command to exit program
                        logger.info(
                            'Exit command received, exiting and sending ' +
                            'exit message')
                        await self.handle_exit()

                    elif command[0] == 'list':
                        # list command to show active filters
                        logger.info(
                            'Recieved list command, sending ' +
                            'message containing list of current filters')
                        self.handle_list()

                    elif command[0] == 'clear':
                        # clear all filters command
                        logger.info(
                            'Recieved clear command, clearing ' +
                            'active filters'
                        )
                        self.handle_clear()
                        self.twitter_client.create_filtered_stream(
                            self.filters)

                    else:
                        # unrecognized command with one word
                        logger.info(
                            'Unrecognized command, showing help message')
                        self.handle_unknown()

                elif len(command) > 1:
                    if command[0] == 'add':
                        # command to add filter(s)
                        logger.info(
                            '\'add\' command recieved, adding filter ' +
                            'and sending message')
                        self.handle_add(command[1:])
                        self.twitter_client.create_filtered_stream(
                            self.filters)

                    elif command[0] == 'del':
                        # command to delete filter(s)
                        logger.info('recieved delete command')
                        self.handle_del(command[1:])
                        self.twitter_client.create_filtered_stream(
                            self.filters)

                    else:
                        # unrecognized command with more than one word
                        logger.info(
                            'Unrecognized command, showing help message')
                        self.handle_unknown()

                else:
                    # unrecognized command
                    logger.info(
                        'Unrecognized command, sending help message')
                    self.handle_unknown()

    def handle_ping(self):
        '''
        sends a message to the appropriate Slack channel reporting
        total uptime of the bot when 'ping' command is recieved

        Parameters:
            None

        Return:
            None
        '''
        messages = [
            'Reporting for duty....',
            'At your service...',
            'Ask and you shall recieve...'
        ]
        rand_num = random.randint(0, len(messages) - 1)

        total_uptime = datetime.datetime.now() - self.start_time
        logger.debug('Attempting to send total uptime message')
        self.rtm_client._web_client.chat_postMessage(
            token=self.token,
            channel=self.current_channel,
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{messages[rand_num]}"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```Total Uptime: {total_uptime}```"
                    }
                }
            ]
        )
        logger.info('Total uptime message sent successfully')

    def handle_unknown(self):
        '''
        sends a message to the appropriate Slack channel along with the 'help'
        block when an unrecognized command is recieved from user

        Parameters:
            None

        Return:
            None
        '''
        comments = [
            'You know I don\'t speak spanish...',
            'Nobody knows what it means, but it\'s provocative',
            'Aim for the bushes...',
            'I\'m a peacock, you gotta let me fly!',
            'Did I hear a \'niner\' in there?',
            'Maybe there\'s some sort of a translation problem...'
        ]
        rand_num = random.randint(0, len(comments) - 1)
        self.handle_help(comments[rand_num])

    @staticmethod
    def log_banner_start():
        '''
        logs a start banner to the log file

        Parameters:
            None

        Return:
            None
        '''

        logger.info(textwrap.dedent(f'''
        *********************************
            slack_client.py started
            Process ID: {os.getpid()}
        *********************************
        '''))

    def log_banner_stop(self):
        '''
        logs a stop banner to the log file

        Parameters:
            None

        Return:
            None
        '''
        uptime = datetime.datetime.now() - self.start_time
        logger.info('RTM Client disconnected')
        logger.info(textwrap.dedent(f'''
        *********************************
            slack_client.py stopped
            Uptime: {uptime}
        *********************************'''))
        logging.shutdown()

    def os_signal_handler(self, sig_num, frame):
        '''
        a handler for various OS signals.

        Parameters:
            sig_num --> the integer code of the signal recieved by the OS
            frame --> unused

        Return:
            None
        '''
        signal_recieved = signal.Signals(sig_num).name
        logger.warning(f'Recieved {signal_recieved}')
        self.future.cancel()

    def register_twitter_client(self, twitter_client):
        '''
        register a twitter client and connect it with a Slack client

        Parameters:
            twitter_client --> a twitter client instance

        Return:
            None
        '''
        self.twitter_client = twitter_client
        twitter_client.register_stream_handler(self.tweet_handler)
        logger.info('Twitter client connected to Slack client')

    def run(self):
        '''
        starts the event loop for the RTM Client

        Parameters:
            None

        Return:
            None
        '''
        try:
            self.config_signal_handlers()
            evt_loop = self.future.get_loop()
            evt_loop.run_until_complete(self.future)
        except asyncio.base_futures.CancelledError:
            logger.error('CancelledError caught, event loop cancelled')
        # Slack API exception handlers
        except slack.errors.SlackApiError:
            logger.error(
                ('The response sent by Slack API was unexpected ' +
                 'and raised a SlackAPIError'))
        except slack.errors.SlackClientNotConnectedError:
            logger.error(
                ('The message sent was rejected because the ' +
                 'SlackClient connection is closed. ' +
                 'SlackClientNotConnectedError raised.'))
        except slack.errors.SlackClientError:
            logger.error(
                ('There is a problem with the Slack WebClient ' +
                 'attempting to call the API. ' +
                 'SlackClientError raised.'))
        finally:
            self.log_banner_stop()

    def tweet_handler(self, tweet):
        '''
        handler that posts message to Slack channel
        when tweet is recieved from stream

        Parameters:
            tweet --> the status object sent by Twitter API

        Return:
            None
        '''
        self.rtm_client._web_client.chat_postMessage(
            token=self.token,
            channel=self.current_channel,
            text=tweet.text
        )

# configure and implement module level logging


def config_logger(log_file):
    '''
    Instantiates a logger that specifically logs information pertaining to
    a SlackClient instance

    Parameters:
        log_file --> name and extension of the file in which the
        log records will be written

    Return:
        a logger instance

    '''
    logger = logging.getLogger(__name__)

    # log formatting
    log_format = ('%(asctime)s.%(msecs)d03 | %(name)s | %(levelname)s |' +
                  ' line: %(lineno)d | %(message)s')
    log_date_format = '[%b %d, %Y] %H:%M:%S'
    formatter = logging.Formatter(fmt=log_format, datefmt=log_date_format)

    # file handler configuration
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


logger = config_logger('slack_client.log')


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


def run_slack_client(args):
    '''
    solely for testing standalone SlackClient instance

    Parameters:
        args --> arguments provided on command-line

    Return:
        None
    '''
    parser = create_parser(args)
    ns = parser.parse_args()

    # set log level and logger name as environment variable
    log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    logger.setLevel(log_levels[int(ns.log_lvl)])

    # instantiate and run SlackClient
    slack_bot = SlackClient(os.environ['SLACK_TOKEN'])
    slack_bot.run()


if __name__ == '__main__':
    run_slack_client(sys.argv[1:])
