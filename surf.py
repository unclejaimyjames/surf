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

# Criteria set 1 (longboard surf with favorable wind and positive swell)
CS1direction_min = 50
CS1direction_max = 230
CS1speed_max_direction1 = 40  # max wind speed when wind direction is between direction_min and direction_max
CS1speed_max_direction2 = 10  # max wind speed when wind direction is outside of direction_min and direction_max
CS1height_min = 0.35
CS1period_min = 5

# Criteria set 2 (shortboard conditions with higher swell and favorable wind)
CS2direction_min = 50
CS2direction_max = 230
CS2speed_max_direction1 = 40  # max wind speed when wind direction is between direction_min and direction_max
CS2speed_max_direction2 = 10  # max wind speed when wind direction is outside of direction_min and direction_max
CS2height_min = 0.5
CS2period_min = 6

# Criteria set 3 (perfect conditions alert)
CS3direction_min = 50
CS3direction_max = 230
CS3speed_max_direction1 = 30  # max wind speed when wind direction is between direction_min and direction_max
CS3speed_max_direction2 = 5  # max wind speed when wind direction is outside of direction_min and direction_max
CS3height_min = 0.9
CS3period_min = 6

# email settings
email_sender = 'surfmelding@gmail.com'
email_password = 'zecngeimazrrbbrw'
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
            part.add_header("Content-Disposition", f"attachment; filename= {f}", )
            msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_sender, email_password)
        server.sendmail(email_sender, email_recipients, msg.as_string())
        server.quit()
        print('Email sent successfully')
    except Exception as e:
        print('Error sending email:', str(e))


# schedule the script to run every 24 hours
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
        tomorrow_data = [data for data in forecast_data if
                         datetime.datetime.fromtimestamp(data['localTimestamp'], tz).date() == tomorrow]

        if len(tomorrow_data) > 0:
            # check if surf conditions meet criteria set 1
            longboard_surf = False
            for data in tomorrow_data:
                if ((CS1direction_min <= data['wind']['direction'] <= CS1direction_max and
                     data['wind']['speed'] <= CS1speed_max_direction1) or
                    (data['wind']['direction'] > CS1direction_max or data['wind']['direction'] < CS1direction_min) and
                    data['wind']['speed'] <= CS1speed_max_direction2) and \
                        data['swell']['absMaxBreakingHeight'] >= CS1height_min and \
                        data['swell']['components']['combined']['period'] >= CS1period_min:
                    longboard_surf = True
                    break

            # check if surf conditions meet criteria set 2
            shortboard_surf = False
            for data in tomorrow_data:
                if ((CS2direction_min <= data['wind']['direction'] <= CS2direction_max and
                     data['wind']['speed'] <= CS2speed_max_direction1) or
                    (data['wind']['direction'] > CS2direction_max or data['wind']['direction'] < CS2direction_min) and
                    data['wind']['speed'] <= CS2speed_max_direction2) and \
                        data['swell']['absMaxBreakingHeight'] >= CS2height_min and \
                        data['swell']['components']['combined']['period'] >= CS2period_min:
                    shortboard_surf = True
                    break

            # check if surf conditions meet criteria set 3
            perfect_surf = False
            for data in tomorrow_data:
                if ((CS3direction_min <= data['wind']['direction'] <= CS3direction_max and
                     data['wind']['speed'] <= CS3speed_max_direction1) or
                    (data['wind']['direction'] > CS3direction_max or data['wind']['direction'] < CS3direction_min) and
                    data['wind']['speed'] <= CS3speed_max_direction2) and \
                        data['swell']['absMaxBreakingHeight'] >= CS3height_min and \
                        data['swell']['components']['combined']['period'] >= CS3period_min:
                    perfect_surf = True
                    break

            # send email if surf conditions meet criteria set 1
            if longboard_surf:
                message = "Surf conditions for tomorrow are good enough for some longboarding!\n\n"
                message += f"Check out the surf forecast for tomorrow at {linktomsw}\n\n"
                message += "Here's a summary of the surf forecast for tomorrow:\n"
                for data in tomorrow_data:
                    message += f"\nTime: {datetime.datetime.fromtimestamp(data['localTimestamp'], tz).strftime('%H:%M')}\n"
                    message += f"Wind: {data['wind']['direction']} degrees @ {data['wind']['speed']} kph\n"
                    message += f"Swell: {data['swell']['absMaxBreakingHeight']} m @ {data['swell']['components']['combined']['period']} s ({data['swell']['components']['combined']['direction']} degrees)\n"
                send_email('Nice surf tomorrow', message)

            # send email if surf conditions meet criteria set 2
            elif shortboard_surf:
                message = "Surf conditions for tomorrow are looking good. Get ready to catch some waves!\n\n"
                message += f"Check out the surf forecast for tomorrow at {linktomsw}\n\n"
                message += "Here's a summary of the surf forecast for tomorrow:\n"
                for data in tomorrow_data:
                    message += f"\nTime: {datetime.datetime.fromtimestamp(data['localTimestamp'], tz).strftime('%H:%M')}\n"
                    message += f"Swell: {data['swell']['absMaxBreakingHeight']} m @ {data['swell']['components']['combined']['period']} s ({data['swell']['components']['combined']['direction']} degrees)\n"
                send_email('Good surf tomorrow!', message)

            # send email if surf conditions meet criteria set 3
            elif perfect_surf:
                message = "Surf conditions for tomorrow are perfect!\n\n"
                message += f"Check out the surf forecast for tomorrow at {linktomsw}\n\n"
                message += "Here's a summary of the surf forecast for tomorrow:\n"
                for data in tomorrow_data:
                    message += f"\nTime: {datetime.datetime.fromtimestamp(data['localTimestamp'], tz).strftime('%H:%M')}\n"
                    message += f"Swell: {data['swell']['absMaxBreakingHeight']} m @ {data['swell']['components']['combined']['period']} s ({data['swell']['components']['combined']['direction']} degrees)\n"
                send_email('Perfect surf tomorrow!', message)

            else:
                print('Surf conditions for tomorrow do not meet criteria')

        # message if there is no surf (conditions not met)
        else:
            print('There are is no surf tomorrow. Time to take a break and rest up for better waves.')

    else:
        print('Error getting surf forecast:', response.text)


schedule.every().day.at("06:00").do(job)
print("Running surf forecast script...")

while True:
    schedule.run_pending()
    # wait for 1 minute
    time.sleep(60)


