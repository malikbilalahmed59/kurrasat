import os
import re
import openai
from django.conf import settings
from pathlib import Path
from docx import Document
import pdfplumber
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document as LangchainDocument
# Build vector store from PDF files in knowledge directory
import hashlib
import pickle
import time
from datetime import datetime
import json
# Ensure OpenAI API key is set
openai.api_key = settings.OPENAI_API_KEY
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY


# 🔹 Function to fix Arabic text
def fix_arabic_text(text):
    """Fix the direction of Arabic text extracted from PDF."""
    return text[::-1]


# 🔹 Improved function to clean Arabic text
def clean_arabic_text(text):
    """Clean and fix Arabic text extracted from PDF."""
    if not text or not isinstance(text, str):
        return ""

    # Remove invisible characters and control codes
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)

    # Remove ZERO WIDTH NON-JOINER and ZERO WIDTH JOINER
    text = re.sub(r'[\u200C\u200D]', '', text)

    # Standardize hamzas and alef forms
    text = re.sub(r'[إأآا]', 'ا', text)
    text = re.sub(r'[ىی]', 'ي', text)
    text = re.sub(r'ة', 'ه', text)

    # Remove diacritics
    text = re.sub(r'[\u0617-\u061A\u064B-\u0652]', '', text)

    # Clean repeated punctuation
    text = re.sub(r'([.،؛؟!:])\1+', r'\1', text)

    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)

    # Fix numbers mixed with Arabic text
    text = re.sub(r'(\d+)([ا-ي])', r'\1 \2', text)
    text = re.sub(r'([ا-ي])(\d+)', r'\1 \2', text)

    # Fix Latin characters mixed with Arabic
    text = re.sub(r'([a-zA-Z])([ا-ي])', r'\1 \2', text)
    text = re.sub(r'([ا-ي])([a-zA-Z])', r'\1 \2', text)

    # Remove spaces at the beginning and end of the text
    text = text.strip()

    return text


# Helper function to save the RFP to a Word document
def save_rfp_sections_to_word(sections, output_path):
    """
    Save the RFP sections to a Word document with proper RTL formatting.

    Args:
        sections: List of tuples (section_title, section_content)
        output_path: Full path to save the document
    """
    from docx import Document
    from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_LINE_SPACING
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.shared import Pt, RGBColor, Inches
    import re
    import os

    # Create a new Document
    document = Document()

    # Configure document for RTL
    for section in document.sections:
        section.page_width, section.page_height = section.page_height, section.page_width

    # Add title
    title = document.add_heading('كراسة شروط مشروع', 0)
    title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    # Define heading styles
    styles = document.styles

    # Configure default paragraph style for RTL
    style = styles['Normal']
    style.font.rtl = True
    style.font.size = Pt(12)
    style.font.name = 'Traditional Arabic'
    style.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

    # Configure heading styles
    for level in range(1, 5):
        style_name = f'Heading {level}'
        if style_name in styles:
            style = styles[style_name]
            style.font.rtl = True
            style.font.name = 'Traditional Arabic'
            style.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

    # Process each section
    for section_title, section_content in sections:
        # Add section heading
        heading = document.add_heading(section_title, level=1)
        heading.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

        # Process content by lines
        lines = section_content.split('\n')
        current_paragraph = None
        in_table = False
        table_rows = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # Handle table rows
            if '|' in line and '-|-' not in line and not line.strip().startswith('|'):
                if not in_table:
                    in_table = True
                    table_rows = []

                # Extract cells from the table row
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                table_rows.append(cells)
                i += 1
                continue

            # If we were in a table and now we're not, create the table
            if in_table and ('|' not in line or not line.strip()):
                in_table = False

                if table_rows:
                    # Create table
                    if len(table_rows) > 0:
                        num_cols = max(len(row) for row in table_rows)
                        table = document.add_table(rows=len(table_rows), cols=num_cols)
                        table.style = 'Table Grid'
                        table.alignment = WD_TABLE_ALIGNMENT.RIGHT

                        # Fill the table
                        for row_idx, row_cells in enumerate(table_rows):
                            for col_idx, cell_text in enumerate(row_cells):
                                cell = table.cell(row_idx, col_idx)
                                p = cell.paragraphs[0]
                                p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
                                run = p.add_run(cell_text)
                                run.font.rtl = True

                    # Add empty paragraph after table
                    document.add_paragraph()

            # Handle headings with # symbols (Markdown headings)
            elif line.strip().startswith('#'):
                heading_level = len(re.match(r'^(#+)', line.strip()).group(1))
                heading_text = line.strip()[heading_level:].strip()

                if heading_level <= 4:  # Only support heading levels 1-4
                    h = document.add_heading(heading_text, level=heading_level)
                    h.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
                else:
                    # For deeper levels, create a paragraph with bold text
                    p = document.add_paragraph()
                    p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
                    run = p.add_run(heading_text)
                    run.bold = True
                    run.font.rtl = True

            # Handle bullet points
            elif line.strip().startswith('•') or line.strip().startswith('-') or line.strip().startswith('*'):
                # Create a normal paragraph with custom formatting instead of using List Bullet style
                p = document.add_paragraph()
                p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
                p.paragraph_format.right_indent = Pt(0)
                p.paragraph_format.left_indent = Pt(12)

                # Set RTL for paragraph
                try:
                    p._element.get_or_add_pPr().set('bidi', '1')
                except:
                    pass

                # Get the text after the bullet
                text = line.strip()[1:].strip()

                # Add manual bullet in RTL
                run = p.add_run('• ')
                run.font.rtl = True
                run.font.name = 'Traditional Arabic'

                # Replace markdown bold with actual bold
                text_parts = re.split(r'(\*\*.*?\*\*)', text)
                for part in text_parts:
                    if part.startswith('**') and part.endswith('**'):
                        # Add bold text
                        run = p.add_run(part[2:-2])
                        run.bold = True
                        run.font.rtl = True
                        run.font.name = 'Traditional Arabic'
                    else:
                        # Add normal text
                        run = p.add_run(part)
                        run.font.rtl = True
                        run.font.name = 'Traditional Arabic'

            # Handle numbered lists
            elif re.match(r'^\d+\.\s', line.strip()):
                # Create a normal paragraph with custom formatting instead of using List Number style
                p = document.add_paragraph()
                p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
                p.paragraph_format.right_indent = Pt(0)
                p.paragraph_format.left_indent = Pt(12)

                # Set RTL for paragraph
                try:
                    p._element.get_or_add_pPr().set('bidi', '1')
                except:
                    pass

                # Get the number from original text
                number_match = re.match(r'^(\d+)\.', line.strip())
                number = number_match.group(1) if number_match else "1"

                # Add manual number in RTL
                run = p.add_run(f"{number}. ")
                run.font.rtl = True
                run.font.name = 'Traditional Arabic'

                # Get the text after the number
                text = re.sub(r'^\d+\.\s', '', line.strip())

                # Replace markdown bold with actual bold
                text_parts = re.split(r'(\*\*.*?\*\*)', text)
                for part in text_parts:
                    if part.startswith('**') and part.endswith('**'):
                        # Add bold text
                        run = p.add_run(part[2:-2])
                        run.bold = True
                        run.font.rtl = True
                        run.font.name = 'Traditional Arabic'
                    else:
                        # Add normal text
                        run = p.add_run(part)
                        run.font.rtl = True
                        run.font.name = 'Traditional Arabic'

            # Regular paragraph
            else:
                # Skip empty lines
                if not line.strip():
                    current_paragraph = None
                    i += 1
                    continue

                # Start a new paragraph for non-empty lines
                if current_paragraph is None:
                    current_paragraph = document.add_paragraph()
                    current_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
                    current_paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

                # Replace markdown bold with actual bold
                text_parts = re.split(r'(\*\*.*?\*\*)', line)
                for part in text_parts:
                    if part.startswith('**') and part.endswith('**'):
                        # Add bold text
                        run = current_paragraph.add_run(part[2:-2])
                        run.bold = True
                        run.font.rtl = True
                    else:
                        # Add normal text
                        run = current_paragraph.add_run(part)
                        run.font.rtl = True

            i += 1

    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save the document
    document.save(output_path)
    return output_path




def build_vector_store(knowledge_dir):
    """
    Process PDF files in the knowledge directory and build a vector store.
    Uses caching to avoid rebuilding if files haven't changed.

    Args:
        knowledge_dir: Directory containing the RFP PDF files

    Returns:
        FAISS vector store object
    """
    cache_dir = os.path.join(knowledge_dir, ".cache")
    os.makedirs(cache_dir, exist_ok=True)

    # Create a hash of the PDF files to check if they've changed
    pdf_files = [os.path.join(knowledge_dir, f) for f in os.listdir(knowledge_dir) if f.endswith('.pdf')]
    pdf_files.sort()  # Ensure consistent ordering

    # Get modification times and file sizes for hash
    file_metadata = []
    for pdf_file in pdf_files:
        file_stat = os.stat(pdf_file)
        file_metadata.append((pdf_file, file_stat.st_mtime, file_stat.st_size))

    # Create a hash of the file metadata
    metadata_str = str(file_metadata).encode('utf-8')
    files_hash = hashlib.md5(metadata_str).hexdigest()

    # Check if we have a cached vector store for this hash
    vector_store_path = os.path.join(cache_dir, f"vector_store_{files_hash}")
    metadata_path = os.path.join(cache_dir, f"metadata_{files_hash}.json")

    # If cache exists, load it
    if os.path.exists(vector_store_path) and os.path.exists(metadata_path):
        try:
            print(f"⏳ Loading vector store from cache...")
            vector_store = FAISS.load_local(
                vector_store_path,
                OpenAIEmbeddings(model='text-embedding-ada-002'),
                allow_dangerous_deserialization=True  # Add this parameter
            )

            # Read metadata (optional, could be useful for debugging)
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                cached_time = metadata.get('time', 'unknown')
                print(f"✅ Using cached vector store from {cached_time}")

            return vector_store

        except Exception as e:
            print(f"⚠️ Error loading cached vector store: {str(e)}")
            print("Rebuilding vector store...")
            # Continue with rebuilding if loading failed

    print(f"🔹 Building new vector store from {len(pdf_files)} PDF files...")

    # The rest of the original function to build vector store
    all_chunks = []
    all_metadata = []
    section_pattern = re.compile(r"^\s*(\d+\..+|[أ-ي]+[.)].+)$", re.MULTILINE)

    for file_index, file in enumerate(pdf_files):
        rfp_name = os.path.basename(file).replace('.pdf', '')
        text = ""

        try:
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    extracted_text = page.extract_text()
                    if extracted_text:
                        text += fix_arabic_text(extracted_text) + "\n"

            if text.strip():
                sections = section_pattern.split(text)
                rfp_text = ""

                for section in sections:
                    section = section.strip()
                    if section:
                        rfp_text += f"{section}\n\n"

                text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50, length_function=len)
                rfp_chunks = text_splitter.split_text(rfp_text)

                for chunk in rfp_chunks:
                    all_chunks.append(chunk)
                    all_metadata.append({"source": rfp_name, "file_path": file})

                print(f"Processed file {file} and extracted {len(rfp_chunks)} chunks.")
        except Exception as e:
            print(f"Error processing {file}: {str(e)}")

    documents = [LangchainDocument(page_content=chunk, metadata=metadata)
                 for chunk, metadata in zip(all_chunks, all_metadata)]

    print(f"Created {len(documents)} documents from all RFPs.")

    if documents:
        embeddings = OpenAIEmbeddings(model='text-embedding-ada-002')
        vector_store = FAISS.from_documents(documents, embedding=embeddings)

        # Save the vector store and metadata
        try:
            vector_store.save_local(vector_store_path)

            # Save metadata about the cache
            metadata = {
                'hash': files_hash,
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'num_documents': len(documents),
                'files': [os.path.basename(f) for f in pdf_files]
            }

            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            print(f"✅ Vector store cached successfully for future use")
        except Exception as e:
            print(f"⚠️ Error caching vector store: {str(e)}")

        return vector_store
    else:
        print("No documents created. Vector store initialization failed.")
        return None

