import os

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileName, FileType, FileContent, Disposition, ContentId
import base64

from config import *


def send_email(message: str, subject, png=None):

    message = message.replace("\n", "<br>")
    html = f'''
        <html>
            <body style="font-family: monospace">
                {message}
                <img src="cid:price_graph"/>
            </body>
        </html>
    '''

    message = Mail(
        from_email=EMAIL_SENDER,
        to_emails=EMAIL_RECIPIENTS,
        subject=subject,
        html_content=html)

    if png is not None:
        encoded_file = base64.b64encode(png).decode()
        attached_file = Attachment(
            FileContent(encoded_file),
            FileName('price_graph.png'),
            FileType('image/png'),
            Disposition('inline'),
            ContentId('price_graph')
        )
        message.attachment = attached_file

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)