import csv
import json
import datetime
import collections
import operator

import ui
import dialogs

from datasources import *

with open('hymns.csv') as hymns_file, open('tags.json') as tags_file, open('history.json') as history_file:
    hymns = list(csv.DictReader(hymns_file))
    tags = json.load(tags_file)
    history = sorted(((datetime.date(*map(int, date.split('-'))), hymns) for date, hymns in json.load(history_file).items()), key=operator.itemgetter(0), reverse=True)

def search(sender):
    if sender.text:
        try:
            v['results'].data_source.set_hymns([hymns[int(sender.text) - 1]])
        except (ValueError, IndexError):
            results = []
            for hymn in hymns:
                for word in sender.text.split():
                    if word.lower() not in hymn['title'].lower():
                        break
                else:
                    results.append(hymn)
            v['results'].data_source.set_hymns(results)
    else:
        v['results'].data_source.set_hymns(hymns)
    
    v['results'].reload_data()

@ui.in_background
def filter(sender):
    f = dialogs.form_dialog('Filter', sections=[
        ('Tags', [
            {'title': tag['name'], 'type': 'check', 'background_color': tag['color']} for tag in tags
        ])
    ])
    
    if f and any(f.values()):
        v['results'].data_source.set_hymns(sorted((hymn for hymn in hymns if all(hymn['#'] in tag['hymns'] for tag in tags if f[tag['name']])), key=lambda h: int(h['#'])))
    else:
        v['results'].data_source.set_hymns(hymns)
    v['results'].reload_data()

def load_history(sender):
    hv = ui.TableView('grouped')
    hv.name = 'History'
    hv.data_source = HistoryDataSource(hymns, tags, history, v['results'].reload_data)
    hv.delegate = hv.data_source
    hv.right_button_items = [
        ui.ButtonItem('Edit', action=lambda s: hv.set_editing(not hv.editing, True))
    ]
    nav.push_view(hv)

v = ui.load_view()

v['results'].data_source = HymnsDataSource(hymns, tags, history)
v['results'].delegate = v['results'].data_source
v.left_button_items = [
    ui.ButtonItem('Filter', action=filter)
]

v.right_button_items = [
    ui.ButtonItem('History', action=load_history)
]

nav = ui.NavigationView(v)
nav.present('sheet', hide_title_bar=True)
