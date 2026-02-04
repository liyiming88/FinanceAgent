#!/usr/bin/env python3
"""
Markdown to PDF Converter

将 Markdown 文件转换为美观的 PDF 文档。
支持中文、表格、代码块、GitHub Alert 等复杂格式。
"""

import argparse
import os
import sys
from pathlib import Path

import markdown
from markdown.extensions import codehilite, fenced_code, tables, toc, md_in_html
from weasyprint import HTML, CSS
from pygments.formatters import HtmlFormatter


# 获取脚本所在目录
SCRIPT_DIR = Path(__file__).parent.absolute()
SKILL_DIR = SCRIPT_DIR.parent
STYLES_DIR = SKILL_DIR / "styles"


def get_pygments_css():
    """生成 Pygments 代码高亮 CSS"""
    formatter = HtmlFormatter(style='monokai')
    return formatter.get_style_defs('.codehilite')


def convert_github_alerts(html_content: str) -> str:
    """
    将 GitHub Alert 语法转换为带样式的 HTML
    支持: [!NOTE], [!TIP], [!IMPORTANT], [!WARNING], [!CAUTION]
    """
    import re
    
    alert_types = {
        'NOTE': ('💡', '#0969da', '#ddf4ff'),
        'TIP': ('💚', '#1a7f37', '#dafbe1'),
        'IMPORTANT': ('💜', '#8250df', '#fbefff'),
        'WARNING': ('⚠️', '#9a6700', '#fff8c5'),
        'CAUTION': ('🔴', '#cf222e', '#ffebe9'),
    }
    
    for alert_type, (icon, border_color, bg_color) in alert_types.items():
        # 匹配 blockquote 中的 [!TYPE] 格式
        pattern = rf'<blockquote>\s*<p>\[!{alert_type}\]'
        replacement = f'''<blockquote class="alert alert-{alert_type.lower()}" style="border-left: 4px solid {border_color}; background-color: {bg_color}; padding: 12px 16px; margin: 16px 0;">
<p><strong>{icon} {alert_type}</strong></p>
<p>'''
        html_content = re.sub(pattern, replacement, html_content, flags=re.IGNORECASE)
    
    return html_content


def create_html_document(body_content: str, title: str = "Document") -> str:
    """创建完整的 HTML 文档结构"""
    pygments_css = get_pygments_css()
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {pygments_css}
    </style>
</head>
<body>
    <article class="markdown-body">
        {body_content}
    </article>
</body>
</html>"""


def convert_md_to_pdf(
    input_file: str,
    output_file: str,
    style: str = "default",
    paper_size: str = "a4"
) -> bool:
    """
    将 Markdown 文件转换为 PDF
    
    Args:
        input_file: 输入 Markdown 文件路径
        output_file: 输出 PDF 文件路径
        style: 样式模板名称 (default/report)
        paper_size: 纸张大小 (a4/letter)
    
    Returns:
        bool: 转换是否成功
    """
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    # 验证输入文件
    if not input_path.exists():
        print(f"❌ 错误: 输入文件不存在: {input_file}")
        return False
    
    # 读取 Markdown 内容
    print(f"📖 读取文件: {input_file}")
    with open(input_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # 配置 Markdown 扩展
    extensions = [
        'tables',
        'fenced_code',
        'codehilite',
        'toc',
        'md_in_html',
        'attr_list',
        'def_list',
        'footnotes',
        'abbr',
        'meta',
        'nl2br',
        'sane_lists',
        'smarty',
        'wikilinks',
    ]
    
    extension_configs = {
        'codehilite': {
            'css_class': 'codehilite',
            'linenums': False,
            'guess_lang': True,
        },
        'toc': {
            'permalink': False,
        },
    }
    
    # 转换为 HTML
    print("🔄 转换 Markdown 为 HTML...")
    md = markdown.Markdown(extensions=extensions, extension_configs=extension_configs)
    html_body = md.convert(md_content)
    
    # 处理 GitHub Alert
    html_body = convert_github_alerts(html_body)
    
    # 获取标题
    title = input_path.stem
    if hasattr(md, 'Meta') and 'title' in md.Meta:
        title = md.Meta['title'][0]
    
    # 创建完整 HTML
    html_content = create_html_document(html_body, title)
    
    # 加载 CSS 样式
    css_file = STYLES_DIR / f"{style}.css"
    if not css_file.exists():
        print(f"⚠️ 警告: 样式文件不存在 {css_file}，使用默认样式")
        css_file = STYLES_DIR / "default.css"
    
    # 纸张大小 CSS
    paper_css = f"@page {{ size: {paper_size}; }}"
    
    # 渲染 PDF
    print(f"📄 生成 PDF: {output_file}")
    try:
        stylesheets = [CSS(string=paper_css)]
        if css_file.exists():
            stylesheets.append(CSS(filename=str(css_file)))
        
        # 设置 base_url 以支持相对路径图片
        base_url = str(input_path.parent.absolute())
        
        HTML(string=html_content, base_url=base_url).write_pdf(
            output_path,
            stylesheets=stylesheets
        )
        
        print(f"✅ 转换成功! PDF 已保存到: {output_path.absolute()}")
        return True
        
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="将 Markdown 文件转换为美观的 PDF 文档",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python convert_to_pdf.py input.md output.pdf
  python convert_to_pdf.py input.md output.pdf --style report
  python convert_to_pdf.py input.md output.pdf --style report --paper letter
        """
    )
    
    parser.add_argument('input', help='输入 Markdown 文件路径')
    parser.add_argument('output', help='输出 PDF 文件路径')
    parser.add_argument(
        '--style', '-s',
        choices=['default', 'report'],
        default='default',
        help='样式模板 (default: default)'
    )
    parser.add_argument(
        '--paper', '-p',
        choices=['a4', 'letter'],
        default='a4',
        help='纸张大小 (default: a4)'
    )
    
    args = parser.parse_args()
    
    success = convert_md_to_pdf(
        args.input,
        args.output,
        args.style,
        args.paper
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
