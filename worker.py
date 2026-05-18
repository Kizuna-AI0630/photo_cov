import os
import tempfile
import shutil
from typing import List, Dict, Any

from PySide6.QtCore import QThread, Signal
from PIL import Image, ImageOps
import img2pdf

class PdfConverterWorker(QThread):
    progress_changed = Signal(int, str)
    conversion_finished = Signal(bool, str)

    def __init__(self, image_paths: List[str], output_path: str, config: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.image_paths = image_paths
        self.output_path = output_path
        self.config = config
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        if not self.image_paths:
            self.conversion_finished.emit(False, "没有选择任何图片。")
            return

        temp_dir = tempfile.mkdtemp(prefix="photo_cov_")
        temp_image_paths = []

        try:
            total_images = len(self.image_paths)
            quality = self.config.get("quality", 80)
            page_size = self.config.get("page_size", "auto")

            for i, img_path in enumerate(self.image_paths):
                if self._is_cancelled:
                    self.conversion_finished.emit(False, "转换已取消。")
                    return

                filename = os.path.basename(img_path)
                self.progress_changed.emit(int((i / total_images) * 80), f"正在处理: {filename}")

                # 读取并处理图片
                with Image.open(img_path) as img:
                    # 修复 EXIF 旋转
                    img = ImageOps.exif_transpose(img)
                    
                    # 转为 RGB 避免 RGBA 保存为 JPEG 报错
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # 暂存为 JPEG 进行压缩
                    temp_img_path = os.path.join(temp_dir, f"temp_{i:04d}.jpg")
                    img.save(temp_img_path, format="JPEG", quality=quality)
                    temp_image_paths.append(temp_img_path)

            self.progress_changed.emit(80, "正在生成 PDF...")
            
            if page_size == "A4":
                # A4 尺寸 210mm x 297mm
                a4inpt = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297))
                # 设置页面尺寸，原图居中（img2pdf 默认 fit 适应页面）
                layout_fun = img2pdf.get_layout_fun(pagesize=a4inpt)
                
                with open(self.output_path, "wb") as f:
                    pdf_bytes = img2pdf.convert(temp_image_paths, layout_fun=layout_fun)
                    f.write(pdf_bytes)
            else:
                with open(self.output_path, "wb") as f:
                    pdf_bytes = img2pdf.convert(temp_image_paths)
                    f.write(pdf_bytes)

            self.progress_changed.emit(100, "处理完成！")
            self.conversion_finished.emit(True, "转换成功！")

        except Exception as e:
            self.conversion_finished.emit(False, f"转换失败: {str(e)}")
        finally:
            # 清理临时文件
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"清理临时文件夹失败: {e}")

if __name__ == "__main__":
    # 简单的本地测试验证块
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    
    # 构建假数据进行测试
    test_images = []
    # 创建几张测试用的纯色图片
    os.makedirs("test_inputs", exist_ok=True)
    for i in range(3):
        img_path = f"test_inputs/test_{i}.jpg"
        img = Image.new('RGB', (800, 600), color=(255, i*80, i*50))
        img.save(img_path)
        test_images.append(img_path)

    output_pdf = "test_output.pdf"
    config = {"quality": 80, "page_size": "A4"}

    worker = PdfConverterWorker(test_images, output_pdf, config)

    def on_progress(percent, text):
        print(f"[{percent}%] {text}")

    def on_finished(success, msg):
        print(f"完成状态: {success}, 信息: {msg}")
        app.quit()

    worker.progress_changed.connect(on_progress)
    worker.conversion_finished.connect(on_finished)
    
    print("开始测试...")
    worker.start()
    
    sys.exit(app.exec())
