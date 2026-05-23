from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QWidget, QLabel,
    QLineEdit, QPushButton, QDateEdit, QGridLayout,
)
from PySide6.QtCore import Signal, Qt, QDate

from docpro_frontend.report.styles import report_styles as S


class TrabajoSection(QFrame):
    """
    Fixed section (no drag/delete): Local, Fecha, Tipo de equipo + dynamic extra fields.
    """

    field_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SectionBlock")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(S.section_block())

        self._extra_rows: list[dict] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_head())

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 16, 20, 20)
        body_layout.setSpacing(14)

        # Fixed fields
        grid = QGridLayout()
        grid.setSpacing(14)

        self._local_input = QLineEdit()
        self._local_input.setPlaceholderText("Nombre del local / establecimiento")
        self._local_input.setStyleSheet(S.field_input())

        local_container = self._wrap_field("LOCAL", self._local_input)
        grid.addWidget(local_container, 0, 0)

        self._fecha = QDateEdit()
        self._fecha.setDate(QDate.currentDate())
        self._fecha.setCalendarPopup(True)
        self._fecha.setDisplayFormat("dd/MM/yyyy")
        self._fecha.setStyleSheet(S.date_edit())

        fecha_container = self._wrap_label_widget("FECHA", self._fecha)
        grid.addWidget(fecha_container, 0, 1)

        self._equipment_input = QLineEdit()
        self._equipment_input.setPlaceholderText("Modelo, marca, número de serie…")
        self._equipment_input.setStyleSheet(S.field_input())

        equip_container = self._wrap_field("TIPO DE EQUIPO", self._equipment_input)
        grid.addWidget(equip_container, 1, 0, 1, 2)

        body_layout.addLayout(grid)

        # Extra fields container
        self._extra_container = QWidget()
        self._extra_layout = QVBoxLayout(self._extra_container)
        self._extra_layout.setContentsMargins(0, 0, 0, 0)
        self._extra_layout.setSpacing(8)
        body_layout.addWidget(self._extra_container)

        # Add field button
        add_btn = QPushButton("+ Agregar campo")
        add_btn.setStyleSheet(S.add_sub_btn())
        add_btn.clicked.connect(lambda: self._add_extra_row())
        body_layout.addWidget(add_btn)

        root.addWidget(body)

        self._local_input.textEdited.connect(lambda _: self.field_changed.emit())
        self._fecha.dateChanged.connect(lambda _: self.field_changed.emit())
        self._equipment_input.textEdited.connect(lambda _: self.field_changed.emit())

    # ── Public ────────────────────────────────────────────────────────────────

    def get_data(self) -> dict:
        return {
            "local":          self._local_input.text().strip(),
            "fecha":          self._fecha.date().toString("yyyy-MM-dd"),
            "equipment_type": self._equipment_input.text().strip(),
            "extra_fields": [
                {"label": r["label"].text().strip(), "value": r["value"].text().strip()}
                for r in self._extra_rows
            ],
        }

    def set_data(self, data: dict) -> None:
        self._local_input.setText(data.get("local", ""))
        fecha_str = data.get("fecha", "")
        if fecha_str:
            try:
                y, m, d = fecha_str.split("-")
                self._fecha.setDate(QDate(int(y), int(m), int(d)))
            except (ValueError, AttributeError):
                pass
        self._equipment_input.setText(data.get("equipment_type", ""))
        for extra in data.get("extra_fields", []):
            self._add_extra_row(extra.get("label", "Campo"), extra.get("value", ""))

    def reset(self) -> None:
        self._local_input.clear()
        self._fecha.setDate(QDate.currentDate())
        self._equipment_input.clear()
        for row in list(self._extra_rows):
            row["widget"].deleteLater()
        self._extra_rows.clear()

    def set_readonly(self, readonly: bool) -> None:
        self._local_input.setReadOnly(readonly)
        self._fecha.setEnabled(not readonly)
        self._equipment_input.setReadOnly(readonly)
        for r in self._extra_rows:
            r["label"].setReadOnly(readonly)
            r["value"].setReadOnly(readonly)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _build_head(self) -> QWidget:
        head = QWidget()
        head.setObjectName("SectionHead")
        head.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        head.setStyleSheet(S.section_head())
        head.setFixedHeight(46)

        h = QHBoxLayout(head)
        h.setContentsMargins(20, 0, 20, 0)

        icon = QLabel("🔧")
        icon.setStyleSheet(S.section_head_icon())

        label = QLabel("Trabajo efectuado")
        label.setStyleSheet(S.section_head_label())

        h.addWidget(icon)
        h.addSpacing(8)
        h.addWidget(label)
        h.addStretch()
        return head

    @staticmethod
    def _wrap_field(label_text: str, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        lbl = QLabel(label_text)
        lbl.setStyleSheet(S.field_label())
        layout.addWidget(lbl)
        layout.addWidget(widget)
        return container

    @staticmethod
    def _wrap_label_widget(label_text: str, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        lbl = QLabel(label_text)
        lbl.setStyleSheet(S.field_label())
        layout.addWidget(lbl)
        layout.addWidget(widget)
        return container

    def _add_extra_row(self, label: str = "Campo", value: str = "") -> None:
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        label_edit = QLineEdit(label)
        label_edit.setPlaceholderText("Etiqueta")
        label_edit.setStyleSheet(S.field_input())
        label_edit.setFixedWidth(150)

        value_edit = QLineEdit(value)
        value_edit.setPlaceholderText("Valor")
        value_edit.setStyleSheet(S.field_input())

        del_btn = QPushButton("✕")
        del_btn.setStyleSheet(S.btn_section_delete())
        del_btn.setFixedSize(34, 34)

        row_layout.addWidget(label_edit)
        row_layout.addWidget(value_edit, 1)
        row_layout.addWidget(del_btn)

        row_data = {"widget": row_widget, "label": label_edit, "value": value_edit}
        del_btn.clicked.connect(lambda: self._remove_extra_row(row_data))
        label_edit.textEdited.connect(lambda _: self.field_changed.emit())
        value_edit.textEdited.connect(lambda _: self.field_changed.emit())

        self._extra_layout.addWidget(row_widget)
        self._extra_rows.append(row_data)
        self.field_changed.emit()

    def _remove_extra_row(self, row_data: dict) -> None:
        self._extra_rows.remove(row_data)
        row_data["widget"].deleteLater()
        self.field_changed.emit()
