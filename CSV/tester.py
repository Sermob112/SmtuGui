import csv

with open('sources/9.5к Закупки полные.csv', 'r', encoding='utf-8', newline='') as infile, \
     open('sources/output.csv', 'w', encoding='utf-8', newline='') as outfile:
    reader = csv.reader(infile, delimiter=',')
    writer = csv.writer(outfile, delimiter=';')
    for row in reader:
        writer.writerow(row)