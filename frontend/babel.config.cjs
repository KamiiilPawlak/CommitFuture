module.exports = (api) => {
  const isTest = api.env("test")

  return {
    presets: [
      ["@babel/preset-env", { targets: { node: "current" } }],
      ["@babel/preset-react", { runtime: "automatic" }],
      "@babel/preset-typescript",
    ],
    // Vite doesn't read this file for app code (esbuild/rollup handle that) — only
    // Jest does, via jest.config.cjs. Jest's CommonJS runtime can't execute
    // `import.meta`, so under test we rewrite `import.meta.env` to `process.env`
    // (see tests/setup.ts for the VITE_* values Jest provides).
    plugins: isTest
      ? [
          function importMetaEnvPlugin() {
            return {
              visitor: {
                MetaProperty(path) {
                  if (
                    path.node.meta.name === "import" &&
                    path.node.property.name === "meta"
                  ) {
                    path.replaceWithSourceString("({ env: process.env })")
                  }
                },
              },
            }
          },
        ]
      : [],
  }
}
