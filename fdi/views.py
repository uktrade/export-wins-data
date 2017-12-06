import itertools
from operator import itemgetter
from collections import defaultdict

from django.db.models import Func, F, Sum, Count, When, Case, Value, CharField, Max, Count
from django.db.models.functions import Coalesce

from core.utils import group_by_key
from fdi.models import (
    Investments,
    GlobalTargets,
    Sector,
    SectorTeam,
    Market,
    Target,
    Country
)
from core.views import BaseMIView
from fdi.serializers import InvestmentsSerializer
from mi.utils import two_digit_float

ANNOTATIONS = dict(
    year=Func(F('date_won'), function='get_financial_year'),
    value=Case(
        When(approved_good_value=True, then=Value(
            'good', output_field=CharField(max_length=10))),
        When(approved_high_value=True, then=Value(
            'high', output_field=CharField(max_length=10))),
        default=Value('standard', output_field=CharField(max_length=10))
    )
)


def fill_in_missing_performance(data, target: GlobalTargets):
    """
    takes a dict of performance dicts e.g. {'high'; {..}
    and fills in the missing if there is no good/standard/high key
    in the dictionary.
    """
    for k in ['high', 'good', 'standard']:
        if not data.get(k):
            data[k] = {
                "number_new_jobs__sum": 0,
                "number_safeguarded_jobs__sum": 0,
                "investment_value__sum": 0,
                "count": 0,
                "target": getattr(target, k),
                "value__percent": 0
            }
    return data


class BaseFDIView(BaseMIView):

    queryset = Investments.objects.all()

    def get_queryset(self):
        return self.queryset

    def get_results(self):
        return []

    def get(self, request, *args, **kwargs):
        return self._success(self.get_results())

    def _get_target(self):
        try:
            fdi_target = GlobalTargets.objects.get(
                financial_year=self.fin_year)
        except GlobalTargets.DoesNotExist:
            fdi_target = GlobalTargets(
                financial_year=self.fin_year, high=0, good=0, standard=0)
        return fdi_target

    def _get_fdi_summary(self):
        fdi_target = self._get_target()

        investments_in_scope = self.get_queryset().won().filter(
            date_won__range=(self._date_range_start(), self._date_range_end())
        )
        pending = self.get_queryset().filter(
            date_won=None
        ).exclude(
            stage='Won'
        ).aggregate(
            Sum('number_new_jobs'),
            Sum('number_safeguarded_jobs'),
            Sum('investment_value'),
            count=Count('id'),
        )

        total = investments_in_scope.count()
        data = investments_in_scope.values(
            'approved_high_value', 'approved_good_value'
        ).annotate(
            value=ANNOTATIONS['value']
        ).annotate(
            Sum('number_new_jobs'),
            Sum('number_safeguarded_jobs'),
            Sum('investment_value'),
            count=Count('value'),
        ).values(
            'value',
            'count',
            'number_new_jobs__sum',
            'number_safeguarded_jobs__sum',
            'investment_value__sum',
        )

        formatted_breakdown_by_value = group_by_key([
            {
                **x,
                "target": getattr(fdi_target, x['value'], 0),
                "value__percent": two_digit_float((x['count'] / total) * 100)
            } for x in data
        ], key='value', flatten=True)

        formatted_breakdown_by_value = fill_in_missing_performance(formatted_breakdown_by_value, fdi_target)

        return {
            "target": fdi_target.total,
            "performance": {
                "verified": formatted_breakdown_by_value if formatted_breakdown_by_value else None,
            },
            "total": {
                "verified": {
                    "number_new_jobs__sum": sum(x['number_new_jobs__sum'] for x in data),
                    "number_safeguarded_jobs__sum": sum(x['number_safeguarded_jobs__sum'] for x in data),
                    "investment_value__sum": sum(x['investment_value__sum'] for x in data),
                    "count": total
                },
                "pending": {k: v or 0 for k, v in pending.items()}
            },
            "verified_met_percent": two_digit_float(
                total / fdi_target.total * 100
            ) if fdi_target.total > 0 and total > 0 else 0.0

        }


