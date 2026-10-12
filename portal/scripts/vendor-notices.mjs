import { mkdir, readFile, writeFile } from "node:fs/promises";

// Retain notices for every locked non-development package in the browser graph.
const lock = JSON.parse(await readFile("package-lock.json", "utf8"));
const notices = [];
for (const [path, entry] of Object.entries(lock.packages)) {
  if (!path || entry.dev || !path.includes("node_modules/")) continue;
  const metadata = JSON.parse(await readFile(`${path}/package.json`, "utf8"));
  let license;
  for (const name of ["LICENSE", "LICENSE.md", "LICENSE.txt", "LICENSE-MIT", "license", "license.md"]) {
    try { license = await readFile(`${path}/${name}`, "utf8"); break; } catch (error) { if (error.code !== "ENOENT") throw error; }
  }
  if (!license) throw new Error(`Missing license notice for ${metadata.name}`);
  notices.push(`${metadata.name} ${metadata.version}\n${metadata.homepage ?? metadata.repository?.url ?? ""}\n${metadata.license ?? ""}\n\n${license}`);
}
await mkdir("static-built", { recursive: true });
await writeFile("static-built/THIRD-PARTY-NOTICES.txt", notices.join("\n\n--------------------\n\n"));
