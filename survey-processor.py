#!/usr/bin/env python3

import argparse
import csv
import json

DEFAULTS = {
        'title': '',
        'answer_types': {'*': 'single'},
        'filter': {},
        'ignore': {},
        'select': {}
}


TABLE_NAMES = [
    'Word',
    'Count',
    'Percent'
]


def calc_percent(numerator, denominator):
    return round((numerator / denominator) * 100, 2)


def get_widths(table_names, rows):
    widths = []
    for index in range(len(rows[0])):
        widths.append(max(len(table_names[index]),
                          len(max([row[index] for row in rows], key=len))))

    return widths


def to_markdown(data):
    output = []
    for header, rows in data:
        width1, width2, width3 = get_widths(TABLE_NAMES, rows)
        output.append('## {}'.format(header))
        output.append('| {} | {} | {} |'.format(TABLE_NAMES[0].rjust(width1, ' '),
                                                TABLE_NAMES[1].rjust(width2, ' '),
                                                TABLE_NAMES[2].rjust(width3, ' ')
            ))
        output.append('| {} | {} | {} |'.format('-' * width1,
                                                '-' * width2,
                                                '-' * width3))

        for entry, count, percent in rows:
            output.append('| {} | {} | {} |'.format(entry.rjust(width1, ' '),
                                                    count.rjust(width2, ' '),
                                                    percent.rjust(width3, ' ')))
        output.append('')
    return '\n'.join(output)


class ReportConf(object):
    def __init__(self, data):
        self._data = data
        self._data.setdefault('defaults', {})
        for key, value in DEFAULTS.items():
            self._data['defaults'].setdefault(key, value)
                
        for report in self._data['reports']:
            for key, value in self._data['defaults'].items():
                report.setdefault(key, value)

    @property
    def reports(self):
        return self._data['reports']

    def __getitem__(self, index):
        return self.reports[index]

class ReportResult(object):
    def _get_answer_type(self, index):
        return self._answer_types.get(str(index)) or self._answer_types.get('*') \
               or DEFAULTS['answer_types'].get(str(index)) or DEFAULTS['answer_types'].get('*')

    def __init__(self, conf, document):
        self._conf = conf
        self._header, *self._entries = document

        self._filter_options = self._conf['filter']
        self._answer_types = self._conf['answer_types']
        rows = []
        for row in self._entries:
            res = []
            for key, val in self._filter_options.items():
                if self._get_answer_type(key) == 'multi':
                    res.append(set(val).issubset(row[int(key)].split(';')))
                else:
                    res.append(row[int(key)] in val)
            if all(res):
                rows.append(row)

        self._results = [{} for _ in range(len(self._header))]
        self._totals = [0 for _ in range(len(self._header))]
   
        ignored = [self._conf['ignore'].get(str(index)) or []
                   for index in range(len(self._header))]

        for row in rows:
            for index, column in enumerate(row):
                updated = False
                if self._get_answer_type(index) == 'multi':
                    for entry in [e.strip() for e in column.split(';')]:
                        if entry not in ignored[index]:
                            self._results[index].setdefault(entry, 0)
                            self._results[index][entry] += 1
                            updated = True
                else:
                    entry = column.strip()
                    if entry not in ignored[index]:
                        self._results[index].setdefault(entry, 0)
                        self._results[index][entry] += 1
                        updated = True

                if updated:
                    self._totals[index] += 1

    @property
    def totals(self):
        return self._totals

    @property
    def results(self):
        return self._results
    def calc_percents(self):
        results = []
        for row in (self._conf['select'] or range(len(self._header))):
            entry = self._results[int(row)]
            total = self.totals[int(row)] if self._get_answer_type(row) == 'multi' else sum(entry.values())
                   
            results.append([
                self._header[int(row)].strip(),
                sorted([(key, str(value), '{}%'.format(calc_percent(value, total))) for key, value in entry.items()], reverse=True, key=lambda x: int(x[1]))
            ])

        return results

    def render(self):
        return to_markdown(self.calc_percents())


def main():
    parser = argparse.ArgumentParser(description='Process CSV')
    parser.add_argument('input', metavar='INPUT', help='Input CSV file')
    parser.add_argument('report', metavar='REPORT', help='Report config JSON file')
    parser.add_argument('--output', metavar='OUTPUT', help='Output file')

    args = parser.parse_args()
    with open(args.report, 'r') as infile:
        report_config = ReportConf(json.load(infile))

    with open(args.input, encoding='utf-8') as infile:
        document = list(csv.reader(infile))

    output = ''
    for report in report_config:
        result = ReportResult(report, document)

        output += result.render()

    if args.output:
        with open(args.output, 'w') as outfile:
            outfile.write(output)
    else:
        print(output)


if __name__ == '__main__':
    main()
