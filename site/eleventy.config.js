import { EleventyHtmlBasePlugin } from "@11ty/eleventy";

export default function (eleventyConfig) {
  // Copy static assets straight through
  eleventyConfig.addPassthroughCopy("src/css");
  eleventyConfig.addPassthroughCopy("src/public");
  eleventyConfig.addPassthroughCopy("public");

  // Allow GitHub Pages base path to be injected at build time
  eleventyConfig.addPlugin(EleventyHtmlBasePlugin);

  // Custom filters used in templates

  eleventyConfig.addFilter("statusClass", (status) => {
    const classes = {
      stable: "status-stable",
      beta: "status-beta",
      experimental: "status-experimental",
      maintenance: "status-maintenance",
      planning: "status-planning",
      alpha: "status-alpha",
    };
    return classes[status] ?? "status-experimental";
  });

  eleventyConfig.addFilter("kindClass", (kind) => {
    const classes = {
      application: "kind-application",
      extension: "kind-extension",
      tool: "kind-tool",
      package: "kind-package",
    };
    return classes[kind] ?? "kind-extension";
  });

  eleventyConfig.addFilter("githubStars", (pkg) => {
    return pkg._github?.github_stars ?? null;
  });

  eleventyConfig.addFilter("pypiVersion", (pkg) => {
    return pkg._pypi?.pypi_version ?? null;
  });

  eleventyConfig.addFilter("lastPushed", (pkg) => {
    const pushed = pkg._github?.github_last_push;
    if (!pushed) return null;
    return new Date(pushed).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  });

  // Collect all unique values for a given field across packages (for filter UIs)
  eleventyConfig.addFilter("allValues", (packages, field) => {
    const values = new Set();
    for (const pkg of packages) {
      const val = pkg[field];
      if (Array.isArray(val)) val.forEach((v) => values.add(v));
      else if (val) values.add(val);
    }
    return [...values].sort();
  });

  return {
    htmlTemplateEngine: "njk",
    markdownTemplateEngine: "njk",
    dir: {
      input: "src",
      output: "_site",
      includes: "_includes",
      layouts: "_layouts",
      data: "_data",
    },
    pathPrefix: process.env.ELEVENTY_PATH_PREFIX ?? "/",
  };
}
