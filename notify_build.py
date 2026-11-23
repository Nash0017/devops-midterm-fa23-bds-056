"""Send the lab notification using the smtp-gmail Jenkins credential."""
import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

def main():
    sender = 'nashama123asim@gmail.com'
    if os.environ['SMTP_USER'].strip().lower() != sender:
        raise ValueError('SMTP credential username must match the submitted sender')
    message = EmailMessage()
    message['From'] = sender
    message['To'] = 'qasimalik@gmail.com'
    message['Cc'] = sender
    message['Subject'] = f"FA23-BDS-056 Jenkins {os.environ.get('BUILD_RESULT', 'UNKNOWN')} build {os.environ.get('BUILD_NUMBER', 'local')}"
    message.set_content('\n'.join([
        'Student: Nashama Asim', 'Registration: FA23-BDS-056',
        'Result: ' + os.environ.get('BUILD_RESULT', 'UNKNOWN'),
        'Git commit: ' + os.environ.get('GIT_COMMIT', 'unknown'),
        'Metrics: ' + os.environ.get('METRICS_URL', 'http://16.192.221.29:8000/metrics'),
        'Build: ' + os.environ.get('BUILD_URL', 'unknown'),
    ]))
    metrics = Path('artifacts/metrics.json')
    if metrics.exists():
        report = json.loads(metrics.read_text())
        message.set_content(message.get_content() + '\nTraining metrics:\n' + json.dumps(report, indent=2))
        message.add_attachment(metrics.read_bytes(), maintype='application', subtype='json', filename='metrics.json')
    verification = Path('artifacts/verification.json')
    if verification.exists():
        message.add_attachment(verification.read_bytes(), maintype='application', subtype='json', filename='verification.json')
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=30, context=ssl.create_default_context()) as smtp:
        smtp.login(sender, os.environ['SMTP_PASSWORD'].replace(' ', ''))
        refused = smtp.send_message(message)
        if refused:
            raise RuntimeError('SMTP did not accept all recipients')
    print('Build email accepted by Gmail SMTP for qasimalik@gmail.com with student copied')

if __name__ == '__main__':
    main()
