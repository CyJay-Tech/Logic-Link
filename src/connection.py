from PyQt5.QtWidgets import QGraphicsPathItem
from PyQt5.QtGui import QPainterPath, QPen, QColor
from PyQt5.QtCore import QPointF
from PyQt5.QtCore import Qt

class ConnectionItem(QGraphicsPathItem):
    def __init__(self, node_from, idx_from, node_to=None, idx_to=None):
        super().__init__()
        self.node_from = node_from
        self.idx_from = idx_from
        self.node_to = node_to
        self.idx_to = idx_to
        self.temp_end_pos = None  # Para arraste dinâmico
        self.setZValue(-1)
        self.setPen(QPen(QColor(50, 50, 200), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        self.update_path()

    def set_end_pos(self, pos):
        self.temp_end_pos = pos
        self.update_path()

    def set_target(self, node_to, idx_to):
        self.node_to = node_to
        self.idx_to = idx_to
        self.update_path()

    def update_path(self):
        if self.node_from and self.idx_from is not None:
            start_pos = self.node_from.get_output_pin_scene_pos(self.idx_from)
        else:
            start_pos = QPointF(0, 0)
        if self.node_to and self.idx_to is not None:
            end_pos = self.node_to.get_input_pin_scene_pos(self.idx_to)
        elif self.temp_end_pos is not None:
            end_pos = self.temp_end_pos
        else:
            end_pos = start_pos
        path = QPainterPath(start_pos)
        dx = (end_pos.x() - start_pos.x()) * 0.5
        c1 = start_pos + QPointF(dx, 0)
        c2 = end_pos - QPointF(dx, 0)
        path.cubicTo(c1, c2, end_pos)
        self.setPath(path)