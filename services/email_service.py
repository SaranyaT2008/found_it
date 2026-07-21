import logging
from flask_mail import Message
from extensions import mail

logger = logging.getLogger(__name__)


def send_match_notification(item, candidate, config):
    if not config.get('MAIL_USERNAME') or not config.get('MAIL_PASSWORD'):
        logger.warning('Mail credentials are not configured; match notification not sent.')
        return False

    subject = 'Lost & Found Match Notification'
    body = (
        f'Hi {item.author.name},\n\n'
        f'We found a potential match between your report "{item.title}" and a report by {candidate.author.name}.\n'
        f'Please contact them at {candidate.author.email} to coordinate pickup or return.\n\n'
        'Thank you for keeping the campus community safe.\n'
        'Lost & Found Team'
    )

    try:
        message = Message(
            subject=subject,
            recipients=[item.author.email],
            body=body,
            sender=config.get('MAIL_DEFAULT_SENDER')
        )
        mail.send(message)
        logger.info('Match notification sent to %s', item.author.email)
    except Exception:
        logger.exception('Failed to send match notification email to %s', item.author.email)
        return False

    return True