# Section generation functions
def generate_rfp_intro(llm, example_rfp, competition_name, competition_objectives, competition_description):
    prompt = f"""
        اكتب القسم الأول فقط من كراسة شروط مشروع بعنوان "{competition_name}" بهدف "{competition_objectives}" في مجال "{competition_description}". هذا القسم هو: المقدمة.

        يجب أن يشمل بالتفصيل:
        - فقرة تعريفية تفصيلية تشرح جميع المصطلحات الفنية المرتبطة بموضوع المشروع، بما في ذلك:
          الجهة الحكومية، المتنافس، المنافسة، النظام، اللائحة التنفيذية، المصطلحات الأخرى المتعلقة بالمنافسة.
        - التعريفات الرسمية لكل المصطلحات المستخدمة في الكراسة كنقاط كتابه المصطلح وتعريفه.
        - خلفية المشروع بشكل مفصل.
        - نطاق الأعمال مع تقسيمه إلى مراحل واضحة.
        - المعايير العامة التي يجب الالتزام بها.
        - أهداف المنافسة بالتفصيل.
        - الجدول الزمني المتوقع وخطة التنفيذ العامة.

        ويجب تضمين الجداول الآتية:
        1. تكاليف وثائق المنافسة:
        | القيمة بالأرقام (… ريال سعودي) | القيمة بالتفقيط | آلية الدفع (شيك مصدق / حوالة بنكية / نظام سداد) |

        2. أهلية مقدمي العروض:
        تحديد الشروط والمعايير التي يجب أن تتوافر في المتنافسين ليكونوا مؤهلين لتقديم العروض، مثل السجلات التجارية والتراخيص اللازمة.

        3. السجلات والتراخيص النظامية:
        بيان الوثائق المطلوبة من المتنافسين مثل السجل التجاري، شهادة الزكاة، شهادة التأمينات الاجتماعية وغيرها.

        4. ممثل الجهة الحكومية:
        | الاسم | الوظيفة | الهاتف | الفاكس | البريد الإلكتروني |

        5. مكان التسليم:
        | العنوان | المبنى | الطابق | الغرفة / اسم الإدارة | وقت التسليم |

        6. نظام المنافسة:
        إشارة إلى النظام واللائحة التنفيذية التي تحكم المنافسة وأي تعليمات قانونية أو تنظيمية.

        ملاحظات هامة للتنسيق:
        - لا تستخدم أبدًا علامة # للعناوين، بل استخدم العناوين بشكل عادي.
        - لا تستخدم علامة ** للنص العريض، اكتب النص بشكل عادي.
        - استخدم الترقيم العادي للقوائم المرقمة (1. 2. 3.).
        - استخدم النقاط العادية للقوائم غير المرقمة (•).
        - ضع الجداول بصيغة عادية باستخدام | بين الأعمدة.

        التعليمات:
        - اكتب ما لا يقل عن 2000 إلى 3000 كلمة.
        - استخدم لغة عربية فصحى رسمية خالية من الأخطاء.
        - اجعل المحتوى مترابطًا ومنطقيًا وطويلًا.
        """
    response = llm.predict(prompt)
    return response


def generate_rfp_general_terms(llm, example_rfp):
    prompt = """
        اكتب القسم الثاني من كراسة الشروط: الأحكام العامة.

        يشمل بالتفصيل:
        1. المساواة والشفافية
        • التعريف:
        توضيح التزام الجهة الحكومية بإتاحة المعلومات بشكل متساوٍ لجميع المتنافسين، لضمان الشفافية والعدالة في تقييم العروض.
        • الالتزامات:
        • توفير المعلومات الضرورية عن المشروع لجميع المتنافسين.
        • إشعار المتنافسين بأي تغييرات تطرأ على المنافسة عبر القنوات الرسمية (البوابة الإلكترونية أو البريد الرسمي).

        2. تعارض المصالح
        • التعريف:
        تحديد معايير تعارض المصالح التي تمنع المتنافسين أو موظفي الجهة الحكومية من الاشتراك في المنافسة في حالة وجود تعارض مباشر أو غير مباشر.
        • الالتزامات:
        • الإفصاح عن أي حالات تعارض مصالح من قبل المتنافسين.
        • الامتناع عن التعاقد مع الأطراف التي لديها تعارض مصالح.

        3. السلوكيات والأخلاقيات
        • التعريف:
        التأكيد على التزام جميع المتنافسين بمعايير السلوك المهني والأخلاقيات في جميع مراحل المنافسة.
        • الالتزامات:
        • عدم تقديم أو قبول أي هدايا أو ميزات خاصة للحصول على معاملة تفضيلية.
        • احترام الشروط والأحكام الموضوعة من قبل الجهة الحكومية.

        4. السرية وإفشاء المعلومات
        • التعريف:
        حماية المعلومات السرية المتعلقة بالمنافسة، وعدم إفشاء أي معلومات تخص العروض أو تفاصيل المنافسة.
        • الالتزامات:
        • عدم نشر أو مشاركة المعلومات السرية مع أطراف أخرى.
        • احترام سياسات الأمان والخصوصية المعتمدة.

        5. ملكية وثائق المنافسة
        • التعريف:
        التأكيد على أن وثائق المنافسة وجميع محتوياتها هي ملك للجهة الحكومية ولا يجوز إعادة استخدامها أو نشرها بدون إذن.
        • الالتزامات:
        • إعادة الوثائق عند طلب الجهة الحكومية.
        • عدم نسخ أو توزيع الوثائق بدون إذن كتابي.

        6. حقوق الملكية الفكرية
        • التعريف:
        حماية حقوق الملكية الفكرية للمعلومات والوثائق المستخدمة في المنافسة.
        • الالتزامات:
        • الالتزام بعدم انتهاك حقوق الملكية الفكرية لأي طرف ثالث.
        • إحالة حقوق الملكية الفكرية للجهة الحكومية عند الترسية.

        7. المحتوى المحلي
        • التعريف:
        تشجيع المحتوى المحلي والمنتجات الوطنية في تنفيذ المشاريع والمشتريات.
        • الالتزامات:
        • الالتزام بمتطلبات المحتوى المحلي في العقود.
        • إعطاء الأفضلية للمنتجات الوطنية عند التساوي في العروض.

        8. أنظمة وأحكام الاستيراد
        • التعريف:
        الالتزام بجميع القوانين والأنظمة المتعلقة بالاستيراد في المملكة العربية السعودية.
        • الالتزامات:
        • التقيد بالأحكام الجمركية والتنظيمات التجارية المعمول بها في المملكة.
        • الالتزام بمنع استيراد المنتجات المحظورة.

        9. تجزئة المنافسة
        • التعريف:
        إمكانية تقسيم المنافسة إلى أجزاء متعددة حسب حاجة الجهة الحكومية.
        • الالتزامات:
        • قبول التجزئة في حال قررت الجهة الحكومية ذلك.
        • تنفيذ الجزء المخصص بكل تفاصيله وشروطه.

        10. الاستبعاد من المنافسة
        • التعريف:
        تحديد الحالات التي يجوز فيها استبعاد المتنافسين من المنافسة.
        • الحالات:
        • مخالفة شروط المنافسة.
        • عدم تقديم الوثائق المطلوبة.
        • التورط في ممارسات غير قانونية أو غير أخلاقية.

        11. إلغاء المنافسة وأثره
        • التعريف:
        الحالات التي يمكن للجهة الحكومية فيها إلغاء المنافسة بشكل كامل.
        • الالتزامات:
        • إرجاع تكاليف وثائق المنافسة للمتنافسين عند الإلغاء لأسباب جوهرية.
        • عدم مطالبة الجهة الحكومية بأي تعويض في حالة الإلغاء.

        12. التفاوض مع أصحاب العروض
        • التعريف:
        توضيح إمكانية التفاوض مع المتنافسين في حالات معينة مثل زيادة الأسعار عن السوق.
        • الالتزامات:
        • تقديم تفاصيل واضحة حول أسباب التفاوض.
        • توثيق عمليات التفاوض بشكل كامل.

        ملاحظات هامة للتنسيق:
        - لا تستخدم أبدًا علامة # للعناوين، بل استخدم العناوين بشكل عادي.
        - لا تستخدم علامة ** للنص العريض، اكتب النص بشكل عادي.
        - استخدم الترقيم العادي للقوائم المرقمة (1. 2. 3.).
        - استخدم النقاط العادية للقوائم غير المرقمة (•).
        - ضع الجداول بصيغة عادية باستخدام | بين الأعمدة.

        التعليمات:
        - اكتب 2000–3000 كلمة.
        - استخدم لغة رسمية، واضحة، طويلة ومترابطة.
        """
    response = llm.predict(prompt)
    return response


