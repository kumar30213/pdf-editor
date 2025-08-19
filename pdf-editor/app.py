from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
import os
import fitz  # PyMuPDF
from werkzeug.utils import secure_filename
import uuid
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['STATIC_PREVIEWS'] = os.path.join('static', 'previews')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['STATIC_PREVIEWS'], exist_ok=True)

def generate_preview(pdf_path, output_folder):
    def process_page(page_num):
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        filename = f"{uuid.uuid4()}.png"
        filepath = os.path.join(output_folder, filename)
        pix.save(filepath)
        doc.close()
        return f"previews/{filename}"

    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    doc.close()
    with ThreadPoolExecutor(max_workers=8) as executor:
        previews = list(executor.map(process_page, range(num_pages)))
    return previews

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if 'file' not in request.files:
            return "No file uploaded", 400
        file = request.files['file']
        if file.filename == '':
            return "Empty filename", 400
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(pdf_path)
        return redirect(url_for('preview', pdf_id=filename))
    return render_template("upload.html")

@app.route("/preview/<pdf_id>", methods=["GET"])
def preview(pdf_id):
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_id)
    previews = generate_preview(pdf_path, app.config['STATIC_PREVIEWS'])
    return render_template("preview.html", previews=previews, pdf_id=pdf_id)

@app.route("/remove_page/<pdf_id>/<int:page_num>", methods=["POST"])
def remove_page(pdf_id, page_num):
    import shutil
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_id)
    temp_path = pdf_path + ".tmp"
    doc = fitz.open(pdf_path)
    if 0 <= page_num < len(doc):
        doc.delete_page(page_num)
        doc.save(temp_path)
        doc.close()
        shutil.move(temp_path, pdf_path)
    else:
        doc.close()
    return jsonify({"success": True})

@app.route("/insert_pdf/<pdf_id>", methods=["POST"])
def insert_pdf(pdf_id):
    import shutil
    position = int(request.form.get('position', 0))
    file = request.files.get('file')
    if not file or file.filename == '':
        return "No file uploaded", 400
    insert_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(insert_path)
    main_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_id)
    temp_path = main_path + ".tmp"
    main_doc = fitz.open(main_path)
    insert_doc = fitz.open(insert_path)
    for i in range(len(insert_doc)):
        main_doc.insert_pdf(insert_doc, from_page=i, to_page=i, start_at=position + i)
    main_doc.save(temp_path)
    main_doc.close()
    insert_doc.close()
    shutil.move(temp_path, main_path)
    return jsonify({"success": True})

@app.route("/finalize", methods=["POST"])
def finalize():
    data = request.get_json()
    pdf_id = data.get("pdf_id")
    if not pdf_id:
        return "Missing pdf_id", 400
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_id)
    if not os.path.exists(pdf_path):
        return "PDF not found", 404
    return send_file(pdf_path, as_attachment=True, download_name=pdf_id)

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
