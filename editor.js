window.pageWraps = window.pageWraps || [];
import { runOCRForPage } from "./ocr.js";
import * as pdfjsLib from "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.5.136/pdf.min.mjs";
import { injectOCRTextToOverlay } from "./ocr.js";
import { makeThumbnailsSortable, enableMobileReordering } from "./pages.js";

if (window.pdfjsLib) {
  pdfjsLib.GlobalWorkerOptions.workerSrc = 
    'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.5.136/pdf.worker.min.mjs';
}

// Application State
let rawPdfBytes = null;
let pdfDoc = null;
let currentScale = 1.4;
let activeTool = null;
let isEditTextMode = false;
let activeColor = "#ff0000";
let activePageNum = 1;

// View Flags
let panMode = false;
let twoPageMode = false;

// PDF & Rendering State
let pageWraps = [];
let textContentCache = [];
let pageRotations = [];

// Trackers for modifications
const editedTextMap = new Map();
let addedTextBoxes = [];
let stickyNotes = [];
let placedImages = [];

// Search Engine State
let matches = [];
let matchElements = [];
let currentMatchIndex = -1;

// History Engine
const undoStack = [];
const redoStack = [];

function recordAction(action) {
  undoStack.push(action);
  redoStack.length = 0;
  updateUndoRedoUI();
}

function updateUndoRedoUI() {
  const undoBtn = document.getElementById("undoBtn");
  const redoBtn = document.getElementById("redoBtn");
  if (undoBtn) undoBtn.disabled = undoStack.length === 0;
  if (redoBtn) redoBtn.disabled = redoStack.length === 0;
}

function undo() {
  if (!undoStack.length) return;
  const action = undoStack.pop();
  redoStack.push(action);
  applyActionState(action, "undo");
  updateUndoRedoUI();
}

function redo() {
  if (!redoStack.length) return;
  const action = redoStack.pop();
  undoStack.push(action);
  applyActionState(action, "redo");
  updateUndoRedoUI();
}

function applyActionState(action, type) {
  const isUndo = type === "undo";

  switch (action.type) {
    case "DRAW": {
      const pw = pageWraps[action.pageIndex];
      if (pw) {
        const ctx = pw.drawCanvas.getContext("2d");
        ctx.putImageData(isUndo ? action.prevState : action.nextState, 0, 0);
      }
      break;
    }
    case "EDIT_TEXT": {
      const { itemKey, prevText, nextText } = action;
      const data = editedTextMap.get(itemKey);
      if (data) data.newText = isUndo ? prevText : nextText;
      const span = document.querySelector(`[data-item-key="${itemKey}"]`);
      if (span) span.innerText = isUndo ? prevText : nextText;
      break;
    }
    case "ADD_TEXT": {
      if (isUndo) {
        addedTextBoxes = addedTextBoxes.filter((t) => t.id !== action.boxData.id);
        const el = document.getElementById(`added-text-${action.boxData.id}`);
        if (el) el.remove();
      } else {
        addedTextBoxes.push(action.boxData);
        renderAddedTextBox(action.boxData);
      }
      break;
    }
    case "WHITEOUT": {
      const pw = pageWraps[action.pageIndex];
      if (pw) {
        if (isUndo) {
          const el = pw.wrap.querySelector(`[data-whiteout-id="${action.id}"]`);
          if (el) el.remove();
        } else {
          renderWhiteoutRect(action.pageIndex, action.x, action.y, action.id);
        }
      }
      break;
    }
    case "ADD_IMAGE": {
      if (isUndo) {
        placedImages = placedImages.filter((img) => img.id !== action.imageData.id);
        const el = document.getElementById(`placed-img-${action.imageData.id}`);
        if (el) el.remove();
      } else {
        placedImages.push(action.imageData);
        renderPlacedImage(action.imageData);
      }
      break;
    }
    case "DELETE_IMAGE": {
      if (isUndo) {
        placedImages.push(action.imageData);
        renderPlacedImage(action.imageData);
      } else {
        placedImages = placedImages.filter((img) => img.id !== action.imageData.id);
        const el = document.getElementById(`placed-img-${action.imageData.id}`);
        if (el) el.remove();
      }
      break;
    }
  }
}

// Global Keyboard Shortcuts
document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
    e.preventDefault();
    e.shiftKey ? redo() : undo();
  } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "y") {
    e.preventDefault();
    redo();
  }
});

// DOM Elements
const fileInput = document.getElementById("pdfFile");
const viewer = document.getElementById("viewer");
const thumbs = document.getElementById("thumbnails");
const panBtn = document.getElementById("panBtn");
const twoPageBtn = document.getElementById("twoPageBtn");
const fitPageBtn = document.getElementById("fitPageBtn");
const fitWidthBtn = document.getElementById("fitWidthBtn");
const searchInput = document.getElementById("searchInput");
const searchPrev = document.getElementById("searchPrev");
const searchNext = document.getElementById("searchNext");
const searchCount = document.getElementById("searchCount");
const drawColorInput = document.getElementById("drawColor");
const textFontSizeInput = document.getElementById("textFontSize");
const textFontFamilyInput = document.getElementById("textFontFamily");
const editTextBtn = document.getElementById("editTextBtn");
const imageLoader = document.getElementById("imageLoader");
const ocrToolBtn = document.getElementById("ocrToolBtn");

