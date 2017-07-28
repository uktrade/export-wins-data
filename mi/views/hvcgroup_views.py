from itertools import groupby
from operator import attrgetter, itemgetter

from mi.models import HVCGroup
from mi.utils import month_iterator
from mi.views.sector_views import BaseSectorMIView


class BaseHVCGroupMIView(BaseSectorMIView):
    """ Abstract Base for other HVC Group MI endpoints to inherit from """

    def _get_hvc_group(self, group_id):
        try:
            return HVCGroup.objects.get(id=int(group_id))
        except HVCGroup.DoesNotExist:
            return False

    def _group_result(self, group):
        """ Basic data about HVC Group - name & hvc's """
        return {
            'name': group.name,
            'avg_time_to_confirm': self._average_confirm_time(win__hvc__in=group.fin_year_campaign_ids(self.fin_year)),
            'hvcs': self._hvc_overview(group.fin_year_targets(fin_year=self.fin_year)),
        }


class HVCGroupsListView(BaseHVCGroupMIView):
    def get(self, request):
        response = self._handle_fin_year(request)
        if response:
            return response

        results = [
            {
                'id': hvc_group.id,
                'name': hvc_group.name,
            }
            for hvc_group in self._hvc_groups_for_fin_year()
        ]
        return self._success(sorted(results, key=itemgetter('name')))


class HVCGroupDetailView(BaseHVCGroupMIView):
    """ HVC Group details with name, targets and win-breakdown """

    def get(self, request, group_id):
        response = self._handle_fin_year(request)
        if response:
            return response

        group = self._get_hvc_group(group_id)
        if not group:
            return self._invalid('hvc group not found')

        results = self._group_result(group)
        wins = self._get_group_wins(group)
        results['wins'] = self._breakdowns(wins, include_non_hvc=False)
        self._fill_date_ranges()
        return self._success(results)


class HVCGroupMonthsView(BaseHVCGroupMIView):
    """
    This view provides cumulative totals for all wins for a given HVC Group,
    grouped by month, for current financial year
    """

    def _month_breakdowns(self, wins):
        month_to_wins = self._group_wins_by_month(wins)
        return [
            {
                'date': date_str,
                'totals': self._breakdowns_cumulative(month_wins, include_non_hvc=False),
            }
            for date_str, month_wins in month_to_wins
        ]

    def _group_wins_by_month(self, wins):
        sorted_wins = sorted(wins, key=self._win_date_for_grouping)
        month_to_wins = []
        # group all wins by month-year
        for k, g in groupby(sorted_wins, key=self._win_date_for_grouping):
            month_wins = list(g)
            date_str = month_wins[0]['date'].strftime('%Y-%m')
            month_to_wins.append((date_str, month_wins))

        # Add missing months within the financial year until current month
        for item in month_iterator(self.fin_year):
            date_str = '{:d}-{:02d}'.format(*item)
            existing = [m for m in month_to_wins if m[0] == date_str]
            if len(existing) == 0:
                # add missing month and an empty list
                month_to_wins.append((date_str, list()))

        return sorted(month_to_wins, key=lambda tup: tup[0])

    def get(self, request, group_id):
        response = self._handle_fin_year(request)
        if response:
            return response

        group = self._get_hvc_group(group_id)
        if not group:
            return self._invalid('hvc group not found')

        results = self._group_result(group)
        wins = self._get_group_wins(group)
        results['months'] = self._month_breakdowns(wins)
        self._fill_date_ranges()
        return self._success(results)


class HVCGroupCampaignsView(BaseHVCGroupMIView):
    """ All campaigns for a given HVC Group and their win-breakdown"""

    def _campaign_breakdowns(self, group):
        wins = self._get_group_wins(group)
        group_targets = group.fin_year_targets(fin_year=self.fin_year)
        campaign_to_wins = self._group_wins_by_target(wins, group_targets)
        campaigns = [
            {
                'campaign': campaign.name.split(":")[0],
                'campaign_id': campaign.campaign_id,
                'totals': self._progress_breakdown(campaign_wins, campaign.target),
            }
            for campaign, campaign_wins in campaign_to_wins
        ]
        sorted_campaigns = sorted(
            campaigns,
            key=lambda c: (
                c['totals']['progress']['confirmed_percent'],
                c['totals']['progress']['unconfirmed_percent'],
                c['totals']['target']
            ),
            reverse=True,
        )
        return sorted_campaigns

    def get(self, request, group_id):
        response = self._handle_fin_year(request)
        if response:
            return response

        group = self._get_hvc_group(group_id)
        if not group:
            return self._invalid('hvc group not found')

        results = self._group_result(group)
        results['campaigns'] = self._campaign_breakdowns(group)
        self._fill_date_ranges()
        return self._success(results)

class HVCGroupWinTableView(BaseHVCGroupMIView):
    def get(self, request, group_id):
        response = self._handle_fin_year(request)
        if response:
            return response
        group = self._get_hvc_group(group_id)
        if not group:
            return self._not_found()

        results = {
            "hvc_group": {
                "code": group_id,
                "name": group.name,
            },
            "wins": self._win_table_wins(self._get_group_wins(group))
        }
        self._fill_date_ranges()
        return self._success(results)
