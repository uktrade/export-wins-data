from django.db.models.aggregates import Sum

from wins.constants import BREAKDOWN_TYPES
from wins.models import Win, Advisor


def report_missing_ids(given, found):
    missing_ids = [x for x in given if x not in [str(w.id) for w in found]]
    print('queried for {} wins'.format(len(given)),
          'found {} wins'.format(found.count()), len(missing_ids),
          'missing wins:', missing_ids)


def get_ids_from_str(id_str):
    return [x for x in id_str.split('\n') if x]


def get_wins(id_str):
    ids = get_ids_from_str(id_str)
    wins = Win.objects.filter(id__in=ids)
    report_missing_ids(ids, wins)
    return wins


def get_field(wins, fieldname):
    for win in wins:
        win = Win.objects.get(id=win.id)
        try:
            display = getattr(win, 'get_{}_display'.format(fieldname))()
        except AttributeError:
            display = ''
        print(getattr(win, fieldname), display, win.id)


def set_field(wins, fieldname, val):
    for win in wins:
        setattr(win, fieldname, val)
        win.save()
    get_field(wins, fieldname)


def reactivate(id_str):
    ids = get_ids_from_str(id_str)
    print('reactivating {} wins'.format(len(ids)))
    active = Win.objects.filter(id__in=ids)
    if active:
        print('found {} already active wins:'.format(len(active)), active,
              'remaining:', ids)
        ids = [x for x in ids if x not in [str(w.id) for w in active]]
    else:
        print('no active wins found')
    if not ids:
        print('no inactive wins supplied')
        return
    wins = Win.objects.inactive().filter(id__in=ids)
    report_missing_ids(ids, wins)
    if not wins:
        print('no inactive wins found')
        return
    for win in wins:
        win.is_active = True
        win.save()
    assert(Win.objects.filter(id__in=ids).count() == len(ids))
    print('activated')


def swap_obj_type(obj):
    if obj.type == 1:
        obj.type = 2
    elif obj.type == 2:
        obj.type = 1
    else:
        raise Exception('wat')
    obj.save()


def swap_win_type(win):
    swap_obj_type(win)
    for breakdown in win.breakdowns.all():
        swap_obj_type(breakdown)


def add_advisor(win_id, name, hq_team):
    win = Win.objects.get(id=win_id)
    team_type = hq_team.split(':')[0]
    if win.advisors.filter(win=win, name=name, team_type=team_type, hq_team=hq_team):
        print('already exists')
        return
    elif win.advisors.filter(win=win, team_type=team_type, hq_team=hq_team):
        print('maybe already exists')
        return
    Advisor(win=win, name=name, team_type=team_type, hq_team=hq_team).save()
    print(win.advisors.all())


def update_numbers(win_id, new_total, year1, year2, year3, year4, year5,
                   audit='', value_type=None, update_confirmed=True):
    assert value_type in ['export', 'non_export', 'odi'], 'invalid value'
    # get breakdown values and check they add up to the total
    years = [year1, year2, year3, year4, year5]
    years = [int(y) if y != '' else 0 for y in years]
    assert_fail_msg = 'values do not add up: %s %s' % (new_total, sum(years))
    assert new_total == sum(years), assert_fail_msg
    # get win, check if its confirmed and we don't want to overwrite confirmed
    win = Win.objects.get(id=win_id)
    if not update_confirmed and win.confirmed:
        print('Win already confirmed, aborting')
        return
    # output current win details
    total_attr_str = 'total_expected_{}_value'.format(value_type)
    print(win_id, getattr(win, total_attr_str), new_total)
    # set the new total
    setattr(win, total_attr_str, new_total)
    win.save()
    # get and re-set the breakdowns
    breakdown_dict = dict((v, k) for k, v in BREAKDOWN_TYPES)
    if value_type == 'odi':
        breakdown_name = 'Outward Direct Investment'
    elif value_type == 'export':
        breakdown_name = 'Export'
    elif value_type == 'non_export':
        breakdown_name = 'Non-export'
    breakdown_type = breakdown_dict[breakdown_name]
    breakdowns = win.breakdowns.filter(type=breakdown_type)
    print(breakdowns)
    for value, breakdown in zip(years, breakdowns):
        breakdown.value = value or 0
        breakdown.save()
    breakdowns = win.breakdowns.filter(type=breakdown_type)
    print(breakdowns)
    # add audit info
    win.add_audit('Updated {}; total: {}, years: {} - {}'.format(
        breakdown_name,
        new_total,
        years,
        audit,
    ))
    win.save()
    print('Audit:\n', win.audit)
    # final check that inoput breakdowns equal input total
    win = Win.objects.get(id=win_id)
    sum_breakdowns = win.breakdowns.filter(
        type=breakdown_type,
    ).aggregate(
        total=Sum('value'),
    )['total']
    assert_fail_msg = ('saved values do not add up {} {}'.format(
        win.total_expected_export_value,
        sum_breakdowns,
    ))
    assert getattr(win, total_attr_str) == sum_breakdowns, assert_fail_msg