class FDIBaseSectorTeamView(BaseFDIView):

    def initial(self, request, team_id, *args, **kwargs):
        self.team = self._get_team(team_id)
        if not self.team:
            return self._not_found(detail=f'team with id: {team_id} not found')
        super(FDIBaseSectorTeamView, self).initial(
            request, team_id, *args, **kwargs)

    def _get_team(self, team_id):
        """ Get SectorTeam object or False if invalid ID """
        try:
            return SectorTeam.objects.get(id=int(team_id))
        except SectorTeam.DoesNotExist:
            return False

    def get_queryset(self):
        qs = super().get_queryset().filter(date_won__range=(
            self._date_range_start(), self._date_range_end()))
        return qs.for_sector_team(self.team)

    def get_targets(self):
        return self.team.targets.filter(financial_year=self.fin_year)

    def get(self, request, *args, **kwargs):
        return super(FDIBaseSectorTeamView, self).get(request, *args, **kwargs)


class FDISectorTeamListView(BaseFDIView):

    def get(self, request, *args, **kwargs):
        all_sectors = SectorTeam.objects.all()
        formatted_sector_teams = [
            {
                'id': x.id,
                'name': x.name,
                'description': x.description,
                'sectors': x.sectors.all().values()
            } for x in all_sectors
        ]
        return self._success(formatted_sector_teams)


class FDISectorTeamOverview(BaseFDIView):
    pass


class FDIOverview(BaseFDIView):

    def get_results(self):
        return self._get_fdi_summary()


class FDISectorOverview(BaseFDIView):
    pass


class FDISectorTeamDetailView(FDIBaseSectorTeamView):
    team = None

    def _group_investments(self, investments, condition):
        group_iter = itertools.groupby(investments, key=condition)
        groups = defaultdict(list)
        for stage, wins in group_iter:
            groups[stage] = list(wins)
        return groups

    def _item_breakdown(self, investments, hvc_target):
        def classify_quality(investment):
            if investment.approved_high_value:
                return 'high'
            elif investment.approved_good_value:
                return 'good'
            else:
                return 'standard'

        grouped = self._group_investments(investments, classify_quality)
        data = {
            'total': len(investments),
            'progress': two_digit_float(len(investments) * 100 / hvc_target) if hvc_target else 0.0,
            'high': len(grouped['high']),
            'good': len(grouped['good']),
            'standard': len(grouped['standard']),
        }
        return data

    def _get_market_target(self, market):
        target = 0
        try:
            target_obj = Target.objects.get(
                sector_team=self.team, market=market)
            # both HVC and non-HVC targets
            if target_obj.hvc_target:
                target += target_obj.hvc_target
            if target_obj.non_hvc_target:
                target += target_obj.non_hvc_target
        except Target.DoesNotExist:
            return 0

        return target

    def _market_breakdown(self, investments, market):
        def classify_stage(investment):
            if investment.stage == 'Verify win':
                return 'verified'
            elif investment.stage == 'Won':
                return 'confirmed'
            else:
                return 'pipeline'

        # order investments by stage and then by quality so as to group them easily
        market_investments = investments.filter(
            company_country__in=market.countries.all()).order_by(
                'stage', 'approved_high_value', 'approved_good_value')
        grouped = self._group_investments(market_investments, classify_stage)

        target = self._get_market_target(market)

        # TODO target distribution needs a home in database, not here
        target_data = {
            'total': target,
            'progress': 100.0,
            'high': target * 40 / 100,
            'good': target * 30 / 100,
            'standard': target * 30 / 100,
        }

        market_data = {
            "id": market.id,
            "name": market.name,
            "verified": self._item_breakdown(grouped['verfied'], target),
            "confirmed": self._item_breakdown(grouped['confirmed'], target),
            "pipeline": self._item_breakdown(grouped['pipeline'], 0),
            "target": target_data,
        }
        return market_data

    def get(self, request, team_id):
        self.team = self._get_team(team_id)
        investments_in_scope = self.get_queryset()

        if not self.team:
            return self._invalid('team not found')

        results = {}
        results['name'] = self.team.name
        results['description'] = self.team.description
        results['overview'] = self._get_fdi_summary()

        markets = Market.objects.all()
        market_data = [self._market_breakdown(
            investments_in_scope, market) for market in markets]

        results['markets'] = market_data
        return self._success(results)


