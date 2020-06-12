import sys
import requests
from datetime import datetime
from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

STYLE = """
color: white;
font: 14pt 'DejaVu Sans Mono';
"""

DATA_KEYS = {
	'M': ('Mach', ''), 
	'Vy, m/s': ('Climb', 'm/s'), 
	'RPM 1': ('RPM', ''), 
	'power 1, hp': ('Power', 'HP'), 
	'thrust 1, kgs': ('Thrust', 'KG'), 
	'radiator 1, %': ('Radiat', ''), 
	'compressor stage 1': ('Compre', '')
}

class MyWindow(QWidget):
	def __init__(self):
		super().__init__()
		self.setGeometry(30, 360, 400, 400)
		self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
		self.setWindowFlags(QtCore.Qt.WindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool))
		
		#Set Tray
		self.tray = QSystemTrayIcon()
		self.tray.setIcon(QIcon('icon.png'))
		self.trayMenu = QMenu()
		self.trayMenu.addAction(QAction('Menu Item'))
		self.trayQuit = QAction('Quit')
		self.trayQuit.triggered.connect(app.quit)
		self.trayMenu.addAction(self.trayQuit)
		self.tray.setContextMenu(self.trayMenu)
		
		self.timer = QtCore.QTimer(self)
		self.timer.timeout.connect(self.onTimeOut)
		self.timer.start(1000)
		
		self.labels = []
		for i in range(11):
			label = QLabel('INIT                                        ', self)
			label.move(0, 30*i)
			label.setStyleSheet(STYLE)
			self.labels.append(label)
		
		self.lastAngle = 0.0
		self.lastSpeed = 0
	
	def onTimeOut(self):
		data = self.getData()
		if data:
			i = 0
			for item in data:
				self.labels[i].setText(item)
				i += 1
		else:
			[label.clear() for label in self.labels]
	
	def getData(self):
		try:
			state = requests.get('http://127.0.0.1:8111/state', timeout=0.2).json()
			indicators = requests.get('http://127.0.0.1:8111/indicators', timeout=0.2).json()
		except:
			return False
		
		if 'valid' not in indicators or indicators['valid'] == False or ('type' in indicators and indicators['type'] == 'dummy_plane'):
			return False
		
		refinedData = ['{}\t{} {}'.format(value[0], state[key], value[1]) for key, value in DATA_KEYS.items() if key in state]
		
		if 'TAS, km/h' in state:
			speed = int(state['TAS, km/h'])
			refinedData.append('{}\t{} {}'.format('Accel', speed - self.lastSpeed, 'kph/s'))
			self.lastSpeed = speed
		
		if 'compass' in indicators:
			angle = float(indicators['compass'])
			deltaAngle = abs(angle - self.lastAngle)
			refinedData.append('{}\t{} {}'.format('Turn', '%.2f' % deltaAngle if deltaAngle < 180 else '%.2f' % (360.0 - deltaAngle), ''))
			self.lastAngle = angle
		
		refinedData.append('{}\t{} {}'.format('Time', datetime.now().strftime('%X'), ''))
		
		return refinedData


if __name__ == '__main__':
	app = QApplication(sys.argv)
	w = MyWindow()
	w.show()
	sys.exit(app.exec_())