#!/usr/bin/env python3
"""
A standalone twitter client implementation
see https://tweepy.readthedocs.io/en/latest/
"""
import os
import sys
import datetime as dt
import time
import logging
import tweepy
import argparse
import textwrap
from dotenv import load_dotenv

# Guard against python2
if sys.version_info[0] < 3:
    print('\n\tThis is a Python 3 program...\n')
    sys.exit()

# Bring all keys and tokens from .env file into environment
load_dotenv()
exit_flag = False


def config_logger(log_file):
    '''
    Instantiates a logger that specifically logs information pertaining to
    a twitter_client.py module

    Parameters:
        log_file --> name and extension of the file in which the
        log records will be written

    Return:
        a logger instance
    '''
    logger = logging.getLogger(__name__)

    # log formatting
    log_format = ('%(asctime)s.%(msecs)d03 | %(name)s | %(levelname)s |' +
                  ' %(lineno)d | %(message)s')
    log_date_format = '[%b %d, %Y] %H:%M:%S'
    formatter = logging.Formatter(fmt=log_format, datefmt=log_date_format)

    # file handler configuration
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


logger = config_logger('twitter_client.log')


class TwitterClient(tweepy.StreamListener):
    """Customized TwitterClient class"""

    def __init__(self, consumer_key, consumer_secret,
                 access_token, access_token_secret):
        """
        Create a Tweepy API object using external tokens
        """

        # logger start
        self.log_start_banner()

        # instance variables
        self.start_time = dt.datetime.now()

        # authentication
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

        # Creation of the twitter api client, using OAuth object.
        self.api = tweepy.API(auth)
        assert self.api is not None
        self.stream_handler = None

    def create_filtered_stream(self, track_list, retweets=False):
        # YOUR CODE HERE
        pass

    @staticmethod
    def log_start_banner():
        '''
        logs a start banner to the log file

        Parameters:
            None

        Return:
            None
        '''

        logger.info(textwrap.dedent(f'''
        *********************************
            twitter_client.py started
            Process ID: {os.getpid()}
        *********************************
        '''))

    def on_status(self, status):
        """Callback for receiving tweet messages"""
        # YOUR CODE HERE
        return True

    def register_stream_handler(self, func=None):
        """This allows an external function to hook into the twitter stream"""
        self.logger.info(f'Registering new stream handler: {func.__name__}')
        self.stream_handler = func


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


def run_twitter_client(args):
    """This is for testing of standalone twitter client only"""
    parser = create_parser(args)
    ns = parser.parse_args()

    # set log level and logger name as environment variable
    log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    logger.setLevel(log_levels[int(ns.log_lvl)])

    # create a twitter client instance
    with TwitterClient(
        consumer_key=os.environ['CONSUMER_KEY'],
        consumer_secret=os.environ['CONSUMER_SECRET'],
        access_token=os.environ['ACCESS_TOKEN'],
        access_token_secret=os.environ['ACCESS_TOKEN_SECRET']
    ) as twit:

        # In real life, this would be the SlackClient
        # registering it's own stream handler
        def my_handler(status):
            logger.info(status.text)
            return (not exit_flag)
        twit.register_stream_handler(my_handler)

        # begin receiving messages
        track_list = ['python']
        twit.create_filtered_stream(track_list)

        # wait for OS exit
        try:
            while not exit_flag:
                logger.debug('zzz ...')
                time.sleep(1.0)
        except KeyboardInterrupt:
            logger.warning('CTRL-C manual exit')

        uptime = dt.now() - twit.start_time

    logger.warning(f'Shutdown completed, uptime: {uptime}')
    logging.shutdown()


if __name__ == '__main__':
    run_twitter_client(sys.argv[1:])
