from qtsymbols import *
import windows, NativeUtils, gobject
from myutils.config import globalconfig
from gui.dynalang import LAction
from traceback import print_exc


# <<< 新增辅助函数：计算虚拟桌面的总几何区域 >>>
def get_virtual_desktop_geometry():
    """
    计算并返回包含所有显示器的虚拟桌面的总 QRect。
    这对于在多显示器环境中正确定位和缩放窗口至关重要。
    """
    desktop_rect = QRect()
    for screen in QApplication.screens():
        desktop_rect = desktop_rect.united(screen.geometry())
    return desktop_rect


class SideGrip(QWidget):
    def __init__(self, parent, edge):
        QWidget.__init__(self, parent)
        if edge == Qt.Edge.LeftEdge:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            self.resizeFunc = self.resizeLeft
        elif edge == Qt.Edge.TopEdge:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
            self.resizeFunc = self.resizeTop
        elif edge == Qt.Edge.RightEdge:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            self.resizeFunc = self.resizeRight
        else:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
            self.resizeFunc = self.resizeBottom
        self.mousePos = None

    def resizeLeft(self, delta):
        window = self.window()
        width = max(window.minimumWidth(), window.width() - delta.x())
        geo = window.geometry()
        geo.setLeft(geo.right() - width)
        window.setGeometry(geo)

    def resizeTop(self, delta):
        window = self.window()
        height = max(window.minimumHeight(), window.height() - delta.y())
        geo = window.geometry()
        geo.setTop(geo.bottom() - height)
        window.setGeometry(geo)

    def resizeRight(self, delta):
        window = self.window()
        width = max(window.minimumWidth(), window.width() + delta.x())
        window.resize(width, window.height())

    def resizeBottom(self, delta):
        window = self.window()
        height = max(window.minimumHeight(), window.height() + delta.y())
        window.resize(window.width(), height)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mousePos = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.mousePos is not None:
            delta = event.pos() - self.mousePos
            self.resizeFunc(delta)

    def mouseReleaseEvent(self, _):
        self.mousePos = None


class Mainw(QMainWindow):
    _gripSize = 8

    def __init__(self, x):
        QMainWindow.__init__(self, x)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | self.windowFlags())

        self.sideGrips = [
            SideGrip(self, Qt.Edge.LeftEdge),
            SideGrip(self, Qt.Edge.TopEdge),
            SideGrip(self, Qt.Edge.RightEdge),
            SideGrip(self, Qt.Edge.BottomEdge),
        ]
        self.cornerGrips = [QSizeGrip(self) for i in range(4)]
        for s in self.cornerGrips:
            s.setStyleSheet("background-color: transparent;")

    @property
    def gripSize(self):
        return self._gripSize

    def setGripSize(self, size):
        if size == self._gripSize:
            return
        self._gripSize = max(2, size)
        self.updateGrips()

    def updateGrips(self):
        self.setContentsMargins(*[self.gripSize] * 4)

        outRect = self.rect()
        inRect = outRect.adjusted(
            self.gripSize, self.gripSize, -self.gripSize, -self.gripSize
        )

        self.cornerGrips[0].setGeometry(QRect(outRect.topLeft(), inRect.topLeft()))
        self.cornerGrips[1].setGeometry(
            QRect(outRect.topRight(), inRect.topRight()).normalized()
        )
        self.cornerGrips[2].setGeometry(
            QRect(inRect.bottomRight(), outRect.bottomRight())
        )
        self.cornerGrips[3].setGeometry(
            QRect(outRect.bottomLeft(), inRect.bottomLeft()).normalized()
        )

        self.sideGrips[0].setGeometry(0, inRect.top(), self.gripSize, inRect.height())
        self.sideGrips[1].setGeometry(inRect.left(), 0, inRect.width(), self.gripSize)
        self.sideGrips[2].setGeometry(
            inRect.left() + inRect.width(), inRect.top(), self.gripSize, inRect.height()
        )
        self.sideGrips[3].setGeometry(
            self.gripSize, inRect.top() + inRect.height(), inRect.width(), self.gripSize
        )

    def resizeEvent(self, event):
        QMainWindow.resizeEvent(self, event)
        self.updateGrips()


