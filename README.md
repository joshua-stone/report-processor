# report-processor
Configurable report processor that turns CSV input into tables for data analysis

## CLI usage

```bash
$ ./survey-processor.py --help
usage: survey-processor.py [-h] [--output OUTPUT] INPUT REPORT

Process CSV

positional arguments:
  INPUT            Input CSV file
  REPORT           Report config JSON file

options:
  -h, --help       show this help message and exit
  --output OUTPUT  Output file
```

```bash
$ ./survey-processor.py survey.csv reports/01.json --output=output.md
```
