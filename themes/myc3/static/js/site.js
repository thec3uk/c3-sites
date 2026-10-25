// Loaded before Alpine (both deferred), so this registers on alpine:init.
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

document.addEventListener("alpine:init", () => {
  Alpine.data("contactForm", () => ({
    submitted: false,
    sending: false,
    failed: false,
    errors: {},
    // Same rules and messages as Next's ContactForm.
    validate(f) {
      const v = (n) => f.elements[n]?.value.trim() ?? "";
      const errors = {};
      if (!v("name")) errors.name = "Name is required";
      if (!v("email")) errors.email = "Email is required";
      else if (!EMAIL.test(v("email"))) errors.email = "Please enter a valid email";
      if (f.elements.category && !v("category")) errors.category = "Please select a category";
      if (!v("subject")) errors.subject = "Subject is required";
      if (!v("message")) errors.message = "Message is required";
      if (!f.elements.consent.checked) errors.consent = "You must agree to continue";
      return errors;
    },
    clear(event) {
      delete this.errors[event.target.name];
    },
    async send(event) {
      const form = event.target;
      this.errors = this.validate(form);
      if (Object.keys(this.errors).length) return;
      this.sending = true;
      this.failed = false;
      const value = (n) => form.elements[n]?.value ?? "";
      try {
        const response = await fetch("/", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams({
            "form-name": value("form-name"),
            "bot-field": value("bot-field"),
            name: value("name"),
            email: value("email"),
            category: value("category"),
            subject: value("subject"),
            message: value("message"),
            consent: form.elements.consent.checked ? "yes" : "no",
          }).toString(),
        });
        if (!response.ok) throw new Error(response.status);
        this.submitted = true;
      } catch {
        this.failed = true;
      }
      this.sending = false;
    },
  }));
});
