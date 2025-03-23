from flask import Flask, request, render_template, jsonify, send_file, redirect, url_for
import os
from PIL import Image
import easyocr
from werkzeug.utils import secure_filename
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import datetime
import textwrap

# Initialize EasyOCR reader (this will download the model on first run)
reader = easyocr.Reader(['en'])

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Set up absolute paths for Python Anywhere
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['PDF_FOLDER'] = os.path.join(BASE_DIR, 'pdfs')
app.config['RESIZED_FOLDER'] = os.path.join(BASE_DIR, 'resized')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure folders exist
for folder in [app.config['UPLOAD_FOLDER'], app.config['PDF_FOLDER'], app.config['RESIZED_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image(image, max_width=None, max_height=None, quality=85):
    """Resize image while maintaining aspect ratio"""
    if max_width is None and max_height is None:
        return image

    # Get original dimensions
    width, height = image.size
    aspect_ratio = width / height

    # Calculate new dimensions
    if max_width and max_height:
        if width > height:
            new_width = min(width, max_width)
            new_height = int(new_width / aspect_ratio)
            if new_height > max_height:
                new_height = max_height
                new_width = int(new_height * aspect_ratio)
        else:
            new_height = min(height, max_height)
            new_width = int(new_height * aspect_ratio)
            if new_width > max_width:
                new_width = max_width
                new_height = int(new_width / aspect_ratio)
    elif max_width:
        new_width = min(width, max_width)
        new_height = int(new_width / aspect_ratio)
    else:  # max_height
        new_height = min(height, max_height)
        new_width = int(new_height * aspect_ratio)

    # Resize the image
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Convert to RGB if necessary (for PNG with transparency)
    if resized_image.mode in ('RGBA', 'P'):
        resized_image = resized_image.convert('RGB')
    
    return resized_image

def preprocess_image(image, resize_width=None, resize_height=None, quality=85):
    """Preprocess image for better OCR results"""
    try:
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        # Resize if specified
        if resize_width or resize_height:
            image = resize_image(image, resize_width, resize_height, quality)
        
        return image
    except Exception as e:
        raise Exception(f"Error preprocessing image: {str(e)}")

def create_pdf(text, original_filename):
    """Create a PDF file from the recognized text"""
    try:
        # Generate a unique filename for the PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"text_recognition_{timestamp}.pdf"
        pdf_path = os.path.join(app.config['PDF_FOLDER'], pdf_filename)
        
        # Create the PDF
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        
        # Add a title
        c.setFont("Helvetica-Bold", 16)
        title = f"Text Recognition Results - {original_filename}"
        c.drawString(50, height - 50, title)
        
        # Add timestamp
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 70, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Add the recognized text
        c.setFont("Helvetica", 12)
        y = height - 100
        
        # Wrap text to fit page width (about 75 characters per line)
        wrapped_text = textwrap.fill(text, width=75)
        for line in wrapped_text.split('\n'):
            if y < 50:  # Start a new page if we're near the bottom
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 12)
            c.drawString(50, y, line)
            y -= 20
        
        c.save()
        return pdf_filename
    except Exception as e:
        raise Exception(f"Error creating PDF: {str(e)}")

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/recognize')
def recognize():
    return render_template('index.html')

@app.route('/resize')
def resize_page():
    return render_template('resize.html')

@app.route('/recognize', methods=['POST'])
def recognize_text():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Get resize parameters
    resize_width = request.form.get('resize_width', type=int)
    resize_height = request.form.get('resize_height', type=int)
    quality = request.form.get('quality', type=int, default=85)
    
    if file and allowed_file(file.filename):
        try:
            # Save the file temporarily
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                # Open and preprocess the image
                with Image.open(filepath) as image:
                    # Get original dimensions
                    original_width, original_height = image.size
                    
                    # Preprocess the image
                    processed_image = preprocess_image(image, resize_width, resize_height, quality)
                    
                    # Get new dimensions
                    new_width, new_height = processed_image.size
                    
                    try:
                        # Save processed image temporarily
                        processed_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f'processed_{filename}')
                        processed_image.save(processed_filepath)
                        
                        # Perform OCR using EasyOCR
                        results = reader.readtext(processed_filepath)
                        
                        # Extract text from results
                        text = '\n'.join([result[1] for result in results])
                        
                        # Create PDF from the recognized text
                        pdf_filename = create_pdf(text, filename)
                        
                        return jsonify({
                            'text': text,
                            'original_dimensions': {
                                'width': original_width,
                                'height': original_height
                            },
                            'new_dimensions': {
                                'width': new_width,
                                'height': new_height
                            },
                            'pdf_filename': pdf_filename
                        })
                    except Exception as e:
                        raise Exception(f"OCR Error: {str(e)}")
                    finally:
                        # Clean up processed image
                        if os.path.exists(processed_filepath):
                            os.remove(processed_filepath)
                    
            except Exception as e:
                raise Exception(f"Image Processing Error: {str(e)}")
            
        except Exception as e:
            # Clean up in case of error
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': str(e)}), 500
        finally:
            # Clean up
            if os.path.exists(filepath):
                os.remove(filepath)
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/download_pdf/<filename>')
def download_pdf(filename):
    """Download the generated PDF file"""
    try:
        pdf_path = os.path.join(app.config['PDF_FOLDER'], filename)
        if not os.path.exists(pdf_path):
            return jsonify({'error': 'PDF file not found'}), 404
            
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': f"Error downloading PDF: {str(e)}"}), 500

