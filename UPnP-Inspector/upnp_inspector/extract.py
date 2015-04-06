# -*- coding: utf-8 -*-

# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2009 - Frank Scholz <coherence@beebits.net>
# Copyright 2014 - Hartmut Goebel <h.goebel@crazy-compilers.com>

import os
import tempfile

from twisted.internet import defer
from twisted.internet import protocol

from twisted.python.filepath import FilePath

EMAIL_RECIPIENT = 'upnp.fingerprint@googlemail.com'
EMAIL_DOMAIN = EMAIL_RECIPIENT.rsplit('@',1)[1]

try:
    from twisted.mail import smtp

    from twisted.names import client as namesclient
    from twisted.names import dns

    import StringIO


    class SMTPClient(smtp.ESMTPClient):

        """ build an email message and send it to our googlemail account
        """

        def __init__(self, mail_from, mail_to, mail_subject, mail_file,
                     *args, **kwargs):
            smtp.ESMTPClient.__init__(self, *args, **kwargs)
            self.mailFrom = mail_from
            self.mailTo = mail_to
            self.mailSubject = mail_subject
            self.mail_file = mail_file
            self.mail_from = mail_from

        def getMailFrom(self):
            result = self.mailFrom
            self.mailFrom = None
            return result

        def getMailTo(self):
            return [self.mailTo]

        def getMailData(self):
            from email.mime.application import MIMEApplication
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg['Subject'] = self.mailSubject
            msg['From'] = self.mail_from
            msg['To'] = self.mailTo
            with open(self.mail_file, 'rb') as fp:
                tar = MIMEApplication(fp.read(), 'x-tar')
            tar.add_header('Content-Disposition', 'attachment',
                           filename=os.path.basename(self.mail_file))
            msg.attach(tar)
            return StringIO.StringIO(msg.as_string())

        def sentMail(self, code, resp, numOk, addresses, log):
            print 'Sent', numOk, 'messages'


    class SMTPClientFactory(protocol.ClientFactory):
        protocol = SMTPClient

        def __init__(self, mail_from, mail_to, mail_subject, mail_file,
                     *args, **kwargs):
            self.mail_from = mail_from
            self.mail_to = mail_to
            self.mail_subject = mail_subject
            self.mail_file = mail_file

        def buildProtocol(self, addr):
            return self.protocol(self.mail_from, self.mail_to,
                                 self.mail_subject, self.mail_file,
                                 secret=None, identity='localhost')

    has_smtp = True
except ImportError:
    has_smtp = False

from coherence.upnp.core.utils import downloadPage

import pygtk
pygtk.require("2.0")
import gtk


class Extract(object):

    def __init__(self, device):
        self.device = device
        self.window = gtk.Dialog(title="Extracting XMl descriptions",
                            parent=None, flags=0, buttons=None)
        label = gtk.Label("Extracting XMl device and service descriptions\n"
                          "from %s @ %s" % (device.friendly_name, device.host))
        self.window.vbox.pack_start(label, True, True, 10)
        tar_button = gtk.CheckButton("tar.gz them")
        tar_button.connect("toggled", self._toggle_tar)
        self.window.vbox.pack_start(tar_button, True, True, 5)

        if has_smtp:
            self.email_button = gtk.CheckButton("email them to Coherence HQ "
                                                "(%s)" % EMAIL_RECIPIENT)
            self.email_button.set_sensitive(False)
            self.window.vbox.pack_start(self.email_button, True, True, 5)

        align = gtk.Alignment(0.5, 0.5, 0.9, 0)
        self.window.vbox.pack_start(align, False, False, 5)
        self.progressbar = gtk.ProgressBar()
        align.add(self.progressbar)

        button = gtk.Button(stock=gtk.STOCK_CANCEL)
        self.window.action_area.pack_start(button, True, True, 5)
        button.connect("clicked", lambda w: self.window.destroy())

        button = gtk.Button(stock=gtk.STOCK_OK)
        self.window.action_area.pack_start(button, True, True, 5)
        button.connect("clicked",
                       lambda w: self.extract(tar_button.get_active()))
        self.window.show_all()

    def show_result(self, msg):
        msgDialog = gtk.MessageDialog(buttons=gtk.BUTTONS_CLOSE)
        msgDialog.set_markup(msg)
        msgDialog.run()
        msgDialog.destroy()

    def _toggle_tar(self, window):
        if has_smtp:
            self.email_button.set_sensitive(window.get_active())

    def extract(self, make_tar):

        def device_extract(workdevice, workpath):
            tmp_dir = workpath.child(workdevice.get_uuid())
            if tmp_dir.exists():
                tmp_dir.remove()
            tmp_dir.createDirectory()
            target = tmp_dir.child('device-description.xml')
            print "device", target.path
            d = downloadPage(workdevice.get_location(), target.path)
            l.append(d)

            for service in workdevice.services:
                target = tmp_dir.child('%s-description.xml' %
                                       service.service_type.split(':', 3)[3])
                print "service", target.path
                d = downloadPage(service.get_scpd_url(), target.path)
                l.append(d)

            for ed in workdevice.devices:
                device_extract(ed, tmp_dir)
            return tmp_dir

        def finished(result):
            uuid = self.device.get_uuid()
            msg = ("Extraction of device <b>%s</b> finished.\n"
                   "Files have been saved to\n" % self.device.friendly_name)
            outpath = workpath.path
            if make_tar:
                tgz_file = self.create_tgz(workpath)
                outpath = tgz_file
                workpath.remove()
                if has_smtp and self.email_button.get_active():
                    self.send_email(tgz_file)
            self.progressbar.set_fraction(0.0)
            self.window.destroy()
            self.show_result(msg + outpath)

        self.progressbar.pulse()
        try:
            l = []
            workpath = device_extract(self.device,
                                      FilePath(tempfile.gettempdir()))
            dl = defer.DeferredList(l)
            dl.addCallback(finished)
        except Exception, msg:
            print "problem creating download directory:",
            import traceback
            print traceback.format_exc()
            self.progressbar.set_fraction(0.0)

    def create_tgz(self, path):
        import tarfile
        tgz_file = path.path + '.tgz'
        print "creating", tgz_file
        cwd = os.getcwd()
        os.chdir(path.dirname())
        with tarfile.open(tgz_file, "w:gz") as tar:
            tar.add(path.basename(), recursive=True)
        os.chdir(cwd)
        return tgz_file

    def send_email(self, file):

        def got_mx(result):
            mx_list = result[0]
            mx_list.sort(lambda x, y: cmp(x.payload.preference,
                                          y.payload.preference))
            if len(mx_list) > 0:
                import posix
                import pwd
                import socket
                from twisted.internet import reactor
                sender = (pwd.getpwuid(posix.getuid())[0] +
                          '@' + socket.gethostname())
                reactor.connectTCP(str(mx_list[0].payload.name), 25,
                    SMTPClientFactory(sender, EMAIL_RECIPIENT,
                                      'xml-files', file))

        mx = namesclient.lookupMailExchange(EMAIL_DOMAIN)
        mx.addCallback(got_mx)