class FDISectorTeamHVCDetailView(FDISectorTeamDetailView):
    def get_queryset(self):
        qs = super().get_queryset().filter(date_won__range=(
            self._date_range_start(), self._date_range_end()))
        qs = qs.for_sector_team(self.team)
        hvc_markets = [t.market for t in Target.objects.filter(hvc_target__isnull=False, sector_team=self.team.id)]
        hvc_countries = Country.objects.filter(market__in=hvc_markets)
        return qs.filter(company_country__in=hvc_countries)

    def _get_market_target(self, market):
        target = 0
        try:
            target_obj = Target.objects.get(
                sector_team=self.team, market=market)
            if target_obj.hvc_target:
                target += target_obj.hvc_target
        except Target.DoesNotExist:
            return 0

        return target

    def get(self, request, team_id):
        self.team = self._get_team(team_id)
        investments_in_scope = self.get_queryset()

        if not self.team:
            return self._invalid('team not found')

        results = {}
        results['name'] = self.team.name
        results['description'] = self.team.description
        results['overview'] = self._get_fdi_summary()

        hvc_markets = [t.market for t in Target.objects.filter(hvc_target__isnull=False, sector_team=self.team.id)]
        market_data = [self._market_breakdown(
            investments_in_scope, market) for market in hvc_markets]

        results['markets'] = market_data
        return self._success(results)


class FDISectorTeamNonHVCDetailView(FDISectorTeamDetailView):
    def get_queryset(self):
        qs = super().get_queryset().filter(date_won__range=(
            self._date_range_start(), self._date_range_end()))
        qs = qs.for_sector_team(self.team)
        non_hvc_markets = [t.market for t in Target.objects.filter(
            non_hvc_target__isnull=False, sector_team=self.team.id)]
        non_hvc_countries = Country.objects.filter(market__in=non_hvc_markets)
        return qs.filter(company_country__in=non_hvc_countries)

    def _get_market_target(self, market):
        target = 0
        try:
            target_obj = Target.objects.get(
                sector_team=self.team, market=market)
            if target_obj.non_hvc_target:
                target += target_obj.non_hvc_target
        except Target.DoesNotExist:
            return 0

        return target

    def get(self, request, team_id):
        self.team = self._get_team(team_id)
        investments_in_scope = self.get_queryset()

        if not self.team:
            return self._invalid('team not found')

        results = {}
        results['name'] = self.team.name
        results['description'] = self.team.description
        results['overview'] = self._get_fdi_summary()

        non_hvc_markets = [t.market for t in Target.objects.filter(
            non_hvc_target__isnull=False, sector_team=self.team.id)]
        market_data = [self._market_breakdown(
            investments_in_scope, market) for market in non_hvc_markets]

        results['markets'] = market_data
        return self._success(results)


class FDIYearOnYearComparison(BaseFDIView):

    def _fill_date_ranges(self):
        self.date_range = {
            "start": None,
            "end": self._date_range_end(),
        }

    def get_results(self):
        breakdown = self.get_queryset().won(
        ).filter(
            date_won__lt=self._date_range_end()
        ).values(
            'date_won'
        ).annotate(
            **ANNOTATIONS
        ).annotate(
            Count('year'),
            Count('value'),
            Sum('number_new_jobs'),
            Sum('number_safeguarded_jobs'),
            Sum('investment_value')
        ).values(
            'year',
            'year__count',
            'number_new_jobs__sum',
            'number_safeguarded_jobs__sum',
            'investment_value__sum',
            'value',
            'value__count'
        ).order_by('year')
        year_buckets = sorted(list({x['year'] for x in breakdown}))
        return [
            {
                "year": y,
                **{b['value']: {
                    "count": b['year__count'],
                    "number_new_jobs__sum": b['number_new_jobs__sum'],
                    "number_safeguarded_jobs__sum": b['number_safeguarded_jobs__sum'],
                    "investment_value__sum": b['investment_value__sum']
                } for b in breakdown if b['year'] == y}
            } for y in year_buckets
        ]


class FDISectorTeamWinTable(FDIBaseSectorTeamView):

    def get_results(self):
        hvc_target = self.get_targets().aggregate(
            target=Coalesce(Sum('hvc_target'), 0))['target']
        non_hvc_target = self.get_targets().aggregate(
            target=Coalesce(Sum('non_hvc_target'), 0))['target']
        investments = InvestmentsSerializer(self.get_queryset().annotate(**ANNOTATIONS), many=True)

        return {
            "name": self.team.name,
            "description": self.team.description,
            "target": {
                "hvc": hvc_target,
                "non_hvc": non_hvc_target,
                "total": sum([hvc_target, non_hvc_target])
            },
            "investments": investments.data
        }
