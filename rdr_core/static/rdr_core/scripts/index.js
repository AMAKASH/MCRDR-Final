const form = document.getElementById("qa-form");
function toggleAB() {
  const sectionA = document.getElementById("section-A");
  const sectionB = document.getElementById("section-B");

  sectionA.classList.toggle("d-none");
  sectionB.classList.toggle("d-none");
  const yOffset = -50;
  if (form) {
    const y = form.getBoundingClientRect().top + window.scrollY + yOffset;
    window.scrollTo({ top: y, behavior: "smooth" });
  }
}
