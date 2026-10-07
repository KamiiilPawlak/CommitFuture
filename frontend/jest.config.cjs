module.exports = {
  rootDir: ".",
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/tests/setup.ts"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
    "\\.(css|less|scss|sass)$": "identity-obj-proxy",
  },
  testMatch: ["<rootDir>/tests/**/*.test.{ts,tsx}"],
  transform: {
    "^.+\\.(ts|tsx|js|jsx)$": "babel-jest",
  },
}
