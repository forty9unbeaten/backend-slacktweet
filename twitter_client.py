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
                  ' line: %(lineno)d | %(message)s')
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
        self.stream = None

    def __enter__(self):
        '''
        allows class instance to be used as a a context manager

        Parameters:
            None

        Return:
            self
        '''
        logger.debug('TwitterClient instance entered as context manager')
        return self

    def __exit__(self, type, value, traceback):
        '''
        Allows TwitterClinet instance to be used a context manager

        Parameters:
            None

        Return:
            None
        '''
        if self.stream is not None:
            self.stream.disconnect()
            logger.debug('TwitterClient instance exited as context manager')

    def create_filtered_stream(self, filters):
        '''
        creates a tweet stream in accordance with any filters

        Parameters:
            filters --> the filters to apply to the tweet stream

        Return:
            None
        '''
        if not self.stream:
            self.stream = tweepy.Stream(
                auth=self.api.auth,
                listener=self,
                daemon=True
            )
            logger.info(f'New stream created: {self.stream}')
            self.stream.filter(
                track=filters,
                is_async=True
            )

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

    def log_stop_banner(self):
        '''
        logs a stop banner to the log file

        Parameters:
            None

        Return:
            None
        '''
        uptime = dt.datetime.now() - self.start_time
        logger.info('TwitterClient stream disconnected')
        logger.info(textwrap.dedent(f'''
        *********************************
            TwitterClient stopped
            Uptime: {uptime}
        *********************************'''))
        logging.shutdown()

    def on_error(self, status_code):
        '''
        handler that is triggered when error is returned by Twitter API
        when trying to connect via stream

        Parameters:
            status_code --> the status code returned by Twitter API

        Return:
            None
        '''
        if status_code == 420:
            logger.error(
                'Reached maximum number of attempts to connect stream ' +
                'to Twitter API. Automatically disconnecting')
            return False
        return super().on_error(status_code)

    def on_status(self, tweet):
        """
        Callback for receiving tweet messages

        Parameters:
            tweet --> tweet object sent by Twitter API

        Return:
            result of the stream handler callback
        """
        if self.stream_handler is not None:
            # filter out retweets
            if not tweet._json.get('retweeted_status', None):
                return self.stream_handler(tweet)
        return True

    def register_stream_handler(self, func=None):
        """
        allows an external function to hook into the twitter stream

        Parameters:
            func --> the function to register as a stream handler callback

        Return:
            None
        """
        logger.info(f'Registering new stream handler: {func.__name__}')
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
    """
    for testing of standalone twitter client only
    """
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
        def my_handler(tweet):
            print(tweet.text)
            return (not exit_flag)
        twit.register_stream_handler(my_handler)

        # begin receiving messages
        filters = ['python']
        twit.create_filtered_stream(filters)

        # wait for OS exit
        try:
            while not exit_flag:
                logger.debug('zzz ...')
                time.sleep(1.0)
        except KeyboardInterrupt:
            twit.log_stop_banner()


if __name__ == '__main__':
    run_twitter_client(sys.argv[1:])
