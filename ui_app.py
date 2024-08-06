import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QSpacerItem, QSizePolicy, QProgressDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from cemento.draw_io.read_diagram import ReadDiagram

class FileParserApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # Layouts
        main_layout = QVBoxLayout()
        file_layout = QHBoxLayout()
        output_layout = QHBoxLayout()
        button_layout = QHBoxLayout()

        # Input File Selection
        self.input_label = QLabel("Input File:")
        self.input_path = QLineEdit()
        self.input_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.input_button = QPushButton("Browse")
        self.input_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.input_button.clicked.connect(self.select_input_file)
        file_layout.addWidget(self.input_label)
        file_layout.addWidget(self.input_path)
        file_layout.addWidget(self.input_button)

        # Output File Selection
        self.output_label = QLabel("Output File:")
        self.output_path = QLineEdit()
        self.output_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.output_button = QPushButton("Browse")
        self.output_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.output_button.clicked.connect(self.select_output_file)
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(self.output_button)

        # Parse Button
        self.parse_button = QPushButton("Read Diagram")
        self.parse_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.parse_button.clicked.connect(self.start_parsing)
        button_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        button_layout.addWidget(self.parse_button)
        button_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Error Table
        self.error_table = QTableWidget()
        self.error_table.setColumnCount(2)
        self.error_table.setHorizontalHeaderLabels(["Element ID", "Error Description"])
        self.error_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Adding layouts to main layout
        main_layout.addLayout(file_layout)
        main_layout.addLayout(output_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.error_table)

        self.setLayout(main_layout)
        self.setWindowTitle("Cemento (Read your Ontologies)")
        self.setGeometry(300, 300, 600, 400)

    def select_input_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Input File")
        if file_name:
            self.input_path.setText(file_name)

    def select_output_file(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Select Output File")
        if file_name:
            self.output_path.setText(file_name)

    def start_parsing(self):
        input_file = self.input_path.text()
        output_file = self.output_path.text()

        if not input_file or not output_file:
            self.show_error("Please select both input and output paths.")
            return

        self.progress_dialog = QProgressDialog("Parsing file...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setAutoClose(True)

        self.parser_thread = ParserThread(input_file, output_file)
        self.parser_thread.progress_update.connect(self.progress_dialog.setValue)
        self.parser_thread.finished.connect(self.on_parsing_finished)
        self.progress_dialog.canceled.connect(self.parser_thread.terminate)

        self.parser_thread.start()

    def on_parsing_finished(self):
        self.populate_error_table(self.parser_thread.errors)
        self.progress_dialog.reset()

    def parse_file(self, progress_callback):
        # Example dummy parsing logic that generates errors
        errors = []
        for i in range(1, 101):
            progress_callback.emit(i)
            if i % 20 == 0:
                errors.append((i, f"Error at line {i}"))

        return errors

    def populate_error_table(self, errors):
        self.error_table.setRowCount(0)
        for element_id, description in errors:
            row_position = self.error_table.rowCount()
            self.error_table.insertRow(row_position)

            if not element_id:
                element_id = "N/A"

            self.error_table.setItem(row_position, 0, QTableWidgetItem(str(element_id)))
            self.error_table.setItem(row_position, 1, QTableWidgetItem(description))

    def show_error(self, message):
        self.error_table.setRowCount(0)
        row_position = self.error_table.rowCount()
        self.error_table.insertRow(row_position)
        self.error_table.setItem(row_position, 0, QTableWidgetItem("N/A"))
        self.error_table.setItem(row_position, 1, QTableWidgetItem(message))

class ParserThread(QThread):
    progress_update = pyqtSignal(int)
    
    def __init__(self, input_file_path, output_file_path):
        super().__init__()
        self._input_file_path = input_file_path
        self._output_file_path = output_file_path
        self.errors = []

    def _get_input_file_path(self):
        return self._input_file_path
    
    def _get_output_file_path(self):
        return self._output_file_path
    
    def _add_errors(self, error_record):
        self.errors.append(error_record)
    
    def run(self):
        try:
            read_diagram = ReadDiagram(file_path=self._get_input_file_path())
            self.progress_update.emit(33)

            rels_df = read_diagram.get_relationships()
            rels_df.to_csv(self._get_output_file_path())
            self.progress_update.emit(66)

            read_errors = read_diagram.get_errors()
            for error_id, error_data in read_errors.items():
                for error in error_data['errors']:
                    self._add_errors((error_id, str(error)))
        except Exception as e:
            self._add_errors((None, str(e)))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FileParserApp()
    ex.show()
    sys.exit(app.exec_())