#!/usr/bin/env python3
"""A standalone Slack client implementation
see https://slack.dev/python-slackclient/
"""
import os
import slack
import logging
import re


class SlackClient:

    def __init__(self, bot_name, oauth_token):
        self.token = oauth_token
        self.bot_name = bot_name
        self.bot_id = self.get_bot_id(bot_name)
        self.logger = self.config_logger('slack_client', 'slack_client.log')
        self.rtm_client = slack.RTMClient(token=oauth_token)
        self.rtm_client.run_on(event='hello')(self.handle_hello)
        self.rtm_client.run_on(event='message')(self.handle_message)

    def config_logger(self, logger_name, log_file, log_level='INFO'):
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
        logger.setLevel(log_level)

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

        # web_client.chat_postMessage(
        #     token=self.token,
        #     channel='robs-test-channel',
        #     text='I\'m Alive!'
        # )

    def handle_message(self, **payload):
        '''
        callback method that fires when RTMClient recieves a 'message' event

        Parameters:
            payload --> message event payload

        Return:
            None
        '''
        self.logger.info('Message recieved from RTM Client.')
        web_client = self.rtm_client._web_client
        assert web_client is not None
        data = payload['data']

        if data.get('text', None):
            bot_id_regex = f'<@{self.bot_id}>'
            is_at_bot = re.search(bot_id_regex, data['text'])
            if is_at_bot:
                web_client.chat_postMessage(
                    token=self.token,
                    channel=data['channel'],
                    text=('I can hear you, but this is all ' +
                          'I have to say for now')
                )


def main():
    slack_bot = SlackClient('RobsTweetBot', os.environ['SLACK_TOKEN'])
    slack_bot.rtm_client.start()


if __name__ == '__main__':
    main()
