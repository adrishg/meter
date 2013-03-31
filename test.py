from scanner import Scanner

scanner = Scanner()

data = {}
import csv
verses = {}
multiple_matches = []
total_verses  = 0
total_matches = 0
with open('data/verses.csv', 'rb') as csvfile:
    versereader = csv.reader(csvfile, delimiter=',', quotechar='|')
    count = 0
    multiple_match_count = 0
    for row in versereader:
        (verse_id, input_string, real_scan) = row
        scan = scanner.scan(input_string, known_only = True)
#        if not(len(scan['results'])>0):
#
#            print 'Error '+verse_id+":"+input_string
#            scan = scanner.scan(input_string, known_only = False)
#            print scanner.print_scan(scan)
#            scan = scanner.scan(input_string, known_only = True)
        total_matches+=len(scan['results'])
        total_verses +=1
              
        assert len(scan['results'])>0

print 'total verses = '+str(total_verses)
print 'total matches = '+str(total_matches)
assert total_verses==3314
assert total_matches==4036
#189.07.0, apnii rusvaa))ii me;n kyaa chaltii hai sa((y,G14
#118.04.0, ;gaalib kuchh apnii sa((y se lahnaa nahii;n mujhe,G3
