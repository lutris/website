import { cp } from "node:fs/promises";
import { defineConfig } from "vite";

const entries = {
  lutris: "frontend/js/app.js",
  editor: "frontend/js/editor.js",
  styles: "frontend/css/lutris.scss",
};

// Vendor files loaded directly by some templates, outside the bundles
const vendorFiles = {
  "node_modules/bootstrap-icons/font": "public/css",
  "node_modules/blueimp-gallery/css": "public/css",
  "node_modules/blueimp-gallery/js": "public/js",
  "node_modules/blueimp-gallery/img": "public/img",
  "node_modules/croppie/croppie.js": "public/js/croppie.js",
  "node_modules/croppie/croppie.min.js": "public/js/croppie.min.js",
  "node_modules/croppie/croppie.css": "public/css/croppie.css",
};

function environment(name, input) {
  return {
    consumer: "client",
    build: {
      rolldownOptions: {
        input: { [name]: input },
        output: {
          // Vite names every non code-split CSS bundle style.css. Apart from
          // it, only bootstrap-icons' fonts are too big to be inlined.
          assetFileNames: ({ names }) =>
            names[0].endsWith(".css") ? `css/${name}.css` : "webfonts/[name][extname]",
        },
      },
    },
  };
}

export default defineConfig(({ mode }) => ({
  // Make asset URLs relative to the CSS files referencing them
  base: "./",
  // public/ is where the assets are built, not a source of files to copy
  publicDir: false,
  environments: Object.fromEntries(
    Object.entries(entries).map(([name, input]) => [name, environment(name, input)]),
  ),
  builder: {
    async buildApp(builder) {
      for (const [from, to] of Object.entries(vendorFiles)) {
        await cp(from, to, { recursive: true });
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
        entryFileNames: "js/[name].min.js",
      },
    },
  },
}));
