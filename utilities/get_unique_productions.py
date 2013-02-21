import re
# This file displays a list of unique rule productions, for generating bad combos.
# I made these more descriptive, so there need to be additions to the bad combos.
 
def load_yaml(filename):
    import yaml
    stream = file(filename)
    return yaml.load(stream)

short = load_yaml("../settings/short.yaml")
long = load_yaml("../settings/long.yaml")
productions = []
for settings in (short, long):
    for (key, value) in settings['rules'].iteritems():
        key_no_spaces = re.sub(' ','', key)
        if key_no_spaces != value[2:]:
            print key+" has wrong production "+value
        productions.append(value)

print "\n".join(sorted(productions))

import csv
with open('../settings/bad_combos.csv', 'rb') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in spamreader:
        for _ in row:
            if not _ in productions:
                print "missing " + _ + " in "+','.join(row)
