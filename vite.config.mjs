import { cp } from "node:fs/promises";
import path from "node:path";
import { defineConfig } from "vite";

// The templates load the bundles with plain <script> tags, so they are built
// as IIFEs. Rolldown only supports that for a single input, hence one
// environment (a separate build) per entry.
const entries = {
  lutris: "frontend/js/app.js",
  editor: "frontend/js/editor.js",
  styles: "frontend/css/lutris.scss",
};

// Vendor files loaded directly by some templates, outside of the bundles
const vendorFiles = {
  "node_modules/bootstrap-icons/font": "css",
  "node_modules/blueimp-gallery/css": "css",
  "node_modules/blueimp-gallery/js": "js",
  "node_modules/blueimp-gallery/img": "img",
  "node_modules/croppie/croppie.js": "js/croppie.js",
  "node_modules/croppie/croppie.min.js": "js/croppie.min.js",
  "node_modules/croppie/croppie.css": "css/croppie.css",
};

function assetFileNames(entryName) {
  return ({ names }) => {
    const ext = path.extname(names[0]);
    if (ext === ".css") {
      return `css/${entryName}.css`;
    }
    if ([".woff", ".woff2", ".eot", ".ttf", ".otf"].includes(ext)) {
      return "webfonts/[name][extname]";
    }
    return "img/[name][extname]";
  };
}

export default defineConfig(({ mode }) => ({
  // The .env* files at the root are Django's
  envDir: false,
  // Make asset URLs relative to the CSS files referencing them
  base: "./",
  // public/ is where the assets are built, not a source of files to copy
  publicDir: false,
  environments: Object.fromEntries(
    Object.entries(entries).map(([name, entry]) => [
      name,
      {
        consumer: "client",
        build: {
          rolldownOptions: {
            input: { [name]: entry },
            output: { assetFileNames: assetFileNames(name) },
          },
        },
      },
    ]),
  ),
  builder: {
    async buildApp(builder) {
      const { root, build } = builder.config;
      for (const [from, to] of Object.entries(vendorFiles)) {
        await cp(path.resolve(root, from), path.resolve(root, build.outDir, to), { recursive: true });
      }
      for (const name of Object.keys(entries)) {
        await builder.build(builder.environments[name]);
      }
    },
  },
  build: {
    outDir: "public",
    // public/ also holds files tracked in git
    emptyOutDir: false,
    // Extract each entry's CSS into a single file, instead of injecting it from
    // the JS as Vite does for IIFE bundles
    cssCodeSplit: false,
    minify: mode === "production",
    sourcemap: mode === "production" ? false : "inline",
    rolldownOptions: {
      output: {
        format: "iife",
        entryFileNames: mode === "production" ? "js/[name].min.js" : "js/[name].js",
      },
    },
  },
}));