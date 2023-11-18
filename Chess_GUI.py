import PyQt6.QtWidgets as PyQt6
import PyQt6.QtGui as PyQt6Gui
import PyQt6.QtCore as PyQt6Core
import sys
import chess
import chess.engine as engine
import logging
from time import sleep
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from traceback import format_tb

"""
This Chess GUI is made by AadithyaSai. All credit for 
the chess engine and GUI development software go to the developers of
stockfish and PyQt6 respectively. Some elements of the Start 
Page were the brainchild of Adarsh K Dileep.

Now that the formalities are done with, ENJOY!!
"""


def errorlog(type_, value, traceback):
    logging.basicConfig(filename='error_logs.log', level=logging.CRITICAL,
                        format='%(asctime)s:%(message)s \n')
    logging.critical(f'{str(type_)} : {str(value)} : {str(format_tb(traceback))}')

    error = PyQt6.QMessageBox()
    error.setText(f'{type_} : {value}')
    error.setIcon(PyQt6.QMessageBox.Icon.Critical)
    error.setWindowTitle('Error')
    error.setDetailedText('\n'.join(format_tb(traceback)) + '\n\nsee error_logs.log for details')
    error.setStandardButtons(PyQt6.QMessageBox.StandardButton.Ok)
    error.exec()

    sys.__excepthook__(type_, value, traceback)


def run_chess(*args):
    Chess(*args)


