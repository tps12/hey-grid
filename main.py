from sys import argv, exit
from PySide.QtGui import QApplication, QFont, QFontDatabase, QFontMetrics
from mainwindow import MainWindow

app = QApplication(argv)
font = QFont(QFontDatabase.applicationFontFamilies(QFontDatabase.addApplicationFont('FreeMono.otf'))[0])
font.setPointSize(14)
QApplication.setFont(font)
w = MainWindow()
metrics = QFontMetrics(font)
w.resize(metrics.width('M') * 80, metrics.height() * 24)
w.show()
exit(app.exec_())
