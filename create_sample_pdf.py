"""
Create a sample PDF manuscript for testing.
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import os

def create_sample_pdf():
    """Create a sample PDF manuscript for testing."""

    # Create exports directory if it doesn't exist
    os.makedirs("exports", exist_ok=True)

    # Sample manuscript content
    content = {
        "title": "Novel Deep Learning Approach for Image Classification",
        "abstract": """
        This paper presents a novel deep learning approach for image classification that achieves state-of-the-art performance on multiple benchmark datasets. Our method combines convolutional neural networks with attention mechanisms to improve feature extraction and classification accuracy. Experimental results demonstrate significant improvements over existing methods, with accuracy gains of up to 5% on standard datasets. The proposed approach is computationally efficient and can be deployed on resource-constrained devices.
        """,
        "introduction": """
        Image classification is a fundamental task in computer vision with applications in various domains including medical imaging, autonomous vehicles, and security systems. Traditional approaches rely on hand-crafted features, but deep learning methods have shown superior performance by automatically learning hierarchical features from raw data.

        Recent advances in attention mechanisms have shown promise in improving the performance of deep learning models by allowing them to focus on relevant parts of the input. However, most existing approaches apply attention mechanisms globally, which may not be optimal for all types of data.
        """,
        "methods": """
        We propose a novel architecture that integrates attention mechanisms into convolutional neural networks. The model consists of multiple layers of convolutional operations followed by attention modules that selectively focus on important regions of the input image.

        The attention mechanism is implemented as follows:
        1. Feature extraction using convolutional layers
        2. Attention weight computation based on feature importance
        3. Weighted feature aggregation
        4. Classification using fully connected layers

        Training is performed using stochastic gradient descent with momentum optimization. The learning rate is initially set to 0.01 and decayed by a factor of 0.1 every 30 epochs.
        """,
        "results": """
        Our experimental results show that the proposed method achieves 95.2% accuracy on the CIFAR-10 dataset, outperforming previous state-of-the-art methods by 2.1%. The model also demonstrates robustness to various data augmentations and noise conditions.

        Table 1 shows the performance comparison with existing methods:

        Method | Accuracy | Parameters
        -------|----------|-----------
        CNN Baseline | 92.5% | 1.2M
        ResNet-50 | 93.8% | 25.6M
        Our Method | 95.2% | 8.7M

        The results indicate that our method provides a good balance between accuracy and computational efficiency.
        """,
        "discussion": """
        The results indicate that attention mechanisms can significantly improve the performance of convolutional neural networks for image classification tasks. The proposed method provides a good balance between accuracy and computational efficiency, making it suitable for real-world applications.

        One limitation of our approach is that it requires more training time compared to simpler CNN architectures. However, the improved accuracy justifies the additional computational cost for applications where high accuracy is critical.

        Future work will explore the application of this method to other computer vision tasks such as object detection and semantic segmentation.
        """,
        "references": """
        [1] Smith, J. et al. Deep learning for image classification. Nature 2020, 580, 123-126.

        [2] Johnson, A. & Brown, B. Attention mechanisms in neural networks. Science 2021, 372, 145-149.

        [3] Zhang, C. et al. Efficient deep learning architectures. IEEE Transactions 2022, 45, 78-92.

        [4] Chen, D. et al. Convolutional neural networks for visual recognition. ACM Computing Surveys 2023, 55, 1-35.
        """
    }

    # Create PDF
    filename = "sample_manuscript.pdf"
    filepath = os.path.join("exports", filename)

    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Center
    )

    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=15,
        spaceBefore=20
    )

    # Build document content
    story = []

    # Title
    story.append(Paragraph(content["title"], title_style))
    story.append(Spacer(1, 20))

    # Abstract
    story.append(Paragraph("Abstract", section_style))
    story.append(Paragraph(content["abstract"].strip(), styles['Normal']))
    story.append(Spacer(1, 15))

    # Introduction
    story.append(Paragraph("Introduction", section_style))
    story.append(Paragraph(content["introduction"].strip(), styles['Normal']))
    story.append(Spacer(1, 15))

    # Methods
    story.append(Paragraph("Methods", section_style))
    story.append(Paragraph(content["methods"].strip(), styles['Normal']))
    story.append(Spacer(1, 15))

    # Results
    story.append(Paragraph("Results", section_style))
    story.append(Paragraph(content["results"].strip(), styles['Normal']))
    story.append(Spacer(1, 15))

    # Discussion
    story.append(Paragraph("Discussion", section_style))
    story.append(Paragraph(content["discussion"].strip(), styles['Normal']))
    story.append(Spacer(1, 15))

    # References
    story.append(Paragraph("References", section_style))
    story.append(Paragraph(content["references"].strip(), styles['Normal']))

    # Build PDF
    doc.build(story)

    print(f"✅ Sample PDF manuscript created: {filepath}")
    return filepath

if __name__ == "__main__":
    try:
        create_sample_pdf()
    except ImportError:
        print("❌ reportlab not installed. Install with: pip install reportlab")
        print("Creating text file instead...")

        # Fallback: create a text file
        content = """# Novel Deep Learning Approach for Image Classification

## Abstract
This paper presents a novel deep learning approach for image classification...

## Introduction
Image classification is a fundamental task in computer vision...

## Methods
We propose a novel architecture that integrates attention mechanisms...

## Results
Our experimental results show that the proposed method achieves 95.2% accuracy...

## Discussion
The results indicate that attention mechanisms can significantly improve...

## References
[1] Smith, J. et al. Deep learning for image classification. Nature 2020...
"""

        with open("sample_manuscript.txt", "w") as f:
            f.write(content)
        print("✅ Sample text manuscript created: sample_manuscript.txt")