import { TextDecoder, TextEncoder } from "node:util"

import "@testing-library/jest-dom"

if (typeof globalThis.TextEncoder === "undefined") {
  globalThis.TextEncoder = TextEncoder
}
if (typeof globalThis.TextDecoder === "undefined") {
  // @ts-expect-error node's TextDecoder is a structural match for the DOM lib type
  globalThis.TextDecoder = TextDecoder
}

process.env.VITE_API_URL ??= "http://localhost:8000/api/v1"
