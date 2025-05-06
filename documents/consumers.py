# documents/consumers.py
import json
import asyncio
import logging
import re
import os
import unicodedata
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from openai import AsyncOpenAI
from django.conf import settings
from asgiref.sync import sync_to_async
from .models import Document, DocumentAnalysis

# Set up logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# System prompt for document analysis
SYSTEM_PROMPT = """
أنت محلل وثائق خبير ومدقق لغوي. مهمتك هي:
1. تحليل المستند المقدم
2. تحديد نقاط الضعف والأخطاء النحوية والمشاكل الهيكلية
3. تقديم اقتراحات محددة للتحسين
4. كن شاملاً ودقيقاً في تحليلك
5. قم بتنسيق إجابتك مع أقسام واضحة

قسم تحليلك إلى الأقسام التالية:
- تحليل الهيكل والتنظيم
- تحليل اللغة والأسلوب
- تحليل المحتوى والأفكار
- اقتراحات التحسين

قدم إجابتك باللغة العربية الفصحى.
"""


class DocumentAnalysisConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle WebSocket connection"""
        try:
            # Accept the WebSocket connection
            await self.accept()
            logger.info(f"WebSocket connection established: {self.channel_name}")
        except Exception as e:
            logger.error(f"Error in WebSocket connection: {str(e)}")
            raise

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        logger.info(f"WebSocket disconnected with code {close_code}: {self.channel_name}")

    @sync_to_async
    def get_document(self, doc_id, user_id):
        """Get document if it belongs to the user"""
        try:
            user = User.objects.get(id=user_id)
            return Document.objects.get(id=doc_id, user=user)
        except User.DoesNotExist:
            logger.warning(f"User with ID {user_id} not found")
            return None
        except Document.DoesNotExist:
            logger.warning(f"Document with ID {doc_id} not found for user {user_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving document: {str(e)}")
            return None

    @sync_to_async
    def save_analysis(self, document, analysis_text, suggestions):
        """Save analysis results to database"""
        try:
            return DocumentAnalysis.objects.create(
                document=document,
                analysis_text=analysis_text,
                suggestions=suggestions
            )
        except Exception as e:
            logger.error(f"Error saving analysis: {str(e)}")
            raise

    def normalize_text(self, text):
        """Normalize text to handle encoding issues with Arabic text"""
        # Fix mojibake and other text rendering issues
        try:
            import ftfy
            text = ftfy.fix_text(text)
        except ImportError:
            logger.warning("ftfy module not available, skipping text fixing")

        # Unicode normalization to handle composite characters
        text = unicodedata.normalize("NFKC", text)
        return text

    def clean_arabic_text(self, text, min_arabic_ratio=0.3, min_length=10):
        """
        Filter and clean Arabic text, removing noise and boilerplate
        """
        # Remove common boilerplate patterns
        boilerplate_patterns = [
            r"رقم الصفحة\s*\d+",
            r"شعار\s+.*?(?:\n|$)",
            r"اسم الجهة.*?(?:\n|$)"
        ]

        for pattern in boilerplate_patterns:
            text = re.sub(pattern, "", text)

        # Process line by line
        lines = text.splitlines()
        filtered_lines = []

        for line in lines:
            line = line.strip()

            # Skip short lines
            if len(line) < min_length:
                continue

            # Check if line has enough Arabic characters
            arabic_chars = len(re.findall(r'[\u0600-\u06FF]', line))
            if len(line) > 0 and (arabic_chars / len(line)) < min_arabic_ratio:
                continue

            # Remove non-Arabic characters except numbers and punctuation
            line = re.sub(r'[^\u0600-\u06FF0-9\s،؛؟.,:()\-]', '', line)

            filtered_lines.append(line)

        return "\n".join(filtered_lines)

    def truncate_document(self, document_content, max_chars=4000):
        """
        Intelligently truncate document content while preserving context
        """
        if len(document_content) <= max_chars:
            return document_content

        # Get first and last part of the document
        beginning = document_content[:max_chars // 2]
        end = document_content[-(max_chars // 2):]

        # Add a note indicating content was truncated
        truncation_note = "\n\n[...تم اختصار المحتوى للتوافق مع قيود النظام...]\n\n"

        return beginning + truncation_note + end

    async def extract_document_content(self, document):
        """
        Extract and clean document content with fallback mechanisms
        """
        document_content = document.content or ""

        if document.file:
            file_path = document.file.path
            if os.path.exists(file_path):
                try:
                    # Try different encodings for Arabic text
                    encodings = ['utf-8', 'cp1256', 'iso-8859-6', 'windows-1256']
                    for encoding in encodings:
                        try:
                            with open(file_path, 'r', encoding=encoding) as f:
                                document_content = f.read()
                            document_content = self.normalize_text(document_content)
                            document_content = self.clean_arabic_text(document_content)
                            break
                        except UnicodeDecodeError:
                            continue

                    # If text extraction failed with all encodings, try binary mode
                    if not document_content:
                        with open(file_path, 'rb') as f:
                            document_content = f.read().decode('utf-8', errors='replace')
                        document_content = self.normalize_text(document_content)
                        document_content = self.clean_arabic_text(document_content)

                    # For PDFs, try additional extraction methods
                    if file_path.lower().endswith('.pdf') and not document_content.strip():
                        try:
                            # Try PyPDF2
                            import PyPDF2
                            with open(file_path, 'rb') as f:
                                reader = PyPDF2.PdfReader(f)
                                pdf_text = []
                                for page_num in range(len(reader.pages)):
                                    page = reader.pages[page_num]
                                    pdf_text.append(page.extract_text() or "")
                                document_content = "\n\n".join(pdf_text)
                                document_content = self.normalize_text(document_content)
                                document_content = self.clean_arabic_text(document_content)
                        except (ImportError, Exception) as e:
                            logger.warning(f"PyPDF2 extraction failed: {str(e)}")

                            # Try PyMuPDF as another fallback
                            try:
                                import fitz
                                with fitz.open(file_path) as doc:
                                    pdf_text = []
                                    for page in doc:
                                        pdf_text.append(page.get_text() or "")
                                    document_content = "\n\n".join(pdf_text)
                                    document_content = self.normalize_text(document_content)
                                    document_content = self.clean_arabic_text(document_content)
                            except ImportError:
                                logger.warning("PyMuPDF not available")
                            except Exception as e:
                                logger.warning(f"PyMuPDF extraction failed: {str(e)}")

                except Exception as e:
                    logger.error(f"Error reading file: {str(e)}")
                    document_content = f"لم يتمكن النظام من قراءة محتوى الملف: {str(e)}"

        # Ensure we have some content, or provide a placeholder
        if not document_content.strip():
            document_content = "لم يتم العثور على محتوى في الملف."

        return document_content

    async def analyze_with_retry(self, system_prompt, user_prompt, max_retries=3):
        """
        Analyze document with automatic retry and content reduction if token limit is exceeded
        """
        retries = 0
        content_length = 4000  # Start with 4000 chars

        while retries < max_retries:
            try:
                # If not first attempt, truncate the content further
                if retries > 0:
                    # Find the content part of the prompt and truncate it
                    start_marker = "المحتوى:\n"
                    start_idx = user_prompt.find(start_marker) + len(start_marker)
                    end_idx = user_prompt.find("\n\nقم بتحليل", start_idx)

                    if start_idx > -1 and end_idx > -1:
                        content = user_prompt[start_idx:end_idx]
                        truncated_content = self.truncate_document(content, content_length)
                        user_prompt = user_prompt[:start_idx] + truncated_content + user_prompt[end_idx:]

                # Use the same model as in the sample code
                model = "gpt-4-turbo"  # Using the model from your sample code

                # Call OpenAI with streaming
                stream = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=4000,
                    stream=True
                )

                return stream

            except Exception as e:
                error_message = str(e).lower()
                # Check if it's a token limit error
                if ("maximum context length" in error_message or
                    "context_length_exceeded" in error_message) and retries < max_retries:
                    retries += 1
                    content_length = content_length // 2  # Reduce content length by half
                    logger.warning(f"Token limit exceeded, retrying with shorter content: {content_length}")
                else:
                    # If it's not a token limit error or we've exceeded max retries, raise the exception
                    raise

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'analyze_document':
                doc_id = data.get('doc_id')
                user_id = data.get('user_id')

                if not doc_id or not user_id:
                    await self.send(json.dumps({
                        'type': 'error',
                        'message': 'بيانات غير كاملة'
                    }))
                    return

                logger.info(f"Analyzing document {doc_id} for user {user_id}")

                # Get document
                document = await self.get_document(doc_id, user_id)

                if not document:
                    await self.send(json.dumps({
                        'type': 'error',
                        'message': 'المستند غير موجود أو غير مصرح به'
                    }))
                    return

                # Send start message
                await self.send(json.dumps({
                    'type': 'analysis_started',
                    'message': 'جاري تحليل المستند...'
                }))

                # Extract document content with enhanced methods
                document_content = await self.extract_document_content(document)

                # Apply initial truncation to avoid token limit issues
                truncated_content = self.truncate_document(document_content, 4000)

                # Prepare the prompt
                user_prompt = f"""
                تحليل المستند التالي:

                عنوان: {document.title}
                وصف: {document.description}

                المحتوى:
                {truncated_content}

                قم بتحليل النص من حيث:
                1. بنية المستند وتنظيمه
                2. سلامة اللغة والأسلوب
                3. دقة المعلومات واكتمالها
                4. التناسق والترابط

                قدم اقتراحات محددة للتحسين.
                """

                # Stream the response from ChatGPT
                analysis_text = ""
                suggestions_text = ""
                section = "analysis"  # Start with analysis section

                try:
                    # Call OpenAI with retry mechanism
                    stream = await self.analyze_with_retry(SYSTEM_PROMPT, user_prompt)

                    full_response = ""

                    # Process streaming response
                    async for chunk in stream:
                        if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_response += content

                            # Check if we're in the suggestions section
                            section_keywords = ["اقتراحات", "توصيات", "التحسين", "الاقتراحات"]
                            if any(keyword in content for keyword in section_keywords):
                                section = "suggestions"

                            # Add content to appropriate section
                            if section == "analysis":
                                analysis_text += content
                            else:
                                suggestions_text += content

                            # Send the chunk to the client
                            await self.send(json.dumps({
                                'type': 'analysis_chunk',
                                'content': content,
                                'section': section
                            }))

                            # Small delay to avoid overwhelming the client
                            await asyncio.sleep(0.01)

                    # If sections weren't properly separated
                    if not suggestions_text:
                        # Try to find a logical point to split the response
                        split_keywords = ["اقتراحات", "توصيات", "التحسين", "الاقتراحات"]
                        for keyword in split_keywords:
                            if keyword in full_response:
                                split_point = full_response.find(keyword)
                                analysis_text = full_response[:split_point]
                                suggestions_text = full_response[split_point:]
                                break
                        else:
                            # If no clear dividing point, use the full response for both
                            suggestions_text = full_response

                    # Save the analysis to the database
                    analysis = await self.save_analysis(
                        document,
                        analysis_text or full_response,
                        suggestions_text or "لم يتم العثور على اقتراحات محددة."
                    )

                    # Send completion message
                    await self.send(json.dumps({
                        'type': 'analysis_complete',
                        'message': 'تم الانتهاء من التحليل',
                        'analysis_id': analysis.id
                    }))

                    logger.info(f"Analysis completed for document {doc_id}")

                except Exception as e:
                    logger.error(f"Error in analysis: {str(e)}")

                    # Try fallback to Gemini model if available and if it was an OpenAI error
                    try:
                        if "openai" in str(e).lower():
                            await self.send(json.dumps({
                                'type': 'analysis_chunk',
                                'content': "\n\nجاري محاولة استخدام نموذج تحليل بديل...\n\n",
                                'section': section
                            }))

                            try:
                                import google.generativeai as genai
                                genai.configure(api_key=settings.GEMINI_API_KEY)

                                model = genai.GenerativeModel('gemini-1.5-pro')
                                prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"

                                response = await asyncio.to_thread(
                                    model.generate_content,
                                    prompt
                                )

                                fallback_text = response.text

                                # Send the fallback response
                                await self.send(json.dumps({
                                    'type': 'analysis_chunk',
                                    'content': fallback_text,
                                    'section': 'analysis'
                                }))

                                # Save the analysis
                                analysis = await self.save_analysis(
                                    document,
                                    fallback_text,
                                    "تم تحليل المستند باستخدام نموذج بديل."
                                )

                                # Send completion message
                                await self.send(json.dumps({
                                    'type': 'analysis_complete',
                                    'message': 'تم الانتهاء من التحليل باستخدام نموذج بديل',
                                    'analysis_id': analysis.id
                                }))

                                return

                            except (ImportError, Exception) as gemini_error:
                                logger.error(f"Fallback to Gemini failed: {str(gemini_error)}")
                    except Exception as fallback_error:
                        logger.error(f"Error in fallback attempt: {str(fallback_error)}")

                    # If we get here, both main and fallback attempts failed
                    await self.send(json.dumps({
                        'type': 'error',
                        'message': f'خطأ في تحليل المستند: {str(e)}'
                    }))
            else:
                logger.warning(f"Unknown action received: {action}")
                await self.send(json.dumps({
                    'type': 'error',
                    'message': 'إجراء غير معروف'
                }))

        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            await self.send(json.dumps({
                'type': 'error',
                'message': 'بيانات غير صالحة'
            }))
        except Exception as e:
            logger.error(f"Unexpected error in WebSocket receive: {str(e)}")
            await self.send(json.dumps({
                'type': 'error',
                'message': f'خطأ غير متوقع: {str(e)}'
            }))