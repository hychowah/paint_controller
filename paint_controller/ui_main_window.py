# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QMainWindow, QMenuBar, QSizePolicy,
    QStackedWidget, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1280, 720)
        MainWindow.setStyleSheet(u"background-color: rgb(94, 92, 100);")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.stackedWidget = QStackedWidget(self.centralwidget)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.stackedWidget.setGeometry(QRect(100, 0, 1180, 720))
        self.page_1 = QWidget()
        self.page_1.setObjectName(u"page_1")
        self.page_1.setStyleSheet(u"background-color: rgb(230, 97, 0);")
        self.vispyWidget = QWidget(self.page_1)
        self.vispyWidget.setObjectName(u"vispyWidget")
        self.vispyWidget.setGeometry(QRect(940, 0, 341, 341))
        self.vispy_widget_layout = QVBoxLayout(self.vispyWidget)
        self.vispy_widget_layout.setObjectName(u"vispy_widget_layout")
        self.vispy_widget_layout.setContentsMargins(0, 0, 0, 0)
        self.stackedWidget.addWidget(self.page_1)
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.selectBar = QWidget(self.page_2)
        self.selectBar.setObjectName(u"selectBar")
        self.selectBar.setGeometry(QRect(210, 0, 101, 720))
        self.selectBar.setStyleSheet(u"background-color: rgb(61, 56, 70);")
        self.stackedWidget.addWidget(self.page_2)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1280, 22))
        MainWindow.setMenuBar(self.menubar)

        self.retranslateUi(MainWindow)

        self.stackedWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
    # retranslateUi