def generate_rfp_offer_preparation(llm, example_rfp):
    prompt = """
       اكتب القسم الثالث من كراسة الشروط: إعداد العروض.

       بالتفصيل:
       - تأكيد المشاركة.
       - اللغة الرسمية.
       - العملة الرسمية.
       - مدة صلاحية العروض.
       - التكاليف والمسؤوليات.
       - دقة المعلومات.
       - مكونات العرض.
       - الجداول الرسمية.

       ملاحظات هامة للتنسيق:
       - لا تستخدم أبدًا علامة # للعناوين، بل استخدم العناوين بشكل عادي.
       - لا تستخدم علامة ** للنص العريض، اكتب النص بشكل عادي.
       - استخدم الترقيم العادي للقوائم المرقمة (1. 2. 3.).
       - استخدم النقاط العادية للقوائم غير المرقمة (•).
       - ضع الجداول بصيغة عادية باستخدام | بين الأعمدة.

       التعليمات:
       - اكتب 2000–3000 كلمة.
       - استخدم لغة رسمية، طويلة ومفصلة.
       """
    response = llm.predict(prompt)
    return response


def generate_rfp_offer_submission(llm, example_rfp):
    prompt = """
       اكتب القسم الرابع من كراسة الشروط: تقديم العروض.

       يشمل بالتفصيل:
       1. لغة العرض
       • التعريف:
       يجب تقديم العروض باللغة العربية، مع إمكانية تقديم بعض الوثائق أو جزء من العرض بلغة أخرى.
       • في حال وجود تعارض بين النص العربي والنص الأجنبي، يُعتمد النص العربي.

       2. العملة المعتمدة
       • التعريف:
       جميع التعاملات المالية المتعلقة بالمنافسة يجب أن تكون بالريال السعودي.
       • الصرف يتم طبقاً للأنظمة واللوائح المالية المعمول بها في المملكة العربية السعودية.

       3. صلاحية العروض
       • التعريف:
       يجب أن تكون العروض المقدمة صالحة لفترة لا تقل عن (عدد الأيام المحددة من الجهة الحكومية) من تاريخ فتح المظاريف.
       • لا يجوز سحب العروض أو تعديلها خلال هذه الفترة إلا بعد موافقة الجهة الحكومية.

       4. تكلفة إعداد العروض
       • التعريف:
       يتحمل المتنافسون جميع التكاليف المترتبة على إعداد العروض، بما في ذلك:
       • إعداد الوثائق.
       • تقديم المعلومات الإضافية المطلوبة.
       • الاجتماعات والمقابلات اللازمة لتوضيح العروض.
       • الجهة الحكومية غير مسؤولة عن أي تكاليف إضافية متعلقة بإعداد العروض.

       5. الإخطارات والمراسلات
       • التعريف:
       تعد البوابة الإلكترونية (أو الوسيلة البديلة المحددة) هي الوسيلة المعتمدة للإخطارات والمراسلات.
       • في حال تعذّر استخدام البوابة، يتم التواصل مع ممثل الجهة الحكومية المحدد في الكراسة.

       6. ضمان المعلومات
       • التعريف:
       يلتزم المتنافس باتخاذ كافة الإجراءات اللازمة للتحقق من دقة المعلومات في العرض المقدم، والتأكد من توافقه مع المتطلبات الفنية والشروط العامة للمنافسة.
       • الجهة الحكومية غير مسؤولة عن أي أخطاء أو معلومات غير دقيقة في العرض.

       7. الأسئلة والاستفسارات
       • التعريف:
       يمكن للمتنافسين إرسال استفساراتهم عبر البوابة الإلكترونية (أو الوسيلة البديلة) خلال مدة (تحددها الجهة الحكومية) من تاريخ طرح المنافسة.
       • الجهة الحكومية ملزمة بالرد على الاستفسارات خلال مدة (تحددها الجهة الحكومية).
       • جميع الاستفسارات والأجوبة تُنشر لكافة المتنافسين للحفاظ على الشفافية.

       8. حصول المتنافسين على كافة المعلومات الضرورية وزيارة موقع الأعمال
       • التعريف:
       يجب على المتنافسين الاطلاع على جميع المعلومات الضرورية، وزيارة موقع المشروع في حال تطلب ذلك، للتحقق من تفاصيل العمل والموقع.
       • يتم التنسيق مع ممثل الجهة الحكومية لزيارة الموقع.

       9. وثائق العرض الفني
       • التعريف:
       يتعين على المتنافس تقديم العرض الفني الذي يشمل:
       • منهجية الإنجاز.
       • الجدول الزمني للتنفيذ.
       • الخبرات السابقة.
       • فريق العمل.
       • نسبة المحتوى المحلي المستهدفة (إن وجد).

       10. وثائق العرض المالي
       • التعريف:
       يشمل العرض المالي المتطلبات التالية:
       • جدول الكميات والأسعار.
       • جدول الدفعات.
       • الضمان الابتدائي.

       11. كتابة الأسعار
       • التعريف:
       يجب على المتنافس:
       • كتابة الأسعار بشكل واضح ومفصل.
       • عدم إجراء أي تعديلات أو شطب على الأسعار بعد التقديم.
       • تسعير كل بند على حدة وعدم ترك أي بند بدون تسعير، إلا إذا كانت شروط المنافسة تسمح بذلك.
       • الالتزام بجداول الكميات المقدمة من الجهة الحكومية.

       12. جدول الدفعات
       • التعريف:
       يجب تقديم جدول مفصل للدفعات يوضح مراحل السداد وقيمتها ونسبتها من قيمة العرض.
       • يمكن للجهة الحكومية طلب تعديلات على الجدول إذا رأت ذلك مناسباً.

       13. الضرائب والرسوم
       • التعريف:
       يجب أن تشمل الأسعار المقدمة جميع الرسوم والضرائب وأي مصاريف إضافية.
       • الجهة الحكومية غير مسؤولة عن أي مصاريف إضافية لم يتم ذكرها في العرض.

       14. الأحكام العامة للضمانات
       • التعريف:
       يتعين على المتنافس تقديم الضمانات المطلوبة وفقًا للشروط التالية:
       • يمكن تقديم الضمان من خلال بنوك محلية أو أجنبية عبر بنوك وسيطة معتمدة.
       • يجب أن يكون الضمان غير مشروط وواجب السداد عند الطلب.
       • لا يفرج عن الضمان إلا بعد تقديم ضمان بديل أو الانتهاء من التزامات المشروع.

       ملاحظات هامة للتنسيق:
       - لا تستخدم أبدًا علامة # للعناوين، بل استخدم العناوين بشكل عادي.
       - لا تستخدم علامة ** للنص العريض، اكتب النص بشكل عادي.
       - استخدم الترقيم العادي للقوائم المرقمة (1. 2. 3.).
       - استخدم النقاط العادية للقوائم غير المرقمة (•).
       - ضع الجداول بصيغة عادية باستخدام | بين الأعمدة.

       التعليمات:
       - اكتب 2000–3000 كلمة.
       - استخدم لغة رسمية ومفصلة وطويلة ومترابطة.
       """
    response = llm.predict(prompt)
    return response


