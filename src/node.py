from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtGui import QBrush, QPen, QColor, QFont
from PyQt5.QtCore import QRectF, Qt, QPointF

class NodeItem(QGraphicsItem):
    WIDTH = 180
    HEIGHT = 100

    def __init__(self, title="Node", inputs=None, outputs=None, description=""):
        super().__init__()
        self.title = title
        self.inputs = inputs if inputs is not None else []
        self.outputs = outputs if outputs is not None else []
        self.description = description
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.input_pins = []
        self.output_pins = []
        self.output_connections = []
        self.input_connections = []

    def boundingRect(self):
        return QRectF(0, 0, self.WIDTH, self.HEIGHT)

    def paint(self, painter, option, widget):
        # Corpo do node
        rect = self.boundingRect()
        painter.setBrush(QBrush(QColor(220, 220, 235)))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawRoundedRect(rect, 8, 8)

        # Título
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.setPen(Qt.black)
        painter.drawText(10, 25, self.title)

        # Inputs (círculos à esquerda)
        self.input_pins = []
        painter.setFont(QFont("Arial", 9))
        for i, inp in enumerate(self.inputs):
            y = 45 + i*18
            pin_center = QPointF(8, y - 4)
            self.input_pins.append(pin_center)
            # Círculo azul
            painter.setBrush(QColor(30, 100, 180))
            painter.setPen(Qt.black)
            painter.drawEllipse(pin_center, 6, 6)
            # Nome
            painter.setPen(QColor(30, 100, 180))
            painter.setBrush(Qt.NoBrush)
            painter.drawText(20, y, inp)

        # Outputs (círculos à direita)
        self.output_pins = []
        for i, out in enumerate(self.outputs):
            y = 45 + i*18
            pin_center = QPointF(self.WIDTH - 8, y - 4)
            self.output_pins.append(pin_center)
            # Círculo laranja
            painter.setBrush(QColor(180, 100, 30))
            painter.setPen(Qt.black)
            painter.drawEllipse(pin_center, 6, 6)
            # Nome
            painter.setPen(QColor(180, 100, 30))
            painter.setBrush(Qt.NoBrush)
            painter.drawText(self.WIDTH - 70, y, out)

        # Descrição (opcional, pequena)
        if self.description:
            painter.setPen(Qt.darkGray)
            painter.setFont(QFont("Arial", 8))
            painter.drawText(10, self.HEIGHT - 10, self.description)
    def add_output_connection(self, conn):
        self.output_connections.append(conn)

    def add_input_connection(self, conn):
        self.input_connections.append(conn)

    def remove_output_connection(self, conn):
        if conn in self.output_connections:
            self.output_connections.remove(conn)

    def remove_input_connection(self, conn):
        if conn in self.input_connections:
            self.input_connections.remove(conn)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            for conn in self.output_connections + self.input_connections:
                conn.update_path()
        return super().itemChange(change, value)

    def get_input_pin_scene_pos(self, idx):
        if 0 <= idx < len(self.input_pins):
            return self.mapToScene(self.input_pins[idx])
        # Fallback: retorna centro do node se pino não existir
        return self.mapToScene(QPointF(self.WIDTH/2, self.HEIGHT/2))

    def get_output_pin_scene_pos(self, idx):
        if 0 <= idx < len(self.output_pins):
            return self.mapToScene(self.output_pins[idx])
        # Fallback: retorna centro do node se pino não existir
        return self.mapToScene(QPointF(self.WIDTH/2, self.HEIGHT/2))

    def hit_test_pin(self, pos, pin_type="output"):
        # pos: posição local ao node (QPointF)
        pins = self.output_pins if pin_type == "output" else self.input_pins
        for idx, pin_center in enumerate(pins):
            # Aumenta o raio de detecção para facilitar o clique
            if (pin_center - pos).manhattanLength() <= 16:
                return idx
        return None