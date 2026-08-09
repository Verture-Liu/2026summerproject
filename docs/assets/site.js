const menuToggle = document.getElementById("menu-toggle");
const siteNav = document.getElementById("site-nav");
const copyButton = document.getElementById("copy-command");
const installCommand = document.getElementById("install-command");

if (menuToggle && siteNav) {
  menuToggle.addEventListener("click", () => {
    const expanded = menuToggle.getAttribute("aria-expanded") === "true";
    menuToggle.setAttribute("aria-expanded", String(!expanded));
    siteNav.classList.toggle("open", !expanded);
  });

  siteNav.addEventListener("click", (event) => {
    if (!event.target.closest("a")) return;
    menuToggle.setAttribute("aria-expanded", "false");
    siteNav.classList.remove("open");
  });
}

const selectCommandText = () => {
  if (!installCommand || !window.getSelection) return;
  const range = document.createRange();
  range.selectNodeContents(installCommand);
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
};

if (copyButton && installCommand) {
  copyButton.addEventListener("click", async () => {
    const originalLabel = copyButton.textContent;
    const command = installCommand.textContent.trim();
    try {
      if (!navigator.clipboard) throw new Error("Clipboard API unavailable");
      await navigator.clipboard.writeText(command);
      copyButton.textContent = "Copied";
    } catch (_) {
      selectCommandText();
      copyButton.textContent = "Selected — press Ctrl/Cmd+C";
    }
    window.setTimeout(() => {
      copyButton.textContent = originalLabel;
    }, 1800);
  });
}
