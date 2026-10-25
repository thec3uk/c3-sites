// Loaded before Alpine (both deferred), so these register on alpine:init.
const BANNER_KEY = "NOTIFICATIONBAR";

function readDismissed() {
  try {
    return JSON.parse(localStorage.getItem(BANNER_KEY)) || [];
  } catch {
    return [];
  }
}

document.addEventListener("alpine:init", () => {
  // Same {message, closed} list as the Gatsby site, so past dismissals carry over.
  Alpine.data("notificationBanner", () => ({
    open: false,
    message: "",
    init() {
      this.message = this.$el.dataset.message;
      this.open = !readDismissed().some((n) => n.message === this.message && n.closed);
    },
    close() {
      this.open = false;
      const dismissed = readDismissed();
      dismissed.push({ message: this.message, closed: true });
      try {
        localStorage.setItem(BANNER_KEY, JSON.stringify(dismissed));
      } catch {}
    },
  }));

  Alpine.data("mobileMenu", () => ({
    open: false,
    toggle() {
      this.open ? this.close() : this.show();
    },
    show() {
      this.open = true;
      document.body.style.overflow = "hidden";
      this.$nextTick(() => this.$refs.panel.querySelector("a").focus());
    },
    close() {
      if (!this.open) return;
      this.open = false;
      document.body.style.overflow = "";
      this.$refs.button.focus();
    },
  }));
});
