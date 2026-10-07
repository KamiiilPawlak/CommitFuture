import { Route, Routes } from "react-router-dom"

import CvResultPage from "@/app/pages/CvResultPage"
import UploadPage from "@/app/pages/UploadPage"

function App() {
  return (
    <Routes>
      <Route path="/" element={<UploadPage />} />
      <Route path="/cv/:cvDocumentId" element={<CvResultPage />} />
    </Routes>
  )
}

export default App
