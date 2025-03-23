# Image Processing Suite

A web application that combines text recognition (OCR) and image resizing capabilities in one place. Built with Flask and modern web technologies.

## Features

- **Text Recognition**: Extract text from images using EasyOCR
- **Image Resizing**: Resize images while maintaining quality
- **PDF Export**: Download recognized text as PDF
- **Drag & Drop**: Easy file upload interface
- **Modern UI**: Clean, responsive design

## Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd image-processing-suite
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Deployment

### Heroku

1. Install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)

2. Login to Heroku:
```bash
heroku login
```

3. Create a new Heroku app:
```bash
heroku create your-app-name
```

4. Set environment variables:
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set FLASK_ENV=production
```

5. Deploy:
```bash
git push heroku main
```

### Other Platforms

The application can be deployed to any platform that supports Python/Flask applications. Key requirements:

- Python 3.8 or higher
- Support for installing packages from requirements.txt
- Environment variable configuration
- File system access for temporary storage

## Environment Variables

- `SECRET_KEY`: Application secret key (required in production)
- `PORT`: Port number (defaults to 5000)
- `FLASK_ENV`: Set to 'development' for debug mode

## File Storage

The application creates three directories for file storage:
- `uploads/`: Temporary storage for uploaded files
- `pdfs/`: Generated PDF files
- `resized/`: Resized images

Files older than 1 hour are automatically cleaned up.

## License

MIT License - feel free to use this project for your own purposes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 