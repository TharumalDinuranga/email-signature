# app.py
import os
import subprocess
from flask import Flask, render_template, request, send_file
import yaml

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SIGNATURE_GENERATOR_DIR = os.path.join(BASE_DIR, "email-signature")
CONFIG_PATH = os.path.join(SIGNATURE_GENERATOR_DIR, "config.yaml")
SIGNATURE_PATH = os.path.join(BASE_DIR, "generated", "signature.html")

# Ensure generated directory exists
os.makedirs(os.path.dirname(SIGNATURE_PATH), exist_ok=True)

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
                },
                "image_url": ""  # Set empty since image upload is removed
            }
        }

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
