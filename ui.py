import os
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QListWidget, QListWidgetItem, 
    QComboBox, QSlider, QLineEdit, QProgressBar, 
    QFileDialog, QFrame, QSizePolicy, QSpacerItem,
    QStyle, QStyledItemDelegate
)

QSS = """
QMainWindow {
    background-color: #f5f6fa;
}
QWidget {
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    color: #2f3640;
}
QPushButton {
    background-color: #ffffff;
    border: 1px solid #dcdde1;
    border-radius: 4px;
    padding: 6px 12px;
}
QPushButton:hover {
    background-color: #e8ecef;
    border-color: #b2bec3;
}
QPushButton#primaryBtn {
    background-color: #00a8ff;
    color: white;
    font-weight: bold;
    border: none;
    padding: 8px 24px;
    font-size: 14px;
}
QPushButton#primaryBtn:hover {
    background-color: #0097e6;
}
QPushButton#primaryBtn:disabled {
    background-color: #a4b0be;
}
QListWidget {
    background-color: #ffffff;
    border: 1px solid #dcdde1;
    border-radius: 4px;
}
QListWidget::item {
    background-color: transparent;
    border: none;
}
QListWidget::item:hover {
    background-color: transparent;
    border: none;
}
QWidget#thumbnail {
    background-color: #f5f6fa;
    border: 1px solid #e1e2e6;
    border-radius: 4px;
}
QWidget#thumbnail:hover {
    border: 1px solid #00a8ff;
}
QFrame#rightPanel {
    background-color: #ffffff;
    border: 1px solid #dcdde1;
    border-radius: 4px;
}
QLineEdit, QComboBox {
    border: 1px solid #dcdde1;
    border-radius: 4px;
    padding: 4px 8px;
    background: #ffffff;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #00a8ff;
}
QProgressBar {
    border: 1px solid #dcdde1;
    border-radius: 4px;
    text-align: center;
    background-color: #f5f6fa;
}
QProgressBar::chunk {
    background-color: #4cd137;
    border-radius: 3px;
}
QSlider::groove:horizontal {
    border: 1px solid #dcdde1;
    height: 6px;
    background: #f5f6fa;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #00a8ff;
    border: 1px solid #0097e6;
    width: 14px;
    margin: -4px 0;
    border-radius: 7px;
}
"""

