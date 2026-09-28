/**
 * Enables HTML5 Drag-and-Drop page thumbnail reordering.
 */
export function makeThumbnailsSortable(containerEl, onReorderCallback) {
  let draggedCard = null;
  const cards = containerEl.querySelectorAll(".thumb-card");

  cards.forEach((card, index) => {
    card.dataset.pageIndex = index;
    card.setAttribute("draggable", "true");

    card.addEventListener("dragstart", (e) => {
      draggedCard = card;
      card.classList.add("dragging");
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", index);
    });

    card.addEventListener("dragend", () => {
      card.classList.remove("dragging");
      cards.forEach((c) => c.classList.remove("drag-over"));
      draggedCard = null;
    });

    card.addEventListener("dragover", (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      if (card !== draggedCard) {
        card.classList.add("drag-over");
      }
    });

    card.addEventListener("dragleave", () => {
      card.classList.remove("drag-over");
    });

    card.addEventListener("drop", async (e) => {
      e.preventDefault();
      card.classList.remove("drag-over");

      if (draggedCard && draggedCard !== card) {
        const fromIndex = parseInt(draggedCard.dataset.pageIndex, 10);
        const toIndex = parseInt(card.dataset.pageIndex, 10);

        if (typeof onReorderCallback === "function") {
          await onReorderCallback(fromIndex, toIndex);
        }
      }
    });
  });
}

export function enableMobileReordering(containerEl, onReorderCallback) {
  const cards = containerEl.querySelectorAll(".thumb-card");

  cards.forEach((card) => {
    let mobileControls = card.querySelector(".mobile-reorder-controls");

    if (!mobileControls) {
      mobileControls = document.createElement("div");
      mobileControls.className = "mobile-reorder-controls";

      const moveUpBtn = document.createElement("button");
      moveUpBtn.className = "reorder-step-btn";
      moveUpBtn.innerText = "▲ Up";

      const moveDownBtn = document.createElement("button");
      moveDownBtn.className = "reorder-step-btn";
      moveDownBtn.innerText = "▼ Down";

      mobileControls.appendChild(moveUpBtn);
      mobileControls.appendChild(moveDownBtn);
      card.appendChild(mobileControls);

      moveUpBtn.onclick = async (e) => {
        e.stopPropagation();
        const currentIndex = parseInt(card.dataset.pageIndex, 10);
        if (currentIndex > 0) {
          await onReorderCallback(currentIndex, currentIndex - 1);
        }
      };

      moveDownBtn.onclick = async (e) => {
        e.stopPropagation();
        const currentIndex = parseInt(card.dataset.pageIndex, 10);
        if (currentIndex < cards.length - 1) {
          await onReorderCallback(currentIndex, currentIndex + 1);
        }
      };
    }
  });
}