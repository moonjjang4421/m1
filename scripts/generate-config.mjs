import { writeFileSync } from "node:fs";

const apiBaseUrl = (process.env.API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
writeFileSync("frontend/config.js", `window.APP_CONFIG = ${JSON.stringify({ apiBaseUrl })};\n`);
console.log("frontend/config.js generated");