if (ocrToolBtn) {
  const ocrToolBtnOriginalHTML = ocrToolBtn.innerHTML;

  ocrToolBtn.onclick = async () => {
    if (!pdfDoc) return alert("Please open a PDF first.");

    ocrToolBtn.disabled = true;
    let totalLines = 0;

    try {
      // Run OCR across every page, not just the currently active one.
      for (let i = 0; i < pdfDoc.numPages; i++) {
        const canvas = pageWraps[i]?.canvas;
        if (!canvas) continue;

        ocrToolBtn.innerText = `Processing ${i + 1}/${pdfDoc.numPages}...`;

        // Correct endpoint: /api/ocr (this used to point at /run-ocr, which does
        // not exist in app.py, so OCR always silently failed).
        const ocrLines = await runOCRForPage(canvas);

        // Draws editable, double-click-to-edit spans over this page.
        renderOCRLayer(ocrLines, i);
        totalLines += ocrLines.length;
      }

      showOCRToast(`${totalLines} editable lines detected across ${pdfDoc.numPages} page(s). Double-click any line to edit.`);
    } catch (err) {
      console.error("OCR execution error:", err);
      showOCRToast(`OCR Failed: ${err.message}`, true);
    } finally {
      ocrToolBtn.disabled = false;
      ocrToolBtn.innerHTML = ocrToolBtnOriginalHTML;
    }
  };
}
const reorderToolBtn = document.getElementById("reorderToolBtn");
const sidebar = document.getElementById("sidebar"); // or the sidebar element ID/class in your DOM

if (reorderToolBtn) {
  reorderToolBtn.onclick = () => {
    // 1. Toggle blue active color on button
    reorderToolBtn.classList.toggle("active");
    
    // 2. Toggle sidebar visibility
    if (sidebar) {
      sidebar.classList.toggle("open"); 
      // Or if using inline styles:
      // sidebar.style.display = sidebar.style.display === "none" ? "flex" : "none";
    }
  };
}

const undoBtn = document.getElementById("undoBtn");
const redoBtn = document.getElementById("redoBtn");
if (undoBtn) undoBtn.onclick = undo;
if (redoBtn) redoBtn.onclick = redo;

const toolbarRotateBtn = document.getElementById("toolbarRotateBtn");
const deletePageBtn = document.getElementById("deletePageBtn");
const addBlankPageBtn = document.getElementById("addBlankPageBtn");

// File Reader
fileInput.addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  rawPdfBytes = await file.arrayBuffer();
  pdfDoc = await pdfjsLib.getDocument({ data: rawPdfBytes.slice(0) }).promise;

  textContentCache = new Array(pdfDoc.numPages).fill(null);
  pageRotations = new Array(pdfDoc.numPages).fill(0);
  editedTextMap.clear();
  addedTextBoxes = [];
  stickyNotes = [];
  placedImages = [];
  undoStack.length = 0;
  redoStack.length = 0;
  updateUndoRedoUI();

  resetSearch();
  await renderAllPages();
});

// Render Document Pages & Wire Drag and Drop
// Render Document Pages & Wire Drag and Drop
async function renderAllPages() {
  viewer.innerHTML = "";
  thumbs.innerHTML = "";

  // Assign pageWraps to window so OCR functions and DevTools can access it
  window.pageWraps = [];
  pageWraps = window.pageWraps;

  for (let i = 1; i <= pdfDoc.numPages; i++) {
    const page = await pdfDoc.getPage(i);
    const rotation = pageRotations[i - 1] || 0;
    const viewport = page.getViewport({ scale: currentScale, rotation });

    const wrap = document.createElement("div");
    wrap.className = "page-wrap";
    wrap.dataset.pageIndex = i - 1;
    wrap.style.width = viewport.width + "px";
    wrap.style.height = viewport.height + "px";

    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    await page.render({ canvasContext: ctx, viewport }).promise;

    const overlay = document.createElement("div");
    overlay.className = "pdf-overlay";

    const drawCanvas = document.createElement("canvas");
    drawCanvas.className = "annotation-layer";
    drawCanvas.width = viewport.width;
    drawCanvas.height = viewport.height;

    wrap.appendChild(canvas);
    wrap.appendChild(overlay);
    wrap.appendChild(drawCanvas);
    viewer.appendChild(wrap);

    pageWraps.push({ wrap, canvas, drawCanvas, overlay, viewport });

    setupDrawingEvents(drawCanvas, i - 1);
    await renderEditableTextLayer(i - 1);
    await renderThumbnail(page, i, rotation);
  }

  // ATTACH DRAG-AND-DROP REORDERING TO SIDEBAR THUMBNAILS
  makeThumbnailsSortable(thumbs, handlePageReorder);
  enableMobileReordering(thumbs, handlePageReorder);

  viewer.classList.toggle("two-page", twoPageMode);
}

// -------------------------------------------------------------
// REORDER PAGE HANDLER
// -------------------------------------------------------------
async function handlePageReorder(fromIndex, toIndex) {
  if (!rawPdfBytes) return;

  const pdfDocLib = await PDFLib.PDFDocument.load(rawPdfBytes);
  const pageIndices = pdfDocLib.getPageIndices();
  
  const [movedIndex] = pageIndices.splice(fromIndex, 1);
  pageIndices.splice(toIndex, 0, movedIndex);

  const newPdfLib = await PDFLib.PDFDocument.create();
  const copiedPages = await newPdfLib.copyPages(pdfDocLib, pageIndices);
  copiedPages.forEach((p) => newPdfLib.addPage(p));

  // Update document memory structures to keep alignment
  const [movedRotation] = pageRotations.splice(fromIndex, 1);
  pageRotations.splice(toIndex, 0, movedRotation);

  const [movedTextCache] = textContentCache.splice(fromIndex, 1);
  textContentCache.splice(toIndex, 0, movedTextCache);

  rawPdfBytes = await newPdfLib.save();
  pdfDoc = await pdfjsLib.getDocument({ data: rawPdfBytes.slice(0) }).promise;
  
  await renderAllPages();
}

// -------------------------------------------------------------
// PAGE MANIPULATION TOOLS (ADD, DELETE, ROTATE)
// -------------------------------------------------------------
if (addBlankPageBtn) {
  addBlankPageBtn.onclick = async () => {
    if (!rawPdfBytes) return;
    const pdfDocLib = await PDFLib.PDFDocument.load(rawPdfBytes);
    pdfDocLib.addPage([600, 800]);

    rawPdfBytes = await pdfDocLib.save();
    pdfDoc = await pdfjsLib.getDocument({ data: rawPdfBytes.slice(0) }).promise;
    
    textContentCache.push(null);
    pageRotations.push(0);
    await renderAllPages();
  };
}

