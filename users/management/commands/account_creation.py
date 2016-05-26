import argparse
import bz2
import csv
import os
import random
import time

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from ...models import User


class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        BaseCommand.__init__(self, *args, **kwargs)
        with bz2.open(os.path.join(settings.BASE_DIR, "users", "words.bz2")) as f:
            self.words = [str(w.strip(), "utf-8") for w in f.readlines()]

    def add_arguments(self, parser):
        parser.add_argument("users_file", type=argparse.FileType('r'))

    def handle(self, *args, **options):

        for row in csv.reader(options["users_file"]):

            if not row:
                continue

            name = row[0].strip()
            email = row[1].strip().lower()
            password = self._generate_password()

            print("Sending mail to {}".format(name))

            u = User.objects.create(name=name, email=email)
            u.set_password(password)
            u.save()

            send_mail(
                "Export Wins Login Credentials",
                "Dear Colleague\n\nThank you for agreeing to test the new "
                "Export Wins service.\n\nThis service is being developed with "
                "feedback from live user testing. It will be delivered in two "
                "parts: the first part is to be completed online by the Lead "
                "Officer in UKTI or FCO who has helped the Customer deliver "
                "the win. In the second part, the Customer will be sent an "
                "email, inviting them to confirm the Export Win.\n\nInitially "
                "we are only testing the functionality the first part of this "
                "process. Your team will have the opportunity to comment on "
                "the process that enables customers to confirm Export Wins "
                "before we begin testing that part.\n\nThe service can be "
                "accessed by copying and pasting the address below into your "
                "internet browser, or by clicking on this link:\n\n  "
                "https://www.exportwins.ukti.gov.uk/\n\n"
                "You should login using these credentials:\n\n  Email: {}\n  "
                "Password: {}\n\nIf you experience a problem accessing or "
                "completing the form using the link above, please contact us "
                "by email using the feedback button in the service or at:"
                "\n\n  Email: ada.lovelace@ukti.gsi.gov.uk\n  Subject: Export "
                "Wins Feedback\n\nBest Regards\n\n"
                "The UKTI Digital Team".format(
                    email,
                    password
                ),
                settings.SENDING_ADDRESS,
                (email,)
            )

            time.sleep(1)

    def _generate_password(self):
        separator = random.choice(("-", ",", ".", "_"))
        return "{}{}{}{}{}{}{}".format(
            random.choice(self.words),
            separator,
            random.choice(self.words),
            separator,
            random.choice(self.words),
            separator,
            random.choice(self.words),
        )
