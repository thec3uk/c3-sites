// Loaded before Alpine (both deferred), so these register on alpine:init.
const BANNER_KEY = "NOTIFICATIONBAR";

function readDismissed() {
  try {
    return JSON.parse(localStorage.getItem(BANNER_KEY)) || [];
  } catch {
    return [];
  }
}

// Mailchimp's post-json endpoint only answers JSONP, as in gatsby-plugin-mailchimp.
function jsonp(url, timeout = 10000) {
  return new Promise((resolve, reject) => {
    const name = "__mc" + Math.random().toString(36).slice(2);
    const script = document.createElement("script");
    const done = () => {
      clearTimeout(timer);
      delete window[name];
      script.remove();
    };
    const timer = setTimeout(() => {
      done();
      reject(new Error("timeout"));
    }, timeout);
    window[name] = (data) => {
      done();
      resolve(data);
    };
    script.onerror = () => {
      done();
      reject(new Error("network"));
    };
    script.src = url + "&c=" + name;
    document.head.append(script);
  });
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

  Alpine.data("contactForm", () => ({
    submitted: false,
    sending: false,
    failed: false,
    valid: false,
    init() {
      this.check();
    },
    // Same rules as Gatsby's contactForm.tsx.
    check() {
      const f = this.$root.querySelector("form");
      const v = (n) => f.elements[n].value;
      // Derive the recipient so autofilled or restored selects still count.
      f.elements.email_recipient.value = f.elements.category_name.selectedOptions[0]?.dataset.recipient ?? "";
      this.valid =
        v("email_recipient") !== "" &&
        v("message").length > 10 &&
        v("name").length > 3 &&
        v("email").includes("@") &&
        v("subject").length > 3;
    },
    pick() {
      this.check();
    },
    async send(event) {
      const form = event.target;
      if (!this.valid) return;
      this.sending = true;
      this.failed = false;
      try {
        const response = await fetch("/", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams(new FormData(form)).toString(),
        });
        if (!response.ok) throw new Error(response.status);
        this.submitted = true;
      } catch {
        this.failed = true;
      }
      this.sending = false;
    },
  }));

  Alpine.data("newsletter", () => ({
    status: "pending",
    thanks: "",
    message: "",
    async send(event) {
      const form = event.target;
      const field = (n) => form.elements[n];
      const locations = [...form.querySelectorAll("[name=LOCATION]:checked")].map((c) => c.value);
      const params = new URLSearchParams({
        EMAIL: field("EMAIL").value,
        FNAME: field("FNAME").value,
        LOCATION: '"' + locations.join('", "') + '"',
        SIGNUPURL: document.location.pathname,
        SOURCE: field("SOURCE").value,
      });
      this.status = "sending";
      this.message = "";
      try {
        const url = form.action.replace("/post?", "/post-json?") + "&" + params;
        const result = await jsonp(url);
        if (result.result === "success") {
          this.thanks = result.msg;
          this.status = "success";
        } else {
          this.message = result.msg;
          this.status = "error";
        }
      } catch {
        this.message = "Sorry, we could not subscribe you. Please try again.";
        this.status = "error";
      }
    },
  }));
});
