// eslint.config.js
// Stricter ESLint config for React/JSX v9+ (Flat Config)

// Attempt to dynamically require, handle potential errors
let pluginReact;
try {
    pluginReact = require('eslint-plugin-react');
    console.log("eslint.config.js: Successfully loaded 'eslint-plugin-react'.");
} catch (e) {
    console.error("eslint.config.js: Could not load 'eslint-plugin-react'. Please install it (`npm install -g eslint-plugin-react` or locally). Linter may not function correctly.");
    pluginReact = null; // Set to null to avoid errors later
}

module.exports = [
  // Base configuration applicable to JS/JSX files
  {
    files: ["**/*.{js,jsx}"],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parserOptions: {
        ecmaFeatures: {
          jsx: true // Enable JSX parsing
        }
      },
      // Using default Espree parser - should handle basic JSX syntax
      // For very complex cases or experimental features, Babel parser might be needed,
      // but let's see if the default works with stricter rules first.
    },
    settings: {
      react: {
        version: "detect" // Automatically detect React version
      }
    },
    rules: {
      // --- Essential JavaScript Rules (Enabled by default in ESLint v9, but explicit is clear) ---
      "constructor-super": "error", "for-direction": "error", "getter-return": "error",
      "no-async-promise-executor": "error", "no-case-declarations": "error", "no-class-assign": "error",
      "no-compare-neg-zero": "error", "no-cond-assign": "error", "no-const-assign": "error",
      "no-constant-binary-expression": "error", "no-constant-condition": "warn",
      "no-control-regex": "error", "no-debugger": "warn", "no-delete-var": "error",
      "no-dupe-args": "error", "no-dupe-class-members": "error", "no-dupe-else-if": "error",
      "no-dupe-keys": "error", "no-duplicate-case": "error", "no-empty": "warn",
      "no-empty-character-class": "error", "no-empty-pattern": "error", "no-ex-assign": "error",
      "no-fallthrough": "error", "no-func-assign": "error", "no-global-assign": "error",
      "no-import-assign": "error", "no-inner-declarations": "error", "no-invalid-regexp": "error",
      "no-irregular-whitespace": "error", "no-loss-of-precision": "error",
      "no-misleading-character-class": "error", "no-mixed-spaces-and-tabs": "error",
      "no-new-native-nonconstructor": "error", "no-nonoctal-decimal-escape": "error",
      "no-obj-calls": "error", "no-octal": "error", "no-prototype-builtins": "warn",
      "no-redeclare": "error", "no-regex-spaces": "error", "no-self-assign": "error",
      "no-setter-return": "error", "no-shadow-restricted-names": "error", "no-sparse-arrays": "warn",
      "no-this-before-super": "error", "no-undef": "error", "no-unexpected-multiline": "error",
      "no-unreachable": "error", "no-unsafe-finally": "error", "no-unsafe-negation": "error",
      "no-unsafe-optional-chaining": "error", "no-unused-labels": "warn",
      "no-unused-vars": ["warn", { "argsIgnorePattern": "^_", "varsIgnorePattern": "^_" }],
      "no-useless-backreference": "error", "no-useless-catch": "warn", "no-useless-escape": "warn",
      "no-with": "error", "require-yield": "error", "use-isnan": "error", "valid-typeof": "error",
      "no-console": "warn", // Add console warning
    }
  },

  // --- React Specific Configuration (Only if plugin loaded) ---
  ...(pluginReact ? [
    {
      files: ["**/*.{js,jsx}"],
      plugins: {
        react: pluginReact
      },
      // Apply React recommended rules
      // For flat config, spread the rules object from the recommended config
      rules: {
        ...pluginReact.configs.recommended.rules,
        // Override or add specific rules below if needed
        "react/react-in-jsx-scope": "off", // Not needed with React 17+ JSX transform
        "react/prop-types": "off", // Disable prop-types if not using them (e.g., using TypeScript)
        "react/jsx-uses-react": "warn", // Still useful sometimes
        "react/jsx-uses-vars": "warn",
        // Add any other specific overrides here
      }
    }
  ] : []) // If pluginReact is null, this evaluates to an empty list
];