def generate_rfp_offer_analysis(llm, example_rfp):
    prompt = """
        اكتب القسم الخامس من كراسة الشروط: تقييم العروض.

        هذا الفصل يوضح الإجراءات والمعايير التي تعتمدها الجهة الحكومية لتقييم العروض الفنية والمالية المقدمة من المتنافسين، بهدف اختيار العرض الأنسب وفقًا للشروط والمعايير المحددة في كراسة الشروط والمواصفات.

        1. سرية تقييم العروض
        • التعريف:
        تلتزم الجهة الحكومية بالحفاظ على سرية تقييم العروض وعدم إفشاء أي معلومات تتعلق بمحتويات العروض أو تفاصيل التقييم لأي جهة غير مخولة.
        • إجراءات السرية:
        • جميع أعضاء لجنة التقييم يوقعون على تعهد بالحفاظ على السرية.
        • لا يحق لأي عضو في اللجنة مناقشة محتويات العروض مع أي طرف خارجي.
        • يتم الاحتفاظ بكافة المستندات المتعلقة بالتقييم في مكان آمن.

        2. معايير تقييم العروض
        • التعريف:
        يتم تحديد معايير تقييم العروض في كراسة الشروط والمواصفات، وتتم عملية التقييم بناءً على النقاط التالية:
        • التقييم الفني:
        • منهجية التنفيذ، الخبرات السابقة، فريق العمل، نسبة المحتوى المحلي، الجدول الزمني للتنفيذ.
        • التقييم المالي:
        • قيمة العرض المالي، جداول الكميات والتكاليف، الالتزام بالميزانية المحددة.
        • آلية التقييم:
        • تمنح النقاط لكل معيار حسب درجة الاستجابة للمتطلبات.
        • يحتسب مجموع النقاط لتحديد الترتيب النهائي للمتنافسين.

        3. تصحيح العروض
        • التعريف:
        تقوم لجنة فحص العروض بمراجعة جداول الكميات والأسعار وتصحيح أي أخطاء حسابية قد تظهر في العرض.
        • إجراءات التصحيح:
        • في حال وجود اختلاف بين السعر المكتوب بالأرقام والمكتوب كتابة، يُعتمد السعر المكتوب كتابة.
        • يتم تصحيح العمليات الحسابية مع إشعار المتنافس بالأخطاء المكتشفة.
        • إذا كانت نسبة الخطأ تتجاوز 10% من قيمة العرض، يتم استبعاده من المنافسة.

        4. فحص العروض
        • التعريف:
        تقوم لجنة فحص العروض بمراجعة جميع المستندات والتحقق من استيفاء المتطلبات والشروط العامة والخاصة.
        • إجراءات الفحص:
        • التأكد من صحة الوثائق المقدمة (السجل التجاري، الشهادات، الضمانات، إلخ).
        • مطابقة العروض مع الشروط والمتطلبات الفنية.
        • التحقق من الجداول المالية والتكاليف المدرجة.
        • في حال وجود نقص في الوثائق، يمكن منح المتنافس فترة (تحددها الجهة الحكومية) لاستكمالها، وإلا يستبعد من المنافسة.

        5. الإعلان عن نتائج المنافسة
        • التعريف:
        بعد الانتهاء من التقييم، يتم إعلان نتائج المنافسة لجميع المتنافسين عبر الوسائل الرسمية.
        • إجراءات الإعلان:
        • نشر أسماء المتنافسين الفائزين وقيمة العروض المقبولة عبر البوابة الإلكترونية أو الوسيلة المعتمدة.
        • إخطار جميع المتنافسين بنتائج التقييم مع إتاحة فرصة لتقديم الاعتراضات خلال فترة محددة.

        6. فترة التوقف (Standstill Period)
        • التعريف:
        هي الفترة التي تسبق توقيع العقد وتتيح للمتنافسين الذين لم تتم ترسيتهم فرصة الاعتراض على نتائج التقييم.
        • إجراءات التوقف:
        • تمتد فترة التوقف لمدة (عدد الأيام المحدد من الجهة الحكومية).
        • يُسمح خلالها للمتنافسين بطلب مراجعة نتائج التقييم وتقديم استفساراتهم.
        • يتم الرد على جميع الاستفسارات بشكل واضح ومكتوب خلال الفترة المحددة.

        7. الاستبعاد من التقييم
        • التعريف:
        يحق للجهة الحكومية استبعاد العروض في الحالات التالية:
        • عدم الالتزام بالشروط العامة أو الخاصة.
        • عدم استكمال الوثائق المطلوبة في المدة المحددة.
        • وجود مغالاة أو تدنٍّ غير مبرر في الأسعار المقدمة.
        • عدم الالتزام بالجدول الزمني أو شروط التنفيذ.

        8. التفاوض مع أصحاب العروض
        • التعريف:
        يحق للجهة الحكومية التفاوض مع أصحاب العروض الأفضل من حيث التقييم المالي أو الفني، في حال كانت الأسعار غير مناسبة أو توجد ملاحظات على خطة التنفيذ.
        • إجراءات التفاوض:
        • توثيق جميع المراسلات والنقاشات خلال التفاوض.
        • الالتزام بالمعايير والشروط الموضحة في الكراسة.
        • عدم تعديل الشروط الأساسية للمنافسة دون موافقة جميع الأطراف.

        ملاحظات هامة للتنسيق:
        - لا تستخدم أبدًا علامة # للعناوين، بل استخدم العناوين بشكل عادي.
        - لا تستخدم علامة ** للنص العريض، اكتب النص بشكل عادي.
        - استخدم الترقيم العادي للقوائم المرقمة (1. 2. 3.).
        - استخدم النقاط العادية للقوائم غير المرقمة (•).
        - ضع الجداول بصيغة عادية باستخدام | بين الأعمدة.

        التعليمات:
        - اكتب 2000–3000 كلمة.
        - استخدم لغة رسمية، مترابطة ومفصلة.
        """
    response = llm.predict(prompt)
    return response


def generate_rfp_award_contract(llm, example_rfp):
    prompt = """
        اكتب القسم السادس من كراسة الشروط: متطلبات التعاقد.

        هذا الفصل يحدد الإجراءات والمتطلبات التي يجب اتباعها بعد الترسية وقبل توقيع العقد بين الجهة الحكومية والمتنافس الفائز. يتضمن أيضًا الضمانات المالية اللازمة والشروط المتعلقة بإتمام التعاقد وتنفيذ المشروع.

        1. إخطار الترسية
        • التعريف:
        بعد الانتهاء من عملية التقييم وتحديد الفائز، يتم إصدار إخطار الترسية للفائز بالعقد.
        • يحتوي الإخطار على معلومات التعاقد الأساسية مثل:
        • قيمة العرض.
        • الجدول الزمني للتنفيذ.
        • الشروط والمتطلبات اللازمة لإتمام التعاقد.
        • إجراءات الإخطار:
        • يتم إرسال الإخطار بشكل رسمي عبر القنوات المعتمدة (البوابة الإلكترونية، البريد الإلكتروني، أو البريد الرسمي).
        • يُطلب من الفائز تقديم الوثائق النهائية المطلوبة خلال فترة (عدد الأيام المحدد من الجهة الحكومية).

        2. الضمان النهائي
        • التعريف:
        يتعين على المتنافس الفائز تقديم ضمان نهائي يغطّي نسبة (تحددها الجهة الحكومية) من إجمالي قيمة العقد.
        • يتم تقديم الضمان بشكل بنكي وغير مشروط.
        • يجب أن يكون الضمان النهائي صالحاً لمدة (تحددها الجهة الحكومية) من تاريخ توقيع العقد.
        • إجراءات تقديم الضمان:
        • يتم تسليم الضمان النهائي للجهة الحكومية قبل توقيع العقد.
        • لا يتم الإفراج عن الضمان إلا بعد انتهاء فترة الضمان النهائية للمشروع وتسليم كافة الأعمال المتفق عليها.

        3. توقيع العقد
        • التعريف:
        بعد تقديم الضمان النهائي واستيفاء جميع المتطلبات، يتم توقيع العقد بين الجهة الحكومية والمتنافس الفائز.
        • إجراءات التوقيع:
        • يتم توقيع العقد من قبل ممثل الجهة الحكومية والمقاول أو المورد المعتمد من الشركة.
        • يشمل العقد جميع الشروط والأحكام الموضحة في كراسة الشروط والمواصفات، بالإضافة إلى الجدول الزمني وطرق الدفع.
        • يحتفظ كل طرف بنسخة معتمدة من العقد.

        4. الغرامات
        • التعريف:
        توضح هذه الفقرة الغرامات التي تُفرض في حال عدم التزام المتعاقد بالشروط والجدول الزمني للتنفيذ.
        • أنواع الغرامات:
        1. غرامات التأخير:
        • تفرض غرامة بنسبة (تحددها الجهة الحكومية) عن كل يوم تأخير بعد الموعد المحدد في العقد.
        2. غرامات مخالفة أحكام لائحة تفضيل المحتوى المحلي:
        • في حال عدم الالتزام بالنسبة المحددة للمحتوى المحلي في المشروع.
        3. إجمالي الغرامات:
        • لا يجب أن تتجاوز الغرامات الإجمالية نسبة (تحددها الجهة الحكومية) من قيمة العقد.

        5. التأمين
        • التعريف:
        يتعين على المتعاقد تقديم التأمينات اللازمة التي تضمن حماية المشروع من المخاطر المحتملة أثناء التنفيذ.
        • إجراءات التأمين:
        • يشمل التأمين:
        • تأمين العمالة.
        • تأمين الموقع.
        • تأمين المعدات المستخدمة.
        • يجب أن تكون جميع التأمينات صالحة طوال فترة التنفيذ حتى الاستلام النهائي.

        6. الاستلام الأولي والنهائي
        • التعريف:
        تحدد هذه الفقرة مراحل استلام المشروع بعد التنفيذ:
        • الاستلام الأولي: يتم بعد إنهاء الأعمال الأساسية والتأكد من مطابقة المواصفات الفنية.
        • الاستلام النهائي: يتم بعد انتهاء فترة الضمان ومعالجة جميع الملاحظات.
        • إجراءات الاستلام:
        • تكوين لجنة من الجهة الحكومية لفحص الأعمال المنجزة.
        • توثيق أي ملاحظات أو عيوب، وإلزام المقاول بمعالجتها في فترة زمنية محددة.
        • إصدار شهادة إتمام المشروع عند التأكد من تنفيذ كافة المتطلبات.

        7. التعديلات والتغييرات
        • التعريف:
        يمكن للجهة الحكومية طلب تعديلات أو تغييرات على نطاق العمل أو الجدول الزمني، حسب الحاجة.
        • إجراءات التعديل:
        • يتم التعديل باتفاق مشترك بين الجهة الحكومية والمتعاقد.
        • يتم توثيق التعديلات في ملحقات رسمية موقعة من الطرفين.
        • في حالة التغيير في الكميات أو النطاق، يتم تعديل التكلفة وجدول الدفعات بناءً على ذلك.

        ملاحظات هامة للتنسيق:
        - لا تستخدم أبدًا علامة # للعناوين، بل استخدم العناوين بشكل عادي.
        - لا تستخدم علامة ** للنص العريض، اكتب النص بشكل عادي.
        - استخدم الترقيم العادي للقوائم المرقمة (1. 2. 3.).
        - استخدم النقاط العادية للقوائم غير المرقمة (•).
        - ضع الجداول بصيغة عادية باستخدام | بين الأعمدة.

        التعليمات:
        - اكتب 2000–3000 كلمة.
        - استخدم لغة رسمية، مترابطة وطويلة.
        """
    response = llm.predict(prompt)
    return response


