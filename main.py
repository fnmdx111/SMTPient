# encoding: utf-8
import base64
from email.mime.text import MIMEText
import getpass

import socket
import logging
import time


class SMTPClient(object):
    def __init__(self, server_ip, domain, server_port=25):
        self._c_server_ip = server_ip
        self._c_server_port = server_port
        self._c_domain = domain

        self._m_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        logging.basicConfig(level=logging.DEBUG)
        self._m_logger = logging.getLogger(__name__)


    def connect(self):
        self._m_sock.connect((self._c_server_ip, self._c_server_port))
        codes, _ = self._ret()
        if 220 not in codes:
            return False
        return True


    def hello(self):
        self._send('EHLO %s\r\n' % self._c_domain)
        if not all([_ == 250 for _ in self._codes]):
            return False
        return True


    def _ret(self, echo=True):
        lines, codes, msgs = [], [], []
        while True:
            data = self._m_sock.recv(4096)
            lines = data.strip().split('\r\n')
            line = '000 '
            for line in lines:
                if not line:
                    continue
                codes.append(int(line[:3]))
                msgs.append(line[4:])
            if line[3] == ' ':
                return codes, msgs
        if echo:
            self._info((codes, msgs))


    def _info(self, (codes, msgs)):
        for code, data in zip(codes, msgs):
            self._m_logger.info('%s: %s', code, data)


    def _send(self, cmd):
        self._m_sock.send(cmd)
        self._m_logger.info('cmd: %s', cmd.strip())

        self._codes, self._msgs = self._ret()


    def login(self, username, password):
        b64_username = base64.b64encode(username)
        b64_password = base64.b64encode(password)

        self._send('AUTH LOGIN\r\n')
        if 334 not in self._codes:
            return False

        self._send('%s\r\n' % b64_username)
        if 334 not in self._codes:
            return False

        self._send('%s\r\n' % b64_password)
        if 235 not in self._codes:
            return False

        return True


    def mail(self, email):
        self._send('MAIL FROM: <%s>\r\n' % email['From'])
        if 250 not in self._codes:
            return False

        self._send('RCPT TO: %s\r\n' % email['To'])
        if 250 not in self._codes:
            return False

        self._send('DATA\r\n')
        if 354 not in self._codes:
            return False

        self._send(email.as_string() + '\r\n.\r\n')
        if 250 not in self._codes:
            return False
        return True


    def quit(self):
        self._send('QUIT\r\n')
        if 221 not in self._codes:
            return False
        return True


    @staticmethod
    def make_email(from_, to, subject, text):
        email = MIMEText(text.encode('utf-8'), 'plain', 'utf-8')
        email['From'] = from_
        email['To'] = to
        email['Subject'] = subject
        email['date'] = time.strftime('%a, %d %b %Y %H:%M:%S %z')

        return email



def para_input():
    print 'Message (use . as End of Multi-line Send)? '
    ret = ''
    while True:
        s = raw_input()
        if s == '.':
            return ret
        else:
            ret += s



if __name__ == '__main__':
    client = SMTPClient(raw_input('Server IP? '), raw_input('Domain Name? '))
    client.connect()
    client.hello()
    client.login(raw_input('Username? '), getpass.getpass('Password? '))
    client.mail(client.make_email(raw_input('From? '),
                                  raw_input('To? '),
                                  raw_input('Subject? '),
                                  para_input()))
    client.quit()


