import os
import io
import base64
import pypdfium2 as pdfium
from PIL import Image
from django.conf import settings
from groq import Groq

def load_document_images(file_path):
    """
    Renders PDF pages as images using pypdfium2.
    Returns a list of PIL Images.
    """
    images = []
    try:
        # Load PDF document
        pdf = pdfium.PdfDocument(file_path)
        
        # Iterate over pages and render
        for i in range(len(pdf)):
            page = pdf[i]
            # Render page to bitmap (scale=300/72 represents roughly 300 DPI)
            bitmap = page.render(scale=300/72)
            # Convert to PIL Image
            pil_image = bitmap.to_pil()
            images.append(pil_image)
            
    except Exception as e:
        print(f"Error extracting images from PDF: {e}")
        # Identify if it's an image file already (fallback)
        try:
             img = Image.open(file_path)
             images.append(img)
        except Exception as img_e:
             print(f"Error loading as image: {img_e}")
             
    return images

def get_markdown_from_page(image, client):
    """
    Sends an image to Groq Vision model to get a Markdown transcription.
    """
    # Convert PIL Image to base64
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    vision_models = ["llama-3.2-11b-vision-preview", "llama-3.2-90b-vision-preview"]
    
    for model_name in vision_models:
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", 
                                "text": "Act as an expert OCR engine. Transcribe this medical report image into highly accurate Markdown. Preserve tables. Do not summarize."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_str}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0,
                max_tokens=1024,
            )
            print(f"[OK] Vision OCR succeeded with model: {model_name}")
            return completion.choices[0].message.content
        except Exception as e:
            print(f"[WARN] Vision model {model_name} failed: {e}")
            continue
    
    print("[ERROR] All vision models failed")
    return ""