def generate_rfp_guarantees(llm, example_rfp):
    prompt = """
        اكتب القسم السابع من كراسة الشروط: نطاق العمل المفصل.

        هذا الفصل يوضح تفاصيل نطاق العمل الذي يتعين على المتعاقد تنفيذه، بما في ذلك المتطلبات الفنية، الجدول الزمني، موقع التنفيذ، والتدريب ونقل المعرفة عند الحاجة. يتم تنظيم هذا الفصل بطريقة واضحة ومفرغة ليسهل على الجهة الحكومية والمتعاقد تعبئتها وفقًا لمتطلبات المشروع.

        1. نطاق عمل المشروع
        • التعريف:
        يوضح هذا البند كافة التفاصيل المتعلقة بالأعمال المطلوبة، بما في ذلك الخدمات أو المنتجات المتفق عليها في العقد.
        • إجراءات التحديد:
        • وصف مفصل لجميع الأعمال المطلوبة، بما في ذلك الخطوات والإجراءات.
        • تحديد المعايير الفنية والمواصفات المطلوبة لكل خدمة أو منتج.
        • توضيح أي متطلبات إضافية خاصة بالمشروع.

        2. برنامج تقديم الخدمات
        • التعريف:
        توضيح الجدول الزمني لتقديم الخدمات المتفق عليها، بما يشمل مواعيد بدء الأعمال ومراحل التنفيذ.
        • إجراءات التخطيط:
        • تحديد تاريخ بدء المشروع وتاريخ الانتهاء المتوقع.
        • تقسيم العمل إلى مراحل واضحة مع تواريخ تسليم لكل مرحلة.
        • توضيح المعايير الزمنية للإنجاز، مع وضع خطة للتعامل مع أي تأخير محتمل.

        3. مكان تنفيذ الخدمات
        • التعريف:
        تحديد الموقع الجغرافي الذي سيتم فيه تنفيذ المشروع، مع توضيح مواقع العمل إذا كانت متعددة.
        • إجراءات التنفيذ:
        • تقديم تفاصيل دقيقة عن الموقع، بما في ذلك العنوان ووسائل الوصول.
        • توضيح مسؤوليات المقاول في إدارة الموقع والمحافظة على السلامة والأمن.
        • الإشارة إلى أي تصاريح أو موافقات مطلوبة للعمل في الموقع.

        4. التدريب ونقل المعرفة
        • التعريف:
        يتضمن هذا البند التدريب الذي سيتم تقديمه للموظفين أو الفرق الفنية لدى الجهة الحكومية، بالإضافة إلى نقل المعرفة لضمان استمرارية المشروع.
        • إجراءات التدريب:
        • تحديد الدورات التدريبية المطلوبة ومواضيعها.
        • تحديد الفئات المستهدفة من التدريب (فنيين، إداريين، مشرفين، إلخ).
        • وضع جدول زمني لورش العمل والدورات التدريبية.
        • تقديم دليل استخدام أو كتيبات تعليمية للمستفيدين.

        5. معايير الجودة والمعاينة
        • التعريف:
        تحديد المعايير التي سيتم اعتمادها في تقييم جودة العمل أثناء التنفيذ وبعد التسليم.
        • إجراءات التقييم:
        • وضع معايير فنية واضحة لكل بند من بنود العمل.
        • إجراء فحص ومعاينة للأعمال المنفذة للتحقق من مطابقتها للمعايير المحددة.
        • توثيق نتائج المعاينة ومتابعة تنفيذ الملاحظات المسجلة.
        • استخدام تقارير متابعة دورية لضمان الالتزام بالجودة.

        ملاحظات هامة للتنسيق:
        - لا تستخدم أبدًا علامة # للعناوين، بل استخدم العناوين بشكل عادي.
        - لا تستخدم علامة ** للنص العريض، اكتب النص بشكل عادي.
        - استخدم الترقيم العادي للقوائم المرقمة (1. 2. 3.).
        - استخدم النقاط العادية للقوائم غير المرقمة (•).
        - ضع الجداول بصيغة عادية باستخدام | بين الأعمدة.

        التعليمات:
        - اكتب 2000–3000 كلمة.
        - استخدم لغة رسمية ومترابطة.
        """
    response = llm.predict(prompt)
    return response


def generate_rfp_specifications(llm, example_rfp):
    prompt = """
    اكتب القسم الثامن من كراسة الشروط: المواصفات الفنية.

    هذا الفصل يوضح المواصفات الفنية المطلوبة لتنفيذ المشروع أو تقديم الخدمات. يشمل هذا الفصل كافة المتطلبات التقنية والمعدات والمواد اللازمة لتحقيق الأهداف المحددة في نطاق العمل، بالإضافة إلى تحديد معايير الجودة والتفاصيل الفنية التي يجب الالتزام بها.

    1. فريق العمل
    • التعريف:
    يحدد هذا البند التكوين الأساسي لفريق العمل المسؤول عن تنفيذ المشروع، بما في ذلك الأدوار والمسؤوليات المطلوبة.
    • إجراءات التحديد:
    • تحديد الوظائف الرئيسية (مدير المشروع، المهندسون، الفنيون، إلخ).
    • تقديم السير الذاتية للكوادر الأساسية (CVs) مع توضيح الخبرات والشهادات المطلوبة.
    • توضيح الهيكل التنظيمي للفريق ومسؤوليات كل فرد.
    • الإشارة إلى متطلبات التأهيل والشهادات المهنية اللازمة.
    • تضمين جدول مواصفات فريق العمل: الأعمدة (الرقم، مسمى الوظيفة، أقل مؤهل للقبول، الحد الأدنى لسنوات الخبرة)، وتعبئته بالتفصيل كما هو في النماذج الرسمية.

    2. الأصناف والمواد
    • التعريف:
    توضح هذه الفقرة جميع المواد والخامات التي سيتم استخدامها في المشروع، مع الالتزام بالمواصفات المحددة من الجهة الحكومية.
    • إجراءات التحديد:
    • إدراج قائمة مفصلة بالأصناف والمواد المطلوبة.
    • تحديد معايير الجودة والمواصفات الفنية لكل صنف.
    • تحديد الموردين المعتمدين للمواد.
    • تقديم شهادات فحص الجودة لكل مادة قبل الاستخدام.
    • تضمين جدول مواصفات المواد: الأعمدة (الرقم، المادة، المواصفات، وحدة القياس)، ويُستكمل حسب المواد المطلوبة.

    3. المعدات
    • التعريف:
    تحدد هذه الفقرة جميع المعدات والآليات التي سيتم استخدامها أثناء تنفيذ المشروع.
    • إجراءات التحديد:
    • تقديم قائمة شاملة بالمعدات المطلوبة للتنفيذ.
    • توضيح حالة المعدات (جديدة، مستعملة، مؤجرة).
    • تحديد معايير الصيانة الدورية والتفتيش الفني.
    • التأكد من توافق المعدات مع معايير السلامة المحلية والدولية.
    • تضمين جدول مواصفات المعدات: الأعمدة (الرقم، الآلة، المواصفات، وحدة القياس)، ويُستكمل حسب المعدات المطلوبة.

    4. كيفية تنفيذ الخدمات
    • التعريف:
    شرح تفصيلي حول كيفية تنفيذ الأعمال والخدمات المطلوبة في المشروع.
    • إجراءات التنفيذ:
    • تحديد الخطوات التفصيلية لتنفيذ كل جزء من المشروع.
    • توضيح طرق العمل ومعايير الأداء المتوقعة.
    • الالتزام بالجدول الزمني المحدد في نطاق العمل.
    • تحديد النقاط المرجعية للتقييم الدوري للتقدم في العمل.

    5. مواصفات الجودة
    • التعريف:
    توضيح معايير الجودة التي يجب اتباعها أثناء تنفيذ المشروع لضمان تحقيق النتائج المطلوبة.
    • إجراءات الجودة:
    • تطبيق معايير الجودة المعتمدة في المملكة العربية السعودية.
    • إجراء اختبارات وفحوصات دورية للتحقق من جودة المواد والمعدات.
    • تقديم تقارير دورية عن نتائج الفحوصات للجهة الحكومية.
    • توثيق أي عيوب أو انحرافات ومعالجتها فورًا.

    6. مواصفات السلامة
    • التعريف:
    تحديد الإجراءات والاحتياطات اللازمة لضمان سلامة العاملين والموقع أثناء تنفيذ المشروع.
    • إجراءات السلامة:
    • توفير معدات الحماية الشخصية (PPE) لجميع العاملين.
    • تطبيق إجراءات السلامة الميدانية (مثل تأمين المناطق الخطرة، لوحات الإرشاد، إلخ).
    • الالتزام بمعايير السلامة المعتمدة محليًا ودوليًا.
    • إعداد خطة طوارئ للتعامل مع الحوادث المحتملة.
    • تدريب العاملين على إجراءات الطوارئ والإخلاء.

    7. الإشراف والمراقبة
    • التعريف:
    وضع آليات للإشراف على تنفيذ الأعمال والمراقبة الدورية للتأكد من الالتزام بالمواصفات الفنية.
    • إجراءات الإشراف:
    • تعيين مشرفين مختصين من الجهة الحكومية لمتابعة تنفيذ المشروع.
    • إجراء زيارات ميدانية دورية لتقييم مستوى التقدم والجودة.
    • إعداد تقارير ميدانية لتوثيق مستوى الأداء والمعايير الفنية.

    8. التسليم والتوثيق
    • التعريف:
    تحديد المعايير والشروط الواجب توفرها عند تسليم المشروع أو الخدمة بعد إتمام التنفيذ.
    • إجراءات التسليم:
    • إعداد قائمة فحص نهائية للمراجعة قبل التسليم.
    • تقديم جميع الوثائق الفنية والفحوصات النهائية عند التسليم.
    • توثيق جميع المراحل النهائية في تقرير معتمد من الجهة الحكومية.
    • التحقق من استيفاء كافة المعايير والمواصفات المطلوبة.

    ملاحظات هامة للتنسيق:
    - لا تستخدم أبدًا علامة # للعناوين، بل استخدم العناوين بشكل عادي.
    - لا تستخدم علامة ** للنص العريض، اكتب النص بشكل عادي.
    - استخدم الترقيم العادي للقوائم المرقمة (1. 2. 3.).
    - استخدم النقاط العادية للقوائم غير المرقمة (•).
    - ضع الجداول بصيغة عادية باستخدام | بين الأعمدة.

    التعليمات:
    - اكتب 2000–3000 كلمة.
    - استخدم لغة رسمية واضحة وطويلة ومترابطة.
    - يجب وصف الجداول الثلاثة بشكل صريح، مع مقدمة لكل منها توضّح أهميته وآلية تعبئته، ومكان إضافته داخل الكراسة.
    """
    response = llm.predict(prompt)
    return response


