import datetime

from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.utils.timezone import get_current_timezone
from django_countries.fields import Country as DjangoCountry
from freezegun import freeze_time

from fixturedb.factories.win import create_win_factory
from mi.tests.base_test_case import (
    MiApiViewsWithWinsBaseTestCase,
    MiApiViewsBaseTestCase
)
from mi.tests.utils import GenericTopNonHvcWinsTestMixin, GenericWinTableTestMixin


@freeze_time(MiApiViewsBaseTestCase.frozen_date_17)
class CountryBaseViewTestCase(MiApiViewsWithWinsBaseTestCase):
    export_value = 100000
    win_date_2017 = datetime.datetime(2017, 4, 25, tzinfo=get_current_timezone())
    win_date_2016 = datetime.datetime(2016, 4, 25, tzinfo=get_current_timezone())
    fy_2016_last_date = datetime.datetime(2017, 3, 31, tzinfo=get_current_timezone())

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('create_missing_hvcs', verbose=False)

    def get_url_for_year(self, year, base_url=None):
        if not base_url:
            base_url = self.view_base_url
        return '{base}?year={year}'.format(base=base_url, year=year)


class CountryDetailTestCase(CountryBaseViewTestCase):
    TEST_COUNTRY_CODE = "FR"
    country_detail_url = reverse('mi:country_detail', kwargs={"country_code": "FR"})
    country_detail_url_invalid = reverse('mi:country_detail', kwargs={"country_code": "ABC"})


    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS)
        self.view_base_url = self.country_detail_url

    def test_2017_win_table_in_2016_404(self):
        self.view_base_url = self.country_detail_url_invalid
        self.url = self.get_url_for_year(2016)
        self._get_api_response(self.url, status_code=404)

    def test_2016_win_table_in_2017_404(self):
        self.view_base_url = self.country_detail_url_invalid
        self.url = self.get_url_for_year(2017)
        self._get_api_response(self.url, status_code=404)

    def test_win_table_json_2016_no_wins(self):
        self.url = self.get_url_for_year(2016)
        self.expected_response = {
            "name": "France",
            "wins": {
                "export": {
                    "totals": {
                        "number": {
                            "grand_total": 0,
                            "unconfirmed": 0,
                            "confirmed": 0
                        },
                        "value": {
                            "grand_total": 0,
                            "unconfirmed": 0,
                            "confirmed": 0
                        }
                    },
                    "non_hvc": {
                        "number": {
                            "total": 0,
                            "unconfirmed": 0,
                            "confirmed": 0
                        },
                        "value": {
                            "total": 0,
                            "unconfirmed": 0,
                            "confirmed": 0
                        }
                    },
                    "hvc": {
                        "number": {
                            "total": 0,
                            "unconfirmed": 0,
                            "confirmed": 0
                        },
                        "value": {
                            "total": 0,
                            "unconfirmed": 0,
                            "confirmed": 0
                        }
                    }
                },
                "non_export": {
                    "number": {
                        "total": 0,
                        "unconfirmed": 0,
                        "confirmed": 0
                    },
                    "value": {
                        "total": 0,
                        "unconfirmed": 0,
                        "confirmed": 0
                    }
                }
            },
            "hvcs": {
                "campaigns": [
                    'HVC: E045',
                    'HVC: E046',
                    'HVC: E047',
                    'HVC: E048',
                    'HVC: E214'
                ],
                "target": 50000000
            },
            "avg_time_to_confirm": 0.0
        }
        self.assertResponse()

    def test_win_table_json_2017_no_wins(self):
        self.url = self.get_url_for_year(2017)
        self.expected_response = {
            "name": "France",
            "wins": {
                "export": {
                    "totals": {
                        "number": {
                            "grand_total": 0,
                            "unconfirmed": 0,
                            "confirmed": 0
                        },
                        "value": {
                            "grand_total": 0,
                            "unconfirmed": 0,
                            "confirmed": 0
                        }
                    },
                    "non_hvc": {
                        "number": {
                            "total": 0,
                            "unconfirmed": 0,
                            "confirmed": 0
                        },
                        "value": {
                            "total": 0,
                            "unconfirmed": 0,
                            "confirmed": 0
                        }
                    },
                    "hvc": {
                        "number": {
                            "total": 0,
                            "unconfirmed": 0,
                            "confirmed": 0
                        },
                        "value": {
                            "total": 0,
                            "unconfirmed": 0,
                            "confirmed": 0
                        }
                    }
                },
                "non_export": {
                    "number": {
                        "total": 0,
                        "unconfirmed": 0,
                        "confirmed": 0
                    },
                    "value": {
                        "total": 0,
                        "unconfirmed": 0,
                        "confirmed": 0
                    }
                }
            },
            "hvcs": {
                "campaigns": ['E04517', 'E04617', 'E04717', 'E05417', 'E11917'],
                "target": 170000000
            },
            "avg_time_to_confirm": 0.0
        }
        self.assertResponse()

    def test_win_table_2017_one_confirmed_hvc_win(self):
        self._create_hvc_win(
            hvc_code='E045',
            win_date=self.win_date_2017,
            confirm=True,
            fin_year=2017,
            export_value=self.export_value,
            country='FR'
        )
        self.url = self.get_url_for_year(2017)
        api_response = self._api_response_data
        print(api_response)
        self.assertTrue(len(api_response["hvcs"]["campaigns"]) > 0)
        self.assertEqual(api_response["name"], "France")
        self.assertEqual(api_response["wins"]["export"]["totals"]["number"]["confirmed"], 1)
        self.assertEqual(api_response["wins"]["export"]["totals"]["number"]["unconfirmed"], 0)


class CountryTopNonHVCViewTestCase(CountryBaseViewTestCase, GenericTopNonHvcWinsTestMixin):

    export_value = 9992

    TEST_COUNTRY_CODE = "FR"
    country_top_nonhvc_url = reverse('mi:country_top_nonhvc', kwargs={"country_code": "FR"})
    country_topnonhvc_url_invalid = reverse('mi:country_top_nonhvc', kwargs={"country_code": "ABC"})
    country_topnonhvc_url_missing_country_kwarg = reverse('mi:country_top_nonhvc', kwargs={"country_code": None})

    fin_years = [2016, 2017]

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS)
        self.view_base_url = self.country_top_nonhvc_url

    def test_fake_country_404(self):
        self.view_base_url = self.country_topnonhvc_url_invalid
        self.url = self.get_url_for_year(2017)
        self._get_api_response(self.url, status_code=404)

    def test_missing_country_404(self):
        self.view_base_url = self.country_topnonhvc_url_missing_country_kwarg
        self.url = self.get_url_for_year(2017)
        self._get_api_response(self.url, status_code=404)


class CountryWinTableTestCase(CountryBaseViewTestCase, GenericWinTableTestMixin):

    TEST_COUNTRY_CODE = 'IE'
    TEST_COUNTRY = DjangoCountry(TEST_COUNTRY_CODE)
    fin_years = [2016, 2017]

    expected_response = {
        "country": {
            "id": TEST_COUNTRY_CODE,
            "name": TEST_COUNTRY.name,
        },
        "wins": {
            "hvc": []
        }

    }

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS)
        self.country_win_table_url = reverse('mi:country_win_table', kwargs={
            'country_code': self.TEST_COUNTRY_CODE
        })
        self.country_win_table_url_invalid = reverse('mi:country_win_table', kwargs={
            'country_code': 'XX'
        })
        self.view_base_url = self.country_win_table_url
