export default [
  {
    files: ["src/components/**/*.js", "observablehq.config.js"],
    rules: {
      "no-unused-vars": ["warn", {argsIgnorePattern: "^_"}],
      "no-undef": "off",        // Observable runtime injects globals (Plot, FileAttachment, etc.)
      "no-console": "off",
    },
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
    },
  },
];