def generate_rfp_general_contract_terms(llm, example_rfp):
    prompt = """
    اكتب القسم التاسع من كراسة الشروط: متطلبات المحتوى المحلي.

    هذا الفصل يحدد متطلبات المحتوى المحلي التي يجب على المتنافسين الالتزام بها في تنفيذ المشروع، وفقًا لرؤية المملكة 2030 التي تشجع على تعزيز الإنتاج المحلي والاعتماد على الكفاءات الوطنية.

    1. القائمة الإلزامية
    • التعريف:
    تحدد الجهة الحكومية قائمة إلزامية للمواد والمنتجات التي يجب توريدها من السوق المحلي أثناء تنفيذ المشروع.
    • إجراءات التطبيق:
    • إدراج قائمة مفصلة بالمنتجات والخدمات التي يجب توريدها محليًا.
    • التأكيد على الالتزام بالمواصفات والمعايير السعودية.
    • تقديم فواتير وشهادات منشأ تثبت أن المواد المستخدمة محلية الصنع.

    2. تفضيل المنتجات الوطنية
    • التعريف:
    يمنح تفضيل خاص للمنتجات الوطنية عند التقييم المالي للعروض، في حال كانت المنتجات المحلية مطابقة للمواصفات.
    • إجراءات التفضيل:
    • منح نقاط إضافية للعروض التي تتضمن منتجات وطنية.
    • في حال تساوي العروض في القيمة المالية، يتم تفضيل العرض الذي يحتوي على أكبر نسبة من المحتوى المحلي.
    • تطبيق آلية المفاضلة بين المنتجات المحلية والمنتجات المستوردة بناءً على نسبة المحتوى المحلي.

    3. اشتراطات آليات المحتوى المحلي
    • التعريف:
    توضيح النسبة المطلوبة من المحتوى المحلي في المشروع، وكيفية حسابها.
    • إجراءات التطبيق:
    • تحديد النسبة المئوية المطلوبة من المحتوى المحلي في كل مرحلة من مراحل المشروع.
    • تقديم تقارير دورية للجهة الحكومية توضح نسبة الالتزام بالمحتوى المحلي.
    • توثيق الفواتير والشهادات الدالة على توريد المنتجات من مصادر محلية.

    4. مراقبة الالتزام بالمحتوى المحلي
    • التعريف:
    تقوم الجهة الحكومية بمتابعة التزام المتعاقد بنسبة المحتوى المحلي المطلوبة، والتأكد من توريد المواد والخدمات المحلية وفقًا للمعايير.
    • إجراءات المراقبة:
    • إجراء زيارات ميدانية لمواقع العمل للتأكد من استخدام المنتجات المحلية.
    • طلب تقارير شهرية من المتعاقد توضح نسبة المنتجات المحلية المستخدمة.
    • في حال عدم الالتزام، يتم تطبيق غرامات مالية حسب ما هو موضح في كراسة الشروط.

    5. الحوافز والدعم
    • التعريف:
    يمكن للجهة الحكومية تقديم حوافز للمتعاقدين الذين يلتزمون بنسبة عالية من المحتوى المحلي تتجاوز الحد الأدنى المطلوب.
    • إجراءات الحوافز:
    • منح خصومات في رسوم المنافسة للمشاريع التي تحقق نسبة عالية من المحتوى المحلي.
    • إعطاء نقاط إضافية في التقييم النهائي للعرض.
    • منح شهادات تقديرية للشركات الملتزمة.

    6. الاستثناءات والشروط الخاصة
    • التعريف:
    في بعض الحالات، يمكن استثناء بعض المواد أو الخدمات من شرط المحتوى المحلي في حال عدم توفرها محليًا أو عدم مطابقتها للمواصفات الفنية المطلوبة.
    • إجراءات الاستثناء:
    • تقديم طلب استثناء رسمي للجهة الحكومية مرفقًا بمبررات عدم توفر المنتج محليًا.
    • دراسة الطلب من قبل لجنة مختصة والبت فيه خلال فترة (تحددها الجهة الحكومية).
    • في حال الموافقة، يتم توثيق الاستثناء ضمن عقد المشروع.

    7. توثيق نسبة المحتوى المحلي في المشروع
    • التعريف:
    يلتزم المتعاقد بتوثيق جميع المشتريات المحلية المستخدمة في تنفيذ المشروع، وتقديم الأدلة اللازمة عند طلب الجهة الحكومية.
    • إجراءات التوثيق:
    • إعداد تقارير شهرية توضح نسبة المنتجات والخدمات المحلية المستخدمة.
    • إرفاق فواتير الشراء، وشهادات المنشأ، وتقارير التفتيش.
    • تقديم تقرير نهائي عند الانتهاء من المشروع لتحديد نسبة المحتوى المحلي الإجمالية.

    8. العقوبات في حالة عدم الالتزام
    • التعريف:
    توضح العقوبات التي يتم تطبيقها في حال عدم التزام المتعاقد بالنسبة المطلوبة من المحتوى المحلي.
    • إجراءات العقوبات:
    • فرض غرامات مالية حسب نسبة النقص في المحتوى المحلي.
    • تخفيض درجات التقييم للمشاريع المستقبلية.
    • في الحالات القصوى، يمكن إلغاء العقد واستبعاد المتعاقد من المناقصات الحكومية لفترة زمنية محددة.

    ملاحظات هامة للتنسيق:
    - لا تستخدم أبدًا علامة # للعناوين، بل استخدم العناوين بشكل عادي.
    - لا تستخدم علامة ** للنص العريض، اكتب النص بشكل عادي.
    - استخدم الترقيم العادي للقوائم المرقمة (1. 2. 3.).
    - استخدم النقاط العادية للقوائم غير المرقمة (•).
    - ضع الجداول بصيغة عادية باستخدام | بين الأعمدة.

    التعليمات:
    - اكتب 2000–3000 كلمة.
    - استخدم لغة رسمية واضحة وطويلة ومترابطة.
    """
    response = llm.predict(prompt)
    return response


def generate_rfp_special_terms(llm, example_rfp):
    prompt = """
    اكتب القسم العاشر من كراسة الشروط: متطلبات برنامج المشاركة الاقتصادية (التوازن الاقتصادي).

    هذا الفصل يوضح المتطلبات والإجراءات المتعلقة ببرنامج التوازن الاقتصادي، الذي يهدف إلى تعزيز التنمية الاقتصادية المحلية من خلال مشاركة القطاع الخاص في تنفيذ المشاريع الحكومية، وتحقيق عوائد اقتصادية مستدامة للمملكة.

    1. تعريف برنامج التوازن الاقتصادي
    • التعريف:
    هو برنامج استراتيجي يهدف إلى تحقيق التوازن الاقتصادي من خلال تعزيز مساهمة الشركات المحلية في تنفيذ المشاريع الحكومية الكبرى، مع التركيز على نقل المعرفة التقنية وتوطين الصناعات الاستراتيجية.
    • الأهداف:
    • زيادة نسبة المحتوى المحلي في المشاريع الكبرى.
    • تعزيز القدرات المحلية في التصنيع والخدمات.
    • خلق فرص عمل للسعوديين في مختلف القطاعات.
    • دعم الابتكار وتطوير المهارات المحلية.

    2. اشتراطات برنامج التوازن الاقتصادي
    • التعريف:
    يجب على المتعاقدين الالتزام بنسبة معينة من المشتريات المحلية وتوظيف الكوادر الوطنية في إطار المشروع.
    • إجراءات الاشتراط:
    • تقديم خطة واضحة ومفصلة لتحقيق نسبة التوازن الاقتصادي المطلوبة في المشروع.
    • الالتزام بتوظيف نسبة من السعوديين في وظائف المشروع.
    • تقديم تقارير دورية تثبت توريد المواد من مصادر محلية معتمدة.
    • استخدام المنتجات والخدمات المحلية متى توفرت بالجودة المطلوبة.

    3. آليات تنفيذ التوازن الاقتصادي
    • التعريف:
    توضيح الآليات المعتمدة لتحقيق التوازن الاقتصادي أثناء تنفيذ المشروع.
    • إجراءات التنفيذ:
    • إعداد خطط تشغيلية مفصلة لتنفيذ الأعمال بمشاركة الموردين المحليين.
    • التعاقد مع الشركات الوطنية لتقديم الخدمات اللازمة.
    • الالتزام بنقل المعرفة والتقنيات إلى الفرق المحلية.
    • توفير برامج تدريبية للمواطنين المشاركين في المشروع.

    4. توثيق المشاركة الاقتصادية
    • التعريف:
    يجب على المتعاقد توثيق جميع الأنشطة المتعلقة ببرنامج التوازن الاقتصادي خلال فترة تنفيذ المشروع.
    • إجراءات التوثيق:
    • إعداد تقارير شهرية توضح نسبة المحتوى المحلي في المشروع.
    • تقديم فواتير وشهادات منشأ للمنتجات المحلية المستخدمة.
    • توثيق عقود التوريد مع الموردين المحليين.
    • توفير بيانات دقيقة عن توظيف المواطنين السعوديين في المشروع.

    5. تقييم الأداء الاقتصادي
    • التعريف:
    تقوم الجهة الحكومية بتقييم مدى التزام المتعاقد بمتطلبات التوازن الاقتصادي على مراحل محددة.
    • إجراءات التقييم:
    • إجراء زيارات ميدانية للتحقق من الالتزام بالمحتوى المحلي.
    • مراجعة التقارير الدورية والعقود المبرمة مع الموردين المحليين.
    • التحقق من تطبيق خطط التدريب وتوظيف السعوديين.
    • إصدار تقارير تقييم الأداء بشكل ربع سنوي.

    6. الحوافز والدعم للمحتوى المحلي
    • التعريف:
    يمكن للجهة الحكومية تقديم حوافز للشركات التي تلتزم بتجاوز نسب المحتوى المحلي المطلوبة.
    • إجراءات الدعم:
    • منح خصومات في الرسوم الحكومية للمشاريع التي تحقق نسب أعلى من المحتوى المحلي.
    • تقديم تسهيلات إضافية في العقود المستقبلية.
    • إعطاء أولوية في المنافسات المستقبلية للشركات التي تتفوق في تطبيق التوازن الاقتصادي.

    7. العقوبات في حالة عدم الالتزام
    • التعريف:
    توضح العقوبات التي يمكن أن تفرض في حال عدم الالتزام بمتطلبات التوازن الاقتصادي.
    • إجراءات العقوبات:
    • فرض غرامات مالية مرتبطة بنسبة النقص في المحتوى المحلي.
    • استبعاد الشركة من المنافسات الحكومية المستقبلية لمدة (تحددها الجهة الحكومية).
    • خصم نسبة من الدفعات المالية المستحقة وفقًا للعقد.
    • في الحالات القصوى، يحق للجهة الحكومية إلغاء العقد مع المتعاقد.

    8. الاستثناءات والشروط الخاصة
    • التعريف:
    في حالات معينة، يمكن للجهة الحكومية منح استثناءات لبعض متطلبات التوازن الاقتصادي عند عدم توفر المنتجات محليًا أو في حال عدم مطابقتها للمواصفات.
    • إجراءات الاستثناء:
    • تقديم طلب رسمي من المتعاقد يوضح أسباب الاستثناء المطلوبة.
    • دراسة الطلب من قبل لجنة مختصة في الجهة الحكومية.
    • إصدار موافقة خطية إذا كانت الأسباب مقبولة مع توثيق القرار.

    ملاحظات هامة للتنسيق:
    - لا تستخدم أبدًا علامة # للعناوين، بل استخدم العناوين بشكل عادي.
    - لا تستخدم علامة ** للنص العريض، اكتب النص بشكل عادي.
    - استخدم الترقيم العادي للقوائم المرقمة (1. 2. 3.).
    - استخدم النقاط العادية للقوائم غير المرقمة (•).
    - ضع الجداول بصيغة عادية باستخدام | بين الأعمدة.

    التعليمات:
    - اكتب 2000–3000 كلمة.
    - استخدم لغة رسمية وطويلة ومترابطة.
    """
    response = llm.predict(prompt)
    return response


