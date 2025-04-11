# app.py
import os
import subprocess
from flask import Flask, render_template, request, send_file
import yaml
# import boto3
import uuid
import base64
from io import BytesIO

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SIGNATURE_GENERATOR_DIR = os.path.join(BASE_DIR, "email-signature")
CONFIG_PATH = os.path.join(SIGNATURE_GENERATOR_DIR, "config.yaml")
SIGNATURE_PATH = os.path.join(BASE_DIR, "generated", "signature.html")

# Ensure generated directory exists
os.makedirs(os.path.dirname(SIGNATURE_PATH), exist_ok=True)

# AWS S3 Configuration (Ideally, use environment variables)
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_S3_BUCKET_NAME = os.environ.get('AWS_S3_BUCKET_NAME')
AWS_S3_REGION = os.environ.get('AWS_S3_REGION', 'ap-south-1') # Default to Mumbai region

# s3 = boto3.client(
#     's3',
#     aws_access_key_id=AWS_ACCESS_KEY_ID,
#     aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
#     region_name=AWS_S3_REGION
# )

@app.route("/", methods=["GET", "POST"])
def generate_signature():
    if request.method == "POST":
        user_data = {
            "personal": {
                "first_name": request.form["first_name"],
                "last_name": request.form["last_name"],
                "phone": request.form.get("phone", ""),
                "email": request.form.get("email", ""),
                "position": request.form["position"],
                "education": request.form.get("education", ""),
                "social": {
                    "x_handle": request.form.get("x_handle", ""),
                    "linkedin_handle": request.form.get("linkedin_handle", "")
                }
            }
        }

        cropped_image_data = request.form.get("cropped_image_data")
        if cropped_image_data:
            try:
                # Decode base64 image data
                header, encoded = cropped_image_data.split(',', 1)
                image_data = base64.b64decode(encoded)
                image_type = header.split(';')[0].split(':')[1]
                file_extension = image_type.split('/')[1]

                # Generate unique filename
                image_filename = f"{uuid.uuid4()}.{file_extension}"
                s3_key = f"profile_images/{image_filename}"

                # Upload to S3
                # s3df.upload_fileobj(BytesIO(image_data), AWS_S3_BUCKET_NAME, s3_key, ExtraArgs={'ContentType': image_type, 'ACL': 'public-read'})

                # Get the public URL
                s3_url = f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_S3_REGION}.amazonaws.com/{s3_key}"
                user_data["personal"]["image_url"] = s3_url
            except Exception as e:
                return f"Error uploading image to S3: {e}", 500
        else:
            user_data["personal"]["image_url"] = ""

        # Save user input to config.yaml
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(user_data, f)

        # Run generate_signature.py
        try:
            subprocess.run(["python", os.path.join(SIGNATURE_GENERATOR_DIR, "generate_signature.py")], cwd=SIGNATURE_GENERATOR_DIR, check=True)

            # Move generated file
            generated_signature_path = os.path.join(SIGNATURE_GENERATOR_DIR, "generated", "signature.html")
            if os.path.exists(generated_signature_path):
                os.replace(generated_signature_path, SIGNATURE_PATH)
        except subprocess.CalledProcessError as e:
            return f"Error generating signature: {e}", 500

        # Read the generated signature content for preview
        with open(SIGNATURE_PATH, 'r') as f:
            signature_html = f.read()

        return render_template("success.html", signature_path="/download", signature_html=signature_html)

    return render_template("form.html")

@app.route("/download")
def download_file():
    if not os.path.exists(SIGNATURE_PATH):
        return "Signature file not found. Please generate it first.", 404
    return send_file(SIGNATURE_PATH, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)