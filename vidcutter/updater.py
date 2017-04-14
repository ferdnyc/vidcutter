#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#######################################################################
#
# VidCutter - a simple yet fast & accurate video cutter & joiner
#
# copyright © 2017 Pete Alexandrou
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#######################################################################

import logging
import os
import sys
from pkg_resources import parse_version

from PyQt5.QtCore import QJsonDocument, QUrl, Qt
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt5.QtWidgets import (qApp, QDialog, QDialogButtonBox, QLabel, QProgressDialog, QStyleFactory, QVBoxLayout,
                             QWidget)


class Updater(QWidget):
    def __init__(self, parent=None, f=Qt.WindowCloseButtonHint):
        super(Updater, self).__init__(parent, f)
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self.api_github_latest = QUrl('https://api.github.com/repos/ozmartian/vidcutter/releases/latest')
        self.manager = QNetworkAccessManager(self)
        self.manager.finished.connect(self.done)

    def get(self, url: QUrl) -> None:
        if url.isValid():
            self.manager.get(QNetworkRequest(url))

    def done(self, reply: QNetworkReply) -> None:
        if reply.error() != QNetworkReply.NoError:
            self.logger.error(reply.errorString())
            return
        if os.getenv('DEBUG', False):
            self.log_request(reply)
        jsondoc = QJsonDocument.fromJson(reply.readAll())
        reply.deleteLater()
        jsonobj = jsondoc.object()
        latest = parse_version(jsonobj.get('tag_name').toString())
        current = parse_version(qApp.applicationVersion())
        self.mbox.show_result(latest, current)

    def check(self) -> None:
        self.mbox = UpdaterMsgBox(self, theme=self.parent.theme)
        self.get(self.api_github_latest)

    def log_request(self, reply: QNetworkReply) -> None:
        self.logger.info('request made at %s' %
                         reply.header(QNetworkRequest.LastModifiedHeader).toString('dd-MM-yyyy hh:mm:ss'))
        self.logger.info('response: %s (%i)  type: %s' %
                         (reply.attribute(QNetworkRequest.HttpReasonPhraseAttribute).upper(),
                          reply.attribute(QNetworkRequest.HttpStatusCodeAttribute),
                          reply.header(QNetworkRequest.ContentTypeHeader)))


class UpdaterMsgBox(QDialog):
    def __init__(self, parent=None, theme: str='light', title: str='Checking updates...', f=Qt.WindowCloseButtonHint):
        super(UpdaterMsgBox, self).__init__(parent, f)
        self.parent = parent
        self.theme = theme
        self.setWindowTitle(title)
        self.setObjectName('updaterdialog')
        self.loading = QProgressDialog('contacting server', None, 0, 0, self.parent, Qt.FramelessWindowHint)
        self.loading.setStyle(QStyleFactory.create('Fusion'))
        self.loading.setStyleSheet('QProgressDialog { border: 1px solid %s; }'
                                   % '#FFF' if self.theme == 'dark' else '#666')
        self.loading.setWindowTitle(title)
        self.loading.setMinimumWidth(485)
        self.loading.setWindowModality(Qt.ApplicationModal)
        self.loading.show()

    def releases_page(self):
        QDesktopServices.openUrl(self.releases_url)

    def show_result(self, latest: str, current: str):
        self.releases_url = QUrl('https://github.com/ozmartian/vidcutter/releases/latest')
        update_available = True if latest > current else False

        pencolor1 = '#C681D5' if self.theme == 'dark' else '#642C68'
        pencolor2 = '#FFF' if self.theme == 'dark' else '#222'
        content = '''<style>
                        h1 {
                            text-align: center;
                            color: %s;
                            font-family: 'Futura LT', sans-serif;
                            font-weight: 400;
                        }
                        div {
                            border: 1px solid #999;
                            color: %s;
                        }
                        p {
                            color: %s;
                            font-size: 15px;
                        }
                        b { color: %s; }
                    </style>''' % (pencolor1, pencolor2, pencolor2, pencolor1)

        if update_available:
            content += '<h1>A new version is available!</h1>'
        else:
            content += '<h1>You are already running the latest version</h1>'

        content += '''
            <p align="center">
                <b>latest version:</b> %s
                <br/>
                <b>installed version:</b> %s
            </p>''' % (str(latest), str(current))

        if update_available and sys.platform.startswith('linux'):
            content += '''<div style="font-size: 12px; padding: 2px 10px; margin:10px 5px;">
                Linux users should always install via their distribution's package manager.
                Packages in formats such as TAR.XZ (Arch Linux), DEB (Ubuntu/Debian) and RPM (Fedora, openSUSE) are
                always produced with every official version released. These can be installed via distribution specific
                channels such as the Arch Linux AUR, Ubuntu LaunchPad PPA, Fedora copr, openSUSE OBS and third party
                repositories.
                <br/><br/>
                Alternatively, you should try the AppImage version available to download for those unable to
                get newer updated versions to work. An AppImage should always be available with  produced for every
                update released.
            </div>
            <p align="center">
                Would you like to visit the <b>VidCutter releases page</b> for more details now?
            </p>'''

        if update_available:
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(self.releases_page)
            buttons.rejected.connect(lambda: self.close())
        else:
            buttons = QDialogButtonBox(QDialogButtonBox.Ok)
            buttons.accepted.connect(lambda: self.close())

        contentLabel = QLabel(content, self.parent, wordWrap=True, textFormat=Qt.RichText)

        layout = QVBoxLayout()
        layout.addWidget(contentLabel)
        layout.addWidget(buttons)

        self.loading.cancel()

        self.setLayout(layout)
        self.setMinimumWidth(600)
        self.show()