if (deletePageBtn) {
  deletePageBtn.onclick = async () => {
    if (!rawPdfBytes || pdfDoc.numPages <= 1) return;
    const targetIdx = activePageNum - 1;

    const pdfDocLib = await PDFLib.PDFDocument.load(rawPdfBytes);
    pdfDocLib.removePage(targetIdx);

    rawPdfBytes = await pdfDocLib.save();
    pdfDoc = await pdfjsLib.getDocument({ data: rawPdfBytes.slice(0) }).promise;

    textContentCache.splice(targetIdx, 1);
    pageRotations.splice(targetIdx, 1);
    activePageNum = Math.max(1, activePageNum - 1);
    await renderAllPages();
  };
}

if (toolbarRotateBtn) {
  toolbarRotateBtn.onclick = async () => {
    if (!pdfDoc) return;
    const idx = activePageNum - 1;
    pageRotations[idx] = ((pageRotations[idx] || 0) + 90) % 360;
    await renderAllPages();
  };
}

// -------------------------------------------------------------
// LIVE SEARCH ENGINE
// -------------------------------------------------------------
function resetSearch() {
  matches = [];
  matchElements.forEach((el) => el.remove());
  matchElements = [];
  currentMatchIndex = -1;
  if (searchCount) searchCount.innerText = "";
}

async function performSearch(query) {
  resetSearch();
  if (!query || !pdfDoc) return;

  for (let i = 0; i < pdfDoc.numPages; i++) {
    const textContent = await getPageTextContent(i);
    const pw = pageWraps[i];

    textContent.items.forEach((item) => {
      const text = item.str;
      let matchIdx = text.toLowerCase().indexOf(query.toLowerCase());

      if (matchIdx !== -1) {
        const box = computeItemBox(item, pw.viewport);
        const highlight = document.createElement("div");
        highlight.className = "text-highlight";
        highlight.style.left = `${box.left}px`;
        highlight.style.top = `${box.top}px`;
        highlight.style.width = `${box.width}px`;
        highlight.style.height = `${box.height}px`;

        pw.wrap.appendChild(highlight);
        matches.push({ pageIndex: i, element: highlight });
        matchElements.push(highlight);
      }
    });
  }

  if (matches.length > 0) {
    currentMatchIndex = 0;
    highlightMatch(currentMatchIndex);
  }
}

function highlightMatch(index) {
  matches.forEach((m, i) => {
    m.element.classList.toggle("active-match", i === index);
  });
  if (matches[index]) {
    matches[index].element.scrollIntoView({ behavior: "smooth", block: "center" });
    if (searchCount) searchCount.innerText = `${index + 1}/${matches.length}`;
  }
}

if (searchInput) {
  searchInput.oninput = (e) => performSearch(e.target.value.trim());
}
if (searchNext) {
  searchNext.onclick = () => {
    if (!matches.length) return;
    currentMatchIndex = (currentMatchIndex + 1) % matches.length;
    highlightMatch(currentMatchIndex);
  };
}
if (searchPrev) {
  searchPrev.onclick = () => {
    if (!matches.length) return;
    currentMatchIndex = (currentMatchIndex - 1 + matches.length) % matches.length;
    highlightMatch(currentMatchIndex);
  };
}

// -------------------------------------------------------------
// IMAGE & SIGNATURE ENGINE
// -------------------------------------------------------------
if (imageLoader) {
  imageLoader.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const format = file.type === "image/png" ? "png" : "jpeg";
    const reader = new FileReader();

    reader.onload = (evt) => {
      const dataUrl = evt.target.result;
      const targetPageIndex = activePageNum - 1;

      const imageData = {
        id: Date.now(),
        pageIndex: targetPageIndex,
        x: 50,
        y: 50,
        width: 150,
        height: 100,
        dataUrl,
        format,
      };

      placedImages.push(imageData);
      renderPlacedImage(imageData);
      recordAction({ type: "ADD_IMAGE", imageData });
      imageLoader.value = "";
    };

    reader.readAsDataURL(file);
  });
}

