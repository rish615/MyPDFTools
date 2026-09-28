
/**
 * OCR Client Module for MyPDF Studio (v1.3)
 * Handles sending canvas images to Flask and retrieving grouped text lines.
 */

/**
 * Sends a rendered canvas element to the Flask OCR endpoint.
 * @param {HTMLCanvasElement} canvasElement - The active page canvas.
 * @returns {Promise<Array>} Array of grouped line objects {text, bbox}.
 */
export async function runOCRForPage(canvasElement) {
  if (!canvasElement) {
    throw new Error("No active canvas available for OCR processing.");
  }

  // 1. Convert page canvas to PNG blob
  const imageBlob = await new Promise((resolve) => {
    canvasElement.toBlob(resolve, "image/png");
  });

  if (!imageBlob) {
    throw new Error("Failed to extract image data from canvas.");
  }

  // 2. Prepare multipart request body
  const formData = new FormData();
  formData.append("file", imageBlob, "page.png");

  // 3. Post canvas frame to Flask server
  const response = await fetch("/api/ocr", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Server status ${response.status}`);
  }

  const result = await response.json();

  // Fix 1: Validate result.lines instead of result.words
  if (!result.success || !Array.isArray(result.lines)) {
    throw new Error(result.error || "Invalid response structure from OCR server.");
  }

  return result.lines;
}
/**
 * 2. Injects OCR text overlay fallback helper
 */
export function injectOCRTextToOverlay(overlayElement, ocrWords, onTextEditCallback) {
  if (!overlayElement || !ocrWords) return;

  ocrWords.forEach((item, index) => {
    const span = document.createElement("span");
    span.className = "editable-pdf-span ocr-recognized-text";
    span.innerText = item.text;

    span.style.cssText = `
      position: absolute;
      left: ${item.bbox.x0}px;
      top: ${item.bbox.y0}px;
      width: ${item.bbox.width}px;
      height: ${item.bbox.height}px;
      font-size: ${Math.max(10, item.bbox.height * 0.75)}px;
      font-family: Arial, sans-serif;
      line-height: 1;
      color: transparent;
      outline: none;
      cursor: pointer;
      pointer-events: auto !important;
    `;

    span.ondblclick = (e) => {
      e.stopPropagation();
      const currentText = span.innerText;
      const userEditedText = prompt("Edit text:", currentText);

      if (userEditedText !== null && userEditedText !== currentText) {
        span.innerText = userEditedText;
        span.style.color = "#000000";
        span.style.backgroundColor = "#ffff80";

        if (typeof onTextEditCallback === "function") {
          onTextEditCallback(index, userEditedText);
        }
      }
    };

    overlayElement.appendChild(span);
  });
}