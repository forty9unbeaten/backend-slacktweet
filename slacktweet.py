#!/usr/bin/env python3
"""
A Slackbot implementation that integrates
Slack and Twitter clients together
"""

import sys
import signal
import argparse
import dotenv
import logging
import textwrap
import os
import datetime
from slack_client import SlackClient
from twitter_client import TwitterClient

# assure that program is run in python3 environment
if sys.version_info[0] < 3:
    print('\n\tThis is a Python 3 program...\n')
    sys.exit()

# load environment variables
dotenv.load_dotenv('./.env')


# modular logging configuration
def config_logger(log_file):
    '''
    Instantiates a logger that specifically logs information pertaining to
    the slacktweet.py program

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
    logger.setLevel(logging.INFO)

    return logger


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
            slacktweet.py started
            Process ID: {os.getpid()}
        *********************************
        '''))


def log_banner_stop(start_time):
    '''
    logs a stop banner to the log file and cleans up logging

    Parameters:
        start_time --> start time of the program

    Return:
        None
    '''
    uptime = datetime.datetime.now() - start_time
    logger.info('RTM Client disconnected')
    logger.info(textwrap.dedent(f'''
        *********************************
            slack_client.py stopped
            Uptime: {uptime}
        *********************************'''))
    logging.shutdown()


logger = config_logger('slacktweet.log')


# signal handling configuration
def config_signal_handlers():
    '''
    Attach handler to various OS signals the program may recieve

    Parameters:
        None

    Return:
        None
    '''
    signals = [signal.SIGINT, signal.SIGTERM, signal.SIGHUP]
    for sig in signals:
        signal.signal(sig, os_signal_handler)
        logger.debug(
            f'{signal.Signals(sig).name} signal handler connected')
    logger.info('All signal handlers connected')


def os_signal_handler(sig_num, frame):
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


# configure command-line argument parser
def create_parser(args):
    '''
        creates an argument parser that handles command-line arguments

        Parameters:
            args --> arguments included on command line

        Return:
            an ArgParser instance
        '''
    parser = argparse.ArgumentParser(
        description=(
            'Stream tweets to a Slack channel filtered ' +
            'by keywords provided in channel'),
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
    log_banner_start()
    start_time = datetime.datetime.now()

    # parse arguments from command-line
    parser = create_parser(args)
    args_ns = parser.parse_args()
    logger.info('Command-line arguments recieved and parsed')

    # set log level for program
    log_levels = [logging.DEBUG, logging.INFO,
                  logging.WARNING, logging.ERROR, logging.CRITICAL]
    logger.setLevel(log_levels[int(args_ns.log_lvl)])
    if args:
        logger.info(
            'Custom log-level set in accordance with ' +
            'command-line argument provided'
        )

    # signal handler configuration
    config_signal_handlers()


if __name__ == '__main__':
    main(sys.argv[1:])
