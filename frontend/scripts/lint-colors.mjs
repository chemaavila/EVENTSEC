import { promises as fs } from "fs";
import path from "path";

const root = path.resolve("src");
const allowedFiles = new Set([path.resolve(root, "styles", "tokens.css")]);
const filePattern = /\.(css|ts|tsx)$/;
const colorPattern = /#([0-9a-fA-F]{3,8})\b|rgba?\(|hsla?\(/;

const matches = [];

const walk = async (dir) => {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      await walk(fullPath);
      continue;
    }
    if (!filePattern.test(entry.name)) {
      continue;
    }
    if (allowedFiles.has(fullPath)) {
      continue;
    }
    const contents = await fs.readFile(fullPath, "utf-8");
    if (!colorPattern.test(contents)) {
      continue;
    }
    contents.split(/\r?\n/).forEach((line, index) => {
      if (colorPattern.test(line)) {
        matches.push(`${path.relative(process.cwd(), fullPath)}:${index + 1} ${line.trim()}`);
      }
    });
  }
};

await walk(root);

if (matches.length) {
  console.error("Hardcoded colors detected (use tokens instead):");
  for (const match of matches) {
    console.error(`- ${match}`);
  }
  process.exit(1);
}