class ThumbnailWidget(QWidget):
    delete_clicked = Signal(str) # 发送文件路径
    rotate_clicked = Signal(str)

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setFixedSize(120, 120)
        self.setObjectName("thumbnail")
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(2)

        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.img_label)

        # 底部工具栏
        self.toolbar = QWidget()
        self.toolbar_layout = QHBoxLayout(self.toolbar)
        self.toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        self.btn_rotate = QPushButton()
        self.btn_rotate.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.btn_rotate.setFixedSize(30, 24)
        self.btn_rotate.clicked.connect(lambda: self.rotate_clicked.emit(self.file_path))
        
        self.btn_delete = QPushButton()
        self.btn_delete.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.btn_delete.setFixedSize(30, 24)
        self.btn_delete.setStyleSheet("color: #e84118; font-weight: bold;")
        self.btn_delete.clicked.connect(lambda: self.delete_clicked.emit(self.file_path))
        
        self.toolbar_layout.addStretch()
        self.toolbar_layout.addWidget(self.btn_rotate)
        self.toolbar_layout.addWidget(self.btn_delete)
        self.toolbar_layout.addStretch()

        self.layout.addWidget(self.toolbar)
        
        # 初始加载缩略图
        self.update_thumbnail()

    def update_thumbnail(self):
        pixmap = QPixmap(self.file_path)
        if not pixmap.isNull():
            # 按比例缩放，保持 100x80 以内
            pixmap = pixmap.scaled(100, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img_label.setPixmap(pixmap)
        else:
            self.img_label.setText("无法加载")

class MainWindowUI(QMainWindow):
    # 允许子类捕获拖拽信号
    files_dropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片转 PDF 工具")
        self.resize(900, 650)
        self.setStyleSheet(QSS)
        self.setAcceptDrops(True)

        # 中心 Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 整体竖直布局 (三段式的顶部主体 + 底部状态栏)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # ====== 上半部分：左右结构 ======
        h_layout = QHBoxLayout()
        
        # --- 左侧主工作区 ---
        left_layout = QVBoxLayout()
        
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.IconMode)
        self.list_widget.setResizeMode(QListWidget.Adjust)
        self.list_widget.setSpacing(10)
        self.list_widget.setMovement(QListWidget.Static)
        self.list_widget.setUniformItemSizes(True)
        self.list_widget.setGridSize(QSize(130, 130))
        
        left_layout.addWidget(self.list_widget)

        left_btn_layout = QHBoxLayout()
        self.btn_add_img = QPushButton("+ 添加图片")
        self.btn_add_folder = QPushButton("+ 添加文件夹")
        self.btn_add_clipboard = QPushButton("📋 剪切板导入")
        left_btn_layout.addWidget(self.btn_add_img)
        left_btn_layout.addWidget(self.btn_add_folder)
        left_btn_layout.addWidget(self.btn_add_clipboard)
        left_btn_layout.addStretch()
        
        left_layout.addLayout(left_btn_layout)
        h_layout.addLayout(left_layout, stretch=2)

        # --- 右侧配置面板 ---
        right_panel = QFrame()
        right_panel.setObjectName("rightPanel")
        right_panel.setFixedWidth(280)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(15)
        right_layout.setContentsMargins(15, 15, 15, 15)

        title_lbl = QLabel("导出配置")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        right_layout.addWidget(title_lbl)

        # 纸张大小
        right_layout.addWidget(QLabel("页面尺寸:"))
        self.combo_page_size = QComboBox()
        self.combo_page_size.setItemDelegate(QStyledItemDelegate())
        self.combo_page_size.addItems(["自适应原图 (Auto)", "标准 A4 (居中)"])
        right_layout.addWidget(self.combo_page_size)

        # 输出文件名和路径
        right_layout.addWidget(QLabel("输出文件名:"))
        self.input_filename = QLineEdit("output.pdf")
        right_layout.addWidget(self.input_filename)

        self.btn_select_path = QPushButton("选择保存位置...")
        right_layout.addWidget(self.btn_select_path)
        
        self.lbl_save_path = QLabel("默认保存到桌面")
        self.lbl_save_path.setStyleSheet("color: #7f8fa6; font-size: 12px;")
        self.lbl_save_path.setWordWrap(True)
        right_layout.addWidget(self.lbl_save_path)

        # 压缩质量
        right_layout.addWidget(QLabel("图片压缩质量 (Quality):"))
        self.slider_quality = QSlider(Qt.Horizontal)
        self.slider_quality.setRange(10, 100)
        self.slider_quality.setValue(80)
        self.lbl_quality_val = QLabel("80%")
        
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(self.slider_quality)
        quality_layout.addWidget(self.lbl_quality_val)
        right_layout.addLayout(quality_layout)
        
        # 绑定滑动事件更新标签
        self.slider_quality.valueChanged.connect(
            lambda v: self.lbl_quality_val.setText(f"{v}%")
        )

        right_layout.addStretch()
        h_layout.addWidget(right_panel)

        main_layout.addLayout(h_layout)

        # ====== 底部状态栏 ======
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 10, 0, 0)
        
        self.lbl_stats = QLabel("已选中 0 张图片 | 0 MB")
        self.lbl_stats.setStyleSheet("color: #7f8fa6; font-weight: bold;")
        bottom_layout.addWidget(self.lbl_stats)
        
        bottom_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(250)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        bottom_layout.addWidget(self.progress_bar)

        self.btn_convert = QPushButton("开始转换")
        self.btn_convert.setObjectName("primaryBtn")
        self.btn_convert.setFixedSize(120, 36)
        bottom_layout.addWidget(self.btn_convert)

        main_layout.addLayout(bottom_layout)

    # 支持拖拽文件
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        files = [url.toLocalFile() for url in urls if url.isLocalFile()]
        if files:
            self.files_dropped.emit(files)

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindowUI()
    window.show()
    sys.exit(app.exec())
