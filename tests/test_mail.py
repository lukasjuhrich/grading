import re
from datetime import datetime
from collections import deque
from unittest import TestCase

from mail import DATE_FORMAT, grab_one_mail, iter_mails


SAMPLE_DATE = "Mon Oct 10 16:40:28 2016"

class MailFormatTestCase(TestCase):
    def test_correct_format(self):
        date = datetime.strptime(SAMPLE_DATE, DATE_FORMAT)
        self.assertEqual(date.month, 10)
        self.assertEqual(date.year, 2016)
        self.assertEqual(date.day, 10)
        self.assertEqual(date.hour, 16)


class GrabMailTestCase(TestCase):
    def test_mail_grab(self):
        mail = grab_one_mail(deque([SAMPLE_DATE, 'testcontent']))

        self.assertIsInstance(mail.date, datetime)
        self.assertEqual(mail.content, 'testcontent')

    def test_date_format(self):
        mail = grab_one_mail(deque(['notadate', 'testcontent']),
                             date_format="")
        self.assertEqual(mail.date, 'notadate')
        self.assertEqual(mail.content, 'testcontent')


class IterMailsTestCase(TestCase):
    def test_iter_mail(self):
        regex = re.compile("@([0-9]*)")
        string = "@2eins@2zwei"

        mails = list(iter_mails(string, regex=regex,
                                options={'date_format': ""}))
        self.assertEqual(len(mails), 2)
        self.assertEqual(mails[0].content, "eins")
        self.assertEqual(mails[0].date, '2')
        self.assertEqual(mails[1].content, "zwei")
        self.assertEqual(mails[0].date, '2')