def generate_rfp_attachments(llm, example_rfp):
    prompt = """
       اكتب القسم الحادي عشر من كراسة الشروط: الشروط الخاصة.

       هذا الفصل يتناول الشروط الخاصة التي تحددها الجهة الحكومية لمشروع معين، بناءً على طبيعة المشروع ومتطلباته الخاصة. يمكن أن تختلف هذه الشروط من مشروع لآخر حسب نوع الخدمات أو المنتجات المطلوبة، وتُضاف هذه الشروط لتكملة الشروط العامة في كراسة الشروط والمواصفات.

       1. نطاق الشروط الخاصة
       • التعريف:
       يشمل هذا القسم تحديد الشروط الإضافية التي تطبق على المشروع، وتشمل المتطلبات التقنية، البيئية، التشغيلية، أو الأمنية التي لم يتم تغطيتها في الشروط العامة.
       • إجراءات التحديد:
       • تحديد الشروط الخاصة حسب طبيعة المشروع.
       • توضيح أي معايير إضافية أو استثناءات تحتاج إلى تطبيق.
       • وضع إطار زمني لتلبية هذه الشروط خلال مدة التنفيذ.

       2. معايير الأمان والسلامة الخاصة
       • التعريف:
       يجب على المتعاقد الالتزام بمعايير أمان وسلامة إضافية خاصة بالموقع أو المعدات المستخدمة في المشروع.
       • إجراءات الأمان:
       • تطبيق إجراءات أمان خاصة إذا كانت طبيعة المشروع تتطلب ذلك.
       • توفير معدات السلامة الشخصية (PPE) المناسبة.
       • الالتزام بإجراءات السلامة البيئية عند تنفيذ المشروع.
       • إعداد خطط للطوارئ ومكافحة الحريق.

       3. متطلبات الاستدامة البيئية
       • التعريف:
       يجب على المتعاقد الالتزام بالمعايير البيئية الصادرة عن الجهات المختصة لضمان الاستدامة البيئية أثناء تنفيذ المشروع.
       • إجراءات الاستدامة:
       • الحد من التأثيرات السلبية على البيئة أثناء التنفيذ.
       • إدارة المخلفات والتخلص منها بطريقة آمنة وصديقة للبيئة.
       • استخدام مواد صديقة للبيئة.
       • تقديم تقارير دورية للجهة الحكومية حول مستوى الالتزام البيئي.

       4. الشروط التقنية الخاصة
       • التعريف:
       في حال كان المشروع يتطلب تقنيات حديثة أو معدات متطورة، يتم توضيح هذه المتطلبات في الشروط الخاصة.
       • إجراءات التنفيذ:
       • تحديد المواصفات التقنية المطلوبة للمعدات والأجهزة.
       • التأكد من توافق الأنظمة مع المعايير العالمية.
       • توفير الدعم الفني والتدريب المطلوب لضمان التشغيل بكفاءة.

       5. متطلبات التوثيق والتقارير
       • التعريف:
       يجب على المتعاقد تقديم تقارير دورية وشهادات إنجاز توضح مستوى التقدم في تنفيذ المشروع.
       • إجراءات التوثيق:
       • إعداد تقارير أسبوعية أو شهرية حسب متطلبات الجهة الحكومية.
       • توثيق جميع العمليات الإنشائية أو التشغيلية.
       • تقديم صور وتقارير فحص الجودة.
       • إعداد تقرير نهائي شامل بعد إتمام المشروع.

       6. شروط الدفع والدفعات الخاصة
       • التعريف:
       توضيح أي شروط خاصة بجدول الدفعات أو آليات الدفع المتفق عليها في العقد.
       • إجراءات الدفع:
       • دفعات مستحقة عند إتمام مراحل محددة.
       • توضيح آلية الاستلام والقبول من الجهة الحكومية.
       • اشتراط تقارير إنجاز قبل صرف الدفعات.

       7. التأمينات الخاصة بالمشروع
       • التعريف:
       يجب على المتعاقد توفير تأمينات خاصة لحماية المشروع من المخاطر المحتملة.
       • إجراءات التأمين:
       • التأمين على المعدات.
       • التأمين ضد الحوادث والإصابات.
       • التأمين ضد الكوارث الطبيعية أو غير المتوقعة.

       8. حالات التعليق والإيقاف المؤقت للمشروع
       • التعريف:
       في بعض الحالات، يمكن للجهة الحكومية تعليق أو إيقاف المشروع مؤقتاً.
       • إجراءات التعليق:
       • إرسال إشعار رسمي للمتعاقد مع بيان الأسباب.
       • تحديد فترة التعليق وتأثيرها على الجدول الزمني.
       • استئناف العمل بعد زوال الأسباب مع تعديل الجدول حسب الحاجة.

       9. تعديلات العقد والشروط الخاصة
       • التعريف:
       يمكن تعديل الشروط الخاصة بناءً على اتفاق الطرفين.
       • إجراءات التعديل:
       • تقديم طلب رسمي مع المبررات.
       • موافقة الجهة الحكومية.
       • توثيق التعديلات في ملحق رسمي.

       10. الشروط الجزائية في حالة عدم الامتثال
       • التعريف:
       تحديد الغرامات أو العقوبات عند عدم الالتزام بالشروط الخاصة.
       • إجراءات العقوبات:
       • فرض غرامات مالية.
       • خصم قيمة الأضرار من الدفعات المستحقة.
       • في الحالات الكبيرة، إنهاء العقد أو استبعاد المتعاقد من المنافسات المستقبلية.

       ملاحظات هامة للتنسيق:
       - لا تستخدم أبدًا علامة # للعناوين، بل استخدم العناوين بشكل عادي.
       - لا تستخدم علامة ** للنص العريض، اكتب النص بشكل عادي.
       - استخدم الترقيم العادي للقوائم المرقمة (1. 2. 3.).
       - استخدم النقاط العادية للقوائم غير المرقمة (•).
       - ضع الجداول بصيغة عادية باستخدام | بين الأعمدة.

       التعليمات:
       - اكتب 2000–3000 كلمة.
       - استخدم لغة رسمية واضحة ومفصلة.
       """
    response = llm.predict(prompt)
    return response


def generate_rfp_annexes_and_forms(llm, example_rfp):
    prompt = """
    اكتب القسم الثاني عشر من كراسة الشروط بعنوان: الملاحق والنماذج الإضافية.

    الهدف من هذا القسم هو تقديم وصف شامل لجميع الملاحق والنماذج التي تُرفق بكراسة الشروط والمواصفات بهدف دعم عملية التقديم والمراجعة وضمان التزام المتنافسين بكافة المتطلبات.

    يجب أن يشمل النص تفصيل النقاط التالية:
    1. خطاب تقديم العروض: تعريف، محتويات، وإجراءات التقديم.
    2. نموذج الأسئلة والاستفسارات: أهميته، طريقة الإرسال، وآلية الرد.
    3. نموذج العقد: مكوناته الأساسية، إجراءات توقيعه، والتزام الأطراف به.
    4. الرسومات والمخططات: أنواعها، كيفية التعامل معها، ومتطلبات التوثيق.
    5. القائمة الإلزامية: المواد والخدمات المحلية، وإثبات الالتزام بها.
    6. متطلبات تطبيق الحد الأدنى للمحتوى المحلي: شرح النسب وآليات المتابعة.
    7. آلية احتساب وزن المحتوى المحلي في التقييم المالي على مستوى المنشأة: التفسير العملي والإجراءات.
    8. آلية احتساب وزن المحتوى المحلي في التقييم المالي على مستوى العقد: التفسير العملي والإجراءات.
    9. سياسة المشاركة الاقتصادية: الأهداف، والالتزامات المطلوبة من المتعاقدين.
    10. نموذج التعهد: مضمونه، طريقة تعبئته، وآلية تقديمه ضمن العرض.

    ملاحظات هامة للتنسيق:
    - لا تستخدم أبدًا علامة # للعناوين، بل استخدم العناوين بشكل عادي.
    - لا تستخدم علامة ** للنص العريض، اكتب النص بشكل عادي.
    - استخدم الترقيم العادي للقوائم المرقمة (1. 2. 3.).
    - استخدم النقاط العادية للقوائم غير المرقمة (•).
    - ضع الجداول بصيغة عادية باستخدام | بين الأعمدة.

    التعليمات:
    - استخدم لغة عربية رسمية وفصحى خالية من الأخطاء.
    - اكتب ما لا يقل عن 2000 كلمة ولا يزيد عن 3000 كلمة.
    - اجعل الفقرات مترابطة ومنظمة وسهلة الفهم.
    """
    response = llm.predict(prompt)
    return response


# Main function to generate RFP document
import concurrent.futures
from functools import partial


