import csv
import io
import tempfile
import zipfile

from django.urls import reverse
from django.test import override_settings, TestCase
from django.utils.timezone import now

from ..constants import BREAKDOWN_NAME_TO_ID
from ..factories import (
    AdvisorFactory,
    BreakdownFactory,
    CustomerResponseFactory,
    NotificationFactory,
    WinFactory,
)
from ..serializers import WinSerializer
from alice.tests.client import AliceClient
from users.factories import UserFactory
from wins.views.flat_csv import CSVView


class TestFlatCSV(TestCase):

    DATE_JOINED = now().replace(year=2017, month=1, day=1)

    def setUp(self):
        user = UserFactory(name='Johnny Fakeman', email="jfakeman@example.com")
        user.date_joined = self.DATE_JOINED
        user.save()

        win1 = WinFactory(
            user=user,
            id='6e18a056-1a25-46ce-a4bb-0553a912706f',
            export_experience=1,
        )
        BreakdownFactory(
            win=win1,
            year=2016,
            value=10000,
            type=BREAKDOWN_NAME_TO_ID['Export'],
        )
        BreakdownFactory(
            win=win1,
            year=2018,
            value=20000,
            type=BREAKDOWN_NAME_TO_ID['Export'],
        )
        BreakdownFactory(
            win=win1,
            year=2020,
            value=2000000,
            type=BREAKDOWN_NAME_TO_ID['Export'],
        )
        BreakdownFactory(
            win=win1,
            year=2017,
            value=300000,
            type=BREAKDOWN_NAME_TO_ID['Non-export'],
        )
        BreakdownFactory(
            win=win1,
            year=2018,
            value=1000,
            type=BREAKDOWN_NAME_TO_ID['Outward Direct Investment'],
        )
        AdvisorFactory(win=win1)
        AdvisorFactory(
            win=win1,
            name='Bobby Beedle',
            team_type='post',
            hq_team="post:Albania - Tirana"
        )
        CustomerResponseFactory(
            win=win1,
            agree_with_win=False
        )
        NotificationFactory(win=win1)
        self.win1 = win1

        self.url = reverse('csv')

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_request(self):
        client = AliceClient()
        user = UserFactory.create(is_superuser=True, email='a@b.c')
        user.set_password('asdf')
        user.is_staff = True
        user.save()
        client.login(username=user.email, password='asdf')
        resp = client.get(self.url)

        chunks = list(resp.streaming_content)
        bytesio = io.BytesIO()
        for chunk in chunks:
            bytesio.write(chunk)
        bytesio.seek(0)

        zf = zipfile.ZipFile(bytesio, 'r')
        csv_path = zf.extract('wins_complete.csv', tempfile.mkdtemp())
        with open(csv_path, 'r') as csv_fh:
            csv_str = csv_fh.read()[1:]  # exclude BOM
        win_dict = list(csv.DictReader(csv_str.split('\n')))[0]
        self._assert_about_win_dict(win_dict)

    def test_direct_call(self):
        chunks = list(CSVView()._make_flat_wins_csv())
        bytesio = io.BytesIO()
        for chunk in chunks:
            bytesio.write(chunk)
        bytesio.seek(0)
        csv_str = bytesio.getvalue().decode('utf-8')[1:]  # exclude BOM

        win_dict = list(csv.DictReader(csv_str.split('\n')))[0]
        self._assert_about_win_dict(win_dict)

    def _choice_to_str(self, obj, fieldname):
        """ Convert display of a choice to equivalent as expected in CSV """

        if not getattr(obj, fieldname):
            return ''
        disp = getattr(obj, 'get_{}_display'.format(fieldname))()
        if ',' in disp:
            return '"{}"'.format(disp)
        return disp

    def test_expected_output(self):
        chunks = list(CSVView()._make_flat_wins_csv())
        bytesio = io.BytesIO()
        for chunk in chunks:
            bytesio.write(chunk)
        bytesio.seek(0)
        actual_lines = bytesio.getvalue().decode('utf-8-sig').split('\n')

        expected_lines_format = '''id,user,Organisation or company name,Data Hub (Companies House) or CDMS reference number,Contact name,Job title,Contact email,HQ location,What kind of business deal was this win?,Summarise the support provided to help achieve this win,Overseas customer,What are the goods or services?,Date business won [MM/YY],country,total expected export value,total expected non export value,total expected odi value,Does the expected value relate to,sector,Prosperity Fund,"HVC code, if applicable","HVO Programme, if applicable",An HVO specialist was involved,E-exporting programme,type of support 1,type of support 2,type of support 3,associated programme 1,associated programme 2,associated programme 3,associated programme 4,associated programme 5,I confirm that this information is complete and accurate,My line manager has confirmed the decision to record this win,Lead officer name,Lead officer email address,Secondary email address,Line manager,team type,"HQ team, Region or Post",Medium-sized and high potential companies,export experience,created,audit,contributing advisors/team,customer email sent,customer email date,Export breakdown 1,Export breakdown 2,Export breakdown 3,Export breakdown 4,Export breakdown 5,Non-export breakdown 1,Non-export breakdown 2,Non-export breakdown 3,Non-export breakdown 4,Non-export breakdown 5,Outward Direct Investment breakdown 1,Outward Direct Investment breakdown 2,Outward Direct Investment breakdown 3,Outward Direct Investment breakdown 4,Outward Direct Investment breakdown 5,customer response recieved,date response received,Your name,Please confirm these details are correct,Other comments or changes to the win details,Securing the win overall?,Gaining access to contacts?,Getting information or improved understanding of the country?,Improving your profile or credibility in the country?,Having confidence to explore or expand in the country?,Developing or nurturing critical relationships?,"Overcoming a problem in the country (eg legal, regulatory, commercial)?",The win involved a foreign government or state-owned enterprise (eg as an intermediary or facilitator),Our support was a prerequisite to generate this export value,Our support helped you achieve this win more quickly,What value do you estimate you would have achieved without our support?,"Apart from this win, when did your company last export goods or services?","If you hadn't achieved this win, your company might have stopped exporting","Apart from this win, you already have specific plans to export in the next 12 months",It enabled you to expand into a new market,It enabled you to increase exports as a proportion of your turnover,It enabled you to maintain or expand in an existing market,Would you be willing for DIT/Exporting is GREAT to feature your success in marketing materials?,"How did you first hear about DIT (or its predecessor, UKTI)",Other marketing source\r
6e18a056-1a25-46ce-a4bb-0553a912706f,Johnny Fakeman <jfakeman@example.com>,company name,cdms reference,customer name,customer job title,customer@email.address,East Midlands,,description,,,2016-05-25,Canada,"£100,000","£2,300","£6,400",Goods,{sector1},Yes,{hvc1},AER-01: Global Aerospace,Yes,Yes,Market entry advice and support – DIT/FCO in UK,,,,,,,,Yes,Yes,lead officer name,,,line manager name,Trade (TD or ST),TD - Events - Financial & Professional Business Services,The company is a medium-sized business or an exporter with high potential,Has never exported before,{created1},,"Name: Billy Bragg, Team DSO - TD - Events - Financial & Professional Business Services, Name: Bobby Beedle, Team Overseas Post - Albania - Tirana",Yes,{sent},"2016: £10,000","2018: £20,000","2020: £2,000,000",,,"2017: £300,000",,,,,"2018: £1,000",,,,,Yes,{response_date},Cakes,{agree},Good work,1,2,3,4,5,1,2,Yes,No,Yes,More than 80%,"Apart from this win, we have exported in the last 12 months",No,Yes,No,Yes,No,No,{marketing_source1},{o_marketing_source1}\r'''  # noqa: E501

        expected_lines = expected_lines_format.format(
            created1=self.win1.created.date(),
            sent=self.win1.notifications.filter(type='c')[0].created.date(),
            response_date=self.win1.confirmation.created.date(),
            sector1=self._choice_to_str(self.win1, 'sector'),
            hvc1=self._choice_to_str(self.win1, 'hvc'),
            agree=CSVView()._val_to_str(self.win1.confirmation.agree_with_win),
            marketing_source1=self._choice_to_str(self.win1.confirmation, 'marketing_source'),
            o_marketing_source1=self._choice_to_str(self.win1.confirmation, 'other_marketing_source'),
        ).split('\n')

        # note these aren't really col-based since just split by comma
        header = None
        for actual_line, expected_line in zip(actual_lines, expected_lines):
            counter = 0
            if not header:
                header = expected_line.split(',')
            zipped_cols = zip(actual_line.split(','), expected_line.split(','))
            for actual_col, expected_col in zipped_cols:
                self.assertEqual(actual_col, expected_col)
                counter += 1

    def test_users_expected_output(self):
        chunks = list(CSVView()._make_user_csv())
        bytesio = io.BytesIO()
        for chunk in chunks:
            bytesio.write(chunk)
        bytesio.seek(0)
        actual_lines = bytesio.getvalue().decode('utf-8').split('\n')  # exclude BOM

        expected_lines = f'''\ufeffname,email,joined,has_export_wins_access\r
Johnny Fakeman,jfakeman@example.com,{self.DATE_JOINED},True\r'''.split('\n')

        # note these aren't really col-based since just split by comma
        for actual_line, expected_line in zip(actual_lines, expected_lines):
            zipped_cols = zip(actual_line.split(','), expected_line.split(','))
            for actual_col, expected_col in zipped_cols:
                self.assertEqual(actual_col, expected_col)

    def _assert_about_win_dict(self, win_dict):
        for field_name in WinSerializer().fields:
            if field_name in CSVView.IGNORE_FIELDS:
                continue

            field = CSVView()._get_win_field(field_name)
            csv_name = field.verbose_name or field.name
            try:
                comma_fields = [
                    'total_expected_export_value',
                    'total_expected_non_export_value',
                    'total_expected_odi_value',
                ]
                value = getattr(self.win1, field_name)
                if field_name in comma_fields:
                    value = "£{:,}".format(value)
                self.assertEqual(
                    win_dict[csv_name],
                    CSVView()._val_to_str(value),
                )
            except AssertionError as exc:
                try:
                    display_fn = getattr(
                        self.win1, "get_{0}_display".format(field_name)
                    )
                    self.assertEqual(
                        win_dict[csv_name],
                        CSVView()._val_to_str(display_fn()),
                    )
                except (AttributeError, AssertionError):
                    if field_name == 'date':
                        self.assertEqual(
                            win_dict[csv_name],
                            str(getattr(self.win1, field_name))[:10],
                        )
                    elif field_name == 'created':
                        self.assertEqual(
                            win_dict[csv_name],
                            str(getattr(self.win1, field_name))[:10],
                        )
                    else:
                        raise Exception(exc)
