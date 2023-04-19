import requests
import datetime
import pytz
import smtplib
import schedule
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.utils import COMMASPACE
from email import encoders

# criteria set 1 (offshore wind and positive swell)
direction_min = 50
direction_max = 240
speed_max = 40
height_min = 0.29
period_min = 3.9
swelldirection_min = 70
swelldirection_max = 200

# Criteria set 2 (just incomming swell, wind irrelevant)
qdirection_min = 359
qdirection_max = 1
qspeed_max = 20
qheight_min = 0.39
qperiod_min = 4.9
qswelldirection_min = 90
qswelldirection_max = 210

# email settings
email_sender = 'surfmelding@gmail.com'
email_password = 'surfsurfsurf'
email_admin = ['jaimyvanderheijden@gmail.com']
email_recipients = ['jaimyvanderheijden@gmail.com']

# function to send email
def send_email(subject, message, files=[]):
    try:
        msg = MIMEMultipart()
        msg['From'] = email_sender
        msg['To'] = COMMASPACE.join(email_recipients)
        msg['Subject'] = subject

        msg.attach(MIMEText(message, 'plain'))

        for f in files:
            with open(f, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename= {f}",)
            msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_sender, email_password)
        server.sendmail(email_sender, email_recipients, msg.as_string())
        server.quit()
        print('Email sent successfully')
    except Exception as e:
        print('Error sending email:', str(e))

# schedule the script to run every 24 hours at 15:00 CET
def job():

    # get current date and time in CET timezone
    tz = pytz.timezone('Europe/Paris')
    now = datetime.datetime.now(tz)

    # get tomorrow's date
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)

    # get surf forecast for tomorrow
    api_key = '149ef032c0d1dd2d26397212fa0658ad'
    secret_url = 'c786d38f8f870a34460af22dde653b7a'
    spot_id = '145'
    fields = 'localTimestamp,swell.*,wind.*'
    linktomsw = "https://magicseaweed.com/Scheveningen-Nord-Surf-Report/145/"

    url = f'http://magicseaweed.com/api/{api_key}/forecast/?spot_id={spot_id}&fields={fields}'
    response = requests.get(url, headers={'Authorization': f'Token {secret_url}'})

    if response.status_code == 200:
        # filter forecast data to get only tomorrow's data
        forecast_data = response.json()
        tomorrow_data = [data for data in forecast_data if datetime.datetime.fromtimestamp(data['localTimestamp'], tz).date() == tomorrow]

        if len(tomorrow_data) > 0:
            # check if surf conditions meet criteria set 1
            good_surf = False
            for data in tomorrow_data:
                if (direction_min <= data['wind']['direction'] <= direction_max and
                    data['wind']['speed'] <= speed_max and
                    data['swell']['height'] >= height_min and
                    data['swell']['period'] >= period_min and
                    swelldirection_min <= data['swell']['direction'] <= swelldirection_max):
                    good_surf = True
                    break

            # check if surf conditions meet criteria set 2
            suboptimal_surf = False
            for data in tomorrow_data:
                if (qdirection_min <= data['swell']['direction'] <= qdirection_max and
                    data['swell']['speed'] <= qspeed_max and
                    data['swell']['height'] >= qheight_min and
                    data['swell']['period'] >= qperiod_min and
                    qswelldirection_min <= data['swell']['direction'] <= qswelldirection_max):
                    suboptimal_surf = True
                    break

            # send email if surf conditions meet criteria set 1
            if good_surf:
                message = "Surf conditions for tomorrow are looking great. Get ready to catch some waves!\n\n"
                message += "Here's a summary of the surf forecast for tomorrow:\n"
                for data in tomorrow_data:
                    message += f"\nTime: {datetime.datetime.fromtimestamp(data['localTimestamp'], tz).strftime('%H:%M')}\n"
                    message += f"Wind: {data['wind']['direction']} degrees @ {data['wind']['speed']} kph\n"
                    message += f"Swell: {data['swell']['height']} m @ {data['swell']['period']} s ({data['swell']['direction']} degrees)\n"
                    message += f"Check out the surf forecast for tomorrow at {linktomsw}\n\n"
                send_email('Good surf tomorrow!', message)

            # send email if surf conditions meet criteria set 2
            elif suboptimal_surf:
                message = "Surf conditions for tomorrow are suboptimal, but there will still be waves to catch.\n\n"
                message += "Here's a summary of the surf forecast for tomorrow:\n"
                for data in tomorrow_data:
                    message += f"\nTime: {datetime.datetime.fromtimestamp(data['localTimestamp'], tz).strftime('%H:%M')}\n"
                    message += f"Swell: {data['swell']['height']} m @ {data['swell']['period']} s ({data['swell']['direction']} degrees)\n"
                    message += f"Check out the surf forecast for tomorrow at {linktomsw}\n\n"
                send_email('Suboptimal surf tomorrow', message)

            else:
                print('Surf conditions for tomorrow do not meet criteria')

        # send email if there is no surf (conditions not met)
        else:
            message = "There are is no surf tomorrow. Time to take a break and rest up for better waves.\n"
            send_email('No surf tomorrow', message)

    else:
        print('Error getting surf forecast:', response.text)
        

 schedule.every().day.at("15:00").do(job)
    print("Running surf forecast script...")
    
while True:
    schedule.run_pending()
    # wait for 1 minute
    time.sleep(60)


