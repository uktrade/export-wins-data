# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-06-12 12:55
from __future__ import unicode_literals

from django.db import migrations


def add_2017_hvc_countries(apps, schema_editor):
    Target = apps.get_model('mi', 'Target')
    FinancialYear = apps.get_model('mi', 'FinancialYear')
    Country = apps.get_model('mi', 'Country')
    hvc_2017 = [['E002', ['AU', 'NZ']], ['E005', ['AU', 'NZ']], ['E006', ['AU']], ['E007', ['AZ']], ['E008', ['BH']], ['E009', ['LT', 'EE', 'LV']], ['E011', ['BE', 'NL', 'LU']], ['E012', ['BR']], ['E013', ['BR']], ['E014', ['BR']], ['E015', ['CA']], ['E016', ['CA']], ['E017', ['HU', 'CZ', 'PL', 'RO', 'SK', 'BG', 'RS']], ['E018', ['PL', 'CZ', 'RO', 'SK', 'BG']], ['E019', ['PL', 'BG', 'CZ', 'RO', 'RS', 'SK']], ['E020', ['RO', 'BG', 'CZ', 'HU', 'PL', 'SK', 'SI']], ['E021', ['CL']], ['E022', ['CN']], ['E023', ['CN']], ['E024', ['CN']], ['E025', ['CN']], ['E026', ['CN']], ['E027', ['CN']], ['E028', ['CN']], ['E029', ['CN']], ['E030', ['CN']], ['E031', ['CN', 'HK']], ['E032', ['CN']], ['E033', ['CN', 'HK']], ['E034', ['CN']], ['E035', ['CN']], ['E037', ['CN']], ['E038', ['CN', 'HK']], ['E040', ['DK']], ['E041', ['KE', 'ET', 'TN', 'UG']], ['E042', ['TN', 'UG', 'MZ']], ['E043', ['KE', 'ET', 'TN', 'UG']], ['E044', ['FI']], ['E045', ['FR']], ['E046', ['FR']], ['E047', ['FR']], ['E049', ['DE']], ['E050', ['DE', 'AT', 'CH']], ['E051', ['DE']], ['E052', ['DE']], ['E053', ['DE', 'SE']], ['E054', ['DE', 'FR', 'IE', 'CH']], ['E055', ['DE', 'CH', 'AT']], ['E056', ['GH', 'GN', 'ZM', "CI", 'AO', 'TN']], ['E058', ['HK']], ['E059', ['HK']], ['E061', ['HK', 'TW']], ['E063', ['IN']], ['E064', ['IN']], ['E065', ['IN']], ['E066', ['IN']], ['E067', ['IN']], ['E068', ['IN']], ['E069', ['IN']], ['E070', ['IN']], ['E071', ['IN']], ['E072', ['IN']], ['E073', ['IN']], ['E074', ['IN']], ['E075', ['IN']], ['E076', ['IN']], ['E078', ['ID']], ['E079', ['ID']], ['E081', ['IQ']], ['E082', ['IQ']], ['E083', ['IT']], ['E085', ['JP']], ['E086', ['JP']], ['E087', ['JP']], ['E089', ['JP']], ['E091', ['KZ']], ['E092', ['KW']], ['E094', ['BR', 'CO', 'MX', 'EC', 'PA']], ['E095', ['BR', 'CO', 'MX', 'VE']], ['E096', ['MX', 'BR', 'CL', 'AR', 'DO', 'EC', 'PY']], ['E097', ['BR', 'MX', 'PE', 'CO', 'CL']], ['E098', ['CL', 'AR', 'BR', 'PE', 'MX', 'EC', 'CO']], ['E099', ['MX', 'AR', 'CO', 'VE']], ['E100', ['CO', 'AR', 'PA', 'PE', 'BR', 'CR']], ['E103', ['MY']], ['E104', ['MY']], ['E105', ['IT', 'PT', 'ES', 'GR', 'CY']], ['E106', ['ES', 'CY', 'GR', 'IL', 'IT', 'PT']], ['E107', ['MX']], ['E108', ['MX']], ['E110', ['MX', 'BR', 'AR', 'CR']], ['E111', ['AE', 'BH', 'KW', 'QA', 'OM', 'SA']], ['E112', ['AE', 'SA']], ['E116', ['DK', 'SE', 'NO', 'FI', 'EE', 'LV', 'LT']], ['E117', ['NG']], ['E118', ['US', 'CA']], ['E119', ['NL', 'BE', 'FR', 'DE']], ['E120', ['NO']], ['E121', ['NO']], ['E122', ['OM']], ['E123', ['OM']], ['E124', ['PH']], ['E125', ['PH']], ['E128', ['PT']], ['E129', ['QA']], ['E132', ['SA']], ['E133', ['SA']], ['E135', ['SA']], ['E137', ['SA']], ['E138', ['SA']], ['E140', ['SG']], ['E141', ['SG']], ['E143', ['SG']], ['E145', ['ZA', 'BW']], ['E146', ['MY', 'VN', 'TH', 'ID', 'MM', 'PH', 'KH']], ['E147', ['SG', 'MY', 'TH', 'ID', 'VN']], ['E148', ['KR']], ['E149', ['KR']], ['E150', ['KR']], ['E151', ['KR']], ['E152', ['KR']], ['E153', ['ZA', 'AO', 'ET', 'ZM', 'NG', 'UG', 'TN']], ['E154', ['ZA', 'GH', 'MZ', 'NA', 'NG', 'CM', 'ZM']], ['E155', ['ES']], ['E156', ['ES']], ['E158', ['SE']], ['E159', ['SE']], ['E161', ['CH', 'US', 'DK']], ['E163', ['TH']], ['E164', ['TH']], ['E165', ['TR']], ['E166', ['TR']], ['E167', ['TR']], ['E168', ['TR']], ['E169', ['TR']], ['E170', ['UA']], ['E171', ['UA']], ['E174', ['AE']], ['E175', ['AE']], ['E179', ['AE', 'KW']], ['E182', ['US']], ['E183', ['US', 'TN', 'UG', 'KE', 'MM', 'PH', 'GH']], ['E184', ['US']], ['E185', ['US']], ['E186', ['US']], ['E187', ['US', 'CA']], ['E188', ['US']], ['E189', ['US']], ['E191', ['US']], ['E192', ['US', 'CA', 'MX']], ['E194', ['US']], ['E209', ['TN', 'LY', 'EG']], ['E210', ['MN']], ['E211', ['KZ']], ['E212', ['TW']], ['E215', ['']], ['E217', ['MA']], ['E218', ['AT']], ['E219', ['CZ', 'BG', 'RO', 'BA', 'SK', 'HR', 'HU']], ['E220', ['CZ', 'PL', 'RO', 'BG', 'SK']], ['E221', ['BG', 'PL', 'RS', 'BA']], ['E222', ['PL', 'BG', 'CZ', 'HU', 'RO', 'SI']], ['E223', ['CO']], ['E224', ['XG']], ['E225', ['QA', 'JP', 'CN', 'PE', 'ID', 'FR']], ['E226', ['CN', 'IN', 'HK']], ['E227', ['IN']], ['E228', ['ID']], ['E229', ['IR']], ['E230', ['BR', 'MX', 'PA', 'CU', 'PE']], ['E231', ['SA', 'AE', 'KW', 'OM', 'BH']], ['E232', ['AE', 'SA', 'KW', 'QA', 'OM']], ['E233', ['FI', 'DK', 'NO', 'SE', 'IS']], ['E234', ['']], ['E235', ['RU']], ['E236', ['SG', 'TH']], ['E237', ['ES']], ['E238', ['CH']], ['E239', ['AT', 'CH', 'NL']], ['E240', ['BR', 'AR', 'MX', 'CO']], ['E241', ['IR']], ['E242', ['RU']], ['E243', ['RU']]]
    financial_year = FinancialYear.objects.get(id=2017)
    for item in hvc_2017:
        hvc = item[0]
        if Target.objects.filter(campaign_id=hvc, financial_year=financial_year).exists():
            target = Target.objects.get(campaign_id=hvc, financial_year=financial_year)
            for country_code in item[1]:
                # skip entries without country codes
                if country_code != '' and country_code != 'XG':
                    country = Country.objects.get(country=country_code)
                    target.country.add(country)


class Migration(migrations.Migration):

    dependencies = [
        ('mi', '0037_auto_20170610_2310'),
    ]

    operations = [
        migrations.RunPython(add_2017_hvc_countries),
    ]
