Mail Forwarder
==============

Python script to help distribute our internal email newsletter to a list of recipients with the following features:

* Read inomcing email from STDIN (e.g. through procmail)
* Check against list (file-based) of authorized senders
* Create a new/empty email from scratch
* Transfer only given headers from original email
* Send email to mailing-list origin
* Hide all other recipients (list is file-based) in BCC
* Works with text/plain and MIMEMultipart messages (keeps attachments)

See mail_forwarder.rst for more information about the script like TODOs, etc.

Mail Dumper
===========

Dumps data from STDIN into file. Helpful to catch some incoming emails and use these to test/tune the forwarder-script.
