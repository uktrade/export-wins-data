from django.core.management import BaseCommand

from fdi.models.importer import InvestmentLoad
from fdi.models.live import (
    Investments, Sector, Country, UKRegion, InvestmentUKRegion, SectorTeamSector,
    MarketGroupCountry, SectorTeamTarget
)


class Command(BaseCommand):
    """
    called like this:
    ./manage.py transform_api

    it is safe to run twice as it will only import rows from fdi_investmentload where
    transform is set to false
    """

    help = 'Transform investment data from API'

    def handle(self, *args, **options):
        new_rows = 0
        updated_rows = 0
        pending_investments = InvestmentLoad.objects.filter(transformed=False)
        for pending_i in pending_investments:
            project_code = pending_i.data["project_code"]
            try:
                # there shouldn't be more than one row per project, but just in case
                # pick up the latest one
                live_i = Investments.objects.filter(
                    project_code=project_code).latest('id')
                # clear UK regions associated with this project
                InvestmentUKRegion.objects.filter(investment=live_i).delete()
                updated_rows += 1
            except Investments.DoesNotExist:
                live_i = Investments(project_code=project_code)
                new_rows += 1

            if pending_i.data["stage"]:
                live_i.stage = pending_i.data["stage"]["name"].lower()
            if pending_i.data["status"]:
                live_i.status = pending_i.data["status"].lower()
            if pending_i.data["number_new_jobs"]:
                live_i.number_new_jobs = pending_i.data["number_new_jobs"]
            if pending_i.data["number_safeguarded_jobs"]:
                live_i.number_safeguarded_jobs = pending_i.data[
                    "number_safeguarded_jobs"]
            if pending_i.data["fdi_value"]:
                live_i.fdi_value_id = pending_i.data["fdi_value"]["id"]
            if pending_i.data["actual_land_date"]:
                live_i.date_won = pending_i.data["actual_land_date"]
            else:
                live_i.date_won = pending_i.data["estimated_land_date"]
            if pending_i.data["sector"]:
                live_i.sector_id = pending_i.data["sector"]["id"]
            if pending_i.data["client_relationship_manager"]:
                live_i.client_relationship_manager = pending_i.data[
                    "client_relationship_manager"]["name"]
            if pending_i.data["investor_company"]:
                live_i.company_name = pending_i.data["investor_company"]["name"]
                live_i.company_reference = pending_i.data["investor_company"]["id"]
            if pending_i.data["total_investment"]:
                live_i.investment_value = pending_i.data["total_investment"]
            if pending_i.data["foreign_equity_investment"]:
                live_i.foreign_equity_investment = pending_i.data[
                    "foreign_equity_investment"]
            if pending_i.data["client_relationship_manager_team"]:
                live_i.client_relationship_manager_team = pending_i.data[
                    "client_relationship_manager_team"]['name']
            if pending_i.data["investor_company_country"]:
                live_i.company_country_id = pending_i.data["investor_company_country"]["id"]
            if pending_i.data["level_of_involvement"]:
                live_i.level_of_involvement_id = pending_i.data["level_of_involvement"]["id"]
            if pending_i.data["investment_type"]:
                live_i.investment_type_id = pending_i.data["investment_type"]["id"]
            if pending_i.data["specific_programme"]:
                live_i.specific_program_id = pending_i.data["specific_programme"]["id"]
            live_i.save()
            # hvc
            try:
                sector_team_sector = SectorTeamSector.objects.get(
                    sector=live_i.sector)
                market_groups_countires = MarketGroupCountry.objects.filter(
                    country=live_i.company_country)
                if market_groups_countires is not None:
                    market_groups = [
                        mgc.market_group for mgc in market_groups_countires]
                    target = SectorTeamTarget.objects.filter(
                        sector_team=sector_team_sector.team, market_group__in=market_groups).first()
                    if target is not None:
                        live_i.hvc_code = target.hvc_code
                        live_i.save()
            except (SectorTeamSector.DoesNotExist, SectorTeamTarget.DoesNotExist):
                pass

            # add regions
            if pending_i.data["uk_region_locations"] and len(pending_i.data["uk_region_locations"]) > 0:
                for location in pending_i.data["uk_region_locations"]:
                    try:
                        uk_region = UKRegion.objects.get(id=location["id"])
                        InvestmentUKRegion(
                            uk_region=uk_region, investment=live_i).save()
                    except UKRegion.DoesNotExist:
                        pass

            pending_i.transformed = True
            pending_i.save()

        print("{} new projects transformed and {} existing projects updated".format(
            new_rows, updated_rows))