def generate_rfp_document(competition_name, competition_objectives, competition_description, output_dir, static_dir):

    # Build vector store from PDF files in knowledge directory
    knowledge_dir = os.path.join(static_dir, "knowledge")
    vector_store = build_vector_store(knowledge_dir)

    # Find similar example RFP
    example_rfp = ""
    if vector_store:
        try:
            retrieved_docs = vector_store.similarity_search(competition_description, k=1)
            if retrieved_docs:
                example_rfp = retrieved_docs[0].page_content
                print("✅ Found similar RFP to use as reference model.")
            else:
                print("⚠️ No similar RFP found. Will generate without reference example.")
        except Exception as e:
            print(f"Error during similarity search: {str(e)}")
            print("⚠️ Will generate without reference example.")
    else:
        print("⚠️ Vector store not initialized. Will generate without reference example.")

    # Setup LLM
    llm = ChatOpenAI(model='gpt-4-turbo', temperature=0.2)

    # Define all section generation tasks with their titles
    generation_tasks = [
        (1, "المقدمة", partial(generate_rfp_intro, llm, example_rfp, competition_name, competition_objectives,
                               competition_description)),
        (2, "الأحكام العامة", partial(generate_rfp_general_terms, llm, example_rfp)),
        (3, "إعداد العروض", partial(generate_rfp_offer_preparation, llm, example_rfp)),
        (4, "تقديم العروض", partial(generate_rfp_offer_submission, llm, example_rfp)),
        (5, "تقييم العروض", partial(generate_rfp_offer_analysis, llm, example_rfp)),
        (6, "متطلبات التعاقد", partial(generate_rfp_award_contract, llm, example_rfp)),
        (7, "نطاق العمل المفصل", partial(generate_rfp_guarantees, llm, example_rfp)),
        (8, "المواصفات الفنية", partial(generate_rfp_specifications, llm, example_rfp)),
        (9, "متطلبات المحتوى المحلي", partial(generate_rfp_general_contract_terms, llm, example_rfp)),
        (10, "متطلبات برنامج المشاركة الاقتصادية", partial(generate_rfp_special_terms, llm, example_rfp)),
        (11, "الشروط الخاصة", partial(generate_rfp_attachments, llm, example_rfp)),
        (12, "الملاحق والنماذج الإضافية", partial(generate_rfp_annexes_and_forms, llm, example_rfp))
    ]

    # Store results by section number to maintain ordering
    sections_content = {}

    print("🔹 Starting parallel generation of all RFP sections...")

    # Use ThreadPoolExecutor to run generation tasks in parallel
    # Limiting to 4 workers to avoid overwhelming the API or system resources
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        # Create a dictionary to map futures to their section info
        future_to_section = {}

        # Submit all tasks
        for section_num, section_title, generate_func in generation_tasks:
            future = executor.submit(generate_func)
            future_to_section[future] = (section_num, section_title)

        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_section):
            section_num, section_title = future_to_section[future]
            try:
                section_content = future.result()
                sections_content[section_num] = (section_title, section_content)
                print(f"✅ Completed section {section_num}: {section_title}")
            except Exception as e:
                print(f"❌ Error generating section {section_num}: {section_title}")
                print(f"   Error details: {str(e)}")
                # Provide a placeholder for failed sections
                sections_content[section_num] = (
                section_title, f"Error generating {section_title} section. Please try again.")

    print("✅ All sections completed!")

    # Combine all sections in the correct order
    sections = [sections_content[i] for i in range(1, 13)]

    # Generate a filename based on the competition name
    safe_filename = re.sub(r'[^\w\s]', '', competition_name).strip().replace(' ', '_')
    filename = f"{safe_filename}_rfp.docx"
    output_path = os.path.join(output_dir, filename)

    # Save the RFP to a Word document
    save_rfp_sections_to_word(sections, output_path)

    return filename


import fitz  # PyMuPDF for PDF extraction


def read_pdf_with_fitz(file_path):
    """
    Extract text from PDF using PyMuPDF (fitz).
    """
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        print(f"Error reading PDF: {str(e)}")
    return text


def clean_text(text):
    """
    Clean extracted text.
    """
    text = re.sub(r'Error! Bookmark not defined\.', '', text)
    text = re.sub(r'\d{1,3}', '', text)
    text = re.sub(r'\.{2,}', '', text)
    text = re.sub(r'\n+', '\n', text)
    return text.strip()


def improve_rfp_with_extracted_text(pdf_text, competition_name, competition_objectives, competition_description,
                                    output_path, vector_store=None):
    """
    Improve an existing RFP document using pre-extracted text.
    This function is optimized for parallel processing.
    """
    # Setup LLM
    llm = ChatOpenAI(model='gpt-4-turbo', temperature=0.2)

    # Define required sections
    required_sections = [
        'المقدمة', 'الأحكام العامة', 'إعداد العروض', 'تقديم العروض',
        'تقييم العروض', 'متطلبات التعاقد', 'نطاق العمل المفصل',
        'المواصفات الفنية', 'متطلبات المحتوى المحلي', 'متطلبات برنامج المشاركة الاقتصادية',
        'الشروط الخاصة', 'الملاحق والنماذج الإضافية'
    ]

    # Get example RFP if vector store is available
    example_rfp = ""
    if vector_store:
        try:
            retrieved_docs = vector_store.similarity_search(competition_description, k=1)
            if retrieved_docs:
                example_rfp = retrieved_docs[0].page_content
                print("✅ Found similar RFP to use as reference model.")
            else:
                print("⚠️ No similar RFP found. Will generate without reference example.")
        except Exception as e:
            print(f"Error during similarity search: {str(e)}")
            print("⚠️ Will generate without reference example.")

    # Clean the text
    text = clean_text(pdf_text)
    notes = []

    # Prepare tasks for section processing
    section_tasks = []

    for section in required_sections:
        # Try to find the section in the original document
        pattern = rf"{section}\s*([\s\S]*?)(?=\n\s*(?:{'|'.join(required_sections)})|$)"
        match = re.search(pattern, text)
        section_content = match.group(1).strip() if match else ""

        generate_flag = False

        # Check if section needs to be generated or improved
        if len(section_content) < 50:
            note = f"❌ القسم '{section}' مفقود → سيتم توليده."
            notes.append(note)
            generate_flag = True
        elif section == 'المقدمة':
            key_terms = ['تعريف', 'خلفية', 'نطاق', 'أهداف']
            if not all(term in section_content for term in key_terms):
                note = f"⚠️ القسم '{section}' ناقص في التعريف/الخلفية/النطاق/الأهداف → سيتم تحسينه."
                notes.append(note)
                generate_flag = True
        else:
            note = f"ℹ️ القسم '{section}' موجود وسنعيد كتابته لضمان التنسيق والترتيب."
            notes.append(note)

        # Add to tasks list
        section_tasks.append((section, section_content, generate_flag))

    # Process sections in parallel using ThreadPoolExecutor with increased workers
    section_results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        # Create a dictionary to map futures to their section info
        future_to_section = {}

        for section, content, generate_flag in section_tasks:
            # Submit task to generate or improve the section
            future = executor.submit(
                improve_section,
                llm,
                section,
                content,
                competition_name,
                competition_objectives,
                competition_description,
                generate_flag
            )
            future_to_section[future] = section

        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_section):
            section = future_to_section[future]
            try:
                section_content = future.result()
                section_results[section] = section_content
                print(f"✅ Completed improving section: {section}")
            except Exception as e:
                print(f"❌ Error improving section {section}: {e}")
                # Provide a placeholder for failed sections
                section_results[section] = f"Error generating {section} section. Please try again."

    # Organize sections in the correct order
    sections = []
    for section in required_sections:
        if section in section_results:
            sections.append((section, section_results[section]))

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save the improved RFP to a Word document
    save_rfp_sections_to_word(sections, output_path)

    # Generate filename
    filename_base = os.path.basename(output_path)

    # Print notes
    notes_text = "\n".join(notes)
    print("\n===== 📝 ملاحظات المراجعة =====\n")
    print(notes_text)
    print(f"\n✅ تم حفظ الكراسة المحسنة في {filename_base}.\n")

    return filename_base


def improve_section(llm, section, original_content, competition_name, competition_objectives, competition_description,
                    generate_flag):
    """
    Generate or improve a single section of an RFP.
    """
    if generate_flag:
        prompt = f"""
        بصفتك خبيرًا محترفًا، اكتب قسم '{section}' لكراسة بعنوان '{competition_name}' بهدف '{competition_objectives}' في مجال '{competition_description}'. 

        اكتب محتوى تفصيلي لا يقل عن 1000-1500 كلمة، بلغة عربية فصحى واضحة وطويلة ومترابطة. المحتوى يجب أن يكون شاملاً وعميقاً ومتخصصاً.

        استخدم التنسيق التالي:
        - لا تستخدم علامة # للعناوين، بل استخدم العناوين بشكل عادي.
        - لا تستخدم علامة ** للنص العريض، اكتب النص بشكل عادي.
        - استخدم الترقيم العادي للقوائم المرقمة (1. 2. 3.).
        - استخدم النقاط العادية للقوائم غير المرقمة (•).
        - ضع الجداول بصيغة عادية باستخدام | بين الأعمدة.

        ابدأ القسم مباشرة دون ذكر العنوان، حيث سيتم إضافته تلقائياً.
        """
    else:
        prompt = f"""
        بصفتك خبيرًا محترفًا، أعد كتابة وتحسين قسم '{section}' التالي من كراسة بعنوان '{competition_name}' بهدف '{competition_objectives}' في مجال '{competition_description}'.

        حافظ على نفس المعنى ولكن حسّن الأسلوب والصياغة، نظّف النص من أي أخطاء، واكتب بلغة عربية فصحى واضحة.
        المحتوى يجب أن يكون لا يقل عن 1000-1500 كلمة، وابدأ القسم مباشرة دون ذكر العنوان (سيتم إضافته تلقائياً).

        أضف المزيد من التفاصيل والشرح إذا كان المحتوى الأصلي مختصراً جداً.

        النص الأصلي:
        {original_content}
        """

    section_content = llm.predict(prompt).strip()
    return clean_text(section_content)