class rangeadjust(Mainw):
    closesignal = pyqtSignal()
    traceoffsetsignal = pyqtSignal(QPoint)

    def starttrace(self, pos):
        self.tracepos = self.geometry().topLeft()
        self.traceposstart = pos

    def traceoffset(self, curr: QPoint):
        hwnd = gobject.base.hwnd
        if not hwnd:
            self.tracepos = QPoint()
            return
        if windows.MonitorFromWindow(hwnd) != windows.MonitorFromWindow(
            int(self.winId())
        ):
            self.tracepos = QPoint()
            return
        keystate = windows.GetKeyState(windows.VK_LBUTTON)
        if keystate < 0 and windows.GetForegroundWindow() == int(self.winId()):
            self.tracepos = QPoint()
            return
        if self._isTracking:
            self.tracepos = QPoint()
            return
        _geo = self.geometry()
        if self.tracepos.isNull():
            self.tracepos = _geo.topLeft()
            self.traceposstart = curr
        target = self.tracepos + (curr - self.traceposstart) * self.devicePixelRatioF()
        self.setGeometry(
            target.x(),
            target.y(),
            _geo.width(),
            _geo.height(),
        )

    def rect(self):
        geo = self.geometry()
        return QRectF(
            0,
            0,
            geo.width() / self.devicePixelRatioF(),
            geo.height() / self.devicePixelRatioF(),
        ).toRect()

    def __init__(self, parent):
        super(rangeadjust, self).__init__(parent)
        self.traceoffsetsignal.connect(self.traceoffset)
        self.label = QLabel(self)
        self.setstyle()
        self.closesignal.connect(self.close)
        self.tracepos = QPoint()
        self.drag_label = QLabel(self)
        self.drag_label.setGeometry(0, 0, 4000, 2000)
        self._isTracking = False
        self._rect = None
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showmenu)
        for s in self.cornerGrips:
            s.raise_()

    def showmenu(self, _):
        menu = QMenu(self)
        close = LAction("关闭", menu)
        mousetransp = LAction("鼠标穿透窗口", menu)
        menu.addAction(mousetransp)
        menu.addAction(close)
        action = menu.exec(QCursor.pos())
        if action == mousetransp:
            windows.SetWindowLong(
                int(self.winId()),
                windows.GWL_EXSTYLE,
                windows.GetWindowLong(int(self.winId()), windows.GWL_EXSTYLE)
                | windows.WS_EX_TRANSPARENT,
            )
        elif action == close:
            self._rect = None
            self.close()

    def setstyle(self):
        self.label.setStyleSheet(
            " border:%spx solid %s; background-color: rgba(0,0,0, %s); border-radius:0;"
            % (globalconfig["ocrrangewidth"], globalconfig["ocrrangecolor"], 1 / 255)
        )

    def mouseMoveEvent(self, e: QMouseEvent):
        if self._isTracking:
            self._endPos = e.pos() - self._startPos
            _geo = self.geometry()
            _geo.translate(self._endPos)
            self.setGeometry(*_geo.getRect())

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self._isTracking = True
            self._startPos = QPoint(e.pos().x(), e.pos().y())

    def mouseReleaseEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self._isTracking = False
            self._startPos = None
            self._endPos = None

    def rectoffset(self, rect: QRect):
        r = self.devicePixelRatioF()
        r = int(globalconfig["ocrrangewidth"] * r)
        _ = [(rect.left() + r, rect.top() + r), (rect.right() - r, rect.bottom() - r)]
        return _

    def setGeometry(self, x, y, w, h):
        windows.MoveWindow(int(self.winId()), x, y, w, h, True)

    def geometry(self):
        rect = windows.GetWindowRect(int(self.winId()))
        return QRect(rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1])

    def moveEvent(self, _):
        if self._rect:
            self._rect = self.rectoffset(self.geometry())

    def enterEvent(self, _):
        self.drag_label.setStyleSheet("background-color:rgba(0,0,0, 0.1)")

    def leaveEvent(self, _):
        self.drag_label.setStyleSheet("background-color:none")

    def resizeEvent(self, a0):

        self.label.setGeometry(0, 0, self.width(), self.height())
        if self._rect:
            self._rect = self.rectoffset(self.geometry())
        super(rangeadjust, self).resizeEvent(a0)

    def getrect(self):
        return self._rect

    def setrect(self, rect):
        self.tracepos = QPoint()
        if rect:
            (x1, y1), (x2, y2) = rect
            self.show()
            r = self.devicePixelRatioF()
            self.setGeometry(
                x1 - int(globalconfig["ocrrangewidth"] * r),
                y1 - int(globalconfig["ocrrangewidth"] * r),
                x2 - x1 + int(2 * globalconfig["ocrrangewidth"] * r),
                y2 - y1 + int(2 * globalconfig["ocrrangewidth"] * r),
            )
        self._rect = rect


