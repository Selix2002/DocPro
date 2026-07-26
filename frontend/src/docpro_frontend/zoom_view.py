from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QPainter, QShortcut
from PySide6.QtWidgets import QFrame, QGraphicsScene, QGraphicsView, QMainWindow, QWidget


class ZoomableView(QGraphicsView):
    """Wraps any widget in a scalable QGraphicsView.

    Ctrl++ / Ctrl+= / Ctrl+Wheel-up  → zoom in
    Ctrl+-  / Ctrl+Wheel-down        → zoom out
    Ctrl+0                           → reset to 100 %
    """

    MIN_SCALE = 0.5
    MAX_SCALE = 2.0
    STEP = 0.1

    def __init__(self, widget: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scale = 1.0

        scene = QGraphicsScene(self)
        self._proxy = scene.addWidget(widget)
        self.setScene(scene)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)

        for keys, slot in [
            ("Ctrl++", self._zoom_in),
            ("Ctrl+=", self._zoom_in),
            ("Ctrl+-", self._zoom_out),
            ("Ctrl+0", self._zoom_reset),
        ]:
            sc = QShortcut(QKeySequence(keys), self)
            sc.setContext(Qt.ShortcutContext.WindowShortcut)
            sc.activated.connect(slot)

    # ── resize ────────────────────────────────────────────────────────

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._resize_proxy()

    def _resize_proxy(self) -> None:
        vp = self.viewport().size()
        w = max(1, round(vp.width() / self._scale))
        h = max(1, round(vp.height() / self._scale))
        self._proxy.widget().resize(w, h)
        self.scene().setSceneRect(self._proxy.boundingRect())

    # ── scale ─────────────────────────────────────────────────────────

    def _set_scale(self, scale: float) -> None:
        self._scale = max(self.MIN_SCALE, min(self.MAX_SCALE, round(scale, 2)))
        self.resetTransform()
        self.scale(self._scale, self._scale)
        self._resize_proxy()
        self._show_zoom_hint()

    def _zoom_in(self) -> None:
        self._set_scale(self._scale + self.STEP)

    def _zoom_out(self) -> None:
        self._set_scale(self._scale - self.STEP)

    def _zoom_reset(self) -> None:
        self._set_scale(1.0)

    def _show_zoom_hint(self) -> None:
        win = self.window()
        if isinstance(win, QMainWindow):
            win.statusBar().showMessage(f"Zoom: {round(self._scale * 100)} %", 1500)

    # ── mouse wheel ───────────────────────────────────────────────────

    def wheelEvent(self, event) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            self._set_scale(self._scale + (self.STEP if delta > 0 else -self.STEP))
            event.accept()
        else:
            super().wheelEvent(event)
