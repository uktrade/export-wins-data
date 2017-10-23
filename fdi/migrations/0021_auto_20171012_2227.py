# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-12 22:27
from __future__ import unicode_literals

from django.db import migrations


def add_markets(apps, schema_editor):
    Market = apps.get_model('fdi', 'Market')
    Country = apps.get_model('fdi', 'Country')
    MarketCountry = apps.get_model('fdi', 'MarketCountry')

    markets = {
        "Australia & New Zealand": "AU|NZ",
        "Austria": "AT",
        "Belgium (& Lux)": "BE|LU",
        "Canada": "CA",
        "China": "CN",
        "Denmark": "DK",
        "Finland": "FI",
        "France": "FR",
        "Germany": "DE",
        "Hong Kong": "HK",
        "India": "IN",
        "Ireland": "IE",
        "Israel": "IL",
        "Italy": "IT",
        "Japan": "JP",
        "Netherlands": "NL",
        "Norway": "NO",
        "Portugal": "PT",
        "Singapore": "SG",
        "South Korea": "KR",
        "Spain": "ES",
        "Sweden": "SE",
        "Switzerland": "CH",
        "Turkey": "TR",
        "United States": "US",
        "Spain & Italy": "ES|IT",
        "France & Italy & Spain & Israel": "FR|IT|ES|IL",
        "Portugal & Italy": "PT|IT",
        "Brazil & Mexico & Argentina": "BR|MX|AR",
        "China & Hong Kong": "CN|HK",
        "UAE & Bahrain & Kuwait & Qatar & Saudi Arabia": "AE|BH|KW|QA|SA",
        "Mexico & Brazil": "MX|BR",
        "Sweden & Finland & Norway & Estonia": "SE|FI|NO|EE",
        "Brazil & Mexico & Argentina & Chile & Colombia": "BR|MX|AR|CL|CO",
        "Baltics (Est, Lat, Lith) & Sweden & Finland & Norway & Denmark & Iceland": "EE|LV|LT|SE|FI|NO|DK|IS",
        "Bulgaria": "BG",
        "Croatia": "HR",
        "Czech Republic": "CZ",
        "Hungary": "HU",
        "Poland": "PL",
        "Romania": "RO",
        "Slovakia": "SK",
        "Slovenia": "SI",
        "Argentina": "AR",
        "Brazil": "BR",
        "Chile": "CL",
        "Colombia": "CO",
        "Mexico": "MX",
        "Peru": "PE",
        "Bahrain": "BH",
        "Kuwait": "KW",
        "Qatar": "QA",
        "Saudi Arabia": "SA",
        "UAE": "AE",
        "Baltics (Est, Lat, Lith)": "EE|LV|LT",
        "Iceland": "IS",
        "Taiwan": "TW",
        "Malaysia": "MY",
        "Philippines": "PH",
        "Thailand": "TH",
        "South Africa": "ZA",
        "Kazakhstan": "KZ",
        "Russia": "RU"
    }

    for market_name, countries_str in markets.items():
        Market(name=market_name).save()
        market = Market.objects.get(name=market_name)
        countries = countries_str.split("|")
        for country_code in countries:
            country = Country.objects.get(iso_code=country_code)
            MarketCountry(market=market, country=country).save()


class Migration(migrations.Migration):

    dependencies = [
        ('fdi', '0020_auto_20171012_2215'),
    ]

    operations = [
        migrations.RunPython(add_markets),
    ]