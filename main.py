import sys
import os
from datetime import datetime
from PIL import Image

from PySide6.QtCore import Qt, QFileInfo, QUrl
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMessageBox, QFileDialog, QListWidgetItem
)

from ui import MainWindowUI, ThumbnailWidget
from worker import PdfConverterWorker

SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}

class AppMain(MainWindowUI):
    def __init__(self):
        super().__init__()
        
        # 内部维护的图片绝对路径列表
        self.image_paths = []
        
        self.worker = None
        self.default_save_dir = os.path.expanduser("~/Desktop")
        self.lbl_save_path.setText(f"默认保存到: {self.default_save_dir}")

        self.bind_events()

    def bind_events(self):
        # 拖拽事件
        self.files_dropped.connect(self.handle_add_files)
        
        # 按钮事件
        self.btn_add_img.clicked.connect(self.browse_images)
        self.btn_add_folder.clicked.connect(self.browse_folder)
        self.btn_add_clipboard.clicked.connect(self.import_from_clipboard)
        self.btn_select_path.clicked.connect(self.select_output_dir)
        self.btn_convert.clicked.connect(self.start_conversion)

    def handle_add_files(self, paths):
        added_count = 0
        for path in paths:
            if os.path.isdir(path):
                # 遍历文件夹
                for root, dirs, files in os.walk(path):
                    for file in files:
                        ext = os.path.splitext(file)[1].lower()
                        if ext in SUPPORTED_FORMATS:
                            full_path = os.path.join(root, file)
                            if full_path not in self.image_paths:
                                self.image_paths.append(full_path)
                                self.add_thumbnail(full_path)
                                added_count += 1
            else:
                ext = os.path.splitext(path)[1].lower()
                if ext in SUPPORTED_FORMATS:
                    if path not in self.image_paths:
                        self.image_paths.append(path)
                        self.add_thumbnail(path)
                        added_count += 1
        
        self.update_stats()

    def browse_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", "", 
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.webp)"
        )
        if files:
            self.handle_add_files(files)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.handle_add_files([folder])

    def import_from_clipboard(self):
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()
        
        if mime.hasImage():
            image = clipboard.image()
            if not image.isNull():
                # 保存到临时目录
                import tempfile
                temp_dir = tempfile.gettempdir()
                filename = f"clipboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                filepath = os.path.join(temp_dir, filename)
                image.save(filepath, "PNG")
                self.handle_add_files([filepath])
        elif mime.hasUrls():
            urls = mime.urls()
            files = [u.toLocalFile() for u in urls if u.isLocalFile()]
            self.handle_add_files(files)

    def select_output_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "选择保存目录", self.default_save_dir)
        if folder:
            self.default_save_dir = folder
            self.lbl_save_path.setText(f"保存到: {self.default_save_dir}")

    def add_thumbnail(self, path):
        item = QListWidgetItem(self.list_widget)
        
        # 自定义 Widget
        thumb_widget = ThumbnailWidget(path)
        item.setSizeHint(thumb_widget.sizeHint())
        thumb_widget.delete_clicked.connect(self.remove_image)
        thumb_widget.rotate_clicked.connect(self.rotate_image)
        
        # 将 item 和路径绑定，方便后续查找
        item.setData(Qt.UserRole, path)
        
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, thumb_widget)

    def remove_image(self, path):
        if path in self.image_paths:
            self.image_paths.remove(path)
            
        # 查找对应的 item 并移除
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == path:
                self.list_widget.takeItem(i)
                break
                
        self.update_stats()

    def rotate_image(self, path):
        try:
            # 顺时针旋转 90 度 (Image.ROTATE_270)
            with Image.open(path) as img:
                img_rotated = img.transpose(Image.ROTATE_270)
                img_rotated.save(path)
            
            # 更新缩略图
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.data(Qt.UserRole) == path:
                    widget = self.list_widget.itemWidget(item)
                    if isinstance(widget, ThumbnailWidget):
                        widget.update_thumbnail()
                    break
        except Exception as e:
            QMessageBox.warning(self, "旋转失败", f"无法旋转图片: {e}")

    def update_stats(self):
        total_size = 0
        for path in self.image_paths:
            try:
                total_size += os.path.getsize(path)
            except Exception:
                pass
        
        mb_size = total_size / (1024 * 1024)
        self.lbl_stats.setText(f"已选中 {len(self.image_paths)} 张图片 | {mb_size:.2f} MB")
        self.btn_convert.setEnabled(len(self.image_paths) > 0)

    def start_conversion(self):
        if not self.image_paths:
            QMessageBox.information(self, "提示", "请先添加图片！")
            return

        filename = self.input_filename.text().strip()
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
            
        output_path = os.path.join(self.default_save_dir, filename)
        
        config = {
            "quality": self.slider_quality.value(),
            "page_size": "A4" if "A4" in self.combo_page_size.currentText() else "auto"
        }

        self.btn_convert.setEnabled(False)
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.lbl_stats.setText("准备转换...")

        self.worker = PdfConverterWorker(self.image_paths, output_path, config)
        self.worker.progress_changed.connect(self.on_progress)
        self.worker.conversion_finished.connect(self.on_finished)
        self.worker.start()

    def on_progress(self, percent, text):
        self.progress_bar.setValue(percent)
        self.lbl_stats.setText(text)

    def on_finished(self, success, msg):
        self.btn_convert.setEnabled(True)
        self.progress_bar.hide()
        self.update_stats()

        if success:
            reply = QMessageBox.information(
                self, "转换成功", 
                "PDF 生成成功！是否打开所在文件夹？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # 打开文件夹并选中文件
                output_path = os.path.join(self.default_save_dir, self.input_filename.text().strip())
                if not output_path.lower().endswith('.pdf'):
                    output_path += '.pdf'
                # 兼容 Windows 资源管理器选中
                os.startfile(self.default_save_dir)
        else:
            QMessageBox.critical(self, "转换失败", f"错误详情: {msg}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppMain()
    window.show()
    sys.exit(app.exec())
