from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal

from docpro_frontend.body.widgets.recent_card import RecentCard

class RecentDocumentsSection(QWidget):
    document_opened = Signal(int, str)  # doc_id, doc_type

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("DOCUMENTOS RECIENTES")
        title.setStyleSheet(
            "font-size: 15px; font-weight: 600; letter-spacing: 1px; color: #374151;"
        )
        layout.addWidget(title)
        layout.addSpacing(15)

        self._cards_layout = QVBoxLayout()
        self._cards_layout.setSpacing(12)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self._cards_layout)

        self.set_documents([])

    def set_documents(self, documents: list[dict]) -> None:
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for doc in documents:
            card = RecentCard(
                doc_type=doc["doc_type"],
                title=doc["title"],
                subtitle=doc["subtitle"],
                status=doc["status"],
                document_id=doc["document_id"],
            )
            card.clicked.connect(self.document_opened)
            self._cards_layout.addWidget(card)
