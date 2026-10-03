// ESLint flat config for the two measurement scripts (measurements/*.mjs). Permissive: real mistakes only.
// Run: npm run lint:js
import js from '@eslint/js';
import globals from 'globals';

export default [
  { ignores: ['node_modules/**', 'results/**', 'out/**'] },
  js.configs.recommended,
  {
    files: ['**/*.{js,mjs,cjs}'],
    languageOptions: { ecmaVersion: 2024, sourceType: 'module', globals: { ...globals.node, ...globals.es2024 } },
    rules: {
      'no-unused-vars': ['warn', { args: 'none', caughtErrors: 'none', varsIgnorePattern: '^_' }],
      'no-empty': ['warn', { allowEmptyCatch: true }],
      'no-constant-condition': ['warn', { checkLoops: false }],
      'no-irregular-whitespace': ['error', { skipStrings: true, skipComments: true, skipRegExps: true, skipTemplates: true }],
    },
  },
];