class Start(PyQt6.QWidget):
    def __init__(self):
        super().__init__()
        self.player_iswhite = True
        self.enemy_iscomp = True

        self.setWindowTitle('Chess')
        self.setWindowIcon(PyQt6Gui.QIcon('assets\\chess_sprites\\icon.ico'))
        self.start_wind()

    # noinspection PyTypeChecker
    def start_wind(self):

        self.setFixedSize(480, 480)
        layout = PyQt6.QVBoxLayout()
        self.setLayout(layout)

        pix = PyQt6Gui.QPixmap('assets\\chess_sprites\\Background_image.png')
        bg = PyQt6.QLabel('', self)
        bg.setPixmap(pix.scaled(480, 480, PyQt6Core.Qt.AspectRatioMode.KeepAspectRatio))
        bg.setFixedSize(480, 480)

        text = PyQt6.QLabel('')
        pix2 = PyQt6Gui.QPixmap('assets\\chess_sprites\\MyLogo.png')
        text.setPixmap(pix2.scaled(400, 200, PyQt6Core.Qt.AspectRatioMode.KeepAspectRatio))
        text.setAlignment(PyQt6Core.Qt.AlignmentFlag.AlignTop | PyQt6Core.Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(text)
        text.show()

        level = PyQt6.QComboBox()

        level.setStyleSheet('font: 20pt; color: White; background-color: rgba(0, 0, 0, 70);')
        level.addItems(['easy', 'medium', 'hard'])
        level.setFixedSize(130, 40)
        level.setMouseTracking(True)
        level.installEventFilter(self)

        b1 = PyQt6.QRadioButton('Player vs Computer', self)
        b2 = PyQt6.QRadioButton('Player vs Player', self)

        b1.setStyleSheet('QRadioButton{font: 20pt; color: White; background-color: rgba(0, 0, 0, 70);}')
        b1.setFixedWidth(300)

        b2.setStyleSheet('QRadioButton{font: 20pt; color: White; background-color: rgba(0, 0, 0, 70);}')
        b2.setFixedWidth(300)

        b1.setChecked(True)
        b2.clicked.connect(lambda: self.ai_check1(self.sender(), level))
        b1.clicked.connect(lambda: self.ai_check2(self.sender(), level))
        b1.setMouseTracking(True)
        b1.installEventFilter(self)
        b2.setMouseTracking(True)
        b2.installEventFilter(self)
        layout.addWidget(b1)
        layout.addWidget(b2)

        color_chooser = PyQt6.QComboBox()
        color_chooser.addItems(['White', 'Black'])
        color_chooser.setStyleSheet('font: 20pt; color: White; background-color: rgba(0,0,0,70);')
        color_chooser.setFixedSize(130, 40)
        color_chooser.setMouseTracking(True)
        color_chooser.installEventFilter(self)
        layout.addWidget(color_chooser)

        layout.addWidget(level)

        btn = PyQt6.QPushButton('Play', self)
        btn.setStyleSheet('font: 30pt; color: White; background: transparent')
        btn.setFixedWidth(80)
        layout.addWidget(btn, alignment=PyQt6Core.Qt.AlignmentFlag.AlignHCenter)

        btn.setMouseTracking(True)
        btn.installEventFilter(self)
        btn.show()

        about = PyQt6.QLabel('Made by AadithyaSai. Design ideas by Adarsh K Dileep\n'
                             'Uses stockfish chess engine. Uses PyQt6 for GUI\n'
                             'Uses python-chess module.')
        about.setStyleSheet('font: 5pt; color: White;')
        layout.addWidget(about, alignment=PyQt6Core.Qt.AlignmentFlag.AlignBottom | PyQt6Core.Qt.AlignmentFlag.AlignRight)

        def data(color, level_, r1, r2):
            color = color.currentText()
            level_ = level_.currentText()

            if r1.isChecked():
                return color, self.enemy_iscomp, level_
            elif r2.isChecked():
                return color, self.enemy_iscomp, None

        btn.clicked.connect(lambda: run_chess(*data(color_chooser, level, b1, b2)))

        self.show()

    def ai_check1(self, sender, lst):
        if sender.isChecked():
            self.enemy_iscomp = False
            lst.setEnabled(False)

    def ai_check2(self, sender, lst):
        if sender.isChecked():
            self.enemy_iscomp = True
            lst.setEnabled(True)

    def eventFilter(self, qobject, qevent):
        if qevent.type() == PyQt6Core.QEvent.Type.HoverEnter:
            shadow = PyQt6.QGraphicsDropShadowEffect()
            shadow.setBlurRadius(15)
            shadow.setColor(PyQt6Gui.QColor(255, 255, 255))
            shadow.setOffset(0)
            qobject.setGraphicsEffect(shadow)
        if qevent.type() == PyQt6Core.QEvent.Type.HoverLeave:
            qobject.setGraphicsEffect(None)

        return super(Start, self).eventFilter(qobject, qevent)


class Chess(PyQt6.QWidget):

    def __init__(self, player, enemy, level):

        super().__init__()

        self.player = player
        self.ai_enemy = enemy
        self.level = level
        self.ongoing = False
        self.old_pos = (0, 0)
        self.board = chess.Board()
        self.board.set_castling_fen('-')
        self.noshell = 0x08000000

        self.stockfish = engine.SimpleEngine.popen_uci(r'stockfish\stockfish-windows-x86-64.exe',
                                                       creationflags=self.noshell)

        if self.level == 'easy':
            self.level = 1

        elif self.level == 'medium':
            self.level = 10

        elif self.level == 'hard':
            self.level = 20
        else:
            self.level = 0

        self.stockfish.configure({'Skill Level': self.level})

        audio_output = QAudioOutput()
        audio_output.setVolume(50)
        self.sounds = QMediaPlayer()
        self.sounds.setAudioOutput(audio_output)
        self.sounds.setSource(PyQt6Core.QUrl.fromLocalFile(r'assets\Sounds\Chess_Piece_Move.wav'))

        self.setMaximumSize(480, 480)

        self.wind()

    def wind(self):

        layout = PyQt6.QGridLayout()
        layout.setSpacing(0)
        self.setLayout(layout)

        layout_pics = PyQt6.QGridLayout()
        layout.setSpacing(0)
        layout.addLayout(layout_pics, 0, 0, 8, 8)

        l_names = [
            'R', 'Kn', 'B', 'Q', 'K', 'B', 'Kn', 'R',
            'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P',
            '', '', '', '', '', '', '', '',
            '', '', '', '', '', '', '', '',
            '', '', '', '', '', '', '', '',
            '', '', '', '', '', '', '', '',
            'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P',
            'R', 'Kn', 'B', 'Q', 'K', 'B', 'Kn', 'R'
        ]

        b_pos = [(x, y) for x in range(8) for y in range(8)]
        b_list = list()

        z = 1
        v = 0
        for pos in b_pos:
            button = PyQt6.QPushButton('')
            button.setFixedSize(60, 60)
            if v % 8 == 0:
                z -= 1
            if z % 2 == 0:
                button.setIcon(PyQt6Gui.QIcon(
                    'assets\\chess_sprites\\Chess_White_sqr.png'
                ))
                z += 1
                v += 1

            else:
                button.setIcon(PyQt6Gui.QIcon(
                    'assets\\chess_sprites\\Chess_Black_sqr.png'
                ))
                z += 1
                v += 1
            b_list.append(button)
            button.setIconSize(PyQt6Core.QSize(57, 57))
            button.setToolTip(f'{pos}')
            layout.addWidget(button, *pos)

        '''board_label = PyQt6.QLabel('')
        board_icon = PyQt6gui.QPixmap('assets\\chess\\board.png')
        board_label.setPixmap(board_icon.scaled(480, 480, PyQt6core.Qt.KeepAspectRatio))
        board_label.setAttribute(PyQt6core.Qt.WA_TransparentForMouseEvents)

        layout.addWidget(board_label, 0, 0, 8, 8)'''

        for pos1, name1 in zip(b_pos[:16], l_names[:16]):
            black = PyQt6.QLabel('')
            black.setFixedSize(60, 60)
            black.setObjectName(f'{name1},black')
            icons = PyQt6Gui.QPixmap(f'assets\\chess_sprites\\black_{name1}.png')
            black.setPixmap(icons.scaled(50, 50, PyQt6Core.Qt.AspectRatioMode.KeepAspectRatio))
            black.setAlignment(PyQt6Core.Qt.AlignmentFlag.AlignCenter)
            black.setAttribute(PyQt6Core.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            layout_pics.addWidget(black, *pos1)

        for i in range(8):
            layout_pics.setColumnStretch(i, 1)
            layout_pics.setRowStretch(i, 1)

        for pos2, name2 in zip(b_pos[48:], l_names[48:]):
            white = PyQt6.QLabel('')
            white.setFixedSize(60, 60)
            white.setObjectName(f'{name2},white')
            icons = PyQt6Gui.QPixmap(f'assets\\chess_sprites\\white_{name2}.png')
            white.setPixmap(icons.scaled(50, 50, PyQt6Core.Qt.AspectRatioMode.KeepAspectRatio))
            white.setAlignment(PyQt6Core.Qt.AlignmentFlag.AlignCenter)
            white.setAttribute(PyQt6Core.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            layout_pics.addWidget(white, *pos2)

        for i in b_list:
            i.clicked.connect(lambda: self.clicked(self.sender(), layout, layout_pics))

        # for player black
        if self.player == 'Black' and self.ai_enemy:
            move = self.stockfish.play(self.board, engine.Limit(time=0.1))
            self.board.push(move.move)
            move = self.board.peek().uci()
            l1, l2 = ((8 - eval(move[1]), ord(move[0]) - 97),
                      (8 - eval(move[3]), ord(move[2]) - 97))

            p1 = layout_pics.itemAtPosition(*l1).widget()

            layout_pics.removeWidget(p1)
            try:
                p2 = layout_pics.itemAtPosition(*l2).widget()
            except AttributeError:
                p2 = None
            if p2:
                p2.hide()
                layout_pics.removeWidget(p2)

            layout_pics.addWidget(p1, *l2)
            self.sounds.play()

        self.setWindowTitle('Chess')
        self.setWindowIcon(PyQt6Gui.QIcon('assets\\chess_sprites\\icon.ico'))
        self.move(300, 50)
        self.show()

    def clicked(self, sender, layout1, layout2):

        if not self.ongoing:

            index = layout1.indexOf(sender)
            pos = layout1.getItemPosition(index)[:2]
            self.old_pos = pos

            try:
                piece = layout2.itemAtPosition(*self.old_pos).widget()
                piece.setStyleSheet('border: 3px solid blue')
                self.ongoing = not self.ongoing
            except AttributeError:
                pass

        else:

            index = layout1.indexOf(sender)
            new_pos = layout1.getItemPosition(index)[:2]
            piece = layout2.itemAtPosition(*self.old_pos).widget()

            if new_pos == self.old_pos:
                self.ongoing = not self.ongoing
                piece.setStyleSheet('')
            else:

                uci_pos = chr(97 + self.old_pos[1]) + str((8 - self.old_pos[0]))
                uci_new_pos = chr(97 + new_pos[1]) + str((8 - new_pos[0]))
                move = chess.Move.from_uci(uci_pos + uci_new_pos)

                if move in self.board.generate_legal_moves():
                    self.board.push_uci(move.uci())

                    try:

                        layout2.removeWidget(piece)
                        try:
                            new_piece = layout2.itemAtPosition(*new_pos).widget()
                        except AttributeError:
                            new_piece = None
                        if new_piece:
                            new_piece.hide()
                            layout2.removeWidget(new_piece)

                        self.sounds.play()
                        layout2.addWidget(piece, *new_pos)
                        PyQt6.QApplication.processEvents()

                        # adding stockfish here
                        if self.ai_enemy:
                            sleep(0.2)
                            opp_move = self.stockfish.play(self.board, engine.Limit(time=0.1 * self.level,
                                                                                    depth=self.level))
                            self.board.push(opp_move.move)
                            last_move = self.board.peek().uci()
                            l1, l2 = ((8 - eval(last_move[1]), ord(last_move[0]) - 97),
                                      (8 - eval(last_move[3]), ord(last_move[2]) - 97))

                            p1 = layout2.itemAtPosition(*l1).widget()

                            layout2.removeWidget(p1)
                            try:
                                p2 = layout2.itemAtPosition(*l2).widget()
                            except AttributeError:
                                p2 = None
                            if p2:
                                p2.hide()
                                layout2.removeWidget(p2)

                            layout2.addWidget(p1, *l2)

                            self.sounds.play()

                        PyQt6.QApplication.processEvents()

                        piece.setFixedSize(60, 60)

                    except AttributeError:
                        pass
                    finally:
                        if self.board.is_check():
                            self.setStyleSheet('border: 3px solid red')
                        else:
                            self.setStyleSheet('')

                        if self.board.is_game_over():
                            self.setStyleSheet('border: 3px solid blue')
                            PyQt6.QApplication.processEvents()
                            sleep(2)
                            msg = PyQt6.QMessageBox()
                            msg.setWindowTitle('results')
                            msg.setWindowIcon(PyQt6Gui.QIcon('assets\\chess_sprites\\icon.ico'))
                            msg.setStandardButtons(PyQt6.QMessageBox.StandardButton.Ok)
                            if self.board.result()[0] == 1:
                                msg.setText('White Wins, GAME OVER')
                            else:
                                msg.setText('Black Wins, GAME OVER')

                            # noinspection PyUnresolvedReferences
                            msg.buttonClicked.connect(self.closeEvent)
                            msg.exec()

                    self.ongoing = not self.ongoing
                    PyQt6.QApplication.processEvents()
                    piece.setStyleSheet('')

    def closeEvent(self, event):

        self.stockfish.close()
        self.board.clear()
        self.close()


def main():
    sys.excepthook = errorlog
    app = PyQt6.QApplication(sys.argv)
    # noinspection PyUnusedLocal
    application = Start()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
