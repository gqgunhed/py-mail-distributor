#!/usr/bin/env python
# encoding: utf-8

"""mail to forward emails to resk-verteiler"""

import sys
import smtplib
import email
import re
from email.message import Message
from email.mime.multipart import MIMEMultipart


INSTPATH = '/home/py_forwarder/'
FROM = 'info@example.com'               # hide original sender
TO = FROM                               # should be identical to "From"
BCC = []                                # list to hold all recipients as Bcc
VERBOSE = False                         # for debugging
MAIL = 'smtp.example.com'               # outgoing smtp-server
OLDMAIL = Message()                     # prepare an email.message-object
NEWMAIL = Message()                     # prepare an email.message-object
AUTHFILE = INSTPATH + 'authorized.txt'           # allowed to relay emails
LISTFILE = INSTPATH + 'distribute.txt'           # complete list of email-addresses
#LISTFILE = INSTPATH + 'distribute-test.txt'      # TESTING and DEBUGGING !!!

# this uses the second field in "distribute.txt" as we use mapped email-addresses within
# our organization. So this is to switch between two sets of email-addresses for the
# same list of recipients
USE_SECONDARY = True                    # use mapped email-addresses instead of original


def authorized_senders():
    """loads list of authorized senders
    @return senders: list of authorized email-addresses
    """
    senders = addresses_from_file(AUTHFILE)
    return senders


def select_email_address(line, use_secondary=False):
    """select the first or second email-address from a ;-separated line

    :line:          string of email-addresses, separated by ";"
    :use_secondary: use the first or second email-address from the line?
    :returns:       a single email-address

    """
    if not ";" in line:
        # only a single email-address here
        return line
    else:
        fields = line.split(";")
        if use_secondary and len(fields) > 1:
            return fields[1]
        else:
            return fields[0]


def strip_comments(line):
    """remove the in-line comments after some text, starting at first '#'

    :line:      string with optional comment starting with '#'
    :returns:   string of line without the comment, and .strip()ed

    """
    if '#' in line:
        regex = re.compile("(.*?)#")
        r = regex.search(line)
        if r.groups():
            return r.groups()[0].strip()
    else:
        # no comment sign found in current line
        # so just return the whole stuff
        return line.strip()


def addresses_from_file(filename):
    """read email-addresses from given file

    ignore all lines starting with '#'

    @returns: list of all email-addresses
    """
    #       1st: original email-address
    #       2nd: mapped email-address
    addlist = []
    try:
        with open(filename, 'r') as f:
            complist = f.readlines()    # store all lines
    except IOError:
        print('Error: unable to read: %s') % filename
        sys.exit(1)
    for line in complist:
        # go through the single lines
        line = line.strip()    # remove all whitespaces
        if not line.startswith('#'):
            line = strip_comments(line)
            # add to the new list
            em = select_email_address(line, USE_SECONDARY)
            em = em.lower()     # all lowercase please
            addlist.append(em)
    return addlist


def sender_is_authorized():
    """checks if the sender of the original email is allowed to relay
    @return boolean: if sender is allowed to use this relay
    """
    sender = OLDMAIL.get('From').lower()
    # maybe some more restrictive 'cleaning' of the
    # found email-address needed, e.g.
    # - removing given name around <...@..>
    if '<' in sender:
        #regex = re.compile(".*?<(.*)>")
        regex = re.compile(".*?<([^>]+)>", re.IGNORECASE|re.DOTALL)
        r = regex.search(sender)
        if r:
            #sender = r.groups()[0]
            sender = r.group(1)
    if sender in authorized_senders():
        return True
    else:
        print 'Error: %s not allowed to send in' % sender
        return False


def transfer_email_headers(headerlist):
    """transfers named email-header-filed from original to new email
    @param headerlist: list of email header-fields
    """
    for field in headerlist:
        if field in OLDMAIL:
            # found desired field in existing email
            # so transferring it to new email-headers
            if VERBOSE:
                print 'transferring %s' % field
            insert_newemail_key(field, OLDMAIL.get(field))
        else:
            print 'error: %s was not found in the email-headers' % field


def transfer_email_payload():
    """transfers email.Message.payload from OLDMAIL to NEWMAIL"""
    if OLDMAIL.is_multipart():
        # Multipart Message = list of Message.objects
        for part in OLDMAIL.get_payload():
            print "transferring %s" % (part.get_content_type(),)
            NEWMAIL.attach(part)
    else:
        # single-part payload = string
        oldp = OLDMAIL.get_payload()
        NEWMAIL.set_payload(oldp)


def insert_newemail_key(key, value):
    """inserts key and value into email-headers
    @param key:     name of header-field
    @param value:   value to be set there
    """
    if isinstance(value, list):
        value = ', '.join(value)
    if key in NEWMAIL:
        NEWMAIL.replace_header(key, value)
    else:
        NEWMAIL.add_header(key, value)


def my_as_string(msg):
    """transform email.Message as shown on
        http://docs.python.org/2/library/email.message.html#email.message.Message
    """
    from cStringIO import StringIO
    from email.generator import Generator
    fp = StringIO()
    g = Generator(fp, mangle_from_=False, maxheaderlen=60)
    g.flatten(msg)
    text = fp.getvalue()
    return text


def send_email_tls():
    """send email via SMTP-server
    """
    #USER=""     # only needed with smtp.login()
    #PASS=""     # only needed with smtp.login()
    recipients = [TO] + generate_distributor()
    print('debug: recipients: %s') % recipients
    #smtp = smtplib.SMTP(MAIL, '587')    # SSL
    smtp = smtplib.SMTP(MAIL, '25')     # stanard/TLS
    try:
        if VERBOSE:
            smtp.set_debuglevel(1)
        smtp.ehlo()
        if smtp.has_extn('STARTTLS'):
            smtp.starttls()
            smtp.ehlo()
            #smtp.login(USER, PASS)
        smtp.sendmail(FROM, recipients, NEWMAIL.as_string())
        #smtp.sendmail(FROM, recipients, my_as_string(NEWMAIL))
    finally:
        smtp.quit()


def generate_distributor():
    """generate a list of email-recipients
    @returns:   list to hold all recipients
    """
    distlist = []
    distlist = addresses_from_file(LISTFILE)
    #distlist = ['me@example.com']    # for testing only
    return distlist


def main():
    if sender_is_authorized():
        # preprare new, empty email.Message
        if OLDMAIL.is_multipart():
            NEWMAIL = MIMEMultipart()
        else:
            NEWMAIL = Message()
        insert_newemail_key('From', FROM)
        insert_newemail_key('To', FROM)
        # transfer information from original email
        # If you transfer the "Date" field from the original email and you use an interval
        # for fetchmail to collect email, you will get Spam-points from SpamAssassin if
        # the email messages is "too old".
        transfer_email_headers(['Content-Encoding', 'MIME-Version', 'Content-Type', 'Subject'])
        transfer_email_payload()
        if VERBOSE:
            # some ugly STDOUT output
            print 'Email Message'
            print 30 * '-'
            print NEWMAIL.as_string()
            #print my_as_string(NEWMAIL)
            print 30 * '-'
        send_email_tls()
    else:
        print 'sender is not authorized to relay'
        sys.exit(1)


if __name__ == '__main__':
    # read email from STDIN
    OLDMAIL = email.message_from_string(sys.stdin.read())       # get email from STDIN and store it
    main()