function renderPlacedImage(imageData) {
  const pw = pageWraps[imageData.pageIndex];
  if (!pw) return;

  const wrapper = document.createElement("div");
  wrapper.className = "placed-image-wrapper";
  wrapper.id = `placed-img-${imageData.id}`;
  wrapper.style.left = `${imageData.x}px`;
  wrapper.style.top = `${imageData.y}px`;
  wrapper.style.width = `${imageData.width}px`;
  wrapper.style.height = `${imageData.height}px`;

  const img = document.createElement("img");
  img.src = imageData.dataUrl;

  const resizeHandle = document.createElement("div");
  resizeHandle.className = "resize-handle";

  wrapper.appendChild(img);
  wrapper.appendChild(resizeHandle);
  pw.wrap.appendChild(wrapper);

  let isDragging = false;
  let startX, startY, origX, origY;

  wrapper.addEventListener("mousedown", (e) => {
    if (activeTool === "delete-object") {
      e.stopPropagation();
      deletePlacedImage(imageData);
      return;
    }
    if (e.target === resizeHandle) return;

    isDragging = true;
    startX = e.clientX;
    startY = e.clientY;
    origX = imageData.x;
    origY = imageData.y;

    const onMouseMove = (moveEvent) => {
      if (!isDragging) return;
      imageData.x = origX + (moveEvent.clientX - startX);
      imageData.y = origY + (moveEvent.clientY - startY);
      wrapper.style.left = `${imageData.x}px`;
      wrapper.style.top = `${imageData.y}px`;
    };

    const onMouseUp = () => {
      isDragging = false;
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  });

  resizeHandle.addEventListener("mousedown", (e) => {
    e.stopPropagation();
    let isResizing = true;
    const startW = imageData.width;
    const startH = imageData.height;
    const startX = e.clientX;
    const startY = e.clientY;

    const onMouseMove = (moveEvent) => {
      if (!isResizing) return;
      imageData.width = Math.max(30, startW + (moveEvent.clientX - startX));
      imageData.height = Math.max(20, startH + (moveEvent.clientY - startY));
      wrapper.style.width = `${imageData.width}px`;
      wrapper.style.height = `${imageData.height}px`;
    };

    const onMouseUp = () => {
      isResizing = false;
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  });
}

function deletePlacedImage(imageData) {
  placedImages = placedImages.filter((img) => img.id !== imageData.id);
  const el = document.getElementById(`placed-img-${imageData.id}`);
  if (el) el.remove();
  recordAction({ type: "DELETE_IMAGE", imageData });
}

// -------------------------------------------------------------
// TOOLBAR SWITCHING & EDIT TEXT
// -------------------------------------------------------------
if (editTextBtn) {
  editTextBtn.onclick = () => {
    isEditTextMode = !isEditTextMode;
    editTextBtn.classList.toggle("active", isEditTextMode);

    if (isEditTextMode) {
      activeTool = null;
      document.querySelectorAll(".tool-btn").forEach((b) => b.classList.remove("active"));
    }

    document.querySelectorAll(".text-overlay").forEach((overlay) => {
      overlay.style.pointerEvents = isEditTextMode ? "auto" : "none";
    });
  };
}

document.querySelectorAll(".tool-btn[data-tool]").forEach((btn) => {
  btn.onclick = () => {
    document.querySelectorAll(".tool-btn").forEach((b) => b.classList.remove("active"));
    const selected = btn.dataset.tool;

    if (activeTool === selected) {
      activeTool = null;
    } else {
      activeTool = selected;
      btn.classList.add("active");

      if (isEditTextMode) {
        isEditTextMode = false;
        if (editTextBtn) editTextBtn.classList.remove("active");
        document.querySelectorAll(".text-overlay").forEach((overlay) => {
          overlay.style.pointerEvents = "none";
        });
      }
    }

    document.body.classList.toggle("delete-mode", activeTool === "delete-object");
  };
});

if (drawColorInput) drawColorInput.addEventListener("change", (e) => (activeColor = e.target.value));

async function renderEditableTextLayer(pageIdx) {
  const pw = pageWraps[pageIdx];
  const textContent = await getPageTextContent(pageIdx);
  const overlay = pw.overlay;

  overlay.innerHTML = "";
  overlay.style.pointerEvents = isEditTextMode ? "auto" : "none";

  textContent.items.forEach((item, itemIdx) => {
    if (!item.str.trim()) return;

    const box = computeItemBox(item, pw.viewport);
    const itemKey = `${pageIdx}_${itemIdx}`;

    const span = document.createElement("span");
    span.className = "editable-pdf-span";
    span.dataset.itemKey = itemKey;
    span.innerText = editedTextMap.has(itemKey) ? editedTextMap.get(itemKey).newText : item.str;

    span.style.cssText = `
      position: absolute; left: ${box.left}px; top: ${box.top}px;
      width: ${box.width}px; height: ${box.height}px; font-size: ${box.height}px;
      font-family: Arial, sans-serif; line-height: 1; color: #000; outline: none;
    `;

    span.ondblclick = (e) => {
      if (!isEditTextMode) return;
      e.stopPropagation();
      span.contentEditable = true;
      span.focus();
    };

    span.onblur = () => {
      if (span.contentEditable !== "true") return;
      span.contentEditable = false;
      const updatedText = span.innerText.trim();
      editedTextMap.set(itemKey, { originalItem: item, box, newText: updatedText, fontSize: box.height, color: activeColor, pageIndex: pageIdx });
    };

    overlay.appendChild(span);
  });
}

function setupDrawingEvents(canvas, pageIdx) {
  const ctx = canvas.getContext("2d");
  let isDrawing = false, startX = 0, startY = 0, prevState = null;

  canvas.onmousedown = (e) => {
    if (!activeTool || panMode || activeTool === "delete-object") return;
    const rect = canvas.getBoundingClientRect();
    startX = e.clientX - rect.left;
    startY = e.clientY - rect.top;

    if (activeTool === "text") {
      createNewTextBox(pageIdx, startX, startY);
      return;
    } else if (activeTool === "whiteout") {
      addWhiteoutRect(pageIdx, startX, startY);
      return;
    } else if (activeTool === "sticky-note") {
      createStickyNote(pageIdx, startX, startY);
      return;
    }

    isDrawing = true;
    prevState = ctx.getImageData(0, 0, canvas.width, canvas.height);
    ctx.beginPath();
    ctx.moveTo(startX, startY);
  };

  canvas.onmousemove = (e) => {
    if (!isDrawing || panMode) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    if (activeTool === "pen") {
      ctx.strokeStyle = activeColor;
      ctx.lineWidth = 2;
      ctx.lineTo(x, y);
      ctx.stroke();
    } else if (activeTool === "highlight") {
      ctx.strokeStyle = activeColor + "80";
      ctx.lineWidth = 12;
      ctx.lineTo(x, y);
      ctx.stroke();
    } else if (activeTool === "eraser") {
      ctx.clearRect(x - 10, y - 10, 20, 20);
    }
  };

  canvas.onmouseup = (e) => {
    if (!isDrawing || panMode) return;
    isDrawing = false;

    const rect = canvas.getBoundingClientRect();
    const endX = e.clientX - rect.left;
    const endY = e.clientY - rect.top;

    if (activeTool === "underline" || activeTool === "strikethrough") {
      // Strikethrough runs through the vertical middle of the drag;
      // underline sits at the height where the drag started.
      const lineY = activeTool === "strikethrough" ? (startY + endY) / 2 : startY;
      ctx.strokeStyle = activeColor;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(startX, lineY);
      ctx.lineTo(endX, lineY);
      ctx.stroke();
    } else if (activeTool === "rect") {
      ctx.strokeStyle = activeColor;
      ctx.lineWidth = 2;
      ctx.strokeRect(startX, startY, endX - startX, endY - startY);
    } else if (activeTool === "circle") {
      const rx = Math.abs(endX - startX) / 2;
      const ry = Math.abs(endY - startY) / 2;
      const cx = (startX + endX) / 2;
      const cy = (startY + endY) / 2;
      ctx.strokeStyle = activeColor;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.ellipse(cx, cy, rx, ry, 0, 0, 2 * Math.PI);
      ctx.stroke();
    } else if (activeTool === "line") {
      ctx.strokeStyle = activeColor;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(startX, startY);
      ctx.lineTo(endX, endY);
      ctx.stroke();
    } else if (activeTool === "arrow") {
      ctx.strokeStyle = activeColor;
      ctx.lineWidth = 2;
      drawArrow(ctx, startX, startY, endX, endY);
    }

    const nextState = ctx.getImageData(0, 0, canvas.width, canvas.height);
    recordAction({ type: "DRAW", pageIndex: pageIdx, prevState, nextState });
  };
}

function addWhiteoutRect(pageIdx, x, y) {
  const id = Date.now();
  renderWhiteoutRect(pageIdx, x, y, id);
  recordAction({ type: "WHITEOUT", pageIndex: pageIdx, x, y, id });
}

function renderWhiteoutRect(pageIdx, x, y, id) {
  const wrap = pageWraps[pageIdx].wrap;
  const block = document.createElement("div");
  block.className = "editable-element whiteout-block";
  block.dataset.whiteoutId = id;
  block.style.cssText = `left:${x}px;top:${y}px;width:100px;height:30px;background:white;box-shadow:0 0 0 1px rgba(0,0,0,0.12);position:absolute;z-index:5;`;

  block.onclick = () => {
    if (activeTool === "delete-object") block.remove();
  };

  wrap.appendChild(block);
}

function drawArrow(ctx, fromX, fromY, toX, toY) {
  const headLength = 10;
  const angle = Math.atan2(toY - fromY, toX - fromX);

  ctx.beginPath();
  ctx.moveTo(fromX, fromY);
  ctx.lineTo(toX, toY);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(toX, toY);
  ctx.lineTo(toX - headLength * Math.cos(angle - Math.PI / 6), toY - headLength * Math.sin(angle - Math.PI / 6));
  ctx.moveTo(toX, toY);
  ctx.lineTo(toX - headLength * Math.cos(angle + Math.PI / 6), toY - headLength * Math.sin(angle + Math.PI / 6));
  ctx.stroke();
}

function createStickyNote(pageIdx, x, y) {
  const pw = pageWraps[pageIdx];
  const noteId = Date.now();

  const icon = document.createElement("div");
  icon.className = "sticky-note-icon";
  icon.textContent = "🗒️";
  icon.style.cssText = `position:absolute;left:${x}px;top:${y}px;font-size:22px;cursor:pointer;z-index:15;`;

  const noteBox = document.createElement("div");
  noteBox.className = "sticky-note-box";
  noteBox.contentEditable = true;
  noteBox.style.cssText = `position:absolute;left:${x + 26}px;top:${y}px;width:160px;min-height:60px;background:#fff9c4;border:1px solid #e0c94a;border-radius:4px;padding:6px;font-size:13px;box-shadow:0 2px 6px rgba(0,0,0,0.25);z-index:16;outline:none;`;

  icon.onclick = () => {
    if (activeTool === "delete-object") {
      icon.remove();
      noteBox.remove();
      stickyNotes = stickyNotes.filter((n) => n.id !== noteId);
      return;
    }
    noteBox.style.display = noteBox.style.display === "none" ? "block" : "none";
    if (noteBox.style.display === "block") noteBox.focus();
  };

  noteBox.onblur = () => {
    const text = noteBox.innerText.trim();
    stickyNotes = stickyNotes.filter((n) => n.id !== noteId);
    if (text) {
      stickyNotes.push({ id: noteId, pageIndex: pageIdx, x, y, text });
    }
    noteBox.style.display = "none";
  };

  pw.wrap.appendChild(icon);
  pw.wrap.appendChild(noteBox);
  setTimeout(() => noteBox.focus(), 0);
}

function createNewTextBox(pageIdx, x, y) {
  const pw = pageWraps[pageIdx];
  const fontSize = textFontSizeInput ? parseInt(textFontSizeInput.value, 10) : 16;
  const fontFamily = textFontFamilyInput ? textFontFamilyInput.value : "Arial, sans-serif";
  const input = document.createElement("div");
  input.contentEditable = true;
  input.className = "added-text-input";
  input.style.cssText = `position:absolute;left:${x}px;top:${y}px;font-size:${fontSize}px;font-family:${fontFamily};color:${activeColor};border:1px dashed #2563eb;background:rgba(255,255,255,0.9);padding:2px 4px;outline:none;z-index:10;`;

  pw.wrap.appendChild(input);
  setTimeout(() => input.focus(), 0);

  input.onblur = () => {
    const text = input.innerText.trim();
    if (text) {
      const boxData = { id: Date.now(), pageIndex: pageIdx, x, y, text, fontSize, fontFamily, color: activeColor };
      addedTextBoxes.push(boxData);
      input.id = `added-text-${boxData.id}`;
      input.contentEditable = false;
      input.style.border = "none";
      input.style.background = "transparent";

      input.onclick = () => {
        if (activeTool === "delete-object") input.remove();
      };

      recordAction({ type: "ADD_TEXT", boxData });
    } else {
      input.remove();
    }
  };
}

function renderAddedTextBox(boxData) {
  const pw = pageWraps[boxData.pageIndex];
  if (!pw) return;
  const input = document.createElement("div");
  input.id = `added-text-${boxData.id}`;
  input.className = "added-text-input";
  input.innerText = boxData.text;
  input.style.cssText = `position:absolute;left:${boxData.x}px;top:${boxData.y}px;font-size:${boxData.fontSize}px;font-family:${boxData.fontFamily || "Arial, sans-serif"};color:${boxData.color};z-index:10;`;

  input.onclick = () => {
    if (activeTool === "delete-object") input.remove();
  };

  pw.wrap.appendChild(input);
}

/**
 * Custom Toast / Status Badge Notification Component
 */
function showOCRToast(message, isError = false) {
  let toast = document.getElementById("ocr-toast-badge");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "ocr-toast-badge";
    toast.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      padding: 12px 20px;
      background: #1e293b;
      color: #ffffff;
      border-radius: 8px;
      font-family: Inter, sans-serif;
      font-size: 14px;
      font-weight: 500;
      box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
      z-index: 9999;
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      gap: 10px;
    `;
    document.body.appendChild(toast);
  }

  toast.style.backgroundColor = isError ? "#ef4444" : "#0f172a";
  toast.innerHTML = isError
    ? `<span>⚠️ ${message}</span>`
    : `<span style="color: #4ade80;">✓</span> <div><strong>OCR Complete</strong><br><small style="color: #94a3b8;">${message}</small></div>`;

  toast.style.opacity = "1";
  setTimeout(() => {
    toast.style.opacity = "0";
  }, 4000);
}

/**
 * Renders editable OCR text spans over a specific page overlay.
 */
export function renderOCRLayer(lines, pageIndex) {
  // Query page wrapper directly from DOM to prevent scope errors
  const pageWrapsList = document.querySelectorAll(".page-wrap");
  const pageWrap = pageWrapsList[pageIndex];

  if (!pageWrap) {
    console.error(`OCR Render Error: Missing .page-wrap element at index ${pageIndex}`);
    return;
  }

  const canvas = pageWrap.querySelector("canvas");
  let overlay = pageWrap.querySelector(".pdf-overlay");

  if (!canvas) {
    console.error(`OCR Render Error: Missing canvas inside .page-wrap at index ${pageIndex}`);
    return;
  }

  // Create overlay container dynamically if it doesn't exist
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.className = "pdf-overlay";
    pageWrap.appendChild(overlay);
  }

  // Calculate rendering scale
  const canvasRect = canvas.getBoundingClientRect();
  const scaleX = canvasRect.width / canvas.width;
  const scaleY = canvasRect.height / canvas.height;

  // Clear previous OCR overlay items
  overlay.innerHTML = "";

  lines.forEach((line) => {
    const span = document.createElement("span");
    span.className = "editable-pdf-span ocr-text";
    span.innerText = line.text;

    const left = line.bbox.x0 * scaleX;
    const top = line.bbox.y0 * scaleY;
    const width = line.bbox.width * scaleX;
    const height = line.bbox.height * scaleY;

    span.style.cssText = `
      position: absolute;
      left: ${left}px;
      top: ${top}px;
      width: ${width}px;
      height: ${height}px;
      font-size: ${Math.max(10, height * 0.75)}px;
      font-family: Arial, sans-serif;
      line-height: 1;
      color: transparent;
      background-color: transparent;
      outline: none;
      cursor: text;
      pointer-events: auto !important;
      z-index: 100 !important;
      user-select: text;
      box-sizing: border-box;
      white-space: nowrap;
      overflow: hidden;
    `;

    // Hover state
    span.addEventListener("mouseenter", () => {
      if (span.contentEditable !== "true") {
        span.style.backgroundColor = "rgba(37, 99, 235, 0.15)";
        span.style.outline = "1px dashed #2563eb";
      }
    });

    span.addEventListener("mouseleave", () => {
      if (span.contentEditable !== "true" && span.style.backgroundColor !== "rgb(255, 255, 128)") {
        span.style.backgroundColor = "transparent";
        span.style.outline = "none";
      }
    });

    // Double-click inline text editor trigger
    span.addEventListener("dblclick", (e) => {
      e.preventDefault();
      e.stopPropagation();
      span.contentEditable = "true";
      span.style.color = "#000000";
      span.style.backgroundColor = "#ffffff";
      span.style.outline = "2px solid #2563eb";
      span.style.zIndex = "1000";
      span.focus();
    });

    // Save and blur state
    span.addEventListener("blur", () => {
      span.contentEditable = "false";
      span.style.zIndex = "100";
      if (span.innerText.trim() !== line.text) {
        span.style.color = "#000000";
        span.style.backgroundColor = "#ffff80";
        span.style.outline = "1px solid #d97706";
      } else {
        span.style.color = "transparent";
        span.style.backgroundColor = "transparent";
        span.style.outline = "none";
      }
    });

    overlay.appendChild(span);
  });
}

// Sidebars & Zooming Helpers
async function renderThumbnail(page, pageNum, rotation) {
  const card = document.createElement("div");
  card.className = `thumb-card ${pageNum === activePageNum ? "current" : ""}`;
  
  // Set explicit page index and drag attributes
  card.dataset.pageIndex = pageNum - 1;
  card.setAttribute("draggable", "true");

  const smallViewport = page.getViewport({ scale: 0.2, rotation });
  const thumbCanvas = document.createElement("canvas");
  thumbCanvas.className = "thumb";
  thumbCanvas.width = smallViewport.width;
  thumbCanvas.height = smallViewport.height;

  const tctx = thumbCanvas.getContext("2d");
  await page.render({ canvasContext: tctx, viewport: smallViewport }).promise;

  const pageLabel = document.createElement("div");
  pageLabel.style.cssText = "font-size: 11px; margin-top: 4px; color: #4b5563; font-weight: bold;";
  pageLabel.innerText = `Page ${pageNum}`;

  card.appendChild(thumbCanvas);
  card.appendChild(pageLabel);

  card.onclick = (e) => {
    // Prevent triggering active card switch if mobile reorder buttons are clicked
    if (e.target.tagName === "BUTTON") return;
    activePageNum = pageNum;
    document.querySelectorAll(".thumb-card").forEach((c) => c.classList.remove("current"));
    card.classList.add("current");
    pageWraps[pageNum - 1]?.wrap.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  thumbs.appendChild(card);
}

async function getPageTextContent(pageIndex) {
  if (!textContentCache[pageIndex]) {
    const page = await pdfDoc.getPage(pageIndex + 1);
    textContentCache[pageIndex] = await page.getTextContent();
  }
  return textContentCache[pageIndex];
}

function computeItemBox(item, viewport) {
  const tx = pdfjsLib.Util.transform(viewport.transform, item.transform);
  const height = Math.hypot(tx[2], tx[3]);
  const width = item.width * Math.hypot(viewport.transform[0], viewport.transform[1]);
  return { left: tx[4], top: tx[5] - height, width, height };
}

fitPageBtn.onclick = async () => {
  if (!pdfDoc) return;
  const page = await pdfDoc.getPage(1);
  const natural = page.getViewport({ scale: 1, rotation: pageRotations[0] || 0 });
  currentScale = Math.min((viewer.clientWidth - 60) / natural.width, (viewer.clientHeight - 60) / natural.height);
  await renderAllPages();
};

fitWidthBtn.onclick = async () => {
  if (!pdfDoc) return;
  const page = await pdfDoc.getPage(1);
  const natural = page.getViewport({ scale: 1, rotation: pageRotations[0] || 0 });
  currentScale = (viewer.clientWidth - 60) / natural.width;
  await renderAllPages();
};

document.getElementById("zoomIn").onclick = async () => { if (pdfDoc) { currentScale += 0.2; await renderAllPages(); } };
document.getElementById("zoomOut").onclick = async () => { if (pdfDoc) { currentScale = Math.max(0.4, currentScale - 0.2); await renderAllPages(); } };
panBtn.onclick = () => { panMode = !panMode; panBtn.classList.toggle("active", panMode); viewer.style.cursor = panMode ? "grab" : "default"; };
twoPageBtn.onclick = () => { twoPageMode = !twoPageMode; twoPageBtn.classList.toggle("active", twoPageMode); viewer.classList.toggle("two-page", twoPageMode); };

// Small helpers used only by the Save export below.
function hexToRgb(hex) {
  if (!hex) return null;
  // Handle "rgb(r, g, b)" strings (what element.style.color returns) as
  // well as "#rrggbb" hex strings.
  const rgbMatch = hex.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
  if (rgbMatch) {
    return PDFLib.rgb(
      parseInt(rgbMatch[1], 10) / 255,
      parseInt(rgbMatch[2], 10) / 255,
      parseInt(rgbMatch[3], 10) / 255
    );
  }
  const hexMatch = hex.replace("#", "").match(/^([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i);
  if (!hexMatch) return null;
  return PDFLib.rgb(
    parseInt(hexMatch[1], 16) / 255,
    parseInt(hexMatch[2], 16) / 255,
    parseInt(hexMatch[3], 16) / 255
  );
}

function dataUrlToUint8Array(dataUrl) {
  const base64 = dataUrl.split(",")[1];
  const binaryString = atob(base64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
}

// Save PDF
const savePdfBtn = document.getElementById("saveBtn");

if (savePdfBtn) {
  savePdfBtn.onclick = async () => {
    if (!pdfDoc) return alert("No PDF loaded to save.");

    try {
      // Use the original file bytes already held in memory (rawPdfBytes) —
      // there is no server URL for a locally-opened file, so re-fetching
      // "currentPdfUrl" (which was never defined anywhere) always failed.
      const { PDFDocument, rgb, StandardFonts } = PDFLib;
      const pdfDocLib = await PDFDocument.load(rawPdfBytes.slice(0));
      const font = await pdfDocLib.embedFont(StandardFonts.Helvetica);

      const pages = pdfDocLib.getPages();
      const pngEmbedPromises = [];

      // 2. Iterate through each page overlay to harvest edited OCR text
      pageWraps.forEach((wrap, pageIndex) => {
        const page = pages[pageIndex];
        const { width, height } = page.getSize();
        
        // Find all edited text spans inside the overlay (this used to look
        // for a class, "ocr-recognized-text", that renderOCRLayer never
        // actually creates — the real class is "ocr-text").
        const editedSpans = wrap.overlay.querySelectorAll(".ocr-text");
        const canvasRect = wrap.canvas.getBoundingClientRect();
        const scaleX = width / canvasRect.width;
        const scaleY = height / canvasRect.height;

        // First pass: compute every edit's geometry and draw ALL the white
        // cover rectangles before any text goes down. If two detected boxes
        // overlap (common on dense tables), drawing rect-then-text one edit
        // at a time let a later box's white rectangle silently erase an
        // earlier edit's text. Drawing every rectangle first, then every
        // piece of text on top, means an edit can never wipe out another.
        const pending = [];

        editedSpans.forEach((span) => {
          const text = span.innerText;

          // Only draw spans that have visible/edited text content
          if (text && span.style.backgroundColor !== "transparent") {
            const rect = span.getBoundingClientRect();

            const pdfX = (rect.left - canvasRect.left) * scaleX;
            // PDF coordinates start from bottom-left
            const pdfY = height - ((rect.top - canvasRect.top + rect.height) * scaleY);
            const boxHeightPdf = rect.height * scaleY;
            const boxWidthPdf = rect.width * scaleX;

            // Derive font size from the font's own metrics instead of a
            // guessed ratio, so it actually matches the detected box height.
            const unitHeight = font.heightAtSize(1);
            const fontSize = Math.max(6, boxHeightPdf / unitHeight);

            // Baseline sits a bit above the box's bottom edge to leave room
            // for descenders (roughly 20% of the font size), scaling with
            // text size instead of a flat pixel offset.
            const baselineY = pdfY + fontSize * 0.2;

            pending.push({ text, pdfX, pdfY, boxWidthPdf, boxHeightPdf, fontSize, baselineY });
          }
        });

        // Pass 1: cover every original word first.
        pending.forEach(({ pdfX, pdfY, boxWidthPdf, boxHeightPdf }) => {
          page.drawRectangle({
            x: pdfX,
            y: pdfY,
            width: boxWidthPdf,
            height: boxHeightPdf,
            color: rgb(1, 1, 1), // White
          });
        });

        // Pass 2: now draw every edited word on top, safe from being
        // covered by a later rectangle.
        pending.forEach(({ text, pdfX, fontSize, baselineY }) => {
          page.drawText(text, {
            x: pdfX,
            y: baselineY,
            size: fontSize,
            font: font,
            color: rgb(0, 0, 0), // Black
          });
        });

        // --- Whiteout boxes ---
        // These lived only in the browser before; Save never looked for
        // them at all, so they silently vanished from the downloaded PDF.
        wrap.wrap.querySelectorAll(".whiteout-block").forEach((block) => {
          const rect = block.getBoundingClientRect();
          const pdfX = (rect.left - canvasRect.left) * scaleX;
          const pdfY = height - ((rect.top - canvasRect.top + rect.height) * scaleY);
          page.drawRectangle({
            x: pdfX,
            y: pdfY,
            width: rect.width * scaleX,
            height: rect.height * scaleY,
            color: rgb(1, 1, 1),
          });
        });

        // --- Added text boxes ---
        // Same issue: typed text boxes showed up on screen but were never
        // read during export.
        wrap.wrap.querySelectorAll(".added-text-input").forEach((input) => {
          const text = input.innerText.trim();
          if (!text) return;
          const rect = input.getBoundingClientRect();
          const pdfX = (rect.left - canvasRect.left) * scaleX;
          const pdfY = height - ((rect.top - canvasRect.top + rect.height) * scaleY);
          const fontSizePx = parseFloat(input.style.fontSize) || 16;
          const fontSizePdf = fontSizePx * scaleY;
          page.drawText(text, {
            x: pdfX,
            y: pdfY + fontSizePdf * 0.2,
            size: fontSizePdf,
            font: font,
            color: hexToRgb(input.style.color) || rgb(0, 0, 0),
          });
        });

        // --- Sticky notes ---
        // PDF flattening can't reproduce click-to-expand behavior, so each
        // note is drawn as a small always-visible yellow box with its text,
        // positioned where its icon sits in the editor.
        stickyNotes
          .filter((note) => note.pageIndex === pageIndex)
          .forEach((note) => {
            const boxWidthPdf = 140 * scaleX;
            const boxHeightPdf = 60 * scaleY;
            const pdfX = (note.x + 26) * scaleX;
            const pdfY = height - (note.y * scaleY) - boxHeightPdf;

            page.drawRectangle({
              x: pdfX,
              y: pdfY,
              width: boxWidthPdf,
              height: boxHeightPdf,
              color: rgb(1, 0.976, 0.831), // matches the editor's note color
              borderColor: rgb(0.878, 0.788, 0.290),
              borderWidth: 1,
            });

            const noteFontSize = Math.max(6, 11 * scaleY);
            page.drawText(note.text, {
              x: pdfX + 4,
              y: pdfY + boxHeightPdf - noteFontSize,
              size: noteFontSize,
              font: font,
              color: rgb(0, 0, 0),
              maxWidth: boxWidthPdf - 8,
              lineHeight: noteFontSize * 1.2,
            });
          });

        // --- Native "Edit Text" changes (edits to the PDF's own real text
        // layer, tracked in editedTextMap) ---
        // This map was being filled in on every edit but nothing ever read
        // it back out at save time, so these edits were lost too.
        editedTextMap.forEach((data, itemKey) => {
          if (data.pageIndex !== pageIndex) return;
          if (data.newText.trim() === data.originalItem.str.trim()) return;

          const { box, newText, fontSize, color } = data;
          const pdfX = box.left * scaleX;
          const pdfY = height - (box.top + box.height) * scaleY;
          const boxHeightPdf = box.height * scaleY;

          page.drawRectangle({
            x: pdfX,
            y: pdfY,
            width: box.width * scaleX,
            height: boxHeightPdf,
            color: rgb(1, 1, 1),
          });

          page.drawText(newText, {
            x: pdfX,
            y: pdfY + boxHeightPdf * 0.2,
            size: (fontSize || box.height) * scaleY,
            font: font,
            color: hexToRgb(color) || rgb(0, 0, 0),
          });
        });

        // --- Pen / Highlight freehand drawings ---
        // These live on a separate transparent <canvas> layer that was
        // never flattened into the exported PDF either. Embed it as a
        // full-page transparent PNG so strokes land exactly where drawn.
        const drawDataUrl = wrap.drawCanvas.toDataURL("image/png");
        const drawPngBytes = dataUrlToUint8Array(drawDataUrl);
        pngEmbedPromises.push(
          pdfDocLib.embedPng(drawPngBytes).then((pngImage) => {
            page.drawImage(pngImage, { x: 0, y: 0, width, height });
          })
        );
      });

      // Wait for all annotation-layer images to finish embedding before saving.
      await Promise.all(pngEmbedPromises);

      // 3. Export and download the modified PDF
      const pdfBytes = await pdfDocLib.save();
      const blob = new Blob([pdfBytes], { type: "application/pdf" });
      const downloadLink = document.createElement("a");
      downloadLink.href = URL.createObjectURL(blob);
      downloadLink.download = "Edited_Document.pdf";
      downloadLink.click();

      alert("PDF exported successfully!");
    } catch (err) {
      console.error("Save Error:", err);
      alert("Failed to export modified PDF.");
    }
  };
}