// ── Typing effect ────────────────────────────────────────
const phrases = [
  "Wallets for AI agents.",
  "Spending limits on-chain.",
  "Escrow for agent tasks.",
  "Compliance built in.",
  "One SDK call."
];

const el = document.getElementById("typed-text");
let phraseIdx = 0, charIdx = 0, deleting = false;

function type() {
  const phrase = phrases[phraseIdx];
  if (!deleting) {
    el.textContent = phrase.slice(0, ++charIdx);
    if (charIdx === phrase.length) {
      setTimeout(() => { deleting = true; type(); }, 1800);
      return;
    }
    setTimeout(type, 55);
  } else {
    el.textContent = phrase.slice(0, --charIdx);
    if (charIdx === 0) {
      deleting = false;
      phraseIdx = (phraseIdx + 1) % phrases.length;
      setTimeout(type, 400);
      return;
    }
    setTimeout(type, 30);
  }
}
type();

// ── Scroll reveal (IntersectionObserver) ────────────────
const reveals = document.querySelectorAll(".reveal");
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) {
        e.target.classList.add("visible");
        observer.unobserve(e.target);
      }
    });
  },
  { threshold: 0.15 }
);
reveals.forEach((el) => observer.observe(el));

// ── Waitlist form ───────────────────────────────────────
const form = document.getElementById("waitlist-form");
const msg = document.getElementById("waitlist-msg");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("waitlist-email").value.trim();
  if (!email) return;

  // Store in localStorage as simple demo persistence
  const list = JSON.parse(localStorage.getItem("aw_waitlist") || "[]");
  if (list.includes(email)) {
    msg.textContent = "You're already on the list!";
    msg.style.color = "#ffbd2e";
    return;
  }
  list.push(email);
  localStorage.setItem("aw_waitlist", JSON.stringify(list));

  msg.textContent = "You're in! We'll reach out soon.";
  msg.style.color = "#00FFA3";
  form.reset();
});

// ── Nav background on scroll ────────────────────────────
const nav = document.querySelector(".nav");
window.addEventListener("scroll", () => {
  nav.style.borderBottomColor =
    window.scrollY > 40 ? "rgba(42,42,62,.8)" : "rgba(42,42,62,.3)";
});
