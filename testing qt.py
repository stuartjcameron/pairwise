# -*- coding: utf-8 -*-
"""
Created on Mon Dec 04 18:52:47 2017

@author: Stuart
"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget

if __name__ == '__main__':
    
    app = QApplication(sys.argv)

    w = QWidget()
    w.resize(250, 150)
    w.move(300, 300)
    w.setWindowTitle('Simple')
    w.show()
    
    sys.exit(app.exec_())