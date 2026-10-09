// import { Route, Routes } from "react-router-dom"

// import CvResultPage from "@/app/pages/CvResultPage"
// import UploadPage from "@/app/pages/UploadPage"
import { Header } from "@/components/Header"

function App() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      {/* <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/cv/:cvDocumentId" element={<CvResultPage />} />
      </Routes> */}
    </div>
  )
}

export default App
