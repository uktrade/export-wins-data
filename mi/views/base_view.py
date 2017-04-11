import datetime
from collections import Counter
from itertools import groupby
from operator import attrgetter, itemgetter
import time

from django.db.models import Count, Sum
from django_countries.fields import Country as DjangoCountry

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from alice.authenticators import IsMIServer, IsMIUser
from mi.models import Sector
from mi.utils import (
    average,
    get_financial_start_date,
    get_financial_end_date,
    percentage,
    percentage_formatted,
)
from wins.models import Notification, Win


class BaseMIView(APIView):
    """ Base view for other MI endpoints to inherit from """

    permission_classes = (IsMIServer, IsMIUser)

    def _invalid(self, msg):
        return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

    def _success(self, results):
        return Response(results, status=status.HTTP_200_OK)

    def _success_fin_year(self, results, fin_year):
        response = {
            "timestamp": time.time(),
            "financial_year": {
                "id": fin_year.id,
                "description": fin_year.description,
            },
            "results": results
        }
        return Response(response, status=status.HTTP_200_OK)

    def _not_found(self):
        return Response(status=status.HTTP_404_NOT_FOUND)

    def _hvc_overview(self, targets):
        """ Make an overview dict for a list of targets """

        return {
            'target': sum(t.target for t in targets),
            'campaigns': sorted([t.name for t in targets]),
        }


