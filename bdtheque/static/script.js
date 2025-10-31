document.querySelectorAll("input[type='checkbox']").forEach(box => {
  box.addEventListener("change", () => {
    fetch(`/toggle/${box.dataset.serie}/${box.dataset.num}`, { method: "POST" });
  });
});
