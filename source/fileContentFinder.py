# -*- coding: utf-8 -*-
import os
import re
import sys
import time

from PyQt4.QtCore import *
from PyQt4.QtGui import *

QTextCodec.setCodecForTr(QTextCodec.codecForName("utf8"))


class Lookthread(QThread):
    def __init__(self, parent=None):
        super(Lookthread, self).__init__(parent)
        self.dir = ''
        self.keyText = ''
        self.pattern = 0
        self.isstop = 0

    def setdir(self, dir):
        self.dir = dir

    def setkey(self, key):
        self.keyText = key

    def setpattern(self, pattern):
        self.pattern = pattern

    def run(self):
        self.isstop = 0
        self.lookfile(self.dir)

    def stop(self):
        self.isstop = 1

    def lookfile(self, dir):
        for root, dirs, files in os.walk(dir):
            for filespath in files:
                filename = os.path.join(root, filespath)
                size = os.path.getsize(filename)
                if self.isstop:
                    return
                if size < 5242880L:
                    words = self.looksmallfile(filename, self.keyText)
                else:
                    words = self.lookbigfile(filename, self.keyText)
                if words:
                    for w in words:
                        self.emit(SIGNAL("insertrows"), root, filespath, w)

                self.emit(SIGNAL("updateProcess()"))
                time.sleep(0.001)

    def looksmallfile(self, filename, key):
        p = re.compile(r'.{0,10}' + key + r'.{0,10}', self.pattern)
        q = open(filename, 'rt').read()
        try:
            file = q.decode('gbk').encode('utf-8')
        except:
            file = q
        return p.findall(file)

    def lookbigfile(self, filename, key):
        match = []
        p = re.compile(r'.{0,10}' + key + r'.{0,10}', self.pattern)
        with open(filename, 'rt') as handle:
            for ln in handle:
                try:
                    file = ln.decode('gbk').encode('utf-8')
                except:
                    file = ln
                match.extend(p.findall(file))
        return match


class FindFile(QWidget):
    def __init__(self, parent=None):
        super(FindFile, self).__init__(parent)

        self.setWindowTitle(self.tr('文件内容查看器v1.0'))
        self.resize(700, 400)
        icon = QIcon()
        icon.addPixmap(QPixmap("index.ico"),QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)

        self.findpos = QLineEdit("")
        self.findpos.setFocusPolicy(Qt.NoFocus)

        self.detail = QLineEdit("")
        self.detail.setFocusPolicy(Qt.NoFocus)

        self.keyword = QLineEdit("")
        self.progressBar = QProgressBar()
        self.Ignorecase = QRadioButton(self.tr('忽略大小写'))

        self.posText = ""
        self.keyText = ""
        self.resCount = 0
        self.processCount = 0
        self.pattern = 0
        self.newthread = None

        posbutton = QPushButton(self.tr("选择路径"))
        keybutton = QPushButton(self.tr("开始查找"))
        detailText = QLabel(self.tr('详细信息:'))
        noteText = QLabel(self.tr('一个可以查找在文件夹里的文件内容的软件~\n'
                                  '点击表格后可以显现详细的信息~\n'
                                  '编码成exe后发现运行很慢..感谢吐槽'))

        hlayout = QGridLayout()
        hlayout.addWidget(self.findpos, 0, 0, 1, 2)
        hlayout.addWidget(posbutton, 0, 2)
        hlayout.addWidget(self.keyword, 1, 0, 1, 2)
        hlayout.addWidget(keybutton, 1, 2)
        hlayout.addWidget(detailText, 2, 0)
        hlayout.addWidget(self.detail, 2, 1)
        hlayout.addWidget(self.Ignorecase, 2, 2)

        vlayout = QVBoxLayout()
        vlayout.addLayout(hlayout)
        vlayout.addWidget(self.progressBar)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels([u'文件位置', u'文件', u'附近文字'])
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        # self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        vlayout.addWidget(self.table)
        vlayout.addWidget(noteText)

        self.connect(posbutton, SIGNAL("clicked()"), self.slotPos)
        self.connect(keybutton, SIGNAL("clicked()"), self.slotKeyword)
        self.connect(self.Ignorecase, SIGNAL("clicked()"), self.triggercase)
        self.connect(self.table, SIGNAL("itemClicked (QTableWidgetItem*)"), self.outSelect)

        self.setLayout(vlayout)

        # self.setTabOrder(keybutton,self.keyword)
        # self.setTabOrder(self.keyword,posbutton)

    def slotPos(self):
        path = QFileDialog.getExistingDirectory(self, 'Open file', '/home')
        if path != '':
            self.findpos.setText(self.tr(unicode(path).encode("utf-8")))
            self.posText = unicode(path).encode("utf-8")

    def slotKeyword(self):
        self.table.clearContents()
        self.table.setRowCount(0)
        self.resCount = 0
        self.processCount = 1
        self.keyText = unicode(self.keyword.text()).encode("utf-8")

        if self.keyText == '':
            QMessageBox.information(self, "warning",
                                    self.tr("填写查找词!"))
        elif self.posText == '':
            QMessageBox.information(self, "warning",
                                    self.tr("选择个路径呀!"))
        else:
            num = self.filecount(self.posText.decode('utf-8'))
            self.progressBar.setMinimum(0)
            if num != 0:
                self.progressBar.setMaximum(num)
            else:
                self.progressBar.setMaximum(1)

            # child thread
            if self.newthread:
                self.newthread.terminate()
                time.sleep(0.5)
            self.newthread = Lookthread()
            self.newthread.setdir(self.posText.decode('utf-8'))
            self.newthread.setkey(self.keyText)
            self.newthread.setpattern(self.pattern)
            self.connect(self.newthread, SIGNAL("updateProcess()"), self.updateProcess)
            self.connect(self.newthread, SIGNAL("insertrows"), self.insertrows)
            self.newthread.start()
        print "over"

    def insertrows(self, res1, res2, res3):
        self.table.insertRow(self.resCount)
        self.table.setItem(self.resCount, 0, QTableWidgetItem(res1))
        self.table.setItem(self.resCount, 1, QTableWidgetItem(res2))
        self.table.setItem(self.resCount, 2, QTableWidgetItem(self.tr(res3)))
        self.resCount += 1

    def filecount(self, dir):
        length = 0
        for root, dirs, files in os.walk(dir):
            length += len(files)
        return length

    def updateProcess(self):
        self.progressBar.setValue(self.processCount)
        self.processCount += 1

    def outSelect(self, Item):
        if Item == None:
            return
        self.detail.setText(Item.text())

    def triggercase(self):
        self.pattern ^= 2
        print self.pattern


def Appmain():
    app = QApplication(sys.argv)
    progess = FindFile()
    progess.show()
    app.exec_()


if __name__ == '__main__':
    Appmain()
