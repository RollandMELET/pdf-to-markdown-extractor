#!/usr/bin/env python3
"""
Generate complex PDF fixture for Feature #47.

Creates technical_report.pdf with characteristics that should score > 35:
- 25 pages (10 points)
- Multi-column layout (25 points)
- Mathematical formulas (15 points)
- Tables (10 points)
- Images (10 points)
Total: 70 points → "complex"
"""

import fitz  # PyMuPDF
from pathlib import Path


def create_complex_pdf():
    """Create a complex PDF for testing."""
    output_path = Path("tests/fixtures/complex/technical_report.pdf")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create PDF
    doc = fitz.open()

    # Page dimensions for multi-column layout
    page_width = 595  # A4 width in points
    page_height = 842  # A4 height in points

    # Create 25 pages with varying content
    for page_num in range(25):
        page = doc.new_page(width=page_width, height=page_height)

        # Add title
        title_rect = fitz.Rect(50, 50, page_width - 50, 100)
        page.insert_textbox(
            title_rect,
            f"Chapter {page_num + 1}: Advanced Topics in Machine Learning",
            fontsize=16,
            fontname="helv",
            align=fitz.TEXT_ALIGN_CENTER,
        )

        # Add page number
        page_num_rect = fitz.Rect(page_width - 80, page_height - 50, page_width - 30, page_height - 30)
        page.insert_textbox(
            page_num_rect,
            f"Page {page_num + 1}",
            fontsize=10,
            fontname="helv",
            align=fitz.TEXT_ALIGN_CENTER,
        )

        # Multi-column layout (25 points)
        # Left column
        left_col_rect = fitz.Rect(50, 120, page_width / 2 - 20, page_height - 80)
        left_content = f"""
This is the left column content for page {page_num + 1}.

Machine learning algorithms require careful consideration of
hyperparameters and model architecture. The optimization process
involves balancing bias-variance tradeoff while maintaining
computational efficiency.

Key considerations:
• Model capacity
• Regularization techniques
• Training dynamics
• Convergence criteria

The theoretical foundation builds upon statistical learning
theory and computational complexity analysis.
"""
        page.insert_textbox(
            left_col_rect,
            left_content,
            fontsize=10,
            fontname="helv",
            align=fitz.TEXT_ALIGN_LEFT,
        )

        # Right column
        right_col_rect = fitz.Rect(page_width / 2 + 20, 120, page_width - 50, page_height - 80)
        right_content = f"""
This is the right column content for page {page_num + 1}.

Neural network architectures have evolved significantly,
incorporating attention mechanisms and transformer blocks.
Recent advances in self-supervised learning demonstrate
promising results across multiple domains.

Performance metrics:
• Accuracy: 94.7%
• Precision: 92.3%
• Recall: 91.8%
• F1-Score: 92.0%

Further research is needed to understand the generalization
properties of these models under distribution shift.
"""
        page.insert_textbox(
            right_col_rect,
            right_content,
            fontsize=10,
            fontname="helv",
            align=fitz.TEXT_ALIGN_LEFT,
        )

        # Add mathematical formulas every few pages (15+ points)
        if page_num % 3 == 0:
            formula_rect = fitz.Rect(50, page_height - 150, page_width - 50, page_height - 100)
            formulas = f"""
Mathematical Framework:

Loss function: L(θ) = ∑ᵢ (yᵢ - f(xᵢ; θ))²
Gradient: ∇L = ∂L/∂θ
Learning rate: α ∈ (0, 1]
Convergence: ||θₜ - θ*|| → 0 as t → ∞
"""
            page.insert_textbox(
                formula_rect,
                formulas,
                fontsize=9,
                fontname="cour",
                align=fitz.TEXT_ALIGN_LEFT,
            )

        # Add tables every 5 pages (10+ points)
        if page_num % 5 == 0 and page_num > 0:
            table_rect = fitz.Rect(50, 400, page_width - 50, 500)
            table_content = """
Table: Model Performance Comparison

Model        Accuracy   F1-Score   Training Time
ResNet-50    94.2%      93.1%      4.2h
ViT-Base     95.7%      94.8%      6.1h
EfficientNet 96.1%      95.3%      3.8h
"""
            page.insert_textbox(
                table_rect,
                table_content,
                fontsize=8,
                fontname="cour",
                align=fitz.TEXT_ALIGN_LEFT,
            )

        # Add simple diagram/image placeholder every 6 pages (10+ points)
        if page_num % 6 == 0 and page_num > 0:
            # Draw a simple rectangle as "image"
            img_rect = fitz.Rect(page_width / 2 - 50, 350, page_width / 2 + 50, 450)
            page.draw_rect(img_rect, color=(0, 0, 0), width=2)

            # Add caption
            caption_rect = fitz.Rect(page_width / 2 - 100, 460, page_width / 2 + 100, 480)
            page.insert_textbox(
                caption_rect,
                f"Figure {page_num // 6}: Architecture Diagram",
                fontsize=8,
                fontname="helv",
                align=fitz.TEXT_ALIGN_CENTER,
            )

    # Save PDF
    doc.save(output_path)
    doc.close()

    print(f"✅ Created complex PDF: {output_path}")
    print(f"   Pages: 25")
    print(f"   Size: {output_path.stat().st_size / 1024:.1f} KB")
    print()
    print("Expected complexity score:")
    print("  - page_count: 10 points (25 pages)")
    print("  - columns: 25 points (multi-column layout)")
    print("  - formulas: 15 points (8 formula sections)")
    print("  - tables: 10 points (5 tables)")
    print("  - images: 10 points (4 diagrams)")
    print("  Total: ~70 points → COMPLEX")


if __name__ == "__main__":
    create_complex_pdf()