class BaseWinMIView(BaseMIView):
    """ Base view with Win-related MI helpers """

    fin_year = None
    # cumulative values for `_breakdowns_cumulative` method
    hvc_confirm_cu_number = hvc_confirm_cu_value = hvc_non_cu_number = hvc_non_cu_value = 0
    non_hvc_confirm_cu_number = non_hvc_confirm_cu_value = non_hvc_non_cu_number = non_hvc_non_cu_value = 0
    non_export_confirm_cu_number = non_export_confirm_cu_value = non_export_non_cu_number = non_export_non_cu_value = 0

    def _wins(self):
        """ Helper for returning Wins used by all Endpoints """

        return Win.objects.filter(
            date__range=(
                get_financial_start_date(self.fin_year),
                get_financial_end_date(self.fin_year),
            ),
        ).select_related('confirmation')

    def _colours(self, hvc_wins, targets):
        """
        Determine colour of all HVCs

        Return a dict of status colour counts e.g. {'red': 3, 'amber': 2, 'green': 4, 'zero': 2}

        """
        colours = {
            'red': 0,
            'amber': 0,
            'green': 0,
            'zero': 0
        }

        hvc_colours = []
        for t in targets:
            target_wins = [win for win in hvc_wins if win.hvc == t.charcode]
            current_val = sum(win.total_expected_export_value for win in target_wins if win.confirmed)
            hvc_colours.append(self._get_status_colour(t.target, current_val))

        colours.update(dict(Counter(hvc_colours)))
        return colours

    def _average_confirm_time(self, **win_filter):
        """ Average confirmation time of Wins matching given filter """

        # fetch all notifications with response date, ordered by win id and
        # notification creation date, so that it is easy to group
        # notifications by win and then find each win's earliest notification
        notifications = Notification.objects.filter(
            type__exact='c',
            win__confirmation__isnull=False,
            **win_filter
        ).values(
            'win__id',
            'created',
            'win__confirmation__created',
        ).order_by(
            'win__id',
            'created'
        )
        confirm_times = []
        for win_id, values_grouper in groupby(notifications, itemgetter('win__id')):
            earliest_values = next(iter(values_grouper))
            delta = earliest_values['win__confirmation__created'] - earliest_values['created']
            confirm_times.append(delta.days)

        avg_confirm_time = average(confirm_times)

        return avg_confirm_time or 0.0

    def _overview_target_percentage(self, wins, total_target):
        """ Percentages of confirmed/unconfirmed wins against total target """

        confirmed, unconfirmed = self._confirmed_unconfirmed(wins)
        confirmed = percentage_formatted(confirmed, total_target)
        unconfirmed = percentage_formatted(unconfirmed, total_target)
        return {
            'confirmed': confirmed,
            'unconfirmed': unconfirmed
        }

    def _overview_win_percentages(self, hvc_wins, non_hvc_wins):
        """ Percentages of total confirmed/unconfirmed value HVC & non-HVC """

        hvc_confirmed, hvc_unconfirmed = self._confirmed_unconfirmed(hvc_wins)
        non_hvc_confirmed, non_hvc_unconfirmed = self._confirmed_unconfirmed(non_hvc_wins)

        total_confirmed = hvc_confirmed + non_hvc_confirmed
        total_unconfirmed = hvc_unconfirmed + non_hvc_unconfirmed
        total_win_percent = {
            'hvc': {
                'confirmed': 0,
                'unconfirmed': 0
            },
            'non_hvc': {
                'confirmed': 0,
                'unconfirmed': 0
            }
        }
        if total_confirmed != 0:
            total_win_percent['hvc']['confirmed'] = percentage(hvc_confirmed, total_confirmed)
            total_win_percent['non_hvc']['confirmed'] = percentage(non_hvc_confirmed, total_confirmed)

        if total_unconfirmed != 0:
            total_win_percent['hvc']['unconfirmed'] = percentage(hvc_unconfirmed, total_unconfirmed)
            total_win_percent['non_hvc']['unconfirmed'] = percentage(non_hvc_unconfirmed, total_unconfirmed)

        return total_win_percent

    def _days_into_year(self):
        """
        abstract away identifying number of days we are into the financial year.

        Return usual number of days, if we are dealing with current financial year

        If in case of previous ones, just return 365
        """

        days_into_year = (datetime.datetime.today() - get_financial_start_date(self.fin_year)).days

        if days_into_year > 365:
            return 365

        return days_into_year

    def _get_status_colour(self, target, current_value):
        """
        Algorithm to determine HVC performance status colour

        `run_rate` is percentage of value achieved out of `target as of today` i.e. prorated target

        zero: for 0 target campaigns
        green: when run_rate > 45%
        red: when run_rate < 25%
        amber: rest of them
        """

        if target == 0:
            return 'zero'

        # calculate prorated target based on number of days
        prorated_target = (target / 365) * self._days_into_year()
        run_rate = (current_value * 100) / prorated_target

        if run_rate > 45:
            return 'green'

        if run_rate < 25:
            return 'red'

        return 'amber'

    def _breakdown_wins(self, wins, non_export=False):
        """
        Breakdown Wins by confirmed and non-confirmed
        Clarification on not including non-export for non-HVC wins:
        Non-export value is the value of a win entered into the export win system that is not technically an export
        by definitions of export e.g. when we lobby a government to reduce corporate taxes – that profit back to
        the UK is a benefit to us but not an export. It has nothing to do with Non-HVC wins which are export wins,
        which could contain 0 or lots of non-export value as with any export win, but do not fall within a HVC.
        """

        confirmed = []
        unconfirmed = []

        for win in wins:
            if non_export:
                value = win.total_expected_non_export_value
            else:
                value = win.total_expected_export_value

            if win.confirmed:
                confirmed.append(value)
            else:
                unconfirmed.append(value)

        return {
            'value': {
                'confirmed': sum(confirmed),
                'unconfirmed': sum(unconfirmed),
                'total': sum(confirmed) + sum(unconfirmed),
            },
            'number': {
                'confirmed': len(confirmed),
                'unconfirmed': len(unconfirmed),
                'total': len(confirmed) + len(unconfirmed),
            },

        }

    def _breakdowns(self, wins, include_non_hvc=True):
        """ Get breakdown of data for wins

        Result looks like:
        {
            'export': {
                'hvc': {
                    'value': ...,
                    'number': ...,
                },
                'non_hvc' <optional>:{
                   'value': ...,
                   'number': ...,
                }
            },
            'non_export': {
               'value': ...,
               'number': ...,
            }

        }

        """
        hvc_wins = [win for win in wins if win.hvc]
        result = {
            'export': {
                'hvc': self._breakdown_wins(hvc_wins),
            },
            'non_export': self._breakdown_wins(hvc_wins, non_export=True),
        }

        confirmed_value = result['export']['hvc']['value']['confirmed']
        unconfirmed_value = result['export']['hvc']['value']['unconfirmed']
        confirmed_number = result['export']['hvc']['number']['confirmed']
        unconfirmed_number = result['export']['hvc']['number']['unconfirmed']

        if include_non_hvc:
            non_hvc_wins = [win for win in wins if not win.hvc]
            result['export']['non_hvc'] = self._breakdown_wins(non_hvc_wins)

            confirmed_value += result['export']['non_hvc']['value']['confirmed']
            unconfirmed_value += result['export']['non_hvc']['value']['unconfirmed']
            confirmed_number += result['export']['non_hvc']['number']['confirmed']
            unconfirmed_number += result['export']['non_hvc']['number']['unconfirmed']

        result['export']['totals'] = {
            'value': {
                'confirmed': confirmed_value,
                'unconfirmed': unconfirmed_value,
                'grand_total': confirmed_value + unconfirmed_value,
            },
            'number': {
                'confirmed': confirmed_number,
                'unconfirmed': unconfirmed_number,
                'grand_total': confirmed_number + unconfirmed_number,
            }
        }

        return result

    def _progress_breakdown(self, wins, target):
        """ Breakdown wins by progress toward HVC target """

        breakdown = self._breakdown_wins(wins)
        confirmed_percent = percentage_formatted(breakdown['value']['confirmed'], target)
        unconfirmed_percent = percentage_formatted(breakdown['value']['unconfirmed'], target)
        return {
            'hvc': breakdown,
            'target': target,
            'change': 'up',
            'progress': {
                'confirmed_percent': confirmed_percent,
                'unconfirmed_percent': unconfirmed_percent,
                'status': self._get_status_colour(target, breakdown['value']['confirmed'])
            },
        }

    def _breakdowns_cumulative(self, wins, include_non_hvc=True):
        """ Breakdown wins by HVC, confirmed and non-export - cumulative

        Month-by-month breakdown using class values

        """
        hvc_confirmed = []
        hvc_unconfirmed = []
        non_hvc_confirmed = []
        non_hvc_unconfirmed = []
        non_export_confirmed = []
        non_export_unconfirmed = []

        for win in wins:
            export_value = win.total_expected_export_value
            if win.hvc:
                if win.confirmed:
                    hvc_confirmed.append(export_value)
                else:
                    hvc_unconfirmed.append(export_value)
            else:
                if win.confirmed:
                    non_hvc_confirmed.append(export_value)
                else:
                    non_hvc_unconfirmed.append(export_value)

            non_export_value = win.total_expected_non_export_value
            if win.confirmed:
                non_export_confirmed.append(non_export_value)
            else:
                non_export_unconfirmed.append(non_export_value)

        # these store cumulative values of each month (see class definition)
        self.hvc_confirm_cu_number += len(hvc_confirmed)
        self.hvc_non_cu_number += len(hvc_unconfirmed)
        self.hvc_confirm_cu_value += sum(hvc_confirmed)
        self.hvc_non_cu_value += sum(hvc_unconfirmed)
        self.non_hvc_confirm_cu_number += len(non_hvc_confirmed)
        self.non_hvc_non_cu_number += len(non_hvc_unconfirmed)
        self.non_hvc_confirm_cu_value += sum(non_hvc_confirmed)
        self.non_hvc_non_cu_value += sum(non_hvc_unconfirmed)
        self.non_export_confirm_cu_number += len(non_export_confirmed)
        self.non_export_non_cu_number += len(non_export_unconfirmed)
        self.non_export_confirm_cu_value += sum(non_export_confirmed)
        self.non_export_non_cu_value += sum(non_export_unconfirmed)

        total_hvc_value = self.hvc_confirm_cu_value + self.hvc_non_cu_value
        total_non_hvc_value = self.non_hvc_confirm_cu_value + self.non_hvc_non_cu_value
        total_confirm_value = self.hvc_confirm_cu_value + self.non_hvc_confirm_cu_value
        total_non_conf_value = self.hvc_non_cu_value + self.non_hvc_non_cu_value

        total_hvc_number = self.hvc_confirm_cu_number + self.hvc_non_cu_number
        total_non_hvc_number = self.non_hvc_confirm_cu_number + self.non_hvc_non_cu_number
        total_confirm_number = self.hvc_confirm_cu_number + self.non_hvc_confirm_cu_number
        total_non_conf_number = self.hvc_non_cu_number + self.non_hvc_non_cu_number

        result = {
            'export': {
                'hvc': {
                    'value': {
                        'confirmed': self.hvc_confirm_cu_value,
                        'unconfirmed': self.hvc_non_cu_value,
                        'total': total_hvc_value,
                    },
                    'number': {
                        'confirmed': self.hvc_confirm_cu_number,
                        'unconfirmed': self.hvc_non_cu_number,
                        'total': total_hvc_number,
                    },
                },
            },
            'non_export': {
                'value': {
                    'confirmed': self.non_export_confirm_cu_value,
                    'unconfirmed': self.non_export_non_cu_value,
                    'total': (self.non_export_confirm_cu_value + self.non_export_non_cu_value),
                },
                'number': {
                    'confirmed': self.non_export_confirm_cu_number,
                    'unconfirmed': self.non_export_non_cu_number,
                    'total': (self.non_export_confirm_cu_number + self.non_export_non_cu_number),
                }
            }
        }

        if include_non_hvc:
            result['export']['non_hvc'] = {
                'value': {
                    'confirmed': self.non_hvc_confirm_cu_value,
                    'unconfirmed': self.non_hvc_non_cu_value,
                    'total': total_non_hvc_value,
                },
                'number': {
                    'confirmed': self.non_hvc_confirm_cu_number,
                    'unconfirmed': self.non_hvc_non_cu_number,
                    'total': total_non_hvc_number,
                }
            }

        result['export']['totals'] = {
            'value': {
                'confirmed': total_confirm_value if include_non_hvc else self.hvc_confirm_cu_value,
                'unconfirmed': total_non_conf_value if include_non_hvc else self.hvc_non_cu_value,
                'grand_total': total_hvc_value + total_non_hvc_value if include_non_hvc else total_hvc_value,
            },
            'number': {
                'confirmed': total_confirm_number if include_non_hvc else self.hvc_confirm_cu_number,
                'unconfirmed': total_non_conf_number if include_non_hvc else self.hvc_non_cu_number,
                'grand_total': total_hvc_number + total_non_hvc_number if include_non_hvc else total_hvc_number,
            },
        }
        return result

    def _group_wins_by_target(self, wins, targets):
        """ Take wins and targets, return list of [(target, target_wins)] """

        # convenient for testing to be ordered by campaign_id
        targets = sorted(targets, key=attrgetter('campaign_id'))

        def target_wins(target):
            return [w for w in wins if w.hvc == target.charcode]

        return [(t, target_wins(t)) for t in targets]

    def _confirmed_unconfirmed(self, wins):
        """ Find total Confirmed & Unconfirmed export value for given Wins """

        confirmed = sum(w.total_expected_export_value for w in wins if w.confirmed)
        unconfirmed = sum(w.total_expected_export_value for w in wins if not w.confirmed)
        return confirmed, unconfirmed

    def _top_non_hvc(self, non_hvc_wins_qs, records_to_retreive=5):
        """ Get dict of data about non-HVC wins """

        non_hvc_wins = non_hvc_wins_qs.values(
            'country',
            'sector'
        ).annotate(
            total_value=Sum('total_expected_export_value'),
            total_wins=Count('id')
        ).order_by('-total_value')[:records_to_retreive]

        # make a lookup to get names efficiently
        sector_id_to_name = {s.id: s.name for s in Sector.objects.all()}
        top_value = int(non_hvc_wins[0]['total_value']) if non_hvc_wins else None
        return [
            {
                'region': DjangoCountry(w['country']).name,
                'sector': sector_id_to_name[w['sector']],
                'totalValue': w['total_value'],
                'totalWins': w['total_wins'],
                'percentComplete': int(percentage(w['total_value'], top_value)),
                'averageWinValue': int(w['total_value'] / w['total_wins']),
                'averageWinPercent': int(percentage((w['total_value'] / w['total_wins']), top_value)),
            }
            for w in non_hvc_wins
        ]
