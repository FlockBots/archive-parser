import csv, praw, requests, re, logging
from http.cookiejar import CookieJar
from urllib.request import build_opener, HTTPCookieProcessor
from collections import namedtuple

class Parser():
    def __init__(self, filename):
        self.filename = filename
        self.user_agent = 'Whisky Archive Parser by /u/FlockOnFire'
        logging.basicConfig(
            filename='parser.log',
            level=logging.INFO,
            format='{asctime} | {levelname:^8} | {message}',
            style='{'
        )

        self.date_pattern = re.compile(r'\d{2}.\d{2}.\d{2,4}')

        # disable requests logging
        requests_logger = logging.getLogger('requests')
        requests_logger.propagate = False

    def download(self, key):
        logging.info('Downloading Archive')
        opener = build_opener(HTTPCookieProcessor(CookieJar()))
        response = opener.open('https://docs.google.com/spreadsheet/ccc?key={key}&output=csv'.format(key=key))
        data = response.read().decode('utf-8')
        with open(self.filename, encoding='utf-8', mode='w') as f:
            f.write(data)

    def parse_date(self, date_string):
        """Gets the year, month and day from a string in mm/dd/yy(yy) format

        Asserts the string is in mm/dd/yy or mm/dd/yyyy format
        and returns a tuple containing the year (yyyy), month (mm) and day (dd).

        If the string happens to be in dd/mm/yy format, it switches the day and month.

        Args:
            date_string: (string) Date in mm/dd/yy or mm/dd/yyyy format

        Returns:
            A namedtuple with year, month and day attributes
        """
        match = self.date_pattern.search(date_string)
        if match:
            month, day, year = map(int, match.groups())
            if month > 12:
                month, day = day, month
            if year < 1000:
                year += 2000

            date = namedtuple("Date", ["year", "month", "day"])
            return date(year, month, day)
        return None

    def _row_to_dict(self, row):
        return {
            'whisky': row[1],
            'user'  : row[2],
            'url'   : row[3],
            'score' : row[4],
            'region': row[5],
            'price' : row[6],
            'date'  : row[7]
        }

    def get_rows(self):
        with open(self.filename, encoding='utf-8', mode='r') as archive:
            reader = csv.reader(archive, delimiter=',')
            headers = next(reader)
            for row in reader:
                yield self._row_to_dict(row)

    def get_submissions(self, skip=0):
        reddit = praw.Reddit(self.user_agent)
        rows = self.get_rows();
        counter = 0
        for row in self.get_rows():
            if counter < skip:
                counter += 1
                continue
            try:
                submission = reddit.get_submission(row['url'])
            except:
                logging.error('Unable to request ' + row['url'])
                continue
            yield submission