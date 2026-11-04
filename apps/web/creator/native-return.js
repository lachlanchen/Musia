"use strict";
const destination = document.getElementById("native-return");
if (destination) {
  const url = new URL(destination.href);
  const keys = [...url.searchParams.keys()];
  const expires = Number(destination.dataset.expiresIn);
  if (url.protocol === "art.lazying.musia:" && url.hostname === "auth" &&
      !url.pathname && !url.username && !url.password && !url.port && !url.hash &&
      keys.length === 2 && keys.includes("attempt") && keys.includes("code") &&
      /^[a-f0-9]{32}$/.test(url.searchParams.get("attempt")) &&
      /^[A-Za-z0-9_-]{32,128}$/.test(url.searchParams.get("code")) &&
      Number.isInteger(expires) && expires > 0 && expires <= 600) {
    // The app still checks attempt, expiry and PKCE before accepting this code.
    history.replaceState(null, "", "/creator/");
    // Keep a real user-gesture link. Mobile browsers may reject automatic launch.
    try { location.replace(url.href); } catch { /* The visible link remains usable. */ }
    setTimeout(() => {
      for (const link of [destination, document.getElementById("android-return")]) {
        if (!link) continue;
        link.removeAttribute("href");
        link.setAttribute("aria-disabled", "true");
      }
      document.getElementById("return-help").textContent =
        "This sign-in has expired. Start again in Musia. 登录已过期，请在 Musia 中重新开始。";
    }, expires * 1000);
  }
}
