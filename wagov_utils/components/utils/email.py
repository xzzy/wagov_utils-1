import logging
import mimetypes
import hashlib
import datetime
import os

#from confy import env

import six
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, EmailMessage

from django.template import loader, Template
from django.utils.encoding import smart_text
from django.utils.html import strip_tags

# Typing
from typing import Any, Optional, Union

logger = logging.getLogger(__name__)


def _render(template, context):
    if isinstance(context, dict):
        context.update({'settings': settings})
    if isinstance(template, six.string_types):
        template = Template(template)
    return template.render(context)

class TemplateEmailBase(object):
    subject = ''
    html_template = 'wagov_utils/emails/base_email.html'
    # txt_template can be None, in this case a 'tag-stripped' version of the html will be sent. (see send)
    txt_template = 'wagov_utils/emails/base-email.txt'

    def __init__(self, subject='', html_template='', txt_template=''):
        # Update
        self.subject = subject if subject else self.subject
        self.html_template = html_template if html_template else self.html_template
        self.txt_template = txt_template if txt_template else self.txt_template

    def send_to_user(self, user, context=None):
        return self.send(user.email, context=context)


    def send(self, to_addresses, from_address=None, context=None, attachments=None, cc=None, bcc=None):
        """
        Send an email using EmailMultiAlternatives with text and html.
        :param to_addresses: a string or a list of addresses
        :param from_address: if None the settings.DEFAULT_FROM_EMAIL is used
        :param context: a dictionary or a Context object used for rendering the templates.
        :param attachments: a list of (filepath, content, mimetype) triples
               (see https://docs.djangoproject.com/en/1.9/topics/email/)
               or Documents
        :param bcc:
        :param cc:
        :return:
        """
        email_delivery = 'off'

        if hasattr(settings, 'EMAIL_DELIVERY'):        
            email_delivery = settings.EMAIL_DELIVERY
        
        log_hash = int(hashlib.sha1(str(datetime.datetime.now()).encode('utf-8')).hexdigest(), 16) % (10 ** 8)
        email_instance = 'DEV'        
        if hasattr(settings, 'EMAIL_INSTANCE'):  
            email_instance = settings.EMAIL_INSTANCE
        # The next line will throw a TemplateDoesNotExist if html template cannot be found
        html_template = loader.get_template(self.html_template)
        # render html
        html_body = _render(html_template, context)
        if self.txt_template is not None:
            txt_template = loader.get_template(self.txt_template)
            txt_body = _render(txt_template, context)
        else:
            txt_body = strip_tags(html_body)

        email_log(str(log_hash)+' '+self.subject+":"+str(to_addresses)+":"+self.html_template)
        if email_delivery != 'on':
            print ("EMAIL DELIVERY IS OFF NO EMAIL SENT -- email.py ")
            return False

        # build message
        if isinstance(to_addresses, six.string_types):
            to_addresses = [to_addresses]
        if attachments is None:
            attachments = []
        if attachments is not None and not isinstance(attachments, list):
            attachments = list(attachments)

        if attachments is None:
            attachments = []

        # Convert Documents to (filename, content, mime) attachment
        _attachments = []
        for attachment in attachments:
            _attachments.append(attachment)

        msg = EmailMultiAlternatives(self.subject, txt_body, from_email=from_address, to=to_addresses,
                attachments=_attachments, cc=cc, bcc=bcc, 
                headers={'System-Environment': email_instance}
                )
        msg.attach_alternative(html_body, 'text/html')
        try:
            email_log(str(log_hash)+' '+self.subject)
            msg.send(fail_silently=False)          
            email_log(str(log_hash)+' Successfully sent to mail gateway')
            logger.exception("Success sending email to {}".format(to_addresses,))
            return msg
        except Exception as e:
            email_log(str(log_hash)+' Error Sending - '+str(e))
            logger.exception("Error while sending email to {}: {}".format(to_addresses, e))
            return None
        
def email_log(line):
     dt = datetime.datetime.now()
     email_log_path = str(settings.BASE_DIR)+"/logs/email.log"
     if not os.path.exists(str(settings.BASE_DIR)+"/logs"):
         os.makedirs(str(settings.BASE_DIR)+"/logs")
     f= open(email_log_path,"a+")
     f.write(str(dt.strftime('%Y-%m-%d %H:%M:%S'))+': '+line+"\r\n")
     f.close()