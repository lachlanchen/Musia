"use strict";
const destination = document.getElementById("native-return");
if (destination) {
  const url = new URL(destination.href);
  if (url.protocol === "art.lazying.musia:" && url.hostname === "auth") {
    // The app still checks attempt, expiry and PKCE before accepting this code.
    history.replaceState(null, "", "/creator/");
    location.replace(url.href);
  }
}
