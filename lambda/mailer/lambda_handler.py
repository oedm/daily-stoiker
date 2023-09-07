import boto3
import json
import sys
import datetime
import locale
import os
from bs4 import BeautifulSoup

# German time format
locale.setlocale(locale.LC_TIME, 'de_DE')

class NewsletterClass:
    def __init__(self, month=None, day=None):
        now = datetime.datetime.now()
        if month is not None or day is not None:
            self.desiredDate = datetime.datetime(now.year, month, day)
        else:
            self.desiredDate = now
        # Hyphen removes leading zero of month 09 -> 9
        self.month = int(self.desiredDate.strftime("%-m"))
        self.day = int(self.desiredDate.strftime("%d"))
        self.monthName = self.desiredDate.strftime("%B")
        self.exec_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Generate HTML message for {str(self.day)}. {str(self.monthName)}")
        self.lookupMessage()

    def lookupMessage(self):
        # Open book chapter of desired month
        filePath = os.path.join(self.exec_dir, "src-pub/chap{:02d}.xhtml".format(self.month))
        with open(filePath, "r") as f:
            xhtmlData = f.read()
            
            # BeautifulSoup initize
            soup = BeautifulSoup(xhtmlData, 'html.parser')

            # find all headline elements
            headlineElements = soup.find_all('p', class_='Headline')
            results = []
            for headline in headlineElements:
                #Extract day and title of headline
                day = int(headline.get_text().split(' ')[0].strip().replace(".", ""))
                textAfterDate = headline.get_text().split(' ')[2:]
                titleOfDay = ' '.join(textAfterDate).capitalize()
                
                #Extract body for each day
                next_sibling = headline.find_next_sibling()
                bodyHtml = ''
                while next_sibling and not next_sibling.get('class') == ['Headline']:
                    bodyHtml += str(next_sibling)
                    next_sibling = next_sibling.find_next_sibling()
                
                results.append(
                    {
                        'day': day,
                        'titleOfDay': titleOfDay,
                        'bodyHtml': bodyHtml
                    }
                )
        # pick dataset from results for our desired day
        desiredEntry = next((item for item in results if item['day'] == self.day), None)
        self.title = desiredEntry['titleOfDay']
        self.htmlBody = desiredEntry['bodyHtml']
        print("Message loaded")

def main(event, context):
    dailyNewsletter = NewsletterClass(
        month=event.get("month", None), 
        day=event.get("day", None)
    )
    sys.exit(0)
    ddb = boto3.resource("dynamodb")
    table = ddb.Table("stoiker_newletter")
    # Example ddb entrie structure
    # {   
    #     "email": S "john.doe@example.com",
    #     "created_at": S "2023-07-17 12:00:00+00:00",
    #     "subscribed": B true
    # }

    # Get all subscribed users from ddb
    recipients = table.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr("subscribed").eq(True)
    )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        event = {}
        main(event, None)
    else:
        # First argument is JSON file
        json_file = sys.argv[1]
        try:
            with open(json_file, 'r') as file:
                event = json.load(file)
                print(type(event))
                print("Loaded JSON file:", event)
        except FileNotFoundError:
            print(f"File not found: {json_file}")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Non valid JSON found in {json_file}")
            sys.exit(1)
        main(event, None)
        sys.exit(0)