screen_shot_ui = None


class rangeselect(QMainWindow):

    def closeEvent(self, a0):
        global screen_shot_ui
        screen_shot_ui = None
        self.deleteLater()
        windows.SetForegroundWindow(self.originhwnd)
        return super().closeEvent(a0)

    def __init__(self, parent=None):

        super(rangeselect, self).__init__(parent)
        self.is_drawing = False
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.backlabel = QLabel(self)
        self.rectlabel = QLabel(self)
        self.backlabel.move(0, 0)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.reset()

    def reset(self):
        # <<< MODIFIED: 使用辅助函数来正确设置全屏几何 >>>
        self.setGeometry(get_virtual_desktop_geometry())
        self.once = True
        self.is_drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.__start = None
        self.__end = None
        self.rectlabel.resize(0, 0)
        self.rectlabel.setStyleSheet(
            " border:%spx solid %s; background-color: rgba(0,0,0, 0)"
            % (globalconfig["ocrrangewidth"], globalconfig["ocrrangecolor"])
        )
        self.backlabel.setStyleSheet(
            "background-color: rgba(255,255,255, %s)" % globalconfig["ocrselectalpha"]
        )

    def resizeEvent(self, e: QResizeEvent):
        self.backlabel.resize(e.size())

    def paintEvent(self, _):

        if self.is_drawing:

            pp = QPainter(self)
            pen = QPen(QColor(globalconfig["ocrrangecolor"]))
            pen.setWidth(globalconfig["ocrrangewidth"])
            pp.setPen(pen)
            _x1 = self.start_point.x()
            _y1 = self.start_point.y()
            _x2 = self.end_point.x()
            _y2 = self.end_point.y()
            _sp = QPoint(
                min(_x1, _x2) - globalconfig["ocrrangewidth"],
                min(_y1, _y2) - globalconfig["ocrrangewidth"],
            )
            _ep = QPoint(
                max(_x1, _x2) + globalconfig["ocrrangewidth"],
                max(_y1, _y2) + globalconfig["ocrrangewidth"],
            )
            self.rectlabel.setGeometry(QRect(_sp, _ep))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.end_point = self.start_point = event.pos()
            self.is_drawing = True
            # <<< MODIFIED: 使用 event.globalPosition() 获取绝对屏幕坐标 >>>
            self.__start = self.__end = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):

        if not self.is_drawing:
            self.is_drawing = True
            self.end_point = self.start_point = event.pos()
            self.__start = self.__end = event.globalPosition().toPoint()
        else:
            self.end_point = event.pos()
            self.__end = event.globalPosition().toPoint()
            self.update()

    def getRange(self):
        if self.__start is None:
            self.__start = self.__end
        x1, y1, x2, y2 = (
            self.__start.x(),
            self.__start.y(),
            self.__end.x(),
            self.__end.y(),
        )

        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)

        return ((x1, y1), (x2, y2))

    def callbackfunction(self, event: QMouseEvent):
        if not self.once:
            return
        self.once = False
        self.end_point = event.pos()
        # <<< MODIFIED: 使用 event.globalPosition() 确保坐标正确 >>>
        self.__end = event.globalPosition().toPoint()
        self.close()
        try:
            self.callback(self.getRange())
        except:
            print_exc()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.callbackfunction(event)
        elif event.button() == Qt.MouseButton.RightButton:
            self.once = False
            self.close()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        return super().keyPressEvent(event)


