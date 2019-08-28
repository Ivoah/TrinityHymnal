import matplotlib.pyplot as plt
import collections
import json
import csv

with open('history.json') as f:
    history = json.load(f)
with open('hymns.csv') as f:
    hymns = list(csv.DictReader(f))

counter = collections.Counter(hymn for day in history.values() for hymn in day)
xs, ys = zip(*counter.most_common())
names = [hymns[int(num) - 1]['title'] for num in xs]

plt.figure(figsize=(15, 8))
plt.xticks(rotation='vertical')
plt.subplots_adjust(0.05, 0.5, 0.95, 0.95)
plt.bar(names, ys)
plt.savefig('history.png')
plt.show()
