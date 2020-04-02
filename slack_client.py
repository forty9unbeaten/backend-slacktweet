#!/usr/bin/env python3
"""A standalone Slack client implementation
see https://slack.dev/python-slackclient/
"""
import os
import slack
import logging


class SlackClient:

    def __init__(self, oauth_token):
        self.logger = self.config_logger('slack_client', 'slack_client.log')
        self.token = oauth_token
        self.rtm_client = slack.RTMClient(token=oauth_token)
        self.rtm_client.run_on(event='hello')(self.handle_hello)

    def config_logger(self, logger_name, log_file, log_level='INFO'):
        '''
        Instantiates a logger that specifically logs information pertaining to
        a SlackClient instance

        Parameters:
            logger_name --> name to apply to the logger instance
            log_file --> name and extension of the file in which the log records will be written
            log_level --> the level to set the logger instance (default is INFO)

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
        logger.setLevel(log_level)

        return logger

    def post_message(self, channel_name, message):
        '''
        Post a message to a specific channel

        Parameters:
            channel_name --> the name of the channel to post on
            message --> the message to post

        Return:
            None
        '''
        assert self.rtm_client._web_client is not None
        self.rtm_client._web_client.chat_postMessage(
            token=self.token,
            channel='#{}'.format(channel_name),
            text=message
        )

    def handle_hello(self, **payload):
        '''
        The callback that fires when a 'hello' event is received from
        a successful RTMClient connection
        '''
        self.logger.info('RTM Client has connected')
        self.post_message('robs-test-channel', "I'm alive and online!")


def main():
    slack_bot = SlackClient(os.environ['SLACK_TOKEN'])
    slack_bot.rtm_client.start()


if __name__ == '__main__':
    main()
