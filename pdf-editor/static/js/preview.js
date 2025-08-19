document.addEventListener("DOMContentLoaded", function () {
    let container = document.getElementById("previewContainer");

    // Handle remove buttons (AJAX)
    container.addEventListener("click", async function (e) {
        if (e.target.classList.contains("removeBtn")) {
            let pageNum = e.target.dataset.page;
            let pdfId = window.PDF_ID;
            e.target.disabled = true;
            e.target.textContent = "Removing...";
            let res = await fetch(`/remove_page/${pdfId}/${pageNum}`, {
                method: "POST"
            });
            let data = await res.json();
            if (data.success) {
                window.location.reload();
            } else {
                e.target.textContent = "Error";
            }
        }
    });

    // Handle insert PDF form (AJAX)
    document.getElementById("insertPdfForm").addEventListener("submit", async function (e) {
        e.preventDefault();
        let pdfId = window.PDF_ID;
        let formData = new FormData(this);
        let res = await fetch(`/insert_pdf/${pdfId}`, {
            method: "POST",
            body: formData
        });
        let data = await res.json();
        if (data.success) {
            window.location.reload();
        } else {
            alert("Insert failed: " + (data.message || "Unknown error"));
        }
    });

    // Finalize button (download PDF)
    document.getElementById("finalizeBtn").addEventListener("click", async function () {
        let pdfId = window.PDF_ID;
        const res = await fetch("/finalize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pdf_id: pdfId })
        });
        if (!res.ok) {
            alert("Failed to generate PDF");
            return;
        }
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = pdfId;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    });
});
