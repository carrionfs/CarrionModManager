# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QCheckBox, QLabel

from qfluentwidgets import (
    PushButton, PrimaryPushButton, ToolButton,
    BodyLabel, CheckBox, TitleLabel, TableWidget,
    HyperlinkLabel, InfoBar, setTheme, SubtitleLabel,
    MessageBoxBase, Theme, FluentIcon,
    InfoBarPosition, LineEdit
)

# =========================
# mainwindow的UI
# =========================

class moddata_ui(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(805, 655)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)

        # 顶层 splitter
        self.splitter_5 = QtWidgets.QSplitter(self.centralwidget)
        self.splitter_5.setOrientation(QtCore.Qt.Vertical)

        self.profile = TitleLabel(self.splitter_5)

        self.profileWidget = QtWidgets.QWidget(self.splitter_5)
        self.profileLayout = QtWidgets.QVBoxLayout(self.profileWidget)
        self.profileLayout.setContentsMargins(0, 30, 0, 0)
        self.profileLayout.addWidget(self.profile)
        from qfluentwidgets import IndeterminateProgressBar

        # ===== 添加进度条（默认隐藏） =====
        self.progressBar = IndeterminateProgressBar(self.profileWidget)
        self.progressBar.setFixedHeight(4)
        self.progressBar.setVisible(False)
        self.profileLayout.addWidget(self.progressBar)

        self.splitter_4 = QtWidgets.QSplitter(self.splitter_5)
        self.splitter_4.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_4.setStretchFactor(0, 1)
        self.splitter_4.setStretchFactor(1, 0)

        # 左侧
        self.widget = QtWidgets.QWidget(self.splitter_4)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.widget)
        self.splitter_2 = QtWidgets.QSplitter(self.widget)
        self.splitter_2.setOrientation(QtCore.Qt.Vertical)
        self.horizontalLayout_4.addWidget(self.splitter_2)

        self.searchWidget = QtWidgets.QWidget(self.splitter_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.searchWidget)

        self.opengamefolder = PushButton(self.searchWidget)
        self.openxnbcil = PushButton(self.searchWidget)
        self.searchline = LineEdit(self.searchWidget)
        self.Refreshbutton = ToolButton(self.searchWidget)

        self.horizontalLayout_3.addWidget(self.opengamefolder)
        self.horizontalLayout_3.addWidget(self.openxnbcil)
        self.horizontalLayout_3.addWidget(self.searchline)
        self.horizontalLayout_3.addWidget(self.Refreshbutton)

        self.tableView = TableWidget(self.splitter_2)

        # ================= 右侧详情区（关键修改） =================
        self.widget_2 = QtWidgets.QWidget(self.splitter_4)
        self.widget_2.setFixedWidth(300)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget_2)
        self.verticalLayout.setContentsMargins(8, 8, 8, 8)
        self.verticalLayout.setSpacing(6)

        # 图片
        self.image = QLabel(self.widget_2)
        self.image.setFixedSize(300, 200)
        self.image.setAlignment(QtCore.Qt.AlignCenter)
        self.image.setStyleSheet("""
            QLabel {
                background-color: rgba(0,0,0,20);
                border-radius: 10px;
            }
        """)
        self.verticalLayout.addWidget(self.image)

        # 名称
        self.name = BodyLabel(self.widget_2)
        self.verticalLayout.addWidget(self.name)

        # 链接
        self.link = HyperlinkLabel(self.widget_2)
        self.verticalLayout.addWidget(self.link)

        # 描述
        self.discription = BodyLabel(self.widget_2)
        self.discription.setWordWrap(True)
        self.verticalLayout.addWidget(self.discription)

        # 把多余空间压到下面
        self.verticalLayout.addStretch()

        # 底部
        self.widget_3 = QtWidgets.QWidget(self.splitter_5)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.widget_3)

        self.splitter = QtWidgets.QSplitter(self.widget_3)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalLayout_5.addWidget(self.splitter)

        self.buttonGroup = QtWidgets.QWidget(self.splitter)
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.buttonGroup)

        self.allactandbanned = PushButton(self.buttonGroup)
        self.allrenew = PushButton(self.buttonGroup)
        self.import_2 = PushButton(self.buttonGroup)
        self.openprofilefolder = PushButton(self.buttonGroup)
        self.opengame = PrimaryPushButton(self.buttonGroup)

        for btn in (
            self.allactandbanned, self.allrenew, self.import_2,
            self.openprofilefolder, self.opengame
        ):
            self.horizontalLayout.addWidget(btn)

        self.gridLayout.addWidget(self.splitter_5, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))

        self.profile.setText(_translate("MainWindow", "配置1"))
        self.opengamefolder.setText(_translate("MainWindow", "打开游戏路径"))
        self.openxnbcil.setText(_translate("MainWindow", "打开Xnbcil路径"))
        self.Refreshbutton.setText(_translate("MainWindow", ""))

        self.image.setText(_translate("MainWindow", "图片"))
        self.name.setText(_translate("MainWindow", "名称："))
        self.link.setText(_translate("MainWindow", "网址尾号："))
        self.discription.setText(_translate("MainWindow", "Mod描述："))

        self.allactandbanned.setText(_translate("MainWindow", "一键启用/禁用"))
        self.allrenew.setText(_translate("MainWindow", "一键更新"))
        self.import_2.setText(_translate("MainWindow", "导入Mod"))
        self.openprofilefolder.setText(_translate("MainWindow", "打开配置目录"))
        self.opengame.setText(_translate("MainWindow", "启动游戏"))





    def CreateErrorInforBar_Noprofileos(self):
        InfoBar.error(
            title='路径错误❌',
            content="当前路径不存在",
            orient=QtCore.Qt.Horizontal,  # 内容太长时可使用垂直布局
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )

    def CreateErrorInforBar_Flieloads(self):
        InfoBar.error(
            title='路径错误❌',
            content="未找到当前路径",
            orient=QtCore.Qt.Horizontal,  # 内容太长时可使用垂直布局
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )

    def CreateErrorInforBar_Flienotexist(self):
        InfoBar.error(
            title='路径错误❌',
            content="当前路径不存在",
            orient=QtCore.Qt.Horizontal,  # 内容太长时可使用垂直布局
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )

    def CreateErrorInforBar_Gamenotexist(self):
        InfoBar.error(
            title='路径错误❌',
            content="游戏路径不存在",
            orient=QtCore.Qt.Horizontal,  # 内容太长时可使用垂直布局
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )

    def CreateErrorInforBar_Gameloads(self):
        InfoBar.error(
            title='路径错误❌',
            content="未找到游戏路径",
            orient=QtCore.Qt.Horizontal,  # 内容太长时可使用垂直布局
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )

    def CreateSuccessInforBar_renameProfile(self):
        InfoBar.success(
            title='名称已修改√',
            content="配置名称修改成功,重启管理器可生效",
            orient=QtCore.Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )
        # self.IndeterminateProgressBar.show()