@app.route('/resize', methods=['POST'])
def resize_image_endpoint():
    """Endpoint for resizing images without OCR"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Get resize parameters
    resize_width = request.form.get('resize_width', type=int)
    resize_height = request.form.get('resize_height', type=int)
    quality = request.form.get('quality', type=int, default=85)
    
    if not (resize_width or resize_height):
        return jsonify({'error': 'Please specify at least one dimension (width or height)'}), 400
    
    if file and allowed_file(file.filename):
        try:
            # Save the file temporarily
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                # Open and resize image
                with Image.open(filepath) as image:
                    # Get original dimensions
                    original_width, original_height = image.size
                    
                    # Resize image
                    resized_image = resize_image(image, resize_width, resize_height, quality)
                    
                    # Get new dimensions
                    new_width, new_height = resized_image.size
                    
                    # Generate unique filename for resized image
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    name, ext = os.path.splitext(filename)
                    resized_filename = f"{name}_resized_{timestamp}{ext}"
                    resized_filepath = os.path.join(app.config['RESIZED_FOLDER'], resized_filename)
                    
                    # Save resized image
                    resized_image.save(resized_filepath, quality=quality)
                    
                    return jsonify({
                        'message': 'Image resized successfully',
                        'original_dimensions': {
                            'width': original_width,
                            'height': original_height
                        },
                        'new_dimensions': {
                            'width': new_width,
                            'height': new_height
                        },
                        'resized_filename': resized_filename
                    })
                    
            except Exception as e:
                raise Exception(f"Image Processing Error: {str(e)}")
            
        except Exception as e:
            # Clean up in case of error
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': str(e)}), 500
        finally:
            # Clean up original upload
            if os.path.exists(filepath):
                os.remove(filepath)
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/download_resized/<filename>')
def download_resized(filename):
    """Download a resized image"""
    try:
        image_path = os.path.join(app.config['RESIZED_FOLDER'], filename)
        if not os.path.exists(image_path):
            return jsonify({'error': 'Resized image not found'}), 404
            
        return send_file(
            image_path,
            mimetype='image/jpeg',  # This will work for most image types
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': f"Error downloading image: {str(e)}"}), 500

def cleanup_old_files():
    """Clean up files older than 1 hour"""
    current_time = datetime.now()
    for folder in [app.config['UPLOAD_FOLDER'], app.config['PDF_FOLDER'], app.config['RESIZED_FOLDER']]:
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            file_time = datetime.fromtimestamp(os.path.getctime(filepath))
            if (current_time - file_time).total_seconds() > 3600:  # 1 hour
                try:
                    os.remove(filepath)
                except:
                    pass

if __name__ == '__main__':
    # Set host to 0.0.0.0 to make it accessible externally
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print("\nStarting Image Processing Suite...")
    print("-----------------------------------")
    print("The application will download the OCR model on first run.")
    print("This may take a few minutes, please be patient.")
    print(f"\nOnce ready, you can access the application at: http://localhost:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug) 