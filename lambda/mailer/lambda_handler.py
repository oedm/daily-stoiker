import boto3
import json
import sys
import datetime
import locale
import os
from bs4 import BeautifulSoup
import botocore

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
        delta = self.desiredDate - datetime.datetime(self.desiredDate.year,1,1)
        self.daysPassed= delta.days + 1
        self.exec_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Generate HTML message for {str(self.day)}. {str(self.monthName)}")
        self.lookupMessage()

    def lookupMessage(self):
        # Load css file
        filePath = os.path.join(self.exec_dir, "src-pub/css/stylesheet.css")
        with open(filePath, "r") as f:
            cssData = f.read()
        # Open book chapter of desired month
        filePath = os.path.join(self.exec_dir, "src-pub/chap{:02d}.xhtml".format(self.month))
        with open(filePath, "r") as f:
            xhtmlData = f.read()
            
            # BeautifulSoup initize
            soup = BeautifulSoup(xhtmlData, 'html.parser')

            # find all headline elements
            headlineElements = soup.find_all('p', class_='Headline')
            topicOfMonth = soup.find('h2', class_='h2a')
            self.topic = topicOfMonth.get_text().strip()
            results = []
            for headline in headlineElements:
                #Extract day and title of headline
                day = int(headline.get_text().split(' ')[0].strip().replace(".", ""))
                textAfterDate = headline.get_text().split(' ')[2:]
                titleOfDay = ' '.join(textAfterDate).capitalize()
                
                #Extract body for each day
                next_sibling = headline.find_next_sibling()
                bodyHtml = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <style>{cssData}</style>
                </head>
                <body>
                {str(topicOfMonth)}
                {str(headline)}"""

                while next_sibling and not next_sibling.get('class') == ['Headline']:
                    bodyHtml += str(next_sibling)
                    next_sibling = next_sibling.find_next_sibling()
                
                bodyHtml += "</body></html>"
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
    ddb = boto3.resource("dynamodb")
    ses = boto3.client('ses')
    tableName = os.environ.get('NEWSLETTER_TABLE', 'stoiker_newsletter')
    #Check if we're in our local development environment
    if os.environ.get('environment') == "local":
        print("Running locally")
        ddb = boto3.resource("dynamodb", endpoint_url="http://localhost:18000")
        session = boto3.Session(profile_name="moed")
        ses = session.client('ses')

    # Instantiate class
    dailyNewsletter = NewsletterClass(
        month=event.get("month", None), 
        day=event.get("day", None)
    )
    
    # Example ddb entrie structure
    # {   
    #     "email": S "john.doe@example.com",
    # }

    # Get all subscribed users from ddb
    table = ddb.Table(tableName)
    response = table.scan()
    receipients = [item['email'] for item in response['Items']]
    if receipients == []:
        print("No subscribers found")
        sys.exit(0)
    
    # Send html email via SES
    totalReceipients = len(receipients)
    for index, receipient in enumerate(receipients):
        try:
            response = ses.send_email(
                Source='"Der tägliche Stoiker" <stoiker@moed.cc>',
                Destination={
                    'ToAddresses': [
                        receipient,
                    ],
                },
                Message={
                    'Subject': {
                        'Data': f'#{dailyNewsletter.daysPassed}: {dailyNewsletter.title}',
                    },
                    'Body': {
                        'Html': {
                            'Data': dailyNewsletter.htmlBody,
                        },
                    },
                },
            )
        except botocore.exceptions.ClientError as e:
            print(e.response['Error']['Message'])
        print(f"Sent {index+1} of {totalReceipients} emails.")
        print(f"messageId: {response['MessageId']} - {response['ResponseMetadata']['HTTPStatusCode']}")

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
                print("Loaded JSON file:", event)
        except FileNotFoundError:
            print(f"File not found: {json_file}")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Non valid JSON found in {json_file}")
            sys.exit(1)
        main(event, None)
        sys.exit(0)