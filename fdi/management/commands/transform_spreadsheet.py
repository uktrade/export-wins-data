from django.core.management import BaseCommand
from django.db import connection


class Command(BaseCommand):
    """
    called like this:
    ./manage.py transform_spreadsheet

    it is safe to run twice as it will only import once if there are any rows with
    legacy = true it will abort. If you want to reimport then it's best to delete
    all legacy rows and run this again.
    """

    help = 'Transform investment spreadsheets'

    def handle(self, *files, **options):
        query = """
        WITH legacy_projects as (
          SELECT i.id, i.data->>'Project Reference Code' as project_code,
              lower(i.data->>'Project Status') as stage,
              lower(i.data->>'Project Status') as status,
              (i.data->>'Number Of New Jobs')::int as number_new_jobs,
              (i.data->>'Number Of Safe Jobs')::int as number_safeguarded_jobs,
              CASE
                WHEN i.data->>'Project Value (New)' LIKE 'High%' THEN 'Higher'
                WHEN i.data->>'Project Value (New)' LIKE 'Good%' THEN 'Good'
                WHEN i.data->>'Project Value (New)' LIKE 'Standard%' THEN 'Standard'
                ELSE NULL
              END as fdi_value,
              to_timestamp(i.data->>' Project Decision Date', 'YYYY-MM-DD')::date as date_won,
              fdi_sector.id as sector_id,
              fdi_ukregion.id as uk_region_id,
              'unknown' as client_relationship_manager,
              CASE
                WHEN i.data->>'Project Level Of Involvement' = 'FDI Hub +LEP' THEN 'FDI Hub + LEP'
                WHEN i.data->>'Project Level Of Involvement' = 'FDI Hub+HQ+Post+Reg' THEN 'FDI Hub + HQ + Post + Reg'
                WHEN i.data->>'Project Level Of Involvement' = 'HQ  and Post Only' THEN 'HQ and Post Only'
                ELSE i.data->>'Project Level Of Involvement'
              END as level_of_involvement,
              CASE
                WHEN i.data->>'Type of Investment (FDI)' = 'Other (non-FDI)' THEN 'Non-FDI'
                WHEN i.data->>'Type of Investment (FDI)' = 'Commitment to Invest' THEN 'Commitment to invest'
                ELSE 'FDI'
              END as investment_type,
              CASE
                WHEN i.data->>'Specific Investment Programme'
                        = 'Venture/ Equity Capital' THEN 'Venture / Equity Capital'
                ELSE i.data->>'Specific Investment Programme'
              END as specific_programme,
              parent_c.data->>'Organisation Name' as company_name,
              parent_c.data->>'Organisation Reference Code' as comapny_reference,
              (i.data->>'Total Value of Investment')::DECIMAL::BIGINT as investment_value,
              (i.data->>'Foreign Equity Investment /£')::DECIMAL::BIGINT as foreign_equity_investment,
              true as legacy,
              fdi_country.id as company_country_id
          from fdi_investmentlegacyload as i
              join fdi_sector
                  on fdi_sector.name = i.data->>'Project Sector UKTI Sector Name'
              join fdi_ukregion
                  on fdi_ukregion.name = i.data->>'Project UK Region'
              join fdi_companylegacyload as parent_c
                  on i.data ->'Project Reference Code' = parent_c.data->'Project Reference Code'
                  and parent_c.data ->'Project Organisation Role' ? 'Parent'
              join fdi_country
                  on fdi_country.name = parent_c.data->>'Organisation Primary Address Country'
          ),
          all_projects as
          (
              SELECT i.id, i.project_code, i.stage, i.status, i.number_new_jobs, i.number_safeguarded_jobs,
              fdi_fdivalue.id as fdi_value_id, i.date_won, i.sector_id, i.uk_region_id,
              i.client_relationship_manager, fdi_involvement.id as level_of_involvement_id,
              fdi_investmenttype.id as investment_type_id,
              i.company_name, i.comapny_reference, i.investment_value,
              i.foreign_equity_investment, i.legacy, i.company_country_id,
              fdi_specificprogramme.id as specific_program_id
              FROM legacy_projects i
              join fdi_involvement
                  on fdi_involvement.name = i.level_of_involvement
              join fdi_investmenttype
                  on fdi_investmenttype.name = i.investment_type
              join fdi_specificprogramme
                  on fdi_specificprogramme.name = i.specific_programme
              join fdi_fdivalue
                  on fdi_fdivalue.name = i.fdi_value
          ),
          latest_projects as
          (
              SELECT Max(id) id, data->>'Project Reference Code' as project_code
              FROM   fdi_investmentlegacyload
              GROUP BY data->>'Project Reference Code'
          ),
          unique_projects AS
          (
              SELECT
                  DISTINCT ON (a.project_code)
                  a.project_code, a.stage, a.status, a.number_new_jobs, a.number_safeguarded_jobs,
                  a.fdi_value_id, a.date_won, a.sector_id, a.uk_region_id, a.client_relationship_manager,
                  a.level_of_involvement_id, a.investment_type_id, a.company_name, a.comapny_reference,
                  a.investment_value, a.foreign_equity_investment, a.legacy, a.company_country_id,
                  a.specific_program_id
              FROM all_projects a
                  INNER JOIN latest_projects l ON l.id = a.id
          ),
          projects_insert AS (
              INSERT INTO fdi_investments (project_code, stage, status, number_new_jobs, number_safeguarded_jobs,
              fdi_value_id, date_won, sector_id, client_relationship_manager, level_of_involvement_id,
              investment_type_id, company_name, company_reference, investment_value, foreign_equity_investment,
              legacy, company_country_id, specific_program_id)
              SELECT
                  a.project_code, a.stage, a.status, a.number_new_jobs, a.number_safeguarded_jobs,
                  a.fdi_value_id, a.date_won, a.sector_id, a.client_relationship_manager,
                  a.level_of_involvement_id, a.investment_type_id, a.company_name, a.comapny_reference,
                  a.investment_value, a.foreign_equity_investment, a.legacy, a.company_country_id,
                  a.specific_program_id
              FROM unique_projects a
              WHERE
                    NOT EXISTS (
                        SELECT id FROM fdi_investments WHERE legacy = true
                    )
              RETURNING id as investment_id, project_code
          )
          INSERT INTO fdi_investmentukregion (investment_id, uk_region_id)
          SELECT i.investment_id, a.uk_region_id FROM projects_insert i
          INNER JOIN unique_projects a ON i.project_code = a.project_code
          WHERE
                NOT EXISTS (
                    SELECT id FROM fdi_investments WHERE legacy = true
                )
        ;
        """
        with connection.cursor() as cursor:
            cursor.execute(query)
            print(f'updated {cursor.rowcount} rows.')
