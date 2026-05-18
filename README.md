# 图片转 PDF 工具 (Image to PDF Converter)

这是一个基于 Python (PySide6) 开发的高性能、100% 离线运行的桌面级“图片转 PDF”转换工具。

## 🌟 核心特性
- **完全离线安全**：所有图像处理与转换均在本地完成，无需依赖任何网络 API，保护隐私安全。
- **高性能转换**：独立后台多线程处理，支持批量拖拽数百张图片而不卡顿。
- **优雅的现代 UI**：扁平化设计、深浅色自适应的高颜值 QSS 样式。
- **自定义布局与质量**：
  - 支持 **自适应原图尺寸** 或 **标准 A4 居中布局**。
  - 支持画质自由压缩（提供 10%~100% 的智能压缩率调节），极大地减小 PDF 文件体积。
- **交互极简**：支持拖拽导入、文件夹导入和剪切板直接解析；缩略图支持快捷旋转与删除。

## 🛠️ 技术栈
- 语言：Python 3.10+
- GUI 框架：PySide6 (Qt for Python)
- 图像处理引擎：Pillow (PIL)
- 极速 PDF 合并：img2pdf

## 🚀 运行与使用方法
如果您配置了 Python 环境：
```bash
pip install PySide6 Pillow img2pdf
python main.py
```
*(或者直接双击 `dist` 目录中打包好的 `ImageToPDF.exe` 独立可执行文件，无需任何环境秒开)*

## 📦 如何打包为 EXE
如果您需要将源码再次编译为独立的 `.exe` 程序分发：
```bash
pyinstaller -y --noconsole --name "ImageToPDF" main.py
```