class rangeselect_1(QMainWindow):
    def __init__(self, p, xx):

        self.is_drawing = False
        super(rangeselect_1, self).__init__(p)
        self.xx = xx
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.backlabel = QLabel(self)
        self.backlabel.move(0, 0)
        self.backlabel2 = QLabel(self)
        self.backlabel2.move(0, 0)
        self.rectlabel = QLabel(self)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def reset(self):
        # <<< MODIFIED: 使用辅助函数来正确设置全屏几何 >>>
        total_geometry = get_virtual_desktop_geometry()
        self.setGeometry(total_geometry)

        # <<< MODIFIED: 从整个虚拟桌面截图，而非仅主屏幕 >>>
        if self.xx:
            # grabWindow(0, ...)中的0代表整个桌面
            screenshot = QApplication.primaryScreen().grabWindow(
                0,
                total_geometry.x(),
                total_geometry.y(),
                total_geometry.width(),
                total_geometry.height(),
            )
            self.screenshot = screenshot
            self.backlabel.setPixmap(screenshot)
        self.once = True
        self.is_drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.rectlabel.resize(0, 0)
        self.rectlabel.setStyleSheet(
            " border:%spx solid %s; background-color: rgba(0,0,0, 0)"
            % (globalconfig["ocrrangewidth"], globalconfig["ocrrangecolor"])
        )
        self.backlabel2.setStyleSheet(
            "background-color: rgba(255,255,255, %s)" % globalconfig["ocrselectalpha"]
        )

    def resizeEvent(self, e: QResizeEvent):
        self.backlabel.resize(e.size())
        self.backlabel2.resize(e.size())

    def paintEvent(self, _):

        if self.is_drawing:

            pp = QPainter(self)
            pen = QPen(QColor(globalconfig["ocrrangecolor"]))
            pen.setWidth(globalconfig["ocrrangewidth"])
            pp.setPen(pen)
            _x1 = self.start_point.x()
            _y1 = self.start_point.y()
            _x2 = self.end_point.x()
            _y2 = self.end_point.y()
            _sp = QPoint(
                min(_x1, _x2) - globalconfig["ocrrangewidth"],
                min(_y1, _y2) - globalconfig["ocrrangewidth"],
            )
            _ep = QPoint(
                max(_x1, _x2) + globalconfig["ocrrangewidth"],
                max(_y1, _y2) + globalconfig["ocrrangewidth"],
            )
            self.rectlabel.setGeometry(QRect(_sp, _ep))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.end_point = self.start_point = event.pos()
            self.is_drawing = True

    def mouseMoveEvent(self, event: QMouseEvent):

        if not self.is_drawing:
            self.is_drawing = True
            self.end_point = self.start_point = event.pos()
        else:
            self.end_point = event.pos()
            self.update()

    def getRange(self):
        # <<< MODIFIED: 坐标转换需要考虑窗口的左上角位置 >>>
        window_origin = self.geometry().topLeft()

        # 鼠标位置是相对于窗口的，需要加上窗口的原点坐标得到屏幕绝对坐标
        start_abs = self.start_point + window_origin
        end_abs = self.end_point + window_origin

        # 应用设备像素比
        dpr = self.devicePixelRatioF()
        x1, y1, x2, y2 = (
            start_abs.x() * dpr,
            start_abs.y() * dpr,
            end_abs.x() * dpr,
            end_abs.y() * dpr,
        )
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)

        return ((int(x1), int(y1)), (int(x2), int(y2)))

    def callbackfunction(self, event: QMouseEvent):
        if not self.once:
            return
        self.once = False
        self.end_point = event.pos()
        self.close()
        try:
            (x1, y1), (x2, y2) = self.getRange()
            img = None
            if self.xx and (x1 != x2 and y1 != y2):
                img = self.screenshot.copy(
                    QRect(QPoint(x1, y1), QPoint(x2, y2))
                ).toImage()
            self.callback(self.getRange(), img)
        except:
            print_exc()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.callbackfunction(event)
        elif event.button() == Qt.MouseButton.RightButton:
            self.once = False
            self.close()

    def closeEvent(self, a0):
        global screen_shot_ui
        screen_shot_ui = None
        self.deleteLater()
        windows.SetForegroundWindow(self.originhwnd)
        return super().closeEvent(a0)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        return super().keyPressEvent(event)


def rangeselct_function(callback, x=True):
    global screen_shot_ui
    if screen_shot_ui:
        screen_shot_ui.close()
    p = gobject.base.translation_ui
    if not p.isVisible():
        p = None
    if (len(QApplication.screens()) == 1) or globalconfig[
        "range_select_multi_dpi_capture_force"
    ]:
        screen_shot_ui = rangeselect_1(p, x)
    else:
        screen_shot_ui = rangeselect(p)
    screen_shot_ui.originhwnd = windows.GetForegroundWindow()
    screen_shot_ui.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
    screen_shot_ui.show()
    screen_shot_ui.reset()
    screen_shot_ui.callback = callback
    windows.SetFocus(int(screen_shot_ui.winId()))
    windows.SetForegroundWindow(int(screen_shot_ui.winId()))
