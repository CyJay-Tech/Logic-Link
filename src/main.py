import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QVBoxLayout, QWidget, QMenu,
    QDockWidget, QLineEdit, QTextEdit, QListWidget, QListWidgetItem, QPushButton, QLabel, QHBoxLayout, QScrollArea
)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QWheelEvent, QPainter
from .node import NodeItem
from .connection import ConnectionItem

class WorkspaceView(QGraphicsView):
    def __init__(self, scene, main_window=None):
        super().__init__(scene)
        self._main_window = main_window
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)
        self._pan = False
        self._pan_start = QPoint()
        self._zoom = 1.0
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)
        self._scene_ref = scene  # para adicionar nodes

        # Estado para conexões
        self._dragging_connection = None
        self._drag_start_node = None
        self._drag_start_idx = None

    def wheelEvent(self, event: QWheelEvent):
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self._zoom *= zoom_factor
        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        item = self.itemAt(event.pos())
        if event.button() == Qt.LeftButton and isinstance(item, NodeItem):
            # Verifica se clicou em pino de output
            node_pos = item.mapFromScene(scene_pos)
            out_idx = item.hit_test_pin(node_pos, "output")
            if out_idx is not None:
                # Inicia arraste de conexão
                pin_pos = item.get_output_pin_scene_pos(out_idx)
                self._dragging_connection = ConnectionItem(item, out_idx)
                self._scene_ref.addItem(self._dragging_connection)
                item.add_output_connection(self._dragging_connection)
                self._drag_start_node = item
                self._drag_start_idx = out_idx
                return
        if event.button() == Qt.MiddleButton:
            self._pan = True
            self._pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._pan:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
        elif self._dragging_connection:
            scene_pos = self.mapToScene(event.pos())
            self._dragging_connection.set_end_pos(scene_pos)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        item = self.itemAt(event.pos())
        if self._dragging_connection:
            # Verifica se soltou sobre pino de input de outro node
            if isinstance(item, NodeItem) and item != self._drag_start_node:
                node_pos = item.mapFromScene(scene_pos)
                in_idx = item.hit_test_pin(node_pos, "input")
                if in_idx is not None:
                    # Finaliza conexão
                    end_pos = item.get_input_pin_scene_pos(in_idx)
                    self._dragging_connection.set_target(item, in_idx)
                    item.add_input_connection(self._dragging_connection)
                    self._dragging_connection = None
                    self._drag_start_node = None
                    self._drag_start_idx = None
                    super().mouseReleaseEvent(event)
                    return
            # Se não conectou, remove a conexão temporária
            self._scene_ref.removeItem(self._dragging_connection)
            self._dragging_connection = None
            self._drag_start_node = None
            self._drag_start_idx = None
        elif event.button() == Qt.MiddleButton and self._pan:
            self._pan = False
            self.setCursor(Qt.ArrowCursor)
            super().mouseReleaseEvent(event)
        else:
            super().mouseReleaseEvent(event)

    def open_context_menu(self, pos):
        menu = QMenu()
        # Submenu de modos
        mode_menu = menu.addMenu("Modo de Operação")
        actions = []
        for mode in self._main_window.MODES:
            act = mode_menu.addAction(mode)
            act.setCheckable(True)
            act.setChecked(mode == self._main_window.current_mode)
            actions.append(act)
        menu.addSeparator()
        action_add_node = menu.addAction("Novo Node")
        action = menu.exec_(self.mapToGlobal(pos))
        if action in actions:
            self._main_window.current_mode = action.text()
        elif action == action_add_node:
            scene_pos = self.mapToScene(pos)
            self._main_window.create_node_by_mode(scene_pos)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.MODES = ["Diagrama de Classes", "Fluxograma"]
        self.current_mode = self.MODES[0]
        self.setWindowTitle("Editor de Lógica Visual")
        self.setGeometry(100, 100, 1200, 800)

        # Área de trabalho (WorkspaceView)
        self.scene = QGraphicsScene()
        self.view = WorkspaceView(self.scene, main_window=self)

        # Menu principal
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Arquivo")
        action_save = file_menu.addAction("Salvar Projeto")
        action_load = file_menu.addAction("Carregar Projeto")
        action_save.triggered.connect(self.save_project)
        action_load.triggered.connect(self.load_project)

        # Layout central
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.view)
        self.setCentralWidget(central_widget)

        # Painel de propriedades (dock)
        self.dock = QDockWidget("Propriedades do Node", self)
        self.dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.prop_widget = QWidget()
        # Campos de edição
        self.title_edit = QLineEdit()
        self.inputs_list = QListWidget()
        self.inputs_list.setEditTriggers(QListWidget.DoubleClicked | QListWidget.SelectedClicked | QListWidget.EditKeyPressed)
        self.outputs_list = QListWidget()
        self.outputs_list.setEditTriggers(QListWidget.DoubleClicked | QListWidget.SelectedClicked | QListWidget.EditKeyPressed)
        self.desc_edit = QTextEdit()
        self.inputs_add_btn = QPushButton("Adicionar Entrada")
        self.inputs_del_btn = QPushButton("Remover Entrada")
        self.outputs_add_btn = QPushButton("Adicionar Saída")
        self.outputs_del_btn = QPushButton("Remover Saída")

        # Novos widgets para propriedades e métodos
        self.properties_list = QListWidget()
        self.properties_list.setEditTriggers(QListWidget.DoubleClicked | QListWidget.SelectedClicked | QListWidget.EditKeyPressed)
        self.properties_add_btn = QPushButton("Adicionar Propriedade")
        self.properties_del_btn = QPushButton("Remover Propriedade")

        self.methods_list = QListWidget()
        self.methods_list.setEditTriggers(QListWidget.DoubleClicked | QListWidget.SelectedClicked | QListWidget.EditKeyPressed)
        self.methods_add_btn = QPushButton("Adicionar Método")
        self.methods_del_btn = QPushButton("Remover Método")

        prop_layout = QVBoxLayout(self.prop_widget)
        prop_layout.addWidget(QLabel("Título:"))
        prop_layout.addWidget(self.title_edit)
        prop_layout.addWidget(QLabel("Entradas:"))
        prop_layout.addWidget(self.inputs_list)
        prop_layout.addWidget(self.inputs_add_btn)
        prop_layout.addWidget(self.inputs_del_btn)
        prop_layout.addWidget(QLabel("Saídas:"))
        prop_layout.addWidget(self.outputs_list)
        prop_layout.addWidget(self.outputs_add_btn)
        prop_layout.addWidget(self.outputs_del_btn)
        prop_layout.addWidget(QLabel("Propriedades:"))
        prop_layout.addWidget(self.properties_list)
        prop_layout.addWidget(self.properties_add_btn)
        prop_layout.addWidget(self.properties_del_btn)
        prop_layout.addWidget(QLabel("Métodos:"))
        prop_layout.addWidget(self.methods_list)
        prop_layout.addWidget(self.methods_add_btn)
        prop_layout.addWidget(self.methods_del_btn)
        prop_layout.addWidget(QLabel("Descrição:"))
        prop_layout.addWidget(self.desc_edit)

        self.prop_widget.setLayout(prop_layout)

        # QLabel para mensagem padrão quando nenhum node está selecionado
        self.no_selection_label = QLabel("Nenhum node selecionado")
        self.no_selection_label.setAlignment(Qt.AlignCenter)
        self.no_selection_label.setStyleSheet("font-size: 16px; color: gray;")

        # Widget de stack para alternar entre painel e mensagem
        from PyQt5.QtWidgets import QStackedWidget, QSizePolicy
        self.panel_stack = QStackedWidget()
        self.panel_stack.addWidget(self.prop_widget)         # index 0: painel de edição
        self.panel_stack.addWidget(self.no_selection_label)  # index 1: mensagem padrão

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.panel_stack)
        self.dock.setWidget(self.scroll_area)
        self.prop_widget.setMinimumWidth(250)
        self.prop_widget.setMaximumWidth(350)
        self.prop_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumWidth(270)
        self.scroll_area.setMaximumWidth(370)
        self.dock.setMinimumWidth(270)
        self.dock.setMaximumWidth(370)
        self.dock.setWidget(self.scroll_area)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.dock.show()
        self.scene.selectionChanged.connect(self.on_selection_changed)
        self.inputs_list.itemChanged.connect(self.input_name_changed)
        self.outputs_list.itemChanged.connect(self.output_name_changed)

        # Conectar sinais dos campos
        self.title_edit.textChanged.connect(self.update_node_title)
        self.desc_edit.textChanged.connect(self.update_node_desc)
        self.inputs_add_btn.clicked.connect(self.add_input)
        self.inputs_del_btn.clicked.connect(self.del_input)
        self.outputs_add_btn.clicked.connect(self.add_output)
        self.outputs_del_btn.clicked.connect(self.del_output)
        # Conectar botões de propriedades e métodos
        self.properties_add_btn.clicked.connect(self.add_property)
        self.properties_del_btn.clicked.connect(self.del_property)
        self.methods_add_btn.clicked.connect(self.add_method)
        self.methods_del_btn.clicked.connect(self.del_method)
        # Conectar edição de itens das listas
        self.properties_list.itemChanged.connect(self.property_name_changed)
        self.methods_list.itemChanged.connect(self.method_name_changed)
    def input_name_changed(self, item):
        if self.selected_node:
            row = self.inputs_list.row(item)
            self.selected_node.inputs[row] = item.text()
            self.selected_node.update()

    def output_name_changed(self, item):
        if self.selected_node:
            row = self.outputs_list.row(item)
            self.selected_node.outputs[row] = item.text()
            self.selected_node.update()

    def on_selection_changed(self):
        # Protege contra acesso à cena destruída
        try:
            if not hasattr(self, "scene") or self.scene is None:
                return
            items = self.scene.selectedItems()
        except RuntimeError:
            # Cena já foi destruída
            return

        if items and isinstance(items[0], NodeItem):
            self.selected_node = items[0]
            self.fill_properties_panel(self.selected_node)
            self.panel_stack.setCurrentIndex(0)  # Mostra painel de edição
        else:
            self.selected_node = None
            self.panel_stack.setCurrentIndex(1)  # Mostra mensagem padrão
        # Garante que o painel nunca seja ocultado
        self.dock.show()

    def fill_properties_panel(self, node):
        self.title_edit.blockSignals(True)
        self.desc_edit.blockSignals(True)
        self.title_edit.setText(node.title)
        self.inputs_list.clear()
        for inp in node.inputs:
            item = QListWidgetItem(inp)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.inputs_list.addItem(item)
        self.outputs_list.clear()
        for out in node.outputs:
            item = QListWidgetItem(out)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.outputs_list.addItem(item)
        # Preencher propriedades
        self.properties_list.blockSignals(True)
        self.properties_list.clear()
        for prop in getattr(node, "properties", []):
            item = QListWidgetItem(prop)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.properties_list.addItem(item)
        self.properties_list.blockSignals(False)
        # Preencher métodos
        self.methods_list.blockSignals(True)
        self.methods_list.clear()
        for method in getattr(node, "methods", []):
            item = QListWidgetItem(method)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.methods_list.addItem(item)
        self.methods_list.blockSignals(False)
    def update_node_title(self, text):
        if self.selected_node:
            self.selected_node.title = text
            self.selected_node.update()

    def update_node_desc(self):
        if self.selected_node:
            self.selected_node.description = self.desc_edit.toPlainText()
            self.selected_node.update()

    def add_input(self):
        if self.selected_node:
            new_input = f"in{len(self.selected_node.inputs)+1}"
            self.selected_node.inputs.append(new_input)
            self.inputs_list.addItem(new_input)
            self.selected_node.update()

    def del_input(self):
        if self.selected_node:
            row = self.inputs_list.currentRow()
            if row >= 0:
                self.selected_node.inputs.pop(row)
                self.inputs_list.takeItem(row)
                self.selected_node.update()

    def add_output(self):
        if self.selected_node:
            new_output = f"out{len(self.selected_node.outputs)+1}"
            self.selected_node.outputs.append(new_output)
            self.outputs_list.addItem(new_output)
            self.selected_node.update()

    def del_output(self):
        if self.selected_node:
            row = self.outputs_list.currentRow()
            if row >= 0:
                self.selected_node.outputs.pop(row)
                self.outputs_list.takeItem(row)
                self.selected_node.update()
        self.inputs_list.addItems(node.inputs)
        self.outputs_list.clear()
        self.outputs_list.addItems(node.outputs)
        self.desc_edit.setPlainText(node.description)
        self.title_edit.blockSignals(False)
        self.desc_edit.blockSignals(False)

    def add_property(self):
        if self.selected_node:
            new_prop = f"propriedade{len(self.selected_node.properties)+1}"
            self.selected_node.properties.append(new_prop)
            item = QListWidgetItem(new_prop)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.properties_list.addItem(item)
            self.selected_node.update()

    def del_property(self):
        if self.selected_node:
            row = self.properties_list.currentRow()
            if row >= 0:
                self.selected_node.properties.pop(row)
                self.properties_list.takeItem(row)
                self.selected_node.update()

    def add_method(self):
        if self.selected_node:
            new_method = f"metodo{len(self.selected_node.methods)+1}"
            self.selected_node.methods.append(new_method)
            item = QListWidgetItem(new_method)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.methods_list.addItem(item)
            self.selected_node.update()

    def del_method(self):
        if self.selected_node:
            row = self.methods_list.currentRow()
            if row >= 0:
                self.selected_node.methods.pop(row)
                self.methods_list.takeItem(row)
                self.selected_node.update()

    def property_name_changed(self, item):
        if self.selected_node:
            row = self.properties_list.row(item)
            self.selected_node.properties[row] = item.text()
            self.selected_node.update()

    def method_name_changed(self, item):
        if self.selected_node:
            row = self.methods_list.row(item)
            self.selected_node.methods[row] = item.text()
            self.selected_node.update()

    def save_project(self):
        import json
        from PyQt5.QtWidgets import QFileDialog
        nodes = []
        node_list = []
        node_index_map = {}
        for item in self.scene.items():
            if isinstance(item, NodeItem):
                node_list.append(item)
        # Garante ordem estável
        node_list = list(reversed(node_list))
        for idx, node in enumerate(node_list):
            node_index_map[node] = idx
            nodes.append({
                "title": node.title,
                "inputs": node.inputs,
                "outputs": node.outputs,
                "description": node.description,
                "properties": getattr(node, "properties", []),
                "methods": getattr(node, "methods", []),
                "pos": [node.pos().x(), node.pos().y()]
            })
        # Serializar conexões
        connections = []
        for item in self.scene.items():
            from src.connection import ConnectionItem
            if isinstance(item, ConnectionItem):
                if item.node_from in node_index_map and item.node_to in node_index_map:
                    connections.append({
                        "from_node": node_index_map[item.node_from],
                        "from_idx": item.idx_from,
                        "to_node": node_index_map[item.node_to],
                        "to_idx": item.idx_to
                    })
        data = {"nodes": nodes, "connections": connections}
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Projeto", "", "JSON (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def load_project(self):
        import json
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Carregar Projeto", "", "JSON (*.json)")
        if path:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.scene.clear()
            node_objs = []
            for node_data in data.get("nodes", []):
                node = NodeItem(
                    title=node_data.get("title", "Node"),
                    inputs=node_data.get("inputs", []),
                    outputs=node_data.get("outputs", []),
                    description=node_data.get("description", ""),
                    properties=node_data.get("properties", []),
                    methods=node_data.get("methods", [])
                )
                node.setPos(*node_data.get("pos", [0, 0]))
                self.scene.addItem(node)
                node_objs.append(node)
            # Forçar atualização dos nodes para garantir que os pinos existam
            for node in node_objs:
                node.update()
            # Reconstruir conexões
            from src.connection import ConnectionItem
            for conn in data.get("connections", []):
                node_from = node_objs[conn["from_node"]]
                idx_from = conn["from_idx"]
                node_to = node_objs[conn["to_node"]]
                idx_to = conn["to_idx"]
                connection = ConnectionItem(node_from, idx_from, node_to, idx_to)
                self.scene.addItem(connection)
                node_from.add_output_connection(connection)
                node_to.add_input_connection(connection)

    def create_node_by_mode(self, scene_pos):
        if self.current_mode == "Diagrama de Classes":
            node = NodeItem(
                title="Classe",
                inputs=["herda", "agrega"],
                outputs=["herda", "agrega"],
                description="Classe com atributos e métodos"
            )
        else:
            node = NodeItem(
                title="Ação",
                inputs=["entrada"],
                outputs=["saída"],
                description="Bloco de lógica"
            )
        node.setPos(scene_pos)
        self.scene.addItem(node)

    def contextMenuEvent(self, event):
        # Menu para alternar modo
        menu = QMenu(self)
        mode_menu = menu.addMenu("Modo de Operação")
        actions = []
        for mode in self.MODES:
            act = mode_menu.addAction(mode)
            act.setCheckable(True)
            act.setChecked(mode == self.current_mode)
            actions.append(act)
        menu.addSeparator()
        action_add_node = menu.addAction("Novo Node")
        action = menu.exec_(event.globalPos())
        if action in actions:
            self.current_mode = action.text()
        elif action == action_add_node:
            scene_pos = self.view.mapToScene(self.view.mapFromGlobal(event.globalPos()))
            self.create_node_by_mode(scene_pos)
        self.outputs_list = QListWidget()
        self.desc_edit = QTextEdit()
        self.inputs_add_btn = QPushButton("Adicionar Entrada")
        self.outputs_add_btn = QPushButton("Adicionar Saída")
        self.inputs_del_btn = QPushButton("Remover Entrada")
        self.outputs_del_btn = QPushButton("Remover Saída")

        prop_layout.addWidget(QLabel("Título:"))
        prop_layout.addWidget(self.title_edit)
        prop_layout.addWidget(QLabel("Entradas:"))
        prop_layout.addWidget(self.inputs_list)
        prop_layout.addWidget(self.inputs_add_btn)
        prop_layout.addWidget(self.inputs_del_btn)
        prop_layout.addWidget(QLabel("Saídas:"))
        prop_layout.addWidget(self.outputs_list)
        prop_layout.addWidget(self.outputs_add_btn)
        prop_layout.addWidget(self.outputs_del_btn)
        prop_layout.addWidget(QLabel("Descrição:"))
        prop_layout.addWidget(self.desc_edit)
        self.prop_widget.setLayout(prop_layout)
        self.dock.setWidget(self.prop_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.dock.hide()

        # Node selecionado
        self.selected_node = None

        # Conexões dos campos
        self.title_edit.textChanged.connect(self.update_node_title)
        self.desc_edit.textChanged.connect(self.update_node_desc)
        self.inputs_add_btn.clicked.connect(self.add_input)
        self.outputs_add_btn.clicked.connect(self.add_output)
        self.inputs_del_btn.clicked.connect(self.del_input)
        self.outputs_del_btn.clicked.connect(self.del_output)

        # Detectar seleção de node
        self.scene.selectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self):
        items = self.scene.selectedItems()
        if items and isinstance(items[0], NodeItem):
            self.selected_node = items[0]
            self.fill_properties_panel(self.selected_node)
            self.dock.show()
        else:
            self.selected_node = None
            self.dock.hide()

    def fill_properties_panel(self, node):
        self.title_edit.blockSignals(True)
        self.desc_edit.blockSignals(True)
        self.title_edit.setText(node.title)
        self.inputs_list.clear()
        self.inputs_list.addItems(node.inputs)
        self.outputs_list.clear()
        self.outputs_list.addItems(node.outputs)
        self.desc_edit.setPlainText(node.description)
        self.title_edit.blockSignals(False)
        self.desc_edit.blockSignals(False)

    def update_node_title(self, text):
        if self.selected_node:
            self.selected_node.title = text
            self.selected_node.update()

    def update_node_desc(self):
        if self.selected_node:
            self.selected_node.description = self.desc_edit.toPlainText()
            self.selected_node.update()

    def add_input(self):
        if self.selected_node:
            self.selected_node.inputs.append(f"in{len(self.selected_node.inputs)+1}")
            self.inputs_list.addItem(self.selected_node.inputs[-1])
            self.selected_node.update()

    def add_output(self):
        if self.selected_node:
            self.selected_node.outputs.append(f"out{len(self.selected_node.outputs)+1}")
            self.outputs_list.addItem(self.selected_node.outputs[-1])
            self.selected_node.update()

    def del_input(self):
        if self.selected_node:
            row = self.inputs_list.currentRow()
            if row >= 0:
                self.selected_node.inputs.pop(row)
                self.inputs_list.takeItem(row)
                self.selected_node.update()

    def del_output(self):
        if self.selected_node:
            row = self.outputs_list.currentRow()
            if row >= 0:
                self.selected_node.outputs.pop(row)
                self.outputs_list.takeItem(row)
                self.selected_node.update()
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())